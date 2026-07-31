# Skill Improvement Plan — Incorporating Alberto's Best Practices

**Goal:** Enhance your subagent builder skills with Alberto's proven methodology while keeping your unique strengths (action config, CLT cards, knowledge article structure, SFDX deployment).

---

## Phase 1: Extract Alberto's Core Assets

### 1.1 Copy His Reference Docs to Your Repo

```bash
# Copy Alberto's reference docs into your sf-demo-skills repo
cp ~/sra-ga-docs/skills/sra-subagent-generator/references/best-practices.md \
   ~/sf-demo-skills/references/alberto-best-practices.md

cp ~/sra-ga-docs/skills/sra-subagent-generator/references/topic-strategy.md \
   ~/sf-demo-skills/references/alberto-topic-strategy.md

cp ~/sra-ga-docs/skills/sra-subagent-generator/references/design-strategy.md \
   ~/sf-demo-skills/references/alberto-design-strategy.md

cp ~/sra-ga-docs/skills/sra-subagent-generator/references/generator-prompt.md \
   ~/sf-demo-skills/references/alberto-generator-prompt.md
```

**Why:** These are his grounding sources. Your skill can reference them as authoritative sources.

---

### 1.2 Extract His 5 Worked Examples

From `alberto-best-practices.md`, extract:
1. Credit Card Declined (no KB pattern)
2. Processing Returns (KB pattern)
3. Travel Documentation (KB pattern)
4. Payroll Issue (dynamic plans)
5. Benefits Enrollment (dynamic plans)

**Create:** `~/sf-demo-skills/references/worked-examples-cx.md` with these 5 examples

**Your existing examples:**
- Pet Travel Booking (action-driven, CLT cards)
- Retail Return (action-driven, knowledge-assisted)
- Financial Fraud Detection (flow-based)

**Combined:** 8 worked examples covering CX use cases + demo patterns

---

## Phase 2: Enhance Existing Files

### 2.1 Update BEST-PRACTICES.md

**Add these sections from Alberto's methodology:**

#### A. Subagent Design Rules (page 1)
```markdown
## Subagent Design Principles

### Naming & Scope
- **Broad enough** to be a meaningful category, but never a generic catch-all
  - ❌ "Account Issue", "Customer Issue" (too broad)
  - ✅ "Credit Card Declined", "Password Reset" (specific)
- **Singular concept** per subagent — never combine two
  - ❌ "Returns and Exchanges" (split into 2)
  - ✅ "Product Returns", "Product Exchanges" (separate)
- **No overlapping** subagents — each must be distinct for accurate classification
- **Never create** a subagent for something SRA already does automatically
  - ❌ "Draft Service Plan", "Summarize Case", "Resolve Case"

### Classification Description Format
- **Always start with:** "Guide service reps in helping customers resolve..."
- **List every subtype**, keyword variation, and common reason code
  - Example: "...declined credit card transactions. Questions are related to authorization failures, including declining reason codes such as insufficient funds, suspected fraud, incorrect card details, travel blocks, and daily spending limits."
- **Purpose:** One high-level subagent covers a wide range of related cases (not one subagent per variation)

### Scope Format
- **State what you DO:** "Your job is to assist service reps in [primary function]..."
- **State what you DON'T:** "You must not handle inquiries outside of [subagent topic]."
- **Always end with:** "You must not handle inquiries outside of [subagent]."

### AI Retrieval Optimization
- Every subagent must be **distinct and specific** — no broad/generic buckets
- Classification accuracy depends on clear boundaries between subagents
- Subagent description drives both:
  1. **Routing** — which subagent handles this conversation?
  2. **Knowledge search** — which articles are relevant?
```

---

#### B. KB-vs-No-KB Instruction Depth Rules (page 2)
```markdown
## Instruction Writing — KB-Grounded vs Action-Driven

### When Knowledge Article Exists (KB-Grounded)
**Instruction count:** 3-5 high-level instructions only
**Detail level:** Framework outline — SRA pulls procedural steps from KB at runtime

**Rules:**
- Do NOT write granular per-subtype instructions
- Use general framework language: "execute the corresponding standard procedure"
- Let the knowledge article fill gaps (you're writing the workflow, not the steps)
- Never instruct SRA to "search" or "review" the knowledge base (it does this automatically)

**Example:**
```
Instruction 1: Authenticate customer using required security fields.
Instruction 2: Identify the decline reason code and execute the corresponding 
               standard procedure from the knowledge article.
