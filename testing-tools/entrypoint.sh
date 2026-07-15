#!/bin/bash

curl 'https://raw.githubusercontent.com/Mase3206/dotfiles/refs/heads/main/dotmgr/install.sh' | bash

dot mod install
dot sync
dot --zsh-completions
zsh