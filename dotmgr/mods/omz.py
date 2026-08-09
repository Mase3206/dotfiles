import subprocess

from dotmgr import HOME, USER, outputs
from dotmgr.mods.base import BaseMod, InstallStatus
from dotmgr.utils import cd, mktemp


# from dotmgr.mods import __mods__

class OhMyZsh(BaseMod):
    """
    Oh My Zsh plugin.

    This plugin installs Oh My Zsh (and Zsh, if it isn't already installed). It will also attempt
    to set the user's shell to Zsh.

    - Dependencies: Zsh
    - Dotfiles: .oh-my-zsh/themes/terse.zsh-theme
    """

    dependencies = ["Zsh"]
    dotfiles = [".oh-my-zsh/themes/terse.zsh-theme"]
    pretty_name = "Oh My Zsh"
    description = 'Install the Oh My Zsh "plugin" for Zsh'

    def detect(self, quiet: bool = False) -> bool:
        dest_path = HOME / ".oh-my-zsh"
        if dest_path.exists() and dest_path.is_dir():
            if not quiet:
                outputs.status_good("OMZ install status", "already installed!")
            self.status = InstallStatus.INSTALLED
            return True
        else:
            if not quiet:
                outputs.status_bad("OMZ install status", "NOT installed.")
            self.status = InstallStatus.NOT_INSTALLED
            return False

    def install(self, force: bool = False):
        outputs.subheader("Installing Oh My Zsh")
        if self.detect(quiet=True) and not force:
            outputs.skip("OMZ installation")
            return

        self._install_dependencies()

        # _zsh = __mods__["Zsh"]
        # if not _zsh.detect():
        #     outputs.step("Zsh not detected, installing")
        #     _zsh.install()

        try:
            with mktemp() as tempfolder, cd(tempfolder) as cwd:
                with open("install.sh", "w+") as f:
                    outputs.step(f"Downloading install script to {cwd / 'install.sh'}")
                    subprocess.run(
                        [
                            "/usr/bin/curl",
                            "-fsS",
                            "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh",
                        ],
                        cwd=cwd,
                        stdout=f,
                        check=True,
                    )

                outputs.step("Installing OMZ")
                subprocess.run(
                    ["/bin/sh", "install.sh"],
                    shell=False,
                    env={
                        "CHSH": "no",
                        "RUNZSH": "no",
                        "KEEP_ZSHRC": "yes",
                        "HOME": HOME,
                        "USER": USER,
                    },
                    cwd=cwd,
                    check=True,
                )

                outputs.step("Setting user's shell to /usr/bin/zsh")
                try:
                    subprocess.run(["/usr/bin/chsh", USER, "-s", "/usr/bin/zsh"], check=True)
                except subprocess.CalledProcessError:
                    print(
                        f"Unable to set Zsh as the shell for user '{USER}'. You'll need to "
                        "change it yourself with this command:\n"
                        f"/usr/bin/chsh {USER} -s /usr/bin/zsh"
                    )

                outputs.step("Cleaning up")
                # Exit the context manager to cd back out and remove temp dir
            self.status = InstallStatus.INSTALLED

        except:
            self.status = InstallStatus.INSTALL_FAILED
            raise
