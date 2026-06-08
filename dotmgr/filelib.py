from pathlib import Path
from enum import Enum
import os
from dotmgr import HOME, DOTFILES_DIR
from dotmgr import mods
from dotmgr.mods.base import BaseMod
import shutil
import tempfile
from contextlib import AbstractContextManager
from typing import Union


class UnknownFileTypeError(FileExistsError):
    pass

class LogLevel(int, Enum):
    DEBUG = 4
    INFO = 3
    WARN = 2
    ERR = 1

class Dotfile:
    relative_path: Path
    src: Path
    dest: Path
    log_level: LogLevel
    logging_enabled: bool
    # is_managed: bool
    managed_by: Union[BaseMod, None]

    def __init__(self, relative_path: Path):
        self.relative_path = relative_path
        self.src = (DOTFILES_DIR / relative_path).resolve()
        self.dest = HOME / relative_path
        self.logging_enabled = True
        self.log_level = LogLevel.DEBUG
        # self.is_managed = self.relative_path in mods.__mod_dotfiles__.keys()
        self.managed_by = mods.__mod_dotfiles__.get(str(self.relative_path), None)

    def log(self, fname: str, level: LogLevel, message: str):
        if self.logging_enabled and level <= self.log_level:
            print(f"[Dotfile({self.relative_path}.{fname})]:{level.name} {message}")

    def rm(self) -> bool:
        """
        Attempts to remove the file at this Dotfile's destination (if one exists).

        :returns bool: True if file was removed successfully, False otherwise
        """

        if not self.dest.exists():
            self.log('rm', LogLevel.DEBUG, "dest doesn't exist, so there's nothing to remove.")
            return True
        
        elif self.dest.is_symlink():
            self.log('rm', LogLevel.WARN, "dest is a symlink, cautiously removing anyways")
            self.dest.unlink()
            return True
        
        elif self.dest.is_file():
            self.log('rm', LogLevel.WARN, "dest is a regular file, cautiously removing anyways")
            self.dest.unlink()
            return True
        
        elif self.dest.is_dir():
            self.log('rm', LogLevel.ERR, "dest is a directory, not removing")
            return False
        
        else:
            self.log('rm', LogLevel.ERR, f"I can't figure out what kind of file dest ({self.dest}) is somehow.")
            return False

        
    def ln(self):
        """
        Links the file.
        
        :returns bool: True if the file was linked successfully, False otherwise
        """

        if not self.dest.exists():
            self.log('ln', LogLevel.DEBUG, "dest does not exist and is not linked, linking")
            self.dest.symlink_to(self.src)
        elif self.dest.is_symlink():
            if self.dest.resolve() == self.src:
                # print(f"[Dotfile.ln] ")
                self.log('ln', LogLevel.DEBUG, "dest is already linked correctly, relinking")
                self.dest.unlink()
                self.dest.symlink_to(self.src)
            else:
                self.log('ln', LogLevel.ERR, f"{self.dest} is already a symlink, but does not point to the right file. It points to: '{self.dest.resolve()}'")
        elif self.dest.is_dir():
            self.log('ln', LogLevel.ERR, "dest exists and is a directory. You'll need to delete it manually before continuing.")
        elif self.dest.is_file():
            # print(f"[Dotfile.ln]:ERR {self.dest} exists and is a file. Remove it with the `rm()` function.")
            self.log('ln', LogLevel.ERR, 'dest exists and is a file. Remove it manually or with the `rm()` function before continuing.')

    def sync(self):
        self.log('sync', LogLevel.INFO, "Attempting to sync")

        self.log('sync', LogLevel.DEBUG, 'Attempting to remove existing link (if exists)')
        if self.rm():
            self.log('sync', LogLevel.DEBUG, "Removal succeeded, attempting to re-link")
            
            if self.ln():
                self.log('sync', LogLevel.INFO, "Sync succeeded")
            else:
                self.log('sync', LogLevel.ERR, 'Sync failed: Failed to re-link')
        
        else:
            self.log('sync', LogLevel.ERR, 'Sync failed: Failed to remove existing link (if exists)')



def load_dotfiles(managed_files_file: Path):
    # relative_paths: list[Path] = []
    dotfiles: dict[str, Dotfile] = {}

    with open(managed_files_file, 'r') as f:
        for line in f.readlines():
            line_stripped = line.strip()
            if line_stripped == '':
                continue
            else:
                dotfiles[line_stripped] = Dotfile(Path(line_stripped))

    return dotfiles


class cd(AbstractContextManager):
    """
    Context manager for changing the current working directory.

    Credit to Brian M. Hunt on StackOverflow (https://stackoverflow.com/a/13197763) for suggesting this, though *this* implementation is pretty much copy-and-pasted from the source code of contextlib.py from Python 3.13.
    """

    path: Path
    _old_cwd: list[Path]

    def __init__(self, path: Path):
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
    """

    path: Path

    def __init__(self):
        self.path = Path(tempfile.mkdtemp())
    
    def __enter__(self):
        return self.path
    
    def __exit__(self, *excinfo):
        shutil.rmtree(self.path)
