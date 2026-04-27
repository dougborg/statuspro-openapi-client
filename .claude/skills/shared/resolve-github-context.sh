#!/usr/bin/env bash
# Resolve GitHub context (owner, repo, PR number, branch, state) from
# the current git state or a PR number/URL argument.
#
# Usage: resolve-github-context.sh [pr-number-or-url]
# Output: JSON to stdout with owner, repo, number, base, branch, state
#
# If no argument: uses current branch to find an associated PR.
# If argument is a number: looks up that PR.
# If argument is a URL: extracts PR number from URL.

set -euo pipefail

# Extract owner/repo from git remote
get_owner_repo() {
  local url
  url=$(git remote get-url origin 2>/dev/null || true)
  if [ -z "$url" ]; then
    echo "No git remote 'origin' found" >&2
    exit 1
  fi
  # Handle both HTTPS and SSH URLs
  echo "$url" | sed -E 's|.*github\.com[:/]||; s|\.git$||'
}

# Extract PR number from URL if needed
parse_pr_arg() {
  local arg="$1"
  if [[ "$arg" =~ ^[0-9]+$ ]]; then
    echo "$arg"
  elif [[ "$arg" =~ /pull/([0-9]+) ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo "Cannot parse PR number from: $arg" >&2
    exit 1
  fi
}

owner_repo=$(get_owner_repo)

if [ $# -ge 1 ] && [ -n "$1" ]; then
  pr_number=$(parse_pr_arg "$1")
else
  # Try to find PR for current branch
  pr_number=$(gh pr view --json number --jq '.number' 2>/dev/null || true)
  if [ -z "$pr_number" ]; then
    # No PR found — return context without PR info
    branch=$(git branch --show-current 2>/dev/null || echo "")
    owner=$(echo "$owner_repo" | cut -d/ -f1)
    repo=$(echo "$owner_repo" | cut -d/ -f2)
    printf '{"owner":"%s","repo":"%s","number":null,"base":null,"branch":"%s","state":null}\n' \
      "$owner" "$repo" "$branch"
    exit 0
  fi
fi

# Fetch PR details
gh pr view "$pr_number" --json number,baseRefName,headRefName,state \
  --jq "{
    owner: \"$(echo "$owner_repo" | cut -d/ -f1)\",
    repo: \"$(echo "$owner_repo" | cut -d/ -f2)\",
    number: .number,
    base: .baseRefName,
    branch: .headRefName,
    state: .state
  }"
