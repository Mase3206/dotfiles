#!/bin/bash

# Uncomment for dry-run
# set -n

# Uncomment for verbose stack trace
# set -x


SHELL_SCRIPT_FILE_NAME="extras.sh"


# --------------------------------------
# DETECT OS AND DISTRO

function detect_os () {
	case $OSTYPE in 
		darwin*)
			DOTFILES_OS_FAMILY="macos"
			detect_pkg_manager
			;;
		
		linux*)
			DOTFILES_OS_FAMILY="linux"
			detect_pkg_manager
			;;
		
		freebsd*)
			DOTFILES_OS_FAMILY="freebsd"
			detect_pkg_manager
			;;
		
		*)
			echo "OS could not be automatically detected." >&2
			DOTFILES_OS_FAMILY="unknown"
			manual_set_os

			detect_pkg_manager
			if [[ $DOTFILES_PKG_MANAGER == "unknown" ]]; then
				echo "Package manager could not be automatically detected." >&2
				manual_set_pkg_manager
			fi
	esac

	# echo "Detected OS family: $DOTFILES_OS_FAMILY" >&2
}


function detect_pkg_manager () {
	# debian
	if [ -x "$(command -v apt-get)" ]; then
		DOTFILES_PKG_MANAGER="apt-get"
	# rhel
	elif [ -x "$(command -v dnf)" ]; then
		DOTFILES_PKG_MANAGER="dnf"
	# suse
	elif [ -x "$(command -v zypper)" ]; then
		DOTFILES_PKG_MANAGER="zypper"
	# freebsd
	elif [ -x "$(command -v pkg)" ]; then
		DOTFILES_PKG_MANAGER="pkg"
	# macos
	elif [ -x "$(command -v brew)" ]; then
		DOTFILES_PKG_MANAGER="brew"
	# unknown
	else
		echo "Package manager not found." >&2
		DOTFILES_PKG_MANAGER="unknown"
		
		manual_set_pkg_manager
	fi

	# [[ $DOTFILES_PKG_MANAGER != "unknown" ]] && echo "Detected package manager: $DOTFILES_PKG_MANAGER" >&2
}


function manual_set_os () {
	os_options=(linux freebsd macos unknown)

	echo "Select the OS family:"
	select os in "${os_options[@]}"; do
		# Test if selected option is even within range
		if [[ "$REPLY" -gt 0 ]] && [[ "$REPLY" -le "${#os_options[@]}" ]]; then
			DOTFILES_OS_FAMILY=$os
			break
		else
			echo "Unknown option $REPLY. Please choose an option between 1 and ${#os_options[@]}."
		fi
	done
}


function manual_set_pkg_manager () {
	pkg_mgr_options=(apt-get dnf zypper pkg brew unknown)
	
	echo ""; echo "Select the package manager:"

	select pkg_mgr in ${pkg_mgr_options[@]}; do
		# Test if selected option is even within range
		if [[ $REPLY -gt 0 ]] && [[ $REPLY -le ${#pkg_mgr_options[@]} ]]; then

			# Test if selected package manager is installed. Display error and re-prompt if not.
			if [ -x "$(command -v $pkg_mgr)" ]; then
				DOTFILES_PKG_MANAGER=$pkg_mgr
				break
			else
				echo "Selected package manager '$pkg_mgr' is not installed."
				echo ""; echo "Select the package manager:"
			fi
		
		else
			echo "Unknown option $REPLY. Please choose an option between 1 and ${#pkg_mgr_options[@]}."
		fi
	done
}



# --------------------------------------
# SCRIPT INITIALIZATION
# SUBCOMMAND PARSING
# GLOBAL HELP

function init () {
	detect_os
	
	if [[ $DOTFILES_OS_FAMILY == "unknown" ]] || [[ $DOTFILES_PKG_MANAGER == "unknown" ]]; then
		echo "OS family and package manager could not be determined. This script will now exit."
		exit 1
	fi
}


function parse_subcommand () {
	case $1 in 
		zsh)
			zsh $2 $3 $4
			;;

		oh-my-zsh | oh_my_zsh | omz)
			oh_my_zsh $2 $3 $4
			;;

		*)
			echo "error: Missing required parameter" >&2
			do_help
			exit 1
	
	esac
		
}


