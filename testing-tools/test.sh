#!/bin/bash


os_options=(fedora ubuntu debian opensuse rocky)

function start () {

	if [[ ${os_options[@]} =~ $1 ]]; then
		echo "Starting testing image for $1"
		docker run -it --volume=/Users/noahroberts/GitHub/dotfiles:/root/dotfiles:ro dotfile-testing:$1 bash
	else
		echo "OS $1 does not have a testing image. Existing images: ${os_options[@]}"
	fi
	
}


function build () {
	
	if [[ ${os_options[@]} =~ $1 ]]; then
		echo "Building testing image for $1"
		docker build -f Dockerfile.$1 --tag "dotfile-testing:$1" .
	else
		echo "OS $1 is not in the list of known OSes. Known OSes: ${os_options[@]}"
	fi

}


case $1 in 
	start)
		start $2
		;;

	build)
		build $2
		;;

	*)
		echo "test.sh <start|build> <distro>"

esac