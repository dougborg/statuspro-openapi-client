#!/usr/bin/env bash
# Fetch PR metadata, diff, comments, and review thread resolution status.
#
# Usage: fetch-pr-context.sh <owner/repo> <pr-number>
# Output: JSON to stdout with title, body, comments (with resolved status)
#
# Combines REST API (for comment details) and GraphQL (for resolved status)
# into a single output so skills don't need to make multiple API calls.

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

# Fetch PR metadata
pr_json=$(gh pr view "$PR_NUMBER" --repo "$REPO" \
  --json title,body,state,baseRefName,headRefName,author)

# Fetch review comments (REST API — has path, line, body, id)
comments_json=$(gh api "repos/${REPO}/pulls/${PR_NUMBER}/comments" \
  --paginate --jq '[.[] | {id: .id, path: .path, line: .line, body: .body, author: .user.login, created_at: .created_at}]')

# Fetch review thread resolved status (GraphQL).
# Pull every comment in each thread so reply-comment IDs also inherit the
# thread's is_resolved status, not just the first comment.
read -r -d '' query <<'GRAPHQL' || true
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 100) {
              nodes { databaseId }
            }
          }
        }
      }
    }
  }
GRAPHQL
# One row per (thread_id, comment_id) so the join works for replies too.
# shellcheck disable=SC2016  # $t is a jq variable, not shell — single-quote intentional.
resolved_json=$(gh api graphql -f query="$query" \
  -F "owner=$OWNER" -F "repo=$REPO_NAME" -F "number=$PR_NUMBER" \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[] as $t |
    $t.comments.nodes[] | {
      comment_id: .databaseId,
      thread_id: $t.id,
      is_resolved: $t.isResolved
    }
  ]')

# Merge resolved status into comments
if command -v jq >/dev/null; then
  echo "$pr_json" | jq --argjson comments "$comments_json" \
    --argjson resolved "$resolved_json" '
    . + {
      comments: [
        $comments[] | . as $c |
        . + {
          is_resolved: (
            ($resolved[] | select(.comment_id == $c.id) | .is_resolved) // false
          )
        }
      ],
      unresolved_count: ([
        $comments[] | . as $c |
        select(
          ($resolved[] | select(.comment_id == $c.id) | .is_resolved) // false
          | not
        )
      ] | length)
    }
  '
else
  # Fallback: merge JSON via python3 (jq is not available).
  # The previous string-concat approach used `${pr_json%\}}`, which fails
  # because `\}` is a literal pattern, not an escape — leaving invalid JSON.
  if ! command -v python3 >/dev/null; then
    echo "fetch-pr-context.sh: needs jq or python3 to merge JSON" >&2
    exit 1
  fi
  PR_JSON="$pr_json" COMMENTS_JSON="$comments_json" RESOLVED_JSON="$resolved_json" \
    python3 - <<'PY'
import json, os, sys

pr = json.loads(os.environ["PR_JSON"])
pr["comments"] = json.loads(os.environ["COMMENTS_JSON"])
pr["resolved_threads"] = json.loads(os.environ["RESOLVED_JSON"])

json.dump(pr, sys.stdout)
sys.stdout.write("\n")
PY
fi
