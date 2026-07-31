# Skill Sharing Preparation — Summary of Changes

**Date:** 2026-05-20  
**Prepared for:** Internal Salesforce PM org sharing  
**Skill:** `sf-prd-writer`

---

## What Was Changed

### 1. Parameterized Product-Specific Content

| Location | Before | After | Why |
|----------|--------|-------|-----|
| **Title section** (line ~7) | "Service Rep Assistant features" | "Salesforce products" + customization note | Makes clear it's adaptable |
| **Phase 1** (line ~123) | "All PRDs for Service Rep Assistant" | "All PRDs for Service Rep Assistant by default. (Customizable...)" | Signals it's product-agnostic |
| **Phase 3a** (line ~337) | "Chad's standard two-part structure" | "standard two-part structure" | Depersonalized |
| **Administrative table** (line ~369) | `Initiative Lead: [User's name]` | `Initiative Lead: TBD` | Removed hardcoded name |

### 2. Added Customization Guidance

**New section after "How It Works"** (line ~41):
- `## Setup & Customization` with 6 subsections:
  1. For SRA PMs (no changes needed)
  2. For Other Salesforce Product PMs
  3. Update Product Name
  4. Replace Slack Channel Registry
  5. Clear PRD Canvas Registry
  6. Replace Product Context Reference
  7. Time Investment (5 min minimal, 2-3 hours full)

**Customization notes added throughout:**
- SRA Channel Registry (Phase 2, line ~157): "Customization Note: This registry is specific to SRA..."
- PRD Canvas Registry (Phase 2b, line ~287): Shows example from original author, provides empty "Your registry starts here" table

### 3. Created Documentation Files

| File | Purpose | Key Sections |
|------|---------|--------------|
| **README.md** | Quick start & feature overview for new adopters | What It Does, Quick Start, Two PRD Formats, Lifecycle Model, Key Features (5), Example Session, Customization Guide (detailed), Best Practices (5), Anti-Solutioning Guidelines, Credits |
| **CHANGELOG.md** | Version history from v1.0 → v2.0 | Documents all features added since April 1 initial release through today's sharing prep. Shows evolution: portfolio cross-ref → two-stage lifecycle → comment review → batch mode → one-pagers → competitive intel → research depth → status dashboard → sharing prep |
| **examples/example-one-pager.md** | Sanitized one-pager showing output format | Full one-pager (Real-Time Context Refresh for AI Service Plans) with generalized customer names, no Slack links, note at bottom explaining it's an example |

### 4. Registry Handling

**PRD Canvas Registry** (Phase 2b, line ~287):
- **Before:** Single table with Chad's 8 SRA canvases
- **After:** 
  - Example block showing Chad's canvases as reference (commented as "Example from original author")
  - Separate "Your registry starts here" table (empty)
  - Note: "For new adopters: This table will be empty when you first fork..."
  - Skill auto-populates as you create canvases

### 5. What Was NOT Changed

✅ **Preserved all SRA-specific content** in the skill:
- 16 SRA Slack channels with IDs
- Competitive Intelligence Registry (Cresta, Sierra, Google CCAI, etc.)
- Product Context Reference (full SRA domain knowledge: editions, plan structure, prompt architecture, token budgets, roadmap)
- All 10 phases (execution flow is product-agnostic)
- All examples use SRA terminology

**Rationale:** SRA PMs use as-is. Other PMs replace these sections per customization guide. Better to show a complete working example than sanitize into generic templates.

---

## File Structure After Changes

```
sf-prd-writer/
├── skill.md                         # Main skill (adjusted, ~25K tokens)
├── README.md                        # NEW — Quick start & customization guide
├── CHANGELOG.md                     # NEW — Version history v1.0 → v2.0
├── SHARING-PREP-SUMMARY.md          # NEW — This file (what changed, checklist)
└── examples/
    └── example-one-pager.md         # NEW — Sanitized one-pager example
```

---

## Adoption Checklist for New PMs

When another PM forks this skill, they should:

- [ ] **5-minute setup** (minimal):
  1. Update product name in Phase 1 (line ~123)
  2. Clear PRD Canvas Registry "Your registry starts here" table (Phase 2b, line ~287)
  3. Test: `/sf-prd-writer One-pager for [feature]`

