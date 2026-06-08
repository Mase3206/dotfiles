from abc import ABC, abstractmethod
from enum import Enum
import pickle
from dotmgr import DOTFILES_DIR


class InstallStatus(str, Enum):
    INSTALLED = 'INSTALLED'
    NOT_INSTALLED = 'NOT_INSTALLED'
    INSTALL_FAILED = 'INSTALL_FAILED'


class BaseMod(ABC):
    @property
    @abstractmethod
    def dependencies(self) -> list[str]:
        """
        The list of mod names this mod depends on. Mod names are the *names* of the classes.
        """

    @property
    @abstractmethod
    def dotfiles(self) -> list[str]:
        """
        The list of relative paths of all dotfiles related to this mod.
        """
    
    @abstractmethod
    def detect(self, quiet: bool = False) -> bool:
        """
        Detect installation and print status to console (if quiet = False)

        :returns bool: True if mod was detected, False otherwise
        """

    @abstractmethod
    def install(self):
        """
        The runner of this mod is responsible for ensuring all dependencies of this mod are satisfied *before* running `install()`.

        Exceptions during the installation process may be thrown and must be handled accordingly.
        """

    @property
    def status(self) -> InstallStatus:
        """
        Whether this mod has already been installed (or if a previous installation attempt failed). Wrapper around the mods.dat file
        """

        with open(DOTFILES_DIR / "mods.dat", 'rb+') as pf:
            data = pickle.load(pf)

        if not data:
            return InstallStatus.NOT_INSTALLED
        s = data.get(self.__name__)
        if not s:
            return InstallStatus.NOT_INSTALLED
        else:
            return s
        
    @status.setter
    def status(self, status: InstallStatus):
        with open(DOTFILES_DIR / "mods.dat", "rwb+") as pf:
            data = pickle.load(pf)
        
            if not data:
                data = {}

            data[self.__name__] = status

            pickle.dump(data, pf)
