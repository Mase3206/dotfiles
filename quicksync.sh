#!/bin/bash

SHELL_SCRIPT_FILE_NAME="quicksync.sh"


function do_rm () {
	# abort if no arguments are given
	[ -z $1 ] && echo "No file given. Run with \`-h\` for usage." && exit 1

	# USAGE
	if [[ $1 == "-h" ]]; then
		cat << EOF
$SHELL_SCRIPT_FILE_NAME rm [-h] <file>

Arguments:
	\`file\`: Relative path to file in home directory
		MUST not be a directory

Options:
	\`-h\`: Display this help text
EOF
		exit 0
	fi

	local type continue
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



function do_ln () {
	# abort if no arguments are given
	[ -z $1 ] && echo "No file(s) given. Run with \`-h\` for usage." && exit 1

	# USAGE
	if [[ $1 == "-h" ]]; then
		cat << EOF
usage: $SHELL_SCRIPT_FILE_NAME ln [-h] <src_file> [dst_file]

Arguments:
	\`src_file\`: Relative path to source file in dotfiles repo
		MUST be regular file or directory
	
	\`dst_file\` (optional): Relative path to destination file in home directory
		DEFAULTS to relative path of src_file if empty
		MUST not already exist

Options:
	\`-h\`: Display this help text
EOF
		exit 0
	fi


	local type continue source dest

	# create source and dest variables for easier scripting
	source=$DOTFILES_DIR/$1
	[ "$2" == "" ] && dest=$HOME/$1 || dest=$HOME/$2

	# get the type of the source file
	[ -f $source ] && ! [ -L $source ] && type="regular file"
	[ -L $source ] && type="symlink"
	[ -d $source ] && type="directory"

	# DEST PATH TYPE CHECKS
	# regular file -> fail
	if [ -f $dest ] && ! [ -L $dest ]; then
		echo "Destination file $dest already exists and is a regular file. You can remove it with \`$SHELL_SCRIPT_FILE_NAME rm\`."
		exit 2

	# already linked -> fail
	elif [ -L $dest ]; then
		echo "Destination file is already symlinked to $(readlink $dest). You can remove it with \`$SHELL_SCRIPT_FILE_NAME rm\`."
		exit 2
	
	# directory -> fail
	elif [ -d $dest ]; then
		echo "Destination $dest is an existing directory. You'll need to delete it manually before continuing. Be 100% sure you're doing this right first though!"
		exit 2
	fi

	# SOURCE PATH TYPE CHECKS
	# symlink -> fail
	if [[ $type == "symlink" ]]; then
		echo "I will not link from a symlink. Canceling"
		exit 1

	# regular file
	elif [[ $type == "regular file" ]]; then
		echo -n "Creating symlink: $source -> $dest... "
		ln -s $source $dest
		echo "done."

	elif [[ $type == "directory" ]]; then
		echo -n "Source $source is a directory. Are you sure you want to link this? [y/N] "
		read continue
		if [[ $continue == "y" ]] || [[ $continue == "Y" ]]; then
			echo "Creating symlink: $source -> $dest... "
			ln -s $source $dest
			echo "done."
		else
			echo "Cancelling"
			0
		fi
	
	else
		echo "File $source has an unknown type. Cancelling"
		exit 1
	fi
}



function do_help () {
	cat << EOF
$SHELL_SCRIPT_FILE_NAME subcommand args

Subcommands: 
	\`ln\`: Link file or directory from dotfiles repo to home directory
	\`rm\`: Remove file or symlink from home directory
	\`sync\`: Remove and re-link file or directory (helpful if source file path changed)

Global Options:
	\`--from\`: Use newline-separated file names listed in a text file
	\`-h\`: Display this help text

Required environment variables:
	DOTFILES_DIR - absolute path to the dotfiles directory
		CAN be set via \`export\` or in-line. Separate declaration and command with a space.
EOF
}


function parse_subcommand () {
	# echo $1 $2 $3 $4 $5
	case $1 in
		rm) 
			# remove file in $2
			# do_rm $2

			# use `eval` to expand brace expressions
			eval "files=($2)"

			# iterate over expanded files
			for file in "${files[@]}"; do
				do_rm "$file"
			done
			;;

		ln)
			# link file/dir from $2 to $3 (if $3 is given)
			# do_ln $2 $3

			# Use `eval` to expand brace expressions
			eval "sources=($2)"
			eval "destinations=($3)"

			# verify that len(sources) == len(destinations) or that destinations is empty
			if [ ${#sources[@]} -ne ${#destinations[@]} ] && [[ ${#destinations[@]} -ne 0 ]]; then
				echo "The number of sources and destinations given do not match. Cancelling"
				exit 1
			elif [[ ${#destinations[@]} -eq 0 ]]; then
				destinations=$sources
			else
				echo "fuck"
				exit 49
			fi
			
			# iterate over expanded items
			for i in "${!sources[@]}"; do
				do_ln "${sources[$i]}" "${destinations[$i]}"
			done
			;;

		sync) 
			# remove and re-link file/dir from $2 to $3

			local sync_help
			function sync_help () {
				cat << EOF
$SHELL_SCRIPT_FILE_NAME sync <src_file> [dst_file]

Arguments:
	\`src_file\`: Relative path to source file in dotfiles repo
		MUST be regular file or directory
	
	\`dst_file\` (optional): Relative path to destination file in home directory
		DEFAULTS to relative path of src_file if empty
		MUST not already exist

Options: 
	\`-h\`: Display this help text
EOF
			}

			# help text
			if [[ "$2" == "-h" ]]; then
				sync_help
				exit 0
			elif [[ "$2" == "" ]]; then
				echo "Missing required argument: src_file. Run with \`-h\` for usage."
				sync_help
				exit 1
			fi
			
			# use `eval` to expand brace expressions
			eval "sources=($2)"
			eval "destinations=($3)"

			# verify that len(sources) == len(destinations) or that destinations is empty
			if [ ${#sources[@]} -ne ${#destinations[@]} ] && [[ ${#destinations[@]} -ne 0 ]]; then
				echo "The number of sources and destinations given do not match. Cancelling"
				exit 1
			elif [[ ${#destinations[@]} -eq 0 ]]; then
				destinations=$sources
			else
				echo "fuck"
				exit 49
			fi

			# iterate over expanded items
			for i in "${!sources[@]}"; do
				echo -n "Removing and re-linking ${sources[$i]} to ${destinations[$i]}... "
				do_rm "${destinations[$i]}" > /dev/null
				do_ln "${sources[$i]}" "${destinations[$i]}" > /dev/null
				echo "done."
			done
			;;
		
		*)
			# doesn't match any of the above
			echo "Unknown or missing subcommand."
			do_help
			;;
	esac
}


# check global options
case $1 in
	-h | help) 
		# display help
		do_help
		;;

	
	--from)
		# check if given file exists and process it
		# $2 = file name
		if [ -f $2 ]; then
			# initialize empty array
			known_files=()

			# read each line from file and add it to array
			while IFS= read -r line; do
				known_files+=("$line")
			done < "$2"
			echo "Found: ${known_files[@]}"
			echo

			# $3 = subcommand
			for i in "${!known_files[@]}"; do
				# echo "Running $3 with ${known_files[$i]}"
				parse_subcommand $3 "${known_files[$i]}"
			done
		else
			echo "Given file $2 does not exist. Cancelling"
			exit 1
		fi
		;;


	*)
		# send all other things to parse_subcommand
		parse_subcommand $1 $2 $3
		;;
esac
