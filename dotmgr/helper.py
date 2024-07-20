#!/usr/bin/env python3

import fdtools
import argparse
import funky
import os

import funky.oh_my_zsh




def sync(files: list[str] = []):
	repo = fdtools.lsAll(DOTFILES_DIR)
	home = fdtools.lsAll(HOME_DIR)
	
	# link .bashrc
	bashrc = (
		repo.findFile('.bashrc'),
		fdtools.File(os.path.join(home.path, '.bashrc'))
	)
	fdtools.ln(bashrc[0], bashrc[1])

	# set up oh my zsh
	funky.oh_my_zsh.setup(home)
	# link .zshrc and terse.zsh-theme
	zshrc = (
		repo.findFile('.zshrc'),
		fdtools.File(os.path.join(home.path, '.zshrc'))
	)
	terseZshTheme = (
		repo.findFile('files/.oh-my-zsh/themes/terse.zsh-theme'),
		fdtools.File(os.path.join(home.path, '.oh-my-zsh', 'themes', 'terse.zsh-theme'))
	)
	fdtools.ln(zshrc[0], zshrc[1])
	fdtools.ln(terseZshTheme[0], terseZshTheme[1])





def init():
	global HOME_DIR, DOTFILES_DIR
	# directory constants
	HOME_DIR = fdtools.home()

	# define the dotfiles directory based on the current working directory by default, but allow overrides.
	DOTFILES_DIR = fdtools.pwd() if (overrideDotfilesDir := input(f'Dotfiles directory: [{fdtools.pwd()}] ')) == '' else overrideDotfilesDir

	if not fdtools.isDir(DOTFILES_DIR):
		print('Dotfiles folder path is not a directory.')
		exit(1)



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
	init()
	a = getArgs()
	# execute the default function associated with the subparser
	a.func(a)


if __name__ == '__main__':
	main()