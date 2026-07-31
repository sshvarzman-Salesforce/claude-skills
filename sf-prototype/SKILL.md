---
name: sf-prototype
description: Coordinate and document APDLC Phase 1 prototypes — tracks prototype artifacts, recorded demos, and validation status needed for Phase 2 inspection gate.
tools: [mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_slack_slack__slack_send_message, mcp__plugin_slack_slack__slack_read_user_profile, Write, Read, Bash]
---

# Salesforce Prototype Coordinator

> **APDLC Phase 1 artifact.** Every program must produce a working prototype + recorded demo before passing the Phase 2 gate. This skill tracks, documents, and validates prototype readiness.

## APDLC Context

This skill operates in **Phase 1 (Discovery & Prototyping)** — a 14-day sprint where the AI Pod validates the approach.

### Phase 1 Sub-Stage Timeline (14-Day Sprint)

| Days | Activity | Lead |
|---|---|---|
| **Days 1-3** | Strategy + PM define Value Proposition (North Star) | Strategy + PM |
| **Days 2-8** | SWE drafts Preliminary Architecture; UX/CX begins prototyping | SWE + UX/CX |
| **Days 9-10** | Pod consolidates prototype for Phase 2 leadership review | Full Pod |

### Phase 1 Required Outputs

The Phase 2 Inspection gate requires ALL of the following:

| Output | Required? | Notes |
|---|---|---|
| Working Prototype | Yes | Demonstrates the proposed solution |
| ★ Recorded Demo (under 10 min) | Yes (pre-read) | Narrated walkthrough proving prototype works |
| ★ Product Business Document (PBD) | Yes (pre-read) | Written by `sf-pbd-writer` |
| Architecture Direction | Yes | Preliminary architecture from SWE |
| Eng Sizing & "Big Rocks" Requirements | Yes | Critical technical/functional requirements posing highest risk to delivery |
| CX Content Plan & UI Text | Yes | Content strategy from CX/CDX |
| UX Guardrails | Yes | Design constraints to prevent scope creep during Phase 2 |
| Marketing/GTM Alignment | Yes | Early GTM coordination |

★ = required pre-reads for inspection (must be delivered before gate)

### Pre-Read Timing

- **Apps & Industries President**: 24 hours before inspection
- **Service Cloud (Jujhar)**: 2 business days before inspection
- Pre-reads = PBD + Recorded Demo (no slides)

### Key Concepts

- **Big Rocks**: Critical technical/functional requirements posing highest risk to delivery. Identified and sized in Phase 1 — these are the items that determine whether the feature is feasible at all.
- **UX Guardrails**: Design constraints established in Phase 1 to prevent scope creep. Once set, Phase 2 work must stay within these boundaries unless leadership approves expansion.
- **Shovel Ready**: A feature that has been prototyped and judged worthy of productization — this is the Phase 0 → Phase 1 handoff criteria.

**APDLC Resources:**
- Hub: https://salesforce.enterprise.slack.com/docs/T01G0063H29/F0BBE8EM1UL
- Champions channel: https://slack.com/archives/C0B356NL2DQ
- Process Doc: https://docs.google.com/document/d/1_cQuP9vzPfX_ejqfPGEf3-ZKThjCan4mKpEjh8ax6zA/edit

---

## When to Use This Skill

Use this skill when:
- You need to plan what your prototype should demonstrate
- You want to track prototype artifacts (links, recordings, environments)
- You're preparing for the Phase 2 inspection and need to validate completeness
- You want to generate a prototype brief (scope doc for eng)

**Do NOT use this skill when:**
- You want a quick visual wireframe to communicate a concept (use `pm-pretotype`)
- You're building the actual prototype code (that's eng work)
- You're writing the PBD (use `sf-pbd-writer`)

---

## Prototype Types (Pick One)

