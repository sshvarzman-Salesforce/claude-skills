---
name: pm-pretotype-shared
description: "Shared PBD → One-Pager → Interactive Pretotype pipeline for PMs. Takes a product concept through the APDLC Phase 0→1 artifact chain: creates a PBD, derives a one-pager, then builds an interactive click-through pretotype with PRD annotations and focus glow."
tools: [Write, Read, Edit, Bash]
---

# PM Pretotype Pipeline (Shared)

> **For any PM building features in Service Cloud / Agentforce.**
> Takes a product concept and builds three linked artifacts that feed each other.

**PBD → One-Pager → Interactive Pretotype** — the complete Phase 0→1 artifact chain.

> "Make sure you are building the right *it* before you build *it* right." — Alberto Savoia

---

## What You Get

Three artifacts, each feeding the next:

| # | Artifact | Purpose | Output |
|---|----------|---------|--------|
| 1 | **PBD** (Product Business Document) | Why it matters, who benefits, workstreams | `pbd-{release}-{slug}.md` |
| 2 | **One-Pager** (Requirements) | The problem, gap, scope, UX considerations | `prd-{release}-{slug}.md` |
| 3 | **Interactive Pretotype** | Click-through HTML demo with PRD annotations | `{slug}-prototype.html` |

The pretotype's annotations **reference specific PRD/PBD sections** so stakeholders see the concept AND the rationale in one view.

---

## Installation

Copy this skill's `SKILL.md` into your `~/.claude/skills/pm-pretotype/` directory:

```bash
mkdir -p ~/.claude/skills/pm-pretotype
cp SKILL.md ~/.claude/skills/pm-pretotype/
```

No other dependencies — just Claude Code with Write/Read/Edit/Bash tools.

---

## When to Use

- You have a validated concept ready for Phase 1 artifacts
- You need to present a feature to stakeholders (design, eng, leadership)
- You want the full chain: business case → requirements → interactive demo
- You're preparing for an alignment meeting and need all three in one go

**Can also be invoked partially:**
- "Just the PBD" → Phase 1 only
- "PBD + one-pager" → Phase 1-2
- "Pretotype from this PBD" → Phase 3 only (reads existing PBD/one-pager)

---

## Usage

```
/pm-pretotype Build the full pipeline for [feature name].

Context:
- Customer: [who needs it + signal]
- Problem: [what's broken today]
- Solution: [high-level approach]
- Key paths: [happy path, edge cases, fallbacks]
```

Or with an existing PBD:
```
/pm-pretotype Build a pretotype from my existing PBD at [path]
```

---

## Pipeline Details

### Phase 1: PBD (Product Business Document)

**Input:** Concept description, customer signal, problem statement
**Output:** Markdown file with APDLC frontmatter

**Structure:**
- Program Info + Team tables
- Executive Summary (2-3 sentences)
- ICP & Persona (table: Industry, Case complexity, Channel, Scale signal)
- Primary + Secondary Persona (Who, Pain, Desired outcome, Success metric)
- Problem Statement (numbered compounding problems)
- Why It Matters (Signal + Evidence table)
- Success Criteria (Metric, Current State, Target table)
- Solution Overview (ASCII architecture diagram + Key Design Decisions)
- Workstreams (table with dependencies)
- Platform Dependencies & TDs
- Risks & Mitigations
- Prototype Validation + Phase 1 Exit Criteria
- Open Questions (for Eng Lead alignment)
- Document History

### Phase 2: One-Pager (Requirements)

**Input:** PBD from Phase 1
**Output:** Markdown requirements document

Derives from the PBD — same content reshaped:
- The Problem (1 paragraph)
- Customer Signal (specific customers + what they said)
- Why This Matters (numbered)
- The Gap: Today vs. Target (step-by-step comparison)
- Who Benefits (Persona/Pain/Outcome table)
- Jobs to be Done (user stories)
- Scope: In/Out (bulleted)
- UX Considerations (~4 interaction design challenges)
- Prototype Approach (what to validate, exit criteria)
- Success Metrics + Open Questions
- Customer References

### Phase 3: Interactive Pretotype

**Input:** PBD + One-Pager
**Output:** Standalone HTML file (no dependencies)

#### Layout: Left 2/3 + Right 1/3

```
┌──────────────────────────────────┬─────────────────┐
│  LEFT (flex: 2)                  │  RIGHT (flex: 1) │
│                                  │                  │
│  ┌─ Case Context (compact) ───┐  │  Product UI     │
│  │  Avatar + Name + Subtitle  │  │  Panel Header   │
│  │  Customer Message/Scenario │  │                  │
│  └────────────────────────────┘  │  Interactive     │
│                                  │  Demo Content    │
│  ┌─ PBD Context Cards ───────┐  │                  │
│  │ Persona │ Customer         │  │  (buttons,      │
│  │ ICP     │ Why It Matters   │  │   messages,     │
│  │ [PBD] [One-Pager]         │  │   state         │
│  └────────────────────────────┘  │   transitions)  │
│                                  │                  │
│  ┌─ Annotation Panel (dark) ─┐  │  ┌─ Focus ─────┐│
│  │  ? STEP X OF Y            │  │  │ Bubble:     ││
│  │  Title (20px)             │  │  │ "PRD: ..."  ││
│  │  Body (15px)              │  │  └─────────────┘│
│  │  PRD Callout (quoted)     │  │                  │
│  │  Flow: ● ● ● ● ●         │  │  ┌─ Input ────┐│
│  │  [PBD] [One-Pager]        │  │  │ (optional) ││
│  └────────────────────────────┘  │  └─────────────┘│
└──────────────────────────────────┴─────────────────┘
```

