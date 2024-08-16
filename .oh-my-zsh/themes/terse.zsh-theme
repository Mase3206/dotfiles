#!/bin/zsh
# Based on the gnzh theme, which is based on the bira theme
# Uses the variables from zsh-git-prompt for the nice git status

# allow for strings to be evaluated as code when displayed
# required for the dynamic information in prompt to be... dynamic
setopt prompt_subst



# handle the SIGWINCH (window change) signal and update the prompt
TRAPWINCH() {
	local new_prompt_width=$(get_prompt_width)
	prompt_width=$new_prompt_width
	terse_theme_prompt
	zle && zle reset-prompt
}


# get the prompt width
# subtract 1 + the width of the venv prompt if a venv is active
get_prompt_width () {
	if [[ "$VIRTUAL_ENV" == "" ]]; then
		echo $(( COLUMNS ))
	else
		echo $(( COLUMNS - ${#VIRTUAL_ENV_PROMPT} - 1 ))
	fi
}


# convert to named function so it can be re-run when the window width changes
terse_theme_prompt() {

	local PR_USER PR_USER_OP PR_PROMPT PR_HOST

	# Check the UID
	if [[ $UID -ne 0 ]]; then # normal user
	PR_USER='%F{green}%n%f'
	PR_USER_OP='%F{green}%#%f'
	PR_PROMPT='%f$%f'
	else # root
	PR_USER='%F{red}%n%f'
	PR_USER_OP='%F{red}%#%f'
	PR_PROMPT='%F{red}#%f'
	fi

	# Check if we are on SSH or not
	if [[ -n "$SSH_CLIENT"  ||  -n "$SSH2_CLIENT" ]]; then
		PR_HOST='%F{blue}%M (ssh)%f' # SSH
	else
		PR_HOST='%F{blue}%m%f' # no SSH
	fi


	return_code="%(?..%F{red}%? ↵%f)"  # ↵


	local user_host="${PR_USER} %F{white}@ ${PR_HOST}"
	local current_dir="%F{magenta}%c%f"
	local git_branch='$(git_prompt_info)'
	prompt_width=$(get_prompt_width)

	PROMPT="
%F{237}$VIRTUAL_ENV_PROMPT${(l.${prompt_width}..─.)}%f
╭─ [${user_host} ; ${current_dir}] ${git_branch}
╰─ %B$PR_PROMPT%b "
	RPROMPT="${return_code}"


	# All of the following variables are from https://github.com/zsh-git-prompt/zsh-git-prompt, which is licensed under the MIT License.
	# I did make a few minor modifications, each of which is marked.

	ZSH_THEME_GIT_PROMPT_PREFIX=" \ue0a0 ["  # added " \ue0a0 "
	ZSH_THEME_GIT_PROMPT_SUFFIX="${reset_color}]"  # added "${reset_color}"
	ZSH_THEME_GIT_PROMPT_HASH_PREFIX=":"
	ZSH_THEME_GIT_PROMPT_SEPARATOR="|"
	ZSH_THEME_GIT_PROMPT_BRANCH="%{$fg_bold[magenta]%}"
	ZSH_THEME_GIT_PROMPT_STAGED="%{$fg[red]%}%{●%G%}"
	ZSH_THEME_GIT_PROMPT_CONFLICTS="%{$fg[red]%}%{✖%G%}"
	ZSH_THEME_GIT_PROMPT_CHANGED="%{$fg[blue]%}%{✚%G%}"
	ZSH_THEME_GIT_PROMPT_BEHIND="%{↓%1G%}"
	ZSH_THEME_GIT_PROMPT_BEHIND_AHEAD_SEPARATOR=""
	ZSH_THEME_GIT_PROMPT_BEHIND_AHEAD_SECTION_SEPARATOR=" "
	ZSH_THEME_GIT_PROMPT_AHEAD="%{↑%1G%}"
	ZSH_THEME_GIT_PROMPT_STASHED="%{$fg_bold[blue]%}%{⚑%G%}"
	ZSH_THEME_GIT_PROMPT_UNTRACKED="%{$fg[cyan]%}%{…%G%}"
	ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg_bold[green]%}%{✔%G%}"
	ZSH_THEME_GIT_PROMPT_LOCAL=" L"
	# The remote branch will be shown between these two
	ZSH_THEME_GIT_PROMPT_UPSTREAM_FRONT=" {%{$fg[blue]%}"
	ZSH_THEME_GIT_PROMPT_UPSTREAM_END="%{${reset_color}%}}"
	ZSH_THEME_GIT_PROMPT_MERGING="%{$fg_bold[magenta]%}|MERGING%{${reset_color}%}"
	ZSH_THEME_GIT_PROMPT_REBASE="%{$fg_bold[magenta]%}|REBASE%{${reset_color}%} "
	ZSH_THEME_GIT_PROMPT_BISECT="%{$fg_bold[magenta]%}|BISECT%{${reset_color}%} "

}

# run function right away upon loading theme
terse_theme_prompt
