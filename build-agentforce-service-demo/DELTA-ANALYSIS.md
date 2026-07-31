# Subagent Builder Delta Analysis

**Goal:** Identify what Alberto's skill does that yours doesn't, what yours does that his doesn't, and where they overlap — to build the **best subagent builder skill** by combining strengths.

---

## Capabilities: Alberto's Only

### 1. **Knowledge Article Analysis & Combine/Split Decision**
**What it does:**
- Takes multiple knowledge articles as input
- Analyzes each article's workflow (authenticate → identify → resolve → confirm)
- Determines if they're **variations of one concept** (combine into 1 subagent) or **fundamentally different workflows** (keep as separate subagents)
- **Forces explicit decision before generating output** — never auto-generates without user confirmation

**Output format:**
```
I've analyzed your knowledge articles. Here's what I found:

Articles reviewed:
- Credit Card Declined - Insufficient Funds
- Credit Card Declined - Suspected Fraud

Workflow analysis:
- Both follow: authenticate → check reason code → execute resolution → confirm
- Differ only in root cause (NSF vs fraud flag)

RECOMMENDATION: Combine into ONE subagent (Transaction Declined)

REASONING: Same workflow, different subtypes. List variations in description.

Proposed structure:
- Subagent Name: Transaction Declined
  Covers: insufficient funds, suspected fraud, travel blocks, incorrect CVV, daily limits

Shall I proceed?
```

**Why it's valuable:**
- Prevents over-fragmentation (too many subagents)
- Ensures each subagent is a meaningful category (not generic catch-all)
- User explicitly approves structure before detailed work begins

**Your skills DON'T have this.**

---

### 2. **KB-vs-No-KB Instruction Depth Rules**
**What it does:**
- Different instruction counts and detail levels depending on whether knowledge article exists

**Rules:**

| Scenario | Instruction Count | Detail Level |
|----------|------------------|-------------|
| **No KB article** | 6-10 instructions | **Full detail** — policies, conditionals, resolution steps spelled out chronologically |
| **Has KB article** | 3-5 instructions | **High-level only** — "execute corresponding standard procedure" (KB fills gaps at runtime) |

**Example (No KB):**
```
Instruction 1: Make sure customer provided: Full Name, Last 4 of card, Security Question answer. Ask for merchant name, amount, date.
Instruction 2: Check Available Credit and Account Balance vs transaction amount. Verify not in arrears or over limit. Check if Card Lock active.
Instruction 3: Search Authorization Log using card details. Locate decline entry to identify Response Code.
Instruction 4: Based on response code (NSF, Fraud, International, Invalid CVV, Status), execute corresponding procedure.
Instruction 5: Send Transaction Status Update email confirming block lifted or next steps.
```

**Example (Has KB):**
```
Instruction 1: Authenticate customer using required fields.
Instruction 2: Identify the decline reason code and execute the corresponding standard procedure from the knowledge article.
Instruction 3: Confirm resolution and send status update notification.
```

**Why it's valuable:**
- Prevents over-instructing when KB already has the detail
- SRA pulls procedural steps from KB at runtime (no need to duplicate in instructions)
- Instructions become high-level workflow outline, not step-by-step script

**Your skills have instruction guidance but NOT this explicit KB-vs-no-KB split.**

---

### 3. **Prescriptive Format Rules**
**What it does:**
- **Description ALWAYS starts with:** *"Guide service reps in helping customers resolve..."*
- **Scope ALWAYS ends with:** *"You must not handle inquiries outside of [subagent]."*
- Never instruct Service Assistant to "search" or "review" the knowledge base
- One instruction = one standalone, actionable step (no combining multiple processes)

**Your skills have description/scope guidance but NOT these exact template phrases.**

