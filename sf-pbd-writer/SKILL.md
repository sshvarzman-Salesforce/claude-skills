---
name: sf-pbd-writer
description: "Creates Product Business Documents (PBDs) for Salesforce Service Cloud programs following the APDLC Phase 1 format. PBDs are program-level business cases that precede prototyping."
tools: [Read, Write, Edit, Bash]
---

# Salesforce PBD Writer

**Product Business Document (PBD) creation for APDLC Phase 1.**

> PBDs answer: Why does this program matter? Who benefits? What are the workstreams, risks, and success criteria?

This skill creates **program-level** business case documents that precede prototyping in the Agentic Product Delivery Lifecycle (APDLC). PBDs are Phase 1 artifacts — they replace theme decks and product briefs.

**Originally built for Service Rep Assistant.** Customizable for other Salesforce products.

---

## When to Use

- You have a validated concept ready for Phase 1 artifacts
- You need a business case for a multi-feature program or initiative
- You're preparing for a Phase 2 Inspection gate (PBD must be delivered 2 business days before)
- You want program-level context (ICP, personas, workstreams, risks) before writing feature PRDs

**Not for individual features** — use `/sf-prd-writer` for feature-level one-pagers or full PRDs.

---

## APDLC Context

| Phase | Artifact | When | What |
|-------|----------|------|------|
| **Phase 0** | One-Pager | Backlog & Research | Problem definition, customer signal, scope (use `/sf-prd-writer`) |
| **Phase 1** | **PBD** + Prototype | Discovery & Prototyping | Business case + working prototype to validate assumptions |
| **Phase 2** | Full PRD | Consolidation & Productization | Post-prototype execution spec for scrum teams |
| **Phase 3** | Launch Materials | GTM & Adoption | Docs, enablement, launch comms |

**PBDs sit between one-pagers and full PRDs.** They provide program-level strategy and justify investment in prototyping.

---

## PBD Structure

All PBDs follow this 11-section format:

