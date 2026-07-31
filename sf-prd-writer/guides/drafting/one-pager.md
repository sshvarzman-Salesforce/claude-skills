# One-Pager Draft (Requirements One-Pager Format)

The one-pager is a **minimum-viable requirements doc**. It aligns engineering / UX / Architect on the *problem, customer signal, gap, and scope* — nothing more. It is not a condensed full PRD. It is a different shape with fewer sections and much less prose.

**Canonical reference:** `F0B05DPJDED` — *Requirements One Pager: Action Output-Driven Knowledge Re-Grounding & Plan Branching in Dynamic Plans*. When in doubt, match that shape exactly.

**When to use:** early alignment before investing in a full PRD. One-pager first, full PRD later via [expansion](../collaboration/expansion.md) when scrum teams need the deeper document.

## Frontmatter

Every PRD file starts with a YAML frontmatter block — before any metadata links, before the H1 title:

```markdown
---
stage: draft
release: 264
feature: step-level-feedback
team: service-rep-assistant
personas: [service-rep, supervisor]
epic: null
hld: null
---
```

**Required fields:**
- `stage` — `draft` | `in-review` | `released-to-eng` | `shipped`. Update as the PRD advances.
- `release` — the release number (e.g., `264`)
- `feature` — kebab-case feature slug matching the filename (e.g., `step-level-feedback`)
- `team` — product team that owns this feature (e.g., `service-rep-assistant`)
- `personas` — YAML list of primary personas this feature serves (use kebab-case: `service-rep`, `supervisor`, `admin`)

**Optional fields (add when known):**
- `epic` — GUS epic W-number (e.g., `W-12345678`). Set to `null` until created.
- `hld` — link to HLD/architecture doc when one exists. Set to `null` if none yet.

