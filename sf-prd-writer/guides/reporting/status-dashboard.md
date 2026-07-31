# PRD Status Dashboard

Use this guide when the user asks for a portfolio overview: "status", "what needs attention", "dashboard", "where are my PRDs at", or similar.

**Research depth: None.** This phase only reads existing local files and the registry — no Slack searches, no canvas reads (unless the user specifically asks for comment counts).

## Gather State

1. Read all markdown files in `.agents/artifacts/prds/`
2. For each PRD, extract:
   - **Title** (from H1)
   - **Format** (one-pager or full PRD — infer from structure)
   - **Release** (from Administrative table or inferred from filename/content)
   - **PRD stage** (from `stage:` frontmatter — `draft` / `in-review` / `released-to-eng` / `shipped`)
   - **Lifecycle stage** (markdown-only vs. post-canvas — check [PRD Canvas Registry](../reference/prd-canvas-registry.md))
   - **Last modified** (file modification date)
   - **Open questions count** (count rows in Open Questions table)
   - **Placeholder count** (count `TBD`, `[Link]`, `[NEEDS EVIDENCE]` markers)
   - **GUS Epic** (if present in Administrative table)

## Present Dashboard

```
## PRD Portfolio Status
Updated: [date]

| # | PRD | Format | Release | PRD Stage | Lifecycle | Last Modified | Open Qs | Gaps |
|---|-----|--------|---------|-----------|-----------|---------------|---------|------|
| 1 | [Title] | One-pager | 262 | 🟢 Released to Eng | 🔗 Canvas | May 19 | 3 | 2 TBDs |
| 2 | [Title] | One-pager | 264 | 🔵 In Review | 🔗 Canvas | May 15 | 1 | 0 |
| 3 | [Title] | Full | 264 | 🟡 Draft | 📄 Markdown | May 8 | 5 | 4 TBDs |

### Needs Attention
- ⚠️ [PRD Title]: 5 open questions, 4 gaps — consider scheduling alignment
- ⚠️ [PRD Title]: Not modified in 14+ days — stale?
- 🔗 [PRD Title]: Canvas exists but 3 unresolved open questions — check comments?

### Cross-PRD Alerts
- 🔀 [PRD A] and [PRD B] both add grounding data — combined token budget impact unvalidated
- 📅 [PRD A] depends on [PRD B] shipping first — confirm sequencing with Eng
```

## Actionable Suggestions

After the dashboard, suggest 1–3 concrete next actions:
- "Want me to check comments on [PRD with canvas]?"
- "The [stale PRD] hasn't been touched in 2 weeks — want to update or archive it?"
- "[PRD] has 5 open questions — want to discuss any of them now?"
