---
name: code-reviewer
description: Structured code review using 6 dimensions. Works with or without the code-reviewer agent.
allowed-tools: Read, Grep, Glob, Bash(git diff*), Bash(git log*)
---

# /code-reviewer — 6-Dimensional Code Review

Perform structured code reviews across six dimensions: correctness, design, readability, performance, testing, and security.

## PURPOSE

Review code systematically to catch bugs, improve design, and enforce quality standards before merge.

## CRITICAL

- **Correctness first** — Blocking issues (type errors, logic bugs, data races) must be addressed before approval
- **Design shapes implementation** — Architecture and interface decisions propagate; poor design blocks downstream work
- **Security is non-negotiable** — Any vulnerability (injection, auth bypass, secret exposure) is BLOCKING
- **Don't duplicate findings** — If linters, type checkers, or automated reviewers already flag it, don't repeat it. Add context, not noise.

## ASSUMES

- Code to review is available (via `git diff`, file paths, or PR context)
- Reviewer has domain knowledge of the system being changed
- If a code-reviewer agent is available, this skill guides using it; otherwise, apply the dimensions manually

## STANDARD PATH

### 1. Gather Context

```bash
# Show recent changes
git diff HEAD~1 HEAD --stat
git diff HEAD~1 HEAD

# Or: review specific file
git diff -- path/to/file.js
```

### 2. Apply 6 Dimensions

For each dimension below, read the checklist in the DETAIL section and apply it:

- **Correctness** — Semantic correctness, logic, type safety
- **Design** — Architecture, interfaces, patterns
- **Readability** — Naming, clarity, documentation
- **Performance** — Efficiency, algorithms, resource usage
- **Testing** — Coverage, edge cases, test quality
- **Security** — Vulnerabilities, auth, secrets, injection risks

### 3. Classify Findings

For each finding, decide:

- **BLOCKING** — Cannot merge without fixing (correctness, security, design that breaks contracts)
- **SUGGESTION** — Worth addressing, improves quality (minor design, performance optimization)
- **NITPICK** — Nice-to-have, not blocking (naming, formatting edge case)

### 4. Report Results

Provide:

1. **Summary** — "Approved" / "Request changes" / "Comment"
2. **Findings by dimension** — Only include dimensions with findings
3. **Blockers first** — List BLOCKING items at the top
4. **Suggestions** — If code is otherwise solid, suggestions are optional

## EDGE CASES

- [Large PRs] — Read DETAIL: Handling Large Changes (split by file category)
- [Complex design] — Read DETAIL: Design Review Depth
- [Legacy code] — Read DETAIL: Reviewing Refactoring
- [Third-party code] — Read DETAIL: Vendor and Dependency Review

## DETAIL: Correctness

Check semantic correctness, logic, and type safety.

**Questions to ask:**

- Does the code do what the commit message says it does?
- Are all variables initialized before use?
- Do conditionals cover all cases? (missing `else`, incomplete `switch`)
- Are there off-by-one errors in loops?
- Do type signatures match implementations?
- Are race conditions or deadlocks possible?
- Can the code throw exceptions? Are they handled?
- Are null/undefined values handled?
- Is the control flow clear? (No hidden returns, confusing nesting)

**Red flags:**

- Unchecked error returns
- Shadowed variables
- Logic inversions (`if !valid` instead of `if valid`)
- Type assertions without runtime checks
- Silent failures (error caught but not re-raised/logged)

**Example feedback:**

```
BLOCKING: In line 45, `user.email` is accessed without null check.
If user creation fails mid-transaction, email will be undefined.

SUGGESTION: Add early return on line 32:
if (!validateInput(data)) return null;
instead of wrapping entire function in if-block.
```

---

## DETAIL: Design

Check architecture, interfaces, and design patterns.

**Questions to ask:**

- Does this follow the project's established patterns?
- Are responsibilities separated correctly? (One thing per module)
- Are interfaces clean? (Parameters, return types, public API)
- Does this violate any contracts or invariants?
- Is this change a special case or a sign of missing abstraction?
- Would this be hard to extend or maintain?
- Are dependencies one-way? (No circular imports)
- Does this introduce coupling where it shouldn't?

