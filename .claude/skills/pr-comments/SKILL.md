---
name: pr-comments
description: Respond to PR review comments systematically in thread context
allowed-tools: Bash(gh api *), Bash(gh pr *), Bash(git *), Bash(.claude/skills/pr-comments/reply-to-comment.sh*), Bash(.claude/skills/shared/resolve-github-context.sh*), Bash(.claude/skills/shared/fetch-pr-context.sh*), Read
---

# /pr-comments — Respond to PR Comments

Systematically respond to PR review comments, ensuring all feedback is addressed in thread context.

## PURPOSE

Reply to every unresolved PR comment with appropriate responses (fixed, already-fixed, or acknowledged).

## CRITICAL

- **ALWAYS use the reply script** — `.claude/skills/pr-comments/reply-to-comment.sh {owner}/{repo} {number} {comment_id} 'body'`. The script validates the comment belongs to the correct PR before posting. Never use standalone `gh pr comment {number}` (loses thread context) or raw `gh api` (easy to get the endpoint wrong).
- **Reply to EVERY comment** — Nothing left unaddressed or hanging
- **Only reply after code is live** — Wait for push to complete before responding. Replies confirm fix is deployed.
- **Batch replies per commenter when appropriate** — Multiple small changes from same reviewer can be batched into one multi-item reply

## ASSUMES

- PR comments already exist (this is addressing feedback, not collecting it)
- You have `gh` CLI and appropriate GitHub access
- Code changes have been made and pushed (you're replying, not fixing)

## STANDARD PATH

### 1. Fetch All Unresolved Comments

```bash
ctx=$(.claude/skills/shared/resolve-github-context.sh {number})
owner_repo=$(echo "$ctx" | jq -r '"\(.owner)/\(.repo)"')
.claude/skills/shared/fetch-pr-context.sh "$owner_repo" {number}
```

The script returns comments with resolved status. Filter to unresolved only.

### 2. Triage Each Comment

For each unresolved comment:

- **fix needed** → Already fixed? → Reply with: "Fixed — [what changed]"
- **already fixed** → Reply: "Addressed in [commit] — [brief explanation]"
- **acknowledged** → Reply: "Noted — [reasoning]. Tracked in #NNN" (with issue link)

### 3. Reply in Thread

Use comment ID to reply in-thread via GitHub API:

```bash
.claude/skills/pr-comments/reply-to-comment.sh {owner}/{repo} {number} {comment_id} 'Fixed — [explanation]'
```

**Never:** `gh pr comment {number} --body='...'` (loses thread context)
**Never:** `gh api .../pulls/comments/{id}/replies` (endpoint does not exist, returns 404)
**Never:** raw `gh api` for replies — always use the script (validates correct PR)

### 4. Summary

Report:

- Fixed: X comments
- Already fixed: Y comments
- Acknowledged: Z comments
- Any unaddressed items

## EDGE CASES

- [Batch replies for same reviewer] — Read DETAIL: Batching Comments (when to group, when to separate)
- [Multiple reviewers on same issue] — Read DETAIL: Multi-Reviewer Coordination (consistency)
- [Conflicting feedback] — Read DETAIL: Handling Conflicts (reconcile before replying)
- [Comment response templates] — Read DETAIL: Response Formats (fix/already-fixed/acknowledged patterns)

---

## DETAIL: Batching Comments

When a single reviewer has multiple comments:

### Batch Small Changes

Group 2-3 small comments into one reply if they're related:

```
Fixed:
1. Added validation on line 45 (comment #1)
2. Extracted to utility function (comment #2)
Both validated locally before push.
```

### Keep Complex Changes Separate

If responses are lengthy or unrelated, reply individually:

```
Comment #1: Lengthy architectural discussion
Comment #2: Simple typo fix
→ Two separate replies (don't batch)
```

### One Reply Per Thread

Multiple comments in the same thread (sub-conversation) → one reply addressing all.

---

## DETAIL: Multi-Reviewer Coordination

When multiple reviewers comment on same code:

### Consistency

Ensure responses are consistent across reviewers:

```
Reviewer A: "Extract to function"
Reviewer B: "This function is hard to test"

✅ Unified response: "Extracted to utility and added tests"
❌ Different responses: Looks like we ignored one reviewer
```

### Timing

Reply to all comments in the same push cycle. Don't reply to some, ignore others.

### Addressing Conflicts

If two reviewers disagree, reply:

```
Good points from both. We've decided on approach X because [reasoning].
Link to GitHub issue for extended discussion if needed.
```

---

## DETAIL: Handling Conflicts

If reviewer feedback contradicts design or project standards:

### Acknowledge Respectfully

```
I understand the concern about [issue]. However, we're using pattern X
because [project constraint]. If you'd like to discuss alternatives,
let's open a separate issue.
```

### Don't Dismiss

Even if you disagree, acknowledge the valid concern:

```
❌ Bad: "That's not how we do things here"
✅ Good: "I see the readability concern. We've chosen approach X
         because [trade-off]. Happy to discuss in future PRs."
```

### Link to Guidance

If feedback relates to project standards, link to CLAUDE.md or relevant docs:

```
Good catch. This follows pattern documented in CLAUDE.md#section.
Let me know if the guidance is unclear.
```

---

## DETAIL: Response Formats

### When Code Was Fixed

```
Fixed — [one sentence what changed].

[If tests added: Also added tests for X.]
```

**Example:**

```
Fixed — Added null check before accessing user.email on line 45.
Also added test case for when user creation fails mid-transaction.
```

### When Issue Was Already Fixed in Prior Commit

```
This was addressed in [commit hash] — [brief explanation].
```

**Example:**

```
This was addressed in 3bc4e2a — Validation now happens in middleware
before request reaches the handler.
```

### When Acknowledging but Deferring

```
Acknowledged — [reason for deferring]. Tracked in #NNN.
```

**Example:**

```
Acknowledged — Migrating to async/await is valuable, but out of scope
for this PR. Tracked in #456 for next quarter.
```

### When Asking for Clarification

```
I want to make sure I understand. Can you clarify [specific question]?
```

**Example:**

```
I want to make sure I understand the concern. Are you concerned about
performance at scale, or the maintainability of this pattern in general?
```

### When Declining Feedback

```
I appreciate the suggestion. However, [reason why we're not doing this].
Let's discuss in [GitHub issue link] if you'd like to revisit.
```

**Example:**

```
I appreciate the suggestion to use immutable data structures. However,
we've benchmarked this code path and mutation is actually faster here.
See discussion in #789 for performance trade-off analysis.
```

---

## IMPORTANT RULES

- **ALWAYS use the reply script** — `.claude/skills/pr-comments/reply-to-comment.sh` validates correct PR before posting
- **NEVER use standalone `gh pr comment`** (loses thread context)
- **NEVER use raw `gh api` for replies** — the script prevents wrong-PR and wrong-endpoint mistakes
- **NEVER use `/pulls/comments/{id}/replies`** — this endpoint does not exist (404)
- **Reply AFTER push** — Confirm code is live
- **Reply to EVERY comment** — Don't leave gaps
- **Batch when appropriate** — Related small items can be grouped
- **Stay respectful** — Acknowledge concern even if declining feedback
- **Link guidance** — Reference CLAUDE.md or project docs when relevant

---

## RELATED

- `/code-reviewer` — Run a 6-dimension structured review before opening
- `/commit` — Create commits being replied to
- [GitHub REST API: Pull Request Comments](https://docs.github.com/en/rest/pulls/comments)
