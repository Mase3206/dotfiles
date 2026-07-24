from __future__ import annotations

import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Union

from dotmgr import DOTFILES_DIR, HOME, mods, outputs
from dotmgr.mods.base import BaseMod


class UnknownFileTypeError(FileExistsError):
    pass


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERR = "ERR"
    CRITICAL = "CRITICAL"

    def __int__(self) -> int:
        mapping = {"DEBUG": 1, "INFO": 2, "WARN": 3, "ERR": 4, "CRITICAL": 5}
        return mapping[self.name]

    def __gt__(self, other: LogLevel) -> bool:
        return int(self) > int(other)

    def __lt__(self, other: LogLevel) -> bool:
        return int(self) < int(other)

    def __eq__(self, other: LogLevel) -> bool:
        return int(self) == int(other)


class Dotfile:
    """
    A managed dotfile.

    :param Path src: Absolute path to the actual file in $DOTFILES_DIR
    :param Path dest: Absolute path to the link destination in $HOME
    :param LogLevel log_level: What log level to use when logging file operations on this dotfile
    :param bool logging_enabled: Whether logging is actually enabled
    :param BaseMod | None used_by: The Mod which uses this dotfile. This field is automatically set.
    """

    _raw_relative_path: str
    """
    [PRIVATE] A string containing the relative path to this dotfile. Use
    :attr:`relative_path` instead.
    """
    src: Path
    dest: Path
    log_level: LogLevel
    logging_enabled: bool
    used_by: Union[BaseMod, None]

    def __init__(self, relative_path: Path):
        """
        Create a new Dotfile object.

        :param Path relative_path: Path to the dotfile, relative to $DOTFILES_DIR (and thus also $HOME)
        """

        self.relative_path = relative_path
        self.src = (DOTFILES_DIR / relative_path).resolve()
        self.dest = HOME / relative_path
        self.logging_enabled = True
        try:
            self.log_level = LogLevel(os.environ.get("DOTFILES_LOGLEVEL", "WARN").upper())
        except ValueError:
            # default to WARN if bad log level is given
            self.log_level = LogLevel("WARN")

        self.used_by = mods.__mod_dotfiles__.get(str(self.relative_path), None)

    def __str__(self) -> str:
        return str(self.relative_path)

    def __repr__(self) -> str:
        return f"Dotfile({self.relative_path})"

    @property
    def relative_path(self) -> str:
        """The path of this dotfile relative to $DOTFILES_DIR (and thus also $HOME)."""
        return self._raw_relative_path

    @relative_path.setter
    def relative_path(self, path: Union[Path, str]):
        """
        :param Path | str path: Path relative to $DOTFILES_DIR (and thus also $HOME)
        """
        if isinstance(path, Path):
            if path.is_absolute():
                try:
                    path = path.relative_to(HOME)
                except ValueError:
                    self.log(
                        "relative_path",
                        LogLevel.ERR,
                        f"Given relative path {path!s} is absolute but not in '{HOME}'",
                    )
            is_dir = path.is_dir()
            path = str(path)
        else:
            is_dir = Path(path).is_dir()

        self._raw_relative_path = path + ("/" if is_dir else "")

    def is_linked(self):
        """
        Is this file linked correctly?

        :returns bool: True if the file is linked correctly, False otherwise
        """
        if self.src.is_dir():
            return (
                self.dest.exists()
                and self.dest.is_dir()
                and self.dest.is_symlink()
                and self.dest.resolve() == self.src
            )
        else:
            return (
                self.dest.exists()
                and self.dest.is_file()
                and self.dest.is_symlink()
                and self.dest.resolve() == self.src
            )

    def log(self, fname: str, level: LogLevel, message: str):
        """
        Use the logger to log a message to stdout via `print`.

        If the specified log level is lower than the log level set when this Dotfile was initialized, the
        message will not be logged.

        :param str fname: Function name
        :param LogLevel level: Log level of this message
        :param str message: Log message
        """
        if self.logging_enabled and level >= self.log_level:
            print(f"{level.name:>5}  [Dotfile('{self.relative_path}').{fname}]: {message}")

    def rm(self) -> bool:
        """
        Attempts to remove the file at this Dotfile's destination (if one exists).

        :returns bool: True if file was removed successfully, False otherwise
        """

        if not self.dest.exists():
            self.log(
                "rm",
                LogLevel.DEBUG,
                "dest doesn't exist, so there's nothing to remove.",
            )
            return True

        elif self.dest.is_symlink():
            self.log("rm", LogLevel.WARN, "dest is a symlink, cautiously removing anyways")
            self.dest.unlink()
            return True

        elif self.dest.is_file():
            self.log(
                "rm",
                LogLevel.WARN,
                "dest is a regular file, making a backup before removing",
            )
            shutil.copyfile(self.dest, str(self.dest) + ".bak")
            self.dest.unlink()
            return True

        # elif self.dest.is_dir():
        #     self.log("rm", LogLevel.ERR, "dest is a directory, not removing")
        #     return False
        elif self.dest.is_dir():
            self.log(
                "rm",
                LogLevel.WARN,
                "dest is a directory, making a backup before removing",
            )
            shutil.copytree(self.dest, str(self.dest) + ".bak")
            shutil.rmtree(self.dest)
            return True

        else:
            self.log(
                "rm",
                LogLevel.ERR,
                f"I can't figure out what kind of file dest ({self.dest}) is somehow.",
            )
            return False

    def ln(self) -> bool:
        """
        Links the file.

        :returns bool: True if the file was linked successfully, False otherwise
        """

        if not self.dest.exists():
            self.log("ln", LogLevel.DEBUG, "dest does not exist and is not linked, linking")
            # Create parent directory of dest if it doesn't exist
            if not self.dest.parent.exists():
                self.log(
                    "ln",
                    LogLevel.DEBUG,
                    "Parent dir of dest does not exist, creating recursively",
                )
                self.dest.parent.mkdir(parents=True)
            self.dest.symlink_to(self.src)
            return True
        elif self.dest.is_symlink():
            if self.dest.resolve() == self.src:
                # print(f"[Dotfile.ln] ")
                self.log("ln", LogLevel.DEBUG, "dest is already linked correctly, relinking")
                self.dest.unlink()
                self.dest.symlink_to(self.src)
                return True
            else:
                self.log(
                    "ln",
                    LogLevel.ERR,
                    f"{self.dest} is already a symlink, but does not point to the right file. It points "
                    f"to: '{self.dest.resolve()}'",
                )
                return False
        # elif self.dest.is_dir():
        #     self.log(
        #         "ln",
        #         LogLevel.ERR,
        #         "dest exists and is a directory. You'll need to delete it manually before continuing.",
        #     )
        #     return False
        elif self.dest.is_dir():
            self.log(
                "ln",
                LogLevel.WARN,
                "dest exists and is a directory. Remove it manually or with the `rm()` function before "
                "continuing.",
            )
            return False
        elif self.dest.is_file():
            # print(f"[Dotfile.ln]:ERR {self.dest} exists and is a file. Remove it with the `rm()` function.")
            self.log(
                "ln",
                LogLevel.ERR,
                "dest exists and is a file. Remove it manually or with the `rm()` function before "
                "continuing.",
            )
            return False
        else:
            self.log(
                "rm",
                LogLevel.ERR,
                f"I can't figure out what kind of file dest ({self.dest}) is somehow.",
            )
            return False

    def sync(self) -> bool:
        """
        Sync this dotfile.

        First, unlink or remove the existing file with :meth:`rm`. Then, link it with
        :func:`ln`.
        """
        self.log("sync", LogLevel.INFO, "Attempting to sync")

        self.log("sync", LogLevel.DEBUG, "Attempting to remove existing link (if exists)")
        if self.rm():
            self.log("sync", LogLevel.DEBUG, "Removal succeeded, attempting to re-link")

            if self.ln():
                self.log("sync", LogLevel.INFO, "Sync succeeded")
                return True
            else:
                self.log("sync", LogLevel.ERR, "Sync failed: Failed to re-link")
                return False

        else:
            self.log(
                "sync",
                LogLevel.ERR,
                "Sync failed: Failed to remove existing link (if exists)",
            )
            return False

    def adopt(self) -> bool:
        """
        Move dest to src, then link src to dest.

        :return bool: True if success, False otherwise.
        """
        self.log("adopt", LogLevel.INFO, "Attempting to adopt")

        if not self.dest.exists():
            self.log("adopt", LogLevel.ERR, "Target file does not exist, can't adopt")
            return False
        elif self.dest.is_symlink():
            # if outputs.confirm(f"File '{self.dest.resolve()}' is a symlink. ")
            self.log(
                "adopt",
                LogLevel.ERR,
                "Dest is a symlink, can't adopt. Run `sync` to fix",
            )
            return False
        # elif self.dest.is_dir():
        #     self.log("adopt", LogLevel.ERR, "Target is a folder, refusing to adopt")
        #     return False
        elif self.dest.is_dir():
            self.log(
                "adopt",
                LogLevel.DEBUG,
                "Target is a folder, moving to dotfiles folder and linking",
            )
            self.dest.rename(self.src)
            if self.ln():
                self.log("adopt", LogLevel.INFO, "Adopt succeeded")
                return True
            else:
                self.log("adopt", LogLevel.ERR, "Adopt failed: Failed to relink")
                return False
        elif self.dest.is_file():
            self.log(
                "adopt",
                LogLevel.DEBUG,
                "Target is a regular file, moving to dotfiles folder and linking",
            )
            if not self.src.parent.exists():
                self.log(
                    "adopt",
                    LogLevel.DEBUG,
                    "Parent dir of src does not exist, creating recursively",
                )
                self.src.parent.mkdir(parents=True)
            self.dest.rename(self.src)
            if self.ln():
                self.log("adopt", LogLevel.INFO, "Adopt succeeded")
                return True
            else:
                self.log("adopt", LogLevel.ERR, "Adopt failed: Failed to relink")
                return False
        else:
            self.log(
                "rm",
                LogLevel.ERR,
                f"I can't figure out what kind of file dest ({self.dest}) is somehow.",
            )
            return False

    def orphan(self) -> bool:
        """
        Copy src to dest, deleting dest symlink if necessary.

        :return bool: True if successfully orphaned, False otherwise
        """

        self.log("orphan", LogLevel.INFO, "Attempting to orphan")

        if not self.src.exists():
            self.log(
                "orphan",
                LogLevel.ERR,
                "Can't orphan dotfile from src that doesn't exist in dotfiles repo",
            )
            return False
        elif self.src.is_symlink():
            self.log(
                "orphan",
                LogLevel.CRITICAL,
                f"Source is a symlink, which is {outputs.AnsiColors.BOLD}{outputs.AnsiColors.RED}very "
                f"bad{outputs.AnsiColors.END}!!! Sources should {outputs.AnsiColors.BOLD}never"
                f"{outputs.AnsiColors.END} be symlinks!",
            )
            return False
        # elif self.src.is_dir():
        #     self.log("orphan", LogLevel.ERR, "Source is a folder, refusing to orphan")
        #     return False
        elif self.src.is_dir():
            self.log("orphan", LogLevel.WARN, "Source is a folder, orphaning anyway")
            if not self.rm():
                self.log("orphan", LogLevel.ERR, "Failed to remove dest")
                return False
            shutil.copytree(self.src, self.dest)
            if self.dest.exists() and not self.dest.is_symlink():  # success
                self.log("orphan", LogLevel.INFO, "Orphan succeeded")
                return True
            else:
                self.log(
                    "orphan",
                    LogLevel.INFO,
                    "Orphan failed: Dest still doesn't exist or wasn't moved correctly",
                )
                return False

        elif self.dest.exists() and not self.dest.is_symlink():
            self.log(
                "orphan",
                LogLevel.ERR,
                "Dest already exists and isn't a symlink, can't orphan",
            )
            return False
        elif self.dest.is_symlink() and self.dest.resolve() != self.src:
            self.log(
                "orphan",
                LogLevel.ERR,
                f"Dest is a symlink, but links to {self.dest.resolve()}. Fix link with `sync` first",
            )
            return False
        elif self.dest.is_symlink() and self.dest.resolve() == self.src:
            self.log(
                "orphan",
                LogLevel.DEBUG,
                "Dest is linked correctly, proceeding with orphaning",
            )
            if not self.rm():
                self.log("orphan", LogLevel.ERR, "Failed to remove dest")
                return False
            shutil.copyfile(self.src, self.dest)
            if self.dest.exists() and not self.dest.is_symlink():  # success
                self.log("orphan", LogLevel.INFO, "Orphan succeeded")
                return True
            else:
                self.log(
                    "orphan",
                    LogLevel.INFO,
                    "Orphan failed: Dest still doesn't exist or wasn't moved correctly",
                )
                return False
        elif not self.dest.exists():
            self.log(
                "orphan",
                LogLevel.DEBUG,
                "Dest doesn't exist, proceeding with orphaning",
            )
            shutil.copyfile(self.src, self.dest)
            if self.dest.exists() and not self.dest.is_symlink():  # success
                self.log("orphan", LogLevel.INFO, "Orphan succeeded")
                return True
            else:
                self.log(
                    "orphan",
                    LogLevel.INFO,
                    "Orphan failed: Dest still doesn't exist or wasn't moved correctly",
                )
                return False
        else:
            self.log(
                "rm",
                LogLevel.ERR,
                f"I can't figure out what kind of files src ({self.src}) and dest ({self.dest}) are somehow.",
            )
            return False

    def prune_src(self):
        """
        If parent directory of source file (the "real" file in $DOTFILES_DIR) is empty, remove it (and its
        parent(s), if applicable).

        :raises FileExistsError: If the "real" source file still exists in $DOTFILES_DIR
        """

        # Make sure the source doesn't exist before continuing.
        if self.src.exists():
            raise FileExistsError(
                f"{self.relative_path} still exists in $DOTFILES_DIR, refusing to prune its parent dir(s)."
            )

        parent = self.src.parent
        while True:
            if not any(parent.iterdir()):  # is empty?
                parent.rmdir()
                parent = parent.parent
            else:
                break


