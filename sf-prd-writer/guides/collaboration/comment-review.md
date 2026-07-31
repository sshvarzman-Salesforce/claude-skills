# Comment Review & Response

This guide handles comment monitoring, triage, and action for both **Slack Canvas** and **Google Doc** surfaces. Run it when the user asks to check comments, or when invoked with a comment-related prompt like "check PRD comments" or "what feedback is on the grounding PRD."

**Two comment surfaces — same triage loop, different APIs:**

| Surface | Who uses it | How to read comments | When to use this guide |
|---|---|---|---|
| **Slack Canvas** | Eng, PM, Leads | `slack_read_canvas` + `slack_search_public_and_private` | Any canvas comment review |
| **Google Doc** | UX, CX, Leads, non-Slack stakeholders | `docs_comments` with the Doc file ID | Any `--from-doc` invocation or when user says "check Doc comments" |

**Where to direct stakeholders who ask how to comment on a `.md` file:**
> *"The .md is the source file — for collaboration, use the [Canvas / Google Doc]. Engineers who prefer the source file can comment directly on a git.soma pull request (open a draft PR against the `sra-prds` repo — same as a code review). Everything flows back to the PRD regardless of surface."*

---

## Discover Comments

Canvas comments in Slack surface as **messages in the channel where the canvas was shared**, typically as threaded replies or as messages referencing the canvas. To find them:

1. **Search for canvas mentions and comment threads:**
   * `slack_search_public_and_private` with query: `"<canvas_title>" is:thread` — finds threaded discussions about the canvas
   * `slack_search_public_and_private` with query: `"<canvas_id>"` — finds direct references to the canvas
   * `slack_search_public_and_private` with query: `"PRD" "<feature_keywords>" has:comment` or `"PRD" "<feature_keywords>" is:thread` — broader search for discussion threads

2. **Read the canvas itself** with `slack_read_canvas` — inline comments appear as annotations in the canvas content (look for comment indicators in section content)

3. **Check known channels** where the canvas was shared — use `slack_read_channel` on likely channels to find recent messages that reference or discuss the PRD

4. **Resolve commenter identities** — use `slack_read_user_profile` to get the name and role of each commenter, so you can present feedback with proper attribution

## Present Comments to User

Present each comment in a structured format for the user to triage:

```
## PRD Comments: [PRD Title] ([canvas_id])
Checked: [date]

### Comment 1
**From:** [Name] ([Role/Team]) — [timestamp]
**On section:** [Section name or quote of commented text]
**Comment:** [Full comment text]
**Thread replies:** [Any follow-up discussion]
**Suggested action:** [Additive / Conflicting change / Question / No PRD change needed]

---

### Comment 2
...
```

For each comment, assess and suggest one of:
* **Accept → Additive change** — The comment requests new info that doesn't conflict. Suggest what to append and where.
* **Accept → Conflicting change** — The comment corrects or supersedes existing text. Suggest what to strikethrough and what to replace it with.
* **Needs discussion** — The comment raises a question or debate that isn't resolved yet. Flag it but don't change the PRD.
* **Acknowledge only** — The comment is a "+1", "looks good", or informational. No PRD change needed, but you can reply to acknowledge.
* **Reject** — The comment conflicts with a deliberate product decision. Explain why and suggest a reply.

## Act on User Decisions

After presenting comments, **wait for the user to decide** on each one. The user may:

* **"Accept comment 1"** or **"take that feedback"** → Apply the change using [post-canvas incremental update rules](../lifecycle/updating-prds.md) (additive = append, conflicting = strikethrough + replace). Then reply to the comment thread in Slack confirming the change was made.
* **"Reply to comment 2 with [message]"** → Send the reply via `slack_send_message` to the comment thread (using `thread_ts`). Do not change the PRD.
* **"Reject comment 3 because [reason]"** → Reply to the comment thread explaining the decision. Do not change the PRD.
* **"Accept all"** → Apply all suggested changes sequentially using incremental update rules, then reply to each thread confirming.
* **"Skip"** or **"ignore"** → Do nothing for that comment.

## Reply Format for Comment Threads

When replying to a comment thread in Slack on behalf of the user:

* Always reply **in-thread** (use `thread_ts`) — never broadcast to channel
* Use a clear format that attributes the update:
  ```
  ✅ Updated — [brief description of what changed in the PRD]
  ```
  or for rejections:
  ```
  Noted — keeping the current text because [reason]. Happy to discuss further.
  ```
  or for questions:
  ```
  Good question — [response]. [Will update the PRD once we align / Added to Open Questions section]
  ```

## Google Doc Comment Review (`--from-doc`)

