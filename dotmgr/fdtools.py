#!/usr/bin/env python3

from __future__ import annotations
import os


class NonAbsolutePathException(Exception):
	pass


class File:
	def __init__(self, path: str):
		self.path = path
		self.basename = os.path.basename(self.path)

	
	def __repr__(self):
		return f"File(path='{self.path}', basename='{self.basename}')"



class Directory:
	def __init__(self, path: str):
		self.path = path
		self.basename = os.path.basename(self.path)
		self.files: list[File] = self._lsFiles()
		self.dirs: list[Directory] = self._lsDirs()


	def _lsFiles(self) -> list[File]:
		try:
			# return a list of all FILES in the given path
			filePaths = [os.path.join(self.path, entry) for entry in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, entry))]

			return [File(fp) for fp in filePaths]
		
		except FileNotFoundError:
			return []
		
	
	def _lsDirs(self): # type: ignore
		directories: list[Directory] = []

		try:
			dirPaths = [entry for entry in os.listdir(self.path) if os.path.isdir(os.path.join(self.path, entry))]
		except FileNotFoundError:
			return [] # type: ignore
		
		for dp in dirPaths:
			directories.append(Directory(os.path.join(self.path, dp)))
		
		return directories

	
	def findFile(self, path_or_basename: str, basename: str = '', relativePath: str = '') -> File | None:
		# autodetect if path or basename
		if '/' in list(path_or_basename):
			relativePath = path_or_basename
			basename = ''
		else:
			relativePath = ''
			basename = path_or_basename

		# probably un-necessary
		if len(self.dirs) == 0 and len(self.files) == 0:
			return None
		
		elif basename != '' and relativePath == '':
			# search in this directory first
			for f in self.files:
				if f.basename == basename:
					return f
			
			# the search recursively in subdirectories
			for d in self.dirs:
				result = d.findFile(basename)
				if result == None:
					continue
				else:
					return result
				
			# will only be run if nothing is found recursively
			return None
				
		elif basename == '' and relativePath != '':
			pathParts = relativePath.split('/')

			for d in self.dirs:
				if d.basename == pathParts[0]:
					if len(pathParts) <= 2:
						result = d.findFile(pathParts[1])
					else:
						result = d.findFile('/'.join(pathParts[1:]))

					if result == None:
						continue
					else:
						return result
				# else:
				# 	return self.findFile(relativePath=relativePath)
					
			# will only be run if nothing is found recursively
			return None
		

	def findDir(self, path_or_basename: str) ->  Directory | None:
		"""
		Recursively find the specified directory.
		"""

		# autodetect if path or basename
		if '/' in list(path_or_basename):
			relativePath = path_or_basename
			basename = ''
		else:
			relativePath = ''
			basename = path_or_basename

		# probably un-necessary
		if len(self.dirs) == 0:
			return None
		
		elif basename != '' and relativePath == '':
			# search in this directory first
			for d in self.dirs:
				if d.basename == basename:
					return d
			
			# the search recursively in subdirectories
			for d in self.dirs:
				result = d.findDir(basename)
				if result == None:
					continue
				else:
					return result
				
			# will only be run if nothing is found recursively
			return None
				
		elif basename == '' and relativePath != '':
			pathParts = relativePath.split('/')

			for d in self.dirs:
				if d.basename == pathParts[0]:
					if len(pathParts) <= 2:
						result = d.findDir(pathParts[1])
					else:
						result = d.findDir('/'.join(pathParts[1:]))

					if result == None:
						continue
					else:
						return result
					
			# will only be run if nothing is found recursively
			return None


	# special methods
	def __repr__(self):
		return f"Directory(path='{self.path}', files={self.files}, dirs={self.dirs})"
		





def pwd() -> str:
	"""
	Get the current working directory and return its absolute path.
	"""

	return os.getcwd()


def home() -> str:
	"""
	Get the current user's home directory and return its absolute path.
	"""

	return os.path.expanduser('~')


def isDir(path: str) -> bool:
	"""
	Check if the given path points to a directory.
	Return True if it is a directory, False otherwise.
	"""

	return os.path.isdir(path)


def lsAll(path: str):
	"""
	Return all items (including hidden ones) in the given directory path as a list.
	"""

	return Directory(path)



def ln(source: File, dest: File, symbolic: bool = True, rmIfExists: bool = True):
	"""
	Create a link (default symbolic) from the source path to the destination path. All paths must be absolute!
	"""
	
	if os.path.isfile(dest.path) or os.path.islink(dest.path):
		os.remove(dest.path)

	if symbolic:
		os.symlink(source.path, dest.path)
	else:
		os.link(source.path, dest.path)






def _tc():
	d = lsAll('/Users/noahroberts/Github/dotfiles')
	print(d.findFile('.zshrc'))
	print(d.findFile('files/.oh-my-zsh/themes/terse.zsh-theme'))
	print(d.findDir('.oh-my-zsh'))
	print(d.findDir('files/.oh-my-zsh/themes'))

if __name__ == '__main__':
	_tc()
