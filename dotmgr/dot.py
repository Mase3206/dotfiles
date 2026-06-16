#!/usr/bin/python

import argparse
import os
import subprocess
from typing import Iterable, Optional

from dotmgr import DOTFILES_DIR, DOTFILES_MANAGED_FILE, filelib, git, mods, outputs
from dotmgr.mods import InstallStatus

ALL_DOTFILES = filelib.load_dotfiles(DOTFILES_MANAGED_FILE)
AVAILABLE_DOTFILES = {
    name: d
    for name, d in ALL_DOTFILES.items()
    if not d.used_by or d.used_by.status == InstallStatus.INSTALLED
}
STANDALONE_DOTFILES = {name: d for name, d in ALL_DOTFILES.items() if not d.used_by}


class Choices(tuple):
    """
    This class provides a wrapper around the `tuple` class to work around a 14-year-old bug in Python that was only fixed in 2024
    and marked for release in Python 3.14: https://github.com/python/cpython/issues/53834. Using this class allows you to
    set multiple possible choices and defaults on a positional argument with `nargs='*'`, as it fixes a bug in `argparse` on line 2496:
    ```python
           if action.choices is not None and value not in action.choices:
               ...
    ```
    If `value` is itself a collection, the latter condition will fail, as the collection itself obviously isn't a member of the given choices.

    Once Apple eventually updates the version of Python it ships to 3.14 or newer, this workaround can be removed.
    """

    def __new__(cls, _iterable: Iterable, default: Optional[Iterable] = None):
        x = tuple.__new__(cls, _iterable)
        Choices.__init__(x, _iterable, default=default)
        return x

    def __init__(
        self, _iterable: Optional[Iterable] = None, default: Optional[Iterable] = None
    ):
        # _iterable is already handled by tuple.__new__
        self.default = default or []

    def __contains__(self, item):
        return super().__contains__(item) or item == self.default


_available_dotfiles_choices = Choices(
    AVAILABLE_DOTFILES.keys(), default=AVAILABLE_DOTFILES.keys()
)
"""
This list contains the keys of the AVAILABLE_DOTFILES dict (i.e. the relative paths of the dotfiles), as well as a "hidden"
`None` element in there to work around a bug in argparse.
"""


# region Define arguments
parser = argparse.ArgumentParser(
    prog="dot",
    description=f"{outputs.AnsiColors.BOLD}dot{outputs.AnsiColors.END} is a custom, lightweight, stdlib-only dependency manager. Written for Python 3.9+, it supports macOS (because even macOS 26 is shipping with Python 3.9.6, which is from 2022) and older Linux distros, and, as Python 3 generally has excellent backwards compatibility, it is highly likely to work on later versions as well.",
)
sp_manager = parser.add_subparsers(required=True, metavar="command", dest="sp")

