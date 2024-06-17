#!/usr/bin/env python3

import argparse
import sys



def CliList(value: str):
	"""
	A custom callable that will automatically convert a comma-separated string given used in the command line into a Python list.
	"""
	rawValues = value.split(',')
	nonWhitespaceValues = [v for v in rawValues if v != '']
	return nonWhitespaceValues




def dotFormat(files):
	for i in range(len(files)):
		files[i] = files[i] if files[i][0] == '.' else f'.{files[i]}'
	return files



def dotImport(args: argparse.Namespace):
	files = args.file
	print(files)



def dotLink(args: argparse.Namespace):
	files = args.file
	print(files)



def init():
	parser = argparse.ArgumentParser(
		description="A quick helper program to make importing and linking dotfiles between this repo and the user's home folder."
	)

	# global options
	parser.add_argument(
		'-v', 
		help='verbose output', 
		action='store_true'
	)

	# initialize subparser controller
	subController = parser.add_subparsers()

	# `import` arguments
	importParser = subController.add_parser(
		'import', 
		help='import <file[,...]>'
	)
	importParser.set_defaults(func=dotImport)

	importParser.add_argument(
		'file', 
		help='name of file or files to import. A dot will automatically be added to file name if not present. Multiple files must be separated by a comma only', 
		metavar='file_or_files',
		type=CliList
		# required=True
	)
	importParser.add_argument(
		'--disable-auto-dot', 
		help='disable default behavior of automatically adding a dot to a file name if missing', 
		action='store_true'
	)
	

	# `link` arguments
	linkParser = subController.add_parser(
		'link', 
		help='link [file[,...]]'
	)
	linkParser.set_defaults(func=dotLink)

	linkParser.add_argument(
		'-x', help='exlude specified files', 
		action='store_true', 
		dest='exclude'
	)
	linkParser.add_argument(
		'file',
		help='name of file or files to link. A dot will automatically be added to file name if not present. Multiple files must be separated by a comma only', 
		metavar='file_or_files', 
		default=[],
		# required='-x' in sys.argv,  # if `-x` is passed, specifying files is required
		type=CliList,
	)

	# parse dem arguments
	args = parser.parse_args()
	args.func(args)


init()
