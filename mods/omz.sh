#!/usr/bin/env bash

# function mod_omz {
# 	case $1 in
# 		detect) 
# 			omz_detect
# 			;;

# 		install)
# 			omz_install
# 			;;

# 		*)
# 			omz_help $1

# 	esac


# }

function omz_detect () {

	if [ -d ~/.oh-my-zsh ]; then
		./outputs.sh status_good "OMZ install status" "already installed!"
		DOTFILES_OMZ_INSTALLED=1
	else
		./outputs.sh status_bad "OMZ install status" "NOT installed."
		DOTFILES_OMZ_INSTALLED=0
	fi
}


function omz_install () {
	./outputs.sh subheader "Installing Oh My Zsh"

	local tempfold curdir

	omz_detect
	if [[ $DOTFILES_OMZ_INSTALLED == 1 ]]; then
		echo -e "\e[31mSkipping\e[0m OMZ installation."
		return
	fi
	echo

	# prep folders
	tempfold=$(mktemp -d)
	curdir=$(pwd)

	# download install script
	./outputs.sh step "Downloading install script"
	cd $tempfold
	curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh > install.sh

	# run with these specific environment variables
	# CHSH='yes' - tells install.sh to set Zsh as the default shell for this user
	# RUNZSH='no' - tells install.sh not to run Zsh after the install
	# KEEP_ZSHRC='yes' - tells install.sh not to create a backup of the existing .zshrc file
	$DOTFILES_DIR/outputs.sh step "Instaling OMZ"
	CHSH='yes' RUNZSH='no' KEEP_ZSHRC='yes' sh install.sh --unattended --skip-chsh > /dev/null 2> /dev/null
	$DOTFILES_DIR/outputs.sh step "Changing $USER's shell to /usr/bin/zsh"
	chsh $USER -s /usr/bin/zsh > /dev/null

	$DOTFILES_DIR/outputs.sh step "Cleaning up"
	rm install.sh
	cd $curdir

	./outputs.sh step "Linking OMZ dotfiles"
	# automatically sync Terse OMZ theme from repo
	$DOTFILES_DIR/quicksync.sh ln .oh-my-zsh/themes/terse.zsh-theme > /dev/null
}


function omz_help () {
	cat << EOF
$SHELL_SCRIPT_FILE_NAME omz [-h] <command>

Commands:
\`detect\`: Detect existing install and display its status
\`install\`: Install Oh My Zsh
EOF
	[[ "$1" == "-h" ]] && exit 0 || exit 1
}


case $1 in
	detect) omz_detect ;;
	install) omz_install ;;
	*) omz_help $1
esac
