#!/usr/bin/env python3

import fdtools
import argparse
import os

import oh_my_zsh

# directory constants
HOME_DIR = fdtools.home()

# define the dotfiles directory based on the current working directory by default, but allow overrides.
DOTFILES_DIR = fdtools.pwd() if (overrideDotfilesDir := input(f'Dotfiles directory: [{fdtools.pwd()}] ')) == '' else overrideDotfilesDir

if not fdtools.isDir(DOTFILES_DIR):
	print('Dotfiles folder path is not a directory.')
	exit(1)


def fileSyncTuple(repoDir: fdtools.Directory, homeDir: fdtools.Directory, fileName: str) -> tuple[fdtools.File, fdtools.File]: 
	t: tuple[fdtools.File, fdtools.File]
	r = repoDir.findFile(fileName)
	if type(r) == None:
		raise FileNotFoundError(f'File "{fileName} not found in dotfiles repo.')
	else:
		h = fdtools.File(os.path.join(homeDir.path, fileName))
		t = (r, h) # type: ignore

	return t




def sync(files: list[str] = []):
	repo = fdtools.lsAll(DOTFILES_DIR)
	home = fdtools.lsAll(HOME_DIR)
	
	# link .bashrc
	bashrc = fileSyncTuple(repo, home, '.bashrc')
	fdtools.ln(bashrc[0], bashrc[1])

	# set up oh my zsh
	oh_my_zsh.setup(home)
	# link .zshrc and terse.zsh-theme
	zshrc = fileSyncTuple(repo, home, '.zshrc')
	terseZshTheme = fileSyncTuple(repo, home, '.oh-my-zsh/themes/terse.zsh-theme')

	fdtools.ln(zshrc[0], zshrc[1])
	fdtools.ln(terseZshTheme[0], terseZshTheme[1])

	return




def getArgs():
	parser = argparse.ArgumentParser(description='A (not so) simple helper tool to manage your dotfiles.')

	rootSubparser = parser.add_subparsers(required=True)
	
	syncParser = rootSubparser.add_parser('sync', aliases=['s'])
	syncParser.set_defaults(func=sync)

	syncParser.add_argument('-f', dest='files', required=False, help='File to sync (defaults to all files in the repo)')

	# syncArgs = syncParser.parse_args()
	args = parser.parse_args()
	return args



def main():
	a = getArgs()
	# execute the default function associated with the subparser
	a.func(a)


def _tc():
	repo = fdtools.lsAll(DOTFILES_DIR)
	# home = fdtools.lsAll(HOME_DIR)
	home = fdtools.Directory(HOME_DIR, leaveEmpty=True)
	
	# link .bashrc
	terseZshTheme = fileSyncTuple(repo, home, '.oh-my-zsh/themes/terse.zsh-theme')
	print(terseZshTheme)


if __name__ == '__main__':
	# main()
	_tc()