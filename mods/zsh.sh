#!/usr/bin/env bash

function zsh_detect () {
	if command -v zsh > /dev/null; then 
		./outputs.sh status_good "Zsh install status" "already installed!" 
		DOTFILES_ZSH_INSTALLED=1
	else
		./outputs.sh status_bad "Zsh install status" "NOT installed."
		DOTFILES_ZSH_INSTALLED=0
	fi
}


function zsh_install () {
	./outputs.sh subheader "Installing Zsh"

	# test if Zsh is already installed
	zsh_detect
	if [[ $DOTFILES_ZSH_INSTALLED == 1 ]]; then
		echo -e "\e[31mSkipping\e[0m Zsh installation."
		return
	fi
	echo

	./outputs.sh step "Installing Zsh using $DOTFILES_PKG_MANAGER"
	sudo $DOTFILES_PKG_MANAGER install -y zsh > /dev/null

	# back up existing .zshrc before syncing it with repo
	[ -f ~/.zshrc ] && ./outputs.sh step "Backing up existing .zshrc before syncing" && mv ~/.zshrc ~/.zshrc.dotbak

	# touch a new .zshrc file temporarily to avoid missing file warning
	# allows other errors to pass through if 
	./outputs.sh step "Linking Zsh dotfiles"
	$DOTFILES_DIR/quicksync.sh ln .zshrc -y > /dev/null
}


function zsh_help () {
	cat << EOF
$SHELL_SCRIPT_FILE_NAME zsh [-h] <command>

Commands:
\`detect\`: Detect existing install and display its status
\`install\`: Install Zsh using detected package manager
EOF
	[[ "$1" == "-h" ]] && exit 0 || exit 1
}


case $1 in 
	detect) zsh_detect ;;
	install) zsh_install ;;
	*) zsh_help $1
esac
