---
name: cvs-sra-tracking
description: "Track a strategic customer account's SRA adoption — requirements, gaps, blockers, exec escalations, and engagement. Living account tracker that reads from private data files."
tools: [mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_google_google__docs_search, mcp__plugin_google_google__docs_get, Read, Write, Edit, Agent]
---

# Customer SRA Account Tracker

> Living tracker for strategic customer SRA deployments — requirements, gaps, blockers,
> exec escalations, engagement history, and dependencies on platform migrations.
> Keep sourced and dated; separate confirmed facts from open questions.

**Invocation:** `/cvs-sra-tracking` (optional: a question, channel, or "log this update")

---

## Customer Data Privacy

**All customer-specific data lives in private files — NEVER in this skill.**

| Data | Location |
|------|----------|
| Account details, contacts, channels | `~/.claude/customer-registry.json` |
| Tracker data (requirements, blockers, decisions, people) | `~/.agents/artifacts/customer-advocacy/{customer}-tracker-data.md` |
| Action plans & advocacy briefs | `~/.agents/artifacts/customer-advocacy/{customer}-*.md` |

**On invocation:**
1. Read `~/.claude/customer-registry.json` for account context and channels
2. Read `~/.agents/artifacts/customer-advocacy/{customer}-tracker-data.md` for current state
3. Optionally search Slack channels from the registry for recent updates

---

## Tracker Structure

The private data file (`{customer}-tracker-data.md`) maintains these sections:

### TL;DR
2-4 bullet summary of current situation — blockers, escalations, next milestone.

### Key Sources
Links to requirements docs, exec briefings, escalation threads. (Google Doc IDs, Slack file IDs.)

### Customer Environment
What makes this customer technically complex or unique.

### Requirements & SRA Responses
Table: customer requirement → SRA response/status (✅ covered, 🟡 in progress, 🔴 blocked, ❓ needs info).

### Blockers
Table: blocker → status → notes. Link to related skills (e.g., `sra-nga-migration`, `sra-latency-research`).

### Open Questions
What we still need to learn from the customer or internally.

### People
Internal (PM, FDE, eng) and customer-side contacts. Roles and ownership.

### Decisions / Commitments Log
Dated table: what was decided, source/evidence.

---

## How to Update

When new materials arrive (Slack, docs, meeting notes):
1. Date the update and cite the source
2. Update the relevant section in the private tracker data file
3. Log any new decision in the Decisions table with who/why
4. Flag new blockers or resolved items
5. Keep customer-stated needs vs. SRA responses clearly separated
6. Flag perception/messaging risks distinctly from technical blockers

---

## Related Skills

| Skill | Relationship |
|-------|-------------|
| `sra-nga-migration` | Platform migration tracker — many customers gated on this |
| `sra-latency-research` | Latency concerns frequently raised by enterprise customers |
| `customer-advocate` | For processing new concern lists into action plans + briefs |
| `sra-expert` | Product knowledge for answering "can SRA do X?" |

---

## Key Behaviors

- NEVER stores customer names, contacts, channels, or account details in this SKILL.md
- All customer data reads from private files at runtime
- Clearly separates technical blockers from perception/messaging issues
- Cross-references the NGA migration skill for platform dependency status
- When updating, always dates entries and cites the source
- Flags when information is stale (>2 weeks on a fast-moving account)
- Never commits private tracker files to any git repo

---

## Error Reference

| Problem | What to do |
|---|---|
| No tracker data file found | Create one at `~/.agents/artifacts/customer-advocacy/{customer}-tracker-data.md` |
| Customer not in registry | Add them to `~/.claude/customer-registry.json` first |
| Slack channel not accessible | Note the gap; proceed with available sources |
| Conflicting information (doc vs. Slack) | Note both, flag as "needs reconciliation", cite both sources |
| Stale data (>2 weeks, fast-moving account) | Search Slack for recent updates before reporting status |
