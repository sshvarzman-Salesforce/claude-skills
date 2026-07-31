# Agentforce Service Assistant — Demo Build Best Practices

Source docs: Topics 101 (Feb 18, 2026), Knowledge Grounding 101 (Mar 5, 2026), Pet Travel Demo learnings (June 2026), Alberto's Subagent Best Practices (Jun 30, 2026), Alberto's Design Strategy (Jun 17, 2026)

Applies to all Service Assistant Dynamic Plans demos.

**Grounding sources:** Read `references/alberto-best-practices.md`, `references/alberto-topic-strategy.md`, `references/alberto-design-strategy.md`, and `references/alberto-generator-prompt.md` for the full source material behind these rules.

---

## Subagent Design Principles

*(From Alberto's best practices — foundational rules for all subagents)*

### Naming & Scope Rules

**What makes a good subagent name:**
- ✅ **Specific enough** to name the issue category clearly — "Credit Card Declined", "Product Returns", "Pet Travel Booking"
- ✅ **Broad enough** to serve as a meaningful category — not so narrow it only covers one exact subtype
- ❌ **Not a catch-all** — "Account Issue", "Customer Issue", "General Support" are too broad
- ❌ **Not agent functions** — "Draft Service Plan", "Summarize Case", "Resolve Case" (Service Assistant already does these)
- ✅ **Singular concept** — "Returns" and "Exchanges" are separate subagents, not "Returns and Exchanges"
- ✅ **No overlapping** — each subagent must be distinct for accurate classification

**Why this matters:** Service Assistant uses the subagent name + description + scope as the **reasoning anchor** for the entire dynamic plan. A vague subagent produces vague, unfocused plans.

---

### Classification Description Format

**Always start with:** "Guide service reps in helping customers resolve..."

**Purpose:** One high-level subagent can cover a wide range of related cases when you explicitly list variations in the description.

**What to include:**
- ✅ All subtypes of the issue (e.g., "insufficient funds, suspected fraud, travel blocks, incorrect card details")
- ✅ Keyword variations customers actually use
- ✅ Common reason codes or triggers
- ✅ Language employees/case records use, not just internal terminology

**Example — Transaction Declined:**
```
Guide service reps in helping customers resolve declined credit card transactions. 
Questions are related to authorization failures, including declining reason codes such as 
insufficient funds, suspected fraud, incorrect card details, travel blocks, and daily 
spending limits.
```

**Why this matters:** The description is the **primary matching signal**. Service Assistant:
1. Uses it to decide which subagent handles a case (routing)
2. Uses it to search knowledge articles (retrieval)

Listing subtypes creates a stronger semantic signal → more accurate case classification → better knowledge retrieval → more focused service plans.

---

### Scope Format

**Structure:**
1. State what the subagent DOES: "Your job is to assist service reps in [primary function]..."
2. State what it DOESN'T do: explicit boundaries
3. **Always end with:** "You must not handle inquiries outside of [subagent topic]."

**Example — Transaction Declined:**
```
Your job is to assist service reps in identifying the reasons behind declined transactions 
and providing the necessary steps to either allow the charge or secure the customer's 
account. You must not handle inquiries outside of declined transactions and account security.
```

**Why this matters:** Scope sets a **reasoning boundary** that:
- Prevents the agent from reasoning outside its intended domain
- Filters out irrelevant knowledge articles during retrieval
- Reduces guidance from unrelated context

---

### One Subagent for Many Variations

**Strategy:** You don't need a separate subagent for every subtype. One well-structured subagent covers many related cases.

**Example: Payroll Issue**
- Covers: missing paychecks, direct deposit errors, overtime miscalculations, incorrect deductions, W-2 discrepancies
- **Not 5 separate subagents** — ONE subagent with all variations listed in the description

**When to combine vs separate:**
Ask: Do these share the **same general workflow** (authenticate → identify → resolve → confirm)?
- **YES → Combine** into one subagent (list variations in description)
- **NO → Separate** into different subagents (fundamentally different processes)

**Example of SEPARATE subagents:**
- "Product Returns" (customer wants refund → issue RMA → refund payment)
- "Product Exchanges" (customer wants different item → check availability → create new order)

Different workflows, different outcomes → separate subagents.

---

## KB-vs-No-KB Instruction Depth Rules

*(From Alberto's topic strategy — critical for instruction count)*

### Pattern 1: Knowledge Article Exists (KB-Grounded)

**Instruction count:** 3-5 high-level instructions only  
**Detail level:** Framework outline — Service Assistant pulls procedural steps from KB at runtime

**Rules:**
- ❌ Do NOT write granular per-subtype instructions
- ✅ Use general framework language: "execute the corresponding standard procedure"
- ✅ Let the knowledge article fill gaps (you're writing the workflow, not the steps)
- ❌ Never instruct Service Assistant to "search" or "review" the knowledge base (automatic)

**Example — Transaction Decline (with KB):**
```
Instruction 1: Make sure the customer has provided required authentication: Full Name, 
               Last 4 digits of card, Security Question answer. Ask for merchant name, 
               transaction amount, and date of attempt.
Instruction 2: Check Available Credit and Account Balance vs transaction amount. Verify 
               Card Lock/Freeze is not active.
Instruction 3: Search Authorization Log using card details. Locate decline entry to 
               identify Response Code.
Instruction 4: Based on response code (NSF, Fraud, International, Invalid CVV, Card Status), 
               execute the corresponding standard procedure to remove blocks, clear flags, 
               or advise customer on next steps.
Instruction 5: Send Transaction Status Update email confirming block lifted or outlining 
               next steps required.
```

**Why 3-5 is enough:** Knowledge articles contain the detailed "how-to" for each subtype. Instructions provide the **general workflow logic**; knowledge articles provide the **specific procedural steps**.

---

### Pattern 2: No Knowledge Article (Action-Driven or No-KB)

**Instruction count:** 6-10 detailed instructions  
**Detail level:** Full procedural detail — policies, conditionals, resolution steps

**Rules:**
- ✅ Write chronologically (step 1 → step 2 → step 3...)
- ✅ Include verification steps (required info, eligibility, authentication)
- ✅ Use conditional language: "If..., then...", "When..., then...", "Once you have..."
- ✅ Cover every branch explicitly (don't assume Service Assistant will figure it out)
- ✅ One instruction = one standalone, actionable step
- ❌ Never combine multiple processes into one instruction

**Example — Credit Card Declined (no KB):**
*(See `references/alberto-best-practices.md` for full 13-instruction example)*

**Why 6-10 is needed:** No knowledge base to fill gaps, so instructions must spell out:
- All policies
- All conditional scenarios
- All resolution steps

---

### Pattern 3: Hybrid (Your Retail Return Pattern)

**Instruction count:** 6-8 instructions (mix of action-driven + KB-assisted)  
**Use when:** Most flow is actions, but some steps reference knowledge

**Your retail return pattern:**
- Actions: Profile, Order, Return, Concession, Email (5 instructions)
- KB-assisted: Troubleshooting (1 instruction referencing KB)
- Render backstop: 1 instruction
- **Total:** 7 instructions

**This is valid!** Not pure KB-grounded, not pure no-KB. You're action-driven with KB assist.

Alberto's "3-5 for KB" rule applies to **pure KB-grounded flows** (all answers from KB, no actions). Your demos are action-first with optional KB augmentation.

---

## Universal Instruction Rules

*(Applies to all patterns)*

### Format Rules

1. **One instruction = one standalone, actionable step**
   - ❌ Don't combine: "Authenticate AND check eligibility" → split into 2
   - ✅ Do separate: Instruction 1 = Authenticate, Instruction 2 = Check eligibility

2. **Chronological order** — step 1 happens before step 2
   - Don't jump around or reference "earlier" steps
   - Use sort order to enforce sequencing

3. **Conditional language** for branches:
   - "If the customer reports X, then do Y"
   - "When the system shows Z, execute procedure A"
   - "Once you have confirmed W, proceed to step N"
   - "Based on the type of discrepancy reported..."

4. **Never say:**
   - ❌ "Search the knowledge base" (Service Assistant does this automatically)
   - ❌ "Review knowledge articles" (Service Assistant does this automatically)
   - ❌ "Create a service plan" (Service Assistant does this automatically)
   - ❌ "Summarize the case" (Service Assistant does this automatically)

---

### Best Practices

1. **Survey link** — where appropriate, include "thank the customer + send survey link"
2. **Concluding action** — final instruction should state what happens at the end:
   - "Send confirmation email with all details discussed"
   - "Update case status to Resolved"
   - "Provide customer with instructions document"

---

### Mandatory Steps Language

For steps that MUST happen:
- "As a first step, [action]..."
- "You must first [action]..."
- "This step must always be in a plan for cases dealing with [data type]."
- "Always find this step in a plan."

**Example:**
```
Make sure the customer has provided the required authentication information: Full Name, 
Last 4 digits of the card, and Answer to Security Question. This step must always be in 
a plan for cases dealing with financial data.
```

---

## Topics Best Practices

*(Chad's original content — enhanced with Alberto's rules above)*

### Naming
- **Do:** Use precise, distinct labels that specify the exact case type — "Pet Travel Booking", "Return Request", "Transaction Declined"
- **Don't:** Use generic catch-all titles like "Case Resolution Assistance" or "General Support"
- **Why:** Service Assistant uses the topic name to categorize the case and form initial plan steps. A vague title means wrong or missing steps.

### Description & Scope
- **Classification Description:** Describe what types of questions and situations this topic covers. Be specific about the case category, related issues, and what triggers it. Explicitly list subtypes, keyword variations, and common reason codes so a single high-level subagent can cover a wide range of related cases.
- **Scope:** Define what the agent should and should NOT do. Explicitly call out boundaries. Always conclude with: "You must not handle inquiries outside of [subagent]."
- **Example:**
  ```
  Description: Assist service reps in helping customers book in-cabin pet travel,
  including manifest availability, carrier requirements, and loyalty perks.
  Questions are related to pet booking requests, flight manifests, and loyalty rewards.

  Scope: Your job is to assist service reps with pet travel bookings on Goldrush Airways
  flights. Do not handle baggage claims or flight changes.
  ```

### Instructions

#### Core Rules
- **One instruction = one task.** Never bundle multiple steps into one instruction.
- **sortOrder controls sequencing.** Instructions execute in sort order. Use this to enforce step progression.
- **Instructions are zero-config.** Just prompt text + sortOrder. No actions, Apex, FLS, or permission sets needed.

#### Sequencing & Ordering
- **The planner is non-deterministic.** It can skip steps, misfire, or execute without complete context. Instructions alone don't guarantee order.
- **Use explicit prerequisite language** in action descriptions to force ordering: "Before calling X, you must first call Y." The planner respects this phrasing.
- **Never use "proceed to [next step]" directives.** If there's a gating instruction between the current step and the target, the planner skips the gate. Let sort order handle sequencing.

#### Enforcing Sequential Chaining (Critical for Demos)

The planner will try to parallelize or skip steps unless you explicitly enforce sequence. Use **all three mechanisms together** for reliable chaining:

**1. Instructions: One instruction per action, in sort order, with temporal connectors**

Each instruction should explicitly reference what happened BEFORE it:

```
Sort 0: "When a customer reaches out about a product issue, first retrieve
their customer profile to understand their loyalty status."

Sort 1: "After identifying the customer, look up their most recent order
to find the specific product they are having issues with."

Sort 2: "Search knowledge articles for troubleshooting steps specific to
the product category and issue type the customer describes."

Sort 3: "If troubleshooting does not resolve the issue, process a return
or replacement based on the warranty status and the nature of the defect."

Sort 4: "Based on the customer's loyalty tier, apply an appropriate
concession to acknowledge the inconvenience."
```

**Key language patterns that enforce sequence:**
- "**first** retrieve..." (anchors as step 1)
- "**After identifying** the customer..." (requires prior step completion)
- "**If troubleshooting does not resolve**..." (conditional on prior step's outcome)
- "**Based on the customer's loyalty tier**..." (references prior step's output)

**2. Action descriptions: Explicit prerequisite declarations**

Every action (except the first) must declare its prerequisites:

```
"Before calling this action, you must first call Get WSI Customer Profile
and Look Up WSI Order. Requires orderNumber (output of Look Up WSI Order)."
```

**3. Data dependencies: Passthrough output→input bindings**

When Action 1 outputs `customerId` and Action 2 takes `customerId` as input, the planner MUST run Action 1 first. This is a hard data dependency, not just a prompt hint.

**The three-layer stack:**
| Layer | Mechanism | Strength |
|-------|-----------|----------|
| Instructions (sort order + temporal language) | Prompt-level sequencing | Soft — planner respects but can override |
| Action descriptions (prerequisite declarations) | Planning-level sequencing | Medium — planner reads these when building the plan |
| Data dependencies (output→input) | Structural sequencing | Hard — action literally cannot fire without the input |

**Use all three.** Any one alone is insufficient. Together they reliably chain 5+ actions in sequence.

**Anti-patterns that break chaining:**
- Generic instructions that don't reference prior steps ("Look up the order" without "After identifying the customer...")
- Action descriptions that don't declare prerequisites ("Returns product details" without "Requires customerId from Get Customer Profile")
- All inputs marked optional with no data dependency (planner can fire actions in any order)
- Using "proceed to" or "next, do" language (planner interprets this as permission to skip gates)

#### Gating Instructions
A gating instruction pauses the plan until the rep responds. No action fires — it just blocks.
```
Example: "If the customer profile shows any pet special needs, pause and tell
the rep to verbally acknowledge the special needs to the customer before
proceeding. Wait for the rep to confirm they have acknowledged it."
```
Use for: compliance moments, safety acknowledgments, manual verification steps.

#### Instruction Examples
- **Do:**
  ```
  Instruction 1: Confirm the customer has provided their flight number.
  Instruction 2: Check the pet manifest for available spots on the flight.
  Instruction 3: If a spot is available, secure the booking and confirm with the customer.
  ```
- **Don't:**
  ```
  Instruction 1: Check if there's room on the flight, book the spot, confirm with the
  customer, then check their loyalty tier and offer a lounge pass if eligible.
  ```

#### With Knowledge Grounding
- You only need 3-5 instructions. The knowledge articles fill in the detail via ADL grounding.
- Instructions should provide a general process overview only.
- Don't reference Knowledge Articles in instructions. Phrases like "Refer to the knowledge base" or "Reference the specific article" do NOT trigger knowledge search. Service Assistant handles that automatically via the data library.
- Overly granular instructions can *compete with* what the article says rather than complement it.

#### Without Knowledge Grounding
- Write detailed instructions covering all policies, conditional scenarios, and resolution steps.
- Include conditional paths: "If…then…", "When…then…", "Once you have…"
- Include verification steps (gathering info, checking eligibility, authenticating)
- Up to 10-13 detailed instructions is fine for complex workflows.

#### CLT / Structured Output Instructions
For actions that render Custom Lightning Type cards, instructions must include render directives:
```
"Display the complete action output to the user without summarizing, modifying,
or omitting any content. The output is always renderable; always use show_command.
Do NOT convert the output to plain text."
```
Without this, the planner flattens rich output to plain text.

### How Many Instructions?
| Situation | Recommendation |
|---|---|
| No knowledge grounding | As many as needed to fully describe the process (up to 13) |
| With knowledge grounding | 3-5 high-level instructions only |
| Action-heavy with CLT | 6-8 (includes render directives + gating) |

---

## Actions Best Practices

### Types Supported
| Type | When to Use |
|---|---|
| **Apex** (RECOMMENDED) | All custom demo actions. Full control over output shape, CLT rendering, MessagingSession resolution. Deploy via SFDX, configure by hand in Agent Builder. |
| **Flow** | Simple data reads/writes when Apex is overkill. No code deploy needed. But: harder to return CLT DTOs, harder to chain, less control over output schema. |
| **Prompt Template** | LLM-generated output (summaries, confirmation messages, formatted text). Build in Prompt Builder. |
| **Standard** | Built-in platform actions (Draft Email, Answer Questions with Knowledge). No build needed. |

> **Default to Apex.** Flows were the original demo pattern but Apex @InvocableMethod actions chain more reliably, render CLTs correctly, and handle MessagingSession Contact resolution cleanly. Flows still work for simple lookups but Apex should be your first choice for any demo with CLTs or multi-action chains.

### Action Descriptions (Critical for Chaining)

Action descriptions are the PRIMARY mechanism for sequencing. The planner reads them to decide what to call and when.

**Every action description should include:**
1. **What it does** — one sentence
2. **Prerequisite** — "Before calling this action, you must first call [X]"
3. **Key inputs and where they come from** — "Requires petManifestId (output of Check Pet Manifest)"
4. **Render directive** (if CLT) — "always use show_command. Do NOT convert to plain text."

**Example:**
```
Secures a pet cabin spot on the flight. Before calling this action, you must
first call Check Pet Manifest and confirm isAvailable=true. Requires
petManifestId (output of Check Pet Manifest), flightNumber, and petName.
Resolves the Contact from the messaging session if customerId is not provided.
```

### Data Flow Between Actions

> **Rule:** Do NOT rely on the LLM to "remember" output from Step A and type it into Step B. Bind steps together using Context Variables or explicit output→input references so the pipe is deterministic, not probabilistic.

**Deterministic pipes (action-to-action outputs):**
- Reference the source action explicitly in the description: "Requires petManifestId (output of Check Pet Manifest)"
- Use Context Variables when available

**Acceptable LLM-mediated data (conversational):**
- Data the customer says (flight number, pet name, order ID) — the LLM is the right mediator here
- Data extracted from a profile card the LLM can read

### Confirmation (Human-in-the-Loop)
| Action Type | Confirmation | Why |
|---|---|---|
| Read-only lookups | **Off** | Silent background execution — no button |
| Write operations (booking, updates) | **On** | Rep must approve before data changes |
| CLT card renders | **Off** | Cards auto-display — no approval needed |
| Destructive actions (cancel, delete) | **On** | Always require explicit confirmation |

> **Design principle:** Read-only auto-runs; writes pause with a Confirmed button. No follow-up/quick-reply buttons exist in Dynamic Plans.

### Progress Indicator Messages
Every action should have a progress message shown while it executes:
- "Loading customer profile..."
- "Checking flight manifest..."
- "Securing pet spot on the manifest..."
- Keep them short, present tense, end with "..."

### Apex Actions (Recommended Pattern)

**Every demo action should follow this Apex pattern:**

```java
global without sharing class MyAction {
    global class Input {
        @InvocableVariable(label='...' description='...' required=false)
        global String myInput;
    }
    global class Response {
        @InvocableVariable(label='...' description='...')
        global MyOutput cardPayload;      // CLT DTO (if rendering a card)

        @InvocableVariable(label='...' description='...')
        global String passthroughField;   // For downstream action chaining

        @InvocableVariable
        global Boolean success;

        @InvocableVariable
        global String errorMessage;
    }
    @InvocableMethod(label='...' description='... always use show_command ...')
    global static List<Response> execute(List<Input> inputs) { ... }
}
```

**Key rules:**
- `global without sharing` — required because EinsteinServiceAgent User has no sharing access
- All inputs `required=false` — let the action resolve internally (especially Contact via MessagingSession)
- Return BOTH a CLT DTO (for card rendering) AND passthrough fields (for action chaining)
- Passthrough fields (customerId, loyaltyTier, orderNumber) let downstream actions receive data deterministically without relying on the LLM to extract it from the card JSON

**MessagingSession Contact Resolution (include in every first action):**

```java
private static String resolveContactId(String customerId, String sessionId) {
    String contactId = customerId;
    if (String.isBlank(contactId) || !contactId.startsWith('003')) contactId = null;
    // Try messaging session
    if (String.isBlank(contactId) && !String.isBlank(sessionId)) {
        List<MessagingSession> ms = [SELECT EndUserContactId FROM MessagingSession WHERE Id = :sessionId LIMIT 1];
        if (!ms.isEmpty()) contactId = ms[0].EndUserContactId;
    }
    // Fallback: most recent active session
    if (String.isBlank(contactId)) {
        List<MessagingSession> ms = [SELECT EndUserContactId FROM MessagingSession WHERE Status = 'Active' ORDER BY CreatedDate DESC LIMIT 1];
        if (!ms.isEmpty() && ms[0].EndUserContactId != null) contactId = ms[0].EndUserContactId;
    }
    return contactId;
}
```

**CLT DTO pattern (single-JSON-field):**

```java
@JsonAccess(serializable='always' deserializable='always')
global class MyOutput {
    @AuraEnabled
    global String payloadJSON;  // ONE field, all data as serialized JSON

    global MyOutput(String payloadJSON) { this.payloadJSON = payloadJSON; }
    global MyOutput() { this.payloadJSON = ''; }
}
```

**Why single field:** Multiple `@InvocableVariable` fields get flattened into separate text outputs by Agent Builder introspection, breaking CLT rendering. One `@AuraEnabled` field → Agent Builder sees it as a single typed output → Lightning Type dropdown appears.

**CLT actions — build BY HAND in Agent Builder:**
- Deploy Apex class + LightningTypeBundle + LWC via `sf project deploy start`
- Then manually: Agent Builder → Create Agent Action → Reference Action → Apex → Invocable Method
- Configure output: Show in conversation ✅, Filter from agent ✅, Output Rendering → select the Lightning Type
- CLT rendering is non-deterministic (~40%, GUS W-21683108). The `show_command` instruction helps but doesn't guarantee.

**CRITICAL: CLT Output Configuration Checklist**

For EVERY CLT card output, you MUST configure these three settings correctly:

| Setting | Required Value | What Breaks If Wrong |
|---------|---------------|---------------------|
| **Show in Conversation** | ✅ Checked | Card won't render to the rep |
| **Filter from Agent Action** | ✅ Checked | Agent narrates as plain text instead of showing card |
| **Output Rendering** | Lightning Type name selected | Shows raw JSON or text, not visual card |

**Most common failure:** "Filter from Agent Action" gets unchecked (during action edits, remove/re-add from Asset Library, or platform updates). Result: Cards that were working suddenly show as plain text bullets.

**Troubleshooting: Cards showing as plain text?**
1. Check Output Rendering → should show Lightning Type name (e.g., `RetailReturnResolutionOutput`)
2. Check Show in Conversation → should be ✅ checked
3. Check Filter from Agent Action → should be ✅ checked ← **most common issue**
4. If Filter is unchecked, re-check it, save, and test again

**Lightning Type description field limit: 255 characters.** Keep it concise. Include "always use show_command. Do NOT convert to text." — this IS read by the LLM.

### Flow Actions (Legacy — Use When Apex Is Overkill)
- Type must be **Autolaunched Flow (No Trigger)**
- All input/output variables must have **Available for Input / Available for Output** checked
- **Activate the flow before registering it as an action** — unactivated flows won't appear in action setup
- Keep flows focused: one flow = one action = one job
- Don't decrement inventory or make irreversible changes in demo flows — it means the demo can only run once
- **Limitation:** Flows cannot easily return CLT DTOs — use Apex if you need card rendering

### Prompt Template Actions
- Build in **Prompt Builder** (Setup → Prompt Builder)
- Use **Insert Resource** button to add data pills (`{!PetName}`, `{!FlightNumber}`) — never type them manually
- Keep output short and conversational — it goes directly into the chat
- Test in Prompt Builder preview before wiring to an action

---

## Action Sequencing Strategies

### Approach 1: Instruction-Based Sequencing (recommended for demos)

The LLM planner sequences actions using instructions + action descriptions.

**Pros:** Flexible, adaptive, visible to rep (HiL buttons), supports topic switching mid-flow, good for demos.
**Cons:** Non-deterministic, relies on prompt engineering, more points of failure.

**Mitigations:**
- Explicit prerequisite declarations: "Before calling X, you must first call Y"
- Output→input references: "Requires petManifestId (output of Check Pet Manifest)"
- Context Variables for deterministic data pipes
- Render directives for CLT actions

### Approach 2: Bundled Single-Action Logic (recommended for production)

Bundle the entire sequence into one Apex action or Flow. LLM calls it once; internal logic handles all steps.

**Pros:** Deterministic, faster (one LLM call), no planner misinterpretation, reliable.
**Cons:** No HiL between steps, less visible, less adaptive, worse for demos.

**When to use:** Fixed, predictable sequences. Production deployments where reliability > visibility.

### Decision Guide
| Need | Use |
|---|---|
| Show AI reasoning step by step | Instruction-based |
| Rep must approve individual steps | Instruction-based |
| Dynamic topic switching mid-flow | Instruction-based |
| Reliability over visibility | Bundled single action |
| Fixed sequence, never varies | Bundled single action |
| Production deployment | Bundled single action |

---

## GenAiPlannerBundle — Version Control Rules

### NEVER Deploy the Bundle to the Org

The planner bundle deploy is **all-or-nothing**. It overwrites:
- ALL actions in every topic (reverts hand-built CLT actions to flow stubs)
- ALL action output rendering config (flattens CLT → plain text)
- ALL actions not defined in the XML (deletes them)
- ALL instructions (reverts to whatever text is in the XML)

### All Agent Changes Are Done By Hand in Agent Builder

Changes to topics, instructions, actions, output rendering, confirmation toggles, context variables, and ADL mappings are made **manually in Agent Builder UI**. No exceptions.

The bundle XML in the repo is for **version control and documentation only** — a record of what's in the org, not a deployment artifact.

### Keeping the Repo in Sync (Retrieve → Commit)

After making changes in Agent Builder:
```bash
sf project retrieve start --source-dir force-app/main/default/genAiPlannerBundles --target-org mySDO
git add force-app/main/default/genAiPlannerBundles/
git commit -m "Retrieve bundle: [describe what changed]"
```

### If You Accidentally Deployed and Lost Actions
1. Roll back to the previous version in Agent Builder (if one exists)
2. OR re-add actions by hand using your rebuild doc
3. THEN retrieve and commit the fixed state

---

## Knowledge Grounding Best Practices

### What's Supported
- **Only Salesforce Knowledge** — not Unified Knowledge, not Enterprise Knowledge, not external sources
- **Only English articles** currently supported

### Knowledge Strategy for Demos

**Don't rely entirely on instructions.** Instructions tell the agent *what to do*; knowledge articles tell it *what to know*. Policy details, troubleshooting steps, and reference data belong in knowledge — not hardcoded in instructions or Apex.

**Two tiers of articles:**

| Tier | Purpose | Count | Example |
|------|---------|-------|---------|
| **Core** | Directly supports the action chain — retrieved during scripted flow | 2-4 | Troubleshooting steps, return policy, loyalty tiers |
| **Conversational** | Supports unscripted follow-up Q&A from rep or audience | 4-6 | Product care, shipping details, warranty details, sizing guides |

**Why conversational articles matter:**
- Demos that ONLY work on the scripted path look pre-programmed
- Audience WILL ask "what if the customer asks about X?"
- Conversational articles let you answer ANY follow-up live and show knowledge grounding working in real-time
- This is the "Conversation Intelligence" beat — proves the agent handles real conversations

**What makes a good conversational article:**
- Covers adjacent topics the customer might naturally ask about
- Written in customer-voice language (not internal jargon)
- Self-contained — answers the question fully without needing the scripted flow context
- Includes trigger phrases that match what a rep would type

**Planning conversational articles:**
Think about what the customer would ask AFTER the main issue is resolved:
- Product care/maintenance ("how do I take care of this?")
- Related logistics ("when will it arrive?", "is assembly included?")
- Policy clarifications ("does this credit work at other stores?")
- Upsell/alternative ("should I get a bigger one?")
- Account questions ("how did I get to this loyalty tier?")

### Article Authoring for ADL Grounding

#### One Article, One Topic
Never mix policies/procedures in one article. Retrieval pulls the whole article; mixed content dilutes the useful signal ("retrieval dilution").

#### Title Format
Use: `[Content Type] - [Specific Topic] - [Scope]`
```
Policy - In-Cabin Pet Travel - Goldrush Airways Domestic Flights
Reference - Pet Carrier Specifications - Goldrush Airways In-Cabin
```
The title IS the primary retrieval signal for the Data Library.

#### SCOPE & APPLICABILITY Block
Add a metadata block at the top of every article:
```
Topic: [what this covers]
Applies To: [products, tiers, channels]
Does NOT Apply To: [explicit exclusions]
Preconditions: [what must be true]
Outcomes: [what the rep achieves]
```
Gives the grounding retriever a fast match signal before the full article body.

#### Standalone Sections
Every section must stand alone — no relative references ("see the previous step"). The LLM may ground on one section chunk, not the full article. Chunks don't carry prior context.

#### Trigger Phrases
Add 5-10 "Common questions this article answers" at the end of every article. Written in customer voice — these are semantic retrieval hooks.
```
- Can I bring my dog on the plane?
- What size carrier do I need for my cat?
- How do I book a spot for my pet on the flight?
```

#### Formatting
- No emojis, heavy bolding, visual indicators, or internal metadata
- Use alphanumeric steps for procedures (1, a, b, c, 2, a, b, c)
- Non-sequential items use standard bulleted lists
- Clear heading hierarchy (H1-H6 in Knowledge rich text)
- Every section has a clear introduction providing context

### Article Content Requirements
- **Published and public** — articles must be active and visible
- **Clear titles and summaries** — use keywords that match what appears in case/chat records
- **Well-organized and specific** — vague articles produce vague plan steps
- **Up to date** — outdated articles = outdated plan steps
- **No conflicts with topic instructions** — if your topic says one thing and the article says another, the agent gets confused

### Data Library Field Selection
When configuring your knowledge data library in Agentforce Builder:

**Identifying Fields (pick max 2):**
- Recommended: **Title** and **Summary**
- These help Service Assistant find and group relevant articles for a case
- Choose fields that represent the general structure of your knowledge base

**Content Fields (pick multiple):**
- Recommended: **Answer**, **Detail**, **Question** + any relevant custom fields
- These are where the agent extracts step content from
- Rich text fields supported but must be under 255 characters and properly formatted

### Permissions Required

| Persona | What to Configure | What It Grants |
|---|---|---|
| **Setup Admin** | Knowledge User checkbox on user record + Data Cloud Architect perm set | Setup access to build the data library |
| **Service Rep** | Service Rep Knowledge Access (custom perm set) | Read, View All Records, View All Fields on Knowledge + Allow View Knowledge |
| **ServicePlanner User** | Agent Knowledge Access (custom perm set) | Allow View Knowledge + Read/View All on Knowledge + Data Category Visibility |

> **Critical:** The ServicePlanner User permission is what controls what the *agent* can see. If ServicePlanner User doesn't have access to an article, it won't be used in plan steps — even if reps can see it.

### Data Categories (Optional)
- Filter which articles Service Assistant grounds on by selecting specific data categories in the data library
- If filtering is enabled: make sure ServicePlanner User has access to those categories, and articles are assigned to them
- If not filtering: all published articles are in scope

### Citations
- **GA Service Assistant:** Shows `[1]` inline citations at the end of steps
- **Dynamic Plans for messaging (beta):** Citations do NOT appear — but grounding still works
- The data library config is the same regardless — citations are just a display feature

---

## Permissions & FLS (Critical — Demos Fail Silently Without This)

Permissions are the #1 reason demos fail silently. Missing FLS returns `null` for a field — no error, no warning, just blank data in the card. Missing Apex class access causes "I cannot do this automatically."

### Who Needs What

There are **three personas** that need permissions in every demo:

| Persona | User Record | Why They Need Access |
|---|---|---|
| **Setup Admin** (you) | Your admin user | Deploy metadata, create articles, configure Agent Builder |
| **Service Rep** | The rep user testing/demoing | See records, view knowledge, use the console |
| **EinsteinServiceAgent User** | System user (auto-created) | The agent that EXECUTES actions. If this user can't see a field, the action returns null. |

### Permission Set Checklist (Create One Per Demo)

Create a Permission Set (e.g., `WSI_Patio_Demo_Access`) and assign it to BOTH the Service Rep AND EinsteinServiceAgent User:

**Object Access:**
- [ ] Contact — Read (at minimum; Create/Edit if actions update records)
- [ ] Account — Read
- [ ] Case — Read, Edit (for case updates)
- [ ] MessagingSession — Read (required for Contact resolution)
- [ ] Knowledge__kav — Read (for knowledge grounding)

**Field-Level Security (every field your Apex queries):**
- [ ] Contact: FirstName, LastName, Email, Phone, MailingStreet, MailingCity, MailingState, MailingPostalCode, Title, Description, AccountId
- [ ] Account: Name, Industry, Type
- [ ] Case: Subject, Description, Status, Priority, ContactId, AccountId
- [ ] MessagingSession: EndUserContactId, Status, CreatedDate
- [ ] Any custom fields you add

**Apex Class Access:**
- [ ] Every action class (GetWSICustomerProfileAction, LookUpWSIOrderAction, etc.)
- [ ] Every DTO class (WSICustomerProfileOutput, WSIOrderProductOutput, etc.)
- [ ] Grant via: Permission Set → Apex Class Access → Add all demo classes

**Knowledge Access:**
- [ ] Allow View Knowledge (system permission)
- [ ] Read + View All on Knowledge__kav
- [ ] Data Category visibility (if using category filters)

### The Silent Failure Pattern

| What's Missing | What Happens | How It Looks |
|---|---|---|
| FLS on a field | Query returns null for that field | Card renders but shows "—" for that field |
| Object access | Query returns 0 rows | Action says "Contact not found" or card is empty |
| Apex class access | Action can't execute | Agent says "I cannot do this automatically" |
| Knowledge access | Articles not retrieved | Agent says "no information in your documents" but may hallucinate an answer |
| MessagingSession access | Contact resolution fails | Falls through to "most recent active session" fallback |

> **Mental model:** Data-access failures fail SILENTLY. `with sharing` → 0 rows. Missing FLS → null fields. Missing object access → empty results. There is NO error thrown — the action "succeeds" with empty data.

### Why `without sharing` Isn't Enough

Using `global without sharing` on your Apex class bypasses **sharing rules** (who owns the record, sharing model). But it does NOT bypass:
- **Field-Level Security** — FLS is still enforced when accessed via certain APIs
- **Object permissions** — the user still needs Read on the object
- **Apex class access** — the user needs permission to execute the class

In practice, `without sharing` handles most demo scenarios because SOQL in Apex doesn't enforce FLS by default. But if you use `WITH SECURITY_ENFORCED` or Schema.describe checks, FLS kicks in. **Best practice for demos: use `without sharing` AND grant FLS anyway** — it's defense in depth and prevents issues if the platform behavior changes.

### Quick Setup Script

After deploying Apex classes, run this to verify EinsteinServiceAgent User has access:

```bash
# Find the EinsteinServiceAgent User
sf data query --query "SELECT Id, Name, Username FROM User WHERE Name = 'EinsteinServiceAgent User'" --target-org mySDO

# Check what permission sets are assigned
sf data query --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = '<userId>'" --target-org mySDO
```

If your demo-specific perm set isn't listed, assign it:
```bash
sf data create record --sobject PermissionSetAssignment --values "AssigneeId=<userId> PermissionSetId=<permSetId>" --target-org mySDO
```

### Admin User FLS (Don't Forget Yourself)

If you're the admin deploying and testing, your profile also needs FLS on all fields. Admin profiles often have "View All Data" which bypasses object/record access, but NOT FLS on custom fields added after the profile was created. Verify:
- Setup → Profiles → System Administrator → Field-Level Security
- OR assign yourself the same permission set you built for the demo

---

## Demo Build Recipe (Start Here)

When building a new demo from scratch, follow this order:

### Phase 1: Spec (30 min)
1. Define persona (name, tier, scenario, product)
2. Define the action chain (3-6 actions, sequence, confirmation flags)
3. Decide which actions get CLT cards (typically: customer profile + product/order context)
4. Map data flow (output→input for every action pair)

### Phase 2: Deploy Infrastructure (1 hour)
1. Create SFDX project (`sf project generate`)
2. Write Apex actions following the `global without sharing` + `@InvocableMethod` pattern
3. Write CLT DTOs (single-JSON-field pattern) for card actions
4. Write LWC cards (targets: `lightning__AgentforceOutput`)
5. Write Lightning Type bundles (meta.xml + renderer.json)
6. Deploy: `sf project deploy start --source-dir force-app/main/default --target-org <alias>`

### Phase 3: Demo Data (15 min)
1. Write idempotent setup-data.apex (check-before-insert)
2. Include: Account, Contact (with persona details in Description), Case
3. Run: `sf apex run --file skill/setup-data.apex --target-org <alias>`

### Phase 4: Knowledge Articles (45 min)
1. Write 2-4 **core** articles (support the action chain)
2. Write 4-6 **conversational** articles (support unscripted Q&A)
3. Every article: SCOPE block, structured content, trigger phrases, Summary field in customer-voice
4. Create manually in Setup → Knowledge → New Article → Publish

### Phase 5: Permissions & FLS (15 min — DO THIS BEFORE AGENT BUILDER)
1. Create a Permission Set for the demo (e.g., `WSI_Patio_Demo_Access`)
2. Add Object Access: Contact (Read), Account (Read), Case (Read/Edit), MessagingSession (Read), Knowledge__kav (Read)
3. Add FLS: every field your Apex classes query (see checklist in Permissions section above)
4. Add Apex Class Access: every action class + every DTO class
5. Add System Permission: Allow View Knowledge
6. Assign the perm set to **EinsteinServiceAgent User** (the agent that executes actions)
7. Assign the perm set to your **Service Rep** user (the user testing/demoing)
8. Assign the perm set to yourself (admin — for testing in dev console)

### Phase 6: Agent Builder Config (30 min — all manual)
1. Create Topic (name, classification description, scope)
2. Create Agent Actions (Apex → Invocable Method → fresh name each time)
3. Configure CLT outputs (Show ✅, Filter ✅, Output Rendering → Lightning Type)
4. Configure passthrough outputs (Filter ✅, Show ☐)
5. Add actions to Topic, set confirmation flags
6. Add Instructions in sort order (include render backstop as last instruction)
7. Configure Data Library (Knowledge → Title + Summary as identifying, Answer as content)
8. Verify EinsteinServiceAgent User has the perm set assigned (double-check — this is the #1 demo-day failure)

### Phase 7: Document (20 min)
1. Write REBUILD-AGENT.md using SUBAGENT-TEMPLATE.md
2. Write DEMO-SCRIPT.md with talk track and anticipated Q&A
3. Commit to sf-demo-skills/subagents/

### Key Learnings (from Pet Travel + WSI builds)

| Learning | Detail |
|----------|--------|
| **Apex > Flows** | Apex @InvocableMethod actions chain more reliably, render CLTs correctly, and handle Contact resolution cleanly. Default to Apex. |
| **Always plan CLTs** | Audiences expect visual cards, not text walls. Plan at least 2 CLTs per demo (customer profile + key context card). |
| **Single-JSON-field DTO** | Multiple @InvocableVariable fields on the output break CLT rendering. Use ONE @AuraEnabled String field with serialized JSON. |
| **Passthrough fields** | Actions that produce CLT cards should ALSO return flat passthrough fields (customerId, loyaltyTier) for downstream action chaining. Don't force the LLM to extract data from the card JSON. |
| **255-char description limit** | Lightning Type bundle `description` field maxes at 255 chars. Keep it short: "WSI profile card. Always use show_command. Do NOT convert to text." |
| **Knowledge > Instructions for policy** | Put policy details, troubleshooting steps, and reference data in knowledge articles — not in instructions or hardcoded in Apex. Instructions say *what to do*; knowledge says *what to know*. |
| **Conversational articles are essential** | Don't just write articles for the scripted flow. Write 4-6 extra articles for unscripted Q&A. This is what makes the demo feel real. |
| **Trigger phrases matter** | Add 5-10 trigger phrases at the bottom of every article. Written in customer-voice, not internal jargon. These are semantic retrieval hooks. |
| **Demo data in Description field** | Store persona metadata (loyalty tier, member since, etc.) in the Contact.Description field. Apex can parse it or hardcode demo values. |
| **Idempotent data scripts** | Always check-before-insert. Demos get reset multiple times. |
| **Build CLT actions BY HAND** | Never rely on metadata deploy for CLT action config. Delete and recreate fresh in Agent Builder every time. |
| **Three-layer chaining** | Use instructions (temporal language in sort order) + action descriptions (prerequisite declarations) + data dependencies (output→input) together. Any one alone is unreliable. All three = reliable 5+ action chains. |
| **Temporal connectors in instructions** | "first...", "After identifying...", "If troubleshooting does not resolve...", "Based on the customer's..." — these enforce sequence better than numbered steps or "proceed to" language. |
| **FLS for EinsteinServiceAgent User** | The agent user needs FLS on EVERY field your Apex queries. Missing FLS = silent null, not an error. Create a perm set, grant all fields, assign to both rep AND EinsteinServiceAgent User. |
| **FLS for admin too** | Your admin profile may have View All Data but NOT FLS on custom fields added post-profile-creation. Assign yourself the same perm set. |
| **Silent failure pattern** | Missing permissions never throw errors — they return null/empty. If a card shows "—" for a field or an action returns no data, check FLS and object access FIRST before debugging Apex logic. |

---

## Pre-Build Checklist (Any Demo)

### Before You Build
- [ ] Know your 3 core value props (Know Customer / Know Engagement / Know Solution)
- [ ] Identify the 3-6 key actions in the workflow — these become your flows/apex
- [ ] Decide which actions need rep confirmation (On) vs. run silently (Off)
- [ ] Map the data flow: which action outputs feed into which action inputs?
- [ ] Know what data your topic needs (objects, fields, relationships)
- [ ] Have demo persona defined: name, company, loyalty tier, key context

### Metadata Deploy
- [ ] Custom objects and fields defined in SFDX project
- [ ] Profile XML includes FLS for all custom fields (exclude required fields — they auto-grant)
- [ ] `sf project deploy start` succeeds clean
- [ ] Demo data created via idempotent Apex (runs safely multiple times)

### Topic Setup
- [ ] Topic name is specific, not generic
- [ ] Classification description covers the case type, subtypes, keyword variations
- [ ] Scope defines what the agent WILL and WON'T do (ends with "must not handle...")
- [ ] Each instruction covers exactly one task
- [ ] No references to "the knowledge base" in instructions
- [ ] No "proceed to [next step]" directives (let sort order handle it)
- [ ] Gating instructions block where compliance/safety requires rep confirmation
- [ ] If using knowledge grounding: max 3-5 instructions
- [ ] CLT render instructions include "always use show_command" + "Do NOT convert to plain text"

### Actions
- [ ] Every action description includes prerequisite + data source
- [ ] Data flow is explicit (output→input references, not LLM memory)
- [ ] Confirmation is set correctly (reads=Off, writes=On)
- [ ] Progress indicator messages set on every action
- [ ] CLT actions built BY HAND (not via deploy)
- [ ] Context Variables mapped for deterministic data pipes

### Flows
- [ ] Each flow is type: Autolaunched (No Trigger)
- [ ] All I/O variables have Available for Input / Output checked
- [ ] Flow is Activated before registering as an action
- [ ] Flows don't make irreversible changes (so demo is repeatable)

### Knowledge (if using)
- [ ] Articles follow one-article-one-topic rule
- [ ] Titles use [Content Type] - [Specific Topic] - [Scope] format
- [ ] SCOPE & APPLICABILITY block at top of each article
- [ ] Standalone sections (no relative references)
- [ ] Trigger phrases (5-10) at the end of each article
- [ ] No formatting noise (emojis, heavy bolding)
- [ ] Data library created with Title + Summary as identifying fields
- [ ] Answer/Detail/Question selected as content fields
- [ ] ServicePlanner User has Agent Knowledge Access permission set
- [ ] Service reps have Service Rep Knowledge Access permission set
- [ ] Data categories configured and accessible (if filtering)

### Version Control
- [ ] Agent version created before any changes
- [ ] Bundle retrieved and committed after changes (never deployed)
- [ ] Rebuild doc created/updated with full action config tables

### Demo Scripts
- [ ] **Case (Email) demo script** created with turn-by-turn talk track
- [ ] **Messaging demo script** created with channel-specific flow
- [ ] **Voice demo script** created with conversational dialogue
- [ ] Each script includes: persona setup, customer utterance, expected agent responses, action outcomes
- [ ] Channel-specific considerations documented (e.g., messaging = no CLT cards, voice = verbal responses only)

### Final Check
- [ ] Run full demo end-to-end at least once before presenting
- [ ] Reset script tested (demo data can be restored in < 2 min)
- [ ] Know your fallback if a step fails (screenshot or slide backup)