function do_help () {
	cat << EOF
$SHELL_SCRIPT_FILE_NAME [-h] <module> <command>

Modules: 
	\`zsh\`: Zsh
	\`omz\`: Oh My Zsh
	\`all\`: apply command to all

Global Options:
	\`-h\`: Display this help text

Required environment variables:
	DOTFILES_DIR - absolute path to the dotfiles repository
		CAN be set via \`export\` or in-line. Separate declaration and command with a space.
EOF
}



# --------------------------------------
# PACKAGE/APP-SPECIFIC STUFF

function zsh {
	case $1 in 
		detect)
			zsh_detect
			;;
		
		install)
			zsh_install
			;;

		*)
			zsh_help $1

	esac


}


function zsh_detect () {
	if [ -x "$(command -v zsh)" ]; then 
		echo "Zsh is installed." 
		DOTFILES_ZSH_INSTALLED=1
	else
		echo "Zsh is NOT installed."
		DOTFILES_ZSH_INSTALLED=0
	fi
}


function zsh_install () {
	# test if Zsh is already installed
	zsh_detect
	if [[ $DOTFILES_ZSH_INSTALLED == 1 ]]; then
		echo "Zsh is already installed!"
		exit 2
	fi

	$DOTFILES_PKG_MANAGER install -y zsh
	# back up existing .zshrc before syncing it with repo
	mv ~/.zshrc ~/.zshrc.dotbak
	$DOTFILES_DIR/quicksync.sh sync .zshrc
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



function oh_my_zsh {
	case $1 in
		detect) 
			omz_detect
			;;

		install)
			# TODO - Test this in a docker container!
			omz_install
			;;

		*)
			omz_help $1

	esac


}


function omz_detect () {
	if [ -d ~/.oh-my-zsh ]; then
		echo "Oh My Zsh is installed."
		DOTFILES_OMZ_INSTALLED=1
	else
		echo "Oh My Zsh is NOT installed."
		DOTFILES_OMZ_INSTALLED=0
	fi
}


function omz_install () {
	local tempfold curdir

	omz_detect
	if [[ $DOTFILES_OMZ_INSTALLED == 1 ]]; then
		echo "Oh My Zsh is already installed!"
		exit 2
	fi

	# prep folders
	tempfold=$(mktemp -d)
	curdir=$(pwd)

	# download install script
	cd $tempfold
	curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh > install.sh

	# run with these specific environment variables
	# CHSH='yes' - tells install.sh to set Zsh as the default shell for this user
	# RUNZSH='no' - tells install.sh not to run Zsh after the install
	# KEEP_ZSHRC='yes' - tells install.sh not to create a backup of the existing .zshrc file
	CHSH='yes' RUNZSH='no' KEEP_ZSHRC='yes' sh install.sh --unattended --skip-chsh
	echo ""; echo "Changing $USER's shell to /usr/bin/zsh"
	chsh $USER -s /usr/bin/zsh

	rm install.sh
	cd $curdir

	# automatically sync Terse OMZ theme from repo
	$DOTFILES_DIR/quicksync.sh ln .oh-my-zsh/themes/terse.zsh-theme
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




# -------------------------------------
# MAIN LOOP

# check if DOTFILES_DIR is set; if not, error out
[ -z $DOTFILES_DIR ] && echo "Required ENV variable \`DOTFILES_DIR\` is not set! Please set via inline declaration or via \`export\`." && exit 5


init


# check global options
case $1 in
	-h | help) 
		# display help
		do_help
		exit 0
		;;

	*)
		# if nothing here matches, just initialize os-specific variables and send it all to parse_subcommand
		init
		parse_subcommand $1 $2 $3
		;;

esac

