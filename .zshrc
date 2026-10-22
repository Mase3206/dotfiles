# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

# Do Homebrew stuff
if [ -f /opt/workbrew/bin/brew ]; then
	eval "$(/opt/workbrew/bin/brew shellenv)"
elif [ -f /opt/homebrew/bin/brew ]; then
	export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
	eval "$(brew shellenv)"
fi
# Don't exit open casks
# export HOMEBREW_NO_UPGRADE_QUIT_CASKS=1

# Is this Variable Set and Not Empty?
function vsne() {
	[[ $(eval echo "\${${1}}") ]]
}
# Custom functions would normally be set down lower, but I need it here.

# Set the XDG variables if they're not set -- looking at you macOS.
vsne XDG_DATA_HOME || export XDG_DATA_HOME="$HOME/.local/share"

# DotMgr stuff
vsne XDG_CONFIG_HOME || export XDG_CONFIG_HOME="$HOME/.config"
export DOTFILES_DIR="$XDG_CONFIG_HOME/dotfiles"
export MANPATH="$XDG_DATA_HOME/man:$MANPATH"

# This line is needed to make the new Python-based dotfiles manager work,
# since it does some dynamic import trickery.
export PYTHONPATH="$DOTFILES_DIR:$PYTHONPATH"
export PATH="$HOME/.local/bin:$PATH"
export EDITOR='vim'

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="terse"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git uv iterm2)

# plugin options
export PYTHON_AUTO_VRUN=false

# Setting this is required for some OSes to correctly render the git prompt
# and detect the console width
LANG="en_US.UTF-8"

source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

[ -f ~/.aliases ] && source ~/.aliases

alias gedit="gnome-text-editor"
alias trim="sed 's/^[ \t]*//;s/[ \t]*$//'"


# Helpful functions to find and search through macOS plist defaults.
if [[ "$(uname)" == "Darwin" ]]; then
    function fdom () {
        # Help text (or missing args)
        if [[ "$1" == "-h" ]]; then
            echo 'usage: fdom [search_key]'
            echo 'search_key - the optional (case-insensitive) key to search for via grep'
            return 0
        fi

        local out="$(defaults domains | sed 's/, /\n/g')"
        if [[ "$1" == "" ]]; then
            echo -e "$out"
        else
            echo -e "$out" | grep -i "$1"
        fi
    }

    function ddom () {
        # Help text (or missing args)
        if [[ "$1" == "" ]] || [[ "$1" == "-h" ]] || [[ "$2" == "" ]] || [[ "$2" == "-h" ]]; then
            local valid_defaults_cmds="$(defaults -h | head -n 28 | tail -n 23 \
                | awk '{ print $1 }' | awk '!seen[$0]++' | sed '/^[[:space:]]*$/d' \
                | tr '\n' ' ' | trim)"

            echo 'usage: ddom <defaults_cmd> <domain_search_key> [...defaults_args]'
            echo ''
            echo '<domain_search_key>" - The part of a domain to look for via grep (case-insensitive).'
            echo '    If only one domain is found, all of its keys are dumped.'
            echo '    If more than one domains are found, the domain names are listed and the function returns 1.'
            echo ''
            echo "<defaults_cmd> - Valid options are '$valid_defaults_cmds'"
            echo '    See `defaults help` for details on each option and the parameters they accept.'

            if [[ "$1" == "-h" ]] || [[ "$2" == "-h" ]]; then
                return 0
            else
                return 2
            fi
        fi

        local out_arr
        declare -a out_arr=($(fdom "$2"))

        if [[ "${#out_arr[@]}" != "1" ]]; then
            echo "Found ${#out_arr[@]} domains:"
            for d in ${out_arr[@]}; do
                echo "- $d"
            done
            return 1
        else
            local key=$2
            local defaults_cmd=$1
            shift 2
            fdom "$key" | xargs -I% defaults $defaults_cmd % $@
        fi
    }
fi