| Type | What It Is | Best For | Typical Owner |
|------|-----------|----------|---------------|
| **SDO Demo** | Working feature in a Salesforce demo org | Platform features, agent config, service flows | PM + Solutions Eng |
| **Figma Prototype** | Clickable interactive mockup | UX-heavy features, new surfaces, layout changes | UX Lead |
| **Code Spike** | Minimal working code (branch or fork) | API features, integrations, performance-sensitive | Eng Lead |
| **Wizard of Oz** | Manual process simulating the feature | AI/ML features where model isn't ready | PM |
| **Pretotype** | Animated wireframe (via `pm-pretotype`) | Early-stage validation before committing to full prototype | PM |

---

## Prototype Brief (What to Document)

When you ask this skill to create a prototype brief, it produces:

```markdown
# Prototype Brief: {Feature Name}

## What to Validate
- [Key hypothesis 1 — what must be proven]
- [Key hypothesis 2]
- [Key hypothesis 3]

## Prototype Scope
- IN: [What the prototype demonstrates]
- OUT: [What's faked, mocked, or skipped]
- FAKE IT: [What looks real but isn't production-ready]

## Success Criteria
- [ ] [Criterion 1 — observable outcome]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## Demo Script (for recording)
| # | Action | Expected Result | What to Call Out |
|---|--------|-----------------|-----------------|
| 1 | [Setup/context] | [Starting state] | "Here's the problem today..." |
| 2 | [First interaction] | [Prototype response] | "Now with our solution..." |
| 3 | [Key moment] | [Value demo] | "This is where the magic happens..." |

## Environment
- Org/Environment: [SDO alias, Figma link, branch name]
- Access: [Who can access and how]
- Reset: [How to return to demo-ready state]

## Recording Checklist
- [ ] Screen recording software ready (Loom/Zoom)
- [ ] Demo environment in clean state
- [ ] Script rehearsed at least once
- [ ] Recording under 10 minutes
- [ ] Key value moments clearly narrated
- [ ] Upload location: [Link]
```

---

## Prototype Readiness Checklist

Before Phase 2 gate, validate:

| Requirement | Status | Notes |
|-------------|--------|-------|
| Prototype demonstrates the proposed solution | ☐ | Must match PBD "Proposed Solution" |
| Prototype covers primary persona | ☐ | At minimum, Persona #1 from PBD Section 3 |
| Recorded demo exists | ☐ | Under 10 min, narrated |
| Demo clearly shows before→after | ☐ | Maps to Customer Journey Impact |
| Stakeholders have reviewed prototype | ☐ | Eng lead, UX lead, at minimum |
| Known limitations documented | ☐ | What's faked/mocked vs. real |
| Prototype link added to PBD | ☐ | In the Pre-Read Requirement section |
| Demo link added to PBD | ☐ | In the Pre-Read Requirement section |
| UX Guardrails documented | ☐ | Design constraints that bound Phase 2 scope |
| Big Rocks identified & sized | ☐ | High-risk technical requirements called out |
| Pre-read delivered on time | ☐ | 24hr (A&I) or 2 biz days (Service Cloud) before gate |

---

## Relationship to Other Skills

| Skill | Relationship |
|-------|-------------|
| `sf-pbd-writer` | **Parallel** — PBD references prototype link + demo; both needed for Phase 2 gate |
| `sf-prd-writer` (one-pager) | **Upstream** — One-pager defines what to prototype |
| `pm-pretotype` | **Subset** — Pretotypes are one option for early validation; not always sufficient for Phase 2 gate |
| `sf-demo-skills` | **Relevant** — If prototype is an SDO demo, use demo skill patterns for build |

---

## Example Workflow

```
User: "Create a prototype brief for the Action Output Re-Grounding feature"

Skill:
1. Reads the one-pager (or PBD) for context
2. Identifies key hypotheses to validate:
   - "Can the planner re-ground on action output mid-plan?"
   - "Does re-grounding change the remaining plan steps?"
   - "Is the UX clear when steps change mid-execution?"
3. Generates prototype brief with demo script outline
4. Suggests prototype type: SDO Demo (agent config + Apex action)
5. Saves: prototype-brief-264-action-output-regrounding.md
6. Reminds: "Record demo once built. Both links go in the PBD Pre-Read section."
```

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-19 | Initial prototype coordinator skill — supports APDLC Phase 1 gate prototype artifact tracking |
