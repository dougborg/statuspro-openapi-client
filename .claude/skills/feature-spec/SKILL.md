---
name: feature-spec
description: Write feature specifications before implementation with structured templates
allowed-tools: Read, Grep, Glob, Bash(gh issue*)
---

# /feature-spec — Feature Specification

Document feature requirements before implementation to prevent scope creep and align development with goals.

## PURPOSE

Write feature specs before coding to align on requirements and prevent scope creep.

## CRITICAL

- **Acceptance criteria must be testable** — "good UX" is not testable; "user can filter by property" is.
- **Out of Scope section prevents creep** — explicitly list what is NOT included.
- **Technical notes must list all affected files/tables/roles** — missing one causes surprise scope mid-implementation.

## ASSUMES

- Feature is significant (touches multiple files, multiple roles, or shipping to users)
- Requirements are not yet crystal clear (spec is tool for alignment)
- You have access to GitHub CLI for linking issues

## STANDARD PATH

Use this template:

```markdown
# Feature: [Name]

## Problem Statement
[1-2 sentences: What user problem does this solve? Why now?]

## User Story
As a [role], I want to [goal] so that [outcome].

## Acceptance Criteria
1. [ ] [Testable criterion]
2. [ ] [Testable criterion]

## Out of Scope
- [Explicit exclusion]

## Technical Notes
- **Affected files/tables:** [list]
- **Required roles:** [list]
- **Dependencies:** [list]

## Related Issues
- Closes #N
- Depends on #M
```

## EDGE CASES

- [When not to write a spec] — read DETAIL: Scope if uncertain

---

## DETAIL: Scope

### Write a spec for

- Any feature touching 3+ files
- Any new database table or schema change
- Any feature affecting multiple roles
- Any feature shipping to users

### Skip for

- Bug fixes (1-2 files)
- Refactors
- Internal optimizations
