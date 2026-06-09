#!/usr/bin/python

import argparse
from dotmgr import mods, filelib, DOTFILES_MANAGED_FILE, outputs
from dotmgr.mods import InstallStatus
import os
import subprocess
from typing import Iterable, Optional


ALL_DOTFILES = filelib.load_dotfiles(DOTFILES_MANAGED_FILE)
AVAILABLE_DOTFILES = {
    name: d
    for name, d in ALL_DOTFILES.items()
    if not d.used_by or d.used_by.status == InstallStatus.INSTALLED
}
STANDALONE_DOTFILES = {
    name: d
    for name, d in ALL_DOTFILES.items()
    if not d.used_by
}


class Choices(tuple):
    """
    This class provides a wrapper around the `tuple` class to work around a 14-year-old bug in Python that was only fixed in 2024
    and marked for release in Python 3.14: https://github.com/python/cpython/issues/53834. Using this class allows you to
    set multiple possible choices and defaults on a positional argument with `nargs='*'`, as it fixes a bug in `argparse` on line 2496:
    ```python
    if action.choices is not None and value not in action.choices: ...
    ```
    If `value` is itself a collection, the latter condition will fail, as the collection itself obviously isn't a member of the given choices.

    Once Apple eventually updates the version of Python it ships to 3.14 or newer, this workaround can be removed.
    """

    def __new__(cls, _iterable: Iterable, default: Optional[Iterable] = None):
        x = tuple.__new__(cls, _iterable)
        Choices.__init__(x, _iterable, default=default)
        return x

    def __init__(self, _iterable: Optional[Iterable] = None, default: Optional[Iterable] = None):
        # _iterable is already handled by tuple.__new__
        self.default = default or []

    def __contains__(self, item):
        return super().__contains__(item) or item == self.default
    

_available_dotfiles_choices = Choices(
    AVAILABLE_DOTFILES.keys(),
    default=AVAILABLE_DOTFILES.keys()
)
"""
This list contains the keys of the AVAILABLE_DOTFILES dict (i.e. the relative paths of the dotfiles), as well as a "hidden"
`None` element in there to work around a bug in argparse.
"""


# region Define arguments
parser = argparse.ArgumentParser()
sp_manager = parser.add_subparsers(required=True, metavar="command", dest="sp")

