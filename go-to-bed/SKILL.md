---
name: go-to-bed
description: End-of-day routine that reviews all learnings from the current session, updates relevant docs/skills/notebooks, commits, and pushes. Run when Chad says "go to bed", "wrap up", "end of day", or "EOD".
tools: [Bash, Read, Write, Edit]
---

# Go to Bed — End-of-Day Knowledge Capture

> Consolidates the day's learnings into permanent documentation so nothing is lost
> overnight. Reviews what was discovered, debugged, built, or discussed — then
> updates all relevant docs, skills, and notebooks before pushing.

## When to trigger

- User says "go to bed", "wrap up", "end of day", "EOD", "close out"
- User asks to "save everything" or "make sure nothing is lost"

## Pipeline

### Phase 1: Audit the Day

1. **Review the conversation** — scan the full session for:
   - New patterns discovered (debugging, configuration, platform behavior)
   - Bugs found and fixed (root causes, not just symptoms)
   - Platform behaviors confirmed (from eng, from Slack threads, from testing)
   - New code deployed (what it does, why it exists)
   - Manual steps documented (Agent Builder config, permission changes, data fixes)
   - Decisions made (why option A over B)

2. **Identify target docs** — for each learning, determine where it belongs:
   - `~/.claude/skills/sra-agent-debugger/SKILL.md` — debugging patterns, diagnostic tables, trace interpretation
   - `~/.claude/skills/sra-expert/SKILL.md` — SRA platform knowledge, configuration patterns
   - `~/.aisuite/notebook/<today>/` — day-specific notes, reference docs, research
   - `~/pet-travel-demo/skill/REBUILD-AGENT.md` — action configuration (Agent Builder setup)
   - `~/pet-travel-demo/skill/KNOWLEDGE-ARTICLE.md` — knowledge article setup
   - Other skills as relevant

3. **Check what's already captured** — read existing docs to avoid duplicating content that was already written during the session.

### Phase 2: Update Docs

For each uncaptured learning:
- **Skills** — add to the appropriate diagnostic table, pattern section, or checklist
- **Notebook** — create or append to today's day folder with reference-quality notes
- **REBUILD-AGENT.md** — update if action configs changed
- **Cross-references** — add pointers between docs so related info is discoverable

Writing rules:
- Be concise and scannable (tables > paragraphs)
- Include the "why" and the evidence (trace data, Slack thread, test result)
- Write for future-Chad who has no memory of today's context
- Include exact steps to reproduce or configure (not vague guidance)
- Never duplicate — if it's already in a doc, add a cross-reference instead

### Phase 3: Update Landing Page

The AI landing page lives at:
- **Repo:** `~/APDLC-Tools-and-Docs/` → `git@git.soma.salesforce.com:chad-goldsmith/APDLC-Tools-and-Docs.git`
- **Live URL:** https://git.soma.salesforce.com/pages/chad-goldsmith/APDLC-Tools-and-Docs/
- **File:** `index.html` (single-page app with cards + detail panels)

If the day's work introduced:
- A new tool, skill, or capability → add/update a card on the landing page
- A significant new workflow or pattern → update the relevant card's detail content
- New metrics (e.g., PRD count, trace count, skill count) → update the numbers

**Learning of the Day** — ALWAYS update this section in `index.html`:
1. Pick the single most interesting/surprising AI-related learning from the day
2. Find the `<!-- Learning of the Day -->` section
3. Update:
   - `id="lotd-date"` — today's date (e.g. "Jun 23, 2026")
   - `id="lotd-text"` — 1-2 sentence learning, written for someone who doesn't know SRA internals
   - `id="lotd-tag-1"`, `id="lotd-tag-2"`, `id="lotd-tag-3"` — 3 short category tags relevant to the learning
4. Good learnings: platform behaviors confirmed, counterintuitive gotchas, workflow discoveries, AI tool composition patterns
5. Bad learnings: generic tips, obvious things, internal jargon without explanation

Only update cards/metrics if there's something genuinely new to surface. Don't touch cards for minor bug fixes or internal-only doc updates.

### Phase 3b: Skills Sync Audit

**Full audit of local skills against all skill-containing repos under `git.soma.salesforce.com/chad-goldsmith`.**

**Repos with skills:**

| Repo | Local Clone | What it holds |
|------|-------------|---------------|
| `chad-goldsmith/claude-skills` | `~/prd-writer-skill/` | All personal skills (mirror of `~/.claude/skills/`) |
| `chad-goldsmith/APDLC-Tools-and-Docs` | `~/APDLC-Tools-and-Docs/` | Landing page + prototypes |
| `service-cloud/pm-fy27pdlc-releases` | `~/pm-fy27pdlc-releases/` | Team shared skills (`pm-cg-*` prefix) |