Run this section when the user asks to check Google Doc comments, or passes `--from-doc`.

### Step 1 — Fetch Doc comments

Use `docs_comments` with the Doc file ID from the [PRD Canvas Registry](../reference/prd-canvas-registry.md) or from the metadata block at the top of the markdown file.

```
docs_comments(file_id="<doc_id>")
```

Returns a list of comments with: author, timestamp, quoted text (the text the comment is anchored to), comment body, and resolved/open status. Fetch open comments only — skip resolved ones unless the user asks for the full history.

### Step 2 — Present Doc comments

Use the same format as Canvas comments above, but note the surface:

```
## PRD Comments: [PRD Title] — Google Doc
Checked: [date]

### Comment 1
**From:** [Name] ([Role/Team]) — [timestamp]
**On text:** "[quoted text the comment is anchored to]"
**Comment:** [Full comment text]
**Suggested action:** [Additive / Conflicting change / Question / No PRD change needed]
```

### Step 3 — Act on decisions

Same triage loop as canvas comments — wait for user to accept/reject/reply on each one. But the downstream action is different:

**Replying to Google Doc comments:** Note the reply for the user to send manually. Flag it: *"Reply this in the Doc: [text]"*. There is no programmatic reply API.

### Step 4 — Append to Discussion section in markdown

After triage, append accepted/discussed comments to the `## Discussion (from Google Doc comments)` section at the bottom of the `.md` file. This section is a running log of Doc feedback with your analysis:

```markdown
## Discussion (from Google Doc comments)

### 2026-06-22 — Comment review

**Alex (Eng)** on "5 grounding sources":
> "Do we have token budget for 5? The 262 expansion was 3."

**My take:** Valid concern. The 262 scope was 3, and extending to 5 needs a
token budget analysis. Recommend adding an Open Question.

**Sarah (UX)** on "Summary Plan visibility":
> "Can we default to collapsed for voice?"

**My take:** Aligns with voice channel density concerns. Recommend adding
as a UX Consideration requirement.
```

This section serves as a persistent thinking space — the skill can reference prior discussions when new comments arrive, spot patterns, and track unresolved threads across review sessions.

### Step 5 — Apply accepted changes to the markdown

Apply the accepted changes to the main body of the `.md` using the normal lifecycle rules:
- **Pre-canvas** → clean rewrite via Write tool
- **Post-canvas** → incremental updates with strikethrough + `*Added DATE*` markers

### Step 6 — Queue manual Doc changes

For every change applied to the `.md`, append a corresponding entry to the `## Recommended Changes for Google Doc` section at the bottom of the `.md`:

```markdown
## Recommended Changes for Google Doc

*Apply these manually when convenient. Each maps to a change already in the .md above.*

| # | Location in Doc | Change | Type |
|---|---|---|---|
| 1 | Section 5, bullet 2 | ~~3 grounding sources~~ → 5 grounding sources | Strikethrough + replace |
| 2 | Open Questions table | Add row: "Token budget for 5 sources — needs eng validation" | Add |
| 3 | UX Considerations | Add bullet: "Summary Plan defaults to collapsed on voice channel" | Add |

*Cleared:*
*(items you've applied get moved here by the user)*
```

**Important:** The Google Doc is never programmatically updated. These are instructions for the user to apply manually. The `.md` is the source of truth; the Doc is a published snapshot that the user maintains by hand.

### When to prompt the user to update the Doc

After populating the Recommended Changes table, tell the user:
> *"I've applied the changes to the .md and queued [N] manual changes for the Google Doc — see the 'Recommended Changes' section at the bottom. Apply them when convenient and resolve the comment threads in the Doc afterward."*

Do NOT nag on every comment review. If the Recommended Changes table has >5 uncleared items, gently note: *"You have [N] queued Doc changes — might be a good time to batch-apply them."*

---

## Comment Log

After processing comments from either surface, append a summary to the markdown PRD file under a new `### Comment Review Log` section in the Appendix:

```markdown
### Comment Review Log

| Date | Surface | Commenter | Section | Comment Summary | Action Taken |
|---|---|---|---|---|---|
| 2026-04-23 | Canvas | Jane (UX) | Scope | Requested voice channel be P0 | Accepted — moved from P1 to P0 |
| 2026-04-23 | Canvas | Alex (Eng) | Requirements §3 | Token budget concern | Added constraint note to §3 |
| 2026-04-23 | Google Doc | Pat (QE) | Test Plan | Asked about edge case coverage | Replied — no PRD change, added to Open Questions |
```

This log provides a decision trail of how stakeholder feedback shaped the PRD, regardless of which surface the comment came from.
