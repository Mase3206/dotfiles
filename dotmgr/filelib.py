import shutil
from enum import Enum
from pathlib import Path
from typing import Union

from dotmgr import DOTFILES_DIR, HOME, mods, outputs
from dotmgr.mods.base import BaseMod


class UnknownFileTypeError(FileExistsError):
    pass


class LogLevel(int, Enum):
    DEBUG = 5
    INFO = 4
    WARN = 3
    ERR = 2
    CRITICAL = 1


class Dotfile:
    _raw_relative_path: str
    src: Path
    dest: Path
    log_level: LogLevel
    logging_enabled: bool
    used_by: Union[BaseMod, None]

    def __init__(self, relative_path: Path):
        self.relative_path = relative_path
        self.src = (DOTFILES_DIR / relative_path).resolve()
        self.dest = HOME / relative_path
        self.logging_enabled = True
        self.log_level = LogLevel.DEBUG
        self.used_by = mods.__mod_dotfiles__.get(str(self.relative_path), None)

    @property
    def relative_path(self) -> str:
        return self._raw_relative_path

    @relative_path.setter
    def relative_path(self, path: Union[Path, str]):
        if isinstance(path, Path):
            if path.is_absolute():
                try:
                    path = path.relative_to(HOME)
                except ValueError:
                    self.log('relative_path', LogLevel.ERR, f"Given relative path {path!s} is absolute but not in '{HOME}'")
            is_dir = path.is_dir()
            path = str(path)
        else:
            is_dir = Path(path).is_dir()
        
        self._raw_relative_path = path + ('/' if is_dir else '')

    def __str__(self) -> str:
        return str(self.relative_path)

    def log(self, fname: str, level: LogLevel, message: str):
        if self.logging_enabled and level <= self.log_level:
            print(
                f"{level.name:>5}  [Dotfile('{self.relative_path}').{fname}]: {message}"
            )

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
            self.log(
                "rm", LogLevel.WARN, "dest is a symlink, cautiously removing anyways"
            )
            self.dest.unlink()
            return True

        elif self.dest.is_file():
            self.log(
                "rm",
                LogLevel.WARN,
                "dest is a regular file, making a backup before removing",
            )
            shutil.copyfile(self.dest, str(self.dest) + '.bak')
            self.dest.unlink()
            return True

        # elif self.dest.is_dir():
        #     self.log("rm", LogLevel.ERR, "dest is a directory, not removing")
        #     return False
        elif self.dest.is_dir():
            self.log("rm", LogLevel.WARN, "dest is a directory, making a backup before removing")
            shutil.copytree(self.dest, str(self.dest) + '.bak')
            self.dest.unlink()
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
            self.log(
                "ln", LogLevel.DEBUG, "dest does not exist and is not linked, linking"
            )
            # Create parent directory of dest if it doesn't exist
            if not self.dest.parent.exists():
                self.log('ln', LogLevel.DEBUG, 'Parent dir of dest does not exist, creating recursively')
                self.dest.parent.mkdir(parents=True)
            self.dest.symlink_to(self.src)
            return True
        elif self.dest.is_symlink():
            if self.dest.resolve() == self.src:
                # print(f"[Dotfile.ln] ")
                self.log(
                    "ln", LogLevel.DEBUG, "dest is already linked correctly, relinking"
                )
                self.dest.unlink()
                self.dest.symlink_to(self.src)
                return True
            else:
                self.log(
                    "ln",
                    LogLevel.ERR,
                    f"{self.dest} is already a symlink, but does not point to the right file. It points to: '{self.dest.resolve()}'",
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
                "dest exists and is a directory. Remove it manually or with the `rm()` function before continuing.",
            )
            return False
        elif self.dest.is_file():
            # print(f"[Dotfile.ln]:ERR {self.dest} exists and is a file. Remove it with the `rm()` function.")
            self.log(
                "ln",
                LogLevel.ERR,
                "dest exists and is a file. Remove it manually or with the `rm()` function before continuing.",
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
        self.log("sync", LogLevel.INFO, "Attempting to sync")

        self.log(
            "sync", LogLevel.DEBUG, "Attempting to remove existing link (if exists)"
        )
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
            self.log("adopt", LogLevel.DEBUG, "Target is a folder, moving to dotfiles folder and linking")
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
        Copy src to dest, deleting dest symlink if necessary
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
                f"Source is a symlink, which is {outputs.AnsiColors.BOLD}{outputs.AnsiColors.RED}very bad{outputs.AnsiColors.END}!!! Sources should {outputs.AnsiColors.BOLD}never{outputs.AnsiColors.END} be symlinks!",
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


def load_dotfiles(managed_files_file: Path):
    # relative_paths: list[Path] = []
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
    dotfiles: Union[list[Dotfile], dict[str, Dotfile]], managed_files_file: Path
):
    if isinstance(dotfiles, dict):
        relative_paths = dotfiles.keys()
    elif isinstance(dotfiles, list) and len(dotfiles) > 0:
        relative_paths = [str(d.relative_path) for d in dotfiles]
    elif not dotfiles:
        return
    else:
        raise TypeError(
            "`dotfiles` is not of type list[Dotfile], or dict[str, Dotfile]"
        )

    with open(managed_files_file, "w+") as f:
        f.write("\n".join(relative_paths))
