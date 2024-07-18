#!/usr/bin/env python3

import os

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