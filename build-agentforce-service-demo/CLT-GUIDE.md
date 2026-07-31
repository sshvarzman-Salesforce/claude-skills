# Custom Lightning Types (CLTs) for Service Rep Assistant — Professional Services Guide

**Author:** Chad Goldsmith  
**Date:** June 2026  
**Audience:** Professional Services consultants implementing CLTs in Agentforce Service Rep Assistant (SRA) engagements  
**Surface:** Service Rep Assistant (SRA) sidebar — messaging channel with Dynamic Plans  
**Context:** This documents Chad's end-to-end approach to building CLTs for SRA, drawn from a working pet travel management demo. It covers the Apex pattern, LWC rendering, Agent Builder configuration, action chaining via topic instructions, and the known platform quirks PS teams need to navigate.

---

## What Are CLTs and Why Do They Matter in SRA?

Custom Lightning Types let you render **rich visual cards** (LWC components) in the **Service Rep Assistant (SRA) sidebar** instead of plain-text responses. This is specific to the SRA surface — the agent panel that appears alongside the messaging console in Service Cloud. Without CLTs, every action result is narrated as text in the chat stream. With CLTs, the SRA agent can display customer profile cards, weather forecasts, seat maps, booking confirmations — anything an LWC can render — directly in the sidebar where the rep is already working.

**The value proposition for customers:**
- Reps get visual, scannable information in the SRA sidebar instead of walls of text in the chat
- Actions feel like native platform features, not chatbot responses
- Data-rich outputs (tables, maps, diagrams) that would be unreadable as narrated text become clear at a glance
- The SRA Dynamic Plans surface can chain multiple CLT-rendering actions into a guided workflow for the rep

---

## Architecture Overview

A CLT card has **four components** that work together:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. APEX ACTION CLASS                                           │
│     @InvocableMethod that queries data and returns a Response   │
│     containing the CLT DTO (output type)                        │
├─────────────────────────────────────────────────────────────────┤
│  2. CLT DTO (Data Transfer Object) — Apex class                │
│     global class with ONE @AuraEnabled String field             │
│     Holds the entire payload as serialized JSON                 │
├─────────────────────────────────────────────────────────────────┤
│  3. LIGHTNING TYPE BUNDLE — metadata                            │
│     Maps the Apex DTO → the LWC renderer                       │
│     Contains: lightningType-meta.xml + schema.json +            │
│     renderer.json                                               │
├─────────────────────────────────────────────────────────────────┤
│  4. LWC COMPONENT — the visual card                            │
│     Receives `this.value.<fieldName>`, JSON.parse()s it,        │
│     renders the card UI                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Single-JSON-Field DTO Pattern

This is the key insight that makes CLTs work reliably. **Do NOT use multiple `@InvocableVariable` fields on the output DTO.** Multiple fields get flattened into separate text outputs by the Agent Builder schema introspection, which breaks CLT rendering.

Instead: ONE field, ONE serialized JSON string.

### ✅ Correct Pattern (What Works)

```java
@JsonAccess(serializable='always' deserializable='always')
global class CustomerProfileOutput {

    // Single String field holding the entire profile payload as serialized JSON.
    // The LWC reads this.value.profileJSON and JSON.parse()'s it.
    // 
    // CRITICAL: Use @AuraEnabled — NOT @InvocableVariable.
    // @InvocableVariable causes Agent Builder to flatten this into a text output.
    // @AuraEnabled lets the CLT renderer bind to the class as a single typed object.
    @AuraEnabled
    global String profileJSON;

    global CustomerProfileOutput(String profileJSON) {
        this.profileJSON = profileJSON;
    }

    global CustomerProfileOutput() {
        this.profileJSON = '';
    }
}
```

### ❌ Wrong Pattern (What Breaks)

```java
// DON'T DO THIS — fields get flattened into separate text outputs
global class CustomerProfileOutput {
    @InvocableVariable global String customerName;
    @InvocableVariable global String loyaltyTier;
    @InvocableVariable global String petName;
    // Agent Builder sees 3 separate text outputs → no CLT rendering
}
```

### Why This Works

