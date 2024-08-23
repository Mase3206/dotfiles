#!/bin/bash

# Uncomment for dry-run
# set -n

# Uncomment for verbose stack trace
# set -x


SHELL_SCRIPT_FILE_NAME="extras.sh"


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
	step "Detecting OS and package manager"
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

		all)
			zsh $2 $3 $4
			echo; sleep 1
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
	# echo -n ": "

	if [ -x "$(command -v zsh)" ]; then 
		status_good "Zsh install status" "already installed!" 
		DOTFILES_ZSH_INSTALLED=1
	else
		status_bad "Zsh install status" "NOT installed."
		DOTFILES_ZSH_INSTALLED=0
	fi
}


function zsh_install () {
	subheader "Installing Zsh"

	# test if Zsh is already installed
	zsh_detect
	if [[ $DOTFILES_ZSH_INSTALLED == 1 ]]; then
		echo -e "\e[31mSkipping\e[0m Zsh installation."
		return
	fi
	echo

	step "Installing Zsh using $DOTFILES_PKG_MANAGER"
	sudo $DOTFILES_PKG_MANAGER install -y zsh > /dev/null

	# back up existing .zshrc before syncing it with repo
	[ -f ~/.zshrc ] && step "Backing up existing .zshrc before syncing" && mv ~/.zshrc ~/.zshrc.dotbak

	# touch a new .zshrc file temporarily to avoid missing file warning
	# allows other errors to pass through if 
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


# --------------------------------------

function oh_my_zsh {
	case $1 in
		detect) 
			omz_detect
			;;

		install)
			omz_install
			;;

		*)
			omz_help $1

	esac


}

function omz_detect () {

	if [ -d ~/.oh-my-zsh ]; then
		status_good "OMZ install status" "already installed!"
		DOTFILES_OMZ_INSTALLED=1
	else
		status_bad "OMZ install status" "NOT installed."
		DOTFILES_OMZ_INSTALLED=0
	fi
}


function omz_install () {
	subheader "Installing Oh My Zsh"

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
	step "Downloading install script"
	cd $tempfold
	curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh > install.sh

	# run with these specific environment variables
	# CHSH='yes' - tells install.sh to set Zsh as the default shell for this user
	# RUNZSH='no' - tells install.sh not to run Zsh after the install
	# KEEP_ZSHRC='yes' - tells install.sh not to create a backup of the existing .zshrc file
	step "Instaling OMZ"
	CHSH='yes' RUNZSH='no' KEEP_ZSHRC='yes' sh install.sh --unattended --skip-chsh > /dev/null 2> /dev/null
	echo -e "\e[36m- Changing $USER's shell to /usr/bin/zsh\e[0m"
	# chsh $USER -s /usr/bin/zsh > /dev/null

	step "Cleaning up"
	rm install.sh
	cd $curdir

	step "Syncing custom OMZ theme"
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
		parse_subcommand $1 $2 $3
		;;

esac

