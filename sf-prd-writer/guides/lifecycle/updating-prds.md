# Updating an Existing PRD

How the skill handles changes depends on the **lifecycle stage** of the PRD. Always sync the remote repo first, then determine the stage.

## Stage Transitions

To advance a PRD to the next stage, update the `stage:` value in the frontmatter at the top of the file:

| Stage | Meaning | Typical trigger |
|---|---|---|
| `draft` | PM-only, not yet shared | Initial creation |
| `in-review` | Canvas or Google Doc created, collecting feedback | User says "create the canvas" or "share with the team" |
| `released-to-eng` | Formally handed to scrum team | Sprint planning, Khoa/Eng lead alignment |
| `shipped` | GA — feature is live | Release confirmation |

**When the user advances a stage:**
1. Update `stage:` in the frontmatter
2. Add a Document History row noting the stage change and who triggered it
3. Regenerate the README manifest (see below)

**Automatic stage transitions the skill should apply proactively:**
- Canvas created → advance `draft` → `in-review`
- User says "release this to eng" / "hand off to scrum" → advance → `released-to-eng`

---

## Updating the README Manifest

The `README.md` at the repo root is the portfolio index. Regenerate it after any of these events:
- A new PRD is created
- A PRD's `stage:` changes
- A PRD is renamed or deleted

**Regeneration script** — run via Bash:

```python
python3 << 'SCRIPT'
import os, re, yaml

repo = "/tmp/sra-prds"
stage_order = ["draft", "in-review", "released-to-eng", "shipped"]
stage_labels = {
    "draft":           "🟡 Draft",
    "in-review":       "🔵 In Review",
    "released-to-eng": "🟢 Released to Eng",
    "shipped":         "✅ Shipped",
}
stage_desc = {
    "draft":           "PM-only — not yet shared for review",
    "in-review":       "Canvas or Google Doc created — collecting feedback",
    "released-to-eng": "Formally handed to scrum team for planning/execution",
    "shipped":         "GA — feature is live",
}

def parse_frontmatter(content):
    """Parse YAML frontmatter from PRD file. Returns dict with defaults."""
    defaults = {"stage": "draft", "release": "?", "feature": "", "team": "", "personas": [], "epic": None, "hld": None}
    fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    if not fm_match:
        return defaults
    try:
        parsed = yaml.safe_load(fm_match.group(1))
        if isinstance(parsed, dict):
            defaults.update({k: v for k, v in parsed.items() if v is not None})
            return defaults
    except Exception:
        pass
    # Fallback: regex parse for stage and release
    stage_m = re.search(r"^stage:\s*(\S+)", fm_match.group(1), re.MULTILINE)
    release_m = re.search(r"^release:\s*(\S+)", fm_match.group(1), re.MULTILINE)
    if stage_m:
        defaults["stage"] = stage_m.group(1)
    if release_m:
        defaults["release"] = release_m.group(1)
    return defaults

prds = {}
for fname in sorted(os.listdir(repo)):
    if not fname.startswith("prd-") or not fname.endswith(".md"):
        continue
    path = os.path.join(repo, fname)
    with open(path) as f:
        content = f.read()
    fm = parse_frontmatter(content)
    stage = fm["stage"]
    release = str(fm["release"])
    # Fallback: extract release from filename if frontmatter has "?"
    if release == "?":
        release_match = re.match(r"prd-(\d+)-", fname)
        release = release_match.group(1) if release_match else "?"
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else fname
    title = re.sub(r"^(Requirements One Pager:\s*|PRD[:\s—-]+|Product Requirements Document[:\s]+)", "", title).strip()
    canvas_match = re.search(r"\*\*Canvas:\*\*\s*(https://\S+)", content)
    canvas = f"[Canvas]({canvas_match.group(1)})" if canvas_match else "—"
    doc_match = re.search(r"\*\*Google Doc:\*\*\s*(https://\S+)", content)
    doc = f"[Doc]({doc_match.group(1)})" if doc_match else "—"
    personas = ", ".join(fm.get("personas", [])) if fm.get("personas") else "—"
    prds.setdefault(stage, []).append({"fname": fname, "title": title, "release": release, "canvas": canvas, "doc": doc, "personas": personas})

lines = ["# SRA PRD Portfolio\n",
    "> Maintained automatically by the `sf-prd-writer` skill. Do not edit by hand — stage changes are made by updating the `stage:` frontmatter in each PRD file.\n",
    "", "## Stage Definitions\n",
    "| Stage | Meaning |", "|---|---|"]
for s in stage_order:
    lines.append(f"| {stage_labels[s]} | {stage_desc[s]} |")
lines += ["", "To advance a PRD: update `stage:` in the frontmatter. The skill updates this README automatically on every PRD edit.\n", "---\n"]
for s in stage_order:
    items = prds.get(s, [])
    lines.append(f"## {stage_labels[s]} ({len(items)})\n")
    if not items:
        lines.append("_None_\n")
        continue
    lines += ["| PRD | Release | Personas | Canvas | Doc |", "|---|---|---|---|---|"]
    for p in items:
        lines.append(f"| [{p['title']}]({p['fname']}) | {p['release']} | {p['personas']} | {p['canvas']} | {p['doc']} |")
    lines.append("")

with open(os.path.join(repo, "README.md"), "w") as f:
    f.write("\n".join(lines))
print("README updated.")
SCRIPT
```

