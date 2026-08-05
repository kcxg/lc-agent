---
name: create-skill
description: >-
  Create Agent Skills following the open standard (agentskills.io).
  Use when authoring a new skill, editing an existing skill,
  or asking about SKILL.md structure, frontmatter fields, or skill best practices.
---

# Creating Agent Skills

Skills follow the [Agent Skills](https://agentskills.io) open standard — a cross-platform format adopted by Claude Code, OpenAI Codex, Gemini CLI, GitHub Copilot, Cursor, and Microsoft Agent Framework.

## Workflow

1. **Clarify scope** — ask what task the skill encodes, who triggers it, and where to store it.
2. **Choose location** — project-level (`.agents/skills/` or `.claude/skills/`) or personal (`~/.agents/skills/` or `~/.claude/skills/`). Check your platform's docs for exact paths.
3. **Draft the description first** — it is the single most important field; everything else follows from it.
4. **Write the body** — step-by-step instructions, examples, edge cases.
5. **Extract long reference** — move anything over ~100 lines into `references/` files.
6. **Validate** — run `scripts/validate_skill.py <skill-dir>` to check encoding, frontmatter, naming, and structure.

## Directory layout

```
skill-name/
├── SKILL.md          # Required — metadata + instructions
├── scripts/          # Optional — executable code the agent can run
├── references/       # Optional — docs loaded on demand
└── assets/           # Optional — templates, schemas, static resources
```

## Frontmatter reference

```yaml
---
name: skill-name                # required, 1-64 chars, lowercase + hyphens, must match directory name
description: >-                 # required, 1-1024 chars, WHAT it does + WHEN to use it
  Extract PDF text, fill forms, merge files.
  Use when handling PDFs or when the user mentions document extraction.
license: MIT                    # optional
compatibility: Requires Python 3.12+  # optional, max 500 chars, environment requirements
metadata:                       # optional, arbitrary key-value pairs
  author: example-org
  version: "1.0"
disable-model-invocation: true  # de-facto cross-platform convention — prevents auto-trigger
---
```

### `name` rules

- Lowercase letters, digits, hyphens only
- No leading/trailing/consecutive hyphens
- Must equal the parent directory name
- Examples: `code-review`, `pdf-processing`, `data-analysis`

### `description` — the most critical field

The agent sees only `name` + `description` at startup and uses them to decide whether to load the full body. A vague description means the skill never fires.

**Rules:**

1. Front-load what the skill does, then state when to use it.
2. Include specific trigger keywords — tool names, file types, commands, task verbs.
3. Write in third person ("Generates commit messages…", not "I help you…").
4. One trigger per distinct use case; collapse synonyms.
5. Stay under 1024 characters.

**Good:**

```yaml
description: >-
  Review code for quality, security, and maintainability following team standards.
  Use when reviewing pull requests, code changes, or when the user asks for a code review.
```

**Bad:**

```yaml
description: Helps with code.
```

### `disable-model-invocation`

Not yet part of the core spec, but a cross-platform convention supported by Claude Code, Cursor, and GitHub Copilot. Set to `true` for skills with side effects (deploy, commit, send message) or skills you only want triggered by name.

## Writing the body

The body loads **only after** the skill triggers. Every token competes for context window space. "When to use this skill" sections in the body are wasted — the agent never sees them before deciding to activate. Put all triggering info in the `description`.

### Guiding principles

- **The agent is already smart.** Only write what it does not already know. Run the "no-op test": if removing a sentence changes nothing about agent behavior, delete it.
- **Under 500 lines.** Move detailed reference into `references/` files, loaded on demand via relative links like `[guide](references/REFERENCE.md)`.
- **One level of file reference.** Link from SKILL.md → reference file. Do not chain reference → reference.

### Degrees of freedom

Match specificity to how fragile the task is:

- **High freedom** (text instructions): Multiple valid approaches, context-dependent decisions. Example: code review guidelines.
- **Medium freedom** (pseudocode/templates): A preferred pattern exists, some variation acceptable. Example: report generation.
- **Low freedom** (specific scripts): Operations are fragile, consistency critical, exact sequence required. Example: database migrations.

### What NOT to include

A skill should only contain files the agent needs to do the job. Do not create:

- README.md, CHANGELOG.md, INSTALLATION_GUIDE.md
- User-facing documentation about the skill itself
- Setup/testing procedures for the skill author

### Recommended sections

- **Scope / Preconditions** — what the skill assumes is already true (e.g. "requires a git repo")
- **Steps** — ordered actions with checkable completion criteria
- **Examples** — concrete inputs → outputs
- **Edge cases** — known gotchas and how to handle them

Not every section is needed. A simple skill may be all steps; a review checklist may be all reference. Do NOT add a "When to use" section in the body — that info belongs in `description` (the body loads only after activation).

### Completion criteria

Every step should end on a condition the agent can check — "all modified files accounted for", not "understanding reached". A vague criterion invites premature completion.

### Leading words

A compact concept from the model's pretraining that anchors behavior in minimal tokens. Example: instead of writing "fast, deterministic, low-overhead" repeatedly, use _tight_. The model's priors do the work; you save tokens.

### When to use scripts, references, or assets

| Folder | Use when | Example |
|--------|----------|---------|
| `scripts/` | Deterministic, repeatable, fragile operations | `validate.py`, `rotate_pdf.py` |
| `references/` | Detail exceeds ~100 lines or is rarely needed | API docs, full schema, style guide |
| `assets/` | Static files the agent copies or fills in | templates, schemas, sample configs |

Scripts should be **executed** by the agent (not read into context). References are **read** into context on demand.

## Progressive disclosure

Agents load skills in stages:

| Stage | What loads | Token budget |
|-------|-----------|-------------|
| Discovery | `name` + `description` | ~100 tokens |
| Activation | Full SKILL.md body | < 5000 tokens recommended |
| Execution | `references/`, `scripts/`, `assets/` | As needed |

Decision-making instructions belong in SKILL.md; detailed reference material belongs in subfolders.

## Common patterns

### Template pattern

Provide output format templates the agent fills in:

```markdown
## Report format

Use this template:
- **Title**: [Analysis Title]
- **Summary**: [one paragraph]
- **Findings**: [bullet list with data]
- **Recommendations**: [numbered actions]
```

### Workflow pattern

Break operations into checkable steps:

```markdown
## Deployment workflow

- [ ] Run tests
- [ ] Build artifacts
- [ ] Deploy to staging
- [ ] Verify staging
- [ ] Deploy to production
```

### Conditional pattern

Guide through decision points:

```markdown
## Choose approach

**Creating from scratch?** → Follow "Creation workflow" below.
**Editing existing?** → Follow "Editing workflow" below.
```

### Feedback loop pattern

For quality-critical tasks:

```markdown
1. Make edits
2. Run `python scripts/validate.py`
3. If validation fails → fix and re-run
4. Proceed only when validation passes
```

## Anti-patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Verbose explanation of obvious concepts | Wastes tokens, agent already knows | Delete — apply the no-op test |
| Multiple tool recommendations without default | Agent picks randomly | Provide one default, escape hatch for alternatives |
| Time-sensitive information | Goes stale | Use a "deprecated" details block |
| Negation-based instructions ("don't do X") | Names the forbidden behavior, making it more likely | State the positive target instead |
| Deeply nested file references | Agent may not follow chains | Keep references one level deep |

## Complete example

A minimal but complete skill for deploying to Vercel:

```
deploy-vercel/
├── SKILL.md
└── scripts/
    └── verify_deploy.sh   # curl -sf "$1" > /dev/null && echo "OK" || echo "FAIL"
```

```yaml
---
name: deploy-vercel
description: >-
  Deploy a Next.js or static site to Vercel. Use when the user asks to deploy,
  ship, or push to production on Vercel.
disable-model-invocation: true
---
```

```markdown
## Scope

Assumes: Node.js 18+, Vercel CLI installed, project has `package.json`.

## Steps

1. Run `vercel --prod` from the project root.
2. Wait for the deployment URL.
3. Run `scripts/verify_deploy.sh <url>` to confirm a 200 response.
4. Report the live URL to the user.

## Edge cases

- Monorepo: pass `--cwd packages/web` to target the correct package.
- First deploy: run `vercel link` first to connect the project.
```

Note: `disable-model-invocation: true` because deployment has side effects.

## Pre-ship checklist

- [ ] `name` matches directory name exactly
- [ ] `description` states WHAT + WHEN with trigger keywords
- [ ] Body < 500 lines
- [ ] No README.md, CHANGELOG.md, or author-facing docs
- [ ] File references are one level deep
- [ ] Side-effect skills have `disable-model-invocation: true`
- [ ] Scripts tested and executable

## Platform compatibility

| Platform | Skill locations |
|----------|----------------|
| Claude Code | `~/.claude/skills/`, `.claude/skills/` |
| OpenAI Codex | `~/.agents/skills/`, `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| GitHub Copilot | `.copilot/skills/` |
| Cursor | Manual placement, spec-compliant |

All platforms share the same `SKILL.md` format. Platform-specific extensions (e.g. `disable-model-invocation`, OpenAI's `agents/openai.yaml`) are additive — a spec-compliant skill works everywhere.
