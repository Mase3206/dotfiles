#!/usr/bin/env bash


SHELL_SCRIPT_FILE_NAME="outputs.sh"

formats=(big_header subheader step status_bad status_good)

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

function do_help () {
	echo "Usage: $SHELL_SCRIPT_FILE_NAME [format] [message] (part_2)"
	echo "formats: ${formats[@]}"
	echo "status_good and status_bad use a two-part message"
}


case $1 in
	big_header) big_header "$2";;
	subheader) subheader "$2";;
	step) step "$2";;
	status_good) status_good "$2" "$3";;
	status_bad) status_bad "$2" "$3";;
	*) do_help
esac
