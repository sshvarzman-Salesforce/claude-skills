---
name: pm-pretotype
description: "PBD → One-Pager → Interactive Pretotype pipeline. Takes a validated concept through the full APDLC Phase 0→1 artifact chain: creates the PBD, derives a one-pager, then builds a click-through interactive pretotype with PRD annotations."
tools: [Write, Read, Edit, Bash]
---

# PM Pretotype Pipeline

**PBD → One-Pager → Interactive Pretotype** — the complete Phase 0→1 artifact chain.

> "Make sure you are building the right *it* before you build *it* right." — Alberto Savoia

This skill takes a product concept and builds three linked artifacts:
1. **PBD** (Product Business Document) — why it matters, who benefits, workstreams
2. **One-Pager** (Requirements One-Pager) — the problem, gap, scope, UX considerations
3. **Interactive Pretotype** — click-through HTML demo with PRD annotations + focus glow

Each artifact feeds the next. The pretotype's annotations reference specific PRD/PBD sections so stakeholders see the concept AND the rationale in one view.

---

## When to Use

- You have a validated concept ready for Phase 1 artifacts
- You need to present a feature to stakeholders (design, eng, leadership)
- You want the full chain: business case → requirements → interactive demo
- You're preparing for an alignment meeting and need all three in one go

**Can also be invoked partially:**
- "Just the PBD" → Phase 1 only
- "PBD + one-pager" → Phase 1-2
- "Pretotype from this PBD" → Phase 3 only (reads existing PBD)

---

## Pipeline

### Phase 1: PBD (Product Business Document)

**Input:** Concept description, customer signal, problem statement
**Output:** `~/sra-prds/pbd-{release}-{slug}.md`

Structure:
```markdown
---
ga_version: {release}
stage: pbd-draft
type: pbd
format: apdlc
team: TBD
authoring_pm: Chad Goldsmith
execution_pm: Chad Goldsmith
program: {Title}
tier: {1-3}
pbd_status: draft
source_prd: prd-{release}-{slug}.md
inspection_date: TBD
pbd_audit: null
prototype: pending
---

# Product Business Document: {Title}

## Program Info
| Field | Value |
|-------|-------|
| Author | Chad Goldsmith |
| Dated | {today} |
| Version | v 1.0 |
| Document Status | Draft |
| Start Target Release | {release} |
| Tier | {1-3} — {tier description} |
| Program Name | {Title} |
| Cloud Name | Service Cloud |
| V2MOM/Cloud Portfolio | Service Rep Assistant |

## Program Team
| Role | Who |
|------|-----|
| PM Owner | Chad Goldsmith |
| Eng. Lead | TBD |
| UX Lead | {name if known} |
| TPM | TBD |

## Executive Summary
{2-3 sentences: what's broken, what this does, why now}

## ICP & Persona

### Ideal Customer Profile
| Dimension | Criteria |
|-----------|----------|
| Industry | {specific verticals} |
| Case complexity | {what makes them need this} |
| SRA adoption | {prerequisite maturity} |
| Channel | {messaging, voice, etc.} |
| Scale signal | {size/volume indicator} |

### Target Persona: {Primary}
- **Who:** {role + context}
- **Pain:** {specific, measurable}
- **Desired outcome:** {concrete}
- **Success metric:** {how we know they're happy}

### Target Persona: {Secondary}
- Same structure

## Problem Statement
{Numbered list of 2-4 compounding problems}

## Why It Matters
| Signal | Evidence |
|--------|----------|
| {type} | {specific data point} |

## Success Criteria
| Metric | Current State | Target |
|--------|---------------|--------|

## Solution Overview
### Architecture
{ASCII diagram showing the flow}

### Key Design Decisions
1. {Decision + rationale}

## Workstreams
| # | Workstream | Description | Dependency |
|---|-----------|-------------|------------|

## Platform Dependencies & TDs
| Dependency | Owner | Status | Risk |

## Risks & Mitigations
| Risk | Impact | Mitigation |

## Prototype Validation
| Artifact | Link |
|----------|------|
| Interactive Pretotype | {pages URL} |
| One-Pager | {repo URL} |
| PRD Portfolio | {portfolio URL} |

### Phase 1 Exit Criteria
- {bulleted list}

## Open Questions
| # | Question | Decision Needed By |

## Document History
| Date | Author | Summary |
```

### Phase 2: One-Pager (Requirements)

**Input:** PBD from Phase 1
**Output:** `~/sra-prds/prd-{release}-{slug}.md`

Derives from the PBD — same content reshaped as a requirements doc:

```markdown
---
stage: draft
release: {release}
ga_version: {release}
team: TBD
authoring_pm: Chad Goldsmith
execution_pm: Chad Goldsmith
feature: {slug}
prototype: done
---

# Requirements One Pager: {Title}

> **APDLC Context:** Phase 0 artifact — exists to mature in backlog and support Phase 1.

## The Problem
{1 paragraph describing the pain — derived from PBD Executive Summary}

## Customer Signal
### {Customer 1}
{What they told us, what they need}

### {Customer 2}
{Same structure}

## Why This Matters
1. {From PBD Problem Statement}
2. {Each numbered, ~1-2 sentences}
3. {...}

## The Gap (Current vs. Target)
### Today
1. {Step-by-step what happens now}

### Target
1. {Step-by-step what should happen}

## Who Benefits
| Persona | Pain Today | Desired Outcome |
|---------|-----------|-----------------|

## Jobs to be Done
- As a **{persona}**, I need to {action} so that {outcome}.

## Scope
**In Scope**
- {bulleted}

**Out of Scope**
- {bulleted}

## UX Considerations
- {~4 bullet points about the interaction design challenges}

## UX Prototype
> **Interactive prototype:** [{slug}.html]({pages URL})

**Flow descriptions with placeholder image links**

## Prototype Approach
**What to validate:**
- {questions}

**Prototype scope:**
- {what we're building}

**Phase 1 exit criteria:**
- {from PBD}

## Success Metrics
| Metric | Current State | Target |

## Open Questions
| Question | Notes |

## Customer References
- {bulleted}

## Document History
| Date | Author | Source | Summary |
```

### Phase 3: Interactive Pretotype

**Input:** PBD + One-Pager from Phases 1-2
**Output:** `~/.agents/artifacts/prototypes/{slug}-prototype.html`

Builds a full-viewport interactive HTML pretotype.

#### Layout: Left 2/3 + Right 1/3

```
┌──────────────────────────────────┬─────────────────┐
│  LEFT (flex: 2)                  │  RIGHT (flex: 1) │
│                                  │                  │
│  ┌─ Case Context (compact) ───┐  │  Product UI     │
│  │  Avatar + Name + Subtitle  │  │  Panel Header   │
│  │  Customer Message Card     │  │                  │
│  └────────────────────────────┘  │  ┌─ Pinned ─┐  │
│                                  │  │  Tracker  │  │
│  ┌─ PBD Context Cards ───────┐  │  └───────────┘  │
│  │ Persona │ Customer         │  │                  │
│  │ ICP     │ Why It Matters   │  │  Conversation   │
│  │ [PBD] [One-Pager] [Portf] │  │  Messages...    │
│  └────────────────────────────┘  │                  │
│                                  │  ┌─ Focus ─────┐│
│  ┌─ Annotation Panel (dark) ─┐  │  │ Bubble:     ││
│  │  ? STEP X OF Y            │  │  │ "PRD: ..."  ││
│  │  Title                    │  │  └─────────────┘│
│  │  Body text                │  │                  │
│  │  PRD Callout (purple BG)  │  │  ┌─ Input ────┐│
│  │  Flow: ● ● ● ● ●         │  │  │ Ask...     ││
│  │  [PBD] [One-Pager]        │  │  └─────────────┘│
│  └────────────────────────────┘  │                  │
└──────────────────────────────────┴─────────────────┘
```

#### Component Breakdown

**Left Panel (`.console-main`, flex: 2):**
- Case context section (flex: none, compact) — scenario avatar, name, customer message
- PBD context cards (flex: none) — 2x2 grid: Persona, Customer, ICP, Why It Matters + doc links
- Annotation panel (flex: 1, fills remaining, dark `#1a1a2e` background, scrollable)

**Right Panel (`.sra-panel`, flex: 1):**
- Product UI header
- Pinned tracker (if applicable)
- Conversation/interaction area (scrollable)
- Focus bubble (absolute positioned, `bottom: 70px`, dark purple, one-liner PRD reference)
- Input area (bottom)

**Focus Glow (`.focus-glow`):**
- Purple pulsing box-shadow on the currently-annotated element in the right panel
- Connects the left annotation to the right UI element visually

#### Annotation Data Structure

Each step in the demo has an annotation object:
```javascript
const annotations = {
    stepKey: {
        step: 'Step 1 of N',           // Progress indicator
        title: 'What\'s Happening',     // Bold heading
        body: 'Description...',         // 1-2 sentences with <strong> highlights
        callout: '<strong>PRD — Section:</strong> "Verbatim quote from the one-pager or PBD"',
        bubble: '<strong>PRD:</strong> One-liner summary for the focus bubble on right panel',
        focusTarget: '#elementId',      // CSS selector for .focus-glow target
        flow: [                         // Flow dots showing progress
            { label: 'Step name', status: 'done|active|pending' }
        ]
    }
};
```

#### Demo Flow Logic

The pretotype is interactive — buttons in the conversation trigger state transitions:
1. Each button click calls a function (e.g., `selectIntent('rebooking')`)
2. That function calls `setAnnotation('stepKey')` which:
   - Updates the left annotation panel content
   - Applies `.focus-glow` to the `focusTarget` element on the right
   - Shows the focus bubble with the short `bubble` text
3. Messages are appended to the conversation area with animation delays
4. Action steps can animate sequentially (pending → running → done)

#### Scenario Design Rules

Build around a **realistic customer scenario** from the PBD's customer signal:
- Use real-ish data (names, flight numbers, amounts, dates, account IDs)
- Match the ICP industry (airline → booking, telco → plan change, finserv → transaction)
- Show the complete happy path, then any fallback/edge paths
- Include at least one "mid-flow event" (new data arriving, state change)
- The scenario should make the problem viscerally obvious