**Audit steps:**

1. **Diff local vs. claude-skills repo** — for every folder in `~/.claude/skills/`:
   ```bash
   for skill in ~/.claude/skills/*/; do
     name=$(basename "$skill")
     repo_path=~/prd-writer-skill/"$name"
     if [ -d "$repo_path" ]; then
       diff -q "$skill/SKILL.md" "$repo_path/SKILL.md" 2>/dev/null
     else
       echo "NEW: $name (not in repo yet)"
     fi
   done
   ```
   - If local is newer → copy to repo, stage for commit
   - If repo has it but local doesn't → note it (may have been intentionally removed)

2. **Check for new skills not yet in repo** — any local skill folder without a match in `~/prd-writer-skill/` gets copied over

3. **Team repo sync check** — for skills shared to `pm-fy27pdlc-releases`:
   - The shared version lives at `~/.claude/skills/{name}-shared/SKILL.md` (customer data stripped)
   - The team repo version lives at `~/pm-fy27pdlc-releases/.claude/skills/pm-cg-{name}/SKILL.md`
   - Diff the `-shared` local version (body only, skip frontmatter) vs team repo
   - If local shared is newer → copy body to team repo (preserve team repo frontmatter: `name`, `author`, `source`, `status` fields), stage for commit
   - Known shared skills: `sra-expert-shared` → `pm-cg-sra-expert`

4. **Report** — print a table:
   ```
   🔄 Skills Sync Audit:
   ✅ In sync: [count] skills
   📤 Updated in claude-skills repo: [list]
   📤 Updated in team repo: [list]
   🆕 New skills added to repo: [list]
   ⚠️  In repo but not local: [list]
   ```

**Always run this audit** — even if the session didn't create new skills. Skills get modified during debugging, doc updates, and refactors without explicit "I'm updating a skill" moments.

### Phase 4: Commit & Push

1. **pet-travel-demo repo** (`~/pet-travel-demo/`) — if there are uncommitted changes:
   - `git add` relevant files (not flexipages/SDO noise)
   - Commit with descriptive message
   - `git push`

2. **APDLC-Tools-and-Docs repo** (`~/APDLC-Tools-and-Docs/`) — if landing page was updated:
   - `git add index.html`
   - Commit with descriptive message
   - `git push`

3. **claude-skills repo** (`~/prd-writer-skill/` → `git@git.soma.salesforce.com:chad-goldsmith/claude-skills.git`) — ALWAYS sync:
   - Copy any new or modified skills from `~/.claude/skills/` into this repo
   - Compare dirs: if local skill has changes not in repo, copy over
   - `git add` new/changed skill dirs
   - Commit with descriptive message
   - `git push`
   - This keeps the shared repo at https://git.soma.salesforce.com/chad-goldsmith/claude-skills in sync with local skills

4. **SRA PRD Portfolio** (`~/sra-prds/` → `git@git.soma.salesforce.com:chad-goldsmith/sra-prds.git`) — ALWAYS sync:
   - Check if any PRDs/PBDs were created or updated during the session (in `~/.agents/artifacts/prds/` or `~/prd-writer-skill/prds/`)
   - Copy new/updated PRDs into `~/sra-prds/` with proper filename convention (`prd-{release}-{slug}.md` or `pbd-{release}-{slug}.md`)
   - Ensure frontmatter matches sra-prds format (`ga_version`, `stage`, `team`, `authoring_pm`, etc.)
   - Run `python3 generate-index.py` to rebuild the portfolio page
   - `git add` changed files + `index.html`
   - Commit with descriptive message
   - `git push`
   - Live at: https://git.soma.salesforce.com/pages/chad-goldsmith/sra-prds/

5. **Verify** — `git status` on all repos to confirm clean state

4. **Summary** — print a short bulleted recap of what was captured and where

## Output Format

After completing, print:

```
🌙 End-of-day wrap-up complete.

📝 Updated:
- [list of docs/skills updated with 1-line description of what was added]

📦 Pushed:
- [repo] — [commit message summary]

💡 Key learnings captured:
- [bullet list of the most important things preserved]

⚠️ Still pending (manual):
- [anything that needs hand-done in a UI, or deferred to next session]
```

## Important

- Do NOT create new files unless the content genuinely doesn't fit anywhere existing
- Do NOT touch `.claude/settings.json` or any config files
- Do NOT push to any repo without showing what's being committed
- If the session was light (just chatting, no real learnings), say so — don't manufacture content
- Always check `git status` before committing to avoid including unintended files
