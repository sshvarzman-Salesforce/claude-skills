# Batch Mode (Multi-PRD Updates)

Use this guide when the user wants to make changes across multiple PRDs in a single session. Batch mode minimizes context usage by collecting all changes up front, then executing them efficiently without redundant reads.

## Collect the Change Set

When the user describes changes to multiple PRDs — either in one message or across a few — build a **change manifest** before executing anything:

```
## Batch Change Manifest

### PRD 1: [Title] ([canvas_id])
| # | Section | Change Type | Description |
|---|---------|-------------|-------------|
| 1 | Scope | Additive | Add voice channel as P0 |
| 2 | Requirements §3 | Conflicting | Change token limit from 1,895 to 2,400 |

### PRD 2: [Title] ([canvas_id])
| # | Section | Change Type | Description |
|---|---------|-------------|-------------|
| 1 | Business Case | Additive | Add EA beta feedback quote |

**Total: 3 changes across 2 PRDs**
```

Present the manifest to the user and **wait for confirmation** before executing. The user may reorder, drop, or modify items.

## Execute Efficiently

Once confirmed, execute changes with minimal context overhead:

1. **Group by PRD** — process all changes for one PRD before moving to the next
2. **Read each PRD once** — read the markdown file and canvas at the start of each PRD's change set, not before every individual change
3. **Markdown first, canvas second** — for each PRD, apply all markdown edits, then all canvas updates. This avoids interleaving read/write cycles across two surfaces.
4. **Sequential canvas updates** — within each PRD's canvas changes, execute one `slack_update_canvas` at a time (per [updating-prds rules](../lifecycle/updating-prds.md))
5. **Skip re-reads between changes to the same PRD** — only re-read the canvas if a previous update to that same canvas might have shifted section IDs (e.g., a structural addition)

## Batch Summary

After all changes are applied, present a single consolidated report:

```
## Batch Complete

### PRD 1: [Title]
- ✅ Change 1: Added voice channel to Scope (md + canvas)
- ✅ Change 2: Struck through old token limit, added 2,400 (md + canvas)

### PRD 2: [Title]
- ✅ Change 1: Appended EA feedback to Business Case (md + canvas)

**3/3 changes applied successfully.**
```

If any change fails (e.g., canvas API limitation), note it in the report and suggest the manual fix.

## Batch + Comments Combo

The user can combine comment review with batch updates:

```
/sf-prd-writer Check comments on all my 262 PRDs and batch the changes
```

This runs [comment review](comment-review.md) across all registry canvases for the specified release, builds a change manifest from the comment suggestions, presents it for approval, then executes via the batch flow above.

## Context Budget Awareness

Batch mode is designed for **light-to-medium changes** (2–5 changes per PRD, up to 3–4 PRDs per session). If the user's request would exceed this:

* **More than ~15 total changes** — warn the user that context may run tight and suggest splitting into two sessions, grouped by PRD priority
* **More than 5 PRDs** — suggest scanning/triaging in this session, then executing in follow-up sessions per PRD
* **Any new PRD creation in the batch** — always break that into its own session (the full PRD draft flow is too heavy to mix with batch updates)

When in doubt, err on the side of completing fewer changes cleanly rather than running out of context mid-batch.
