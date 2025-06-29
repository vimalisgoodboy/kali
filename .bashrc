# ─── HACKER THEME PROMPT ─────────────────────────────────────────
GREEN="\[\033[0;32m\]"
BLUE="\[\033[0;34m\]"
RED="\[\033[0;31m\]"
RESET="\[\033[0m\]"

parse_git_branch() {
  git branch 2>/dev/null | grep '\*' | sed 's/* /on /'
}

export PS1="${GREEN}\u@\h ${BLUE}\w ${RED}\$(parse_git_branch)${RESET}\n\$ "

# ─── GIT ALIASES ─────────────────────────────────────────────────
alias gs='git status'
alias ga='git add .'
alias gc='git commit -m'
alias gp='git push'
alias gpl='git pull --rebase'
alias gco='git checkout'
alias gb='git branch'
alias gl='git log --oneline --graph --decorate --all'
alias gr='git restore'
alias grs='git reset --soft HEAD~1'
alias gundo='git reset --soft HEAD~1'
alias gsave='git stash'
alias gpop='git stash pop'
alias gfix='git add . && git rebase --continue'

# ─── SHORTCUTS ──────────────────────────────────────────────────
alias cls='clear'
alias code.='code .'
alias serve='python3 -m http.server'
alias today='date "+%A, %d %B %Y"'

# ─── EXTRAS ─────────────────────────────────────────────────────
export EDITOR='code --wait'
export GIT_PS1_SHOWDIRTYSTATE=1