Instruction 3: Confirm resolution and send Transaction Status Update email.
```

---

### When No Knowledge Article (Action-Driven or No-KB)
**Instruction count:** 6-10 detailed instructions
**Detail level:** Full procedural detail — policies, conditionals, resolution steps

**Rules:**
- Write chronologically (step 1 → step 2 → step 3...)
- Include verification steps (required info, eligibility, authentication)
- Use conditional language: "If..., then...", "When..., then...", "Once you have..."
- Cover every branch explicitly (don't assume SRA will figure it out)
- One instruction = one standalone, actionable step
- Never combine multiple processes into one instruction

**Example:**
```
Instruction 1: Make sure the customer has provided Full Name, Last 4 digits of 
               the card, and Security Question answer. Ask for merchant name, 
               transaction amount, and date of the declined attempt.
Instruction 2: Check Available Credit and Account Balance against the transaction 
               amount. Confirm the account is not in arrears or over the credit 
               limit. Verify if Card Lock or Freeze is active.
Instruction 3: Search the Authorization Log using card details. Locate the specific 
               decline entry to identify the system Response Code.
Instruction 4: Based on response code (NSF, Fraud, International, Invalid CVV, 
               Card Status), execute the corresponding procedure to remove blocks, 
               clear flags, or advise customer on next steps.
Instruction 5: Send Transaction Status Update email confirming block lifted or 
               outlining next steps required.
```

---

### Hybrid Pattern (Your Retail Return Demo)
**Instruction count:** 6-8 instructions (mix of action-driven + KB-assisted)
**Use when:** Most flow is actions, but some steps use knowledge articles

**Your retail return pattern:**
- Actions: Profile, Order, Return, Concession, Email (5 instructions)
- KB-assisted: Troubleshooting (1 instruction referencing KB)
- Total: 6-7 instructions

**This is valid!** Not pure KB-grounded, not pure no-KB. You're action-driven with KB assist.

Alberto's "3-5 for KB" rule applies to PURE KB-grounded flows (all answers from KB, no actions).
Your demos are action-first with optional KB augmentation.
```

---

#### C. Universal Instruction Rules (page 3)
```markdown
## Universal Instruction Rules

### Format
1. **One instruction = one standalone, actionable step**
   - Don't combine "authenticate AND check eligibility" — split into 2
2. **Chronological order** — step 1 happens before step 2
   - Don't jump around or reference "earlier" steps
3. **Conditional language** for branches:
   - "If the customer reports X, then do Y"
   - "When the system shows Z, execute procedure A"
   - "Once you have confirmed W, proceed to step N"
4. **Never say:**
   - "Search the knowledge base" (SRA does this automatically)
   - "Review knowledge articles" (SRA does this automatically)
   - "Create a service plan" (SRA does this automatically)

### Best Practices
1. **Survey link** — where appropriate, include "thank the customer + send survey link"
2. **Concluding action** — final instruction should state what happens at the end:
   - "Send confirmation email with all details discussed"
   - "Update case status to Resolved"
   - "Provide customer with instructions document"

### Action-Specific Patterns
For demos with Agent Actions (not just KB):
- **Instruction 0 (Sort: 0):** Get customer profile (always first)
- **Instruction N-1 (Sort: N-1):** Final deliverable action
- **Instruction N (Sort: N):** Render backstop (ensures CLT cards display)
```

---

### 2.2 Create NEW File: SUBAGENT-DESIGN-GUIDE.md

This is Alberto's "combine vs separate" methodology:

