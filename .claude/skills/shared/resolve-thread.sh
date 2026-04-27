#!/usr/bin/env bash
# Resolve a single PR review thread by thread ID.
#
# Usage: resolve-thread.sh <thread-id>
# Example: resolve-thread.sh PRRT_kwDOPU5ZrM53uZhY
#
# Exit 0: thread resolved successfully
# Exit 1: invalid args or API error

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <thread-id>" >&2
  echo "Example: $0 PRRT_kwDOPU5ZrM53uZhY" >&2
  exit 1
fi

thread_id="$1"

read -r -d '' mutation <<'GRAPHQL' || true
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { isResolved }
  }
}
GRAPHQL

gh api graphql \
  -f query="$mutation" \
  -f threadId="$thread_id" \
  --jq '.data.resolveReviewThread.thread.isResolved'
