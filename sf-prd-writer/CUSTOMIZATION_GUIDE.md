# PRD Writer Skill - Customization Guide for Other Products

This guide identifies all the **Service Rep Assistant (SRA)-specific** sections in `SKILL.md` that you'll want to customize for your product.

---

## Quick Start: What to Customize

| Section | Lines | What to Change | Why |
|---|---|---|---|
| **Product name in description** | Line 2, 10 | Replace "Service Rep Assistant" with your product name | Appears in skill metadata and intro |
| **One-pager canonical reference** | Line 17 | Replace `F0B05DPJDED` with your reference doc (or remove) | Sets the structural pattern for one-pagers |
| **PRD Portfolio (Phase 0, Step 1)** | Lines 55-67 | Replace the example PRD list with your portfolio | Used for routing "which PRD?" questions |
| **SRA Channel Registry** | Lines 157-175 | Replace with your product's Slack channels | Where Phase 2 searches for evidence |
| **Google Drive Reference Folders** | Lines 179-192 | Replace Drive folder links with yours | Beta docs, prior PRDs, architecture references |
| **Record Companion Architecture Docs** | Lines 194-206 | Replace or remove — this is SRA's UI framework | Only relevant if your product has similar architecture docs |
| **PRD Canvas Registry** | Lines 242-257 | Replace with your canvas IDs (or start empty) | Tracks which PRDs have been published as canvases |
| **Product Context Reference (entire section)** | Lines 1233-1480 | **REPLACE ENTIRELY** — this is 100% SRA domain knowledge | Product positioning, editions, vocabulary, roadmap, technical architecture |
| **Competitive Intelligence Registry** | Lines 1440-1480 | Update competitors list for your market | Currently lists SRA competitors (Cresta, Google CCAI, Sierra, etc.) |

---

## Detailed Customization Instructions

### 1. **Skill Metadata (Lines 1-4)**

**Current:**
```yaml
---
name: sf-prd-writer
description: Draft comprehensive PRDs for Salesforce Service Rep Assistant features with Slack-based research
tools: [...]
---
```

**Change to:**
```yaml
---
name: [your-product]-prd-writer
description: Draft comprehensive PRDs for [Your Product Name] features with Slack-based research
tools: [...]
---
```

---

### 2. **Product Name Throughout (Lines 2, 10, 100)**

**Find and replace:** "Service Rep Assistant" → "[Your Product Name]"

**Locations:**
- Line 2: skill description
- Line 10: "Drafts a PRD for Salesforce Service Rep Assistant features..."
- Line 100: "All PRDs produced by this skill are for the **Service Rep Assistant** product."

---

### 3. **One-Pager Canonical Reference (Line 17)**

**Current:**
```markdown
Reference shape: `F0B05DPJDED` (Action Output-Driven Knowledge Re-Grounding)
```

**Change to:**
- Your own canonical one-pager canvas ID, OR
- Remove the reference entirely if you don't have one yet

---

### 4. **Example PRD Portfolio (Lines 55-67, Phase 0 Step 1)**

**Current:**
```markdown
> | # | PRD Title | Canvas | Release |
> |---|-----------|--------|---------|
> | 1 | Ground Message and Voice Plans on Related Records | `F0ATZJMT4B1` | 262 |
> | 2 | Ground on Agent Builder Profile Details | `F0ATP326N79` | 262 |
> | 3 | Ground Case Service Plan on DE Service Plan | `F0ART8QRAKD` | 262 |
> ...
```

**Change to:** Your product's PRD list (or start with an empty placeholder):
```markdown
> | # | PRD Title | Canvas | Release |
> |---|-----------|--------|---------|
> | 1 | [Your first PRD title] | [Canvas ID] | [Release] |
> | 8 | *New PRD* | — | — |
```

---

### 5. **SRA Channel Registry (Lines 157-175) — CRITICAL**

**Current:** 16 SRA-specific Slack channels + Agentforce platform channels.

**Change to:** Your product's key Slack channels for evidence gathering.

**Template:**
```markdown
| Channel | ID | What it covers |
|---|---|---|
| [Your Product Core] | `C...` | Core product channel — feature discussions, bugs, releases |
| [Your Product Engineering] | `C...` | Engineering discussions, architecture decisions |
| [Your Product PM Leads] | `C...` | PM leadership — roadmap, prioritization, strategy |
| [FDE Collaboration] | `C0AN1E181M3` | Forward Deployed Engineers — keep this; cross-product |
| [SE Collaboration] | `C08E300HPUK` | Solution Engineers — keep this; cross-product |
```

