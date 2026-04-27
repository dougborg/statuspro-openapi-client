#!/usr/bin/env bash
# Check if the current branch has commits from other authors.
# Used to determine if rebasing is safe (solo branch) or risky (shared).
#
# Usage: is-branch-shared.sh
# Exit 0: safe — branch is unpublished or solo-authored
# Exit 1: shared — other authors found, rebasing would disrupt collaborators
#
# Uses git config user.email for comparison (not $USER which is a short username).

set -euo pipefail

# Check if branch has a remote tracking ref
if ! git rev-parse --verify "@{u}" >/dev/null 2>&1; then
  # No upstream — branch is unpublished, safe to rebase
  exit 0
fi

current_email=$(git config user.email 2>/dev/null || true)
if [ -z "$current_email" ]; then
  echo "Warning: git user.email not configured, cannot check authorship" >&2
  exit 0
fi

other_authors=$(git log "@{u}..HEAD" --format='%ae' | sort -u | grep -Fvc "$current_email" || true)

if [ "$other_authors" -gt 0 ]; then
  echo "Branch has commits from other authors. Rebasing will disrupt collaborators." >&2
  echo "Other authors:" >&2
  git log "@{u}..HEAD" --format='%ae' | sort -u | grep -Fv "$current_email" >&2
  echo "Use merge instead, or confirm with collaborators first." >&2
  exit 1
fi

exit 0
