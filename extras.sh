#!/bin/bash

# Uncomment for dry-run
# set -n

# Uncomment for verbose stack trace
# set -x


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
			echo "OS could not be automatically detected."
			DOTFILES_OS_FAMILY="unknown"
			manual_set_os

			detect_pkg_manager
			if [[ $DOTFILES_PKG_MANAGER == "unknown" ]]; then
				echo "Package manager could not be automatically detected."
				manual_set_pkg_manager
			fi
	esac

	echo "Detected OS family: $DOTFILES_OS_FAMILY"
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

	[[ $DOTFILES_PKG_MANAGER != "unknown" ]] && echo "Detected package manager: $DOTFILES_PKG_MANAGER"
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
			echo "Missing required parameter"
			do_help
			exit 1
	
	esac
		
}



# --------------------------------------
# PACKAGE/APP-SPECIFIC STUFF

function zsh {
	local option
	option=$1

	case $option in 
		detect)
			if [ -x "$(command -v zsh)" ]; then 
				echo "Zsh is installed." 
				DOTFILES_ZSH_INSTALLED=1
			else
				echo "Zsh is NOT installed."
				DOTFILES_ZSH_INSTALLED=0
			fi
			;;
		
		install)
			$DOTFILES_PKG_MANAGER install -y zsh
	
	esac
}

function oh_my_zsh {
	local option
	option=$1

	case $option in
		detect) 
			if [ -d ~/.oh-my-zsh ]; then
				echo "Oh My Zsh is installed."
				DOTFILES_OMZ_INSTALLED=1
			else
				echo "Oh My Zsh is NOT installed."
				DOTFILES_OMZ_INSTALLED=0
			fi
			;;

		install)
			CHSH='yes' RUNZSH='no' KEEP_ZSHRC='yes'
		
	esac
}




# -------------------------------------
# MAIN LOOP

# check global options
case $1 in
	-h | help) 
		# display help
		do_help
		;;

	*)
		# if nothing here matches, just send it all to parse_subcommand
		parse_subcommand $1 $2 $3
		;;

esac

init