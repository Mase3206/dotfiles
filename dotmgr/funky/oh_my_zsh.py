from fdtools import Directory, File
import subprocess

CONFIG_MODULE = 'oh-my-zsh'
REQUIRES = ['zsh']


def isInstalled(homedir: Directory) -> bool:
	"""
	Checks if Oh My Zsh files are present in the user's home directory.
	"""

	r = homedir.findDir('.oh-my-zsh')
	if r == None:
		return False
	else:
		return True


def setup(homedir: Directory):
	import zsh

	if not zsh.isInstalled():
		zsh.setup(homedir)

	subprocess.run('curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh > install.sh')
	subprocess.run('sh install.sh --unattended')
	subprocess.run('chsh -s /bin/zsh $(id -un)')
	


# def _tc():
# 	home = lsAll('/Users/noahroberts')
# 	print(isInstalled(home))

# if __name__ == '__main__':
# 	_tc()