Always commit the README change together with the PRD change in the same git commit.

---

## Step 0 — Sync Remote Before Editing

Before reading or editing any PRD, pull the latest version from the remote git repo. Collaborators (e.g. engineers, UX) may have pushed changes directly to origin since the last session — editing a stale local file will overwrite their work.

**Run this every time you enter this guide, regardless of edit type:**

```bash
cd /tmp/sra-prds && git pull origin master 2>&1
```

If the pull advances HEAD (new commits were fetched), copy the updated file to the notebook artifacts path before editing:

```bash
cp /tmp/sra-prds/<filename>.md /Users/chad.goldsmith/.aisuite/notebook/.agents/artifacts/prds/<filename>.md
```

**If the pull fails** (network issue, auth error): note the failure to the user and proceed with the local file — but warn that the edit may overwrite remote changes and they should review the diff before pushing.

**After any edit**, commit and push:

```bash
cd /tmp/sra-prds && git add <filename>.md && git commit -m "<message>\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>" && git push origin main
```

---

## Determine Lifecycle Stage

For the target PRD, check whether a Slack canvas has been created:

* **Canvas ID is in the [PRD Canvas Registry](../reference/prd-canvas-registry.md)** → Post-canvas stage → use **Incremental Updates** (below)
* **PRD is markdown-only in `.agents/artifacts/prds/`, no registry entry** → Pre-canvas stage → use **Clean Rewrite** (below)
* **Unsure** → Ask the user: *"Has this PRD been published as a Slack canvas yet? If not, I'll do a clean rewrite of the markdown. Once you're ready to create the canvas, I'll switch to incremental updates."*

The two paths diverge sharply. Do not mix them.

---

## Markdown-Only (Pre-Canvas) — Clean Rewrites

While the PRD is still just a markdown file and no canvas exists, **every change is a clean rewrite of the file using the Write tool.**

### Rules for clean rewrites

