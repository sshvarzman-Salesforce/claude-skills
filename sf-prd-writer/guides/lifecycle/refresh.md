# PRD Refresh (Research-Backed Staleness Review)

Run this guide when the user says something like *"refresh this PRD"*, *"is this PRD current?"*, *"review the grounding on this PRD"*, *"what's changed since this was written?"*, or *"check if this PRD is still accurate"*.

**What this does:** Re-runs targeted research against the PRD's topic using the latest Slack discussions and Google Drive call notes, then compares findings to the existing PRD content. It produces a structured **Refresh Report** — a diff of suggested updates — rather than silently rewriting anything. The user decides what to act on.

**This is not a rewrite.** No changes land in the PRD until the user approves them. The refresh surfaces what's new; [updating-prds](updating-prds.md) applies the changes.

---

## Step 1: Read the current PRD

Read the target PRD file in full. Extract:
- **Feature topic and scope** — what problem does it solve, what channels/objects does it touch
- **Named customers** — every customer mentioned in Customer Signal or References
- **Key claims** — specific facts, dates, metrics, open questions, and decisions that could have changed
- **Written date / last modified** — to scope the "what's new since then" research window
- **Open Questions** — questions marked Open that may now have answers

---

## Step 2: Re-run research in parallel

Run all of the following simultaneously:

**Slack searches (use `slack_search_public_and_private`):**
- Feature keywords + customer names from the PRD — look for new discussions, decisions, or engineering updates since the PRD was written
- Any open questions from the PRD — search to see if they've been answered in Slack
- Named customers + "SRA" — look for new feedback, escalations, or changed requirements
- Check `service-assistant-capabilities-*` channel matching the feature area for recent activity
- Check FDE (`C0AN1E181M3`) and SE (`C08E300HPUK`) for new field signal on the feature

**Slack Canvas comments (MANDATORY — always run this):**
- Look up the PRD's canvas ID in the [PRD Canvas Registry](../reference/prd-canvas-registry.md) or the `**Canvas:**` link at the top of the .md file
- If a canvas ID exists: call `slack_read_canvas` with that canvas ID to get the full current canvas content — the canvas may be ahead of the .md file
- Compare canvas content against the .md file: any sections in the canvas that differ from the .md are candidates for 🟡 (Potentially Stale) or 🔴 (Outdated) items

**Google Doc comments (MANDATORY — always run this):**
- Look up the PRD's Google Doc ID from the `**Google Doc:**` link at the top of the .md file
- Call `docs_comments` with that document ID to retrieve all open comment threads
- Each open, unresolved comment thread is a candidate for 🆕 (New Signal) or ❓ (Open Questions) items in the Refresh Report

**Google Drive — Customer & Enablement Call Notes folder (`1S6jSrpPEGv0e5HLmPwlLX3fAVaJL4Z8J`):**
- Search for the feature topic and named customers
- Search for any call notes dated *after* the PRD's written date
- Pull full content of any relevant recent call notes docs with `docs_get`

**Google Drive — Previous PRD Documents and PM Decks:**
- Check if any official PRDs or roadmap decks have been published for this feature since the markdown was written — may indicate the feature has progressed or been re-scoped

**Portfolio cross-reference:**
- Re-read sibling PRDs in `.agents/artifacts/prds/` that were listed in the Portfolio Cross-Reference section — check if their scope, release, or status has changed in ways that affect this PRD

---

## Step 3: Produce the Refresh Report

Present findings as a structured report — do not apply any changes yet. Format:

```
## PRD Refresh Report: [PRD Title]
Refreshed: [today's date]
PRD last written: [date from file or inferred]
Research window: [date range searched]

### 🟢 Still Accurate
[List of key claims that research confirms are still correct — e.g., "ADP pilot framing confirmed in May 12 call notes", "Scope aligns with current engineering direction per NGS channel"]

### 🟡 Potentially Stale — Review Recommended
[List of sections/claims where new evidence exists but doesn't clearly contradict — e.g., "Open Question #2 may have been answered — see Slack thread from Alex (Eng) on May 14", "Beta timeline mentioned as June — GA Blockers call notes (May 26) suggest this has shifted"]

For each item:
- **Section:** [Which section/line]
- **Current text:** [What the PRD says now]
- **New evidence:** [What was found, with source/link]
- **Suggested action:** [e.g., "Update beta date", "Close open question", "Add new customer signal"]

### 🔴 Outdated — Update Recommended
[List of claims that new evidence clearly contradicts or supersedes]

For each item:
- **Section:** [Which section/line]
- **Current text:** [What the PRD says now]
- **New evidence:** [What was found, with source/link]
- **Suggested change:** [Specific replacement text]

### 🆕 New Signal — Not Yet in PRD
[Customer asks, engineering decisions, or field evidence found in research that isn't in the PRD at all but should be]

For each item:
- **Source:** [Call notes doc title / Slack channel / date]
- **Signal:** [What was found]
- **Where it belongs:** [Which section to add it to]
- **Suggested text:** [Draft of the addition]

### ❓ Open Questions — Now Answered
[Any questions marked Open in the PRD that research found answers for]

For each item:
- **Question:** [Original question text]
- **Answer found:** [What research found]
- **Source:** [Link/channel/doc]
```

---

## Step 4: Offer to apply changes

After presenting the report, ask:

> *Found [N] items worth updating. Want me to apply all of them, pick specific ones, or just note them for now?*

- **"Apply all"** → Execute clean rewrite (if pre-canvas) or incremental updates (if post-canvas) per [updating-prds](updating-prds.md) for all Stale + Outdated + New Signal items
- **"Apply [numbers]"** → Apply only the selected items
- **"Note them"** → Save the Refresh Report as a dated note appended to the PRD file but make no changes to the PRD content itself

---

## Routing trigger phrases

| Signal | Route to |
|---|---|
| "refresh this PRD" / "is this current?" / "what's changed?" / "review the grounding" / "check if this is still accurate" / "update from latest calls" | This guide |
