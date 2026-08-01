#!/usr/bin/python

import argparse
import os
import shutil
import subprocess
import sys
from collections import UserList
from typing import Generic, Iterable, TypeVar

from dotmgr import DOTFILES_DIR, DOTFILES_MANAGED_FILE, HOME, filelib, git, mods, outputs
from dotmgr.mods import InstallStatus


ALL_DOTFILES = filelib.load_dotfiles(DOTFILES_MANAGED_FILE)
AVAILABLE_DOTFILES = {
    name: d
    for name, d in ALL_DOTFILES.items()
    if not d.used_by or d.used_by.status == InstallStatus.INSTALLED
}
STANDALONE_DOTFILES = {name: d for name, d in ALL_DOTFILES.items() if not d.used_by}

T = TypeVar("T", bound=str)


class DynamicChoices(UserList[T], Generic[T]):
    """
    Wrapper class around tuple to fix a weird bug in argparse.

    This class provides a wrapper around the `tuple` class to work around a 14-year-old bug in
    Python that was only fixed in 2024 and marked for release in Python 3.14:
    https://github.com/python/cpython/issues/53834. Using this class allows you to set multiple
    possible choices and defaults on a positional argument with `nargs='*'`, as it fixes a bug in
    `argparse` on line 2496:

    ```python
    if action.choices is not None and value not in action.choices:
        ...
    ```
    If `value` is itself a collection, the latter condition will fail, as the collection itself
    obviously isn't a member of the given choices.

    Once every platform I wish to support eventually updates the version of Python it ships to 3.14
    or newer, this workaround can be removed.

    :param Iterable[T] = [] data: Defined choices
    :param Iterable[T] = [] default: Default selection
    :param str = "" dynamic_shell: Shell command which runs to get the up-to-date list, separated by null
        characters. Needed for autocomplete.
    """

    data: list
    default: list
    dynamic_shell: str

    def __init__(
        self,
        data: Iterable[T] = [],
        default: Iterable[T] = [],
        dynamic_shell: str = "",
    ):
        """
        Create a new `Choices` object.

        :param Iterable = [] _iterable: All allowed choices
        :param Iterable = [] default: Default choices
        :param str = '' dynamic_shell: Shell command to run to get the up-to-date list, separated by null
            characters. Needed for autocomplete.
        """
        self.data = list(data)
        self.default = list(default) or []
        self.dynamic_shell = dynamic_shell

    def __contains__(self, item):
        return super().__contains__(item) or item == self.default

    def __add__(self, value: Iterable[T]) -> Iterable[T]:
        return super().__add__(value)


_available_dotfiles_choices = DynamicChoices(
    AVAILABLE_DOTFILES.keys(),
    default=AVAILABLE_DOTFILES.keys(),
    dynamic_shell="dot list -ra0",
)
"""
This list contains the keys of the AVAILABLE_DOTFILES dict (i.e. the relative paths of the
dotfiles), as well as a "hidden" `None` element in there to work around a bug in argparse.
"""


# region Define arguments
parser = argparse.ArgumentParser(
    prog="dot",
    description=f"""
        {outputs.AnsiColors.BOLD}dot{outputs.AnsiColors.END} is a custom, lightweight, stdlib-only
        dotfile manager. Written for Python 3.9+, it supports macOS (because even macOS 26 is
        shipping with Python 3.9.6, which is from 2022) and older Linux distros, and, as Python 3
        generally has excellent backwards compatibility, it is highly likely to work on later
        versions as well.
    """,
)

parser.add_argument(
    "--zsh-completions",
    action="store_true",
    help="Generate and save the Zsh completion definition for dot",
)

sp_manager = parser.add_subparsers(required=False, metavar="command", dest="sp")

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
    help="""
        (Optional) relative path to file(s) to link. If not given, all files (except those used by
        uninstalled Mods) will be linked.
    """,
    default=_available_dotfiles_choices.default,
    choices=_available_dotfiles_choices,
    metavar="file",
)

# Remove
sp_rm = sp_manager.add_parser(
    "rm",
    help="Remove (unlink) dotfiles",
    description="Remove (unlink) dotfiles. The actual source file is not removed.",
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
    help="""
        (Optional) relative path to file(s) to sync. If not given, all files (except those used by
        uninstalled Mods) will be synced.
    """,
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
    metavar="file",
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
    "-k",
    "--keep",
    help="Do not remove (keep) file from dotfile repo after orphaning",
    action="store_true",
)