def load_dotfiles(managed_files_file: Path):
    """
    Load managed dotfiles from the managed.files file.

    :param Path managed_files_file: Path to the managed.files file
    :returns dict[str, Dotfile]: Dictionary of managed dotfiles, where the key is the relative path
    """

    dotfiles: dict[str, Dotfile] = {}

    with open(managed_files_file, "r") as f:
        for line in f.readlines():
            line_stripped = line.strip()
            if line_stripped == "":
                continue
            else:
                dotfiles[line_stripped] = Dotfile(Path(line_stripped))

    return dotfiles


def update_managed_list(
    dotfiles: Union[list[Dotfile], dict[str, Dotfile]],
    managed_files_file: Path,
):
    """
    Mark the given dotfiles as managed by listing them in managed.files.

    :param list[Dotfile] | dict[str, Dotfile] dotfiles: Dotfiles to mark as managed. If dict, the keys must
        be the relative paths of the dotfiles.
    :param Path managed_files_file: Path to the managed.files file
    """

    if isinstance(dotfiles, dict):
        relative_paths = dotfiles.keys()
    elif isinstance(dotfiles, list) and len(dotfiles) > 0:
        relative_paths = [str(d.relative_path) for d in dotfiles]
    elif not dotfiles:
        return
    else:
        raise TypeError("`dotfiles` is not of type list[Dotfile], or dict[str, Dotfile]")

    with open(managed_files_file, "w+") as f:
        f.write("\n".join(relative_paths))