- `@AuraEnabled` exposes the field to the LWC framework (needed for rendering)
- `@JsonAccess(serializable='always')` ensures the platform can serialize it correctly
- A single field means Agent Builder introspects ONE output of a custom Apex type → maps it to the Lightning Type → renders via the LWC
- The payload inside `profileJSON` can be arbitrarily complex — the LWC handles all the parsing

---

## Complete Example: Customer Profile Card

### Step 1: The DTO (Output Type)

```java
// CustomerProfileOutput.cls
@JsonAccess(serializable='always' deserializable='always')
global class CustomerProfileOutput {

    @AuraEnabled
    global String profileJSON;

    global CustomerProfileOutput(String profileJSON) {
        this.profileJSON = profileJSON;
    }

    global CustomerProfileOutput() {
        this.profileJSON = '';
    }
}
```

### Step 2: The Action Class

```java
// GetCustomerProfileAction.cls
global without sharing class GetCustomerProfileAction {

    global class Input {
        @InvocableVariable(label='Customer ID' 
            description='The Salesforce Contact ID of the customer' 
            required=false)
        global String customerId;

        @InvocableVariable(label='Messaging Session ID' 
            description='The Salesforce Messaging Session ID — used to resolve 
            Contact when Customer ID is not available' 
            required=false)
        global String messagingSessionId;
    }

    global class Response {
        @InvocableVariable
        global Boolean success;

        @InvocableVariable(label='Customer Profile' 
            description='Structured payload for the petCustomerProfileCard renderer')
        global CustomerProfileOutput profile;

        @InvocableVariable
        global String errorMessage;
    }

    @InvocableMethod(label='Get Customer Profile' 
        description='Retrieves customer loyalty tier, pet name, and seat preference. 
        The output of this action is always renderable, always use show_command.')
    global static List<Response> getProfile(List<Input> inputs) {
        List<Response> results = new List<Response>();

        for (Input inp : inputs) {
            Response res = new Response();
            try {
                String resolvedContactId = inp.customerId;

                // Resolve via MessagingSession if no direct Contact ID
                if (String.isBlank(resolvedContactId) 
                    && !String.isBlank(inp.messagingSessionId)) {
                    List<MessagingSession> sessions = [
                        SELECT EndUserContactId FROM MessagingSession
                        WHERE Id = :inp.messagingSessionId LIMIT 1
                    ];
                    if (!sessions.isEmpty()) {
                        resolvedContactId = sessions[0].EndUserContactId;
                    }
                }

                // Fallback: most recent active session
                if (String.isBlank(resolvedContactId)) {
                    List<MessagingSession> sessions = [
                        SELECT EndUserContactId FROM MessagingSession
                        WHERE Status = 'Active'
                        ORDER BY CreatedDate DESC LIMIT 1
                    ];
                    if (!sessions.isEmpty() && sessions[0].EndUserContactId != null) {
                        resolvedContactId = sessions[0].EndUserContactId;
                    }
                }

                // Build the payload
                Map<String, Object> payload = new Map<String, Object>();

                if (String.isBlank(resolvedContactId)) {
                    payload.put('customerName', 'Unknown');
                } else {
                    List<Contact> contacts = [
                        SELECT Id, FirstName, LastName, Email,
                               Loyalty_Tier__c, Pet_Name__c, Pet_Type__c,
                               Pet_Special_Needs__c, Seat_Preference__c
                        FROM Contact
                        WHERE Id = :resolvedContactId LIMIT 1
                    ];
                    if (!contacts.isEmpty()) {
                        Contact c = contacts[0];
                        payload.put('customerId', c.Id);
                        payload.put('customerName', 
                            (c.FirstName != null ? c.FirstName + ' ' : '') 
                            + (c.LastName != null ? c.LastName : ''));
                        payload.put('email', c.Email);
                        payload.put('loyaltyTier', c.Loyalty_Tier__c);
                        payload.put('petName', c.Pet_Name__c);
                        payload.put('petType', c.Pet_Type__c);
                        payload.put('petSpecialNeeds', c.Pet_Special_Needs__c);
                        payload.put('seatPreference', c.Seat_Preference__c);
                    }
                }

                res.profile = new CustomerProfileOutput(JSON.serialize(payload));
                res.success = true;
            } catch (Exception e) {
                res.success = false;
                res.errorMessage = e.getMessage();
                res.profile = new CustomerProfileOutput(
                    '{"error":"' + e.getMessage().replace('"', '\\"') + '"}');
            }
            results.add(res);
        }
        return results;
    }
}
```

