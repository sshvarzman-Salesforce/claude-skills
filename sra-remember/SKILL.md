---
name: sra-remember
description: Store a learning in the SRA memory system with categorization, tagging, and approval flow. Use when saving decisions, preferences, or domain insights about Service Rep Assistant, its customers, platform constraints, or team patterns. Supports Decision, Preference, and Domain Knowledge categories.
tools: [Read, Write, Edit]
---

# SRA Remember

Store a learning: $ARGUMENTS

## Process

1. **Parse** — Extract core learning; detect category hints (`Decision:`, `Preference:`)

2. **Categorize** — Determine file:
   - **decisions** — Choices made and rationale ("decided", "chose", "deprioritized", "deferred", "went with")
   - **preferences** — Customer, stakeholder, or team preferences ("prefers", "likes", "always", "never", "wants")
   - **domain-knowledge** — SRA platform insights, integration patterns, customer workflows, technical constraints ("requires", "needs", "discovered", "learned", "turns out")

3. **Format Entry**
   ```markdown
   ## [Short descriptive title]
   - **Learned**: [Today YYYY-MM-DD]
   - **Source**: [Conversation / Customer call / PRD / Meeting / etc.]
   - **Confidence**: high | medium
   - **Tags**: #tag1 #tag2

   [Learning in 1-3 sentences]

   ---
   ```

4. **Extract Tags** from:
   - **Customers/accounts:** #meta, #ups, #adp, #customer
   - **Features:** #summary-plan, #dynamic-plan, #show-summary, #guidance-plan, #message-history, #url-clickability
   - **Channels:** #voice, #messaging, #case
   - **Platform:** #record-home-load, #recactoraction-feed, #genopplan, #eligibility, #routing, #gater, #metering
   - **Team/process:** #sf-spa, #scrum-team, #admin-config, #ux, #qa, #ga, #beta

5. **Present for Approval**
   ```
   Category: [decisions | preferences | domain-knowledge]
   File: memory/[category].md
   [Show formatted entry]
   → Store this? (yes / edit / reject)
   ```

6. **Handle Response**
   - **yes** → Append to `memory/[category].md`
   - **edit: [modification]** → Apply edit, ask again
   - **reject** → Discard

## Examples

```
/sra-remember Meta prefers zero UI before the first Dynamic Plan step on Voice — dead air on live calls is their biggest pain point
/sra-remember Decision: Deferred Summary Plan as grounding signal for Dynamic Plans — Hyperclassifier intent replaces it until quality improves
/sra-remember Show Summary = OFF must skip GenOpPlanRequest creation entirely — checking the flag after generation would still meter the event
/sra-remember UPS needs the Summary Plan to scroll away naturally — their console layout breaks when it's pinned to the top
/sra-remember Voice eligibility re-evaluates on call transfer — the plan generates for the new rep, not the old one
```
