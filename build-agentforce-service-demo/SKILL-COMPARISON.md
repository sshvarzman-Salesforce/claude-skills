# Subagent Skill Comparison

**Alberto's Skill:** `sra-subagent-generator` (CX Persona focused)  
**Your Skills:** `retail-return-demo/skill/REBUILD-AGENT.md` (Demo build focused)

---

## Key Differences

### Alberto's Skill (sra-subagent-generator)

**Purpose:** Generate NEW subagents from scratch — analyzes knowledge articles or use cases, recommends structure, outputs Agent Builder-ready configuration.

**Workflow:**
1. **Gather Input** — Upload knowledge article or describe use case
2. **Analyze & Recommend** — Combine vs. separate decision, propose structure, WAIT for confirmation
3. **Apply Design Rules** — Specific rules for Name/Description/Scope/Instructions based on whether knowledge article exists
4. **Output Format** — Agent Builder ready-to-paste format

**Strengths:**
- ✅ **Prescriptive design rules** from Alberto's grounding sources (4 reference docs)
- ✅ **Knowledge-article-aware** — different instruction depth depending on whether KB exists
- ✅ **Explicit combine/separate decision** — forces analysis before generating output
- ✅ **Output limits** — max 10 subagents (no KB) or 6 subagents (with KB)
- ✅ **Real worked examples** — Credit Card Declined, Processing Returns, Travel Documentation, Payroll Issue, Benefits Enrollment

**Grounding Sources (Must Read Before Output):**
1. `references/best-practices.md` — design rules + 3 full worked examples
2. `references/generator-prompt.md` — original prompt
3. `references/topic-strategy.md` — instruction-writing guidance
4. `references/design-strategy.md` — reasoning-anchor model, dynamic plans

**Instructions Pattern:**

| Scenario | Instruction Count | Depth |
|----------|------------------|-------|
| **No knowledge article** | 6-10 instructions | **Full detail** — policies, conditionals, resolution steps spelled out chronologically |
| **Has knowledge article** | 3-5 instructions | **High-level only** — "execute corresponding standard procedure" (KB fills gaps at runtime) |

**Key Rules:**
- Description ALWAYS starts with: *"Guide service reps in helping customers resolve..."*
- Scope ALWAYS ends with: *"You must not handle inquiries outside of [subagent]."*
- Never instruct Service Assistant to "search" or "review" the knowledge base
- One instruction = one standalone, actionable step
- Chronological order (no jumping around)
- Conditional language: "If..., then...", "When..., then...", "Once you have..."

---

### Your Skill (REBUILD-AGENT.md)

**Purpose:** Rebuild/configure an EXISTING demo subagent — detailed action configuration, variable mapping, CLT cards, data flow architecture.

**Workflow:**
- Subagent identity table (Name, Description, Scope)
- Demo persona table (customer, scenario, product)
- Action chain table (6 actions with CLT, confirmation, prerequisites, outputs)
- Data flow map (variable mappings between actions)
- Variable chaining architecture explanation (why "Map to Variable" for fan-out pattern)

**Strengths:**
- ✅ **Action-level detail** — exact configuration for each action (type, confirmation, CLT, inputs/outputs)
- ✅ **Variable mapping architecture** — explicit fan-out pattern documentation
- ✅ **Demo persona embedded** — Lauren Chen, Gold tier, patio umbrella scenario
- ✅ **Data flow visualization** — source/target/binding type table
- ✅ **Architecture decision rationale** — why variable mapping vs description-based chaining

**Focus:**
- Not generating new subagents from scratch
- Documenting how an existing demo is configured
- Rebuild checklist for demo replication
- Action configuration validation

---

## Coverage Comparison

