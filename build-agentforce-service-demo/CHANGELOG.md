# Skill Evolution Changelog

## v2.0 — Merged with Alberto's CX Subagent Methodology (2026-07-09)

**Major enhancement:** Integrated Alberto Ruiz's sra-subagent-generator skill patterns with Chad's action-driven demo builder to create one comprehensive subagent builder skill.

---

### Added from Alberto's sra-subagent-generator

1. **Combine vs Separate Decision Framework** (`SUBAGENT-DESIGN-GUIDE.md`)
   - Workflow analysis methodology
   - One-sentence test for validation
   - Common mistakes (over-fragmenting, catch-alls, combining unrelated)
   - Worked examples (Payroll, Benefits)
   - Quick decision tree

2. **KB-vs-No-KB Instruction Depth Rules** (added to `BEST-PRACTICES.md`)
   - **Pattern 1:** KB-Grounded (3-5 high-level instructions, KB fills gaps)
   - **Pattern 2:** No-KB/Action-Driven (6-10 detailed instructions, spell everything out)
   - **Pattern 3:** Hybrid (6-8 instructions, action-first + KB-assisted)

3. **Prescriptive Format Templates** (`INSTRUCTION-TEMPLATES.md`)
   - Copy-paste templates for all 3 patterns
   - Universal closing phrases (description opening, scope closing)
   - Conditional language patterns
   - Mandatory steps language
   - Never-say phrases
   - Best practices checklist

4. **5 CX Worked Examples** (`references/` directory)
   - Credit Card Declined (no-KB, 13 instructions)
   - Processing Returns (KB-grounded, 11 instructions)
   - Travel Documentation (KB-grounded, 8 instructions)
   - Payroll Issue (dynamic plans example)
   - Benefits Enrollment (dynamic plans example)

5. **Grounding Source Methodology**
   - Added 4 reference docs: alberto-best-practices.md, alberto-topic-strategy.md, alberto-design-strategy.md, alberto-generator-prompt.md
   - "Read all before generating" requirement
   - Consistency across multiple subagent generations

6. **Output Limits by Scenario**
   - No KB uploaded: max 10 subagents (detailed instructions)
   - KB uploaded: max 6 subagents (high-level instructions)

---

### Enhanced Existing Capabilities

**BEST-PRACTICES.md:**
- Added 3 new sections at top:
  1. Subagent Design Principles (naming, description format, scope format, combine vs separate)
  2. KB-vs-No-KB Instruction Depth Rules (explains WHY instruction counts differ)
  3. Universal Instruction Rules (format, never-say, best practices, mandatory steps)
- Existing Topics/Actions sections preserved (Alberto's rules enhance, don't replace)

**SUBAGENT-TEMPLATE.md:**
- Added Design Decision section (complete BEFORE filling template)
  - Step 1: List all articles/use cases
  - Step 2: Workflow analysis
  - Step 3: Combine or separate?
  - Step 4: Instruction depth pattern

**SKILL.md:**
- Added Grounding Sources section
- References all 4 Alberto docs + BEST-PRACTICES.md
- "Read all before producing subagent output"

---

### Retained Unique Capabilities (Chad's Only)

These differentiators were NOT in Alberto's skill and remain unique to sf-demo-skills:

1. **Action Configuration Detail**
   - Input/output toggle rules (Require vs Collect, Filter vs Show vs Rendering)
   - Action chain prerequisites
   - Variable mapping architecture (explicit vs implicit patterns)

2. **CLT Card Setup Guide** (`CLT-GUIDE.md`)
   - Lightning Types directory structure (schema.json + renderer.json)
   - New format (API 67.0+): componentOverrides not propertyBindings
   - LWC requirements (lightning__AgentforceOutput target)
   - Output Rendering dropdown selection

3. **Knowledge Article Creation Methodology** (`retail-return-demo/skill/`)
   - SCOPE & APPLICABILITY blocks (5 components)
   - Title format: [Content Type] — [Topic] — [Scope]
   - Content types: Policy, Procedure, Reference, Troubleshooting
   - Trigger phrases (10+ customer-voice keywords)
   - Article splitting rules (one topic per article, Policy vs Procedure)
   - Deployment process (batch scripts, delete → create → publish)

4. **SFDX Deployment Infrastructure**
   - Project setup (sf project generate, git init)
   - Auth (sf org login web)
   - Deploy (sf project deploy start)
   - Demo data (sf apex run, idempotent scripts)
   - Profile XML rules (FLS, required fields, CRUD)

5. **Demo Persona Embedding**
   - Repeatable scenarios with character details
   - Loyalty tiers, account types, scenario context

6. **Demo Scripts by Channel**
   - Case/Messaging/Voice variants
   - Channel-specific considerations (CLT cards work in Case, not Messaging/Voice)

7. **Context Variables**
   - Platform-injected (messagingSessionId, currentRecordId)
   - Documentation of what's auto-available

8. **Reset & Repeatability**
   - Idempotent data scripts (check-before-insert, upsert if exists)
   - Reset commands for demo repeatability

---

## Pattern Recognition Enhancement

### Before v2.0:
- Generic "with KB vs without KB" guidance
- No clear rules for instruction count
- Unclear when to combine subagents vs separate

