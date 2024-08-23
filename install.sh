#!/bin/bash

echo 
echo -e "\e[32m == Checking if \$DOTFILES_DIR is set == \e[0m"

# If $DOTFILES_DIR is unset, assume current directory
if [ -z $DOTFILES_DIR ]; then
	echo -e "\$DOTFILES_DIR is \e[31mNOT\e[0m set. Assuming current directory: $(pwd)"
	export DOTFILES_DIR=$(pwd)

	# add to ~/.aliases so it's sourced
	echo -n "Adding new \$DOTFILES_DIR export to ~/.aliases... "
	echo "export DOTFILES_DIR=$DOTFILES_DIR" >> ~/.aliases
	echo "done."
fi

echo
echo -e "\e[32m == Installing all extras == \e[0m"
./extras.sh all install


echo
echo -e "\e[32m == Syncing all dotfiles listed in 'known.txt' == \e[0m"
./quicksync.sh --from known.txt sync -y
sudo chsh $USER -s /usr/bin/zsh