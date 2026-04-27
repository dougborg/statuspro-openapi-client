#!/usr/bin/env bash
# Ensure we're on a feature branch. If on main/master, auto-create one.
#
# Usage: ensure-feature-branch.sh
# Output: prints the feature branch name to stdout
# Exit 1: if no changes to create a PR from
#
# Handles three scenarios:
# a) Unpushed commits on main → infer name, create branch, reset main
# b) Staged/unstaged changes only → stash, create branch, pop
# c) Clean state → exit 1 (nothing to PR)

set -euo pipefail

current=$(git branch --show-current)

# Already on a feature branch
if [ "$current" != "main" ] && [ "$current" != "master" ]; then
  echo "$current"
  exit 0
fi

# Infer branch name from most recent commit or generate fallback
infer_branch_name() {
  local msg
  msg=$(git log -1 --format='%s' 2>/dev/null || true)
  local pattern='^([a-z]+)(\(([^)]+)\))?: (.+)$'
  # shellcheck disable=SC2295
  if [[ "$msg" =~ $pattern ]]; then
    local type="${BASH_REMATCH[1]}"
    local scope="${BASH_REMATCH[3]}"
    local desc="${BASH_REMATCH[4]}"
    local slug
    slug=$(echo "$desc" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | sed 's/-$//')
    if [ -n "$scope" ]; then
      echo "${type}/${scope}-${slug}"
    else
      echo "${type}/${slug}"
    fi
  else
    echo "feature/pr-$(date +%Y%m%d)"
  fi
}

# Check for branch name collisions
get_unique_branch() {
  local base="$1"
  local name="$base"
  local i=2
  while git branch --list "$name" | grep -q .; do
    name="${base}-${i}"
    i=$((i + 1))
  done
  echo "$name"
}

# Scenario a: Unpushed commits on main
if git rev-list "@{u}..HEAD" 2>/dev/null | head -1 | grep -q .; then
  branch_name=$(get_unique_branch "$(infer_branch_name)")
  dirty=$(git status --porcelain)
  stashed=false
  if [ -n "$dirty" ]; then
    # Preserve working tree changes (tracked, staged, and untracked) across the reset
    git stash push -u -m "open-pr: preserve working tree" >&2
    stashed=true
  fi
  git branch "$branch_name"
  git reset --hard "@{u}"
  git checkout "$branch_name"
  if [ "$stashed" = true ]; then
    git stash pop >&2
  fi
  echo "$branch_name"
  exit 0
fi

# Scenario b: Staged or unstaged changes
if [ -n "$(git status --porcelain)" ]; then
  branch_name=$(get_unique_branch "$(infer_branch_name)")
  git stash push -m "open-pr: auto-stash" >&2
  git checkout -b "$branch_name" >&2
  git stash pop >&2
  echo "$branch_name"
  exit 0
fi

# Scenario c: Clean state
echo "No changes to create a PR from." >&2
exit 1