The stage is updated in the frontmatter as the PRD advances — never in the body. After every stage change, regenerate the `README.md` manifest in the repo root (see [updating-prds](../lifecycle/updating-prds.md#updating-the-readme-manifest)).

---

## Structural rules

- **Title only** — single H1 at the top, format: `# Requirements One Pager: <Feature Title>`. No subtitle, no italic marker line, no `PRD One-Pager —` prefix.
- **PDLC context note** (immediately after title, before horizontal rule) — Add a brief note positioning the one-pager in the APDLC workflow:
  ```markdown
  > **APDLC Context:** This one-pager is a **Phase 0** artifact — it exists to mature this concept in the backlog and support **Phase 1** prototyping decisions. Once a Phase 1 prototype is validated and approved, this one-pager can be expanded to a full PRD for **Phase 2** execution handoff to the scrum team.
  ```
  This helps stakeholders understand the artifact's purpose and where it sits in the Agentic Product Delivery Lifecycle (APDLC) without needing to know the full model context.
- **No Administrative table.** Roles, release, status, leads do not appear in a one-pager. Those live in the full PRD when we get there.
- **No Part 1 / Part 2 split.** Flat `#` section headers, in this order.
- **No Appendix.** No Portfolio Cross-Reference, no Key Decisions, no Post GA Ideas, no Key Evidence References, no References. (Portfolio research from [portfolio-cross-reference](../research/portfolio-cross-reference.md) still *runs* — it informs drafting — but doesn't get published inside the one-pager.)
- **Use `---` horizontal rules** between major sections for visual separation (matches `F0B05DPJDED`).

## Required sections (in this exact order)

Use flat `#` (H1) for top-level section headers and `##` (H2) only for per-customer signal subsections inside Customer Signal.

1. **`# The Problem`** — One paragraph. Describes the user/system behavior that is broken today and why it matters. No numbered lists, no sub-headers. Aim for 3–5 sentences.

2. **`# Customer Signal`** — Grounds the PRD in real customer asks. For each named customer, add a `##` subsection with the customer name. Inside each subsection:
   - 1 short paragraph describing what they do today and what is missing (bold the key nouns)
   - A **`What they need:`** line (bold prefix) that describes the concrete outcome the customer wants in customer-specific terms (name the product, the data, the path)
   - Typically 2–3 customers. If only one, that is fine. Never fabricate a second customer to pad the section.

3. **`---` + `# Why This Matters`** — 1 to 3 numbered principles. Each principle is `**N. Short claim.**` followed by 1–2 sentences of explanation. This is not the place for a business case bulleted list or customer quotes — those belong in the full PRD.

4. **`# The Gap (Current vs. Target)`** — Two subsections, `## Today` and `## Target`, each a numbered list of 4–6 steps describing the current flow vs. the target flow. Same step count in both lists so they are comparable step-by-step. Use inline code for structured examples (e.g., `` `{model: "...", error_code: "..."}` ``). This is the heart of the one-pager.

5. **`---` + `# Who Benefits`** — Single table with exactly three columns: `Persona | Pain Today | Desired Outcome`. 3–5 rows (typical: CSR, Admin/Builder, Customer). Each cell is a single sentence. No priority column. No goal column. Keep it lean — this is the one-pager persona shape.

6. **`---` + `# Jobs to be Done`** — 3–4 bulleted JTBD statements in `As a <persona>, I need <capability>, so that <outcome>.` form. Bold the persona. One bullet per persona in the Who Benefits table.

7. **`---` + `# Scope`** — Two labeled bullet lists:
   - `**In Scope**` — 3–5 bullets of what is included
   - `**Out of Scope**` — 3–5 bullets of what is explicitly excluded, often naming adjacent concerns that could be confused with this feature

8. **`---` + `# UX Considerations`** — Bulleted list of 2–4 design challenges (outcome-focused, not prescriptive). Each bullet: `**[Challenge Area]**: What needs to be solved from user's perspective`. Keep brief — this is a one-pager. Examples: "**New information visibility**: Reps need to notice when plan updates due to new customer message without disrupting current step", "**Error clarity**: When generation fails, rep needs to understand what went wrong and how to fix it". Omit if no UX-specific challenges exist.

9. **`---` + `# Prototype Approach`** (Optional — Agentic PDLC Phase 1) — Brief description of what to validate in a Phase 1 prototype. Include:
   - **What to validate:** Key assumptions, UX flows, or technical feasibility questions the prototype should answer
   - **Prototype scope:** Minimal clickable demo or technical spike showing X behavior (be specific — what must the prototype demonstrate?)
   - **Phase 1 exit criteria:** What would make this prototype ready for Phase 1 approval and gate entry to Phase 2 (e.g., "Rep can execute 3-step flow end-to-end without PM intervention", "Latency < 2s in demo environment", "UX confirms information hierarchy is discoverable without training"). A Phase 1 prototype that clears its exit criteria becomes the basis for the full PRD in Phase 2.
   
   **When to include:** Use this section when the feature requires Phase 1 prototyping to validate assumptions before writing a full PRD. Omit if (a) the feature is straightforward enough to skip Phase 1 prototyping, or (b) a Phase 1 prototype already exists and has been approved — in that case, go straight to the full PRD. This section helps teams scope what to build for the Phase 1 demo without over-specifying the implementation.

10. **`---` + `# Success Metrics`** — Table with exactly three columns: `Metric | Current State | Target`. 3–5 rows. Use concrete numbers where possible (`0%`, `> 80%`, `High`, `Near zero`, `TBD — measure baseline`). Metrics describe observable outcomes, not implementation internals.

11. **`---` + `# Open Questions`** — Table with exactly two columns: `Question | Notes`. 3–6 questions. Notes column is often blank — questions that still need an answer go here; questions that are already decided do not belong. No status column.

12. **`---` + `# Customer References`** — Bulleted list naming each customer referenced in Customer Signal with a one-line description of their use case. 2–4 bullets.

13. **`---` + `# Document History`** — Table at the very bottom of every PRD. Always present; starts with the initial draft row and grows with each update. Format:

    ```markdown
    | Date | Author | Source | Summary of Changes |
    |---|---|---|---|
    | YYYY-MM-DD | Author Name | Initial draft | Created one-pager for [feature name] |
    ```

    - **Date** — date the change was made
    - **Author** — person who made the change (typically Chad Goldsmith; use note author when incorporating call notes or comment feedback)
    - **Source** — where the change came from: "Initial draft", "Gemini meeting notes — [Meeting Name]", "Canvas comment — [Author]", "Slack thread — [channel]", "Scope review", etc.
    - **Summary of Changes** — one-line description of what changed in that batch
    - Add one row per update session (not per individual field). When applying a batch of changes from a single meeting or comment review, that is one row.
    - This section lives outside the one-pager line count target — it does not count toward the 80–150 line target.

## Sections to OMIT from one-pagers

These belong in the full PRD. Do not add them to a one-pager even when evidence exists for them:

- Administrative / Role table
- Business Case (`# Why This Matters` covers the short version)
- Value Statement (`# The Problem` covers the short version)
- Configuration Matrix (deep-dive detail; flag in Open Questions if needed)
- UX Mocks section (no Figma link in a one-pager — but `# UX Considerations` highlights design challenges)
- Competitive / Comparable (unless critical to positioning — then fold one line into `# Why This Matters`)
- Functional Requirements (numbered, with What/Why/Success/Constraints)
- User Stories
- Acceptance Criteria
- Risks & Edge Cases
- Dependencies
- Non-Functional Requirements
- Rollout Strategy
- Test Plan
- Required Content (from CX)
- Portfolio Cross-Reference (research still runs, but lives in drafting notes, not in the published one-pager)
- Key Decisions / Key Evidence / Post GA / References appendices

If the user asks "what about X?" and X is one of the above, point them at [expansion](../collaboration/expansion.md) — don't bloat the one-pager.

## Style rules

- **Total file length target: ~80–150 lines.** Reference canvas `F0B05DPJDED` is ~120 lines. If you are at 200+, you are drifting toward a full PRD — compress. Customer Signal with 3 customers will naturally push toward 140–150 and that is fine — don't sacrifice evidence depth to hit a line count.
- **Prose over lists where possible inside short sections.** The Problem and Customer Signal subsections are prose paragraphs, not bullet lists. Bullet lists are reserved for JTBD, Scope, and Customer References.
- **No sub-sub-headers (`###`).** H1 for sections, H2 only for per-customer signal subsections and the Today/Target split. Nothing deeper.
- **No block code fences except for inline examples.** One-pagers are plain-text friendly; fenced code blocks are a full-PRD signal.
- **Anti-solutioning still applies.** The Problem, Target Behavior, and Scope describe *what* needs to happen, not *how* to build it. Name the data, the path, the outcome — not the API, class, or schema.
- **Every customer name in Customer Signal maps 1:1 to a bullet in Customer References.** No unsourced customer claims.
- **Portfolio cross-reference still informs drafting** (avoid accidental duplication with existing PRDs) but does not appear in the published one-pager.

---

## Structural Fidelity Check (One-Pagers Only)

After drafting a one-pager, verify structural fidelity against the canonical reference (`F0B05DPJDED`):

| Check | Pass? |
|---|---|
| 12-13 sections in the prescribed order (Problem → Customer Signal → Why This Matters → Gap → Who Benefits → JTBD → Scope → UX Considerations → [Prototype Approach - optional] → Success Metrics → Open Questions → Customer References → Document History) | |
| H1 (`#`) for all section headers; H2 (`##`) only inside Customer Signal and Gap (Today/Target) | |
| No `###` sub-sub-headers anywhere | |
| `---` horizontal rules between major sections (before Why This Matters, Who Benefits, JTBD, Scope, UX Considerations, Success Metrics, Open Questions, Customer References) | |
| Every customer in Customer Signal has a matching bullet in Customer References | |
| Gap section has same step count in Today and Target lists | |
| Who Benefits table has exactly 3 columns (Persona / Pain Today / Desired Outcome) | |
| Total file length is ~80–150 lines | |
| No fenced code blocks (except inline examples) | |
| No Administrative table, no Part 1/Part 2 split, no Appendix | |

If any check fails, fix it before proceeding to over-solutioning review.
