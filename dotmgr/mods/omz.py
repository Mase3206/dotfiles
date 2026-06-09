import subprocess

from dotmgr import HOME, USER, outputs
from dotmgr.mods.base import BaseMod, InstallStatus
from dotmgr.utils import cd, mktemp


class OhMyZsh(BaseMod):
    @property
    def dependencies(self) -> list[str]:
        return ["Zsh"]

    @property
    def dotfiles(self) -> list[str]:
        return [".oh-my-zsh/themes/terse.zsh-theme"]

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

    def install(self):
        outputs.subheader("Installing Oh My Zsh")
        if self.detect():
            outputs.skip("OMZ installation")
            return

        try:
            with mktemp() as tempfolder, cd(tempfolder) as cwd:
                with open("install.sh", "w+") as f:
                    outputs.step(f"Downloading install script to {cwd / 'install.sh'}")
                    subprocess.run(
                        [
                            "/usr/bin/curl",
                            "-fsS:",
                            "'https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh'",
                        ],
                        cwd=cwd,
                        stdout=f,
                    ).check_returncode()

                outputs.step("Installing OMZ")
                subprocess.run(
                    ["/bin/sh", "install.sh"],
                    shell=True,
                    env={
                        "CHSH": "yes",
                        "RUNZSH": "no",
                        "KEEP_ZSHRC": "yes",
                        "HOME": HOME,
                        "USER": USER,
                    },
                    cwd=cwd,
                ).check_returncode()

                outputs.step("Setting user's shell to /usr/bin/zsh")
                subprocess.run(
                    ["/usr/bin/chsh", USER, "-s", "/usr/bin/zsh"]
                ).check_returncode()

                outputs.step("Cleaning up")
                # Exit the context manager to cd back out and remove temp dir
            self.status = InstallStatus.INSTALLED

        except:
            self.status = InstallStatus.INSTALL_FAILED
            raise
