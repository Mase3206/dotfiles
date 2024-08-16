#!/bin/sh

SHELL_SCRIPT_FILE_NAME="quicksync.sh"

function rm () {
	local type, continue
	[ -f $HOME/$1 ] && ! [ -L $HOME/$1 ] && type="regular file"
	[ -L $HOME/$1 ] && type="symlink"
	[ -d $HOME/$1 ] && type="directory"

	if [[ $type == "regular file" ]]; then
		echo -n "File $HOME/$1 is a regular file. Are you sure you want to remove it? [y/N] "
		read continue
		if [[ $continue == "y" ]] || [[ $continue == "Y" ]]; then
			echo -n "Removing regular file $HOME/$1... "
			rm $HOME/$1
			echo "done."
		else
			echo "Cancelling"
			exit 0
		fi
	
	elif [[ $type == "symlink" ]]; then
		echo -n "Removing symlink $HOME/$1... "
		rm $HOME/$1
		echo "done."
	
	elif [[ $type == "directory" ]]; then
		echo "I will not remove a directory. Cancelling"
		exit 1
	
	else
		echo "File $HOME/$1 has an unknown type. Cancelling"
		exit 1
	fi
}



function ln () {
	if [[ $1 == "-h" ]]; then
		cat << EOF
usage: $SHELL_SCRIPT_FILE_NAME ln [-h] src_file [dst_file]

	src_file: relative path to source file in dotfiles repo
		MUST be regular file
	
	dst_file (optional): relative path to destination file in home directory
		defaults to relative path of src_file if empty
EOF
		exit 0
	fi


	local type, continue, source, dest
	[ -f $HOME/$1 ] && ! [ -L $HOME/$1 ] && type="regular file"
	[ -L $HOME/$1 ] && type="symlink"
	[ -d $HOME/$1 ] && type="directory"

	source=$DOTFILES_DIR/$1
	[[ "$2" != ""]] && dest=$HOME/$2 || dest=$HOME/$1


	if [[ $type == "symlink" ]] || [[ $type == "directory" ]]; then
		echo "I will not link a $type. Canceling"
		exit 1

	elif [[ $type == "regular file" ]]; then
		echo -n "Creating symlink: $source -> $dest... "
		ln -s $source $dest
		echo "done."
	
	else
		echo "File $source has an unknown type. Cancelling"
		exit 1
	fi
}



function help () {
	cat << EOF
$0 subcommand args

Required environment variables:
	DOTFILES_DIR - absolute path to the dotfiles directory
EOF
}