**Red flags:**

- Mixed concerns (HTTP + business logic in same function)
- God objects (classes doing too many things)
- Leaky abstractions (internal details visible to callers)
- Inconsistent naming or patterns vs. rest of codebase
- Silently changing behavior of existing APIs
- Hardcoded values that should be configurable

**Example feedback:**

```
BLOCKING: Adding `user.role` check in the API route breaks the
permission-at-boundary pattern. Auth should be enforced in middleware,
not scattered across handlers.

SUGGESTION: Extract email parsing into a standalone utility function
rather than inline regex. Makes it reusable and testable.
```

---

## DETAIL: Readability

Check naming, clarity, and documentation.

**Questions to ask:**

- Are variable and function names clear? (Avoid abbreviations, unclear terms)
- Is the code flow obvious? (No surprising jumps, clear intent)
- Are comments present where non-obvious? (Skip obvious comments)
- Is the code formatted consistently?
- Would a new team member understand this on first read?
- Are magic numbers explained? (Should be named constants)
- Are complex expressions broken into simpler steps?

**Red flags:**

- Single-letter variables outside loops (except `x`, `y` for coords)
- Unclear abbreviations (`usr`, `proc`, `calc`)
- Missing blank lines between logical sections
- Very long functions (>50 lines is a smell)
- Deeply nested code (>3 levels)
- Comments that restate the code instead of explaining "why"

**Example feedback:**

```
SUGGESTION: Rename `processData` to `validateAndTransformUserInput`.
Current name doesn't explain what kind of data or what kind of processing.

SUGGESTION: Break this 8-line conditional into a helper function:
if (user.status === 'active' && user.verified && !user.suspended) {
  // ... 20 lines ...
}
→ helper: isUserEligible(user)
```

---

## DETAIL: Performance

Check efficiency, algorithms, and resource usage.

**Questions to ask:**

- Are there obvious inefficiencies? (N² when O(n) is possible)
- Are expensive operations cached? (DB queries, API calls, computation)
- Are we loading more data than needed? (Lazy load vs. eager)
- Could this use a better data structure? (Array when Set would be faster)
- Is memory usage proportional to input? (Leaks, unbounded growth)
- Are there unnecessary copies of large objects?
- Could this block? (Sync where async is needed)

**Red flags:**

- Nested loops fetching data from DB/API per iteration
- Loading entire dataset then filtering in memory
- Regex compiled inside loops
- Large objects passed by value instead of reference
- Synchronous operations blocking the event loop
- Missing indexes on database queries

**Example feedback:**

```
SUGGESTION: Move `JSON.parse(config)` outside the loop (line 12).
Currently parsing the same config every iteration.

SUGGESTION: Use Set instead of Array for user lookup (line 8).
Current O(n) lookup inside loop → O(n²) overall. Set gives O(1).
```

---

## DETAIL: Testing

Check coverage, edge cases, and test quality.

**Questions to ask:**