**Keep the Agentforce platform channels** if you use Agentforce:
- Agentforce (`C0981N8RC57`)
- Agentforce Builder (`C088HG7U448`)
- Agentforce Big Impact (`C07RDL9CLDR`)
- Agentforce Innovation (`C06DZ4J5T4K`)

**Remove SRA-specific channels:**
- A3 Record Companion (`C0A99FLAE1G`)
- Service Assistant for Conversations (`C08DEK0ND0B`)
- Service Assistant for Voice (`C09K1CCKL8J`)
- NGS Engineering (`C06NDLHQJD7`)
- Sox Engineering (`C02CLRPJT1R`)
- SPA SF Engineering (`C02P450NJ84`)
- SOBA Engineering (`C05UAR03WHY`)
- SOUP Engineering (`C041YHQ8LQ0`)
- Service Assistant Engineering (`C06TPK97CCE`)
- Service Assistant PM Leads (`C078Y9DEDEE`)
- Service Assistant Leads (`C07DVDVH26A`)

---

### 6. **Research Strategy by Channel Type (Lines 208-220)**

**Update the table** to match your new channel registry:

**Current:**
```markdown
| Customer feedback, field evidence | FDE Collaboration (`C0AN1E181M3`), SE Collaboration (`C08E300HPUK`) |
| Engineering feasibility, architecture | NGS Engineering (`C06NDLHQJD7`), Service Assistant Engineering (`C06TPK97CCE`), Sox/SPA/SOBA/SOUP per domain |
| Product strategy, roadmap, prioritization | PM Leads (`C078Y9DEDEE`), Leads (`C07DVDVH26A`) |
```

**Change to:**
```markdown
| Customer feedback, field evidence | FDE Collaboration (`C0AN1E181M3`), SE Collaboration (`C08E300HPUK`) |
| Engineering feasibility, architecture | [Your Eng Channel] (`C...`), [Your Arch Channel] (`C...`) |
| Product strategy, roadmap, prioritization | [Your PM Leads] (`C...`) |
```

---

### 7. **Google Drive Reference Folders (Lines 179-192)**

**Current:** SRA Beta Documents and Previous PRD Documents folders.

**Change to:** Your product's Drive folders (or remove if you don't have them):

```markdown
| Folder | Link | What it covers |
|---|---|---|
| [Your Product] Beta Documents | [Drive Folder](https://...) | Beta program docs — setup guides, customer onboarding |
| [Your Product] Previous PRDs | [Drive Folder](https://...) | Historical PRDs for your product |
```

---

### 8. **Architecture Docs Section (Lines 194-206) — Optional**

**Current:** Record Companion (A3) architecture — SRA's UI container.

**Options:**
- **Replace** with your product's architecture docs folder (if you have one)
- **Remove** this section entirely if you don't have product-specific architecture references
- **Rename** to "[Your Product] Architecture Documents"

---

### 9. **PRD Canvas Registry (Lines 242-257) — CRITICAL**

**Current:** Table of 8 SRA PRD canvases.

**Change to:** Start with an empty registry or add your existing canvases:

```markdown
| Canvas ID | PRD Title | Release |
|---|---|---|
| `F...` | [Your first PRD title] | [Release] |
| (Add as you create canvases) | | |

> **Maintaining this registry:** When you write a new PRD and publish it as a Slack canvas, append its canvas ID and title to this table.
```

**Why this matters:** The skill uses this registry to determine PRD lifecycle stage (markdown-only vs. post-canvas) and for portfolio cross-referencing.

---

### 10. **Product Context Reference (Lines 1233-1480) — REPLACE ENTIRELY**

This entire section is **100% SRA domain knowledge**. You must replace it with your product's context.

**Current sections to replace:**

#### **Product Positioning** (Lines 1233-1240)
Replace with your product's value proposition and positioning statement.

#### **Editions & Licensing** (Lines 1242-1258)
Replace with your product's edition/addon requirements.

**Example template:**
```markdown
| Requirement | Details |
|---|---|
| **Add-On (required)** | [Your add-on name] |
| **Base Edition (required)** | [Required editions] |
| **Prerequisites** | [List prerequisites] |
```

#### **Prerequisites** (Lines 1260-1267)
Replace with your product's technical prerequisites.

#### **Building Blocks Vocabulary** (Lines 1269-1283)
Replace with your product's domain terminology.

**SRA example:** Topics, Instructions, Actions, Eligibility Flow, Skills

**Your version:** Define the 5-10 key terms that appear in every PRD for your product.

#### **Product-Specific Technical Sections (Lines 1285-1430)**