* Use the **Write tool** to fully replace the file with the updated content
* **No strikethroughs.** No `*Added DATE:*` markers. No `> **Updated DATE · SOURCE:**` blockquotes. No change annotations of any kind.
* **Consolidate prior edits.** If the file still carries leftover strikethroughs or change markers from a pre-transition state, use this opportunity to clean them up — keep only the final, current content.
* Preserve everything the user still wants: all requirements, ACs, personas, decisions, portfolio cross-reference, appendix items, etc. The rewrite is a reformatting of the *same* PRD, not a blank-slate draft.
* Re-run the over-solutioning review (see [full-prd guide](../drafting/full-prd.md#review-for-over-solutioning-run-after-drafting)) after the rewrite.

### Why clean rewrites in this stage

* No one else is commenting yet — there is no collaboration history to preserve
* Change markers create noise during early drafting and make the PRD harder to read
* Keeps the markdown easy to scan when the user is still iterating on the core shape
* The moment a canvas is created, the skill transitions to incremental updates and starts preserving every change

### Workflow

1. Read the current markdown file in full
2. Apply the user's requested changes mentally/in a diff
3. Write the file back in full, cleanly, with the updated content
4. Summarize what changed (in the reply to the user, not in the file) so they can verify

### Do NOT

* Do NOT invoke `slack_update_canvas` — there is no canvas
* Do NOT invoke `slack_create_canvas` — canvas creation is always user-initiated (see [saving-and-delivery](saving-and-delivery.md))
* Do NOT leave `*Added:*` or strikethrough markers behind — a clean rewrite means clean

---

## Post-Canvas — Incremental Updates

Once a canvas has been created, all changes to the PRD — whether the local markdown file or the Slack canvas — **must be incremental**. Never regenerate or overwrite the full document. This preserves comments, edit history, and collaborator changes.

### Determine Update Type

For each change, classify it as one of:

| Type | Definition | Inline Marker | Action |
|---|---|---|---|
| **Additive** | New information that doesn't contradict anything already in the PRD | `*Added DATE:*` italic prefix | Append to the appropriate section |
| **Conflicting** | New information that supersedes, corrects, or contradicts existing text | `~~strikethrough~~` old + `> **Updated DATE · SOURCE:**` blockquote replacement | Strikethrough the old text, add the new text in a blockquote immediately after |
| **Structural** | New section, new requirement block, or new table row | `*Added DATE — CONTEXT*` italic note under new header | Insert at the correct location within the existing structure |

**Every change gets a date and source.** The source is whoever/whatever prompted the change: a comment author name and role (`Alex (Eng)`), a user decision (`scope review`), Slack evidence (`EA beta feedback`), etc. This makes the PRD self-documenting — collaborators can understand what changed, when, and why without scrolling to the appendix.

### Markdown File Updates

When updating the local `.agents/artifacts/prds/*.md` file:

* **Read the file first** to understand current content and find the correct insertion point
* **Use the Edit tool** for targeted changes. Do not rewrite the entire file with the Write tool.
* **Never delete content.** Superseded content gets struck through, not removed. This preserves the decision trail.

**Additive changes** — append with an italic `*Added*` prefix:

```markdown
* Existing requirement bullet
* Existing requirement bullet
* *Added 2026-04-23:* New requirement for voice channel grounding
```

For additive paragraphs in a section body:

```markdown
Existing paragraph text stays untouched.

*Added 2026-04-23 · EA beta feedback:* New paragraph with additional context from the beta program.
```

**Conflicting changes** — strikethrough old text + blockquote replacement with bold attribution:

```markdown
~~The system supports up to 3 grounding sources per plan.~~
> **Updated 2026-04-23 · Alex (Eng):** The system supports up to 5 grounding sources per plan, following the token budget expansion in 262.
```

The blockquote makes replacements visually distinct — you can scan the entire doc and immediately spot every change. For conflicting bullet items:

```markdown
* ~~Beta target: May 2026~~
  > **Updated 2026-04-23 · schedule change:** Beta target: June 2026, shifted to accommodate voice channel testing.
```

**Structural additions** — insert at the correct position with a one-line italic context note:

```markdown
### 5. Summary Plan Grounding
*Added 2026-04-23 — addresses gap identified during 262 scope review*

* Requirement bullets here...
```

For new table rows, just add the row — no marker needed since the row content is self-evidently new.

### Slack Canvas Updates

When updating a Slack canvas:

* **Always use `slack_update_canvas`** with incremental operations (`action=append`, `action=prepend`). This preserves existing comments and edits.
* **Never recreate the canvas.** Do not use `slack_create_canvas` for a PRD that already has a canvas (check the [PRD Canvas Registry](../reference/prd-canvas-registry.md)).
* **Read the canvas first** with `slack_read_canvas` to find the correct `section_id` targets.

**Additive changes:**
* Use `action=append` on the section that should receive the new content
* Prefix new content with a bold marker: `**New (2026-04-23):** content here`
* For new bullets: `* **New (2026-04-23):** Voice channel grounding requirement`

**Conflicting changes:**
* Use `action=append` on the section containing the old text to add the replacement
* For the old text: use `action=replace` on the specific section to wrap it in strikethrough (`~old text~` in Slack markdown)
* Format the replacement as: `**Updated 2026-04-23 · Alex (Eng):** New text here`
* If the section is a bold-text header (section headers), **do not use `action=replace`** — it destroys child content underneath. Instead, append a strikethrough + replacement note after the section's children.

**Structural additions:**
* Append the new section/block content to the parent section
* Include an italic context line: `*Added 2026-04-23 — context*`

**Critical Canvas API limitations to respect:**
* **Bold-text headers are destructive to replace.** Replacing a bold-text section header (`**Header**`) destroys all child elements (bullets, paragraphs) underneath it. Never replace a header to fix a typo — instead append a correction note.
* **Sections cannot be deleted.** There is no delete-section operation. If content must be visually removed, replace it with a `---` horizontal rule or strikethrough it.
* **Never run parallel canvas updates.** Execute all `slack_update_canvas` calls sequentially. Parallel calls cause race conditions that duplicate or orphan content.
* **After each update, re-read the canvas** to confirm the change landed correctly before proceeding to the next update.

---

## Updating from Meeting Notes or Call Transcripts (`--from-notes`)

Use this workflow when the user provides a Gemini meeting note, call transcript, or any other meeting artifact and wants to incorporate decisions into an existing PRD.

### Step 1 — Read the source

Fetch the meeting note using `docs_get` (Google Drive file ID or URL) or read from a local path if provided. If the user just pastes text directly, use that.

Extract the following from the note:
- **Aligned decisions** — things explicitly marked as decided or "ALIGNED"
- **Scope changes** — in-scope or out-of-scope determinations
- **Architecture or design decisions** — confirmed technical or UX directions
- **Action items assigned to Chad** — especially "Update documentation", "Update pager", "Share updated doc"
- **Open items / pending validation** — things discussed but not resolved, or needing a follow-up meeting
- **Named participants** — for attribution in change markers

### Step 2 — Map to PRD sections

For each extracted item, identify which PRD section(s) it affects:
- New deployment status, timeline, owner → Scope or Customer References
- Format/UX decisions → UX Considerations
- Out-of-scope determinations → Out of Scope
- Open questions raised → Open Questions (add new row)
- Open questions closed → Open Questions (strike through, add resolution note)
- Success metric targets confirmed → Success Metrics

### Step 3 — Propose changes before applying

**Never apply meeting notes directly.** Always present a diff-style proposal first:

```
## Proposed PRD Updates — [Meeting Name, Date]

**Source:** [Meeting title, date, attendees]

### Change 1 — [Section name]
**Current:** [existing text]
**Proposed:** [new text or addition]

### Change 2 — [Section name]
...

⚠️ Candidate for unresolved item: [anything discussed but not clearly decided]
```

Wait for user approval. Ask: *"Apply all, or call out which to skip/adjust?"*

### Step 4 — Apply approved changes

Apply using the normal lifecycle rules:
- **Pre-canvas PRD** → clean rewrite via Write tool (no change markers in the body)
- **Post-canvas PRD** → incremental updates with `*(Added DATE)*` / strikethrough markers (see Post-Canvas section above)

**Regardless of lifecycle stage:** always add a new row to the **Document History** table at the bottom of the PRD documenting the meeting as the source.

### Step 5 — Update Document History

Add one row per meeting/source, even when multiple PRD sections changed:

```markdown
| 2026-05-27 | Chad Goldsmith | Connect on SRA = SR + Service Plans (Gemini notes) | WS2 Voice architecture confirmed; auto-translate scoped to beta; feedback mechanism gap added |
```

### Tips

- **Gemini notes have a Decisions section** — start there; it has the highest-confidence, explicitly aligned items
- **Transcript is the ground truth** — when the summary and transcript conflict, the transcript wins; read it to get the specific wording
- **"One other thing" pattern** — when the user says "there was one more thing from the call", search the transcript for items that were raised, acknowledged, then NOT listed in the Decisions section. These are often things that were discussed and implicitly deferred or called out of scope without a formal decision moment.
- **Action items for Chad = PRD updates** — if the meeting notes list "Chad: Update documentation" or "Chad: Update pager to state X", those are direct signals of what needs to change
- **Pending validations** → Open Questions, not Scope changes — if something was decided pending a follow-up meeting (e.g., "verify with Wenqing"), add it to Open Questions rather than treating it as a firm scope decision

### Keeping Markdown and Canvas in Sync

When both a markdown file and a Slack canvas exist for a PRD:

* Apply the same incremental change to both, markdown first (since it's faster to verify)
* **Marker parity:** Use the same date, source, and change context in both surfaces. The markdown uses blockquotes (`> **Updated...**`) and the canvas uses bold text (`**Updated...**`) — these are the closest visual equivalents across the two formats.
* If the canvas update encounters API limitations (e.g., can't strikethrough a header), note the discrepancy and flag it for the user to fix manually in the canvas UI
* The markdown file is the source of truth for version-controlled content; the canvas is the collaboration surface

### Google Docs Are NOT Synced

**Google Docs are published snapshots — never programmatically updated.** When a Google Doc exists for a PRD:

* Do NOT re-export or overwrite the Google Doc after changes. The Doc is frozen at publish time.
* Instead, append changes to the `## Recommended Changes for Google Doc` section at the bottom of the `.md` file — a table of manual instructions for the user to apply.
* The user applies Doc changes manually (strikethroughs, additions) and resolves comment threads at their convenience.
* Doc comments flow back to the `.md` via the `## Discussion (from Google Doc comments)` section — see [comment-review → Google Doc](../collaboration/comment-review.md#google-doc-comment-review---from-doc).

**Rationale:** No `docs_edit` tool exists to surgically update a Doc while preserving inline comments. A full re-export destroys all comment threads. The one-way-publish model keeps comments intact and gives the user control over what stakeholders see.

---

## PRD Bottom Sections (Post-Doc)

Once a Google Doc has been created for a PRD, the `.md` gains two persistent sections at the very bottom (below Document History, below Comment Review Log):

### `## Discussion (from Google Doc comments)`

A running log of Doc feedback with analysis. Each review session gets a dated subsection. The skill uses this as a thinking space — prior discussions inform future analysis, pattern-spotting, and unresolved-thread tracking.

### `## Recommended Changes for Google Doc`

A table of manual changes for the user to apply in the Doc. Each row specifies:
- Location in the Doc (section + context)
- What to change (exact text to strikethrough, add, or replace)
- Change type (Strikethrough + replace / Add / Delete)

Rows stay until the user clears them (moves to a "Cleared" subsection after applying). If the table exceeds 5 uncleared items, gently prompt the user to batch-apply.
