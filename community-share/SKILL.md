---
name: community-share
description: "Manages sharing skills to the Agentic PDLC PM team repo. Prompts when new skills are created, creates shareable versions (strips personal paths, adds installation docs), and publishes to service-cloud/pm-fy27pdlc-releases with pm-cg- prefix."
tools: [Write, Read, Edit, Bash]
---

# Community Share

> Manages the lifecycle of sharing your skills with the broader Agentic PDLC PM team.

**Team repo:** `git@git.soma.salesforce.com:service-cloud/pm-fy27pdlc-releases.git`
**Skills path:** `.claude/skills/pm-cg-{skill-name}/SKILL.md`
**Naming convention:** All shared skills use `pm-cg-` prefix (PM Chad Goldsmith)

---

## When to Trigger

### Proactive (after skill creation/major update)

After ANY new skill is created or an existing skill gets a major rewrite, ask:

> **Community share?**
> I just created/updated `{skill-name}`. Would you like me to:
> 1. Create a shared version (`pm-cg-{skill-name}`)
> 2. Publish it to the team repo
> 3. Both
> 4. Skip — this one's personal

**Skip automatically for these (always personal):**
- `go-to-bed`, `good-morning`, `caturday` — personal routines
- `ai-landing-page` — personal dashboard
- `cvs-sra-tracking` — customer-specific
- Any skill with org credentials, personal API keys, or private Slack channels

**Customer Data Rule (STANDING):**
Customer-specific data (names, channels, contacts, account details, concern docs) NEVER goes into skill files or shared repos. Customer data lives ONLY in:
- `~/.claude/customer-registry.json` (private, gitignored)
- `~/.agents/artifacts/customer-advocacy/` (private output docs)

Skills that reference customer data must read from these private files at runtime — the SKILL.md itself contains only generic logic and placeholder references. This applies to shared AND local skills. If a skill currently has customer data baked in (e.g., `cvs-sra-tracking`), it should be refactored to separate the data out before sharing.

### Manual invocation

```
/community-share {skill-name}        — share a specific skill
/community-share list                — show what's shared vs. local-only
/community-share sync                — push any local updates to team repo
/community-share status              — check if team repo is up to date
```

---

## Pipeline

### Step 1: Clone/Update Team Repo

```bash
# Local clone location
TEAM_REPO=~/pm-fy27pdlc-releases

# Clone if not exists, pull if exists
if [ -d "$TEAM_REPO" ]; then
    cd $TEAM_REPO && git pull origin master
else
    git clone git@git.soma.salesforce.com:service-cloud/pm-fy27pdlc-releases.git $TEAM_REPO
fi
```

### Step 2: Create Shared Version

Transform the local skill into a team-shareable version:

**Strip:**
- Personal file paths (`~/sra-prds/`, `~/.agents/artifacts/`, `~/APDLC-Tools-and-Docs/`)
- Personal repo URLs (replace with `{your-repo}` placeholders or generic instructions)
- References to personal routines or workflows
- Hardcoded Slack channel IDs or private channels
- Any org credentials or instance-specific config

**Add:**
- Installation instructions (copy folder to `~/.claude/skills/`)
- Prerequisites section (what tools/access needed)
- "Adapt to your setup" notes where paths are environment-specific
- Author attribution: `author: Chad Goldsmith`
- Source tag: `source: chad-goldsmith`

**Keep:**
- All functional logic and structure
- Tool requirements
- Examples and templates
- Domain knowledge and patterns

### Step 3: Format to Team Standard

Follow `.claude/skills/SKILL_AUTHORING.md` from the team repo:

```markdown
---
name: pm-cg-{skill-name}
description: "{one-sentence, ≤200 chars}"
author: Chad Goldsmith
source: chad-goldsmith
status: live
---

# {Human-Readable Title}

{One-paragraph elevator pitch.}

**Trigger:** Manual — invoke as `/pm-cg-{skill-name} [args]`

**Examples:**
- `/pm-cg-{skill-name} example one`
- `/pm-cg-{skill-name} example two`

---

{Rest of skill content}
```

### Step 4: Write README.md

**Every shared skill folder MUST include a `README.md`** alongside `SKILL.md`. This is the human-readable landing page for anyone browsing the repo.

