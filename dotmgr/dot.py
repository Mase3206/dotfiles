#!/usr/bin/python

import argparse
from dotmgr import mods, filelib, DOTFILES_DIR, DOTFILES_MANAGED_FILE
from dotmgr.mods import InstallStatus


ALL_DOTFILES = filelib.load_dotfiles(DOTFILES_MANAGED_FILE)
AVAILABLE_DOTFILES = [
    name for name, d in ALL_DOTFILES.items()
    if not d.managed_by or d.managed_by.status == InstallStatus.INSTALLED
]


parser = argparse.ArgumentParser()
sp_manager = parser.add_subparsers(required=True, metavar='command', dest='sp')

sp_ln = sp_manager.add_parser('ln', help='Link dotfiles', epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR')
sp_ln.add_argument('file', nargs='*', help='(Optional) relative path to file(s) to link. If not given, all files will be linked.', default=AVAILABLE_DOTFILES)

sp_rm = sp_manager.add_parser('rm', help='Remove dotfiles', epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR')
sp_rm.add_argument('file', nargs="+", help='Relative path to file(s) to remove.')

sp_sync = sp_manager.add_parser('sync', help='Sync dotfiles', epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR')
sp_sync.add_argument('file', nargs='*', help='(Optional) relative path to file(s) to sync. If not given, all files will be synced.', default=AVAILABLE_DOTFILES)

sp_adopt = sp_manager.add_parser('adopt', help='Adopt local dotfile to dotfile repo', epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR')
sp_adopt.add_argument('file', nargs='+', help='Relative path to the file(s) to adopt')

sp_desync = sp_manager.add_parser('desync', help='De-sync one or more dotfiles. This converts a once synced dotfile to a local-only dotfile.', epilog='NOTE: "relative paths" are relative to the dotfiles directory $DOTFILES_DIR')
sp_desync.add_argument('file', nargs='+', help='Relative path to the file(s) to desync')

sp_mod = sp_manager.add_parser('mod', help='Manage mods')
sp_mod.add_argument('action', choices=('install', 'detect'), help='Action')
sp_mod.add_argument('mod_name', choices=mods.__mods__.keys(), help='Mod name')

sp_git = sp_manager.add_parser('git', help="Interact with the dotfile Git repo")
sp_git.add_argument('action', choices=('pull', 'push', 'reset', 'commit', 'update'), help='Git subcommand/action')
sp_git.add_argument('message', nargs="?", type=str, help="Git commit message (optional)")



args = parser.parse_args()
print(args)

# print(filelib.load_dotfiles(DOTFILES_MANAGED_FILE))