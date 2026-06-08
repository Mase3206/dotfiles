#!/usr/bin/bash

set -euo pipefail


# Set the DOTFILES_DIR if it hasn't been set yet.
[ -n "${DOTFILES_DIR}" ] || export DOTFILES_DIR='~/.config/dotfiles'

# This line is needed to make the new Python-based dotfiles manager work,
# since it does some dynamic import trickery.
export PYTHONPATH="$DOTFILES_DIR:$PYTHONPATH"

# If the folder containing the dotfiles doesn't exist, create it.
[ -d "$DOTFILES_DIR/.." ] || mkdir -p "$DOTFILES_DIR/.."

# If this is a Mac, advise the user to install Xcode Command Line Tools and Homebrew before continuing.
if [[ "$OSTYPE" == darwin* ]] && ! command -v brew > /dev/null; then
cat << EOF
It looks like you're on a Mac, and you don't have Homebrew installed yet. For this program to be useful, you really should install Homebrew first. https://brew.sh/

If you don't want to install Homebrew, you will still need to install the Xcode Command Line Tools, as that installs Git, which this requires. I still don't know why Apple doesn't just ship Git with every computer, since it's not that big, (the binary is only 12K), but Apple just wanted to make things complicated. xcode-select --install

I also don't know why Apple *still* ships the latest macOS with a five-year-old version of Python (which will be going EOL soon)...

Anyways, that's the end of my info dump and little diatribe.

EOF
fi


echo "Checking dependencies:"

# Find the Python 3 executable, and make sure it's at least version 3.9
echo -n " • Python 3.9+"
if command -v python3 > /dev/null; then
    PYTHON_BIN="$(which python3)"
elif command -v python > /dev/null; then
    PYTHON_BIN="$(which python)"
else
    echo -e " - not found.\nExiting"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_BIN --version | awk '{ print $2 }')
# PYTHON_VERSION="2.7.1"
PYTHON_MAJOR=$(echo $PYTHON_VERSION | awk -F. '{ print $1 }')
PYTHON_MINOR=$(echo $PYTHON_VERSION | awk -F. '{ print $2 }')

if ! [ $PYTHON_MAJOR -eq 3 ] || \
 [ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -lt 9 ]; then
    echo " - detected ($PYTHON_BIN, $PYTHON_VERSION), but lower than version 3.9"
    echo "Exiting"
    exit 1
else
    echo " - detected ($PYTHON_BIN, $PYTHON_VERSION)"
fi


# Make sure Git is installed
echo -n " • Git"
if command -v git > /dev/null; then
    echo " - detected ($(command -v git))"
else
    echo -e " - not found.\nExiting"
    exit 1
fi

echo -e "Dependencies satisfied.\n\n"

# echo "Cloning mase3206/dotfiles in to $DOTFILES_DIR"
git https://github.com/Mase3206/dotfiles.git $DOTFILES_DIR

echo -e "\nAdding \`dot\` wrapper to user's ~/.aliases file"
echo "alias dot=\"$PYTHON_BIN \$DOTFILES_DIR/dotmgr/dot.py\"" >> ~/.aliases

echo "Creating empty mods.dat file in the dotfiles directory"

cat << EOF | $PYTHON_BIN -
import pickle
with open("$DOTFILES_DIR/mods.dat", "wb+") as pf:
    pickle.dump({}, pf)
EOF