```markdown
# Subagent Design Guide — Combine vs Separate Decision

**When to use:** You have multiple knowledge articles or use cases and need to decide:
- ONE subagent covering all variations? OR
- MULTIPLE separate subagents?

---

## The Analysis Process

### Step 1: Identify the Core Workflow
For each knowledge article or use case, extract the high-level workflow:
- Authenticate
- Identify root cause
- Execute resolution procedure
- Confirm outcome
- Send notification

### Step 2: Compare Workflows
Ask: Do these articles follow the **same general sequence of steps** but differ only in:
- Root cause?
- Condition type?
- Subtype of the same problem?

**If YES → COMBINE into one subagent**

**Example:**
- "Credit Card Declined - Insufficient Funds"
- "Credit Card Declined - Suspected Fraud"
- "Credit Card Declined - Travel Block"

All follow: authenticate → check reason code → execute resolution → confirm

**RECOMMENDATION:** ONE subagent (Transaction Declined) covering all 3 subtypes

---

**If NO → KEEP SEPARATE**

**Example:**
- "Process Product Return" (authenticate → verify order → issue RMA → apply concession)
- "Process Product Exchange" (authenticate → verify order → check availability → create exchange order)

Different workflows, different outcomes, different data requirements.

**RECOMMENDATION:** TWO separate subagents

---

## The One-Sentence Test

**Ask:** Can I describe all these use cases with one sentence starting with "Guide service reps in helping customers resolve..."?

**Example 1 (Combine):**
✅ "Guide service reps in helping customers resolve declined credit card transactions, including insufficient funds, suspected fraud, travel blocks, incorrect card details, and daily spending limits."

**Example 2 (Don't Combine):**
❌ "Guide service reps in helping customers resolve declined credit card transactions and process product returns."
→ These are two fundamentally different topics. Split into 2 subagents.

---

## Recommendation Format (Always Present to User)

Before generating detailed subagent output, present this analysis:

```
I've analyzed your knowledge articles. Here's what I found:

Articles reviewed:
- [Article 1 title/topic]
- [Article 2 title/topic]

Workflow analysis:
- [Article 1] describes: [brief workflow]
- [Article 2] describes: [brief workflow]

RECOMMENDATION: [Combine into X subagent(s) / Keep as Y separate subagents]

REASONING:
[Articles 1, 2] share the same general workflow (authenticate → identify → resolve)
and differ only in [root cause]. These are variations of the same concept and should
be ONE subagent with subtypes listed in the description.

OR

[Article 1] describes [action type] while [Article 2] describes [different action].
These are fundamentally different workflows and should be SEPARATE subagents.

Proposed structure:
- Subagent Name: [Name]
  Covers: [variation 1, variation 2, variation 3]

Shall I proceed with this structure?
```

**DO NOT generate detailed instructions until user confirms structure.**

---

## Common Mistakes

### Mistake 1: Over-Fragmenting
Creating one subagent per tiny variation:
- ❌ "Insufficient Funds Decline" (separate subagent)
- ❌ "Fraud Decline" (separate subagent)
- ❌ "Travel Block Decline" (separate subagent)

**Fix:** ONE "Transaction Declined" subagent covering all 3 as subtypes

### Mistake 2: Generic Catch-Alls
Creating overly broad subagents:
- ❌ "Account Issues"
- ❌ "Customer Problems"
- ❌ "Payment Inquiries"

**Fix:** Break into specific categories (Credit Card Declined, Payment Method Update, Billing Address Change)

### Mistake 3: Combining Unrelated Processes
Mixing fundamentally different workflows:
- ❌ "Returns and Exchanges" (different workflows, different outcomes)
- ❌ "Password Reset and Account Unlock" (different security implications)

**Fix:** Separate subagents even if they seem thematically related

---

## Design Patterns from Alberto's Examples

### Pattern: Variations of One Workflow → ONE Subagent
**Example:** Transaction Declined
- Subtype 1: Insufficient Funds (execute: advise customer, offer payment plan)
- Subtype 2: Suspected Fraud (execute: verify customer, lift fraud flag)
- Subtype 3: Travel Block (execute: note travel dates, remove block)

**Workflow is identical** (authenticate → ID reason → resolve → confirm)
**Only the resolution procedure differs** by subtype

### Pattern: Different Outcomes → SEPARATE Subagents
**Example:** Returns vs Exchanges
- Return: customer wants refund (issue RMA → refund payment)
- Exchange: customer wants different item (check availability → create new order)

**Workflows diverge** after identification step
**Outcomes are fundamentally different** (money back vs new product)
```

---

### 2.3 Update SUBAGENT-TEMPLATE.md

Add this section right after "Subagent Identity":