**SRA has:**
- Guidance Plans vs. Dynamic Plans comparison
- Plan Output Structure (4-header structure)
- Plan Generation Pipeline (Detect → Plan → Outcome)
- Product Roadmap (258, 260, 262 releases)
- Prompt Architecture (3-tier privilege model)
- Plan Output JSON Schema
- Prompt Optimization Context (token budget, latency benchmarks)

**Replace with your product's technical context:**
- Key architectural patterns
- Data models or schemas
- API contracts
- Performance benchmarks
- Technical constraints (like SRA's 1,895 token budget)
- Release roadmap

#### **Beta Program Context** (Lines 1418-1423)
Replace with your product's beta program (or remove if not in beta).

---

### 11. **Competitive Intelligence Registry (Lines 1440-1480)**

**Current:** SRA competitors (Cresta, Google CCAI, Sierra, Decagon, Intercom Fin, Observe.AI).

**Change to:** Your product's competitors.

**Template:**
```markdown
| Competitor | Category | Key Capabilities | [Your Product] Overlap | Known Accounts | Positioning Against [Your Product] |
|---|---|---|---|---|---|
| **[Competitor 1]** | [Category] | [Capabilities] | HIGH/MEDIUM/LOW | [Accounts] | **Weakness:** ... **Strength:** ... **Play:** ... |
| **[Competitor 2]** | [Category] | [Capabilities] | HIGH/MEDIUM/LOW | [Accounts] | **Weakness:** ... **Strength:** ... **Play:** ... |
```

**Keep the usage instructions** (lines 1468-1480) — they're product-agnostic.

---

### 12. **Relevant Research Insights Template (Lines 466-480)**

**Current:** Lists SRA's competitors as examples.

**Change to:** Your competitors list.

```markdown
* External Competitive Research (include only those relevant to THIS feature)
  - **[Competitor 1]**: [specific overlapping capabilities]
  - **[Competitor 2]**: [specific overlapping capabilities]
  
* [Your Product] Differentiation for This Feature
  - How does this feature strengthen [Your Product]'s positioning?
  - What gap does it close that competitors currently exploit?
```

---

## Product-Agnostic Sections (Keep As-Is)

These sections work for any product — **do not change**:

- **Phase 0: Route the Request** (routing logic)
- **Phase 1: Understand the Feature Idea** (batched questions pattern)
- **Phase 2: Gather Context from Slack** (search strategy — just update channels)
- **Phase 2a: GUS Context** (GUS integration)
- **Phase 2b: Cross-Reference Your PRD Portfolio** (portfolio logic)
- **Phase 3a: Full PRD Draft** (template structure)
- **Phase 3b: One-Pager Draft** (template structure)
- **Phase 3c: Structural Fidelity Check** (one-pager validation)
- **Phase 4: Review for Over-Solutioning** (anti-solutioning guidelines)
- **Phase 5: Save and Deliver the PRD** (file saving logic)
- **Phase 5b: Canvas Creation** (Slack canvas integration)
- **Phase 5c: Google Doc Creation** (Google Docs export)
- **Phase 6: Updating an Existing PRD** (lifecycle management)
- **Phase 7: Comment Review & Response** (comment workflow)
- **Phase 8: Batch Mode** (multi-PRD updates)
- **Phase 9: Expand One-Pager to Full PRD** (expansion logic)
- **Phase 10: PRD Status Dashboard** (portfolio dashboard)
- **Key Principles** (PRD writing principles)
- **Usage Examples** (example invocations)
- **Changelog** (version history)

---

## Testing Your Customized Skill

After customization:

1. **Test Phase 2 research:** Invoke the skill and verify it searches your product's Slack channels (not SRA channels)
2. **Test portfolio routing:** Create a second PRD and verify Phase 0 routing works
3. **Test canvas creation:** Verify canvases are created and the registry updates correctly
4. **Test Product Context Reference:** Verify PRDs include your product's terminology, not SRA's

---

## Maintenance

When you add new PRDs, update:
1. **PRD Canvas Registry** (lines 242-257) — add canvas ID when published
2. **Example PRD list** (lines 55-67) — optional; update if you want the routing example to show real PRDs

---

## Questions?

If you're unsure whether a section is SRA-specific or product-agnostic:
- **SRA-specific** = mentions "Service Rep Assistant", "Dynamic Plans", "Record Companion", SRA channel names, SRA customers (Meta, EA, Humana), SRA competitors, or SRA architecture
- **Product-agnostic** = describes PRD structure, workflow phases, Slack/GUS/Google integration, or writing principles

When in doubt, check the **Product Context Reference** section — if it's in there, it's SRA-specific and should be replaced.
