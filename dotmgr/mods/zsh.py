#!/usr/bin/python3

if __name__ == '__main__':
    print("You must run this script through dots.py, as it initializes critical environment variables used for installation and detection.")

# from pathlib import Path
from .. import outputs
from dotmgr import HOME
from dotmgr.pkg import PackageManager
from dotmgr.mods.base import BaseMod, InstallStatus
import subprocess


class Zsh(BaseMod):
    @property
    def dependencies(self):
        return []
    
    @property
    def dotfiles(self):
        return ['.zshrc']
    
    def detect(self, quiet: bool = False) -> bool:
        if subprocess.run(
            'command -v zsh',
            shell=True
        ).returncode == 0:
            if not quiet:
                outputs.status_good(
                    "Zsh install status",
                    "already installed!"
                )
            self.status = InstallStatus.INSTALLED
            return True
        else:
            if not quiet:
                outputs.status_bad(
                    "Zsh install status",
                    "NOT installed"
                )
            self.status = InstallStatus.NOT_INSTALLED
            return False
        
    def install(self):
        outputs.subheader("Installing Zsh")

        if self.detect():
            outputs.skip("Zsh installation.")
            return
        
        try:
            outputs.step("Initializing package manager wrapper handler manager class manager")
            pkgmgr = PackageManager()

            outputs.step(f"Installing Zsh using {pkgmgr.package_manager_name}")
            pkgmgr.install_package('zsh')

            existing_zshrc = HOME / '.zshrc'
            if existing_zshrc.is_file():
                if existing_zshrc.is_symlink():
                    outputs.step("Existing .zshrc is a symlink, so I'm not moving it.")
                else:
                    outputs.step("Backing up existing .zshrc")
                    existing_zshrc.rename(existing_zshrc.parent / '.zshrc.bak')

            self.status = InstallStatus.INSTALLED
        
        except:
            self.status = InstallStatus.INSTALL_FAILED
            raise
