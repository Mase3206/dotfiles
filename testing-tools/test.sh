#!/bin/zsh

set -euo pipefail

os_options=(fedora debian opensuse rocky)

function do_test() {
	if [[ ${os_options[@]} =~ $1 ]]; then
		# Build image
		echo "Building image for $1 - this could take a while..."
		hash=$(docker build -q -f Dockerfile.$1 .)

		# Start image
		echo "Starting test for for $1"
		echo "Once you're finished in there, just run \`exit\`."
		docker run --rm -it $hash bash

		# Remove image (since they're quite large)
		echo "Cleaning up"
		docker image rm $hash

	else
		echo "OS $1 does not have a testing image. Existing images: ${os_options[@]}"
		exit 1
	fi
}


case $1 in 
	-h)
		echo "test.sh <distro>"
		;;

	*)
		do_test $@
esac