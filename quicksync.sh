#!/bin/bash

# set -x

SHELL_SCRIPT_FILE_NAME="quicksync.sh"


# function big_header () {
# 	echo; echo; echo -e "\e[32m========  $1  ========\e[0m"; echo
# }

# function subheader () {
# 	echo; echo -e "\e[34m----  $1  ----\e[0m"
# }

# function step () {
# 	echo -e "\e[36m- $1\e[0m"
# }

# function status_bad () {
# 	echo -e "$1: \e[31m$2\e[0m"
# }

# function status_good () {
# 	echo "$1: $2"
# }





function do_rm () {
	# abort if no arguments are given
	[ -z $1 ] && echo "error rm: Missing required argument: file. Run with \`-h\` for usage." >&2 && exit 1

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

	# get file type
	[ -f $HOME/$1 ] && ! [ -L $HOME/$1 ] && type="regular file"
	[ -L $HOME/$1 ] && type="symlink"
	[ -d $HOME/$1 ] && type="directory"
	# echo $type

	# TYPE CHECKS
	# regular file -> warning
	if [[ $type == "regular file" ]]; then
		
		# if `-y` is passed, bypass confirmation prompt
		if [[ $force_yes == 0 ]]; then
			echo -n "File $HOME/$1 is a regular file. Are you sure you want to remove it? [y/N] "
			read continue
		else
			continue="y"
		fi

		if [[ $continue == "y" ]] || [[ $continue == "Y" ]]; then
			echo -n "Removing regular file $HOME/$1... "
			rm $HOME/$1
			echo "done."
		else
			echo "Cancelling"
			exit 0
		fi
	
	# symlink
	elif [[ $type == "symlink" ]]; then
		echo -n "Removing symlink $HOME/$1... "
		rm $HOME/$1
		echo "done."
	
	# directory -> fail if not force_yes
	elif [[ $type == "directory" ]]; then
        if [[ $force_yes == 1 ]]; then
            rm -r $HOME/$1
        else
		    echo "error rm: I will not remove a directory. Cancelling" >&2
		    exit 1
        fi

	# nonexistent -> skip
	elif ! [[ $type == "exists" ]]; then
		echo "error rm: File $HOME/$1 doesn't exist or may have already been removed. Skipping" >&2
	
	# unknown/nonexistent
	else
		# nonexistent -> skip
		if ! [ -e $HOME/$1 ]; then
			echo "error rm: File $HOME/$1 doesn't exist or may have already been removed. Skipping" >&2

		# unknown -> fail
		else
			echo "error rm: File $HOME/$1 has an unknown type. Cancelling" >&2
			exit 1
		fi
	fi
}



