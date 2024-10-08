# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# User specific environment
if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]; then
    PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
export PATH

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
if [ -d ~/.bashrc.d ]; then
    for rc in ~/.bashrc.d/*; do
        if [ -f "$rc" ]; then
            . "$rc"
        fi
    done
fi
unset rc


# bash prompt
function nonzero_return() {
	RETVAL=$?
	[ $RETVAL -ne 0 ] && echo "<$RETVAL> "
}

export PS1="\[\e[31m\]\`nonzero_return\`\[\e[m\][\[\e[32m\]\u\[\e[m\] @ \[\e[36m\]\h\[\e[m\] ; \[\e[35m\]\W\[\e[m\]] \\$ "


# aliases and function
alias gedit=gnome-text-editor

function dotsync () {
	if [[ "$DOTFILES_DIR" == "" ]]; then
		echo "DOTFILES_DIR environment variable is not set. Setting it in your ~/.aliases file is recommended."
		return 1
	else
		local currdir 
		currdir=$(pwd)
		cd $DOTFILES_DIR
		echo "Pulling updates from repo"
		git pull
		echo; echo "Syncing"
		cd $currdir
		$DOTFILES_DIR/quicksync.sh --from $DOTFILES_DIR/known.txt sync
	fi
}

source ~/.aliases
