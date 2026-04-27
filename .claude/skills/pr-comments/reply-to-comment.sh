#!/usr/bin/env bash
# Reply to a PR review comment in-thread.
#
# Usage: reply-to-comment.sh <owner/repo> <pr-number> <comment-id> <body>
#
# This wraps the correct GitHub API endpoint for creating threaded replies
# to pull request review comments. The key is the `in_reply_to` parameter
# on POST /repos/{owner}/{repo}/pulls/{number}/comments.
#
# WARNING: The endpoint /pulls/comments/{id}/replies does NOT exist (returns 404).
# This script uses the correct endpoint.

set -euo pipefail

if [ $# -lt 4 ]; then
  echo "Usage: $0 <owner/repo> <pr-number> <comment-id> <body>" >&2
  echo "" >&2
  echo "Example:" >&2
  echo "  $0 owner/repo 19 3025404069 'Fixed — clarified the endpoint.'" >&2
  exit 1
fi

REPO="$1"
PR_NUMBER="$2"
COMMENT_ID="$3"
BODY="$4"

# Verify the comment exists and belongs to this PR
COMMENT_PR=$(gh api "repos/${REPO}/pulls/comments/${COMMENT_ID}" --jq '.pull_request_url' 2>/dev/null || true)
if [ -z "$COMMENT_PR" ]; then
  echo "Error: Comment ${COMMENT_ID} not found in ${REPO}" >&2
  exit 1
fi

# Extract PR number from the comment's pull_request_url to verify
COMMENT_PR_NUM=$(echo "$COMMENT_PR" | grep -oE '[0-9]+$')
if [ "$COMMENT_PR_NUM" != "$PR_NUMBER" ]; then
  echo "Error: Comment ${COMMENT_ID} belongs to PR #${COMMENT_PR_NUM}, not PR #${PR_NUMBER}" >&2
  echo "You may be replying to the wrong PR." >&2
  exit 1
fi

# Post the reply in-thread
gh api "repos/${REPO}/pulls/${PR_NUMBER}/comments" \
  -X POST \
  -F in_reply_to="${COMMENT_ID}" \
  -f body="${BODY}" \
  --jq '{id: .id, url: .html_url}'
