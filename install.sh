#!/bin/bash


# If $DOTFILES_DIR is unset, assume current directory
if [ -z $DOTFILES_DIR ]; then
	echo "\$DOTFILES_DIR is not set. Assuming current directory: $(pwd)"
	export DOTFILES_DIR=$(pwd)

	# add to ~/.aliases so it's sourced
	echo "export DOTFILES_DIR=$DOTFILES_DIR" >> ~/.aliases
fi


./extras.sh all install
./quicksync.sh --from known.txt sync -y