#### Key Principles

1. **Every annotation references the PBD/PRD** — callouts quote specific sections verbatim
2. **Focus glow connects left to right** — purple pulsing border on active element
3. **Focus bubble = one-liner** — max 1-2 sentences, viewer doesn't HAVE to look left
4. **Interactive, not passive** — buttons, click-through, progressive reveal
5. **Full viewport** — no scrolling on body, panels fill height
6. **PBD context cards persist** — always visible at top of left panel
7. **Dark annotation panel** — visually distinct from product UI (light theme on right)
8. **Progressive events** — show evolving state (new intent, new data, status changes)
9. **Doc links everywhere** — PBD, One-Pager, Portfolio badges in annotation + PBD cards

---

## Publishing

After generation, all three artifacts are published:

**PBD + One-Pager:**
1. Save to `~/sra-prds/` with naming: `pbd-{release}-{slug}.md` / `prd-{release}-{slug}.md`
2. Run `cd ~/sra-prds && python3 generate-index.py` to update portfolio page
3. `git add . && git commit && git push`
4. Live at: https://git.soma.salesforce.com/pages/chad-goldsmith/sra-prds/

**Pretotype:**
1. Save to `~/.agents/artifacts/prototypes/{slug}-prototype.html`
2. Copy to `~/APDLC-Tools-and-Docs/prototypes/{slug}.html`
3. `git add && git commit && git push` → live at: `https://git.soma.salesforce.com/pages/chad-goldsmith/APDLC-Tools-and-Docs/prototypes/{slug}.html`
4. Also copy to `~/prd-writer-skill/prototypes/` and push to claude-skills repo

---

## Iteration

After initial generation, the user will iterate on the pretotype:
- "Make the font bigger on the left"
- "Add a new step showing X"
- "Add an emergent event mid-flow"
- "Change the layout ratio"
- "The annotation should quote this PRD section"

Apply changes incrementally. Each iteration: edit HTML → copy to both repos → commit → push.

---

## Reference Implementations

### Gold Standard: Dynamic Guidance Plans (July 2026)

**THE gold standard for pretotypes** — use this as the primary template:
- **PBD:** `~/sra-prds/pbd-264-dynamic-guidance-plans.md`
- **One-Pager:** `~/sra-prds/prd-264-dynamic-guidance-plans-one-pager.md`
- **Pretotype:** `~/APDLC-Tools-and-Docs/prototypes/dynamic-guidance-plans.html`
- **Live:** https://git.soma.salesforce.com/pages/chad-goldsmith/APDLC-Tools-and-Docs/prototypes/dynamic-guidance-plans.html

**Why this is the gold standard:**
- **Left panel conversation in one unified white box** — initial customer utterance + evolving rep-customer conversation all inside the "Customer Issue" card with white background, making it easy to read and emphasizing the triggering utterance
- **Real SRA UX patterns** — matches production layout: LEFT = rep ↔ customer conversation (voice call transcript style), RIGHT = SRA guidance + plan + actions
- **Action execution on right** — actions execute sequentially (pending → running → done) in the Service Rep Assistant panel, showing real-time work
- **Clean visual hierarchy** — conversation flows naturally, guidance stays contextual, annotations reference PRD sections
- **Step-by-step scenarios** — 6 interactive scenarios showing plan generation, insertion, branching, multi-intent detection, and removal
- **PBD context cards** — persona, customer, ICP, why it matters visible at bottom of left panel
- **Dark annotation panel** — separates product demo (light) from PRD context (dark)

**Key layout principle from this prototype:**
> Conversation should be unified in one white box, not split between static text and a separate grey area. The initial utterance triggers the plan, and all subsequent messages flow in the same container with consistent white background for easy reading.

### Secondary Reference: Multi-Intent Detection

Also a strong reference (pre-gold standard):
- **PBD:** `~/sra-prds/pbd-266-sra-multi-intent-detection.md`
- **One-Pager:** `~/sra-prds/prd-266-sra-multi-intent-detection.md`
- **Pretotype:** `~/.agents/artifacts/prototypes/sra-multi-intent-prototype.html`
- **Live:** https://git.soma.salesforce.com/pages/chad-goldsmith/APDLC-Tools-and-Docs/prototypes/sra-multi-intent.html

Good for:
- Progressive detection (new intent added mid-conversation)
- Two-path architecture (topic matched vs. NBA fallback)
- Action execution with sequential animation

**Always use Dynamic Guidance Plans as the primary template for new pretotypes.**

---

## Changelog

| Date | Change |
|---|---|
| 2026-05-20 | Initial skill creation — animated wireframe pretotypes for PMs |
| 2026-06-26 | Major rewrite — full PBD → One-Pager → Interactive Pretotype pipeline. Added layout spec (left 2/3 + right 1/3), focus bubble, PBD context cards, publishing workflow, reference implementation (multi-intent). |
| 2026-07-16 | Updated gold standard to Dynamic Guidance Plans prototype. Key principle: conversation should be unified in one white box (initial utterance + evolving messages) with consistent white background for easy reading, not split between static text and grey area. |