```markdown
---
ga_version: {release}
stage: pbd-draft
type: pbd
format: apdlc
release: {release}
team: {team names}
authoring_pm: Chad Goldsmith
execution_pm: Chad Goldsmith
program: {Program Title}
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
| Revised | — |
| Version | v 1.0 |
| Document Status | Draft |
| Start Target Release | {release} |
| Inspection Date | TBD |
| Tier | {1-3} — {tier description} |
| Program Name | {Title} |
| Cloud Name | Service Cloud |
| V2MOM/Cloud Portfolio | Service Rep Assistant |
| PFT | TBD |

## Program Team
| Role | Who |
|------|-----|
| PM Owner | Chad Goldsmith |
| Eng. Lead | TBD (needs scoping) |
| UX Lead | {name if known, else TBD} |
| TPM | TBD |
| Technical Writer | TBD |
| PMM | TBD |

## Executive Summary
{2-4 paragraphs: current state → problem → proposed solution → why now}

Key elements:
- What's the current state and gap?
- What does this program deliver?
- Why does it matter now?
- Target release + expansion plan

## ICP & Persona

### Ideal Customer Profile
| Dimension | Criteria |
|-----------|----------|
| Industry | {specific verticals} |
| Case complexity | {what makes them need this} |
| SRA adoption | {prerequisite maturity} |
| Channel | {messaging, voice, etc.} |
| Scale signal | {size/volume indicator} |

### Target Persona: {Primary Role} (Primary)
- **Who:** {role + context}
- **Pain Points:** {bulleted list of specific pains}
- **Desired outcome:** {concrete, measurable}
- **Success metric:** {how we know they're happy}

### Target Persona: {Secondary Role} (Secondary)
- Same structure

### Target Persona: {Tertiary Role} (Tertiary)
- Same structure (if applicable)

## Problem Statement
{Numbered list of 2-4 compounding problems}

Each problem should:
- Be specific and measurable
- Show how problems compound
- Reference customer evidence

## Why It Matters
| Signal | Evidence |
|--------|----------|
| Customer demand | {specific customer + requirement} |
| Field feedback | {FDE/CSM feedback with source} |
| Platform readiness | {what's already available} |
| Competitive pressure | {competitor capability or gap} |
| Strategic enabler | {what this unlocks} |

## Success Criteria
| Metric | Current State | Target (Release) | Measurement |
|--------|---------------|------------------|-------------|
| **Feature Adoption** | {baseline} | {target %} | {telemetry source} |
| **Usage Depth** | {baseline} | {target %} | {telemetry source} |
| **Engagement Quality** | {baseline} | {target %} | {telemetry source} |
| **Business Impact** | {baseline} | {target improvement} | {customer surveys, telemetry} |

## Solution Overview

### Architecture: {Name}
```
{ASCII diagram showing the flow}
```

### Key Design Decisions
1. **{Decision}** — {Rationale and implications}
2. **{Decision}** — {Rationale and implications}
3. {...}

## Workstreams
| # | Workstream | Description | Owner | Dependency |
|---|-----------|-------------|-------|------------|
| **WS1** | **{Name}** | {What this workstream delivers} | {Team/Person} | {What this depends on} |
| **WS2** | **{Name}** | {Description} | {Owner} | {Dependency} |
| {...} |

## Platform Dependencies & TDs
| Dependency | Owner | Status | Risk | Mitigation |
|-----------|-------|--------|------|------------|
| **{Dependency Name}** | {Owner} | {Status emoji + description} | {Risk level} | {How we mitigate} |

**Hard Dependencies (Without these, feature can't ship):**
1. {Dependency} — {Status and risk}

**Soft Dependencies (Feature works without, but value is reduced):**
1. {Dependency} — {Nice-to-have}

## Risks & Mitigations
| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| 🔴 HIGH: {Risk} | {What breaks} | {HIGH/MEDIUM/LOW} | {How we mitigate + contingency} |
| 🟡 MEDIUM: {Risk} | {What breaks} | {MEDIUM} | {Mitigation} |
| 🟢 LOW: {Risk} | {What breaks} | {LOW} | {Mitigation} |

## Prototype Validation
| Artifact | Status | Link |
|----------|--------|------|
| **One-Pager (Phase 0)** | {status} | {repo URL or TBD} |
| **Pretotype (Interactive HTML Demo)** | {status} | {git.soma pages URL or TBD} |
| **Full PRD (Phase 2)** | {status} | {repo URL or TBD} |

### Phase 1 Exit Criteria
Before proceeding to Full PRD (Phase 2):

✅ {Criterion 1}  
✅ {Criterion 2}  
✅ {Criterion 3}  
✅ {...}

## Open Questions (for Eng Lead Alignment)
| # | Question | Decision Needed By | Blocker For |
|---|---------|-------------------|-------------|
| 1 | {Question} | {Milestone} | {What this blocks} |
| 2 | {Question} | {Milestone} | {What this blocks} |
| {...} |

## Document History
| Date | Author | Summary |
|------|--------|---------|
| {today} | Chad Goldsmith | Initial PBD draft |
```

---

## Tier Classification

Every PBD must specify a tier (1-3) based on strategic importance:

| Tier | Definition | Examples |
|------|------------|----------|
| **Tier 1** | Strategic foundation — enables future capabilities, closes GA blockers, unlocks key accounts | NGA migration, Dynamic Guidance Plans, Multi-agent orchestration |
| **Tier 2** | High-value adoption driver — measurable customer impact, competitive parity | Multi-intent detection, Knowledge grounding, Voice channel expansion |
| **Tier 3** | Feature enhancement — improves existing capability, fills edge case gaps | Plan history UI, Custom plan templates, Plan export |

**Tier determines:** Inspection rigor, eng allocation priority, PMM support, exec visibility.

---

## Research & Evidence

Before drafting, gather:

