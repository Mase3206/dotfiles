#!/bin/bash

# Uncomment for dry-run
# set -n

# Uncomment for verbose stack trace
# set -x


# DETECT OS AND DISTRO

function detect_os () {
	case $OSTYPE in 
		darwin*)
			OS_FAMILY="macos"
			detect_pkg_manager
			;;
		
		linux*)
			OS_FAMILY="linux"
			detect_pkg_manager
			;;
		
		freebsd*)
			OS_FAMILY="freebsd"
			detect_pkg_manager
			;;
		
		*)
			echo "OS could not be automatically detected."
			OS_FAMILY="unknown"
			manual_set_os

			detect_pkg_manager
			if [[ $OS_PKG_MANAGER == "unknown" ]]; then
				echo "Package manager could not be automatically detected."
				manual_set_pkg_manager
			fi
	esac

	echo "Detected OS family: $OS_FAMILY"
}


function detect_pkg_manager () {
	# debian
	if [ -x "$(command -v apt-get)" ]; then
		OS_PKG_MANAGER="apt-get"
	# rhel
	elif [ -x "$(command -v dnf)" ]; then
		OS_PKG_MANAGER="dnf"
	# suse
	elif [ -x "$(command -v zypper)" ]; then
		OS_PKG_MANAGER="zypper"
	# freebsd
	elif [ -x "$(command -v pkg)" ]; then
		OS_PKG_MANAGER="pkg"
	# macos
	elif [ -x "$(command -v brew)" ]; then
		OS_PKG_MANAGER="brew"
	# unknown
	else
		echo "Package manager not found." >&2
		OS_PKG_MANAGER="unknown"
		
		manual_set_pkg_manager
	fi

	[[ $OS_PKG_MANAGER != "unknown" ]] && echo "Detected package manager: $OS_PKG_MANAGER"
}


function manual_set_os () {
	os_options=(linux freebsd macos unknown)

	echo "Select the OS family:"
	select os in "${os_options[@]}"; do
		# Test if selected option is even within range
		if [[ "$REPLY" -gt 0 ]] && [[ "$REPLY" -le "${#os_options[@]}" ]]; then
			OS_FAMILY=$os
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
				OS_PKG_MANAGER=$pkg_mgr
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



function init () {
	detect_os
	
	if [[ $OS_FAMILY == "unknown" ]] || [[ $OS_PKG_MANAGER == "unknown" ]]; then
		echo "OS family and package manager could not be determined. This script will now exit."
		exit 1
	fi
}

init