#!/bin/bash

# Git Aliases
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg 'log --oneline --graph --decorate --all'
git config --global alias.last 'log -1 HEAD'
git config --global alias.amend 'commit --amend --no-edit'
git config --global alias.undo 'reset --soft HEAD~1'

# Git Settings
git config --global core.editor "code --wait"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global color.ui auto

# Git Diff & Merge Tool
git config --global diff.tool vscode
git config --global merge.tool vscode

# Success message
echo "✅ Git Ninja mode activated!"
