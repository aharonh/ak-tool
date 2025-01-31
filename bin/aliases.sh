#!/bin/bash

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
