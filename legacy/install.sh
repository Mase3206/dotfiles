#!/usr/bin/env bash

./outputs.sh big_header "Running pre-checks"

# try to move the cursor up one line to remove an extra space below big_header
tput cuu1
./outputs.sh subheader "Ensuring the \$USER variable is set"
if [ -z $USER ]; then
	./outputs.sh status_bad "\$USER variable" "NOT set"

	m="Setting to $(id -un) (collected from \`id -un\`)"
	./outputs.sh step "$m"
	export USER=$(id -un)

	# echo; echo "It's recommended to logout and log back in, as manually setting the \$USER variable may cause issues. Logging out and back in should fix this." >&2
else
	./outputs.sh status_good "\$USER variable" "set"
fi


./outputs.sh subheader "Checking if \$DOTFILES_DIR is set"

# If $DOTFILES_DIR is unset, assume current directory
if [ -z $DOTFILES_DIR ]; then
	./outputs.sh status_bad "\$DOTFILES_DIR" "NOT set"

	m="Setting \$DOTFILES_DIR. Assuming current directory: $(pwd)"
	./outputs.sh step "$m"
	export DOTFILES_DIR=$(pwd)

	# add to ~/.aliases so it's sourced
	./outputs.sh step "Adding new \$DOTFILES_DIR export to ~/.aliases"
	echo "export DOTFILES_DIR=$DOTFILES_DIR" >> ~/.aliases
else
	m="set to $DOTFILES_DIR."
	./outputs.sh status_good "\$DOTFILES_DIR" "$m"
fi

sleep .2
./outputs.sh big_header "Installing all extras"
./extras.sh all install


sleep .2
./outputs.sh big_header "Syncing all dotfiles listed in 'known.txt'"
./quicksync.sh --from known.txt sync -y


sleep .2
m="Ensuring $USER's shell was changed to Zsh"
./outputs.sh big_header "$m"
current_shell=$(cat /etc/passwd | grep "^$USER" | awk -F: '{print $7}')

if [[ "$current_shell" != '/usr/bin/zsh' ]]; then
	m="$USER's login shell"
	./outputs.sh status_bad "$m" "$current_shell"

	m="Changing $USER's shell to '/usr/bin/zsh'"
	./outputs.sh step "$m"
	sudo chsh $USER -s /usr/bin/zsh > /dev/null
else
	m="$USER's login shell"
	./outputs.sh status_good "$m" "/usr/bin/zsh"
fi
unset current_shell


./outputs.sh big_header "Done!"