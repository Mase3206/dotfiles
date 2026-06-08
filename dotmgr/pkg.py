#!/usr/bin/python3

import os
from enum import Enum
import subprocess
from pathlib import Path


class OsType(str, Enum):
    MACOS = "macos"
    LINUX = "linux"
    FREEBSD = "freebsd"


class PkgMgrName(str, Enum):
    APT = "apt-get"
    DNF = "dnf"
    ZYPPER = "zypper"
    PKG = "pkg"
    HOMEBRW = "brew"


class PackageManager:
    ostype: OsType
    package_manager_name: PkgMgrName
    package_manager_path: Path
    sudo_required: bool

    def __init__(self):
        self.ostype = self.detect_os()
        self.package_manager_name = self.detect_package_manager()
        self.sudo_required = (
            False if self.package_manager_name == PkgMgrName.HOMEBRW else True
        )

        out = subprocess.run(
            f"which {self.package_manager_name}",
            shell=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        out.check_returncode()
        self.package_manager_path = Path(out.stdout.strip())
        if not (
            self.package_manager_path.exists() and self.package_manager_path.is_file()
        ):
            raise FileNotFoundError(
                f"Detected package manager path as {self.package_manager_path!s}, but it doesn't actually exist or isn't a file."
            )

    @classmethod
    def detect_os(cls) -> OsType:
        ostype = os.environ.get("OSTYPE", "unset")
        if "darwin" in ostype:
            return OsType.MACOS
        elif "linux" in ostype:
            return OsType.LINUX
        elif "freebsd" in ostype:
            return OsType.FREEBSD
        else:
            raise Exception(f"Unknown or unsupported OSTYPE: '{ostype}'")

    @classmethod
    def detect_package_manager(cls) -> PkgMgrName:
        names_to_test = PkgMgrName._value2member_map_.keys()
        for n in names_to_test:
            if subprocess.run(f"command -v {n}", shell=True).returncode == 0:
                return PkgMgrName(n)

        raise Exception("Unable to automatically detect package manager.")

    def install_package(self, package_name: str):
        cmd = [str(self.package_manager_path), "install"]
        if self.sudo_required:
            cmd = ["sudo"] + cmd
        if self.package_manager_name != PkgMgrName.HOMEBRW:
            cmd += ["-y"]

        cmd += [package_name]

        subprocess.run(cmd, stdout=subprocess.DEVNULL)