# List managed files
sp_list = sp_manager.add_parser(
    "list",
    help="List all managed files' relative paths.",
    description="""
        List all managed files' relative paths. If no arguments are given, a file's install status is
        distinguised with a check/cross, and unavailable files are greyed out.
    """,
    epilog="""
        An "available" file is one that either (1) isn\'t associated with a mod, or (2) is associated with
        an *installed* mod.
    """,
)
sp_list.add_argument(
    "-n",
    "--no-color",
    help="Avoid using colors. File availibility is distinguished via a +/- after the check/cross.",
    action="store_true",
)
sp_list.add_argument(
    "-r",
    "--raw",
    help="""
        Just list the files. Don't add checkmarks/crosses indicating file status or +/- indicating file
        availability. Implies --no-color.
    """,
    action="store_true",
)
sp_list.add_argument(
    "-0",
    "--null-sep",
    help="List the files with null separators. Without --raw, this has no effect.",
    action="store_true",
    dest="null_sep",
)
sp_list.add_argument(
    "-l",
    "--linked",
    help="List linked files.",
    action="store_true",
)
sp_list.add_argument(
    "-u",
    "--unlinked",
    help="List unlinked files.",
    action="store_true",
)
sp_list.add_argument(
    "-a",
    "--available",
    help="List available files.",
    action="store_true",
)
sp_list.add_argument(
    "-U",
    "--unavailable",
    help="List unavailable files.",
    action="store_true",
)

