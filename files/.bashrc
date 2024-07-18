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


function nonzero_return() {
	RETVAL=$?
	[ $RETVAL -ne 0 ] && echo "<$RETVAL> "
}

export PS1="\[\e[31m\]\`nonzero_return\`\[\e[m\][\[\e[32m\]\u\[\e[m\] @ \[\e[36m\]\h\[\e[m\] ; \[\e[35m\]\W\[\e[m\]] \\$ "

# eval "$(thefuck --alias)"

SHARED="/run/media/noahsroberts/Shared"

alias gedit=gnome-text-editor
