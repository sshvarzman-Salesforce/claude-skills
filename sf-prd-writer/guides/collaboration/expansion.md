# Expand One-Pager to Full PRD

Use this guide when the user has an existing one-pager and wants to promote it to a full PRD (usually because the feature is now ready for scrum team handoff).

## Lifecycle-aware expansion

* **Pre-canvas (markdown-only):** Expansion is a **clean rewrite** of the markdown file with the added full-PRD sections. No change markers, no strikethroughs. The file after expansion reads like a brand-new full PRD. This is consistent with the [pre-canvas update path](../lifecycle/updating-prds.md#markdown-only-pre-canvas--clean-rewrites) — while there is no canvas, there is no audit trail to preserve, and a clean file is easier to review.
* **Post-canvas:** Expansion is **incremental** — new sections get `*Added YYYY-MM-DD — expansion from one-pager*` markers, existing sections are deepened with `*Added:*` prefixes, and the top-of-file marker transitions via the strikethrough pattern. Comments, portfolio references, and collaborator edits are preserved. Canvas is expanded via `slack_update_canvas append` per the [post-canvas update rules](../lifecycle/updating-prds.md#post-canvas--incremental-updates).

Determine which mode applies using the [lifecycle-stage check](../lifecycle/updating-prds.md#determine-lifecycle-stage) before starting.

## Confirm the expansion

Before expanding, confirm with the user:
* *"Expanding the `[title]` one-pager to a full PRD. This will add the full-PRD sections (Scenarios, Current Journeys, HLD link, Architecture, full test plan, etc.) and deepen existing sections. Existing content, decisions, and comment log stay intact. Proceed?"*

Wait for confirmation before editing.

## Update the top-of-file marker

Replace the one-pager marker with a full-PRD marker, keeping the strikethrough-and-replace convention:

```markdown
# PRD — [Feature Title]

> ~~*One-pager — condensed Part 1 / Part 2 structure for early alignment. Expand to full PRD when ready to hand off to scrum teams.*~~
>
> **Expanded to full PRD YYYY-MM-DD — ready for scrum team handoff.**
```

Also update the `Status` row in the Administrative table: `Draft — one-pager` → `~~Draft — one-pager~~ **Draft — full PRD** (expanded YYYY-MM-DD)`.

## Add missing sections

Add the sections that the one-pager intentionally omits, in their canonical positions. Each new section header gets an italic context note: `*Added YYYY-MM-DD — expansion from one-pager*`.

Sections to add:
* Part 1: **Scenarios**, **Current User Journeys / Solutions**, **Approach**, **Internal Competitive Features** (if relevant), **Relevant Research Insights**
* Part 2: **Architectural Concept Document** (link TBD), **Comparable Features or Technologies**, **UX User Journeys or Flow Diagrams**, standalone **Questions to Refine the PRD**
* Appendix: **References, Additional Resources**

See [full-prd guide](../drafting/full-prd.md) for the full structure and section-by-section guidance.

## Deepen existing sections

For existing sections in the one-pager, append detail (don't rewrite):
* **Business Case** — add any additional customer quotes, EA/beta signals, or evidence since one-pager drafting
* **Requirements** — add sub-points (success metrics, telemetry expectations, rollout-gating constraints) to each numbered requirement
* **Acceptance Criteria** — expand to 15–20+ ACs with edge-case coverage
* **Risks & Edge Cases** — add architecture, security, and compliance risks
* **Test Plan** — expand bullets into a detailed test matrix with entry/exit criteria
* **NFRs** — expand each bullet to full paragraph with benchmarks and constraints
* **Rollout Strategy** — add entry/exit criteria, beta customer targets, success metrics

**Lifecycle-aware additions:**
* **Pre-canvas (markdown-only):** Deepened content is written cleanly inline — no `*Added:*` markers, no strikethroughs. The entire file reads as a unified full PRD after expansion. (Consistent with clean rewrites while no canvas exists.)
* **Post-canvas:** Additions use `*Added YYYY-MM-DD:*` prefix on appended bullets, or italic context note on new subsections. This preserves the audit trail for collaborators.

## Preserve the decision trail

Everything in the Appendix (Portfolio Cross-Reference, Key Evidence References, Key Decisions Made, Post GA Ideas, Comment Review Log) **stays intact** — do not edit, renumber, or reorder. New items get appended with the same `*Added YYYY-MM-DD:*` convention.

## Canvas expansion

If a Slack canvas exists for the one-pager:
* Use `slack_update_canvas` with `action=append` to add each new section
* Do not recreate the canvas — that destroys comments
* Update the top-of-canvas marker via the strikethrough pattern (append a replacement note; do not replace the header block, since that would destroy children underneath)

## Post-expansion summary

After expansion, present:
* What was added ✅ (new sections, deepened sections)
* What still needs input ✍️ (HLD link, architecture details, full test matrix entries, rollout success metrics, etc.)
* Remind the user this is now a full PRD and subsequent updates follow the [updating-prds rules](../lifecycle/updating-prds.md) (same as before)