| Capability | Alberto's Skill | Your Skill |
|------------|----------------|-----------|
| **Generate new subagent from scratch** | ✅ Primary purpose | ❌ Not covered |
| **Analyze knowledge articles** | ✅ Compares multiple, recommends combine/split | ❌ Not covered |
| **Instruction-writing rules** | ✅ Prescriptive rules, worked examples | ⚠️ Embedded in instructions but not generalized |
| **Action chain configuration** | ❌ Not covered | ✅ Detailed tables |
| **Variable mapping** | ❌ Not covered | ✅ Fan-out architecture documented |
| **CLT card setup** | ❌ Not covered | ✅ Marked per action |
| **Demo persona** | ❌ Not covered | ✅ Lauren Chen scenario |
| **Knowledge article grounding** | ✅ Different rules for KB vs no-KB | ❌ Not covered |
| **Combine vs separate decision** | ✅ Explicit analysis step | ❌ Not covered |
| **Ready-to-paste output format** | ✅ Agent Builder format | ⚠️ Table format (not paste-ready) |

---

## Complementary Use Cases

**Use Alberto's skill when:**
- Starting from scratch (no existing subagent)
- Have knowledge articles to analyze
- Need to decide: one subagent or multiple?
- Want prescriptive instruction-writing rules
- Building CX-facing subagents (not demo-specific)

**Use your skill when:**
- Rebuilding an existing demo
- Need exact action configuration
- Documenting variable mapping architecture
- Validating demo setup completeness
- Replicating retail return demo pattern

---

## Recommendations

### 1. **Merge the instruction-writing rules into your demo skill**

Alberto's instruction rules are excellent and should be embedded in your REBUILD-AGENT.md:

**Add this section:**

```markdown
## Instruction Writing Rules (from Alberto's best practices)

### When NO knowledge article is grounded:
- Write **6-10 instructions** with full detail
- Spell out policies, conditional scenarios, resolution steps chronologically
- Use conditional language: "If..., then...", "When..., then...", "Once you have..."
- One instruction = one standalone, actionable step
- Never instruct Service Assistant to "search" or "review" the knowledge base
- Best practice: Include "thank customer + survey link" instruction where appropriate
- Best practice: Final instruction states concluding action (email, status update, instructions doc)

### When knowledge article IS grounded:
- Write **3-5 high-level instructions** only
- Use general framework language: "execute the corresponding standard procedure"
- Do NOT write granular per-subtype instructions — SRA pulls detail from KB at runtime
- Same best practices as above (survey link, concluding action)

### Universal Rules:
- Description ALWAYS starts with: *"Guide service reps in helping customers resolve..."*
- Scope ALWAYS ends with: *"You must not handle inquiries outside of [subagent]."*
- Never instruct Service Assistant to "search" or "review" the knowledge base
```

---

### 2. **Keep Alberto's skill for net-new subagent generation**

When you need to create a NEW demo or CX subagent from scratch:
1. Use Alberto's `sra-subagent-generator` skill to generate the subagent structure
2. Use your `REBUILD-AGENT.md` to document the action chain + variable mapping afterward

---

### 3. **Your retail return demo instructions are HYBRID**