- [ ] **2-3 hour setup** (full):
  1. Replace Slack Channel Registry (Phase 2, line ~157) with your product's channels
  2. Replace Product Context Reference (bottom section, line ~1500+) with your product's domain knowledge
  3. Update Competitive Intelligence Registry (line ~1850) with your competitors
  4. Test full PRD creation workflow

- [ ] **After 1st PRD** (validate):
  1. Verify markdown saved to `.agents/artifacts/prds/`
  2. Create canvas: `/sf-prd-writer create the canvas`
  3. Verify canvas ID auto-appended to registry
  4. Test incremental update: `/sf-prd-writer Add a requirement about [X]`
  5. Test comment review: `/sf-prd-writer check comments`

---

## Sharing Recommendations

### Internal Channels to Announce
1. **Service Cloud PM Leads** — primary audience
2. **Agentforce PM Leads** — overlapping product area
3. **Service Assistant PM Leads** — SRA PM team (they can use as-is)
4. **Einstein PM Leads** — if AI product PMs are interested

### Sample Announcement Message

```
📝 New Internal Tool: AI-Powered PRD Writer Skill for Claude Code

I built a Claude Code skill that automates PRD drafting, Slack research, canvas management, and portfolio cross-referencing. It's saved me 4-6 hours per PRD across 8+ SRA PRDs.

**What it does:**
• Drafts full PRDs or one-pagers in minutes
• Auto-searches 16 Slack channels for evidence
• Cross-references your PRD portfolio to catch conflicts
• Manages Slack canvas lifecycle (create, incremental updates, comment review)
• Batch updates across multiple PRDs

**Originally built for SRA, but customizable for any Salesforce product.**

📂 Repo: [internal Salesforce GitHub link]
📖 README: Quick start, customization guide, examples

Try it:
/sf-prd-writer One-pager for [your feature]

Questions? DM me or ask in #service-assistant-pm-leads
```

### Demo Session (Optional)
Offer a 30-min live demo:
1. **Show workflow** — create one-pager, publish to canvas, check comments, expand to full PRD
2. **Show customization** — walk through README, explain 5-min vs. 2-3 hour setup
3. **Q&A** — answer adoption questions

---

## Maintenance Plan

As the original author, you may want to:

1. **Accept PRs from other PMs** who add features or fix bugs
2. **Version bump** when making breaking changes (follow CHANGELOG conventions)
3. **Keep Product Context Reference up to date** for SRA (or delegate to another SRA PM if you move to a different product)
4. **Monitor adoption** — check how many PMs are using it, gather feedback

Consider adding a **Contributors** section to README after other PMs fork/customize for their products.

---

## Known Limitations to Disclose

1. **Token budget** — skill.md is ~25K tokens. If Product Context Reference grows too large for other products, may need to split into separate file or use dynamic loading.
2. **Slack channel access** — new adopters need access to channels in their registry. If they don't have access, searches will return empty results (not fail, but no evidence).
3. **Canvas API quirks** — bold-text headers can't be replaced (destroys child content). Documented in Phase 6c, but may surprise new users.
4. **Research depth auto-detection** — defaults are smart but not perfect. Users can override with "skip research" or "do full research" in their request.
5. **GUS integration optional** — Phase 2a requires GUS MCP plugin. If not installed, skill skips gracefully.

---

## What to Communicate

✅ **This is production-ready** — battle-tested on 8+ PRDs, stable  
✅ **Customization is low-friction** — 5 min for basic, 2-3 hours for full  
✅ **SRA PMs can use immediately** — no setup needed  
✅ **Other PMs replace SRA-specific sections** — clear guidance in README  
✅ **Saves 4-6 hours per PRD** — measured time savings on SRA PRDs  
✅ **Living document model** — markdown source of truth, canvas for collaboration  
✅ **Portfolio-aware** — prevents duplicate/conflicting PRDs  

---

## Next Steps

1. ✅ **Adjustments complete** — skill.md updated, docs created
2. **Push to internal Salesforce repo** — add to your org's shared skills directory
3. **Announce in PM channels** — use sample message above or customize
4. **Offer demo session (optional)** — 30-min walkthrough for interested PMs
5. **Gather feedback** — iterate based on adoption experience

---

**Ready to share!** 🚀
