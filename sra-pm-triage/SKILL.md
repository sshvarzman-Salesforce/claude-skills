---
name: sra-pm-triage
description: Scans SRA engineering and product Slack channels for unanswered @Chad mentions. Surfaces questions with full context, maps each to the relevant PRD, flags PM bottlenecks, and identifies cross-team conflicts. Writes a running triage log and drafts replies on request.
tools: [mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_slack_slack__slack_send_message, mcp__plugin_slack_slack__slack_send_message_draft, Read, Write, Edit]
---

# SRA PM Triage

> Scan SRA engineering and product channels for unanswered @Chad mentions. Surface each question with context, map to PRDs, flag bottlenecks and cross-team conflicts, draft replies on request.

**Invocation:** `$ARGUMENTS` (optional: `--lookback 14` to override day window, `--draft` to auto-draft all replies, `--addressed <N>` to mark item N as resolved)

---

## Channel Registry

**Primary scan targets — internal SRA engineering channels only:**

These are the channels where SRA eng teams ask PM questions. This is the core triage signal.

| Channel | ID | What it covers |
|---|---|---|
| SOUP Engineering | `C041YHQ8LQ0` | SOUP eng team |
| SOBA Engineering | `C05UAR03WHY` | SOBA eng team — testing framework, quality metrics |
| Sox Engineering | `C02CLRPJT1R` | Sox eng team — service orchestration |
| NGS Engineering | `C06NDLHQJD7` | NGS — planner service, plan generation pipeline |
| SPA SF Engineering | `C02P450NJ84` | SPA SF eng team — UI components, LWC, service plan rendering |
| Service Assistant Engineering | `C06TPK97CCE` | Engineering-wide discussions, architecture decisions |
| Service Assistant for Conversations | `C08DEK0ND0B` | Messaging channel discussions |
| Service Assistant for Voice | `C09K1CCKL8J` | Voice channel discussions |
| Service Assistant Leads | `C07DVDVH26A` | Cross-functional leads — PM + Eng + UX alignment |

**Also scan:** `service-assistant-capabilities-*` channels (e.g. `service-assistant-capabilities-dynamic-plans`) — search by keyword when relevant.

**Excluded from triage** — do NOT surface mentions from these sources:
- Direct Messages (DMs) and Group DMs — handle those yourself
- Customer channels (`#sra-meta`, `#temp-ea-poc-*`, `#ups-*`, etc.) — customer-facing threads are not eng team questions
- FDE Collaboration (`C0AN1E181M3`) — field eng feedback, not internal eng questions
- SE Collaboration (`C08E300HPUK`) — pre-sales, not internal eng
- PM Leads (`C078Y9DEDEE`) — PM-to-PM, not eng questions
- A3 Record Companion (`C0A99FLAE1G`) — broad product channel, too noisy; only include if the mention is in a thread started by an eng team member asking a direct question

---

## PRD Registry (for mapping)

| PRD | Slug | Key topics |
|---|---|---|
| prd-262-show-hide-summary-plan-autorun | Auto Run / No Summary Plan | Auto Run, Summary Plan, Run Plan button, Voice no-summary, Messaging Auto Run, eligibility, LLM confidence check, feedback mechanism, intent visibility |
| prd-264-ae-dynamic-plan-reporting | AE Reporting | RecActorActionFeed, STDM, Service Insights, plan ended, session tracing, Agent Platform Tracing, AEA observability gap, ServicePlanner agent type |

Read the current PRD files from `.agents/artifacts/prds/` at the start of each run to keep the topic mapping current. New PRDs will be picked up automatically.

---

## Phase 0 — Determine Lookback Window

Default lookback: **7 days**. Override with `--lookback N` argument.

Parse today's date from the system context. Compute the earliest timestamp to include.

---

## Phase 1 — Scan Channels for Unanswered @Chad Mentions

Run two parallel search strategies and merge results — do NOT rely on channel-scoped user ID searches alone, as Slack does not reliably index raw user IDs in the `in:` filter:

**Strategy A — broad display name search (catches everything):**
```
slack_search_public_and_private:
  query: "@Chad Goldsmith after:{lookback_date}"
```
This is the primary signal. Paginate through ALL pages — do not stop at 20 results. Continue fetching next pages until no more results.

**Strategy B — channel-scoped searches using display name (catches channel-specific results that may rank lower):**
```
slack_search_public_and_private:
  query: "Chad Goldsmith in:<channel_id> after:{lookback_date}"
```
Run in parallel for all channels in the registry. Merge with Strategy A results, deduplicating by message_ts.

Collect every matching message across both strategies before filtering.

**Filter to unanswered only:**
- For each matching message, read the thread (`slack_read_thread`)
- A message is **unanswered by Chad** if:
  - Chad has NOT replied in the thread after the mention, AND
  - The thread's most recent message is NOT from Chad
