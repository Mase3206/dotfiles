import pickle
from abc import ABC, abstractmethod
from enum import Enum

from dotmgr import DOTFILES_DIR, outputs


class InstallStatus(str, Enum):
    INSTALLED = "INSTALLED"
    NOT_INSTALLED = "NOT_INSTALLED"
    INSTALL_FAILED = "INSTALL_FAILED"


class BaseMod(ABC):
    @property
    @abstractmethod
    def dependencies(self) -> list[str]:
        """
        The list of mod names this mod depends on. Mod names are the *names* of the classes.
        """
        ...

    @property
    @abstractmethod
    def dotfiles(self) -> list[str]:
        """
        The list of relative paths of all dotfiles related to this mod.

        **Note:** Directories must end in a forward slash to be correctly identified.
        """
        ...

    @abstractmethod
    def detect(self, quiet: bool = False) -> bool:
        """
        Detect installation and print status to console (if quiet = False).

        :param bool quiet: If true, do not print status to console. Defaults to False.
        :returns bool: True if mod was detected, False otherwise
        """
        ...

    @abstractmethod
    def install(self, force: bool = False):
        """
        Install this mod.

        :param bool = False force: Force installation, regardless of whether or not 
            this mod is already detected.

        The runner of this mod is responsible for ensuring all dependencies of this mod are satisfied
        *before* actually installing anything. The use of :meth:`_install_dependencies` is recommended, as
        long as the mod's dependencies are properly defined in the mod's :attr:`dependencies`, as
        _install_dependencies automatically installs every mod in that list (if auto-discovered, of course).

        Exceptions during the installation process may be thrown and must be handled accordingly, like this:

        ```python
        try:
            # do stuff
        except Exception:
            print(f"Mod failed to install")
            self.status = InstallStatus.INSTALL_FAILED
            raise
        ```
        """
        ...

    def _install_dependencies(self):
        """
        Install all dependencies of this mod.
        """
        # Putting this here lets us avoid circular imports from partially
        # imported modules. Idk man, blame Python.
        from dotmgr.mods import __mods__

        for dep_name in self.dependencies:
            try:
                dep = __mods__[dep_name]
                if dep.detect(quiet=True):
                    outputs.status_good(f"Dependency {dep_name}", "installed")
                else:
                    outputs.status_bad(f"Dependency {dep_name}", "NOT installed", end=" - ")
                    print("installing now")
                    dep.install()

            except KeyError as e:
                raise KeyError(
                    f"This mod ({self.mod_name}) depends on {dep_name}, which either does not exist or was "
                    "not automatically detected by the mod manager."
                ) from e

    def update_status(self):
        """
        Update saved status in mods.dat.

        :return bool: True if mod was detected, False otherwise
        """
        if self.detect(quiet=True):
            self.status = InstallStatus.INSTALLED
            return True
        else:
            self.status = InstallStatus.NOT_INSTALLED
            return False

    @property
    def status(self) -> InstallStatus:
        """
        Whether this mod has already been installed (or if a previous installation attempt failed).
        Wrapper around the mods.dat file.
        """

        with open(DOTFILES_DIR / "mods.dat", "rb+") as pf:
            data = pickle.load(pf)

        if not data:
            return InstallStatus.NOT_INSTALLED

        s = data.get(self.mod_name)
        if s:
            return s
        else:
            _status = InstallStatus.INSTALLED if self.detect(quiet=True) else InstallStatus.NOT_INSTALLED
            self.status = _status
            return _status

    @status.setter
    def status(self, status: InstallStatus):
        """
        :param InstallStatus status: Install status to set
        """  # docstring description is inherited by getter
        with open(DOTFILES_DIR / "mods.dat", "rb+") as pf:
            data = pickle.load(pf)

        if not data:
            data = {}

        data[self.mod_name] = status

        with open(DOTFILES_DIR / "mods.dat", "wb+") as pf:
            pickle.dump(data, pf)

    @property
    def mod_name(self):
        """The name of this mod. Wrapper around some class introspection."""
        return self.__class__.__name__

    def __str__(self) -> str:
        return self.mod_name