Looking at your `UPDATED-INSTRUCTIONS.md`:
- You have **7 instructions** (more than Alberto's KB-grounded max of 5)
- But your instructions ARE high-level (not super granular)
- You're using knowledge article for troubleshooting
- BUT you're also using actions (not just KB)

**This is valid!** Your demo is:
- **Knowledge-grounded** for troubleshooting steps (Get Troubleshooting Steps action returns KB content)
- **Action-driven** for profile/order/return/concession/email (Apex actions, not KB)

So you're in a middle ground:
- Not pure KB-grounded (no knowledge article for returns/concessions)
- Not pure no-KB (troubleshooting does use KB content)

**Alberto's rules apply best to pure KB-grounded subagents.** Your action-driven pattern is different (and valid for demos).

---

### 4. **Profile/Order Lookup Skipping Issue**

Alberto's skill doesn't address this because it's an **action execution problem**, not a **subagent generation problem**.

Your issue is:
- Instructions say "do profile first, then order"
- Agent sees "order #00000197 and crank mechanism stuck" and jumps to troubleshooting
- Skips profile/order actions

**This is a runtime behavior issue, not a subagent design issue.**

Alberto's skill focuses on NAME/DESCRIPTION/SCOPE/INSTRUCTIONS format, not on:
- Variable mapping
- Action execution order
- User confirmation gates
- Output rendering (CLT cards)

**Those are Agent Builder configuration details** — which your REBUILD-AGENT.md DOES cover.

---

## Your Complete Skill Ecosystem

You actually have **THREE complementary skills**, not just one vs Alberto's:

### 1. **sf-demo-skills** (Universal Demo Builder)
**Location:** `~/sf-demo-skills/`  
**Purpose:** Universal build process for ANY Service Assistant demo

**Key files:**
- `SKILL.md` — SFDX setup, metadata deploy, SF CLI auth, Agentforce checklist
- `SUBAGENT-TEMPLATE.md` — Framework for NEW demo docs (Action Chain, Data Flow Map, Instruction tables)
- `BEST-PRACTICES.md` — Rules and patterns (38KB!)
- `CLT-GUIDE.md` — Custom Lightning Type card guide
- `DEMO-PLANNER.md` — Questionnaire-driven spec generator

**This is your BUILDER skill** — it creates the infrastructure (SFDX project, metadata, action configs).

---

### 2. **retail-return-demo/skill/REBUILD-AGENT.md** (Demo-Specific Config)
**Location:** `~/retail-return-demo/skill/`  
**Purpose:** Rebuild/configure the RETAIL RETURN demo specifically

**Built from:** `SUBAGENT-TEMPLATE.md` (sf-demo-skills)

**Key sections:**
- Subagent Identity (Product Troubleshooting and Returns)
- Demo Persona (Lauren Chen, Gold tier, patio umbrella)
- Action Chain (6 actions with CLT, confirmation, prerequisites)
- Data Flow Map (variable mappings)
- Variable Chaining Architecture (why "Map to Variable" for fan-out)

**This is your INSTANCE skill** — a filled template for one specific demo.

---

### 3. **Alberto's sra-subagent-generator** (CX Subagent Writer)
**Location:** `~/sra-ga-docs/skills/sra-subagent-generator/`  
**Purpose:** Generate NEW subagents from knowledge articles or use cases

**Grounding sources:**
- `references/best-practices.md` — design rules + 3 worked examples
- `references/generator-prompt.md` — original prompt
- `references/topic-strategy.md` — instruction-writing guidance
- `references/design-strategy.md` — reasoning-anchor model

**This is your GENERATOR skill** — it creates subagent NAME/DESCRIPTION/SCOPE/INSTRUCTIONS from scratch.

---

## How They Work Together

```
┌─────────────────────────────────────────────────────────┐
│ Alberto's sra-subagent-generator                        │
│ "Generate a subagent for Credit Card Decline issues"   │
│                                                         │
│ OUTPUT: Name, Description, Scope, Instructions          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ sf-demo-skills (Universal Builder)                      │
│ "Build SFDX project, deploy metadata, configure actions"│
│                                                         │
│ USES: SUBAGENT-TEMPLATE.md framework                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ retail-return-demo/skill/REBUILD-AGENT.md               │
│ "Here's the exact config for THIS demo"                │
│                                                         │
│ CONTAINS: Action chain, variable mapping, persona       │
└─────────────────────────────────────────────────────────┘
```

**Workflow:**
1. **Use Alberto's skill** → Generate subagent structure (Name/Desc/Scope/Instructions)
2. **Use sf-demo-skills** → Build SFDX project, create actions, deploy metadata
3. **Fill SUBAGENT-TEMPLATE.md** → Becomes your demo's REBUILD-AGENT.md
4. **Deploy + document** → Demo-specific skill for rebuilds

---

## Coverage Comparison (Updated)

| Capability | Alberto's Generator | sf-demo-skills (Builder) | retail-return-demo (Instance) |
|------------|--------------------|--------------------------|-----------------------------|
| **Generate new subagent from scratch** | ✅ Primary purpose | ❌ | ❌ |
| **Analyze knowledge articles** | ✅ Compares, recommends combine/split | ❌ | ❌ |
| **Instruction-writing rules** | ✅ Prescriptive (KB vs no-KB) | ✅ Embedded in BEST-PRACTICES.md | ⚠️ Embedded in instructions |
| **SFDX project setup** | ❌ | ✅ Primary purpose | ❌ |
| **Metadata deployment** | ❌ | ✅ CLI commands | ❌ |
| **Action chain configuration** | ❌ | ✅ SUBAGENT-TEMPLATE.md framework | ✅ Filled tables |
| **Variable mapping** | ❌ | ✅ Data Flow Map in template | ✅ Fan-out architecture documented |
| **CLT card setup** | ❌ | ✅ CLT-GUIDE.md | ✅ Marked per action |
| **Demo persona** | ❌ | ✅ Template section | ✅ Lauren Chen scenario |
| **Ready-to-paste output** | ✅ Agent Builder format | ⚠️ Template format | ⚠️ Table format |
| **Combine vs separate decision** | ✅ Explicit analysis | ❌ | ❌ |

---

## Key Insight: sf-demo-skills HAS Instruction-Writing Rules!

I missed this initially — your `BEST-PRACTICES.md` (38KB!) likely contains instruction-writing guidance.

Let me check if it overlaps with Alberto's rules or if they complement each other.

---

## Recommendations (Updated)

### 1. **Keep all three skills — they serve different phases**
- **Phase 1 (Design):** Use Alberto's generator → get Name/Desc/Scope/Instructions
- **Phase 2 (Build):** Use sf-demo-skills → SFDX setup, action config, CLT cards
- **Phase 3 (Document):** Fill SUBAGENT-TEMPLATE.md → becomes demo-specific REBUILD-AGENT.md

### 2. **Cross-reference instruction rules**
Check if `sf-demo-skills/BEST-PRACTICES.md` has instruction-writing guidance.

If it does:
- **Merge** Alberto's KB-vs-no-KB rules into your BEST-PRACTICES.md
- Make sf-demo-skills the single source of truth for demo builds
- Alberto's skill stays focused on CX subagent generation (not demo-specific)

### 3. **Your retail return demo is action-driven, not KB-grounded**
Alberto's rules are optimized for KB-grounded subagents. Your demo uses:
- **Actions** for profile/order/return/concession/email (not KB)
- **Knowledge** only for troubleshooting steps (partial KB use)

So you're in a hybrid pattern:
- **Action-driven:** Most of the flow (6 of 7 instructions)
- **KB-assisted:** Only troubleshooting (1 instruction)

This is valid for demos! Alberto's "3-5 instructions for KB-grounded" doesn't apply because you're not fully KB-grounded.

### 4. **Profile/Order Lookup Skipping Issue**
None of these skills address this because it's a **runtime execution problem**, not a **design/configuration problem**.

Your issue is:
- Instructions say "profile first, then order"
- Agent sees "order #00000197 and crank stuck" and jumps to troubleshooting
- Skips the first two actions

**This is Agent Builder behavior** — not subagent design, not action config, not instruction-writing.

**Solution space:**
- Subagent Scope (when does it trigger?)
- Variable dependencies (make downstream actions require profile/order outputs)
- Action prerequisites (block troubleshooting until profile/order complete)

**None of the three skills solve this** — it's a new problem space (runtime action execution order).

---

## Conclusion

**Alberto's skill is for:**
- Generating NEW CX subagents from KB articles
- Prescriptive instruction-writing for KB-grounded flows

**sf-demo-skills is for:**
- Building demo SFDX projects
- Action configuration
- CLT cards
- Demo-specific patterns

**retail-return-demo/REBUILD-AGENT.md is for:**
- Exact config for THIS demo
- Rebuild/replication checklist

**They're complementary phases of demo development:**
1. Generate subagent (Alberto's)
2. Build demo infrastructure (sf-demo-skills)
3. Document instance (REBUILD-AGENT.md)

**For your current issue:**
- None of these skills solve profile/order skipping
- Need to debug Agent Builder runtime behavior
- First fix: cards rendering (Output Rendering dropdowns)
- Second fix: action execution order (Scope? Dependencies? Prerequisites?)

Let me know when you're ready to tackle the cards! 🎯