# Link
sp_ln = sp_manager.add_parser(
    "ln",
    help="Link dotfiles",
    description="Link dotfiles",
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
    description="Remove dotfiles",
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
    description="Sync dotfiles",
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

# Manage - add file in dotfiles to managed.files
sp_manage = sp_manager.add_parser(
    "manage",
    help="Add file(s) in $DOTFILES_DIR to managed.files",
    description=f"Add file(s) in $DOTFILES_DIR ({DOTFILES_DIR}) to managed.files",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_manage.add_argument(
    "file",
    nargs="+",
    help="Relative path to file(s) to add to managed.files.",
)

# Unmanage - remove file in dotfiles to managed.files
sp_unmanage = sp_manager.add_parser(
    "unmanage",
    help="Remove file(s) in $DOTFILES_DIR from managed.files",
    description=f"Remove file(s) in $DOTFILES_DIR ({DOTFILES_DIR}) from managed.files",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_unmanage.add_argument(
    "file",
    nargs="+",
    help="Relative path to files(s) to remove from managed.files.",
    choices=_available_dotfiles_choices,
)

# Adopt
sp_adopt = sp_manager.add_parser(
    "adopt",
    help="Adopt local dotfile to dotfile repo $DOTFILES_DIR",
    description=f"Adopt local dotfile to dotfile repo $DOTFILES_DIR ({DOTFILES_DIR})",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_adopt.add_argument(
    "file",
    nargs="+",
    help="Relative path to the file(s) to adopt",
)

# Orphan
sp_orphan = sp_manager.add_parser(
    "orphan",
    help="Orphan one or more dotfiles. This converts a once synced dotfile to a local-only dotfile.",
    description="Orphan one or more dotfiles. This converts a once synced dotfile to a local-only dotfile.",
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
    description=f"Edit or view a dotfile, respecting the your chosen editor (set in $EDITOR) by default. Your current editor is {os.environ.get('EDITOR', 'unset')}.",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_edit.add_argument(
    "-c", help="Open in VSCode", dest="editor_vscode", action="store_true"
)
sp_edit.add_argument(
    "-v",
    help="Open in Vim",
    dest="editor_vim",
    action="store_true",
)
sp_edit.add_argument(
    "-n",
    help="Open in Nano",
    dest="editor_nano",
    action="store_true",
)
sp_edit.add_argument(
    "-l",
    help="Open in Less",
    dest="editor_less",
    action="store_true",
)
sp_edit.add_argument(
    "file",
    help="Relative path to the file to edit or view",
    choices=_available_dotfiles_choices,
    metavar="file",
)

# Mod
sp_mod = sp_manager.add_parser(
    "mod",
    help="Manage and interact with known mods",
    description="Manage and interact with known mods",
)
_choices_mods = Choices(mods.__mods__.keys(), default=mods.__mods__.keys())
sp_mod.add_argument(
    "action",
    choices=("install", "detect"),
    help="Action",
)
sp_mod.add_argument(
    "mod_name",
    choices=_choices_mods,
    help="(Optional) mod name(s). If none are given, defaults to all.",
    nargs="*",
    default=_choices_mods.default,
)

# Git
sp_git = sp_manager.add_parser(
    "git",
    help="Interact with the local dotfile Git repo",
    description=f"""\
    Interact with the local dotfile Git repo in $DOTFILES_DIR ({DOTFILES_DIR}).

    COMMIT: Commit changes to managed dotfiles.
    PUSH: Push changes to remote.
    PULL: Stash changes in local repo, pull changes from remote, then unstash changes.
    UNDO: Undo the last commit and unstage the previously committed files.
    STATUS: Get the current Git status of the local repo.
    """,
)
sp_git.add_argument(
    "action",
    choices=("commit", "push", "pull", "undo", "status"),
    help="Upload or download changes to Git remote",
    # default="status",
    # nargs="?",
    # metavar="action",
)
# sp_git.add_argument(
#     "message",
#     nargs="?",
#     type=str,
#     help="Git commit message (optional)",
# )

# endregion

args = parser.parse_args()
# args = parser.parse_args(['git', 'status'])

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

# Manage - add file(s) to managed.files
elif args.sp == "manage":
    # dotfiles_to_add: list[filelib.Dotfile] = []
    new_paths = []
    for fn in args.file:
        if fn in ALL_DOTFILES.keys():
            print(f"'{fn}' is already managed, skipping")
        elif not (DOTFILES_DIR / fn).exists():
            print(f"'{fn}' does not exist, skipping")
        else:
            new_paths.append(fn)
            ALL_DOTFILES[fn] = filelib.Dotfile(fn)

    print(f"Adding new files to managed list: {' '.join(new_paths)}")
    filelib.update_managed_list(ALL_DOTFILES, DOTFILES_MANAGED_FILE)

# Unmanage - remove file(s) from managed.files
elif args.sp == "unmanage":
    removed = []
    for fn in args.file:
        dotfile = ALL_DOTFILES[fn]

        if fn not in STANDALONE_DOTFILES:
            if not outputs.confirm(
                f"Heads up! Dotfile {fn} is used by installed mod {dotfile.used_by}, so unmanaging probably isn't recommended. Continue anyways?"
            ):
                continue

        if dotfile.dest.exists() and dotfile.dest.is_symlink():
            print(f"'{fn}' is still linked. Remove the link with `dot rm {fn}` first.")
        else:
            removed.append(fn)
            del ALL_DOTFILES[fn]

    filelib.update_managed_list(ALL_DOTFILES, DOTFILES_MANAGED_FILE)
    print(f"Unmanaged files: {', '.join(removed)}")

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
        else os.environ.get("EDITOR")
    )
    if not editor:
        print(
            "WARN: $EDITOR variable is unset, and editor was not specified, so defaulted to `cat`."
        )
        editor = "cat"

    dotfile = ALL_DOTFILES.get(args.file)
    # Safely assert here, as argparse makes sure the chosen dotfile is known and valid.
    assert dotfile

    subprocess.run([editor, dotfile.src])

# Interact with mods
elif args.sp == "mod":
    for mod_name in args.mod_name:
        selected_mod = mods.__mods__.get(mod_name)
        if not selected_mod:
            raise ValueError(f"Selected mod {mod_name} does not exist.")

        if args.action == "detect":
            selected_mod.detect()
        elif args.action == "install":
            selected_mod.install()

# Interact with Git
elif args.sp == "git":
    # raise NotImplementedError("The Git wrapper is not yet implemented.")
    # upload, download, status
    if args.action == "commit":
        changed = git.get_changed_dotfiles()
        print(git.format_changed_human(*changed))

        # print("\nA commit message will automatically be generated.")
        msg = git.generate_commit_message(*changed)
        print("\nCommit message:\n" + msg, end="\n\n")

        if outputs.confirm("Confirm commit?"):
            git.commit_dotfiles(*changed)

    if args.action == "push":
        git.git_cmd("status")
        print()
        if outputs.confirm("Confirm push?"):
            git.push_dotfiles()

    elif args.action == "pull":
        git.stash_push()
        git.pull()
        git.stash_pop()

    elif args.action == "undo":
        print(f"{outputs.AnsiColors.BOLD}Last commit:{outputs.AnsiColors.END}")
        git.git_cmd("--no-pager log -1 --pretty=oneline")

        print(f"\n{outputs.AnsiColors.BOLD}Files changed:{outputs.AnsiColors.END}")
        changed_files = (
            git.git_cmd("--no-pager diff -z --name-only HEAD HEAD~1", stdout=True)
            .stdout[:-1]
            .split("\0")
        )
        print("\n".join(changed_files), end="\n\n")

        if outputs.confirm("Undo last commit?"):
            git.git_cmd("reset --soft HEAD~1")
            git.git_cmd(["restore", "--staged", *changed_files])

    elif args.action == "status":
        # git.git_cmd('status')
        changed = git.get_changed_dotfiles()
        print(git.format_changed_human(*changed))


# endregion
