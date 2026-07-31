# Portfolio Cross-Reference

Before drafting, scan the user's existing PRDs for overlap, conflicts, shared dependencies, and synergy opportunities. This catches issues like two PRDs claiming different token budgets, conflicting rollout timelines, or features that could share a single admin config UI.

## Where to look

1. **Local PRD files:** Glob for `**/*.md` in `.agents/artifacts/prds/` and read each PRD found.
2. **PRD Canvas Registry** — see [PRD Canvas Registry](../reference/prd-canvas-registry.md). As you create canvases, the skill auto-appends them there.
3. **Ad-hoc Slack search** (fallback): If the user mentions a PRD not in the registry, search Slack for `"PRD" "Service Rep Assistant"` or `"PRD" "SRA"` to find it, then add it to the registry.

## What to check in each existing PRD

| Check | What to look for | Why it matters |
|---|---|---|
| **Dependency overlap** | Same dependencies listed (e.g., Service AI Grounding, Eligibility Flow, MIAW, SCV) | Shared dependencies = coordination needed for delivery |
| **Token budget conflicts** | Multiple PRDs adding data to the prompt Data section | Combined grounding data could exceed the ~1,895 token budget |
| **Scope overlap** | Features that touch the same admin config, same objects, or same channels | Potential for consolidation or sequencing |
| **Rollout conflicts** | Beta/GA timelines that depend on each other or compete for beta customer bandwidth | Beta customers (Meta, EA) can only validate so many features at once |
| **Shared NFRs** | Same edition/addon requirements, same performance constraints | Should be consistent across PRDs |
| **Synergy opportunities** | Features that are better together (e.g., related record grounding + voice plans) | Call out in the PRD that these features compound |
| **Contradictions** | Conflicting statements about architecture, behavior, or scope | Fix before publishing |

## Output

Add a **"Portfolio Cross-Reference"** section in the Appendix of the new PRD:

```markdown
## Portfolio Cross-Reference

| Existing PRD | Relationship | Details |
|---|---|---|
| [PRD Name] (release) | Shared Dependency | Both require [dependency]. Coordinate delivery. |
| [PRD Name] (release) | Token Budget Impact | Both add data to prompt Data section. Combined impact on ~1,895 token budget needs validation. |
| [PRD Name] (release) | Synergy | [Feature A] + [Feature B] compound value — [explain]. Consider joint demo/beta. |
| [PRD Name] (release) | Rollout Sequencing | [Feature A] should ship before [Feature B] because [reason]. |
```

If no existing PRDs are found, note that this is the first PRD in the portfolio and skip the section.

## One-pager note

For one-pagers, portfolio cross-reference still **runs** (it informs drafting and helps avoid accidental duplication), but the resulting section is **not published** in the one-pager itself. It lives in drafting notes only. See [one-pager guide](../drafting/one-pager.md).