#### Key Components

**Left Panel:**
- Case context (compact scenario setup)
- PBD context cards (2x2 grid: Persona, Customer, ICP, Why It Matters)
- Dark annotation panel (`#1a1a2e` background, fills remaining space, scrollable)

**Right Panel:**
- Product UI mockup (light theme)
- Interactive elements (buttons trigger state transitions)
- Focus bubble (floating tooltip with one-liner PRD reference)

**Focus Glow:**
- Purple pulsing `box-shadow` on the currently-annotated element in the right panel
- Visually connects left annotation to right UI element

#### Annotation Data Structure

```javascript
const annotations = {
    stepKey: {
        step: 'Step 1 of N',           // Progress indicator
        title: 'What\'s Happening',     // Bold heading (20px)
        body: 'Description...',         // Body text (15px) with <strong> highlights
        callout: '<strong>PRD — Section:</strong> "Verbatim quote from one-pager or PBD"',
        bubble: '<strong>PRD:</strong> One-liner for the focus bubble on right panel',
        focusTarget: '#elementId',      // CSS selector for .focus-glow target
        flow: [                         // Progress dots
            { label: 'Step name', status: 'done|active|pending' }
        ]
    }
};
```

#### Interaction Pattern

1. Button click → calls function (e.g., `selectStep('planning')`)
2. Function calls `setAnnotation('stepKey')` which:
   - Updates left annotation panel
   - Applies `.focus-glow` to the target element on right
   - Shows focus bubble with one-liner PRD context
3. Messages/state appended to right panel with animation delays
4. Action steps animate sequentially (pending → running → done)

#### Scenario Design Rules

- Use realistic data from the PBD's customer signal (names, IDs, amounts)
- Match the ICP industry (airline → booking, telco → plan, finserv → transaction)
- Show complete happy path + any fallback/edge paths
- Include at least one mid-flow event (new data arriving, state change)
- Make the problem viscerally obvious in the "before" state

---

## Key Principles

1. **Every annotation references the PBD/PRD** — callouts quote specific sections verbatim
2. **Focus glow connects left to right** — purple pulsing border on active element
3. **Focus bubble = one-liner** — max 1-2 sentences, viewer doesn't have to look left
4. **Interactive, not passive** — buttons, click-through, progressive reveal
5. **Full viewport** — no scrolling on body, panels fill height
6. **PBD context cards persist** — always visible at top of left panel
7. **Dark annotation panel** — visually distinct from product UI
8. **Progressive events** — show evolving state mid-flow
9. **Never create a full PRD** — pipeline stops at PBD + One-Pager + Pretotype unless explicitly asked

---

## Publishing (Adapt to Your Setup)

The pretotype is a standalone HTML file — host it however your team shares artifacts:
- GitHub Pages (push to a repo with Pages enabled)
- Internal wiki (embed or link)
- Slack (share the file directly — opens in browser)
- PRD doc (link to hosted version)

Recommended structure:
```
your-repo/
├── prds/
│   ├── pbd-266-feature-name.md
│   └── prd-266-feature-name.md
└── prototypes/
    └── feature-name.html        ← interactive pretotype
```

---

## Limitations

- **Not pixel-perfect UI** — this communicates concepts, not final design
- **Not a substitute for UX** — hand off to design after stakeholder alignment
- **Standalone HTML only** — no external dependencies, no build step
- **Sequential execution** — pretotype shows one path at a time (not parallel)

---

## Example: What Multi-Intent Detection Looks Like

The reference pretotype demonstrates:
- Left 2/3 + right 1/3 layout
- PBD context cards (persona, customer, ICP, why it matters)
- Dark annotation panel with PRD callouts + flow dots
- Focus glow connecting annotation to demo element
- Focus bubble (one-liner on right panel)
- Interactive click-through with state transitions
- Progressive detection (new intent added mid-conversation)
- Two-path architecture (topic matched vs. NBA fallback)
- Action execution with sequential animation

Ask your PM lead for a link to the reference implementation if you'd like to see it in action.

---

## Changelog

| Date | Change |
|---|---|
| 2026-05-20 | Initial skill creation — animated wireframe pretotypes for PMs |
| 2026-06-26 | Major rewrite — full PBD → One-Pager → Interactive Pretotype pipeline. Added layout spec, focus bubble, PBD context cards, publishing workflow. |