# Edit
sp_edit = sp_manager.add_parser(
    "edit",
    help="Edit or view a dotfile, respecting the your chosen editor (set in $EDITOR) by default.",
    description=f"""
        Edit or view a dotfile, respecting the your chosen editor (set in $EDITOR) by default. Your current
        editor is {outputs.AnsiColors.UNDERLINE}{os.environ.get("EDITOR", "unset")}{outputs.AnsiColors.END}.
    """,
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_edit.add_argument(
    "-c",
    help="Open in VS Code",
    dest="editor_vscode",
    action="store_true",
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
    help="""
        Relative path to the file to edit or view. If no file is given, the editor will open to the
        dotfiles directory.
    """,
    choices=_available_dotfiles_choices,
    metavar="file",
    nargs="?",
)


# Dump/Cat
sp_cat = sp_manager.add_parser(
    "cat",
    help="Dump (cat) the contents of the dotfile to stdout.",
    description="Dump (cat) the contents of the dotfile to stdout.",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_cat.add_argument(
    "file",
    help="Relative path to the file to dump (cat).",
    choices=_available_dotfiles_choices,
    metavar="file",
    nargs="+"
)


# Mod
_choices_mods = DynamicChoices(
    mods.__mods__.keys(),
    default=mods.__mods__.keys(),
    dynamic_shell="dot mod list -0",
)
sp_mod = sp_manager.add_parser(
    "mod",
    help="Manage and interact with known mods",
    description="Manage and interact with known mods",
    # aliases=["mods"],
)
sp_mod_manager = sp_mod.add_subparsers(required=True, metavar="mod_subcommand", dest="mod_sp")

sp_mod_install = sp_mod_manager.add_parser("install", help="Install mod(s)")
sp_mod_install.add_argument(
    "mod_name",
    choices=_choices_mods,
    help="(Optional) mod name(s). If none are given, defaults to all discovered mods.",
    nargs="*",
    default=_choices_mods.default,
)

sp_mod_detect = sp_mod_manager.add_parser("detect", help="Detect mod(s)")
sp_mod_detect.add_argument(
    "mod_name",
    choices=_choices_mods,
    help="(Optional) mod name(s). If none are given, defaults to all discovered mods.",
    nargs="*",
    default=_choices_mods.default,
)
sp_mod_detect.add_argument(
    "-n",
    "--no-color",
    help="When running `dot mod detect`, don't use ANSI colors to color the checkmarks/crosses.",
    action="store_true",
)

sp_mod_list = sp_mod_manager.add_parser(
    "list",
    help="List mods satisfying the requested conditions - useful for scripting",
    description="List mods satisfying the requested conditions. If no conditions are listed, all mods "
    "(regardless of status) are listed.",
)
sp_mod_list.add_argument(
    "-0",
    "--null-sep",
    help="List the mods with null separators.",
    action="store_true",
    dest="null_sep",
)
sp_mod_list.add_argument(
    "-i",
    "--installed",
    help="List installed mods",
    action="store_true",
)
sp_mod_list.add_argument(
    "-u",
    "--uninstalled",
    help="List uninstalled mods",
    action="store_true",
)


# Git
sp_git = sp_manager.add_parser(
    "git",
    help="Interact with the local dotfile Git repo",
    description="Interact with the local dotfile Git repo in $DOTFILES_DIR",
)
sp_git_manager = sp_git.add_subparsers(required=True, metavar="action", dest="action")

sp_git_commit = sp_git_manager.add_parser(
    "commit",
    help="Commit changes to managed dotfiles",
    description="Commit changes to managed dotfiles.",
)
sp_git_commit.add_argument(
    "-m",
    help="Commit message (optional)",
    required=False,
    dest="commit_message",
)

sp_git_push = sp_git_manager.add_parser(
    "push",
    help="Push changes to remote",
    description="Push changes to remote.",
)

sp_git_pull = sp_git_manager.add_parser(
    "pull",
    help="Stash changes in local repo, pull changes from remote, then unstash changes",
    description="Stash changes in local repo, pull changes from remote, then unstash changes.",
)

sp_git_undo = sp_git_manager.add_parser(
    "undo",
    help="Undo the last commit and unstage the previously committed files",
    description="Undo the last commit and unstage the previously committed files.",
)

sp_git_status = sp_git_manager.add_parser(
    "status",
    help="Get the current Git status of the local repo",
    description="Get the current Git status of the local repo.",
)

sp_git_diff = sp_git_manager.add_parser(
    "diff",
    help="Get the current Git diff of changed files",
    description="Get the current Git diff of changed files.",
)
sp_git_diff.add_argument(
    "-a",
    "--all",
    help="Include diff of non-dotfiles",
    action="store_true",
)
sp_git_diff.add_argument(
    "file",
    help="Relative path to the file (optional). If not given, the diff of all dotfiles will be shown.",
    choices=_available_dotfiles_choices,
    default=_available_dotfiles_choices.default,
    metavar="file",
    nargs="*",
)

# endregion

# region Handle arguments


def main():
    args = parser.parse_args()
    # args = parser.parse_args(['-h'])

    if args.zsh_completions:
        from dotmgr import compmaker  # noqa: I001

        print("Generating Zsh completions")
        compfile_path = HOME / ".oh-my-zsh/custom/completions/_dot"
        if not compfile_path.parent.exists():
            compfile_path.parent.mkdir()
        commands = compmaker.convert_from_parser(parser, cmd_name="dot")
        with open(compfile_path, "w+") as f:
            f.write(compmaker.render_zsh(commands))
        print(f"Saved completions to {compfile_path!s}. Reload shell to use them.")
        exit()
        return  # don't do anything after this

    if not args.sp:
        # print(parser.usage)
        # print(f"{parser.prog}: error: the following arguments are required: {parser._subparsers}")
        parser.error("the following arguments are required: command")
        exit(2)

    # Link
    if args.sp == "ln":
        for fn in args.file:
            if fn in ALL_DOTFILES.keys():
                dotfile = ALL_DOTFILES[fn]

                if fn not in AVAILABLE_DOTFILES.keys():
                    print(
                        f"Dotfile {fn} shouldn't be linked yet, since it's used by {dotfile.used_by}, which "
                        "isn't installed yet."
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
                        f"Dotfile {fn} shouldn't be removed yet, since it's used by {dotfile.used_by}, which "
                        "isn't installed yet."
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
                        f"Dotfile {fn} shouldn't be synced yet, since it's used by {dotfile.used_by}, which "
                        "isn't installed yet."
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
                    f"Heads up! Dotfile {fn} is used by installed mod {dotfile.used_by}, so unmanaging "
                    "probably isn't recommended. Continue anyways?"
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
                    f"Heads up! Dotfile {fn} is used by installed mod {dotfile.used_by}, so orphaning it is "
                    "risky. Continue anyways?"
                ):
                    continue

            dotfile.orphan()

            if not args.keep:
                print(f"Removing orphaned file {fn} from managed.files")
                if dotfile.src.is_dir():
                    shutil.rmtree(dotfile.src, )
                else:
                    dotfile.src.unlink()
                dotfile.prune_src()
                del ALL_DOTFILES[fn]

        filelib.update_managed_list(ALL_DOTFILES, DOTFILES_MANAGED_FILE)

    # List managed dotfiles in the format requested, limiting by status and/or availability (if requested)
    elif args.sp == "list":
        # If neither is given, make both true.
        if not args.linked and not args.unlinked:
            args.linked = True
            args.unlinked = True
            hide_link_mark = False
        else:
            hide_link_mark = True

        # If neither is given, make both true.
        if not args.available and not args.unavailable:
            args.available = True
            args.unavailable = True
            hide_avail_mark = False
        else:
            hide_avail_mark = True

        def make_format(installed: bool, available: bool, relative_path: str) -> str:
            """
            Format the line with the right marker. If it makes you feel any better, I hate the obnoxious
            if-tree too, but it was the cleanest way I could think of to implement this.
            """
            if hide_link_mark:
                if args.no_color:
                    if hide_avail_mark:
                        return relative_path
                    elif available:
                        return "+ " + relative_path
                    else:
                        return "- " + relative_path
                else:
                    if available:
                        return relative_path
                    else:
                        return outputs.AnsiColors.GREY + d.relative_path + outputs.AnsiColors.END
            else:
                mark = ""
                if args.no_color:
                    if installed:
                        mark += "✔"
                    else:
                        mark += "✘"
                    if hide_avail_mark:
                        pass
                    elif available:
                        mark += "+"
                    else:
                        mark += "-"
                    mark += " "
                    return mark + relative_path
                else:
                    if installed:
                        mark += outputs.AnsiColors.GREEN + "✔" + outputs.AnsiColors.END
                    else:
                        mark += outputs.AnsiColors.RED + "✘" + outputs.AnsiColors.END
                    if available:
                        return mark + " " + relative_path
                    else:
                        if hide_avail_mark:
                            return mark + " " + relative_path
                        else:
                            return (
                                mark + " " + outputs.AnsiColors.GREY + relative_path + outputs.AnsiColors.END
                            )

        # Only include files with the specified availability
        dotfiles: list[filelib.Dotfile] = []
        for d in ALL_DOTFILES.values():
            # Are we filtering ONLY available files?
            if args.available and not args.unavailable:
                # If so, is this dotfile used by a mod, and is that mod installed?
                if d.used_by and d.used_by.status == mods.InstallStatus.INSTALLED:
                    dotfiles.append(d)
                # Or, alternatively, is this mod unused?
                # Unused mods can't have availibility, so just include them.
                elif not d.used_by:
                    dotfiles.append(d)

            # Are we filtering ONLY unavailable files?
            elif not args.available and args.unavailable:
                # If so, is this dotfile used by a mod, and is that mod NOT installed?
                if d.used_by and d.used_by.status != mods.InstallStatus.INSTALLED:
                    dotfiles.append(d)
                # If this dotfile isn't used by a mod or is installed, skip it.
                else:
                    continue

            # Are both available AND unavailable files included, and is the dotfile NOT used by a mod?
            # If neither -a or -U are passed, both are assumed to be included.
            # Unused mods can't have availibility, so just include them.
            elif (args.available and args.unavailable) or not d.used_by:
                dotfiles.append(d)

        for d in dotfiles:
            if args.linked and d.is_linked():
                if args.raw:
                    print(d.relative_path, end="\0" if args.null_sep else "\n")
                else:
                    print(
                        make_format(
                            installed=True,
                            available=d in AVAILABLE_DOTFILES.values(),
                            relative_path=d.relative_path,
                        )
                    )
            elif args.unlinked and not d.is_linked():
                if args.raw:
                    print(d.relative_path, end="\0" if args.null_sep else "\n")
                else:
                    print(
                        make_format(
                            installed=False,
                            available=d in AVAILABLE_DOTFILES.values(),
                            relative_path=d.relative_path,
                        )
                    )

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
            print("WARN: $EDITOR variable is unset, and editor was not specified, so defaulted to `cat`.")
            editor = "cat"

        if args.file:
            dotfile = ALL_DOTFILES.get(args.file)
            # Safely assert here, as argparse makes sure the chosen dotfile is known and valid.
            if not dotfile:
                raise ValueError(dotfile)
            subprocess.run([editor, dotfile.src], check=True)
        else:
            subprocess.run([editor, DOTFILES_DIR], check=True)

    # Dump (cat) the contents of the dotfile to stdout
    elif args.sp == "cat":
        for fn in args.file:
            dotfile = ALL_DOTFILES[fn]
            with open(dotfile.src, 'r') as f:
                # Use sys.stdout.write instead of print, as print might mangle the contents a bit (like add
                # an extra newline at the end). `cat` does't do that, and we're emulating `cat`.
                sys.stdout.write(f.read())
        sys.stdout.flush()

    # Interact with mods
    elif args.sp in ["mod", "mods"]:
        # print(args)
        if args.mod_sp == "detect":
            for mod_name in args.mod_name:
                selected_mod = mods.__mods__.get(mod_name)
                if not selected_mod:
                    raise ValueError(f"Selected mod {mod_name} does not exist.")
                if selected_mod.status == mods.InstallStatus.INSTALLED:
                    print(
                        (
                            (outputs.AnsiColors.GREEN + "✔ " + outputs.AnsiColors.END)
                            if not args.no_color
                            else "✔ "
                        )
                        + selected_mod.mod_name
                    )
                elif selected_mod.status == mods.InstallStatus.INSTALL_FAILED:
                    print(
                        (
                            (outputs.AnsiColors.YELLOW + "~ " + outputs.AnsiColors.END)
                            if not args.no_color
                            else "~ "
                        )
                        + selected_mod.mod_name
                    )
                elif selected_mod.status == mods.InstallStatus.NOT_INSTALLED:
                    print(
                        (
                            (outputs.AnsiColors.RED + "✘ " + outputs.AnsiColors.END)
                            if not args.no_color
                            else "✘ "
                        )
                        + selected_mod.mod_name
                    )

        elif args.mod_sp == "install":
            for mod_name in args.mod_name:
                selected_mod = mods.__mods__.get(mod_name)
                if not selected_mod:
                    raise ValueError(f"Selected mod {mod_name} does not exist.")
                selected_mod.install()

        elif args.mod_sp == "list":
            list_installed = bool(args.installed)
            list_uninstalled = bool(args.uninstalled)
            if not list_installed and not list_uninstalled:
                list_installed = True
                list_uninstalled = True

            for mod in mods.__mods__.values():
                if list_installed and mod.status == mods.InstallStatus.INSTALLED:
                    print(mod.mod_name, end="\0" if args.null_sep else "\n")
                if list_uninstalled and mod.status != mods.InstallStatus.INSTALLED:
                    print(mod.mod_name, end="\0" if args.null_sep else "\n")

    # Interact with Git
    elif args.sp == "git":
        # upload, download, status
        if args.action == "commit":
            changed = git.get_changed_dotfiles()
            print(git.format_changed_human(*changed))

            # print("\nA commit message will automatically be generated.")
            if args.commit_message:
                msg = args.commit_message
            else:
                msg = git.generate_commit_message(*changed)
            print("\nCommit message:\n" + msg, end="\n\n")

            if outputs.confirm("Confirm commit?"):
                git.commit_dotfiles(*changed, msg)

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
                git.git_cmd("--no-pager diff -z --name-only HEAD HEAD~1", stdout=True).stdout[:-1].split("\0")
            )
            print("\n".join(changed_files), end="\n\n")

            if outputs.confirm("Undo last commit?"):
                git.git_cmd("reset --soft HEAD~1")
                git.git_cmd(["restore", "--staged", *changed_files])

        elif args.action == "status":
            changed = git.get_changed_dotfiles()
            print(git.format_changed_human(*changed))

        elif args.action == "diff":
            git.diff(args.file)


if __name__ == "__main__":
    main()

# endregion