**NOTE:** Alberto's skill mentions knowledge articles as INPUT (analyzes existing articles to generate subagent config) but does NOT cover how to WRITE knowledge articles. That's your unique capability (see #11 below in "Your Skills Only" section).

---

### 4. **Grounding Source Methodology**
**What it does:**
- Requires reading 4 reference docs BEFORE generating output:
  - `best-practices.md` — design rules + 3 full worked examples
  - `generator-prompt.md` — original prompt
  - `topic-strategy.md` — instruction-writing guidance
  - `design-strategy.md` — reasoning-anchor model

**Why it's valuable:**
- Skill output is grounded in pre-written examples (not ad-hoc generation)
- Consistency across multiple subagent generations
- User can update reference docs to change generation style without editing the skill

**Your skills reference BEST-PRACTICES.md but don't have a "read these 4 docs first" step.**

---

### 5. **Output Limits by Scenario**
**What it does:**
- **No KB uploaded:** max 10 subagents (detailed instructions required)
- **KB uploaded:** max 6 subagents (high-level instructions only)

**Why it's valuable:**
- Prevents analysis paralysis (too many subagents generated at once)
- Forces prioritization

**Your skills don't have output count limits.**

---

### 6. **Worked Examples Embedded**
**What it does:**
- Includes 5 full worked examples in reference docs:
  - Credit Card Declined (no KB pattern)
  - Processing Returns (KB pattern)
  - Travel Documentation (KB pattern)
  - Payroll Issue (dynamic plans)
  - Benefits Enrollment (dynamic plans)

**Your skills reference pet-travel-demo and retail-return-demo but don't have inline worked examples in the skill itself.**

---

## Capabilities: Your Skills Only

### 1. **Action Configuration Detail**
**What it does:**
- Full action setup tables with every toggle documented:

| Setting | Value |
|---------|-------|
| **Invocable Method** | GetCustomerProfileAction.execute |
| **Agent Action Label** | Get Customer Profile |
| **Description** | Retrieves customer profile. {CLT: always use show_command.} |
| **Confirmation Required** | Off |
| **Progress Indicator** | Looking up customer profile... |

**Inputs:**

| API Name | Label | Require | Collect | Description |
|----------|-------|---------|---------|-------------|
| customerId | Customer ID | ☐ | ☐ | Resolved from messaging session if blank |

**Outputs:**

| API Name | Label | Filter | Show | Rendering |
|----------|-------|--------|------|-----------|
| profileCard | Profile Card | ✅ | ✅ | customerProfileOutput |
| customerId | Customer ID | ✅ | ☐ | — |

**Why it's valuable:**
- Exact Agent Builder configuration (not just instruction text)
- Input toggle guidance (Require vs Collect)
- Output toggle guidance (Filter vs Show vs Rendering)
- Ready-to-configure action (no guessing)

**Alberto's skill doesn't cover action configuration at all.**

---

### 2. **Input/Output Toggle Rules**
**What it does:**
- Explains what each toggle does and when to use it

**Input toggles:**

| Toggle | What it does | When to use |
|--------|-------------|-------------|
| **Require** | Action won't fire until this has a value | Use when action literally can't execute without it (e.g., record ID to query) |
| **Collect** | Planner asks human to provide before firing | Use when value MUST come from human (not context/prior actions) |

**Common patterns:**
- `Require: OFF, Collect: OFF` — Value from conversation context or prior actions (most common)
- `Require: ON, Collect: ON` — Mandatory AND human-provided (use sparingly)
- `Require: ON, Collect: OFF` — Mandatory but already have it (blocks if missing, doesn't prompt)

**Output toggles:**

| Toggle | What it does | When to use |
|--------|-------------|-------------|
| **Filter from Agent** | Planner can read, reference, pass to downstream actions | ON for: values downstream actions need (IDs, booleans), primary display payload |
| **Show in Conversation** | Renders in chat/sidebar for rep | ON for: human-readable results. OFF for: internal data (IDs, booleans) |
| **Output Rendering** | Selects Lightning Type for visual card | Set to Lightning Type name for CLT cards, leave blank for text |

**Why it's valuable:**
- New Agent Builder users don't understand these toggles
- Prevents common mistakes (showing raw IDs to reps, filtering outputs from planner)
- Design patterns documented (not just "check this box")

**Alberto's skill doesn't cover Agent Builder UI configuration.**

---

### 3. **Variable Mapping Architecture**
**What it does:**
- Documents two variable passing patterns: explicit (Map to Variable) vs implicit (description-based)
- Explains when to use which pattern

**Explicit (Map to Variable):**
- Action 1 output `customerId` → "Map to Variable" field = `customerId`
- Action 2 input `customerId` → Dropdown shows `customerId` variable → select it
- **Use when:** Fan-out architecture (one output used by multiple downstream actions)

**Implicit (Description-based):**
- Action description: "Requires petManifestId (output of Check Pet Manifest)"
- Planner reads description, passes value automatically
- **Use when:** Linear chain (A→B→C, each variable used once)

**Data Flow Map:**

| Source | Output | Target | Input | Binding Type |
|--------|--------|--------|-------|-------------|
| Action 1 | customerId | Action 2 | customerId | Variable mapping |
| Action 1 | loyaltyTier | Action 4 | loyaltyTier | Variable mapping |
| Action 2 | orderNumber | Action 4 | orderNumber | Variable mapping |

**Why it's valuable:**
- Explains WHY retail-return-demo uses explicit mapping (fan-out) vs pet-travel-demo uses implicit (linear)
- Not a mistake, it's an architectural choice based on flow complexity

**Alberto's skill doesn't cover variable passing.**

---

### 4. **CLT Card Setup**
**What it does:**
- Full guide for Custom Lightning Types (CLT-GUIDE.md)
- Lightning Type directory structure (schema.json + renderer.json)
- New format (API 67.0+): `componentOverrides` not `propertyBindings`
- LWC requirements (`lightning__AgentforceOutput` target)
- Output Rendering dropdown selection

**Why it's valuable:**
- Visual cards are a major demo differentiator
- CLT configuration is complex and poorly documented
- New format changed recently (old docs outdated)

**Alberto's skill doesn't mention CLT cards.**

---

### 5. **Demo Persona Embedding**
**What it does:**
- Every demo has a persona table:

| Field | Value |
|-------|-------|
| Customer | Lauren Chen |
| Key Attribute | Gold Key Rewards Member |
| Scenario Context | Patio umbrella crank jammed on first use |
| Route/Product | Montecito 10ft Cantilever Umbrella ($1,299) |

**Why it's valuable:**
- Makes demos repeatable (same persona every time)
- Rep knows the "character" they're playing
- Demo has narrative continuity

**Alberto's skill doesn't embed personas (it's CX-focused, not demo-focused).**

---

### 6. **Action Chain Prerequisites**
**What it does:**
- Documents execution order dependencies

| # | Action | Prerequisites | Key Outputs |
|---|--------|--------------|-------------|
| 1 | Get Profile | None (runs first) | customerId, loyaltyTier |
| 2 | Look Up Order | Action 1 (customerId) | orderNumber |
| 3 | Troubleshoot | Actions 1+2 (product context) | troubleshootingSteps |
| 4 | Process Return | Action 2 (orderNumber) | rmaNumber, replacementOrder |
| 5 | Apply Concession | Actions 1+4 (loyaltyTier, rmaNumber) | creditAmount, perks |

**Why it's valuable:**
- Visualizes dependency chain (can't run Action 4 without Action 2)
- Helps debug "why did this action skip?"
- Clear execution order

**Alberto's skill doesn't cover action ordering.**

---

### 7. **Context Variables**
**What it does:**
- Documents platform-injected variables

| Variable | Set by API | LLM Can Use | Maps To |
|----------|-----------|-------------|---------|
| currentRecordId | ✅ | ✅ | Gets Case ID automatically |
| messagingSessionId | ✅ | ✅ | Gets conversation ID automatically |

**Why it's valuable:**
- New users don't know these exist
- No need to pass Case ID manually (platform injects it)

**Alberto's skill doesn't mention Context Variables.**

---

### 8. **Demo Scripts by Channel**
**What it does:**
- Requires 3 separate scripts per demo:
  - `DEMO-SCRIPT-CASE.md` — Email case, CLT cards render, full UI
  - `DEMO-SCRIPT-MESSAGING.md` — Web chat/SMS, no CLT cards, text-only
  - `DEMO-SCRIPT-VOICE.md` — Phone call, verbal-only, no visual UI

**Why it's valuable:**
- Same subagent behaves differently per channel
- CLT cards don't work in messaging/voice (outputs narrated as text)
- Demo flow adjusts to channel constraints

**Alberto's skill doesn't cover channel variants (CX focus, not demo delivery).**

---

### 9. **SFDX Project Infrastructure**
**What it does:**
- Project setup: `sf project generate`, git init, remote add
- Auth: `sf org login web --alias mySDO`
- Deploy: `sf project deploy start --source-dir force-app`
- Demo data: `sf apex run --file skill/setup-data.apex`
- Profile XML rules (FLS, required fields, CRUD)

**Why it's valuable:**
- Can't demo without deployment working
- Common errors documented (DUPLICATE_DEVELOPER_NAME, INSUFFICIENT_ACCESS, etc.)

**Alberto's skill doesn't cover Salesforce deployment (it generates subagent config, not code).**

---

### 10. **Reset & Repeatability**
**What it does:**
- Idempotent data scripts (check-before-insert, upsert if exists)
- Reset command to restore demo to known state

**Why it's valuable:**
- Demos must be repeatable (run 10x in one day)
- Can't manually delete records between demos

**Alberto's skill doesn't cover demo data management.**

---

### 11. **Knowledge Article Best Practices & Structure**
**What it does:**
- Prescriptive article structure with required components:
  - **SCOPE & APPLICABILITY** block (5 components: Applies to, Models, Does NOT apply to, Warranty note, Common questions)
  - **Title format:** `[Content Type] — [Topic] — [Scope]` (e.g., "Troubleshooting — Cantilever Umbrella Crank — Williams-Sonoma Models")
  - **Content types:** Policy, Procedure, Reference, Troubleshooting
  - **Trigger phrases** at end of article (10+ customer-voice keywords)
- Article splitting rules:
  - One topic per article (don't mix Policy + Procedure)
  - Split customer-facing vs rep-facing content
  - Separate reference data from procedures
- Deployment process:
  - Batch creation scripts (Apex, file size limits)
  - Delete old articles → Create new → Publish
  - Verification query

**Example structure:**
```
Title: Troubleshooting — Cantilever Umbrella Crank — Williams-Sonoma Models

Summary: Steps to troubleshoot jammed, slipping, or non-functioning crank mechanism on Williams-Sonoma cantilever patio umbrellas including Montecito, Pacifica, Larnaca models. Covers grinding noises, handle spinning without engaging, canopy that won't stay open.

SCOPE & APPLICABILITY:
- Applies to: All Williams-Sonoma cantilever (offset) patio umbrellas with crank-operated tilt and lift mechanisms
- Models: Montecito, Pacifica, Larnaca, Napa Valley, Carmel
- Does NOT apply to: market umbrellas, beach umbrellas, or push-up pole umbrellas

[Body content with numbered steps, subsections]

Trigger Phrases: umbrella crank stuck, umbrella won't open, crank handle spinning, umbrella mechanism jammed, patio umbrella broken, cantilever umbrella problem, umbrella grinding noise, canopy won't stay open, crank slipping, Montecito umbrella issue
```

**Why it's valuable:**
- Knowledge articles are THE grounding source for SRA
- Poor article structure → poor retrieval → agent can't find answers
- Summary field drives search (must be in customer voice, not SEO keywords)
- Proper scope blocks prevent wrong article matches
- Trigger phrases improve recall (agent finds article when customer uses these words)

**Version 2 improvements:**
- Split 8 articles → 11 articles (one topic per article)
- Added proper SCOPE blocks (missing in v1)
- Separated Policy from Procedure (was mixed)
- Added "Common Questions This Article Answers" sections

**Deployment artifacts:**
- `KNOWLEDGE-ARTICLES.md` — article content (copy-paste ready)
- `README-KNOWLEDGE-V2.md` — structure rules, splitting rationale
- `create-knowledge-articles-v2.apex` (3 batches) — programmatic creation
- `publish-knowledge-articles.apex` — mass publish
- `delete-old-knowledge-articles.apex` — cleanup

**Alberto's skill doesn't cover knowledge article creation methodology.**

---

## Overlaps (Both Have, But Different Approaches)

### 1. **Instruction Writing Guidance**
**Alberto's approach:**
- KB vs no-KB split (3-5 instructions vs 6-10 instructions)
- Never say "search knowledge base" or "review knowledge base"
- Chronological order
- Conditional language ("If..., then...", "When..., then...")

**Your approach:**
- Action-driving vs gating vs render backstop (instruction types)
- One instruction = one standalone step
- Embedded in BEST-PRACTICES.md (not in-skill rules)

**Delta:**
- Alberto's is more prescriptive (exact instruction count)
- Yours is more action-centric (tied to Agent Builder action chain)

---

### 2. **Name/Description/Scope Format**
**Alberto's approach:**
- Description starts with: "Guide service reps in helping customers resolve..."
- Scope ends with: "You must not handle inquiries outside of [subagent]."
- Subtype variations listed in description

**Your approach:**
- Description similar but no required template phrase
- Scope includes explicit exclusions but no required closing phrase
- Demo-specific context embedded (not generic CX)

**Delta:**
- Alberto's has stricter templates (copy-paste ready)
- Yours is more flexible (demo-specific customization)

---

### 3. **Worked Examples**
**Alberto's approach:**
- 5 inline examples in reference docs (Credit Card Declined, Processing Returns, etc.)
- CX use cases (financial services, HR, travel)

**Your approach:**
- References to standalone demo repos (pet-travel-demo, retail-return-demo, financial-fraud-demo)
- Full SFDX projects, not just Name/Desc/Scope/Instructions

**Delta:**
- Alberto's examples are lighter weight (text-only, Agent Builder ready)
- Your examples are full implementations (code + metadata + data)

---

## Gaps Neither Covers

### 1. **Runtime Execution Troubleshooting**
**Missing:**
- Why do actions get skipped?
- Why does agent go straight to Action 3 instead of running Actions 1-2 first?
- How does Subagent Scope affect triggering?
- What's the difference between "agent didn't call the action" vs "action failed"?

**This is a major gap.** Both skills focus on DESIGN and CONFIGURATION, not DEBUG.

---

### 2. **Subagent Scope Crafting**
**Missing:**
- What keywords trigger this subagent vs another?
- How specific vs broad should Scope be?
- What happens if two subagents have overlapping scope?
- How does the planner decide which subagent to route to?

**Your BEST-PRACTICES.md might have this — need to check.**

---

### 3. **Testing & Validation Patterns**
**Missing:**
- How to test each action individually before chaining?
- How to verify variable passing worked?
- How to confirm CLT cards render (vs plain text)?
- Regression testing (after action changes, does demo still work?)

**Your Quick Verification Checklist is a start, but not comprehensive.**

---

### 4. **Common Agent Builder Bugs & Workarounds**
**Missing:**
- Output Rendering dropdown caching (must delete/re-add action to see new outputs)
- Creating actions inside subagent UI (doesn't appear in Asset Library)
- Flow variable changes not auto-refreshing in actions
- Success message language affecting when outputs display

**Your skills mention some of these, but not systematically.**

---

### 5. **Multi-Subagent Architecture**
**Missing:**
- When to split into multiple subagents vs one?
- How do subagents hand off to each other?
- Parent agent routing logic?
- General CRM / General FAQ baseline subagents?

**Alberto's skill mentions this (combine vs separate decision) but doesn't cover multi-subagent orchestration.**

---

## Recommendation: Build ONE Comprehensive Subagent Builder Skill

Merge the best of both into a single authoritative skill:

### **Phase 1: Design** (from Alberto's)
1. Gather input (KB articles or use case description)
2. Analyze workflows (combine vs separate decision)
3. Get user approval on structure before generating
4. Apply KB-vs-no-KB instruction depth rules
5. Output Name/Desc/Scope/Instructions (Agent Builder ready)

### **Phase 2: Configure** (from your skills)
6. Create SFDX project (if code needed)
7. Build actions (Apex/Flow) with input/output tables
8. Configure action toggles (Require/Collect, Filter/Show/Rendering)
9. Set up CLT cards (if visual outputs needed)
10. Map variables (explicit vs implicit patterns)
11. Document action chain prerequisites

### **Phase 3: Deploy** (from your skills)
12. Deploy metadata (`sf project deploy start`)
13. Run demo data script (idempotent)
14. Create demo persona (repeatable scenario)
15. Write channel-specific demo scripts (Case/Messaging/Voice)

### **Phase 4: Debug** (NEW — neither has this)
16. Test action chain (verify execution order)
17. Validate variable passing (check planner sees outputs)
18. Confirm CLT rendering (not plain text)
19. Troubleshoot skipped actions (Scope? Dependencies? Prerequisites?)
20. Document known bugs & workarounds

---

## Structure for New Skill

```
sf-demo-skills/
├── SKILL.md                      ← Main skill (phases 1-4)
├── SUBAGENT-DESIGN.md            ← Phase 1: Design (Alberto's rules)
├── SUBAGENT-CONFIGURE.md         ← Phase 2: Configure (your action tables)
├── SUBAGENT-DEPLOY.md            ← Phase 3: Deploy (your SFDX commands)
├── SUBAGENT-DEBUG.md             ← Phase 4: Debug (NEW — troubleshooting)
├── BEST-PRACTICES.md             ← Cross-cutting rules
├── CLT-GUIDE.md                  ← CLT card reference
├── references/
│   ├── worked-examples.md        ← Merge Alberto's 5 + your 3 demos
│   ├── instruction-templates.md  ← KB vs no-KB patterns
│   └── action-patterns.md        ← Common action configurations
```

**This becomes THE definitive subagent builder skill** — from blank slate to deployed demo.

---

## Next Steps

1. **Read your BEST-PRACTICES.md** — does it already have Scope crafting guidance?
2. **Read Alberto's 4 reference docs** — extract the instruction templates
3. **Merge into one skill** — phases 1-4 above
4. **Add debug section** — this is the biggest gap
5. **Test on new demo** — does it cover everything?

Want me to read your BEST-PRACTICES.md and start the merge? 🎯
