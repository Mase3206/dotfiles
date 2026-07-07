import os
import shutil
import tempfile
from contextlib import AbstractContextManager
from pathlib import Path


class cd(AbstractContextManager):
    """
    Context manager for changing the current working directory.

    Credit to Brian M. Hunt on StackOverflow (https://stackoverflow.com/a/13197763) for suggesting this,
    though *this* implementation is pretty much copy-and-pasted from the source code of contextlib.py
    from Python 3.13.

    :param Path path: Path to the directory to enter
    """

    path: Path
    _old_cwd: list[Path]

    def __init__(self, path: Path):
        """
        Initialize a new `cd` context manager.
        """
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(Path.cwd())
        os.chdir(self.path)
        return self.path

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())


class mktemp(AbstractContextManager):
    """
    Context manager for creating a new temporary directory and removing it once finished.

    :param Path path: Path to the temporary directory
    """

    path: Path

    def __init__(self):
        """
        Initialize a new `mktemp` context manager by creating a new temporary folder and saving its path.
        """
        self.path = Path(tempfile.mkdtemp())

    def __enter__(self):
        return self.path

    def __exit__(self, *excinfo):
        """Delete the temporary directory and its contents."""
        shutil.rmtree(self.path)
