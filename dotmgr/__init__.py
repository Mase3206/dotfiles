import getpass
import os
from pathlib import Path

HOME = Path(os.environ.get("HOME", "~")).resolve()
USER = os.environ.get("USER", getpass.getuser())

# Make sure the dotfiles directory is set
DOTFILES_DIR = os.environ.get("DOTFILES_DIR")
if not DOTFILES_DIR:
    raise EnvironmentError("$DOTFILES_DIR is not set.")
else:
    DOTFILES_DIR = Path(DOTFILES_DIR)

# Get the path to managed.files
DOTFILES_MANAGED_FILE = Path(
    os.environ.get("DOTFILES_MANAGED_FILE", DOTFILES_DIR / "managed.files")
)
if not DOTFILES_MANAGED_FILE.exists():
    raise FileNotFoundError(
        f"managed.files file (which lists which dotfiles to care about) wasn't found in the dotfiles directory '{DOTFILES_DIR}'"
    )