- A message is **answered** if Chad's user ID (`U01G1CJ1LUW`) appears in any reply after the mention — skip it
- Apply the lookback window: discard messages older than the lookback date

**Filter to eng team questions only — discard:**
- Messages from DMs or Group DMs (channel type = DM/MPIM)
- Messages from excluded channels (customer channels, FDE, SE, PM Leads — see Channel Registry)
- FYI/CC mentions where no question is being asked — e.g. "cc @Chad", status updates, announcements, welcome messages
- Messages where Chad is mentioned only in passing (e.g. someone quoting a prior Chad comment, not directing a question at him)

**What to keep:** mentions in eng channels where the sender is an engineer or cross-functional lead asking Chad a direct question about product behavior, requirements, scope, or a PM decision.

After filtering, sort remaining items oldest-first (most overdue at the top).

---

## Phase 2 — Enrich Each Item

For each unanswered mention:

1. **Read the full thread** — get the parent message + all replies for context
2. **Summarize the question** — 2–3 sentences: what is being asked, what context was provided, what decision or input is needed from Chad
3. **Map to PRD** — check the PRD registry topic list; if a match exists, name the PRD. If no PRD matches, mark as `⚠️ No PRD — potential gap`
4. **Classify the ask type:**
   - `🔴 Blocked` — eng team explicitly says they cannot proceed without PM input
   - `🟡 Decision needed` — question requires a PM call (scope, priority, behavior)
   - `🟠 Clarification` — needs PM to confirm or explain existing PRD language
   - `🟢 FYI / no action` — informational, CC'd, no action required from Chad
5. **Age** — days since the mention was posted
6. **Conflict check** — does this reveal an assumption or design direction that contradicts another PRD or another team's work? Flag if yes.

---

## Phase 3 — Build the Triage Report

