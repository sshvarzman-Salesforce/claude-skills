# GUS Epic Description Generator

Use this guide when the user asks to create a GUS epic for a PRD — either via the prompt in the [saving-and-delivery flow](../lifecycle/saving-and-delivery.md#step-2-prompt-for-additional-outputs), or directly ("create the epic", "generate the GUS epic", "write the epic description for the grounding PRD").

**What this produces:** A markdown file in the `sra-epics` git repo (`git@git.soma.salesforce.com:chad-goldsmith/sra-epics.git`, local clone at `/tmp/sra-epics/`) that contains a GUS epic description in the exact format used to populate the Description field of a GUS epic work item. It does NOT create the GUS item directly — it generates the content so the user can paste it in or share it.

**When to invoke:** On-demand only. Never auto-create during the saving-and-delivery flow unless the user says yes to the prompt.

---

## Identify the Source PRD and Confirm Epic Metadata

1. **If invoked from the saving-and-delivery prompt:** The source PRD is the one just created — no need to ask.
2. **If invoked directly:** Check whether the user named a specific PRD. If ambiguous, ask which PRD from the portfolio.
3. **Read the source PRD** from `.agents/artifacts/prds/prd-{release}-{slug}.md` — this is the only input needed. No additional Slack research required.
4. **Always ask for release and team** before generating — do not infer these from the PRD filename. Send exactly this message:

   > *Before I generate the epic, two quick questions:*
   > *1. **Release?** (e.g., 262, 264)*
   > *2. **Team tag?** (e.g., SF/SPA, NGS, SOX — the team label that goes in the epic name)*

   Wait for the user's reply. Do not proceed until both are confirmed.

---

## Derive Epic Metadata

From the PRD content, extract or infer the following GUS epic fields:

| GUS Field | How to derive |
|---|---|
| **Epic Name** | `[{Release}][{Team}] SRA - {Feature Name}` — max 80 chars. Use release and team confirmed above. Use the PRD title, condensed to title case. E.g., `[264][SF/SPA] SRA - Show/Hide Summary Plan for Message and Voice` |
| **Description** | See template below — fully generated from PRD content |
| **Owner** | From PRD Administrative table (Initiative Lead or Major Feature Lead) — default to `Chad Goldsmith` if not present |
| **Team** | `SRA` (Service Rep Assistant) — always |
| **Project** | Derive from release: `262` → `Summer '26`, `264` → `Winter '27`. Full project name: `Summer '26 (262)` |
| **Planned Release** | Same as project |
| **Priority** | Default `P2` unless PRD explicitly calls out P0 urgency (customer blocker, GA dependency) — then use `P1` |
| **PRD Link** | The Google Doc link from the PRD metadata line. If no Google Doc, use the Slack Canvas link. |
| **Success Criteria** | Pulled from the PRD's Success Metrics section — condensed to 2–3 bullet points |

---

## Generate the Epic Description

Use this template exactly. All sections use **bold headers** (no `#` headers — GUS description is plain text with bold formatting). Fill every section from the PRD; never leave a section blank. If a PRD section is thin, write a condensed version from what's available.

```markdown
**Feature Overview**

{2–3 sentences describing what this feature does and how it works at a high level. Pull from the PRD's "What Engineering Already Solved" or the opening problem statement. Focus on the end state — what is being built.}

**Benefits / Goals (The "Why")**

• {Benefit 1}

• {Benefit 2}

• {Benefit 3}

**Target Customer / Persona (The "Who")**

{1–2 sentences describing the primary persona(s). Pull from "Who Benefits" table. E.g., "Case reps using Adaptive Experience in Dynamic Plan mode. Admins configuring the Service Assistant for multi-channel deployments."}

**Customer Outcomes / High-Level Requirements**

• {Outcome 1}

• {Outcome 2}

• {Outcome 3}

**User Scenarios in Scope**

1. {Persona} — {scenario description}

2. {Persona} — {scenario description}

**Out of Scope**

• {Out of scope item 1}

• {Out of scope item 2}

**Acceptance Criteria**

AC 1: {Testable acceptance criterion}

AC 2: {Testable acceptance criterion}

AC 3: {Testable acceptance criterion}

AC 4: {Testable acceptance criterion}

**KPIs**

• {Metric 1}: {current} → {target}

• {Metric 2}: {current} → {target}

**Definition of Done**

• Feature is fully functional end-to-end in a scratch org

• All Acceptance Criteria verified by QE

• No P0/P1 bugs open at time of release

• PRD reviewed and approved by PM lead

• UX sign-off received (if applicable)

• Help documentation stub created or updated

• Feature is behind a feature flag / gater for controlled rollout

**Reference Links**

• [prd-{release}-{slug}.md](https://git.soma.salesforce.com/chad-goldsmith/sra-prds/blob/main/prd-{release}-{slug}.md)

• [Google Doc]({Google Doc URL from PRD metadata — use the full https://docs.google.com/... URL}) *(omit if no Google Doc exists)*

• [Canvas]({Slack Canvas URL from PRD metadata — use the full https://salesforce.enterprise.slack.com/... URL}) *(omit if no Canvas exists; do NOT write "TBD" for Canvas — just omit the line)*

• [Figma]({Figma URL from PRD if present}) *(omit if not present)*

• GUS Epic: TBD *(update after creating the GUS item)*
```

---

## Save the Epic File

1. **Clone check:** Verify `/tmp/sra-epics/` exists. If not, clone it:
   ```
   git clone git@git.soma.salesforce.com:chad-goldsmith/sra-epics.git /tmp/sra-epics
   ```
2. **File naming:** `epic-{release}-{slug}.md` — same slug as the source PRD. Example: `epic-262-show-hide-summary-plan-autorun.md`
3. **File location:** `/tmp/sra-epics/epic-{release}-{slug}.md`
4. **File structure:**

   ```markdown
   # GUS Epic Description: [{Release}][{Team}] SRA - {Feature Name}

   **Source PRD:** `prd-{release}-{slug}.md`
   **PRD Google Doc:** {URL or TBD}
   **PRD Canvas:** {URL or TBD}
   **Generated:** {today's date}

   ---

   {epic description content — all sections from template above}
   ```

5. **Commit and push:**
   ```
   cd /tmp/sra-epics && git add epic-{release}-{slug}.md && git commit -m "Add GUS epic description for {Feature Name}" && git push
   ```

---

## Deliver to User

After saving and pushing:

1. Show the generated **Epic Name** (the `[{Release}][{Team}] SRA - {Feature Name}` string — copy-paste ready for the GUS Name field)
2. Show the full epic description content inline so the user can review it before pasting into GUS
3. Provide the file path: `/tmp/sra-epics/epic-{release}-{slug}.md`
4. Remind the user:

   > *"To create the GUS work item: paste the Epic Name into the GUS Name field and the description content into the Description field. Once you've created it, share the GUS URL with me and I'll update the `• GUS Epic: TBD` line in the file with a live link."*

**Do NOT create a GUS work item automatically.** [GUS context research](../research/gus-context.md) handles GUS item lookup — that's separate and also user-initiated. This guide only generates the content file.

## Update GUS Epic Link (Follow-up)

When the user shares a GUS epic URL after creating the item:

1. Identify which epic file it maps to (from context or by asking)
2. Replace `• GUS Epic: TBD` with `• [GUS Epic]({GUS URL})`
3. Commit and push:
   ```
   cd /tmp/sra-epics && git add epic-{release}-{slug}.md && git commit -m "Link GUS epic for {Feature Name}" && git push origin main:master
   ```
4. Confirm the update to the user

---

## Usage Examples

```
/sf-prd-writer Create the GUS epic description for the Show/Hide Summary Plan PRD
```
→ Asks for release and team, then reads `prd-262-show-hide-summary-plan-autorun.md`, generates `epic-262-show-hide-summary-plan-autorun.md`, pushes to sra-epics repo

```
/sf-prd-writer Generate epic for the grounding PRD
```
→ Disambiguates which grounding PRD if multiple match, then generates epic

```
/sf-prd-writer [saving-and-delivery prompt response] Yes, create the epic too
```
→ Runs this guide immediately after PRD outputs are delivered
