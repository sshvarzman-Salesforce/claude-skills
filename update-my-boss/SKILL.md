---
name: update-my-boss
description: "Generate a VP-level weekly status update for SRA Product Management. Covers recent wins, upcoming week priorities, key accounts, risks, and what to watch. Designed for exec consumption — concise, structured, opinionated."
tools: [mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_google_google__docs_search, mcp__plugin_google_google__docs_get, Read, Write, Edit]
---

# Update My Boss — VP-Level Weekly Status

> Produces a structured weekly status update suitable for VP/Director audience.
> Designed for a PM leading a product area (Service Rep Assistant) who needs to
> communicate up clearly: what shipped, what's coming, what's at risk, and what
> needs exec attention.

**Invocation:** `/update-my-boss` (optional: time range, special topics, or "I'm going OOO")

**Examples:**
- `/update-my-boss` — generates this week's update
- `/update-my-boss OOO next week, TJ covering` — adds coverage info + what to watch
- `/update-my-boss last 2 weeks` — broader recap for returning from PTO

---

## Output Format

The update follows a fixed structure. Every section is required but can be "nothing to report" if genuinely empty. Write for someone who has 30 seconds to scan.

```markdown
# Service Rep Assistant — Weekly Update ({date range})
{One-line context if relevant: OOO coverage, milestone week, etc.}

## Wins (Last {N} Days)
{Bullet each win with a single emoji + bold headline + 1-line detail}
{Wins = shipped code, customer go-lives, signed-off releases, resolved escalations}

## Shipping This Week
{What's deploying or publishing. Include dates, dependencies, known issues.}

## Key Accounts
{Status of strategic customers. Use traffic light: :red_circle: :yellow_circle: :green_circle:}
{For each: 1-line status + the single most important thing to know}

## Risks & Watch Items
{Things that could escalate. Be specific: what, when, who owns, what happens if ignored.}
{Include licensing, billing, org perm, gate flag, or cross-team dependency risks.}

## Next Week Priorities
{Numbered list of what's being worked on. Include owner if not Chad.}

## FYI / Context
{Non-urgent but useful: internal customer decisions, model upgrades, cross-team pivots}
```

---

## Research Pipeline

When generating the update, gather from these sources:

### 1. Slack Channels (search last 7-14 days)
| Channel | What to look for |
|---------|-----------------|
| Team channel (meta-sra-internal or similar) | Daily updates, decisions, blockers |
| Customer collab channels | Go-live announcements, escalations, feedback |
| Release channels | Sign-off status, release notes, known issues |
| FDE/field channels | Customer deployment status, field questions |
| OrgCS channels | Internal adoption status, blockers |
| Eng channels | Code drops, bug fixes, regression reports |

### 2. Skills & Artifacts (local knowledge)
| Source | What to pull |
|--------|-------------|
| `~/.claude/skills/sra-expert/SKILL.md` | Platform behaviors, known issues, model status |
| `~/.claude/skills/sra-nga-migration/SKILL.md` | Migration status, blockers |
| `~/.agents/artifacts/customer-advocacy/` | Customer action plans, latest status |
| `~/sra-prds/` | PRD portfolio — what's in flight |

### 3. User-Provided Context
The user will often paste or dictate raw context (Slackbot summaries, notes, bullet points). Treat user-provided content as ground truth — refine the language for VP audience but don't change facts.

---

## Writing Rules for VP Audience

1. **Lead with outcomes, not activities.** "Calix went live" not "we had calls with Calix."
2. **Be specific on dates.** "June 30" not "next week." "July 21" not "after licensing."
3. **One sentence per bullet.** If it needs two sentences, it's two bullets.
4. **Traffic lights mean something:**
   - :green_circle: = on track, no action needed from leadership
   - :yellow_circle: = issue exists, team is handling, exec awareness only
   - :red_circle: = needs exec attention or decision, escalation risk
5. **Don't bury the lede.** If there's a single thing the VP needs to act on, call it out at the top.
6. **Name names.** Who's covering, who owns the risk, who's the customer contact.
7. **Quantify where possible.** "3 known issues (P1/P2)" not "some known issues."
8. **No jargon without context.** First mention of an acronym gets a parenthetical. VP may not know what "AQWK" or "CLT" means.
9. **Separate facts from opinions.** If you're editorializing (e.g., "this is fine" or "this concerns me"), flag it.
10. **Keep it to one screen.** If the VP has to scroll more than once on a laptop, it's too long.

---

## OOO Variant

When the user mentions they're going OOO, add:
- **Coverage line** at the top: who's covering what
- **"What to Watch" framing** — shift from "here's what I'm doing" to "here's what could come up"
- **Escalation path** — who to ping for what category of issue
- **Don't worry about** — explicitly call out things that look scary but are handled

---

## Tone

- Professional but not formal. Write like a senior PM talks to their VP in a 1:1.
- Confident. Don't hedge unless there's genuine uncertainty.
- Brief. Respect the reader's time.
- Honest about risks. VPs hate surprises more than bad news.

---

## Integration with Other Skills

| Skill | How it connects |
|-------|----------------|
| `sra-expert` | Pull platform knowledge, known behaviors, model status |
| `customer-advocate` | Pull latest customer status from action plans |
| `sra-nga-migration` | Pull migration status for "strategic context" section |
| `sra-latency-research` | Pull latency metrics if performance is a topic |

---

## Privacy Rules

- Customer names are OK in VP updates (internal audience)
- Don't include customer org IDs, credentials, or PII
- Don't include exact Slack message links unless the VP is in those channels
- ARR/revenue figures only if the user provides them

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-26 | Initial skill creation |
