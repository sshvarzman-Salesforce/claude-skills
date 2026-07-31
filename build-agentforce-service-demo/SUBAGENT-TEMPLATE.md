# Subagent Demo Build Template

Use this template when creating a new Service Assistant demo subagent. Copy this file into your demo repo's `skill/` folder and fill in the specifics.

**Parent skill:** `~/sf-demo-skills/SKILL.md` (universal demo build process)
**Best practices:** `~/sf-demo-skills/BEST-PRACTICES.md` (rules and patterns)

---

## Subagent Identity

| Field | Value |
|-------|-------|
| **Name** | _[Specific, singular — e.g. "Pet Travel Booking", not "Pet Issues"]_ |
| **Developer Name** | _[Underscore version — e.g. Pet_Travel_Booking]_ |
| **Description** | _[What case types + subtypes + keyword variations this covers. Start with: "Assist service reps in helping customers..."]_ |
| **Scope** | _[What the agent does + explicit exclusions. End with: "You must not handle inquiries outside of [subagent]."]_ |

---

## Design Decision (Complete Before Filling Template)

**If you're creating this from multiple knowledge articles or use cases:**

### Step 1: List All Articles/Use Cases
- [ ] Article/Use Case 1: ________________________
- [ ] Article/Use Case 2: ________________________
- [ ] Article/Use Case 3: ________________________