# Link
sp_ln = sp_manager.add_parser(
    "ln",
    help="Link dotfiles",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_ln.add_argument(
    "file",
    nargs="*",
    help="(Optional) relative path to file(s) to link. If not given, all files (except those used by uninstalled Mods) will be linked.",
    default=_available_dotfiles_choices.default,
    choices=_available_dotfiles_choices,
    metavar="file",
)

# Remove
sp_rm = sp_manager.add_parser(
    "rm",
    help="Remove dotfiles",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_rm.add_argument(
    "file",
    nargs="+",
    help="Relative path to file(s) to remove.",
    choices=_available_dotfiles_choices,
    metavar="file",
)

# Sync
sp_sync = sp_manager.add_parser(
    "sync",
    help="Sync dotfiles",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_sync.add_argument(
    "file",
    nargs="*",
    help="(Optional) relative path to file(s) to sync. If not given, all files (except those used by uninstalled Mods) will be synced.",
    default=_available_dotfiles_choices.default,
    choices=_available_dotfiles_choices,
    metavar="file",
)

# Adopt
sp_adopt = sp_manager.add_parser(
    "adopt",
    help="Adopt local dotfile to dotfile repo",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_adopt.add_argument("file", nargs="+", help="Relative path to the file(s) to adopt")

# Orphan
sp_orphan = sp_manager.add_parser(
    "orphan",
    help="Orphan one or more dotfiles. This converts a once synced dotfile to a local-only dotfile.",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_orphan.add_argument(
    "file",
    nargs="+",
    help="Relative path to the file(s) to orphan",
    choices=_available_dotfiles_choices,
    metavar="file",
)
sp_orphan.add_argument(
    "-r",
    "--rm",
    help="Remove file from dotfile repo after orphaning",
    action="store_true",
)

# Edit
sp_edit = sp_manager.add_parser(
    "edit",
    help="Edit or view a dotfile, respecting the your chosen editor (set in $EDITOR) by default.",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_edit.add_argument(
    "-c", help="Open in VSCode", dest="editor_vscode", action="store_true"
)
sp_edit.add_argument("-v", help="Open in Vim", dest="editor_vim", action="store_true")
sp_edit.add_argument("-n", help="Open in Nano", dest="editor_nano", action="store_true")
sp_edit.add_argument("-l", help="Open in Less", dest="editor_less", action="store_true")
sp_edit.add_argument(
    "file",
    help="Relative path to the file to edit or view",
    choices=ALL_DOTFILES.keys(),
    metavar="file",
)

# Mod
sp_mod = sp_manager.add_parser("mod", help="Manage mods")
sp_mod.add_argument("action", choices=("install", "detect"), help="Action")
sp_mod.add_argument("mod_name", choices=mods.__mods__.keys(), help="Mod name")

# Git
sp_git = sp_manager.add_parser("git", help="Interact with the dotfile Git repo")
sp_git.add_argument(
    "action",
    choices=("pull", "push", "reset", "commit", "update"),
    help="Git subcommand/action",
)
sp_git.add_argument(
    "message",
    nargs="?",
    type=str,
    help="Git commit message (optional)",
)

# endregion

args = parser.parse_args()

# region Handle arguments

# Link
if args.sp == "ln":
    for fn in args.file:
        if fn in ALL_DOTFILES.keys():
            dotfile = ALL_DOTFILES[fn]

            if fn not in AVAILABLE_DOTFILES.keys():
                print(
                    f"Dotfile {fn} shouldn't be linked yet, since it's used by {dotfile.used_by}, which isn't installed yet."
                )
                continue

            dotfile.ln()

# Remove
elif args.sp == "rm":
    for fn in args.file:
        if fn in ALL_DOTFILES.keys():
            dotfile = ALL_DOTFILES[fn]

            if fn not in AVAILABLE_DOTFILES.keys():
                print(
                    f"Dotfile {fn} shouldn't be removed yet, since it's used by {dotfile.used_by}, which isn't installed yet."
                )
                continue

            dotfile.rm()

# Sync
elif args.sp == "sync":
    for fn in args.file:
        if fn in ALL_DOTFILES.keys():
            dotfile = ALL_DOTFILES[fn]

            if fn not in AVAILABLE_DOTFILES.keys():
                print(
                    f"Dotfile {fn} shouldn't be synced yet, since it's used by {dotfile.used_by}, which isn't installed yet."
                )
                continue

            dotfile.sync()

# Adopt - copy unmanaged (unlinked) dotfile to repo, then link it back
elif args.sp == "adopt":
    for fn in args.file:
        dotfile = filelib.Dotfile(fn)
        if dotfile.adopt():
            ALL_DOTFILES[str(dotfile.relative_path)] = dotfile

    filelib.update_managed_list(ALL_DOTFILES, DOTFILES_MANAGED_FILE)

# Orphan - remove dotfile link, then copy the actual file to its destination
elif args.sp == "orphan":
    for fn in args.file:
        dotfile = ALL_DOTFILES[fn]

        if fn not in STANDALONE_DOTFILES:
            if not outputs.confirm(
                f"Heads up! Dotfile {fn} is used by installed mod {dotfile.used_by}, so orphaning it is risky. Continue anyways?"
            ):
                continue

        dotfile.orphan()

        if args.rm:
            print(f"Removing orphaned file {fn} from managed.files")
            dotfile.src.unlink()
            del ALL_DOTFILES[fn]

    filelib.update_managed_list(ALL_DOTFILES, DOTFILES_MANAGED_FILE)

# Edit the dotfile - respects $EDITOR if editor is not chosen explicitly
elif args.sp == "edit":
    editor = (
        "code"
        if args.editor_vscode
        else "vim"
        if args.editor_vim
        else "nano"
        if args.editor_nano
        else "less"
        if args.editor_less
        else os.environ.get("EDITOR", "cat")
    )
    if editor == "cat":
        print(
            "WARN: $EDITOR variable is unset, and editor was not specified, so defaulted to `cat`."
        )

    dotfile = ALL_DOTFILES.get(args.file)
    # Safely assert here, as argparse makes sure the chosen dotfile is known and valid.
    assert dotfile

    subprocess.run([editor, dotfile.src])

# Interact with mods
elif args.sp == "mod":
    mod_name: str = args.mod_name
    selected_mod = mods.__mods__.get(mod_name)
    if not selected_mod:
        raise ValueError(f"Selected mod {mod_name} does not exist.")

    if args.action == "detect":
        selected_mod.detect()
    elif args.action == "install":
        selected_mod.install()

# Interact with Git
elif args.sp == "git":
    raise NotImplementedError("The Git wrapper is not yet implemented.")

# endregion
