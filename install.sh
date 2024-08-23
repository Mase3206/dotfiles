#!/bin/bash

set -e

function big_header () {
	echo; echo; echo -e "\e[32m========  $1  ========\e[0m"; echo
}

function subheader () {
	echo; echo -e "\e[34m----  $1  ----\e[0m"
}

function step () {
	echo -e "\e[36m- $1\e[0m"
}

function status_bad () {
	echo -e "$1: \e[31m$2\e[0m"
}

function status_good () {
	echo "$1: $2"
}


big_header "Running pre-checks"

# move the cursor up one line to remove an extra space below big_header
tput cuu1
subheader "Ensuring the \$USER variable is set"
if [ -z $USER ]; then
	status_bad "\$USER variable" "NOT set"

	step "Setting to $(id -un) (collected from \`id -un\`)"
	export USER=$(id -un)

	# echo; echo "It's recommended to logout and log back in, as manually setting the \$USER variable may cause issues. Logging out and back in should fix this." >&2
else
	status_good "\$USER variable:" "set"
fi


subheader "Checking if \$DOTFILES_DIR is set"

# If $DOTFILES_DIR is unset, assume current directory
if [ -z $DOTFILES_DIR ]; then
	status_bad "\$DOTFILES_DIR" "NOT set"

	step "Setting \$DOTFILES_DIR. Assuming current directory: $(pwd)"
	export DOTFILES_DIR=$(pwd)

	# add to ~/.aliases so it's sourced
	step "Adding new \$DOTFILES_DIR export to ~/.aliases"
	echo "export DOTFILES_DIR=$DOTFILES_DIR" >> ~/.aliases
else
	status_good "\$DOTFILES_DIR" "set to $DOTFILES_DIR."
fi

sleep .2
big_header "Installing all extras"
./extras.sh all install


sleep .2
big_header "Syncing all dotfiles listed in 'known.txt'"
./quicksync.sh --from known.txt sync -y


sleep .2
big_header "Ensuring $USER's shell was changed to Zsh"
current_shell=$(cat /etc/passwd | grep "^$USER" | awk -F: '{print $7}')

if [[ "$current_shell" != '/usr/bin/zsh' ]]; then
	status_bad "$USER's login shell" "$current_shell"
	step "Changing $USER's shell to '/usr/bin/zsh'"
	sudo chsh $USER -s /usr/bin/zsh > /dev/null
else
	status_good "$USER's login shell" "/usr/bin/zsh"
fi
unset current_shell


big_header "Done!"