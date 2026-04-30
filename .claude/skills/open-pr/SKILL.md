---
name: open-pr
description: >-
  Open a PR for the current feature branch — validate, self-review, simplify,
  organize commits, push, create the PR, wait for CI and review, then address
  feedback. Use when implementation is complete and ready for review.
argument-hint: "[base branch]"
allowed-tools: Bash(gh pr *), Bash(gh api *), Bash(gh run *), Bash(git status), Bash(git diff *), Bash(git log *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git branch *), Bash(git stash *), Bash(git checkout *), Bash(git reset *), Bash(git rev-list *), Bash(git rev-parse *), Bash(.claude/skills/open-pr/*), Bash(.claude/skills/shared/discover-verification-cmd.sh*), Bash(.claude/skills/shared/resolve-github-context.sh*), Read
---

# /open-pr — Open a Pull Request

Take the current feature branch from "implementation done" to "PR open, CI green, first-round review addressed."

## PURPOSE

Ship a feature branch end-to-end: validate, self-review, push, create PR, wait for CI, address the first round of review.

## CRITICAL

- **Validate before opening** — the project's verification command must pass before `gh pr create`. Don't push broken code.
- **Self-review the full diff** — read every change before opening; never skip this and rely on reviewers.
- **Stage specific files** — never `git add -A` or `git add .`. Intentional staging prevents accidentally committing secrets, scratch files, or unrelated changes.
- **Use polling scripts for CI and review state** — never check review comments with `gh pr view --json`. That endpoint only returns top-level PR comments, not inline review comments attached to code lines. Use `poll-review.sh` which calls the correct API (`gh api repos/.../pulls/.../comments`).
- **Never merge with unaddressed review comments** — every comment gets fixed, deferred with a tracked issue, or discussed. CI green does not override review feedback.
- **No `--no-verify`** — never bypass commit hooks, type checkers, or linters. If a check fails, fix the cause.
- **Push with the safe refspec, never the bare branch name** — use `git push -u origin HEAD:refs/heads/<branch-name>`, **not** `git push -u origin <branch-name>`. The bare form resolves the destination via the local branch's *upstream*. When a feature branch is created with `git checkout -b <name> origin/main`, its upstream is `origin/main` — and `git push -u origin <name>` then pushes straight to **`main`**, not to a new remote `<name>` ref. The pre-push guard at `scripts/pre-push-guard.sh` exists for this reason but does not fire from worktrees that haven't installed the repo hooks via `uv run pre-commit install`. Same rule applies to subsequent pushes (`git push --force-with-lease` after a rebase).

## STANDARD PATH

The skill runs nine phases. Each phase is short; phase headings below are the navigation index.

1. **Pre-flight** — ensure feature branch, run validation, check for existing PR
2. **Self-review** — read the full diff, check for bugs/secrets/debug code
3. **Simplify (optional)** — reuse, dead code, duplication
4. **Organize commits** — logical commits with conventional format + HEREDOC
5. **Push and create PR** — `gh pr create` with HEREDOC body
6. **Wait for CI** — `poll-ci.sh`; fix in place if anything fails
7. **Wait for review** — `poll-review.sh`; never skip with `gh pr view`
8. **Address review comments** — delegate to `/pr-comments`
9. **Summary** — report PR URL, CI status, comments addressed

## Phase 1: Pre-flight

1. **Ensure feature branch** — auto-create if on `main`:

   ```bash
   branch=$(.claude/skills/open-pr/ensure-feature-branch.sh)
   ```

   The script handles three scenarios automatically:
   - **Unpushed commits on main** → infers branch name from commit, creates branch, resets main
   - **Staged/unstaged changes** → stashes, creates branch, pops
   - **Clean state** → exits 1 ("No changes to create a PR from.")

2. **Determine base branch** — use `$ARGUMENTS` if provided, otherwise `main`.

3. **Discover and run validation:**

   ```bash
   cmd=$(.claude/skills/shared/discover-verification-cmd.sh)
   eval "$cmd"
   ```

   **ALL must pass.** Fix any failures before proceeding.

4. **Check for existing PR**:

   ```bash
   gh pr view --json number,url,state
   ```

   If a PR already exists and is open, auto-delegate to `/pr-comments` — do not stop and tell the user.

## Phase 2: Self-review

Review **every change** in the diff:

```bash
git diff <base>...HEAD
git diff
git diff --cached
```

Check for:

- Bugs, logic errors, edge cases, missing null checks
- Missing error handling
- Security concerns (secrets, injection, unsafe deserialization)
- Missing or inadequate tests
- Leftover debug code (`print()`, `console.log`, `TODO`/`FIXME` without issue refs)
- Code quality and naming consistency

Fix any issues found, then re-run validation.

## Phase 3: Simplify (Optional)

Review for opportunities to simplify:

- Reuse opportunities (existing utilities that could replace new code)
- Dead code or unnecessary complexity
- Duplication within the changeset

If improvements are found, apply them and re-run validation.

Note: This phase is optional and relies on manual review or the `/simplify` skill if available in your Claude Code environment.

## Phase 4: Organize commits

1. Review current state:

   ```bash
   git log <base>..HEAD --oneline
   git status
   ```

1. Organize changes into logical commits:
   - If all uncommitted: group into meaningful commits (separate feature from tests, refactoring from new functionality)
   - If commits exist and are well-organized: just commit remaining changes
   - If messy (WIP, fixup): clean up

2. **Stage specific files** — never use `git add -A` or `git add .`

3. Use conventional commit format with HEREDOC:

   ```bash
   git commit -m "$(cat <<'EOF'
   feat(client): short description

   Optional longer explanation.

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

   This project uses release-please. Valid scopes are `client` (drives the
   Python client release) and `mcp` (drives the MCP server release); use no
   scope for cross-cutting changes that should not trigger a release. See
   CLAUDE.md "Commit Standards" for the full list and breaking-change syntax.

## Phase 5: Push and create PR

1. Push with the explicit-destination refspec (see CRITICAL — bare-branch form
   can push to `main` when the local branch's upstream is `origin/main`):

   ```bash
   git push -u origin HEAD:refs/heads/<branch>
   ```

2. Create PR with HEREDOC body:

   ```bash
   gh pr create --base <base> --title "feat(scope): short description" --body "$(cat <<'EOF'
   ## Summary
   - Bullet points describing what this PR does

   ## Test plan
   - [ ] How to verify the changes work

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

3. Print the PR URL.

## Phase 6: Wait for CI

```bash
.claude/skills/open-pr/poll-ci.sh <number>
```

Exit 0 = passed, exit 1 = failed (fix, commit, push, re-poll), exit 2 = timeout.

**If a check fails:** fetch logs with `gh run view <run-id> --log-failed`, fix, validate locally, commit (specific files), push, resume waiting.

## Phase 7: Wait for review

**Always use the polling script** — never check for review comments with `gh pr view --json`. That endpoint only returns top-level PR comments, not inline review comments attached to code lines. The polling script uses the correct API (`gh api repos/.../pulls/.../comments`).

```bash
ctx=$(.claude/skills/shared/resolve-github-context.sh <number>)
owner_repo=$(echo "$ctx" | jq -r '"\(.owner)/\(.repo)"')
.claude/skills/open-pr/poll-review.sh "$owner_repo" <number>
```

Outputs: `approved`, `comments`, or `timeout` (exit 2).

- **approved** → tell user and stop
- **comments** → proceed to Phase 8
- **timeout** → tell user "CI green, PR open, no review comments yet" and stop

## Phase 8: Address review comments

Invoke `/pr-comments` to handle all review comments:

```bash
/pr-comments <number>
```

**Do not duplicate the review-comment workflow** — always delegate to `/pr-comments`.

## Phase 9: Summary

Print:

- PR URL
- Number of commits
- CI status
- Review comments addressed (if any)
- Current PR state

## Important Rules

- **Never dismiss review findings** — Code quality concerns are the entire point of code review. Never rationalize skipping them ("not blocking", "acceptable", "good for future refinement"). Every finding gets fixed, deferred with a tracked issue, or discussed with the reviewer. "CI is green" and "tests pass" do not override review feedback.
- **Never merge with unaddressed comments** — All review comments must be resolved before merging. No exceptions.
- **Validate before opening** — verification must pass before creating the PR
- **Self-review is mandatory** — always review the full diff
- **Simplify is encouraged but optional** — Phase 3; use `/simplify` if it would
  meaningfully reduce duplication or dead code, otherwise skip
- **Logical commits** — organize into meaningful commits, not one giant squash
- **No shortcuts** — never use `--no-verify`, `noqa`, or `type: ignore`
- **Fix CI in-place** — don't close and re-open
- **Stage specific files** — never `git add -A` or `git add .`
- **HEREDOC for messages** — always use HEREDOC for commit messages and PR bodies
- **File issues for deferred work** — if self-review finds out-of-scope issues, create GitHub issues before opening
- **Delegate to /pr-comments** — don't duplicate the comment-response workflow

## Related Skills

- `/pr-comments` — Address review feedback (fix, commit, push, reply)
- `/commit` — Quality-gated conventional commits
- `/simplify` — Code simplification pass
