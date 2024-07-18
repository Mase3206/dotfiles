#!/usr/bin/env python3

import fdtools


# directory constants
HOME = fdtools.home()

# define the dotfiles directory based on the current working directory by default, but allow overrides.
DOTFILES_DIR = fdtools.pwd() if (overrideDotfilesDir := input(f'Dotfiles directory: [{fdtools.pwd()}] ')) == '' else overrideDotfilesDir

if not fdtools.isDir(DOTFILES_DIR):
	print('Dotfiles folder path is not a directory.')
	exit(1)



print(HOME)
print(DOTFILES_DIR)
