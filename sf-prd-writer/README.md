# Salesforce PRD Writer — AI Skill for Claude Code

**Automated PRD drafting, Slack research, canvas management, and portfolio cross-referencing for Salesforce PMs**

Originally built for **Service Rep Assistant** PRDs. Customizable for any Salesforce product.

---

## What It Does

This Claude Code skill automates the heavy lifting of PRD creation:

✅ **Drafts full PRDs or one-pagers** in minutes (not days)  
✅ **Searches Slack automatically** for customer evidence, engineering discussions, competitive intel  
✅ **Cross-references your PRD portfolio** to catch conflicts (overlapping features, token budget collisions, rollout sequencing)  
✅ **Integrates with Slack Canvas** for collaborative editing with UX/Eng/QE stakeholders  
✅ **Tracks changes incrementally** after canvas creation to preserve comment history  
✅ **Reviews canvas comments** and acts on feedback (accept → update PRD, reject → reply in thread)  
✅ **Batch updates** across multiple PRDs in one session  
✅ **Status dashboard** shows portfolio health (gaps, open questions, stale PRDs)

**Time savings:** ~4-6 hours per PRD (research + drafting + canvas management)

---

## Quick Start

### 1. Install the Skill

This skill is already in your Claude Code skills directory if you're reading this. If not:

```bash
# Copy to your Claude Code skills directory
cp -r sf-prd-writer ~/.claude/skills/
```

### 2. Basic Usage (No Customization)

If you're an **SRA PM**, you can use immediately:

```
/sf-prd-writer One-pager for [feature name]
```

The skill will:
- Search 16 SRA Slack channels for evidence
- Draft a one-pager with Problem, Customer Signal, Gap, Scope, etc.
- Save as markdown in `.agents/artifacts/prds/`
- When ready: `/sf-prd-writer create the canvas` to publish to Slack

### 3. Customization (For Non-SRA Products)