```markdown
## Design Decision (Complete Before Filling Template)

**If you're creating this from multiple knowledge articles or use cases:**

1. **List all articles/use cases** this subagent will cover:
   - [ ] Article/Use Case 1: [name]
   - [ ] Article/Use Case 2: [name]
   - [ ] Article/Use Case 3: [name]

2. **Workflow analysis:**
   - Article 1 workflow: [brief description]
   - Article 2 workflow: [brief description]
   - Common steps: [list]
   - Differences: [list]

3. **Decision:** ☐ Combine into ONE  ☐ Split into MULTIPLE
   - **Reasoning:** [Why? Same workflow with subtypes, or fundamentally different?]

4. **If combining:** List all subtypes in Classification Description
   - Example: "...including insufficient funds, suspected fraud, travel blocks, incorrect card details, and daily spending limits."

5. **Instruction depth:**
   - ☐ KB-Grounded (3-5 high-level instructions, KB fills gaps)
   - ☐ Action-Driven (6-10 detailed instructions, no KB)
   - ☐ Hybrid (6-8 instructions, mix of actions + KB-assisted steps)

**Complete this section BEFORE filling out the rest of the template.**
```

---

## Phase 3: Create New Skill Files

### 3.1 Create: ~/sf-demo-skills/INSTRUCTION-TEMPLATES.md

Extract Alberto's exact instruction templates for copy-paste:

```markdown
# Instruction Templates by Pattern

Copy-paste these templates when writing subagent instructions.

---

## Template 1: KB-Grounded Subagent (3-5 Instructions)

**Use when:** Knowledge article exists with full procedural detail

```
Instruction 1 (Sort: 1): Authenticate & Gather Context
Authenticate the customer using [required security fields]. Ask for [specific details 
about the issue] including [field 1], [field 2], and [date/time].

Instruction 2 (Sort: 2): Identify & Execute
Identify the [type/category/reason code] based on [system lookup or customer description]. 
Execute the corresponding standard procedure from the knowledge article.

Instruction 3 (Sort: 3): Confirm & Close
Confirm the resolution with the customer. [Optional: Apply any required concession or 
benefit.] Send [confirmation notification type] via [channel] confirming [outcome] or 
outlining next steps required.

[Optional] Instruction 4 (Sort: 4): Survey
Thank the customer for their time and send the post-interaction survey link.
```

---

## Template 2: No-KB / Action-Driven Subagent (6-10 Instructions)

**Use when:** No knowledge article, or action-heavy flow

```
Instruction 1 (Sort: 1): Get Customer Profile
[Action-driving text for profile lookup]

Instruction 2 (Sort: 2): Authenticate & Verify
Make sure the customer has provided [required field 1], [required field 2], and 
[required field 3]. Verify [eligibility condition] and confirm [status requirement].

Instruction 3 (Sort: 3): Gather Issue Details
Ask the customer for [specific detail 1], [specific detail 2], and [specific detail 3]. 
[If applicable:] Search [system/log] using [lookup fields] to locate [relevant record].

Instruction 4 (Sort: 4): Identify Root Cause
Check [system field 1] and [system field 2] against [condition]. Confirm [status check]. 
Locate the [record type] to identify the [classification field].

Instruction 5 (Sort: 5): Execute Resolution
Based on the identified [category/code/condition]:
- If [condition A], then [action A]
- If [condition B], then [action B]
- If [condition C], then [action C]

Instruction 6 (Sort: 6): Apply Concession (if applicable)
[Action-driving text for concession/perk/benefit based on customer tier or issue severity]

Instruction 7 (Sort: 7): Generate Deliverable
[Action-driving text for creating output — boarding pass, confirmation, RMA, etc.]

Instruction 8 (Sort: 8): Send Confirmation
Send [notification type] via [channel] confirming [outcome details] and [next steps if any].

[Optional] Instruction 9 (Sort: 9): Survey
Thank the customer and send the post-interaction survey link.

Instruction 10 (Sort: 10): Render Backstop
When an action has a renderable output, display the complete action output to the user 
without summarizing, modifying, or omitting any content. The output is always renderable; 
always use show_command. Do NOT convert the output to plain text.
```

---

## Template 3: Hybrid (Your Retail Return Pattern)

**Use when:** Most flow is actions, but one or two steps reference knowledge

```
Instruction 1 (Sort: 1): Get Profile
[Your existing profile lookup instruction]