Output the triage report to the conversation. Each item gets a sequential number (**#N**) that can be used with `--addressed` to mark it resolved.

Format:

```
# SRA PM Triage — {DATE}
Lookback: {N} days | Channels scanned: {N} | Unanswered @mentions: {N}
Say "addressed 2" or "/sra-pm-triage --addressed 2" to mark any item resolved.

---

## 🔴 Blocked ({N})

### #N · [{CHANNEL}] {QUESTION SUMMARY} — {N} days old
🔗 **[Open thread in Slack]({permalink})**
**From:** {name} ({role if known})
**Context:** {2-3 sentence summary of the full thread — what they need from Chad and why}
**PRD:** {PRD name, or ⚠️ No PRD — potential gap}
**Conflict:** {Yes — {description} | None detected}
**Draft reply:** *(run `/sra-pm-triage --draft` to generate)*

---

## 🟡 Decision Needed ({N})
[same format]

## 🟠 Clarification ({N})
[same format]

## 🟢 FYI / No Action ({N})
[abbreviated — #N, channel, summary, 🔗 **[Open thread]({permalink})**, age]

---

## ⚠️ Potential PRD Gaps ({N})
Items that surfaced topics not covered by any current PRD:
- #N [{CHANNEL}] {summary} → 🔗 **[Open thread]({permalink})**

## ⚔️ Cross-Team Conflicts ({N})
Items where two teams are making divergent assumptions about the same behavior:
- {description of conflict} → 🔗 threads: **[link]({permalink1})** **[link]({permalink2})**
```

---

## Phase 3b — Handle `--addressed N` (fast path, no scan needed)

If the arguments contain `--addressed N` or the user says "addressed N" (where N is an item number from the last triage report):

1. Read the triage log
2. Find the matching Open row by number (match on summary text or thread link if number is ambiguous)
3. Move it from **Open** to **Resolved** — set Date Resolved to today, Resolution to "Marked addressed by Chad"
4. Write the updated log
5. Confirm: *"✅ Item #N marked resolved — moved to Resolved in the triage log."*
6. Do NOT run a full Slack scan. This is a one-step log update only.

If the user says "addressed 2, 3, 5" — process all listed numbers in one pass.

---

## Phase 4 — Update the Triage Log

Read the running log at:
```
/Users/chad.goldsmith/.aisuite/notebook/.agents/artifacts/pm-triage-log.md
```

For each item in the report:
- If it already exists in the log (match by thread permalink): update its status and last-seen date
- If it is new: append it to the **Open** section
- If it was previously open and is now answered (Chad replied): move it to **Resolved** with the resolution date

Write the updated log back using the Edit tool (targeted inserts/updates — never rewrite the whole file unless it's the first run and the file is empty).

Log format:
```markdown
# SRA PM Triage Log

## Open

| Date First Seen | Channel | Summary | PRD | Type | Age (days) | Thread |
|---|---|---|---|---|---|---|
| 2026-05-28 | NGS Engineering | Q about LLM confidence check contract | prd-262 | 🔴 Blocked | 3 | [link] |

## Resolved

| Date First Seen | Date Resolved | Channel | Summary | PRD | Resolution |
|---|---|---|---|---|---|
```

---

## Phase 5 — Draft Replies via Slack DM

For every item classified as 🔴 Blocked or 🟡 Decision Needed (and any 🟠 Clarification where a draft reply is possible), automatically send Chad a Slack DM for each item individually. Do NOT just present drafts in the conversation — send them as DMs so Chad can act from Slack directly.

**Send each DM to Chad's user ID: `U01G1CJ1LUW`**

Use `slack_send_message` for each item. Send them sequentially (not in parallel) to avoid rate limits.

**DM format per item:**

```
*#N · [{CHANNEL}] — {QUESTION SUMMARY}*
*Type:* 🔴 Blocked / 🟡 Decision Needed / 🟠 Clarification
*From:* {name}, {age} days old
*PRD:* {PRD name or ⚠️ No PRD}
🔗 <{permalink}|Open thread in Slack>

*Context:*
{2-3 sentence summary of what's being asked and why it needs PM input}

*Suggested reply:*
{Draft reply written in Chad's voice — direct, uses PRD language where relevant, flags if a PRD update is implied}

_Reply "addressed {N}" in your next Claude Code session to mark this resolved, or go reply directly in the thread above._
```

After sending all DMs, confirm in the conversation: *"Sent {N} DMs to you in Slack — one per item. Reply in the thread directly or say 'addressed N' here to close them out."*

If `--draft` is NOT set and the user hasn't asked for drafts, still send DMs but omit the "Suggested reply" block — just context + thread link.

**If a draft implies a PRD update:** Note it at the end of the DM: `⚠️ _This answer may require updating {PRD name} — say "update prd" in Claude Code to apply._`

---

## Phase 6 — PRD Update Recommendations

After presenting all triage items, synthesize any PRD updates implied by the questions:

```
## 📝 Suggested PRD Updates

Based on today's triage, the following PRD changes may be warranted:

- **prd-262:** [question from NGS about X] suggests the LLM confidence check section
  needs to define the data contract more explicitly. Suggested addition: [...]
- **prd-264:** [question from SOBA about Y] is not addressed in scope —
  consider adding it to Open Questions.
```

Do not make PRD edits automatically. Present the suggestions and ask: *"Want me to apply any of these?"*

---

## Invocation Modes

| Mode | Command | What it does |
|---|---|---|
| **Standard triage** | `/sra-pm-triage` | Full scan + report + log update |
| **Extended lookback** | `/sra-pm-triage --lookback 14` | Same but 14-day window |
| **Draft all replies** | `/sra-pm-triage --draft` | Triage + generate draft replies for all blocked/decision items |
| **Single channel** | `/sra-pm-triage --channel NGS` | Scan only the named channel |
| **Mark addressed** | `/sra-pm-triage --addressed N` or just `"addressed N"` | Mark item #N as resolved — moves it from Open to Resolved in the log with today's date. No Slack scan needed. |
| **Log view** | `/sra-pm-triage --log` | Show current triage log without scanning Slack |
| **Reply to item** | `/sra-pm-triage --reply [permalink]` | Draft and optionally send a reply to a specific thread |

---

## Daily Schedule Behavior

When invoked on schedule (not by the user directly):
1. Run the full triage scan
2. Build the report
3. Update the triage log
4. Send one header summary DM to Chad (`U01G1CJ1LUW`):

```
*SRA PM Triage — {DATE}*
{N} unanswered @mentions | 🔴 {N} blocked  🟡 {N} decisions  🟠 {N} clarifications  🟢 {N} FYI
⚠️ {N} PRD gaps  ⚔️ {N} conflicts
Individual DMs follow for each item below 👇
```

5. Then send individual per-item DMs (Phase 5 format) for every 🔴 and 🟡 item — each with context, suggested reply, and thread link so Chad can act entirely from Slack.
6. Send 🟠 items as DMs without the suggested reply (context + thread link only).
7. Skip 🟢 FYI items — they don't need DMs.
8. **Re-DM on every daily run for any item that remains Open in the triage log** — regardless of whether it was already DM'd before. Continue re-sending until one of these is true:
   - Chad has replied in the thread (detected during Phase 1 thread read — his user ID `U01G1CJ1LUW` appears after the original mention)
   - The item has been marked resolved via `--addressed N`
   - Add a *"(reminder — N days old, still open)"* note to the re-DM header so Chad knows it's a follow-up, not a new item.
