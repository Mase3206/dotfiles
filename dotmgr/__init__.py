import getpass
import os
from pathlib import Path


HOME = Path.home()
"""~ (aka. $HOME)"""
USER = os.environ.get("USER", getpass.getuser())
"""$USER"""
XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
"""~/.local/share"""

# Make sure the dotfiles directory is set
DOTFILES_DIR = os.environ.get("DOTFILES_DIR")
"""Path to the directory containing the dotfiles manager and the dotfiles repository"""
if not DOTFILES_DIR:
    raise EnvironmentError("$DOTFILES_DIR is not set.")
else:
    DOTFILES_DIR = Path(DOTFILES_DIR)

# Get the path to managed.files
DOTFILES_MANAGED_FILE = Path(os.environ.get("DOTFILES_MANAGED_FILE", DOTFILES_DIR / "managed.files"))
"""Path to the "managed.files" file"""
if not DOTFILES_MANAGED_FILE.exists():
    raise FileNotFoundError(
        "managed.files file (which lists which dotfiles to care about) wasn't found in the "
        f"dotfiles directory '{DOTFILES_DIR}'"
    )

# Meta folder
META_DIR = DOTFILES_DIR / "dotmgr" / "meta"
"""
Stuff stored here are typically pickled objects that either:
1. Are used across executions, or
2. Would otherwise cause circular imports if imported directly.
"""