1. **Customer signal** — Which customers need this? What did they say? (Slack, call notes, Google Drive)
2. **Field feedback** — What are FDEs/CSMs reporting? (FDE Pioneer channel, customer call notes)
3. **Competitive intel** — What do competitors offer? (From competitive-intel guide)
4. **Platform readiness** — What's already built that this leverages? (APIs, services, infra)
5. **Related PRDs** — What other PRDs overlap or depend on this? (Portfolio cross-reference)

**Research depth:**
- Always search Slack (customer channels, eng channels, PM channels)
- Always check existing PRDs/PBDs for overlap
- Read related Google Docs (requirements docs, gap analyses, call notes)

**Sources (for SRA):**
- Slack: #service-plans-field-feedback, #cx-feedback-service-plans, #service-plans-product-ai-collab
- Drive: Customer Call Notes folder, Beta Program Docs folder
- PRD Portfolio: https://git.soma.salesforce.com/pages/chad-goldsmith/sra-prds/

---

## Workflow

### Step 1: Understand the Program

Ask the user (batch into one confirmation message):
1. **Program name** — What's the initiative called?
2. **Release** — Target release number (default 264)
3. **Tier** — 1 (Strategic), 2 (High-value), or 3 (Enhancement)
4. **Problem** — What's broken/missing?
5. **Customer signal** — Who needs this? Any specific accounts/evidence?
6. **Output** — Just PBD, or PBD + Pretotype? (Pretotype requires `/pm-pretotype` skill)

**Never ask more than one message of questions.** Infer what you can from the user's prompt, confirm once, proceed.

### Step 2: Research

Run in parallel:
1. **Slack search** — Customer signal, field feedback, eng discussions
2. **PRD portfolio scan** — Check for overlap with existing PRDs/PBDs
3. **Google Drive search** (if relevant docs mentioned) — Requirements docs, call notes

**Research depth:**
- New program = Full research (Slack + portfolio + Drive)
- Update existing PBD = Targeted research (only changed areas)
- Known context = None (user provides all context)

### Step 3: Draft the PBD

Use the 11-section structure above. Key principles:

**Executive Summary:**
- Lead with current state + gap (not solution)
- 2-4 paragraphs max
- Include target release + expansion plan

**ICP & Persona:**
- At least 2 personas (primary + secondary)
- Pain points should be specific, measurable, quoted from customer feedback
- Success metrics must be measurable (not "better experience" — "≥4.0/5.0 satisfaction")

**Problem Statement:**
- Numbered list of 2-4 problems
- Show how problems compound (problem 2 exists because problem 1 unsolved)

**Why It Matters:**
- Every row must have specific evidence (customer name, Slack link, doc reference)
- No generic claims ("customers want this" without citing who)

**Success Criteria:**
- Always include: Feature Adoption, Usage Depth, Business Impact
- Targets must be measurable (not "high adoption" — "60% within 90 days")

**Solution Overview:**
- ASCII diagram showing architecture flow
- Key Design Decisions explain WHY (not just WHAT)

**Workstreams:**
- Each workstream = one deliverable/milestone
- Owner should be specific team/person (not "TBD" unless truly unknown)

**Risks:**
- Use emoji (🔴 HIGH, 🟡 MEDIUM, 🟢 LOW) for visual scanning
- Mitigation must include contingency ("if mitigation fails, we...")

**Phase 1 Exit Criteria:**
- Concrete, testable criteria (not vague "validate design")
- Should reference pretotype validation (if applicable)

**Open Questions:**
- Only include questions that block decisions
- "Decision Needed By" should reference milestone (WS1 scoping, Phase 2 kickoff, etc.)

### Step 4: Save & Publish

1. **Save locally:** `~/.agents/artifacts/prds/pbd-{release}-{slug}.md`
2. **Copy to sra-prds:** `cp ~/.agents/artifacts/prds/pbd-{release}-{slug}.md ~/sra-prds/`
3. **Commit & push:**
   ```bash
   cd ~/sra-prds
   git add pbd-{release}-{slug}.md
   git commit -m "Add PBD: {Title} ({release})
   
   {Brief description of the program}
   
   Key elements:
   - {Element 1}
   - {Element 2}
   - {Element 3}
   
   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   git push
   ```
