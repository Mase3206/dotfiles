#!/usr/bin/python3
from __future__ import annotations

import subprocess
import sys
from enum import Enum
from pathlib import Path


class Platform(str, Enum):
    MACOS = "macos"
    LINUX = "linux"
    FREEBSD = "freebsd"

    @staticmethod
    def detect_os() -> Platform:
        """
        Attempt to detect this computer's operating system.

        :raises Exception: If an unknown or unsupported operating system is detected
        """

        # ostype = os.environ.get("OSTYPE", "unset")
        if sys.platform == "darwin":
            return Platform.MACOS
        elif sys.platform == "linux":
            return Platform.LINUX
        elif sys.platform == "freebsd":
            return Platform.FREEBSD
        else:
            raise Exception(f"Unknown or unsupported OSTYPE: '{ostype}'")
        
    def __str__(self) -> str:
        return self.value


class PkgMgrName(str, Enum):
    APT = "apt-get"
    DNF = "dnf"
    ZYPPER = "zypper"
    PKG = "pkg"
    HOMEBRW = "brew"
        
    def __str__(self) -> str:
        return self.value


class PackageManager:
    """
    Wrapper around a system's package manager.

    This class attempts to detect your system's package manager and provide wrapper methods
    around it. Currently, only the following OS families and package managers are (theoretically)
    supported:
    - Debian (apt-get)
    - RHEL (dnf)
    - SuSE (zypper)
    - FreeBSD (pkg)
    - macOS (brew)

    Notes
    -----
    Support for all these package managers is theoretical at this point. The only mod which uses
    this (as of writing) is Zsh, and I have only tested that mod on my Mac, which already has Zsh
    installed. Use at your own risk.

    :param Platform platform: This computer's operating system family
    :param PkgMgrName package_manager_name: The detected package manager for this computer
    :param Path package_manager_path: The absolute path to the binary of this computer's package manager
    :param bool sudo_required: Whether sudo is required for this package manager. Homebrew requires this
        to be False.
    """

    platform: Platform
    package_manager_name: PkgMgrName
    package_manager_path: Path
    sudo_required: bool

    def __init__(self):
        """
        Initialize a new package manager by attempting to automatically detect both this computer's
        operating system andits package manager.
        """
        self.platform = Platform.detect_os()
        self.package_manager_name = self.detect_package_manager()
        self.sudo_required = False if self.package_manager_name == PkgMgrName.HOMEBRW else True

        out = subprocess.run(
            f"which {self.package_manager_name.value}",
            shell=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
            check=True,
        )
        self.package_manager_path = Path(out.stdout.strip())
        if not (self.package_manager_path.exists() and self.package_manager_path.is_file()):
            raise FileNotFoundError(
                f"Detected package manager path as {self.package_manager_path!s}, but it doesn't actually "
                "exist or isn't a file."
            )

    @classmethod
    def detect_package_manager(cls) -> PkgMgrName:
        """
        Attempt to detect this computer's package manager.

        :returns PkgMgrName: The name of the detected package manager
        :raises FileNotFoundError: If the package manager could not be detected
        """
        names_to_test = PkgMgrName._value2member_map_.keys()
        for n in names_to_test:
            if (
                subprocess.run(
                    f"command -v {n}",
                    shell=True,
                    check=False,  # failures are expected, so chill
                ).returncode
                == 0
            ):
                return PkgMgrName(n)

        raise FileNotFoundError("Unable to automatically detect package manager.")

    def install_package(self, package_name: str):
        """
        Install the named package.

        :param str package_name: Package to install
        :raises subprocess.CalledProcessError[str]: If the command failed in some way
        """
        cmd = [str(self.package_manager_path), "install"]
        if self.sudo_required:
            cmd = ["sudo"] + cmd
        if self.package_manager_name != PkgMgrName.HOMEBRW:
            cmd += ["-y"]

        cmd += [package_name]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, check=True)