**Key patterns in the action:**
- `global without sharing` — required because the action runs as `EinsteinServiceAgent User`, which has no sharing access to Contact records. `with sharing` → silent empty results, not an error.
- Multiple input resolution paths (direct ID → messaging session → fallback) — makes the action resilient across surfaces.
- Error case still returns a valid DTO (with error JSON) so the LWC can render an error state instead of crashing.

### Step 3: Lightning Type Bundle

Three files in `force-app/main/default/lightningTypes/petCustomerProfileOutput/`:

**`petCustomerProfileOutput.lightningType-meta.xml`** (not needed — use JSON format instead):

The working format is actually a JSON file named with `.lightningType-meta.xml` extension but containing JSON:

```json
{
  "title" : "Pet Customer Profile Output",
  "description" : "Customer profile data rendered as a card in the SRA sidebar. The output of this action is always renderable. Always use show_command to display this to the user. Do NOT convert to text.",
  "lightning:type" : "@apexClassType/c__CustomerProfileOutput"
}
```

> **Important:** The `description` field in the Lightning Type schema is read by the LLM. Include rendering instructions here — this is part of the instruction layer.

**`lightningDesktopGenAi/renderer.json`:**

```json
{
  "componentOverrides": {
    "$": {
      "definition": "c/petCustomerProfileCard"
    }
  }
}
```

### Step 4: LWC Component

**`petCustomerProfileCard.js-meta.xml`:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__AgentforceOutput</target>
        <target>lightning__AgentforceInput</target>
    </targets>
</LightningComponentBundle>
```

**`petCustomerProfileCard.js`:**

```javascript
import { LightningElement, api, track } from 'lwc';

export default class PetCustomerProfileCard extends LightningElement {

    @api value;        // Platform passes the DTO here
    @track profile = {};
    @track errorMessage = '';

    connectedCallback() {
        try {
            if (!this.value || !this.value.profileJSON) {
                this.errorMessage = 'No profile data provided.';
                return;
            }

            const raw = this.value.profileJSON;
            const data = typeof raw === 'string' ? JSON.parse(raw) : raw;

            if (data.error) {
                this.errorMessage = data.error;
                return;
            }

            this.profile = data;
        } catch (e) {
            console.error('PetCustomerProfileCard parse error:', e);
            this.errorMessage = 'Error loading customer profile.';
        }
    }

    get hasData() {
        return !this.errorMessage && this.profile && this.profile.customerName;
    }

    get resolvedCustomerName() {
        return this.profile.customerName || '—';
    }

    get resolvedLoyaltyTier() {
        return this.profile.loyaltyTier || '—';
    }

    // ... additional getters for each field
}
```

**Key:** The LWC receives the entire DTO via `this.value`. The field name (`profileJSON`) matches what the Apex class declared with `@AuraEnabled`. The LWC is responsible for parsing and rendering — the platform just passes the object through.

---

## Action Chaining: How to Make the Agent Execute a Multi-Step Flow

The real power of CLTs in Service Assistant comes from **action chaining** — where the output of one action feeds into the next, and each step renders a visual card while advancing the flow.

### Demo Chain: Pet Travel Booking (5 steps)

```
1. Get Customer Profile     → renders profile card (CLT)
2. Check Pet Manifest       → renders seat map card (CLT)
3. Pet Booking              → confirmation button (HiL) → creates record
4. Loyalty Perk             → confirmation button (HiL) → applies perk
5. Generate Boarding Pass   → confirmation button (HiL) → generates pass
```

### Topic Instructions That Drive Chaining

Copy this into the **Topic Instructions** field in Agent Builder:

```
Topic Goal: Efficiently manage pet travel bookings, loyalty rewards, 
and boarding pass generation.

Instructions:

Tone: Professional, efficient, and proactive.

UI Priority: Always present action confirmations via the sidebar Service 
Plan buttons. Never list next steps as a numbered list (e.g., 1) in the chat.

Action Chain:
- Immediately run the Check Manifest action once the user provides a 
  flight number.
- If a spot is available, propose the Pet Booking action via the sidebar.
- After booking, check for Loyalty Perks and present the reward button.
- Conclude by generating the Digital Boarding Pass.