4. **Live at:** https://git.soma.salesforce.com/pages/chad-goldsmith/sra-prds/

### Step 5: Next Steps Prompt

After saving, prompt the user:

> **PBD created:** `pbd-{release}-{slug}.md`  
> **Live at:** https://git.soma.salesforce.com/pages/chad-goldsmith/sra-prds/
>
> **Next steps:**
> - Want me to create the **pretotype** (interactive HTML demo)? Use `/pm-pretotype` with this PBD as input.
> - Want me to create a **one-pager** (requirements doc)? Use `/sf-prd-writer` to derive from this PBD.
> - Ready to **update** this PBD? Just ask — I'll read it and apply incremental changes.

---

## Updating Existing PBDs

To update an existing PBD:
1. Read the current PBD from `~/sra-prds/pbd-{release}-{slug}.md`
2. Apply changes (replace sections, add to tables, update status fields)
3. Update `Document History` table with new row
4. Save, commit, push (same workflow as creation)

**Changes to track in Document History:**
- Section additions/removals
- Status updates (prototype: pending → done)
- Risk/dependency changes
- Phase 1 exit criteria updates

---

## Reference Implementation

**Example PBD:** `~/sra-prds/pbd-266-sra-multi-intent-detection.md`

This demonstrates:
- Complete 11-section structure
- Proper frontmatter
- ASCII architecture diagram
- Evidence-backed "Why It Matters" table
- Specific workstream breakdown
- Risk/mitigation with emoji severity
- Phase 1 exit criteria tied to pretotype
- Open questions for eng alignment

**Use this as a template** when creating new PBDs.

---

## Integration with Other Skills

**Before invoking sf-pbd-writer:**
- Use `/sra-expert` or `/cvs-sra-tracking` to gather context
- Use Slack search to pull customer signal

**After sf-pbd-writer:**
- Use `/pm-pretotype` to create the interactive pretotype
- Use `/sf-prd-writer` to derive one-pagers or full PRDs from the PBD

**Lifecycle:**
- Use `/sc-pdlc-audit` to validate PBD completeness before Phase 2 Inspection

---

## Customization (For Other Products)

This skill is built for **Service Rep Assistant** by default. To customize for other Salesforce products:

1. **Update product name** — Replace "Service Rep Assistant" with your product in Program Info template
2. **Update ICP dimensions** — Replace SRA-specific criteria (channels, case complexity) with your product's ICP
3. **Update competitive intel** — Replace SRA competitors (Cresta, Google CCAI) with your product's competitors
4. **Update success criteria** — Replace SRA-specific metrics (plan adoption, AHT reduction) with your product's metrics
5. **Update research sources** — Replace SRA Slack channels/Drive folders with your product's sources

---

## Key Principles

✅ **Evidence-first business case** — Every claim in "Why It Matters" must cite specific evidence  
✅ **Program-level, not feature-level** — PBDs cover initiatives with multiple workstreams  
✅ **Tier classification matters** — Tier 1 = strategic foundation, Tier 3 = enhancement  
✅ **Phase 1 exit criteria drive prototype validation** — Concrete, testable criteria  
✅ **Open questions = real blockers** — Only include questions that gate decisions  
✅ **Document history = change log** — Track all meaningful updates  

❌ **Don't over-solution** — PBD explains WHAT and WHY, not HOW (that's for PRDs)  
❌ **Don't skip research** — Customer signal and field feedback are mandatory  
❌ **Don't use vague metrics** — "High adoption" is not measurable, "60% within 90 days" is  
❌ **Don't create PBDs for single features** — Use one-pagers for individual features  

---

## Changelog

| Date | Change |
|---|---|
| 2026-07-10 | Initial skill creation — extracted from pm-pretotype, focused solely on PBD creation |