Instruction 2 (Sort: 2): Look Up Order
[Your existing order lookup instruction]

Instruction 3 (Sort: 3): Troubleshoot (KB-Assisted)
When the customer describes a product issue, call Get Troubleshooting Steps action with 
the product name and issue description. Display the troubleshooting card. Ask: "Would you 
like to try these steps, or would you prefer to proceed with a warranty replacement?"

Instruction 4 (Sort: 4): Process Return (Action)
[Your existing return processing instruction]

Instruction 5 (Sort: 5): Apply Concession (Action)
[Your existing concession instruction]

Instruction 6 (Sort: 6): Send Confirmation (Action)
[Your existing email confirmation instruction]

Instruction 7 (Sort: 7): Render Backstop
[Your existing render instruction]
```

---

## Universal Closing Phrases

**Classification Description opening:**
"Guide service reps in helping customers resolve..."

**Scope closing:**
"You must not handle inquiries outside of [subagent topic]."

**Instruction 1 conditional example:**
"If the customer has not provided [field], ask for it before proceeding."

**Instruction N (final):**
"Send [notification] confirming [outcome] and [next steps]."

**Never say:**
- "Search the knowledge base"
- "Review knowledge articles"
- "Create a service plan"
- "Summarize the case"
```

---

### 3.2 Update: ~/sf-demo-skills/SKILL.md

Add this to the "Related Skills" section:

```markdown
## Grounding Sources

Before generating any subagent, read these reference docs (grounding material):

- `references/alberto-best-practices.md` — 3 worked examples from Alberto (Credit Card Declined, Processing Returns, Travel Documentation)
- `references/alberto-topic-strategy.md` — Instruction-writing guidance, KB-grounding depth
- `references/alberto-design-strategy.md` — Reasoning-anchor model, combine vs separate logic
- `BEST-PRACTICES.md` — Your comprehensive rules (includes Alberto's + your action/CLT patterns)
- `SUBAGENT-DESIGN-GUIDE.md` — Combine vs separate decision framework
- `INSTRUCTION-TEMPLATES.md` — Copy-paste templates by pattern (KB-grounded, action-driven, hybrid)

**Read all before producing subagent output** — they're the source material this skill reasons from.
```

---

## Phase 4: Test the Enhanced Skill

### Test Case 1: Pure KB-Grounded (Alberto's Pattern)
**Input:** "Create a subagent for credit card decline issues. Subtypes: insufficient funds, suspected fraud, travel blocks."

**Expected output:**
1. ✅ Combine/separate analysis ("These are variations, combine into ONE")
2. ✅ User approval prompt ("Shall I proceed?")
3. ✅ 3-5 high-level instructions (not 6-10 detailed)
4. ✅ Description starts with "Guide service reps..."
5. ✅ Scope ends with "You must not handle..."

---

### Test Case 2: Action-Driven (Your Pattern)
**Input:** "Create a subagent for pet travel booking. Actions: Get Profile, Check Pet Manifest, Book Paired Seats, Apply Loyalty Perk, Generate Boarding Pass."

**Expected output:**
1. ✅ Action chain table with prerequisites
2. ✅ 6-8 instructions (action-driving, not KB-grounded)
3. ✅ Input/output toggle guidance
4. ✅ CLT card configuration
5. ✅ Variable mapping table

---

### Test Case 3: Hybrid (Your Retail Return)
**Input:** "Create a subagent for product returns. Actions: Profile, Order, Process Return, Apply Concession, Send Email. Plus: Get Troubleshooting Steps (uses KB article)."

**Expected output:**
1. ✅ 6-7 instructions (mostly actions, one KB-assisted)
2. ✅ Instruction 3: "call Get Troubleshooting Steps action" (not "search KB")
3. ✅ Instructions 4-6: action-driving (not KB-grounded)
4. ✅ Acknowledges hybrid pattern (not pure KB, not pure no-KB)

---

## Phase 5: Document the Merge

Create `CHANGELOG.md` in sf-demo-skills:

