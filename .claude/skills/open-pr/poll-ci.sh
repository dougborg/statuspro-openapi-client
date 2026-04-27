#!/usr/bin/env bash
# Poll CI status for a PR with timeout.
#
# Usage: poll-ci.sh <pr-number> [timeout-seconds]
# Exit 0: all checks passed
# Exit 1: a check failed (prints failed check details)
# Exit 2: timeout reached

set -euo pipefail

pr_number="${1:?Usage: poll-ci.sh <pr-number> [timeout-seconds]}"
timeout="${2:-300}" # default 5 minutes
interval=30
elapsed=0

# Try --watch first (if supported)
if gh pr checks "$pr_number" --watch --fail-fast 2>/dev/null; then
  exit 0
fi

# Fallback: manual polling
while [ "$elapsed" -lt "$timeout" ]; do
  status=$(gh pr checks "$pr_number" 2>&1 || true)

  if echo "$status" | grep -q "fail"; then
    echo "CI check failed:" >&2
    echo "$status" | grep "fail" >&2
    exit 1
  fi

  if ! echo "$status" | grep -q "pending\|queued\|in_progress"; then
    echo "All CI checks passed"
    exit 0
  fi

  sleep "$interval"
  elapsed=$((elapsed + interval))
done

echo "CI polling timed out after ${timeout}s" >&2
exit 2
