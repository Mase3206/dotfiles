#!/usr/bin/env python3

import fdtools
import argparse

# global HOME, DOTFILES_DIR



def sync(files: list[str] = []):
	allFiles = fdtools.lsAll(DOTFILES_DIR)
	# print(allFiles)
	print(allFiles.findFile(relativePath='files/.oh-my-zsh/themes/terse.zsh-theme'))



def init():
	global HOME, DOTFILES_DIR
	# directory constants
	HOME = fdtools.home()

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
	args = parser.parse_args('s'.split())
	return args



def main():
	init()
	a = getArgs()
	# execute the default function associated with the subparser
	a.func(a)


if __name__ == '__main__':
	main()