#!/bin/bash

# "ak" shell function to call the Python CLI and eval environment changes.
# Usage:
# source /path/to/ak.sh
# ak l 123456
# ak c dev
# ak x dev-context
# ak r

function ak() {
    # Call the Python CLI 
    # Capture stdout (which may include lines like 'export KUBECONFIG=...') 
    local output 
    output=$(python3 "$(dirname "$BASH_SOURCE")/../src/ak/cli.py" "$@") || return 1

    # Evaluate each line in $output that starts with 'export'
    # This sets environment variables in our current shell
    while IFS= read -r line; do
        if [[ "$line" =~ ^export[[:space:]] ]]; then
            eval "$line"
        else
            echo "$line"
        fi
    done <<< "$output"
}

function _ak_completion() { 
    local cur prev COMPREPLY=() cur="${COMP_WORDS[COMP_CWORD]}" prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Simple completion for subcommands
    local subcommands="l c x r h"
    if [[ $COMP_CWORD == 1 ]]; then
        COMPREPLY=( $(compgen -W "$subcommands" -- "$cur") )
        return 0
    fi

    # If they typed 'ak c' we can complete from .kubeconfigs
    if [[ $prev == "c" ]]; then
        local kcfg_dir=~/.kubeconfigs
        if [[ -d "$kcfg_dir" ]]; then
            local files=$(ls "$kcfg_dir")
            COMPREPLY=( $(compgen -W "$files" -- "$cur") )
        fi
    fi

    # If they typed 'ak x' we can complete from contexts
    if [[ $prev == "x" ]]; then
        local cur prev opts
        cur="${COMP_WORDS[COMP_CWORD]}"
        opts=$(kubectl config get-contexts -o name)
        COMPREPLY=($(compgen -W "${opts}" -- "${cur}"))
    fi

    return 0
}

# show git branch and kubectl context in prompt along with user and host and current directory
PS1=\[\033[01;32m\]\u@\h \[\033[01;34m\]\w \[\033[31m\]`git branch 2> /dev/null | grep -e ^* | sed -E  s/^\\\\\*\ \(.+\)$/\(\\\\\1\)\ /`\[\033[36m\]`kubectl config current-context 2>/dev/null | sed -E "s/^(.+)$/{\1} /"`\[\033[35m\]$\[\033[00m\] 

complete -F _ak_completion ak

# short alias for kubectl
complete -F __start_kubectl k

alias k=kubectl

alias kgp='k get pod'
alias kgd='k get deploy'
alias kgi='k get ingress'
alias kgs='k get sts'
alias kgc='k get cm'
alias kgse='k get secret'
alias kgpvc='k get pvc'
alias kgpv='k get pv'
alias kgn='k get node'

alias kgpl='k get pod --show-labels'
alias kgdl='k get deploy --show-labels'
alias kgil='k get ingress --show-labels'
alias kgsl='k get sts --show-labels'
alias kgcl='k get cm --show-labels'
alias kgsel='k get secret --show-labels'
alias kgpvcl='k get pvc --show-labels'
alias kgpvl='k get pv --show-labels'
alias kgnl='k get node --show-labels'

alias kgpw='k get pod -o wide'
alias kgdw='k get deploy -o wide'
alias kgiw='k get ingress -o wide'
alias kgsw='k get sts -o wide'
alias kgcw='k get cm -o wide'
alias kgsecw='k get secret -o wide'
alias kgpvcw='k get pvc -o wide'
alias kgpvw='k get pv -o wide'
alias kgnw='k get node -o wide'

alias kgpwl='k get pod -o wide --show-labels'
alias kgdwl='k get deploy -o wide --show-labels'
alias kgiwl='k get ingress -o wide --show-labels'
alias kgswl='k get sts -o wide --show-labels'
alias kgcwl='k get cm -o wide --show-labels'
alias kgsecwl='k get secret -o wide --show-labels'
alias kgpvcwl='k get pvc -o wide --show-labels'
alias kgpvwl='k get pv -o wide --show-labels'
alias kgnwl='k get node -o wide --show-labels'
