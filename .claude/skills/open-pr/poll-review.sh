#!/usr/bin/env bash
# Poll for review activity on a PR with timeout.
#
# Usage: poll-review.sh <owner/repo> <pr-number> [timeout-seconds]
# Exit 0: review activity detected (approved or comments)
# Exit 2: timeout reached with no activity

set -euo pipefail

repo="${1:?Usage: poll-review.sh <owner/repo> <pr-number> [timeout-seconds]}"
pr_number="${2:?Missing PR number}"
timeout="${3:-900}" # default 15 minutes
interval=60
elapsed=0

while [ "$elapsed" -lt "$timeout" ]; do
  comment_count=$(gh api "repos/${repo}/pulls/${pr_number}/comments" --jq 'length' 2>/dev/null || echo "0")
  review_count=$(gh pr view "$pr_number" --repo "$repo" --json reviews --jq '.reviews | length' 2>/dev/null || echo "0")

  if [ "$review_count" -gt 0 ]; then
    # Check if approved
    approved=$(gh pr view "$pr_number" --repo "$repo" --json reviews --jq '[.reviews[] | select(.state == "APPROVED")] | length' 2>/dev/null || echo "0")
    if [ "$approved" -gt 0 ] && [ "$comment_count" -eq 0 ]; then
      echo "approved"
      exit 0
    fi
  fi

  if [ "$comment_count" -gt 0 ]; then
    echo "comments"
    exit 0
  fi

  sleep "$interval"
  elapsed=$((elapsed + interval))
done

echo "timeout"
exit 2
