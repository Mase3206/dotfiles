from fdtools import Directory, File
import shutil

CONFIG_MODULE = 'zsh'




def isInstalled() -> bool:
	"""
	Checks if Zsh is installed. Returns True if it is, False otherwise.
	"""

	if shutil.which('zsh') == '':
		return False
	else:
		return True
	


def setup(homedir: Directory):
	print('Please install Zsh manually before continuing. Automated installation is currently out of development scope.')
	exit(1)