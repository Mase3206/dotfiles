#!/usr/bin/python

import argparse
from dotmgr import mods, filelib, DOTFILES_MANAGED_FILE
from dotmgr.mods import InstallStatus


ALL_DOTFILES = filelib.load_dotfiles(DOTFILES_MANAGED_FILE)
AVAILABLE_DOTFILES = {
    name: d
    for name, d in ALL_DOTFILES.items()
    if not d.used_by or d.used_by.status == InstallStatus.INSTALLED
}

# region Define arguments
parser = argparse.ArgumentParser()
sp_manager = parser.add_subparsers(required=True, metavar="command", dest="sp")

sp_ln = sp_manager.add_parser(
    "ln",
    help="Link dotfiles",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_ln.add_argument(
    "file",
    nargs="*",
    help="(Optional) relative path to file(s) to link. If not given, all files (except those used by uninstalled Mods) will be linked.",
    default=AVAILABLE_DOTFILES.keys(),
)

sp_rm = sp_manager.add_parser(
    "rm",
    help="Remove dotfiles",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_rm.add_argument("file", nargs="+", help="Relative path to file(s) to remove.")

sp_sync = sp_manager.add_parser(
    "sync",
    help="Sync dotfiles",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_sync.add_argument(
    "file",
    nargs="*",
    help="(Optional) relative path to file(s) to sync. If not given, all files (except those used by uninstalled Mods) will be synced.",
    default=AVAILABLE_DOTFILES.keys(),
)

sp_adopt = sp_manager.add_parser(
    "adopt",
    help="Adopt local dotfile to dotfile repo",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_adopt.add_argument("file", nargs="+", help="Relative path to the file(s) to adopt")

sp_desync = sp_manager.add_parser(
    "orphan",
    help="Orphan one or more dotfiles. This converts a once synced dotfile to a local-only dotfile.",
    epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR',
)
sp_desync.add_argument("file", nargs="+", help="Relative path to the file(s) to orphan")

sp_mod = sp_manager.add_parser("mod", help="Manage mods")
sp_mod.add_argument("action", choices=("install", "detect"), help="Action")
sp_mod.add_argument("mod_name", choices=mods.__mods__.keys(), help="Mod name")

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

elif args.sp == "sync":
    for fn in args.file:
        if fn in ALL_DOTFILES.keys():
            dotfile = ALL_DOTFILES[fn]

            if fn not in AVAILABLE_DOTFILES.keys():
                print(
                    f"Dotfile {fn} shouldn't be removed yet, since it's used by {dotfile.used_by}, which isn't installed yet."
                )
                continue

            dotfile.sync()

elif args.sp == "adopt":
    raise NotImplementedError("Dotfile adoption is not yet implemented.")

elif args.sp == "orphan":
    raise NotImplementedError("Dotfile orphaning is not yet implemented.")

elif args.sp == "mod":
    mod_name: str = args.mod_name
    selected_mod = mods.__mods__.get(mod_name)
    if not selected_mod:
        raise ValueError(f"Selected mod {mod_name} does not exist.")

    if args.action == "detect":
        selected_mod.detect()
    elif args.action == "install":
        selected_mod.install()

elif args.sp == "git":
    raise NotImplementedError("The Git wrapper is not yet implemented.")