function do_ln () {
	# abort if no arguments are given
	[ -z $1 ] && echo "error ln: Missing required argument: src_file. Run with \`-h\` for usage." >&2 && exit 1

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
		echo "error ln: Destination file $dest already exists and is a regular file. You can remove it with \`$SHELL_SCRIPT_FILE_NAME rm\`." >&2
		exit 2

	# already linked -> fail
	elif [ -L $dest ]; then
		echo "error ln: Destination file is already symlinked to $(readlink $dest). You can remove it with \`$SHELL_SCRIPT_FILE_NAME rm\`." >&2
		exit 2
	
	# directory -> fail
	elif [ -d $dest ]; then
		echo "error ln: Destination $dest is an existing directory. You'll need to delete it manually before continuing. Be 100% sure you're doing this right first though!" >&2
		exit 2
	fi

	# SOURCE PATH TYPE CHECKS
	# symlink -> fail
	if [[ $type == "symlink" ]]; then
		echo "error ln: I will not link from a symlink. Canceling" >&2
		exit 1

	# regular file
	elif [[ $type == "regular file" ]]; then
		echo -n "Creating symlink: $source -> $dest... "
		ln -s $source $dest
		echo "done."

	# directory -> warn
	elif [[ $type == "directory" ]]; then

		# if `-y` is passed, bypass confirmation prompt
		if [[ $force_yes == 0 ]]; then
			echo -n "Source $source is a directory. Are you sure you want to link this? [y/N] " >&2
			read continue
		else
			continue="y"
		fi

		if [[ $continue == "y" ]] || [[ $continue == "Y" ]]; then
			echo "Creating symlink: $source -> $dest... "
			ln -s $source $dest
			echo "done."
		else
			echo "Cancelling"
			exit 0
		fi
	
	# unknown -> fail
	else
		echo "error ln: Source file $source has an unknown type. Cancelling" >&2
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

			# verify that len(sources) == len(destinations)
			if [ ${#sources[@]} -ne ${#destinations[@]} ] && [[ ${#destinations[@]} -ne 0 ]]; then
				echo "error ln: The number of sources and destinations given do not match. Cancelling" >&2
				exit 1
			
			# OR destinations is empty
			elif [[ ${#destinations[@]} -eq 0 ]]; then
				destinations=("${sources[@]}")
			
			# otherwise, the brace expressions probably weren't in quotes
			else
				echo "error ln: Brace expressions need to be enclosed in double-quotes." >&2
				exit 1
			fi
			
			# iterate over expanded items
			for i in "${!sources[@]}"; do
				do_ln "${sources[$i]}" "${destinations[$i]}"
			done
			;;

		sync)			
			# remove and re-link file/dir from $2 to $3
			# help text
			if [[ "$2" == "-h" ]]; then
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
				exit 0
			elif [[ "$2" == "" ]]; then
				echo "error sync: Missing required argument: src_file. Run with \`-h\` for usage." >&2
				# sync_help
				exit 1
			fi

			# use `eval` to expand brace expressions
			eval "sources=($2)"
			eval "destinations=($3)"

			# maybe len(sources) != len(destinations) and destinations is not empty
			if [ ${#sources[@]} -ne ${#destinations[@]} ] && [[ ${#destinations[@]} -ne 0 ]]; then
				echo "error sync: The number of sources and destinations given do not match. Cancelling" >&2
				exit 1
			
			# OR destinations is empty
			elif [[ ${#destinations[@]} -eq 0 ]]; then
				destinations=("${sources[@]}")
			fi

			# otherwise, the brace expressions probably weren't in quotes
			# else
			# 	echo "${sources[@]}" "${#sources[@]}"
			# 	echo "${destinations[@]}" "${#destinations[@]}"
			# 	echo "error sync: Brace expressions need to be enclosed in double-quotes." >&2
			# 	exit 1
			# fi

			# iterate over expanded items
			for i in "${!sources[@]}"; do
				# echo ${sources[$i]}
				# echo ${destinations[$i]}
				if [[ "${sources[$i]}" != "${destinations[$i]}" ]]; then
					m="Removing and re-linking ${sources[$i]} to ${destinations[$i]}"
					./outputs.sh step "$m"
				else
					m="Removing and re-linking ${sources[$i]}"
					./outputs.sh step "$m"
				fi

				# run `rm` and `ln`
				do_rm "${destinations[$i]}" > /dev/null
				do_ln "${sources[$i]}" "${destinations[$i]}" > /dev/null
			done
			;;
		
		*)
			# doesn't match any of the above
			echo "error: Unknown or missing subcommand." >&2
			do_help
			;;
	esac
}


# check if DOTFILES_DIR is set; if not, error out
[ -z $DOTFILES_DIR ] && echo "Required ENV variable \`DOTFILES_DIR\` is not set! Please set via inline declaration or via \`export\`." && exit 5


# Check if `-y` is present
# `-y` automatically answers "yes" to all y/n prompts
# if `-y` is detected, remove it from $@
force_yes=0
filtered_args=()

for arg in "$@"; do
	if [[ "$arg" == "-y" ]]; then
		force_yes=1
	else
		filtered_args+=("$arg")
	fi
done

# re-set the positional parameters to the filtered args (excluding `-y`)
set -- "${filtered_args[@]}"


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
			echo -n "Found: "
			for i in "${!known_files[@]}"; do
				echo -n "${known_files[$i]}"
				! (( 1 + i == ${#known_files[@]} )) && echo -n ", "
			done 
			echo; echo

			# $3 = subcommand
			for i in "${!known_files[@]}"; do
				# echo "Running $3 with ${known_files[$i]}"
				force_yes=1 parse_subcommand $3 "${known_files[$i]}" $4
			done
		else
			echo "error: Given file $2 does not exist. Cancelling" >&2
			exit 1
		fi
		;;


	*)
		# if nothing here matches, just send it all to parse_subcommand
		# $1 = module
		# $2 = module subcommand
		parse_subcommand $1 $2 $3
		;;
esac
