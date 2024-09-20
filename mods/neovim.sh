#!/usr/bin/env bash

# used to properly show $0 and enforce running via extras.sh
if [[ -n $DOTFILES_MODS_RUNNER ]]; then
	SHELL_SCRIPT_FILE_NAME="$DOTFILES_MODS_RUNNER neovim"
else 
	echo "You must run this script through extras.sh, as it initializes critical environment variables used for installation and detection."
	exit 1
fi


function neovim_detect () {
	if command -v nvim > /dev/null; then 
		./outputs.sh status_good "Neovim install status" "already installed!" 
		DOTFILES_NEOVIM_INSTALLED=1
	else
		./outputs.sh status_bad "Neovim install status" "NOT installed."
		DOTFILES_NEOVIM_INSTALLED=0
	fi
}


function neovim_install () {
	./outputs.sh subheader "Installing Neovim"

	# test if Zsh is already installed
	neovim_detect
	if [[ $DOTFILES_NEOVIM_INSTALLED == 1 ]]; then
		echo -e "\e[31mSkipping\e[0m Neovim installation."
		return
	fi
	echo

	# RHEL systems require EPEL to be installed and CRB to be enabled
	if [[ $DOTFILES_OS_RHEL == 1 ]]; then
		./outputs.sh step "Installing the Extra Packages for Enterprise Linux (EPEL) repository - this is where Neovim is located"
		sudo dnf install -y epel-release 2>&1 > /dev/null

		./outputs.sh step "Enabling the CodeReady Builder (CRB) repository - required for many EPEL packages"
		/usr/bin/crb enable > /dev/null
	fi

	./outputs.sh step "Installing Neovim using $DOTFILES_PKG_MANAGER"
	if [[ $DOTFILES_PKG_MANAGER == "zypper" ]]; then
		# if opensuse, busybox-which conflicts with gnu-which required by neovim, so --force-resolution must be passed to force it to fix it
		# ./outputs.sh step "Removing busybox-which, as it conflicts with gnu-which required by neovim"
		sudo zypper install -y --force-resolution neovim > /dev/null 2> /dev/null
	else
		sudo $DOTFILES_PKG_MANAGER install -y neovim > /dev/null 2> /dev/null
	fi
}


function neovim_help () {
	cat << EOF
$SHELL_SCRIPT_FILE_NAME [-h] <command>

Commands:
\`detect\`: Detect existing install and display its status
\`install\`: Install Neovim
EOF
	[[ "$1" == "-h" ]] && exit 0 || exit 1
}


case $1 in
	detect) neovim_detect ;;
	install) neovim_install ;;
	*) neovim_help $1
esac