```markdown
# Skill Evolution Changelog

## v2.0 — Merged with Alberto's CX Subagent Methodology (2026-07-09)

### Added from Alberto's sra-subagent-generator:
1. **Combine vs separate decision framework** (SUBAGENT-DESIGN-GUIDE.md)
2. **KB-vs-no-KB instruction depth rules** (added to BEST-PRACTICES.md)
3. **Prescriptive format templates** (INSTRUCTION-TEMPLATES.md)
4. **5 CX worked examples** (references/worked-examples-cx.md)
5. **Grounding source methodology** (read 4 reference docs before generating)
6. **Output limits by scenario** (max 6 or 10 subagents)

### Enhanced existing capabilities:
- BEST-PRACTICES.md now includes Alberto's subagent design rules
- SUBAGENT-TEMPLATE.md includes design decision section
- SKILL.md references Alberto's grounding sources

### Retained unique capabilities:
- Action configuration detail (input/output toggles)
- Variable mapping architecture
- CLT card setup guide
- Knowledge article creation methodology
- SFDX deployment process
- Demo persona embedding
- Channel-specific demo scripts

### Pattern recognition:
- **Pure KB-grounded:** Alberto's 3-5 instruction pattern
- **Action-driven:** Your 6-10 instruction pattern
- **Hybrid:** Your 6-8 instruction pattern (action-first + KB-assisted)

### Result:
One comprehensive subagent builder covering:
1. Design (Alberto's combine/split + KB rules)
2. Configure (your action tables + CLT)
3. Deploy (your SFDX + data)
4. Document (knowledge articles + demo scripts)
```

---

## Implementation Timeline

**Week 1: Extract & Copy**
- [ ] Copy Alberto's 4 reference docs to your repo
- [ ] Extract 5 worked examples
- [ ] Git commit: "Add Alberto's grounding sources"

**Week 2: Enhance Existing Files**
- [ ] Update BEST-PRACTICES.md (add 3 new sections)
- [ ] Update SUBAGENT-TEMPLATE.md (add design decision section)
- [ ] Update SKILL.md (reference grounding sources)
- [ ] Git commit: "Merge Alberto's design rules into BEST-PRACTICES"

**Week 3: Create New Files**
- [ ] Create SUBAGENT-DESIGN-GUIDE.md
- [ ] Create INSTRUCTION-TEMPLATES.md
- [ ] Create CHANGELOG.md
- [ ] Git commit: "Add combine/separate guide and instruction templates"

**Week 4: Test & Iterate**
- [ ] Test on 3 scenarios (KB-grounded, action-driven, hybrid)
- [ ] Refine based on what works/doesn't
- [ ] Git commit: "Validate merged skill with test cases"

---

## Success Criteria

You'll know the merge is successful when:

1. ✅ **You can generate pure KB-grounded subagents** (3-5 instructions, Alberto's pattern)
2. ✅ **You can generate action-driven subagents** (6-10 instructions, your pattern)
3. ✅ **The skill explains WHY** it chose one pattern over another
4. ✅ **Users get combine/separate analysis** before detailed output
5. ✅ **All 8 worked examples** are referenced (Alberto's 5 + your 3)
6. ✅ **BEST-PRACTICES.md is authoritative** (no need to read multiple docs)
7. ✅ **Instruction templates are copy-paste ready**

---

## What NOT to Change

Keep these unique to your skills (don't force Alberto's patterns):

1. **Action configuration tables** — his skill doesn't cover Agent Builder UI
2. **CLT card setup** — his skill doesn't mention Lightning Types
3. **Knowledge article structure** — his skill uses KB as input, doesn't teach KB authoring
4. **Variable mapping** — his skill doesn't cover action-to-action data flow
5. **SFDX deployment** — his skill is config-only, no code deployment
6. **Demo persona** — his skill is CX-focused, not demo delivery focused
7. **Channel scripts** — his skill doesn't differentiate Case vs Messaging vs Voice

These are YOUR differentiators. Keep them.

---

## Next Step

Want me to start Phase 1 (extract Alberto's reference docs and copy to your repo)? I can:
1. Read his 4 reference files
2. Copy them to `~/sf-demo-skills/references/`
3. Create the initial commit

Let me know! 🎯
