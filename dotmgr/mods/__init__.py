from abc import ABCMeta
from importlib import import_module
from pathlib import Path

from dotmgr.mods.base import BaseMod, InstallStatus

# Dynamically load the known/enabled mods and store them for other things to use
__mods__: dict[str, BaseMod] = {}
"""
Dictionary containing all mods (as *instances*) found in the dotmgr/mods/ folder.
- key: mod name
- value: mod *instance*
"""

# from dotmgr.mods.omz import OhMyZsh
# __mods__['OhMyZsh'] = OhMyZsh()

try:
    for mod_module_file in Path(__file__).parent.glob("*.py"):
        # ignore base and this file
        if mod_module_file.stem in ["base", "__init__"]:
            continue

        mod_module = import_module("dotmgr.mods." + mod_module_file.stem)
        for var_name, var_value in mod_module.__dict__.items():
            # Because Python's sad attempt at a baseclass system sucks, I have to do this janky two-step check to see if something is a subclass of BaseMod, then make it ignore the typing issue.
            # Ruff says it's fine, so it's fine by me.
            if isinstance(var_value, ABCMeta) and BaseMod in var_value.__bases__:
                # print(f'Found mod: {var_name}')
                __mods__[var_name] = var_value()

except ModuleNotFoundError as e:
    if e.name == "dotmgr":
        print(
            'Unable to find dotmgr module. This is likely the result of an unset (or improperly set) PYTHONPATH variable. Run `export PYTHONPATH=".:$PYTHONPATH"` to fix this.'
        )
        exit(1)
    else:
        raise


# Collect the dotfiles (just their relative paths) handled by mods
__mod_dotfiles__: dict[str, BaseMod] = {}
"""
Dictionary containing the dotfiles that are used (a.k.a. managed) by a mod.
- key: dotfile's relative path
- value: dotfile instance
"""

for mod in __mods__.values():
    for df in mod.dotfiles:
        __mod_dotfiles__[df] = mod

# Make sure each mod's stored status is accurate
for mod in __mods__.values():
    mod.update_status()

__all__ = [
    "BaseMod",
    "InstallStatus",
    "__mod_dotfiles__",
    "__mods__",
]