```markdown
# pm-cg-{skill-name}

> {One-sentence description}

**Author:** Chad Goldsmith
**Source:** [claude-skills repo](https://git.soma.salesforce.com/chad-goldsmith/claude-skills)

---

## What It Does

{2-3 sentences explaining the skill's purpose and output}

## Quick Start

1. This skill is already available in the team repo — just invoke:
   ```
   /pm-cg-{skill-name} [args]
   ```

2. Or copy to your personal skills for customization:
   ```bash
   cp -r .claude/skills/pm-cg-{skill-name} ~/.claude/skills/pm-cg-{skill-name}
   ```

## Configuration

{Section explaining what the user needs to adapt for their own use:}

| Setting | Default | How to Change |
|---------|---------|---------------|
| Output path | `.agents/artifacts/` | Edit the save location in SKILL.md Step X |
| Repo URL | `{your-repo}` | Replace with your GitHub Pages-enabled repo |
| PRD format | APDLC one-pager | Adjust templates in SKILL.md Phase 2 |
| Portfolio link | None | Add your team's portfolio URL |

## Prerequisites

- Claude Code with {tools} access
- {Any other requirements: Slack, org access, etc.}

## Examples

```
/pm-cg-{skill-name} {example 1}
/pm-cg-{skill-name} {example 2}
```

## Related Skills

- `{other-skill}` — {how it relates}

## Questions?

Ping **Chad Goldsmith** in #agentic-pdlc or see the source repo.
```

### Step 5: Write to Team Repo

```bash
mkdir -p $TEAM_REPO/.claude/skills/pm-cg-{skill-name}
# Write SKILL.md
# Write README.md
# Copy any templates/ or references/ if needed
```

### Step 6: Commit and Push

```bash
cd $TEAM_REPO
git add .claude/skills/pm-cg-{skill-name}/
git commit -m "Add pm-cg-{skill-name}: {short description}"
git push origin master
```

### Step 7: Update Registry

Maintain a local registry of what's shared:

**File:** `~/.claude/skills/community-share/shared-registry.json`

```json
{
  "shared": [
    {
      "local": "pm-pretotype",
      "team": "pm-cg-pretotype",
      "last_synced": "2026-06-26",
      "version": "2.0"
    }
  ],
  "skipped": ["go-to-bed", "caturday", "ai-landing-page"]
}
```

---

## Commands

### `/community-share {skill-name}`

Share a specific skill:
1. Read the local skill from `~/.claude/skills/{skill-name}/`
2. Create shared version (strip personal, add install docs)
3. Save to `~/.claude/skills/pm-cg-{skill-name}/` (local shared copy)
4. Also save to `~/prd-writer-skill/pm-cg-{skill-name}/` (personal repo)
5. Ask: "Push to the team repo now?"
6. If yes → write to `~/pm-fy27pdlc-releases/.claude/skills/pm-cg-{skill-name}/`, commit, push

### `/community-share list`

Show status of all skills:
```
📦 Shared to team repo:
  pm-cg-pretotype          (synced Jun 26)
  pm-cg-pdlc-audit         (synced Jun 24)

🏠 Local only (shareable):
  sf-clt-builder           — CLT config guide
  sra-expert-shared        — SRA knowledge base

🔒 Personal (never share):
  go-to-bed, caturday, ai-landing-page, cvs-sra-tracking
```

### `/community-share sync`

For each skill in the shared registry:
1. Diff local version vs. team repo version
2. If local is newer → update team repo, commit, push
3. Report what was synced

### `/community-share status`

Quick check:
- Is `~/pm-fy27pdlc-releases` cloned and up to date?
- Any local skills with changes not pushed to team?
- Any new skills created since last share prompt?

---

## What Makes a Good Shared Skill

**Share if:**
- Other PMs could use it for their features (not just SRA)
- It encodes a repeatable workflow or process
- It fills a gap in the team repo (check existing skills first)
- It has been validated through actual use (not theoretical)

**Don't share if:**
- It requires access to specific orgs or private data
- It's a personal productivity routine
- It duplicates something already in the team repo
- It's half-baked or experimental

---

## Existing Skills Ready to Share

| Local Skill | Team Name | Status | Notes |
|-------------|-----------|--------|-------|
| `pm-pretotype-shared` | `pm-cg-pretotype` | Ready | PBD → One-Pager → Pretotype pipeline |
| `sc-pdlc-audit` | `pm-cg-pdlc-audit` | Ready | PRD quality gate |
| `sra-expert-shared` | `pm-cg-sra-expert` | Ready | SRA knowledge base |
| `sra-setup-debug` | `pm-cg-setup-debug` | Needs strip | Org diagnostic |
| `sf-clt-builder` | `pm-cg-clt-builder` | Needs strip | Agent Builder CLT config |
| `sra-test-case-writer` | `pm-cg-test-cases` | Needs strip | Generate test scenarios from PRD |

---

## Integration with Go-to-Bed

During the end-of-day routine, if new skills were created during the session:
- The go-to-bed skill should note: "New skill created: {name} — run `/community-share` to publish"
- Does NOT auto-share — always asks first

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-26 | Initial creation — community share management skill |