See [Customization Guide](#customization-guide) below.

---

## Two PRD Formats

| Format | When to Use | Output |
|--------|-------------|--------|
| **One-pager** | Early alignment with Eng/UX before investing in full PRD | ~80-150 lines. Sections: Problem, Customer Signal, Why This Matters, Gap (Today vs. Target), Who Benefits, JTBD, Scope, Success Metrics, Open Questions, Customer References. No Administrative table, no Appendix. |
| **Full PRD** | Scrum team handoff — bottoms-up planning | Part 1 (UX/Architect context) + Part 2 (scrum team detail). Full requirements, 20+ acceptance criteria, rollout strategy, test plan, NFRs, risks, dependencies. |

**Expansion path:** Start with a one-pager. When ready for scrum handoff: `/sf-prd-writer expand to full PRD`

---

## Lifecycle Model: Markdown-Only → Canvas

The skill has two lifecycle stages:

### Stage 1: Markdown-Only (Pre-Canvas)
- PRD exists only as a local `.md` file
- All edits are **clean rewrites** (no change markers, no strikethroughs)
- Rationale: No one else is commenting yet; churn markers make early drafts harder to read
- **Canvas creation is user-initiated** — the skill never auto-creates canvases

### Stage 2: Post-Canvas (Collaborative)
- Once you publish to canvas: `/sf-prd-writer create the canvas`
- All future edits are **incremental** (strikethroughs + `*Added DATE:*` markers)
- Preserves comment history and collaborator changes
- Both markdown and canvas stay in sync

**Comment review:**
```
/sf-prd-writer check comments on [PRD name]
```
Presents each comment with attribution, suggests accept/reject/reply, waits for your decision.

---

## Key Features

### 1. Slack-Backed Research (Phase 2)
Before drafting, the skill searches Slack for:
- Customer feedback (FDE/SE channels)
- Engineering validation (architecture discussions, feasibility)
- Competitive intel (other Agentforce teams building similar features)
- Prior art (historical PRDs, HLDs)
- Known blockers (bugs, GUS work items)

Evidence appears as inline quotes with Slack message links.

### 2. Portfolio Cross-Reference (Phase 2b)
Scans all your existing PRDs (local + canvas) for:
- **Dependency overlap** — shared dependencies need coordinated delivery
- **Token budget conflicts** — multiple PRDs adding grounding data
- **Scope overlap** — features that touch the same admin config
- **Rollout conflicts** — beta timelines competing for same customers
- **Synergy opportunities** — features better together

Output: `## Portfolio Cross-Reference` table in the Appendix

### 3. Canvas Management (Phase 5b, 6b, 7)
- **Create canvas** (user-initiated): `/sf-prd-writer create the canvas`
- **Incremental updates** after canvas creation (additive = append, conflicting = strikethrough + replace)
- **Comment review**: skill fetches comments, presents with attribution, applies your decisions
- **Always personal canvases** — you share manually with the right audience

### 4. Batch Mode (Phase 8)
Update multiple PRDs in one session:
```
/sf-prd-writer batch: [PRD A] add voice as P0, [PRD B] change beta to June, [PRD C] add edge case
```
Presents a change manifest for approval, then executes sequentially.

### 5. Status Dashboard (Phase 10)
```
/sf-prd-writer status
```
Shows:
- All PRDs with format, release, lifecycle stage, last modified, gaps, open questions
- **Needs Attention** alerts (high gap count, stale, unresolved questions)
- **Cross-PRD Alerts** (token budget conflicts, dependency overlaps, customer overlap)
- Actionable suggestions (check comments, complete gaps, expand to full)

---

## Example Session

```
> /sf-prd-writer One-pager for real-time plan re-grounding on case comments

Skill: Starting a 262 one-pager for real-time plan re-grounding. Sound right?

> Yes

[Skill searches 16 Slack channels, finds Meta and Singapore Airlines feedback, drafts one-pager]

Skill: ✅ Saved to .agents/artifacts/prds/sra-plan-regrounding-case-comments.md
      Ready: Problem, Customer Signal, Gap, Scope
      Needs input: Success metrics baseline

> Create the canvas

[Skill publishes to Slack canvas, transitions to post-canvas stage]

Skill: Canvas created: https://salesforce.enterprise.slack.com/docs/...
      From now on, changes tracked incrementally to preserve comments.

[3 days later, after UX/Eng review]

> /sf-prd-writer check comments

Skill: ## Comments: Real-Time Plan Re-Grounding (F0B...)
      
      Comment 1 — Jane (UX): "Should voice channel be P0?"
      Suggested action: Conflicting change (move voice from P1 to P0)
      
      Comment 2 — Alex (Eng): "Token budget concern — this adds 200 tokens"
      Suggested action: Additive (add constraint note to Requirements)

> Accept both

[Skill applies incremental updates to markdown + canvas, replies to both threads confirming]

Skill: ✅ Updated PRD and replied to comments
```

---

## Customization Guide

### For SRA PMs (No Changes Needed)
Use as-is. The skill is pre-configured with:
- 16 SRA Slack channels
- SRA competitive intel (Cresta, Sierra, Google CCAI, etc.)
- SRA product context (editions, plan structure, prompt architecture, roadmap)
- Example PRD portfolio (Chad's 8 canvases as reference)

### For Other Salesforce Product PMs

#### Step 1: Update Product Name
**File:** `SKILL.md`  
**Line:** ~123 (Phase 1)

```markdown
* All PRDs produced by this skill are for the **[Your Product Name]** product.
```

#### Step 2: Replace Slack Channel Registry
**File:** `SKILL.md`  
**Section:** Phase 2 → SRA Channel Registry (line ~157)

Replace the 16 SRA channels with your product's key channels:

```markdown
| Channel | ID | What it covers |
|---|---|---|
| [Your Product] Engineering | `C...` | Engineering discussions |
| [Your Product] PM Leads | `C...` | Roadmap, prioritization |
| FDE Collaboration | `C0AN1E181M3` | Field feedback (keep this one) |
| SE Collaboration | `C08E300HPUK` | Pre-sales feedback (keep this one) |
```

**How to find channel IDs:**
1. In Slack, right-click a channel → "Copy link"
2. The ID is the last segment: `https://salesforce.enterprise.slack.com/archives/C0A99FLAE1G` → `C0A99FLAE1G`

#### Step 3: Clear PRD Canvas Registry
**File:** `SKILL.md`  
**Section:** Phase 2b (line ~287)

The example registry shows Chad's 8 SRA canvases. When you fork:

1. Keep the empty "Your registry starts here" table
2. Remove or comment out the example registry above it
3. As you publish PRDs to canvas, the skill auto-populates your registry

#### Step 4: Replace Product Context Reference
**File:** `SKILL.md`  
**Section:** Product Context Reference (bottom ~1/3 of file, line ~1500+)

This section contains deep SRA domain knowledge:
- Product positioning
- Editions/licensing (E4S, A4S, etc.)
- Prerequisites (Data Cloud, Agentforce Builder, etc.)
- Building blocks vocabulary (Topics, Instructions, Actions)
- Plan structure (4-header format, step types)
- Prompt architecture (deliberation pattern, token budget)
- Roadmap (262, 264 releases)
- Competitive intelligence (Cresta, Sierra, etc.)

**Replace with your product's equivalent:**
- Positioning, editions, prerequisites
- Product vocabulary (object names, feature names)
- Architecture constraints (API limits, token budgets, performance benchmarks)
- Roadmap milestones
- Competitive landscape

**If you don't have this depth yet:** Start with a minimal stub and expand as you draft PRDs. The skill will still work — it just won't have as much grounding context.

#### Step 5: Update Competitive Intelligence Registry (Optional)
**File:** `SKILL.md`  
**Section:** Product Context Reference → Competitive Intelligence Registry (line ~1850)

Replace SRA competitors with your product's direct competitors. Keep the table format:

```markdown
| Competitor | Category | Key Capabilities | [Your Product] Overlap | Known Accounts | Positioning Against [Your Product] |
```

### Time Investment
- **Minimal** (product name + clear canvas registry): ~5 minutes
- **Full** (replace all SRA sections): ~2-3 hours
- **Worth it after:** Your 1st PRD (saves 4-6 hours per PRD thereafter)

---

## File Structure

```
sf-prd-writer/
├── SKILL.md              # Main skill definition (10 phases, product context)
├── README.md             # This file
└── examples/             # (Optional) Add sanitized example PRDs here
```

---

## Best Practices

### 1. Start with One-Pagers
One-pagers align Eng/UX/Arch on *problem, customer signal, scope* before investing in a full PRD. Expand to full later via Phase 9.

### 2. Research Depth Matters
The skill has 3 research depth modes:
- **None** — typo fixes, date changes (skip Slack search)
- **Targeted** — adding one requirement (1-2 targeted searches)
- **Full** — new PRD, expansion, major changes (all 16 channels + portfolio cross-reference)

Defaults are smart, but you can override: "Skip research for this change" or "Do full research before updating"

### 3. Canvas = Collaboration Surface
Markdown is source of truth (version control). Canvas is for UX/Eng/QE comments. The skill keeps them in sync.

### 4. Comment Review Cadence
Check weekly during active development:
```
/sf-prd-writer check comments
```

### 5. Batch for Efficiency
If you have 3+ changes across multiple PRDs, batch them:
```
/sf-prd-writer batch: [PRD A] X, [PRD B] Y, [PRD C] Z
```
Skill builds a manifest, waits for approval, executes sequentially.

---

## Anti-Solutioning Guidelines

The skill enforces outcome-based requirements writing:

❌ **Don't prescribe HOW:**
- "Create a REST API endpoint at /api/v1/plans"
- "Add an Apex class `PlanGenerationService`"
- "Use a database column `is_mandatory`"

✅ **Do describe WHAT:**
- "Reps can manually trigger plan generation when automated triggers don't fire"
- "System tracks which steps are mandatory vs. optional"
- "Plan generation uses up to 5 grounding sources per plan"

**Rationale:** Engineering is extremely sensitive to over-solutioning. PRDs focus on *problems, outcomes, constraints* — not implementation details.

---

## Changelog

| Date | Change |
|---|---|
| 2026-05-20 | Added Setup & Customization section. Parameterized product name, channel registry, canvas registry. Prepared for internal Salesforce sharing. |
| 2026-05-19 | Added Competitive Intelligence Registry, SRA Channel Registry, Google Drive folders, research depth routing, status dashboard (Phase 10), GUS integration (Phase 2a), structural fidelity check (Phase 3c), graceful tool failure handling. |
| 2026-05-05 | Added Phase 3b (one-pager format), Phase 9 (expand one-pager to full PRD). |
| 2026-04-23 | Added Phase 8 (batch mode), Phase 7 (comment review). |
| 2026-04-15 | Split Phase 6 into 6a (markdown-only clean rewrites) and 6b (post-canvas incremental updates). Two-stage lifecycle model. |
| 2026-04-01 | Initial skill creation by Chad Goldsmith for SRA PRDs. Phases 0–6, Product Context Reference. |

---

## Credits

**Original Author:** Chad Goldsmith (Service Rep Assistant PM, Salesforce)  
**Battle-Tested On:** 8+ SRA PRDs across releases 262-264  
**Open for Internal Use:** Customizable for any Salesforce product PM

---

## Questions?

Reach out in Slack: `#service-assistant-pm-leads` or DM Chad Goldsmith

Or just try it:
```
/sf-prd-writer One-pager for [your feature]
```

The skill will walk you through the rest.