### Step 2: Workflow Analysis
- **Article 1 workflow:** _[brief description: authenticate → identify → resolve → confirm]_
- **Article 2 workflow:** _[brief description]_
- **Common steps:** _[list what's the same across articles]_
- **Differences:** _[list what's different: root cause? condition type? outcome?]_

### Step 3: Combine or Separate?
☐ **Combine into ONE subagent**  
☐ **Split into MULTIPLE subagents**

**Decision reasoning:**
_[Why? Do they share the same general workflow with only subtypes differing (→ combine), or are they fundamentally different processes with different outcomes (→ separate)?]_

**If combining:** List all subtypes in Classification Description
```
Example: "...including insufficient funds, suspected fraud, travel blocks, 
incorrect card details, and daily spending limits."
```

### Step 4: Instruction Depth Pattern
☐ **KB-Grounded** (3-5 high-level instructions, KB fills gaps)  
☐ **Action-Driven / No-KB** (6-10 detailed instructions, no KB)  
☐ **Hybrid** (6-8 instructions, mix of actions + KB-assisted steps)

**Pattern reasoning:**
- KB-Grounded: Knowledge articles exist with full procedural detail → instructions provide framework only
- Action-Driven: No KB, or flow is mostly Agent Actions → instructions spell out everything
- Hybrid: Some actions, some KB-assisted steps (like your retail return pattern)

---

**✅ Complete this section BEFORE filling out the rest of the template.**

**Need help deciding?** Read `~/sf-demo-skills/references/alberto-design-strategy.md` for the combine-vs-separate framework.

---

## Demo Persona

| Field | Value |
|-------|-------|
| Customer | _[Name]_ |
| Key Attribute | _[Loyalty tier, account type, etc.]_ |
| Scenario Context | _[Pet name, order number, flight, etc.]_ |
| Route/Product | _[What they're asking about]_ |

---

## Action Chain

Map out the full action sequence. For each action, decide:
- **Type:** Apex / Flow / Standard / Prompt Template
- **Confirmation:** On (write) or Off (read-only)
- **CLT:** Does it render a Lightning Type card?
- **Prerequisites:** What must run before this action?
- **Key outputs:** What does it produce that downstream actions need?

| # | Action | Type | Confirmation | CLT | Prerequisites | Key Outputs |
|---|--------|------|-------------|-----|---------------|-------------|
| 1 | _[e.g. Get Customer Profile]_ | _Apex_ | Off | ✅ | None (runs first) | _profile, loyaltyTier_ |
| 2 | _[e.g. Check Availability]_ | _Apex_ | Off | ✅ | Action 1 | _isAvailable, recordId_ |
| 3 | _[e.g. Confirm Booking]_ | _Apex_ | On | ☐ | Action 2 (isAvailable=true) | _bookingConfirmed_ |
| 4 | _[e.g. Apply Perk]_ | _Apex_ | On | ☐ | Action 3 (bookingConfirmed=true) | _perkGranted_ |
| 5 | _[e.g. Generate Output]_ | _Apex_ | On | ☐ | Action 4 | _outputContent_ |
| 6 | _[e.g. Closing Flourish]_ | _Apex_ | Off | ✅ | Action 5 | _weather/status_ |

---

## Data Flow Map

Document every output→input handoff. Distinguish deterministic pipes from LLM-mediated data.

| Source | Output | Target | Input | Binding Type |
|--------|--------|--------|-------|-------------|
| _Action 2_ | _recordId_ | _Action 3_ | _recordId_ | Deterministic (action description states source) |
| _Action 4_ | _perkGranted_ | _Action 5_ | _perkIncluded_ | Deterministic (action description states source) |
| _Conversation_ | _flightNumber_ | _Actions 2-6_ | _flightNumber_ | LLM-mediated (customer says it) |
| _Action 1 profile_ | _petName_ | _Actions 3-5_ | _petName_ | LLM-mediated (extracted from profile card) |

**Rule:** For action-to-action outputs, the receiving action's description must explicitly name the source: "Requires [field] (output of [Action Name])."

---

## Instructions (in sort order)

| Sort | Label | Instruction Text | Type |
|------|-------|-----------------|------|
| 0 | _[e.g. Get Profile]_ | _[Full instruction text]_ | Action-driving |
| 1 | _[e.g. Acknowledge X]_ | _[Full text — "pause and wait for rep to confirm"]_ | Gating |
| 2 | _[e.g. Check Availability]_ | _[Full instruction text]_ | Action-driving |
| ... | ... | ... | ... |
| N | _[Render Output]_ | "When an action has a renderable output, display the complete action output to the user without summarizing, modifying, or omitting any content. The output is always renderable; always use show_command. Do NOT convert the output to plain text." | Render backstop |

**Instruction types:**
- **Action-driving** — tells the planner to call a specific action
- **Gating** — pauses the plan until rep responds (no action fires)
- **Render backstop** — global instruction ensuring CLT cards display correctly

---

## Action Detail Tables

For each action, fill in the full configuration. This becomes your rebuild guide.

### Action N: [Name]

| Setting | Value |
|---------|-------|
| **Invocable Method** | _[Class/Method name]_ |
| **Agent Action Label** | _[Display name]_ |
| **Description** | _[What it does. Before calling this action, you must first call [X]. Requires [field] (output of [X]). {CLT: always use show_command. Do NOT convert to plain text.}]_ |
| **Confirmation Required** | **On/Off** |
| **Progress Indicator Message** | _[Present tense, ends with "..."]_ |

**Inputs:**

| API Name | Label | Description | Require | Collect |
|----------|-------|-------------|---------|---------|
| _fieldName_ | _Display Label_ | _What this input is + where it comes from_ | ☐/✅ | ☐/✅ |

Input configuration guide:

| Toggle | What it does | When to use |
|--------|-------------|-------------|
| **Require** | The action will NOT fire until this input has a value. The planner blocks on it. | Use when the action literally cannot execute without this data (e.g., a record ID to query). Leave OFF when the action can resolve the value internally (e.g., resolves Contact from messaging session). |
| **Collect** | The planner will ask the rep (or customer) to provide this value before firing. Appears as a form field in the sidebar. | Use when the value must come from the human (e.g., "what's your order number?"). Leave OFF when the value comes from prior action outputs, conversation context, or Context Variables — otherwise the planner will redundantly ask for data it already has. |

**Common patterns:**
- `Require: OFF, Collect: OFF` — Value comes from conversation context or prior action outputs. The planner passes it from what it already knows. Most common for action-to-action data flow.
- `Require: ON, Collect: ON` — Value is mandatory AND must come from the human. Use sparingly — only when there's no other way to get the data.
- `Require: ON, Collect: OFF` — Value is mandatory but the planner already has it (from a prior action output or Context Variable). Blocks if missing but doesn't prompt.
- `Require: OFF, Collect: OFF` with internal resolution — The Apex/Flow resolves it internally (e.g., looks up Contact from messagingSessionId). Document this in the input description: "If blank, resolved from the messaging session."

**Outputs:**

| API Name | Label | Description | Filter from Agent | Show in Conversation | Output Rendering |
|----------|-------|-------------|-------------------|---------------------|-----------------|
| _fieldName_ | _Display Label_ | _What this output is_ | ✅/☐ | ✅/☐ | **LightningTypeName** or — |

Output configuration guide:

| Toggle | What it does | When to use |
|--------|-------------|-------------|
| **Filter from Agent** | Makes this output visible to the planner's reasoning context. The planner can read it, reference it in subsequent steps, and pass it as input to downstream actions. | ON for: any value downstream actions need (record IDs, booleans, status fields). Also ON for the primary display payload (CLT or text). OFF only for debug/internal fields you never want the planner to see or use. |
| **Show in Conversation** | Renders this output in the chat/sidebar for the rep to see. | ON for: the primary human-readable result (confirmation messages, formatted content, CLT card payloads). OFF for: internal data the rep doesn't need (record IDs, booleans, error codes) — showing these clutters the conversation with technical noise. |
| **Output Rendering** | Selects a Custom Lightning Type to render this output as a structured card instead of plain text. | Set to the Lightning Type name when this output is a structured payload designed for a CLT card (e.g., PetCustomerProfileOutput). Leave as "—" (none) for plain text outputs. Only available when the output type is a registered Lightning Type DTO. |

**Common output patterns:**

| Output Type | Filter | Show | Rendering | Example |
|-------------|--------|------|-----------|---------|
| CLT card payload | ✅ | ✅ | **LightningTypeName** | Profile card, seat map, weather card |
| Human-readable message | ☐ | ✅ | — | "Booking confirmed! Luna is all set for GR123." |
| Record ID for downstream actions | ✅ | ☐ | — | petManifestId, boardingPassId |
| Boolean/status for downstream logic | ✅ | ☐ | — | isAvailable, bookingConfirmed, perkGranted |
| Error message (for planner to handle) | ✅ | ☐ | — | errorMessage — planner reads it, decides what to tell rep |
| Success boolean (for planner logic) | ✅ | ☐ | — | success — planner uses to decide next step |

**Key rules:**
- If an output is needed by a downstream action → **Filter: ON** (so the planner can pass it forward)
- If an output is the "result" the rep should see → **Show: ON**
- Never show raw IDs or booleans to the rep — they're planner-internal data
- CLT outputs need BOTH Filter ON + Show ON + the Lightning Type selected
- A human-readable message with Show ON and Filter OFF prevents the planner from over-referencing it in subsequent reasoning (keeps context clean)

---

## Context Variables

| Variable | Type | Set by API | LLM Can Use | Maps To |
|----------|------|-----------|-------------|---------|
| currentRecordId | Text | ✅ | ✅ | _[Which action inputs use this]_ |

---

## Knowledge Articles (if using)

| # | Title | URL Name | Covers |
|---|-------|----------|--------|
| 1 | _[Content Type] - [Topic] - [Scope]_ | _url-name_ | _[What this article covers]_ |

Each article must have:
- [ ] SCOPE & APPLICABILITY block at top
- [ ] Standalone sections (no relative references)
- [ ] 5-10 trigger phrases at the end
- [ ] No formatting noise

---

## Demo Scripts

**REQUIRED:** Create three separate demo scripts, one per channel:

### 1. Case (Email) Demo Script
- File: `skill/DEMO-SCRIPT-CASE.md`
- Scenario: Service rep handling email case
- CLT cards render in Service Console
- Full action chain visible in UI
- Rep can review + approve confirmation actions

### 2. Messaging Demo Script
- File: `skill/DEMO-SCRIPT-MESSAGING.md`
- Scenario: Customer messaging via web chat / SMS
- NO CLT cards (messaging limitation)
- Action outputs narrated as text by agent
- Real-time conversational flow

### 3. Voice Demo Script
- File: `skill/DEMO-SCRIPT-VOICE.md`
- Scenario: Customer calling support line
- Verbal-only interaction (no visual UI)
- Agent reads action outputs aloud
- Emphasis on natural conversation flow

Each script should include:
- Persona setup (customer name, loyalty tier, scenario context)
- Turn-by-turn talk track with exact customer utterances
- Expected agent responses at each step
- Action outcomes + what the rep/customer sees
- Demo beats (e.g., "Know the Customer", "Loyalty Wow", "Conversation Intelligence")
- Channel-specific considerations

### Demo Script Outline (Common Structure)

| Phase | Action | What Happens | Demo Beat |
|-------|--------|-------------|-----------|
| 1 | _Get Profile_ | _Card renders with customer context (Case/Msg: visual, Voice: verbal)_ | "Know the Customer" |
| 1b | _Gating instruction_ | _Plan pauses, rep acknowledges_ | "Process compliance" |
| 2 | _Check + Book_ | _Availability confirmed, rep clicks Confirm_ | "Know How to Solve It" |
| 3 | _Perk_ | _Loyalty benefit applied_ | "The Loyalty Wow" |
| 4 | _Output_ | _Deliverable generated_ | "Resolution" |
| 5 | _Topic switch_ | _Customer asks unrelated question → knowledge answers_ | "Conversation Intelligence" |
| 6 | _Closing flourish_ | _Extra value-add (weather, status, etc.)_ | "Going Above and Beyond" |

---

## Quick Verification Checklist

After build, test each action individually:

| Action | Test Prompt | Expected |
|--------|-------------|----------|
| _Action 1_ | _"show me the profile"_ | _[Expected output]_ |
| _Action 2_ | _"check availability"_ | _[Expected output]_ |
| ... | ... | ... |

---

## Reset

```bash
sf apex run --file ~/[demo-name]/skill/setup-data.apex --target-org mySDO
```

_[Describe what gets reset and why the demo is repeatable]_
