# Noah's Dotfiles

You seem to have found my super secret dotfiles. Go you. They're pretty boring for the most part. 


## New dotfile manager

**dot** is a custom, lightweight, stdlib-only dotfile manager. Written for Python 3.9+, it supports macOS (because even macOS 26 is shipping with Python 3.9.6, which is from 2022) and older Linux distros, and, as Python 3
generally has excellent backwards compatibility, it is highly likely to work on later versions as well.

I am aware that others have created dedicated programs to do just this. However, I have deliberately avoided them for that exact reason: I want a *script*, not a *program*. I want to clone my dotfiles repository, add an alias to a local ~/.aliases file (which is unique to each computer, but is sourced in .zshrc), and run `dot sync`. That's exactly what install.sh does. Nothing to install, nothing to have to update separately. It's a *script*.

Is this a bit overly particular? Oh probably. But this is the \*nix world we're talking about. This little niche of the tech world is nothing if not passionately opinionated. And besides, people with opinions get things done.


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
curl 'https://github.com/Mase3206/dotfiles/blob/main/dotmgr/install.sh' | bash
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

> [!note]
> A "managed" dotfile is one that is listed in the 'managed.files' file and is thus known to **dot**. Even if a dotfile exists in this repository, if it's not in 'managed.files', **dot** pays no attention to it.
> Files can be easily managed or unmanaged with `dot manage <file>` and `dot unmanage <file>`, respectively.

<!-- > [!warning]
> Currently, **dot** does not support linking or managing folders. This was a deliberate design decision to avoid confusing situations, though it is likely to change in the near future. -->

> [!warning]
> Currently, **dot** does support linking and managing folders. This is a new and not thoroughly-tested feature, so use it at your own risk. Before anything is done to existing folders (like files), a backup in its current directory is made, so recovering from failures should be relatively painless.

All file paths from hereon out are *relative paths*, relative to the user's home directory (and thus also dotfiles repository).


#### Environment Variables

- `$DOTFILES_DIR`: Points to the folder containing the dotfiles repo.
- `$DOTFILES_LOGLEVEL`: Sets the log level. Defaults to "WARN" if unset.


#### Link managed files

```shell
dot ln [file ...]
```

Link one (or more) managed files from the local dotfiles repository to the user's home directory. If no file names are given, all managed files will be linked.


#### Remove managed files

```shell
dot rm <file> [file ...]
```

Remove one (or more) links to managed files from the user's home directory.


#### Sync managed files

```shell
dot sync [file ...]
```

Sync one (or more) managed files from the local dotfiles repository to the user's home directory by:
1. Removing the existing file (backing up first) or link from the user's home
2. Linking from the "real" managed file into the user's home

If no file(s) are given, all managed files are synced.


#### Make a file managed

```shell
dot manage <file> [file ...]
```

Make one or more files managed by adding their relative path to managed.files. These file(s) must exist within dotfiles repository to manage them.


#### Make a file unmanaged

```shell
dot unmanage <file> [file ...]
```

Make one or more files unmanaged by removing their relative path from managed.files. This does not remove the actual file from dotfiles repository.


#### Adopt a file

```shell
dot adopt <file> [file ...]
```

Move a local dotfile into the dotfiles repository, link it, and add it to managed.files. This imports a local dotfile into the repo and re-links it.


#### Orphan a file

```shell
dot orphan [-r / --rm] <file> [file ...]
```

Unlink a managed dotfile and move it to the user's home folder. If `-r` or `--rm` are passed, the managed dotfile will be unmanaged and deleted from the dotfiles repository. This converts the once linked file into a local-only, unlinked, and unsynced dotfile.


#### Edit a dotfile

```shell
dot edit [-cvnl] <file>
```

Edit a managed dotfile with either the editor set in $EDITOR or with the chosen editor, selected by flag:
- `-c`: Open in VSCode
- `-v`: Open in Vim
- `-n`: Open in Nano
- `-l`: Open in Less (not technically an editor, but still helpful

If $EDITOR is unset and no editor flag is chosen, the contents of the file are sent to stdout with `cat`.


#### Interact with mods

```shell
dot mod {install,detect} [<mod_name> ...]
```

See [Mods](#mods) for more details.


#### Interact with Git

```shell
dot git <action>
```

The *git* subcommand provides an easy way to commit and push changes to dotfiles.

#### Actions

- **commit:** Commit all changes to managed dotfiles. A commit message is automatically generated. **Only managed dotfiles are committed.**
- **push:** Push all committed changes to the remote.
- **pull:** Stash all local changes (both committed and uncommitted), pull from remote, then unstash changes.
- **undo:** Undo the last commit and unstage the previously committed files.
	- Note: this has not been tested very thoroughly, so use it at your own risk.
- **status:** Get the current Git status of the local repo.


### Mods

Mods are Python modules with one or more classes which subclass `dotmgr.mods.base.BaseMod` and implement certain methods. See [Authoring Mods.md](dotmgr/mods/Authoring Mods.md) for details.

Mods which subclass `BaseMod` and are in a module within `dotmgr.mods` will be automatically detected and imported.

Once a mod is installed, you will need to run `dot ln` to link the dotfiles it uses, as those files are unavailable until the mod which uses them is installed. This may be improved in a future version, where the mod's file(s) (if any) will be linked automatically after a successful installation.

Mods keep track of their install status between executions via the mods.dat file. While it's not strictly necessary to do this, it saves us a bit of time to just quickly check the file rather than run a potentially rather long detection script every single time **dot** runs.

For example, the Zsh mod will install the Z-shell (if not already installed) with your system's package manager (if it's able to detect it). If Zsh is already installed, it will mark itself as such in the gitignored mods.dat file and exit successfully.

The OhMyZsh mod will install Oh My Zsh (which basically just downloads some files and shoves them in your home folder) and mark itself as installed. If ~/.oh-my-zsh is already present, it will mark itself as already installed and exit successfully.

