# Noah's Dotfiles

You seem to have found my super secret dotfiles. Go you. They're pretty boring for the most part. 


## New dotfile manager

**dot** is a custom, lightweight, stdlib-only dotfile manager. Written for Python 3.9+, it supports macOS (because even macOS 26 is shipping with Python 3.9.6, which is from 2022) and older Linux distros, and, as Python 3
generally has excellent backwards compatibility, it is highly likely to work on later versions as well.

### Installation

Before installing, make sure you have the following dependencies installed:
- Python 3.9 or later
- Git
- Curl

The following package managers are supported:
- dnf
- apt-get
- brew
- zypper
- pkg (FreeBSD)

If installing on macOS, you'll need to install the Xcode Command Line Tools, as this installs Git. It's also *highly* recommended to install [Homebrew](https://brew.sh), both because **dot mods** can make use of it to install packages, and because it's just awesome.

```shell
# install Xcode Command Line Tools
xcode-select --install
```

If you end up installing Homebrew as well (which, let's be real, the only person likely reading this is me, so you will), Homebrew automatically prompts you to install the Xcode Command Line Tools during its own installation process.

After making sure the dependencies are installed, run the following command:
```shell
curl 'https://github.com/Mase3206/dotfiles/blob/main/dotmgr/install.sh' | sh
```

If your shell profile file sources ~/.aliases, you should already have an alias to **dot**. If you don't, you should set it in your profile with the following bit of code:

```shell
echo "alias dot=\"$PYTHON_BIN \$DOTFILES_DIR/dotmgr/dot.py\"" >> ~/.aliases
```

where `$PYTHON_BIN` is the full path to or name of the Python 3 executable you wish to use. The install script detects this automatically, but you'll need to do it manually here.

After all that, run these commands to install all mods and sync all files:
```shell
dot mod install
dot sync
```

### Usage

Use `dot -h` or `dot <subcommand> -h` for usage.