- Are new functions/features covered by tests?
- Do tests cover happy path AND error cases?
- Are edge cases tested? (empty, null, boundary values)
- Are mocks used appropriately? (Don't mock what you should test)
- Are tests clear about what they're testing?
- Do tests isolate the unit under test?
- Could these tests pass with wrong implementations? (Mock too loose)

**Red flags:**

- No tests added for new code
- Tests only for happy path (no error cases)
- Mocking the function under test (defeats purpose)
- Assertions testing side effects instead of return values
- Brittle tests (fail if internals change, even if behavior is same)
- Copy-pasted test code (should be parameterized)

**Example feedback:**

```
BLOCKING: No tests added for the new `parseEmail` function.
Add tests for: valid email, invalid format, empty string, null.

SUGGESTION: Test error case on line 5. What happens if API fails?
Currently only testing happy path.
```

---

## DETAIL: Security

Check vulnerabilities, auth, secrets, and injection risks.

**Questions to ask:**

- Could this code be exploited? (Injection, XSS, CSRF)
- Is user input validated before use?
- Are secrets hardcoded or in git history? (Should be env vars)
- Is authentication/authorization enforced?
- Could this expose internal implementation details?
- Are external APIs called safely? (Rate limiting, error handling)
- Is sensitive data logged or exposed?
- Are dependencies known to be safe? (No malicious packages)

**Red flags:**

- User input used in SQL, shell, HTML without escaping
- Secrets in code (API keys, passwords, tokens)
- Missing authentication on sensitive endpoints
- Authorization bypass (assuming user is trusted after one auth check)
- Eval, dynamic code execution, or similar
- Disabled CSRF/CORS/CSP protections
- Dependencies with known vulnerabilities

**Example feedback:**

```
BLOCKING: User ID on line 18 is used directly in SQL query without
parameterization. Vulnerable to SQL injection.
→ Use parameterized query: db.query('SELECT * FROM users WHERE id = ?', [userId])

BLOCKING: API key hardcoded on line 5. This will leak if pushed to repo.
→ Move to environment variable: process.env.OPENAI_API_KEY
```

---

## DETAIL: Handling Large Changes

For PRs with many files or thousands of lines:

1. **Categorize by file type** — Review group of similar files together
2. **Focus on critical paths** — Auth, payments, data mutation first
3. **Ask for split** — If review is becoming overwhelming (>1 hour), ask author to split PR
4. **Sample verification** — For large refactors, verify the pattern across 3-5 representative files, then assume consistency

**Example:**

```
This PR is quite large. I've reviewed:
- Core auth changes (6/8 files) — LGTM
- Utility refactor (sampled 5 files) — Consistent pattern, approved
- Tests (spot-check) — Coverage looks good

Recommendation: For next round, consider splitting refactors by domain
(auth, API, database) so reviews can be focused.
```

---

## DETAIL: Design Review Depth

For architectural decisions, designs that touch multiple systems, or complex patterns:

1. **Understand the rationale** — Why this design vs. alternatives?
2. **Challenge core assumptions** — Is the problem statement correct?
3. **Check downstream impact** — What systems depend on this interface?
4. **Review maintainability** — Will future developers understand and extend this?
5. **Consider performance, security, and scalability** — Not just correctness

**Example:**

```
Design question: Why direct user-to-database model vs. service layer?

This works for current scale, but will make caching and multi-tenant
support hard later. Worth discussing if those are on the roadmap.

If you expect to cache: add a service layer now.
If you expect to stay monolithic: fine as-is.
```

---

## DETAIL: Reviewing Refactoring

When reviewing refactors or migrations:

1. **Verify behavior is unchanged** — Test the same scenarios pre/post
2. **Check edge cases** — Does refactoring handle all original cases?
3. **Review for accidental simplification** — Did we lose important complexity?
4. **Ensure tests pass** — All original tests should still pass
5. **Look for performance impact** — Is refactoring faster, slower, or same?

**Example:**

```
BLOCKING: In the refactor from Map to Object, iteration order is lost.
If code depends on insertion order, this breaks behavior.
→ Verify all callers don't assume order, or use Map.

SUGGESTION: The new version is ~20% faster (good!), but readability
dropped. Consider adding a comment explaining the performance trade-off.
```

---

## DETAIL: Vendor and Dependency Review

When reviewing changes to external code or dependencies:

1. **Audit supply chain** — Is this package from a known, trusted maintainer?
2. **Check version** — Is this the latest stable release?
3. **Security scan** — Any known CVEs in this version?
4. **Minimal surface area** — Import only what you need
5. **Evaluate necessity** — Does this add value or complexity?

**Example:**

```
BLOCKING: Package `left-pad` has a known supply chain attack history.
Use built-in padStart() instead.

SUGGESTION: Consider lighter dependency (2kb vs 50kb).
Similar functionality in `tiny-validator` or as 10-line utility function.
```

---

## RELATED

- `/pr-comments` — Respond to PR review comments thread-by-thread
- `code-reviewer` agent — Run 6D review automatically (provided by harness-kit plugin or project `.claude/agents/code-reviewer.md`)
- `CLAUDE.md` — Project-specific review standards