### After v2.0:
**Pattern 1: Pure KB-Grounded (Alberto's Pattern)**
- 3-5 high-level instructions
- Knowledge articles exist with full procedural detail
- Instructions provide framework only (authenticate → identify → execute → confirm)
- Example: Transaction Declined, Processing Returns, Travel Documentation

**Pattern 2: Action-Driven / No-KB (Alberto's Pattern)**
- 6-10 detailed instructions
- No knowledge articles, or no KB for this workflow
- Instructions spell out all policies, conditionals, resolution steps
- Example: Credit Card Declined (13 instructions, no KB)

**Pattern 3: Hybrid (Chad's Pattern)**
- 6-8 instructions (mix)
- Most flow is Agent Actions, but some steps reference KB
- Example: Retail Return (Profile → Order → Troubleshoot [KB] → Return → Concession → Email)

**Key insight:** Pattern 3 is NOT violating Alberto's "3-5 for KB" rule — that rule applies to PURE KB-grounded flows. Action-driven demos with optional KB assist are a valid hybrid pattern.

---

## Success Criteria Achieved

✅ **Can generate pure KB-grounded subagents** (3-5 instructions, Alberto's pattern)  
✅ **Can generate action-driven subagents** (6-10 instructions, Chad's pattern)  
✅ **Explains WHY** it chose one pattern over another (KB exists? Actions involved?)  
✅ **Users get combine/separate analysis** before detailed output (SUBAGENT-DESIGN-GUIDE.md)  
✅ **All 8 worked examples referenced** (Alberto's 5 CX + Chad's 3 demos)  
✅ **BEST-PRACTICES.md is authoritative** (single source of truth)  
✅ **Instruction templates are copy-paste ready** (INSTRUCTION-TEMPLATES.md)

---

## File Structure After v2.0

```
sf-demo-skills/
├── SKILL.md                                  ← Main skill (references grounding sources)
├── BEST-PRACTICES.md                         ← Comprehensive rules (Alberto's + Chad's)
├── SUBAGENT-DESIGN-GUIDE.md                  ← NEW: Combine vs separate framework
├── INSTRUCTION-TEMPLATES.md                  ← NEW: Copy-paste templates by pattern
├── CHANGELOG.md                              ← NEW: This file
├── SUBAGENT-TEMPLATE.md                      ← Enhanced with design decision section
├── CLT-GUIDE.md                              ← Chad's unique (CLT card setup)
├── DEMO-PLANNER.md                           ← Chad's unique (questionnaire-driven spec)
└── references/
    ├── alberto-best-practices.md             ← NEW: 3 worked examples + guidelines
    ├── alberto-topic-strategy.md             ← NEW: Instruction-writing guidance
    ├── alberto-design-strategy.md            ← NEW: Reasoning-anchor model
    └── alberto-generator-prompt.md           ← NEW: Original prompt
```

---

## Implementation Timeline

**Phase 1: Extract & Copy** (Complete)
- ✅ Copied Alberto's 4 reference docs to references/
- ✅ Extracted 5 worked examples
- ✅ Git commit: "Add Alberto's grounding sources"

**Phase 2: Enhance Existing Files** (Complete)
- ✅ Updated BEST-PRACTICES.md (added 3 new sections)
- ✅ Updated SUBAGENT-TEMPLATE.md (added design decision section)
- ✅ Updated SKILL.md (reference grounding sources)
- ✅ Git commit: "Merge Alberto's design rules into BEST-PRACTICES"

**Phase 3: Create New Files** (Complete)
- ✅ Created SUBAGENT-DESIGN-GUIDE.md
- ✅ Created INSTRUCTION-TEMPLATES.md
- ✅ Created CHANGELOG.md
- ✅ Git commit: "Add combine/separate guide and instruction templates"

**Phase 4: Test & Iterate** (Next)
- [ ] Test on 3 scenarios (KB-grounded, action-driven, hybrid)
- [ ] Refine based on what works/doesn't
- [ ] Git commit: "Validate merged skill with test cases"

---

## Migration Notes

**If you have existing demos built with v1.0:**
- Your action-driven patterns are still valid (no changes needed)
- Your CLT cards still work the same way
- Your SFDX deployment process unchanged
- Your demos are "Pattern 3: Hybrid" (action-driven + optional KB)

**New demos should:**
1. Read BEST-PRACTICES.md (now includes Alberto's rules)
2. Use SUBAGENT-DESIGN-GUIDE.md to decide combine vs separate
3. Use INSTRUCTION-TEMPLATES.md for copy-paste ready formats
4. Fill SUBAGENT-TEMPLATE.md with Design Decision section completed first

---

## Version History

### v2.0 (2026-07-09)
- Merged with Alberto's sra-subagent-generator
- Added combine/separate framework
- Added KB-vs-no-KB depth rules
- Added instruction templates
- 5 CX examples + 3 demo examples = 8 total worked examples

### v1.0 (2026-06-01)
- Initial release
- Action configuration detail
- CLT card setup
- Knowledge article methodology
- SFDX deployment
- Demo personas
- Channel-specific scripts
- 3 demo examples (Pet Travel, Retail Return, Financial Fraud)

---

## Credits

**Alberto Ruiz** — sra-subagent-generator skill, CX subagent patterns, KB-grounding methodology  
**Chad Goldsmith** — Action-driven demos, CLT cards, SFDX infrastructure, knowledge article structure

**Merge by:** Claude Code (2026-07-09)
