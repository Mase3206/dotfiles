#!/usr/bin/env python3

import os


class NonAbsolutePathException(Exception):
	pass


class File:
	def __init__(self, path: str):
		self.path = path
		self.basename = os.path.basename(self.path)

	
	def __repr__(self):
		return f"File(path='{self.path}')"



class Directory:
	def __init__(self, path: str):
		self.path = path
		self.files: list[File] = self._lsFiles()
		self.dirs: list[Directory] = self._lsDirs()


	def _lsFiles(self) -> list[File]:
		try:
			# return a list of all FILES in the given path
			filePaths = [entry for entry in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, entry))]

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

	
	def find(self, basename: str = '', relativePath: str = '') -> File | None:
		if len(self.dirs) == 0:
			return None
		elif basename != '':
			# search in this directory first
			for f in self.files:
				if f.basename == basename:
					return f
			
			# the search recursively in subdirectories
			for d in self.dirs:
				result = d.find(basename=basename, relativePath=relativePath)
				if result == None:
					continue
				else:
					return result




	# special methods
	def __repr__(self):
		return f"\nDirectory(path='{self.path}', files={self.files}, dirs={self.dirs})"
		





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



def ln(source: str, dest: str, symbolic: bool = True):
	"""
	Create a link (default symbolic) from the source path to the destination path. All paths must be absolute!
	"""

	if source[0] != '/' or dest[0] != '/':
		raise NonAbsolutePathException(f'Given source or destination path is not an absolute path.')
	
	if symbolic:
		os.symlink(source, dest)
	else:
		os.link(source, dest)




def _tc():
	d = lsAll('/Users/noahroberts/Github/dotfiles')
	print(d)

if __name__ == '__main__':
	_tc()
