---
name: skill-writer
description: Create well-structured skills and agents using progressive disclosure pattern
allowed-tools: Glob, Grep, Read, Write, Edit
---

# /skill-writer — Skill and Agent Creation

Create scannable skills and agents: PURPOSE ≤10 tokens, CRITICAL constraints, STANDARD PATH ≤30 lines, optional DETAIL sections. Works for AI agents with token budgets and humans skimming for relevance.

## PURPOSE

Generate well-structured `.claude/skills/*/SKILL.md` and `.claude/agents/*.md` files with proper PURPOSE/CRITICAL/STANDARD PATH/DETAIL structure.

## CRITICAL

- **Constraint clarity before happy path** — CRITICAL prevents catastrophic mistakes. Don't bury constraints in STANDARD PATH.
- **Minimum permissions required** — Reviewers should not have Write. Validators need only specific Bash patterns.
- **One responsibility per skill** — Multiple workflows → split into focused skills and reference each other.
- **Progressive disclosure always** — PURPOSE ≤10 tokens, CRITICAL ≤20 tokens, STANDARD PATH ≤30 lines, full skill ≤1500 tokens.

## ASSUMES

- Skill/agent will be read by agents with token budgets (skim PURPOSE, decide if needed)
- Both AI and humans are scanning for relevance before full read
- Catastrophic mistakes belong in CRITICAL; edge cases belong in EDGE CASES/DETAIL

## STANDARD PATH

### 1. Determine Type

**Skill:** User invokes explicitly (`/commit`). Workflow with steps. STANDARD PATH is a checklist.

**Agent:** Answers questions (read-only). No execution. Tool permissions: Read only.

### 2. Write Frontmatter

```yaml
---
name: skill-name
description: [One-liner, <80 chars]
allowed-tools: [minimum permissions needed]
---
```

Omit `model:` on skills — they execute in the parent conversation context, and pinning a model can break long sessions (e.g. 1M-context Opus). Agents get a fresh context, so specifying `model:` on agent frontmatter is fine.

### 3. Write Structure

PURPOSE → CRITICAL → ASSUMES → STANDARD PATH → EDGE CASES → DETAIL

- **PURPOSE** ≤10 tokens: What + when
- **CRITICAL** ≤20 tokens: Catastrophic mistakes
- **STANDARD PATH** ≤30 lines: Happy path
- **EDGE CASES**: Named links only
- **DETAIL**: Only if referenced

See DETAIL: Detailed Workflow for step-by-step guide.

## EDGE CASES

- [Skill too large] — read DETAIL: Scope Creep if STANDARD PATH >50 lines or EDGE CASES >5 items
- [Agent should execute] — read DETAIL: Advisor vs Enforcer if tempted to add Write/Edit tools
- [Unclear permissions] — read DETAIL: Allowed-Tools if unsure what to grant

---

## DETAIL: Detailed Workflow

### 1. Determine Skill or Agent Type

**Skill (automation workflow):**

- Solves a repetitive task
- User invokes explicitly (e.g., `/commit`)
- STANDARD PATH is a workflow with steps

**Agent (answering questions):**

- Reads and analyzes (advisor only)
- Answers domain questions
- Does NOT execute or modify files
- Tool permissions: Read only

### 2. Draft PURPOSE

"What does this do? When do I invoke/use it?" in one sentence.

**Test:** Can someone skim this in 5 seconds and know if they need to read more?

### 3. List CRITICAL Constraints

Non-negotiable rules preventing catastrophic mistakes:

- Destructive operations that can't be undone
- Security/compliance rules
- Ordering dependencies ("must run X before Y")
- Permission boundaries

**Examples:**

- ✅ "Never commit secrets. Always run detect-private-key first."
- ✅ "Formatters must run before validators. Validators gate commits."
- ❌ "Consider running tests" → Not critical (nice-to-know)

### 4. Write ASSUMES

What the skill assumes about the environment/codebase:

