# Saving and Delivery

How to save the PRD markdown file, and how to optionally publish to Slack Canvas or Google Doc on user request.

## First-time creation

### Step 1: Save the markdown file

* **Always save the markdown file first**, before any other output. Use the Write tool to save to `.agents/artifacts/prds/`.
* **File naming convention:** `prd-{release}-{slug}.md` — always.
  * `{release}` = the release number confirmed in Phase 1 (e.g., `262`, `264`)
  * `{slug}` = short kebab-case description of the feature (e.g., `url-display-clickability-guidance-plans`, `mandatory-steps-enforcement`)
  * Examples: `prd-262-url-display-clickability-guidance-plans.md`, `prd-264-service-replies-voice.md`
  * Never use `sra-` prefix. Never omit the release number.
* Also copy the file to the `sra-prds` git repo at `/tmp/sra-prds/` (if checked out) and commit + push. If the repo is not checked out, note the file path so the user can push manually.

### Step 2: Prompt for additional outputs

After saving the markdown file, **always ask** which additional outputs the user wants before creating them. Send exactly this message:

> *Markdown saved at `.agents/artifacts/prds/prd-{release}-{slug}.md`. Would you like me to also create:*
> *- [ ] **Slack Canvas** — for team collaboration and comment tracking*
> *- [ ] **Google Doc** — for UX/CX stakeholders or external sharing*
> *- [ ] **Both**
> *- [ ] **Neither** — markdown only for now*
>
> *Also: want me to generate the **GUS epic description** for this PRD? (creates a .md file in the `sra-epics` repo in the format used to populate a GUS epic description)*

Wait for the user's reply. **Do not auto-create a canvas, Google Doc, or GUS epic without being asked.** If the user selected a canvas or Google Doc output when they invoked the skill, skip that part of this prompt and create it immediately after saving the markdown. The GUS epic question is always asked, regardless of what the user specified upfront — it's a separate workflow that requires explicit opt-in every time.

### Step 3: After outputs are created, summarize

* **Format mode** — call out explicitly whether this is a one-pager or full PRD, and (for one-pagers) remind the user they can expand to full PRD via the [expansion guide](../collaboration/expansion.md) when they're ready for scrum team handoff
* **Lifecycle stage** — "Markdown-only — no canvas yet. I'll keep changes as clean rewrites until you ask me to create the canvas." (or confirm canvas/doc created if applicable)
* What's ready ✅ (sections fully written from the feature input and Slack evidence)
* What still needs input ✍️ (sections with placeholders — business case field signal, Figma links, engineering leads, rollout targets, etc.)
* Provide the file path and any canvas/doc links created
* Offer to help draft any placeholder sections

### Multi-agent review offer

After summarizing, always offer a multi-agent review:

> *"Want me to run a multi-perspective review on this PRD? I can get simultaneous takes from:*
> *- 🔧 **Engineering** — technical feasibility and data model concerns*
> *- 🎨 **UX** — usability, rep workflow, and accessibility gaps*
> *- 🔍 **Critical Thinker** — assumptions, risks, and blind spots*
> *- ❓ **Socratic Questioner** — clarifying questions to sharpen the thinking*
> *Say "review" (all four), or name the specific perspectives you want."*

When the user says yes, dispatch the requested reviewers as parallel sub-agents (use the `Agent` tool with relevant personas) and synthesize their feedback into a consolidated review report before presenting it. Each reviewer should read the saved PRD file and return: top 3 findings, 1 biggest risk, and 1 recommended change.

**All subsequent changes — see [Updating PRDs](updating-prds.md).**

While the PRD is still markdown-only, subsequent changes are **clean rewrites via the Write tool**. No strikethroughs, no change markers — the markdown stays clean and easy to read during early drafting. Once a Slack canvas has been created, the skill switches to incremental updates to preserve comments and edit history. **Expansion from one-pager to full PRD** follows the same stage-aware rule — see [expansion guide](../collaboration/expansion.md).

---

## Canvas Creation (On Request Only)

**Only invoke `slack_create_canvas` when the user explicitly asks.** Trigger phrases: *"create the canvas"*, *"publish to Slack"*, *"put this in a canvas"*, *"make the Slack canvas"*, *"canvas it"*, or any other direct instruction to publish the PRD as a Slack canvas.

**Never auto-create a canvas** — not during initial save, not after incremental edits, not after comment review. The user decides when the PRD is ready for collaboration.

### Before creating the canvas

1. **Confirm the current markdown is the version to publish.** Ask: *"Ready to create the canvas from the current markdown at `<path>`? I'll publish the file as-is, so any in-flight changes should land first."*
2. Wait for confirmation.

### When creating the canvas

1. Use `slack_create_canvas` with the full markdown content. **Always create it as a personal canvas — do not pass a `channel_id`.** The user prefers to own the canvas in their personal space and then share it manually with the right audience (team channel, specific reviewers, DM, etc.). Never auto-post a PRD canvas to a channel. This applies to both one-pagers and full PRDs.
   * **Canvas title format:** `{release} [Human Assisted Service] Service Rep Assistant PRD - {Feature Name}` — e.g., `264 [Human Assisted Service] Service Rep Assistant PRD - Step Level Feedback`. Same convention as Google Docs for consistency across surfaces.
