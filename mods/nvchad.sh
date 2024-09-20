#!/usr/bin/env bash

# used to properly show $0
if [[ -n $DOTFILES_MODS_RUNNER ]]; then
	SHELL_SCRIPT_FILE_NAME="$DOTFILES_MODS_RUNNER nvchad"
else 
	SHELL_SCRIPT_FILE_NAME="mods/neovim.sh"
fi


function nvchad_detect () {
	# is file and not link
	if [ -f ~/.config/nvim/README.md ] && [ -L ~/.config/nvim/README.md ]; then
		./outputs.sh status_good "NvChad install status" "already installed!"
		DOTFILES_NVCHAD_INSTALLED=1
	else
		./outputs.sh status_bad "NvChad install status" "NOT installed."
		DOTFILES_NVCHAD_INSTALLED=0
	fi
}


function nvchad_install () {
	./outputs.sh subheader "Installing NvChad"

	local av av_maj av_min av_bug

	if [[ $DOTFILES_OS_RHEL == 1 ]]; then
		av=$(dnf info neovim | grep 'Version' | awk -F: '{gsub(/ /, "", $2); print $2}')
		av_maj=$(echo $av | awk -F. '{print $1}')
		av_min=$(echo $av | awk -F. '{print $2}')
		av_bug=$(echo $av | awk -F. '{print $3}')

		if (( $av_maj < 1 )) && (( $av_min < 10 )); then
			./outputs.sh status_bad "Latest Neovim version avaiable" "v$av"
			echo -e "NvChad \e[31mcan't\e[0m be installed here, as it requires Neovim v0.10.0 or greater, but v$av is the latest version available for this system."

			# without the lua folder present, quicksync will complain about a missing file in the user's home dir
			./outputs.sh step "Creating ~/.config/nvim folder so quicksync.sh can shut up"
			mkdir -p ~/.config/nvim/lua
			return 1
		else
			./outputs.sh status_good "Latest Neovim version avaiable" "v$av"
		fi
	fi

	nvchad_detect
	if [[ $DOTFILES_NVCHAD_INSTALLED == 1 ]]; then
		echo -e "\e[31mSkipping\e[0m NvChad installation."
		return
	fi
	echo

	# download nvchad repo
	./outputs.sh step "Downloading NvChad starter config"
	git clone https://github.com/NvChad/starter ~/.config/nvim > /dev/null 2> /dev/null

	# let lazy.nvim download plugins
	echo -e "You'll need to run \e[1;33mnvim\e[0m manually to let lazy.nvim download all its plugins."
	echo -e "You'll also need to run \e[1;33m:MasonInstallAll\e[0m from within Neovim once that's done."
	echo

	# remove .git folder from nvim folder
	# leaving it would probably have weird outcomes when just using neovim
	./outputs.sh step "Removing .git folder (from git clone) from .config/nvim"
	rm -rf ~/.config/nvim/.git

	# link dem dots
	./outputs.sh step "Linking customized NvChad configs"
	./quicksync.sh rm .config/nvim/lua -y > /dev/null
	./quicksync.sh ln .config/nvim/lua -y > /dev/null
}


function nvchad_help () {
	cat << EOF
$SHELL_SCRIPT_FILE_NAME [-h] <command>

Commands:
\`detect\`: Detect existing install and display its status
\`install\`: Install NvChad
EOF
	[[ "$1" == "-h" ]] && exit 0 || exit 1
}


case $1 in
	detect) nvchad_detect ;;
	install) nvchad_install ;;
	*) nvchad_help $1
esac
