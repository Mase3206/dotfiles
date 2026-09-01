"""
This module contains mods which provide supplemental functionality to `dot`.
"""

import shutil

from dotmgr import DOTFILES_DIR, HOME, XDG_DATA_HOME, compmaker, outputs
from dotmgr.mods.base import BaseMod, InstallStatus


class ZshCompletions(BaseMod):
    """
    Detect and install Zsh completions for **dot**.

    - Dependencies: Zsh, OhMyZsh
    """

    dependencies = ["Zsh", "OhMyZsh"]
    dotfiles = []
    pretty_name = "Zsh Completions"
    description = "Generate and install Zsh completions for " \
        + f"{outputs.AnsiColors.BOLD}dot{outputs.AnsiColors.END}"

    _compfile_path = HOME / ".oh-my-zsh/custom/completions/_dot"

    def detect(self, quiet: bool = False) -> bool:
        if self._compfile_path.exists() and self._compfile_path.is_file():
            if not quiet:
                outputs.status_good("Zsh completions install status", "already installed!")
            self.status = InstallStatus.INSTALLED
            return True
        else:
            if not quiet:
                outputs.status_bad("Zsh completions install status", "NOT installed.")
            self.status = InstallStatus.NOT_INSTALLED
            return False

    def install(self, force: bool = False):
        # Putting this here lets us avoid circular imports from partially
        # imported modules. Idk man, blame Python.
        from dotmgr.dot import parser

        outputs.subheader("Adding Zsh completions")
        if self.detect(quiet=True) and not force:
            outputs.skip("Zsh completions")
            return

        try:
            self._install_dependencies()

            outputs.step("Generating Zsh completions")
            commands = compmaker.convert_from_parser(parser, cmd_name="dot")
            render = compmaker.render_zsh(commands)

            outputs.step("Save Zsh completions")
            if not self._compfile_path.parent.exists():
                self._compfile_path.parent.mkdir(parents=True)
            with open(self._compfile_path, "w+") as f:
                f.write(render)

            print(f"Saved completions to {self._compfile_path!s}. Reload shell to use them.")
            self.status = InstallStatus.INSTALLED

        except Exception:
            print(f"Zsh completions {outputs.AnsiColors.RED}failed to install{outputs.AnsiColors.END}.")
            self.status = InstallStatus.INSTALL_FAILED
            raise


class ManPages(BaseMod):
    """
    Detect and install man pages for **dot** into the user's local man pages store
    (set in .zshrc as ~/.local/share/man/man1).
    """

    dependencies = []
    dotfiles = []
    pretty_name = "Man Pages"
    description = f"Install man pages for {outputs.AnsiColors.BOLD}dot" \
        + f"{outputs.AnsiColors.END} into the user's local man pages store"

    _manpages_path = XDG_DATA_HOME / "man/man1"
    _docs_path = DOTFILES_DIR / "docs" / "man"

    @property
    def _expected_manfiles(self) -> list[str]:
        files: list[str] = []
        for ronn_file in self._docs_path.glob("*.ronn"):
            files.append(ronn_file.stem)
        return files

    def detect(self, quiet: bool = False) -> bool:
        if (
            self._manpages_path.exists()
            and self._manpages_path.is_dir()
            and all([(self._manpages_path / f).exists() for f in self._expected_manfiles])
            and all([(self._manpages_path / f).is_file() for f in self._expected_manfiles])
        ):
            if not quiet:
                outputs.status_good("Man pages install status", "already installed!")
            self.status = InstallStatus.INSTALLED
            return True
        else:
            if not quiet:
                outputs.status_bad("Man pages install status", "NOT installed.")
            self.status = InstallStatus.NOT_INSTALLED
            return False

    def install(self, force: bool = False):
        outputs.subheader("Installing man pages")
        if self.detect(quiet=True) and not force:
            outputs.skip("Man pages installation")
            return

        try:
            self._install_dependencies()

            if not self._manpages_path.exists():
                outputs.step(f"Creating user man pages path in {self._manpages_path}")
                self._manpages_path.mkdir(parents=True)

            _exp = self._expected_manfiles  # store it once to reduce impact on performance
            outputs.step(f"Copying man files: {', '.join(_exp)}")
            for mf in _exp:
                shutil.copyfile(self._docs_path / mf, self._manpages_path / mf)

            self.status = InstallStatus.INSTALLED

        except Exception:
            print(f"Man pages {outputs.AnsiColors.RED}failed to install{outputs.AnsiColors.END}.")
            self.status = InstallStatus.INSTALL_FAILED
            raise