- Project structure
- Tool availability
- Configuration patterns

**Why this matters:** If ASSUMES break, skill needs redesign, not patching.

### 5. Write STANDARD PATH

Happy path covering 80% of uses. Prose + code blocks. ≤30 lines total.

**For skills:**

- User runs `/skill-name`
- Step-by-step workflow (2-5 steps)
- Prose explaining each step
- Code blocks showing commands

**For agents:**

- User asks a question
- Agent reads files
- Agent answers in structured format
- Don't include execution; agents are read-only

### 6. List EDGE CASES

Link to DETAIL sections. Name them and link; don't explain yet.

```markdown
## EDGE CASES

- [Case name] — read DETAIL: Name if you encounter this
```

### 7. Write DETAIL Sections (If Needed)

Only for edge cases referenced above. Format: `## DETAIL: Edge Case Name`

---

## DETAIL: Scope Creep

Skill is too big if:

- User spends >3 minutes reading
- STANDARD PATH has many conditionals
- EDGE CASES has >5 items

**Solution:** Split into focused skills that reference each other.

**Example (bad):** `/commit` covers conventional commits, validate, stage, and push (3 workflows)

**Better:** `/commit` (commit), `/push` (push), `/pre-flight` (validate)

---

## DETAIL: Advisor vs Enforcer

Agents should be **advisors** (read-only, guidance), not **enforcers** (check state, gate decisions).

| Bad | Good |
| --- | --- |
| Agent enforces a business rule | Should be a unit test |
| Agent checks product state | Should be a product feature |
| ✅ Agent answers domain questions | Read-only, provides guidance |

---

## DETAIL: Allowed-Tools

Grant minimum permissions needed:

| Role | Tools |
| --- | --- |
| Advisor (agent) | Read, Glob, Grep only (no execution) |
| Validator | Bash with specific patterns: `Bash(nix flake check*)` |
| Writer | Write for generated files only: `Write(.claude/skills/**)` |
| Code reviewer | Read, Bash for output (never Write) |

**Test:** Remove one permission. Does the skill still work? If yes, remove it.

---

## TEMPLATE: Skill

```markdown
---
name: skill-name
description: [One-liner, specific, <80 chars]
allowed-tools: Bash(git add*), Bash(git commit*), Read, Write
---

# [Skill Name]

## PURPOSE

[One-liner: What + when, ≤10 tokens]

## CRITICAL

- [Non-negotiable constraint]
- [Catastrophic mistake prevention]

## ASSUMES

- [Environment assumption]
- [When this breaks, skill needs rewrite]

## STANDARD PATH

[Prose describing happy path]

\`\`\`bash
[commands for happy path]
\`\`\`

## EDGE CASES

- [Case name] — read DETAIL: Name if you encounter this

## DETAIL: Edge Case Name

[Explanation when triggered]
```

---

## TEMPLATE: Agent

```markdown
---
name: agent-name
description: [One-liner, specific, <80 chars]
model: haiku
allowed-tools: Read, Glob, Grep
---

# [Agent Name]

## PURPOSE

[What questions does this answer about what domain?]

## CRITICAL

- [Boundary: "read-only, never execute"]
- [Domain rule: "all queries must include X context"]

## ASSUMES

- [File structure assumptions]
- [Domain knowledge assumptions]

## STANDARD QUESTION

[Example question the agent answers well]

[Agent's structured response format]

## RELATED

- [Related agents/skills]
```

---

## RELATED

- `/documentation-writer` — Write scannable docs using progressive disclosure
- `/harness audit` — Audit skills for structure compliance
- `agents/references/hooks-reference.md` — Plugin hooks.json schema, events, and gotchas (for plugins that include hooks)

## SOURCES

- [Progressive Disclosure | ixdf.org](https://ixdf.org/literature/topics/progressive-disclosure/)
- [Agent Skills: Progressive Disclosure](https://www.newsletter.swirlai.com/p/agent-skills-progressive-disclosure)