2. Capture the returned `canvas_id`
3. **Immediately strip the Slack AI disclaimer.** Slack automatically prepends the following line to every canvas created via API — remove it right away using `slack_update_canvas` with a replace operation targeting that exact text:
   > *This canvas was generated using AI, which can produce inaccurate or harmful responses. Review for accuracy and safety before using.*

   Use `slack_update_canvas` with `action=replace` to remove this line. The canvas content should start with the PRD title (`# PRD ...`), not the disclaimer.
4. **Append the canvas ID and title to the [PRD Canvas Registry](../reference/prd-canvas-registry.md).** This is how future invocations learn that the PRD has transitioned to the post-canvas stage.
5. Report the canvas link to the user and note that it is a personal canvas — they can share it from Slack when ready.

### After creation — lifecycle transition

* All further changes to this PRD now follow the **post-canvas incremental updates** path in [Updating PRDs](updating-prds.md)
* The markdown file and canvas stay in sync (see "Keeping Markdown and Canvas in Sync" in that guide)
* Comments on the canvas can now be reviewed and acted on via [comment review](../collaboration/comment-review.md)
* Tell the user: *"Canvas created. From now on, changes to this PRD will be tracked incrementally (strikethroughs + `*Added*` markers) in both the markdown and canvas to preserve comments."*

---

## Google Doc Creation (On Request Only)

**Only create a Google Doc when the user explicitly asks.** Trigger phrases: *"create a Google Doc"*, *"export to Docs"*, *"put this in a Doc"*, *"share as a Doc"*.

### When to use Google Docs over Canvas

- UX/CX stakeholders who prefer Google Docs for commenting and collaboration
- When the PRD needs to be shared outside of Slack (external partners, cross-org stakeholders)
- When the user prefers Docs for their personal workflow

### Shared PRD Google Drive folder

All PRD Google Docs must be created inside this shared folder:
> `https://drive.google.com/drive/folders/1iugu24A3_xt6o-l6ofxo2TqkuZfZdeQI`
> Folder ID: `1iugu24A3_xt6o-l6ofxo2TqkuZfZdeQI`

Always pass this folder ID when calling `docs_create` so the Doc lands in the shared folder, not the user's personal Drive root. This ensures the other PMs on the team have access.

### When creating the Google Doc

1. Confirm the markdown file is the version to publish (same as canvas flow)
2. Call `docs_create` with the PRD content and `folder_id: "1iugu24A3_xt6o-l6ofxo2TqkuZfZdeQI"` so it lands in the shared PRD folder
3. Name the Doc using the format: `{release} [Human Assisted Service] Service Rep Assistant PRD - {Feature Name}` — e.g., `264 [Human Assisted Service] Service Rep Assistant PRD - Step Level Feedback`. Derive the feature name from the filename slug in title case.
4. **Add cross-references** — after creating the Doc, update all three artifacts:
   - **Google Doc:** Add a metadata block at the very top (before the H1 title):
     ```
     **Source file:** `prd-{release}-{slug}.md`
     **Slack Canvas:** https://salesforce.slack.com/canvas/{canvas-id} (if exists)
     ---
     ```
   - **Markdown file:** Add/update a metadata block at the very top (before the H1 title):
     ```
     **Google Doc:** https://docs.google.com/document/d/{doc-id}/edit
     **Slack Canvas:** https://salesforce.slack.com/canvas/{canvas-id} (if exists)
     ---
     ```
   - **Slack Canvas** (if exists): Prepend a metadata line at the top of the canvas:
     ```
     📄 Source: `prd-{release}-{slug}.md` | 🔗 Google Doc: https://docs.google.com/document/d/{doc-id}/edit
     ```
5. Report the Doc link to the user
6. Note: Google Docs do NOT trigger the post-canvas lifecycle transition. The markdown file remains the source of truth.

**Google Docs are published snapshots — never programmatically updated.**

Once created, a Google Doc is a frozen snapshot. The `.md` file remains the living source of truth for all ongoing changes. There is no re-export workflow — the Doc is created once and left alone.

**Why:** There is no `docs_edit` tool to surgically update a Doc while preserving inline comment threads. A full re-export destroys all comments. Instead, changes to the Doc are queued as manual recommendations (see below).

**Google Doc does NOT replace Canvas:** Canvas is updated incrementally via `slack_update_canvas` and preserves comment threads inline. Google Docs are a one-time publish for UX/CX stakeholders who prefer that format. Both can coexist — Canvas for engineering collaboration, Google Doc for UX/CX/Leads review.

**How Doc feedback flows back:**
1. User says "check doc comments" → skill reads via `docs_comments`
2. Comments are appended to the `.md` under `## Discussion (from Google Doc comments)` with analysis
3. Accepted changes are applied to the `.md` using normal lifecycle rules
4. A corresponding entry is added to `## Recommended Changes for Google Doc` — a table of manual changes for the user to apply in the Doc
5. User applies them manually when convenient (strikethroughs, insertions, etc.)
6. User resolves the comment threads in the Doc after applying

See [comment-review → Google Doc Comment Review](../collaboration/comment-review.md#google-doc-comment-review---from-doc) for the full flow.

**Directing stakeholders to the right surface:**
- **Engineers** who want to comment on the source file → git.soma PR on the `sra-prds` repo (draft PR, inline comments, same as code review)
- **UX, CX, Leads** → Google Doc (comment directly; comments reviewed via `--from-doc`)
- **Eng leads, PM, Architect** → Slack Canvas (comment inline; comments reviewed via comment-review guide)
- **Do not send non-engineers to the .md file** — they have no way to comment on it inline
