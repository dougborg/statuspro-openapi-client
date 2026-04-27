#!/usr/bin/env bash
# Resolve all unresolved review threads on a PR.
#
# Usage: resolve-all-threads.sh <owner/repo> <pr-number>
# Output: count of resolved threads to stdout
# Exit 0: all threads resolved (or none to resolve)
# Exit 1: invalid args or API error

set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <owner/repo> <pr-number>" >&2
  echo "Example: $0 owner/repo 19" >&2
  exit 1
fi

REPO="$1"
PR_NUMBER="$2"
OWNER="${REPO%%/*}"
REPO_NAME="${REPO##*/}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Fetch all unresolved thread IDs
read -r -d '' query <<'GRAPHQL' || true
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
        }
      }
    }
  }
}
GRAPHQL

thread_ids=$(gh api graphql \
  -f query="$query" \
  -F "owner=$OWNER" -F "repo=$REPO_NAME" -F "number=$PR_NUMBER" \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not) | .id] | .[]')

if [ -z "$thread_ids" ]; then
  echo "0"
  exit 0
fi

# Resolve each thread
resolved=0
failed=0
while IFS= read -r thread_id; do
  if "$SCRIPT_DIR/resolve-thread.sh" "$thread_id" >/dev/null 2>&1; then
    resolved=$((resolved + 1))
  else
    echo "Failed to resolve thread: $thread_id" >&2
    failed=$((failed + 1))
  fi
done <<<"$thread_ids"

echo "$resolved"
[ "$failed" -eq 0 ]