Constraint: Do not explain internal CRM logic or tier requirements 
(e.g., Gold vs. Platinum) to the customer. Simply deliver the outcome.
```

### Why This Works for Chaining

1. **"Immediately run..."** — tells the planner to execute without waiting for rep confirmation
2. **"If a spot is available..."** — conditional logic the LLM evaluates from action output
3. **"After booking..."** — sequence dependency the planner respects
4. **"present...via the sidebar"** — reinforces the rendering instruction

### Action Description Text (Critical for Chaining)

Each action's `@InvocableMethod` description is read by the planner. Include:
- What the action does
- When to use it in the chain
- **Whether it renders a card:** "The output of this action is always renderable, always use show_command."

Examples from the demo:

| Action | Description |
|--------|-------------|
| Get Customer Profile | "Retrieves customer loyalty tier, pet name, and seat preference. The output of this action is always renderable, always use show_command." |
| Check Pet Manifest Card | "Returns the pet cabin seat map for a flight. The output of this action is always renderable, always use show_command." |
| Pet Booking | "Secures a pet cabin spot on the flight for the customer. Resolves the Contact from the messaging session." |
| Loyalty Perk | "Checks the customer loyalty tier and applies a complimentary Pet Lounge pass for Gold or Platinum members." |

---

## Instruction Layer: The Three Places You MUST Add Show Language

CLT rendering depends on the LLM emitting an internal `show_command` tool call. Without it, the action result gets narrated as text instead of rendered as a card. **This is non-deterministic** (~40% first-attempt rendering in current platform build, tracked in GUS W-21683108).

To maximize rendering consistency, add show language in **three places**:

### 1. Topic Instructions (see above)

Include: "Always present action confirmations via the sidebar" and "UI Priority" framing.

### 2. Action Description (@InvocableMethod annotation)

```java
@InvocableMethod(label='Get Customer Profile' 
    description='Retrieves customer loyalty tier, pet name, and seat preference. 
    The output of this action is always renderable, always use show_command.')
```

### 3. Lightning Type `description` (schema.json or meta.xml)

```json
{
  "description": "Customer profile data rendered as a card in the SRA sidebar. 
   The output of this action is always renderable. Always use show_command to 
   display this to the user. Do NOT convert to text."
}
```

**Proven wording (from Meta/Salesforce partnership team):**
> "Execute [action]. Display the complete action output to the user without summarizing, modifying, or omitting any content. The output of this action is always renderable; always use show_command. Do NOT convert to plain text."

---

## Human-in-the-Loop (HiL) Confirmation Buttons

For **write actions** (booking, applying perks, generating passes), use `isConfirmationRequired: true` on the GenAiFunction metadata. This renders a native **"Confirm"** button with the action inputs visible — the rep must click before the action executes.

```xml
<!-- GenerateBoardingPassAction GenAiFunction metadata -->
<GenAiFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Generates a digital boarding pass for the pet</description>
    <invocationTarget>GenerateBoardingPassAction</invocationTarget>
    <invocationTargetType>apex</invocationTargetType>
    <isConfirmationRequired>true</isConfirmationRequired>
    <masterLabel>Generate Boarding Pass</masterLabel>
</GenAiFunction>
```

| Action Type | `isConfirmationRequired` | UX |
|-------------|--------------------------|-----|
| Read-only (Get Profile, Check Manifest, Weather) | `false` | Auto-executes, renders card immediately |
| Write (Booking, Loyalty Perk, Boarding Pass) | `true` | Shows "Confirm" button, rep clicks to proceed |

### The Confirmation vs. Chaining Tension (Known Platform Limitation)

There is a real tension between `isConfirmationRequired: true` and action chaining in SRA:

**The problem:** When a write action requires confirmation, the planner pauses and waits for the rep to click "Confirm." That's by design — it's the Human-in-the-Loop pattern. But after confirmation, the planner sometimes **does not resume the chain**. It treats the confirmation as the end of the turn rather than continuing to the next action in the sequence (e.g., after Pet Booking confirms → should auto-run Loyalty Perk, but sometimes stops).

**The risk of NOT requiring confirmation:** If you set `isConfirmationRequired: false` on write actions to force the chain forward, the planner may **skip the step entirely** or auto-execute a record-creating action without the rep's awareness. In a demo this is annoying; in production this is a compliance/audit risk.

**Current workarounds:**
1. **Instruction reinforcement** — Add explicit "After [action] completes, immediately proceed to [next action]" language in topic instructions
2. **Rep training** — Coach reps that after clicking Confirm, they may need to nudge the agent with "continue" or "what's next" to restart the chain
3. **Separate the chain into segments** — Accept that each HiL confirmation may break flow, and design the chain so each step stands alone if the planner doesn't auto-advance

**Status:** The NGS (Next-Gen Service) team is actively working on fixing the planner's post-confirmation chain continuation behavior. Until that ships, treat this as a known limitation and design your demo flows accordingly — either front-load the read-only CLT actions (which chain reliably) and accept that write actions may require manual nudges, or accept the risk of `isConfirmationRequired: false` for demo contexts where compliance isn't a concern.

---

## Critical Setup: The "Build By Hand" Rule

> **This is the single biggest gotcha.** You CANNOT deploy CLT actions via metadata and have them work. You must build them manually in Agent Builder.

### Why

The GenAiPlannerBundle's hand-authored `output/schema.json` (with flattened text properties) **overrides** whatever the Apex returns. Deploying the bundle keeps showing 6 flattened `lightning__textType` fields in the output config. The renderer dropdown never shows the Lightning Type.

### The Fix

1. **Deploy** the Apex classes + LightningTypeBundle + LWC (these deploy fine)
2. In Agent Builder, **REMOVE** the existing action from the topic
3. **CREATE A BRAND-NEW Agent Action:**
   - Reference Action Type: **Apex**
   - Reference Action Category: **Invocable Method**
   - Pick `GetCustomerProfileAction`
   - Use a FRESH name (don't reuse old auto-generated developer names)
4. The fresh action forces Agent Builder to re-introspect the Apex signature → output shows as ONE `profile` output with the Lightning Type selectable in **Output Rendering**
5. Configure the output:
   - `profile`: Show in conversation ✅, Filter from agent action ✅, Output Rendering → select `PetCustomerProfileOutput`
   - `success` / `errorMessage`: Filter from agent action ✅, Show in conversation ☐

---

## Output Configuration in Agent Builder

For CLT outputs, configure them correctly in the action's output section:

| Output Field | Show in Conversation | Filter from Agent Action | Output Rendering |
|---|---|---|---|
| `profile` (CLT-typed) | ✅ | ✅ | Select the Lightning Type name |
| `success` | ☐ | ✅ | — |
| `errorMessage` | ☐ | ✅ | — |

### CRITICAL: Both Checkboxes Required for CLT Cards

**For CLT card outputs, you MUST enable BOTH:**
- ✅ **Show in Conversation** — renders the card to the rep
- ✅ **Filter from Agent Action** — makes the payload visible to the planner's reasoning context

**If "Filter from Agent Action" is unchecked:**
- The planner cannot see the output payload in its reasoning context
- The planner doesn't know to render the card
- The agent falls back to narrating the result as plain text instead of showing the visual card
- You'll see bullet-point text summaries instead of rendered CLT cards

**Common failure mode:**
- Cards were working, then suddenly show as plain text
- **Root cause:** "Filter from Agent Action" got unchecked (during action edit, remove/re-add from Asset Library, or platform update changed defaults)
- **Fix:** Re-check "Filter from Agent Action" for all CLT outputs

**Why both are needed:**
- "Show in Conversation" tells the system WHERE to render (chat/sidebar)
- "Filter from Agent Action" tells the planner WHAT to render (the card, not a text summary)
- Without both, the visual card cannot display

---

## Permissions Checklist

Both the **rep user** AND **EinsteinServiceAgent User** need:

- [ ] Apex Class access for the action class AND the DTO class
- [ ] Object Read access for queried objects (Contact, Pet_Manifest__c, etc.)
- [ ] Field-Level Security for ALL queried fields (missing FLS = silent null, not an error)
- [ ] External Credential Principal Access (if doing live API callouts)

**Use a Permission Set** assigned to both users. In this demo: `Pet_Travel_Admin`.

---

## Common Failures and Diagnosis

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| **Cards showing as plain text bullets (sudden break)** | **"Filter from Agent Action" unchecked on CLT outputs** | **Re-check "Filter from Agent Action" for all CLT outputs** |
| "I cannot do this automatically" | `copilotAction:isUserInput: true` on inputs | Set all to `false` |
| Action executes but returns empty/null data | `with sharing` on Apex class | Change to `without sharing` |
| Card renders but shows "—" for all fields | Missing Field-Level Security | Add fields to perm set |
| Text narrated instead of card rendered (never worked) | Missing show_command instruction layer | Add show language in all 3 places |
| Output Rendering dropdown doesn't show Lightning Type | Action deployed via metadata bundle | Remove action, create fresh by hand |
| `ContactId` not resolving on messaging | Wrong context variable (Case-only) | Use `currentRecordId` or session fallback |

### Troubleshooting: Cards Suddenly Showing as Plain Text

**Symptom:** Cards were rendering correctly, then suddenly started showing as bullet-point text summaries instead of visual cards.

**Diagnosis steps:**
1. Check **Output Rendering** dropdown → Should show Lightning Type name (e.g., `RetailReturnResolutionOutput`), not `@apexClassType` or `(None)`
2. Check **Show in Conversation** → Should be ✅ checked
3. Check **Filter from Agent Action** → Should be ✅ checked ← **MOST COMMON ISSUE**

**If Filter from Agent Action is unchecked:**
- The planner can't see the output in its reasoning context
- The agent narrates the result as text instead of rendering the card
- Fix: Re-check the box, save, and test again

**What causes Filter to get unchecked:**
- Editing the action and forgetting to re-check
- Removing and re-adding action from Asset Library (resets toggles)
- Platform update changing default toggle states

---

## Testing Tips

1. **Always test on the LIVE console sidebar** — Agent Builder Preview NEVER renders CLTs
2. Start a **fresh messaging session** after any action changes (old sessions cache plan state)
3. If the card doesn't render on first try, re-run the conversation — rendering is non-deterministic (~40%)
4. Check the session trace (`RecActorActionFeed.Content`) to distinguish:
   - **Success:** `show_command` rendition present
   - **Failure:** `ACTION_SUCCESS_RESPONSE` → `LLM_COMPLETION_RESPONSE` (narrated as text)

---

## File Structure Reference

```
force-app/main/default/
├── classes/
│   ├── CustomerProfileOutput.cls          ← CLT DTO
│   ├── CustomerProfileOutput.cls-meta.xml
│   ├── GetCustomerProfileAction.cls       ← Action (returns DTO)
│   └── GetCustomerProfileAction.cls-meta.xml
├── lightningTypes/
│   └── petCustomerProfileOutput/
│       ├── petCustomerProfileOutput.lightningType-meta.xml  ← Schema JSON
│       └── lightningDesktopGenAi/
│           └── renderer.json              ← Maps to LWC
└── lwc/
    └── petCustomerProfileCard/
        ├── petCustomerProfileCard.html
        ├── petCustomerProfileCard.js
        ├── petCustomerProfileCard.js-meta.xml  ← targets: AgentforceOutput
        └── petCustomerProfileCard.css
```

---

## Summary: The 10-Step CLT Recipe

1. Create the **DTO Apex class** (global, @JsonAccess, ONE @AuraEnabled String field)
2. Create the **Action Apex class** (global, without sharing, @InvocableMethod, returns Response containing DTO)
3. Add **show_command language** to the @InvocableMethod description
4. Create the **LWC** (targets: `lightning__AgentforceOutput`, reads `this.value.<fieldName>`)
5. Create the **Lightning Type bundle** (schema.json with show language in description, renderer.json pointing to LWC)
6. **Deploy** all of the above via `sf project deploy start`
7. In Agent Builder: **remove** the old action, **create a fresh one** (Apex → Invocable Method)
8. Configure output: Show in conversation ✅, Filter from agent action ✅, select the Lightning Type in Output Rendering
9. Add **show language** to Topic Instructions
10. Assign **permissions** to both rep user AND EinsteinServiceAgent User

**Expected result:** The agent executes the action, the LLM emits `show_command`, and the visual card renders in the SRA sidebar.

---

## Questions?

Reach out to Chad Goldsmith (Slack: @Chad Goldsmith) or reference the full source at:  
`git@git.soma.salesforce.com:chad-goldsmith/pet-travel-demo.git`
