---
name: sf-clt-builder
description: >
  Build Apex-based Custom Lightning Type (CLT) cards for Agentforce surfaces —
  Service Rep Assistant, Employee Agent (LEX), Enhanced Chat v2, and Agentforce Cowork.
  Generates renderer DTOs, Invocable actions, LWC renderers, Lightning Type bundles,
  GenAiFunction schemas, and surface-specific write-back. TRIGGER when the user asks
  to build, add, or generate a custom Lightning Type / CLT / chat card / visual action
  output for SRA, employee chat, Enhanced Chat, Cowork, or Agentforce. DO NOT TRIGGER
  for object-schema CLTs (Experience Builder, Prompt Builder, Mosaic), MIAW v1, Slack /
  Block Kit, or plain record-page LWCs. For a card that will not render, also load
  agentforce-lightning-types (ECv2 preflight, ShowCommand, known platform bugs).
tools: [Bash, Read, Write, Edit]
---

# Custom Lightning Type (CLT) Builder

Generates Apex-based CLT cards that render an LWC instead of narrating action results as text.

The **envelope is the same on every surface.** Channel folder, write-back API, and sharing
model are not. Pick the surface first — see [guides/surfaces.md](guides/surfaces.md) — then
generate files from the templates.

**Verified reference (Path A / SRA):** Summit Ridge — 8 Lightning Types, 8 read actions,
4 write actions, shared `summitRidgeReply` helper. Cards rendered in the Service Rep
Assistant sidebar on first use after deploy.

**Runtime/debug:** `agentforce-lightning-types` owns ECv2 Connection/ESD republish,
ShowCommand vs InformCommand, Daisy++ tool names, and GUS bugs. Load it whenever the
card will not render, and **always** when the target is Enhanced Chat v2.

**Do not use this skill for:** object-schema CLTs (`lightning__objectType` for Experience
Builder, Prompt Builder, Flow structured outputs, Mosaic widgets) — use
`generating-custom-lightning-type`. MIAW (Chat v1). Slack / Block Kit. Plain LWCs on
record, app, or home pages.

---

## When to Use This Skill

Activate when the user asks to:
- Build a CLT / Custom Lightning Type / card / visual output for an Agentforce action
- Show a card in Service Rep Assistant, the Employee Agent LEX panel, Enhanced Chat v2,
  or Agentforce Cowork
- Add rendered output to an existing action
- Build an action chain where some steps render visual cards
- Port a working card from one of those surfaces to another

**Do NOT use for:** actions that return plain text only; object-based CLTs; MIAW v1;
Slack; LWCs that are not targeted at `lightning__AgentforceOutput`.

---

## Step 0: Pick the surface before generating anything

Ask (or infer) which surface the card will render on. Then apply the adapter. Full
rationale, privacy warning, and write-back contracts: [guides/surfaces.md](guides/surfaces.md).

| Surface | Channel folder | Write-back | Sharing / run-as |
|---|---|---|---|
| **SRA sidebar** | `lightningDesktopGenAi` only | `copytochat` / `acc:execute`; Messaging send via `conversationToolkitApi` | `without sharing`; permset on EinsteinServiceAgent **and** the rep |
| **Employee Agent LEX panel** | same folder | `lightning/accApi` `execute()` (documented). Do **not** assume `copytochat` works | logged-in user; `with sharing` unless proven otherwise |
| **Enhanced Chat v2** | same folder; **do not add** `enhancedWebChat/` | `this.configuration?.util.sendTextMessage(...)` | portal user vs botUser; **must** also load `agentforce-lightning-types` |
| **Agentforce Cowork** | treat as Employee LEX until proven | **none** — display-only or `NavigationMixin`. Label any write-back unverified | logged-in user |

Salesforce's compatibility table lists `enhancedWebChat` as a valid ECv2 channel, and
ECv2 **falls back** to `lightningDesktopGenAi` when that folder is missing. Adding
`enhancedWebChat/renderer.json` has broken working desktop configs in field testing.
Default is: **one folder, `lightningDesktopGenAi`.** Do not port a rep card to customer
chat without stripping internal fields — the fallback is silent.

---

## Dual naming — the easy-to-get-wrong join

Four artifacts, four conventions, joined by explicit references — not string matching.
Summit Ridge example for "Customer Equipment":

| Artifact | Convention | Example | Who points at it |
|---|---|---|---|
| Apex DTO class | PascalCase + `Output` | `SummitRidgeEquipmentOutput` | LT `schema.json` → `@apexClassType/c__SummitRidgeEquipmentOutput` |
| Lightning Type **folder** | camelCase + `Output` | `summitRidgeEquipmentOutput` | GenAi output `lightning:type` → `c__summitRidgeEquipmentOutput` |
| LWC folder | camelCase + `Card` | `summitRidgeEquipmentCard` | `renderer.json` → `c/summitRidgeEquipmentCard` |
| DTO JSON field | `<noun>JSON` | `equipmentJSON` | LWC reads `this.value.equipmentJSON` |
| GenAiFunction folder | `Brand_Verb_Noun` | `Summit_Ridge_Get_Customer_Equipment` | planner `<source>` / Action Library API Name |
| Apex action class | `BrandVerbNounAction` | `SummitRidgeGetEquipmentAction` | GenAi `invocationTarget` |

The LT schema points at the **Apex class**. The action schema points at the **LT folder**.
Swapping those two is a silent blank card.

---

## Display flags (Path A — closed)

These are two independent flags. Help articles that treat `filter_from_agent` as the
render-tool gate are mixing them with `isDisplayable`.

Verified across all 8 Summit Ridge card actions:

| Output | `copilotAction:isDisplayable` | `copilotAction:isUsedByPlanner` | `lightning:type` |
|---|---|---|---|
| the CLT field (the card) | `true` | **`false`** | `c__<lightningTypeFolderName>` |
| passthroughs used for chaining | `false` | **`true`** | `lightning__textType` / `booleanType` / `numberType` |
| `success` / `errorMessage` | `false` | `false` | boolean / text |

In the Builder UI: **Show in Conversation** = `isDisplayable`. **Filter from Agent
Action** is the *inverse* of `isUsedByPlanner` — ON hides the card JSON from the
planner so it cannot narrate it as text. Lift the 2–3 scalars the next action needs
into their own unfiltered outputs.

Path B (Agent Script) uses `is_displayable` / `filter_from_agent` on the `.agent`
output. Same idea: card is displayable and filtered from the planner; a short
narrative or passthrough scalars stay visible. Do not start from Help's
`filter_from_agent: False` on the card — that is what made planners summarize JSON.

---

## Core Architecture: The Single-JSON-Field DTO Pattern

Every CLT has four layers. Generate them in this order:

```
1. CLT DTO (Apex class)        — Single @AuraEnabled String field holding serialized JSON
2. Action Class (Apex)          — @InvocableMethod returning Response that contains the DTO
3. Lightning Type Bundle        — Maps Apex DTO → LWC renderer
4. LWC Component                — Renders the card from this.value.<fieldName>
5. GenAiFunction (+ planner)    — Path A: deployable action + topic wiring
```

### The Critical Rule

**ONE field. ONE serialized JSON string. `@AuraEnabled` — NOT `@InvocableVariable`.**

Multiple `@InvocableVariable` fields on the DTO get flattened into separate text outputs
by Agent Builder schema introspection, which breaks CLT rendering entirely.

The two annotations sit one level apart and each is wrong in the other's position:

| Location | Annotation | Why |
|---|---|---|
| The single `String` field **inside the DTO** | `@AuraEnabled` only | `@AuraEnabled` exposes it to the LWC. Adding `@InvocableVariable` here is what triggers flattening. |
| The **DTO-typed field on the action's `Response`** | `@InvocableVariable` | This is how the DTO becomes a declared action output at all. Without it the output does not exist and there is nothing to bind the Lightning Type to. |

So the DTO is invisible to the planner from the inside and declared from the outside.
Get these backwards in either direction and the card silently renders as text.

---

## Verified Reference Implementation

Extracted from the Summit Ridge telecom build: **8 Lightning Types**, 8 read (card)
actions, 4 write (no-card) actions, one shared reply-routing LWC. Every invariant
below was mechanically verified across all classes. Cards rendered in the SRA sidebar.

**Structural invariants — 100% consistent across all 8 card actions:**

- Sharing is **surface-specific**. Summit Ridge (SRA / EinsteinServiceAgent) used
  `global without sharing` on every action — that user has no sharing access to
  Contact/Asset. Employee Agent / Cowork default to `with sharing` unless the run-as
  user is proven to have no sharing. See [guides/surfaces.md](guides/surfaces.md).
- `global static List<Response> execute(List<Input> inputs)` — the bulk signature, always.
- Every action wraps its body in `try / catch (Exception e)`.
- **Zero `throw new` statements across the entire codebase.** An action that throws
  produces no output, so the card cannot render and the user sees a generic failure.
  Every failure path returns a well-formed DTO carrying `{"error": "..."}`, and the
  LWC renders an error state. This is the single highest-leverage reliability decision.

**Response-class shape.** Card actions carried 4–7 outputs, and the extra ones matter:

```apex
global class Response {
    @InvocableVariable global Boolean success;

    @InvocableVariable(label='Customer Equipment'
        description='Structured payload for the summitRidgeEquipmentCard renderer')
    global SummitRidgeEquipmentOutput equipment;      // the card

    // Flat passthroughs so the planner can chain without re-parsing the card JSON.
    @InvocableVariable global Integer deviceCount;
    @InvocableVariable global String  faultyDeviceName;
    @InvocableVariable global String  faultyDeviceId;

    @InvocableVariable global String  errorMessage;
}
```

The card JSON is opaque to the planner by design (`isUsedByPlanner: false`). If the
next action needs the faulty device's ID, lift it. Do this sparingly: every unfiltered
output is extra reasoning context.

**Put the business rule in Apex, then surface it twice.** Only a `Degraded` device is
RMA-eligible — an `Offline` device is usually a symptom of the upstream outage. That
rule is encoded once in Apex and emitted both as `rmaEligible` per device inside the
card JSON (so the button only appears where it should) and as a `faultyDeviceId`
passthrough (so the planner can chain). Never leave a judgement like that to the LLM
or to the LWC.

**Resolve the customer through a fallback ladder, not one input** (SRA / messaging
demos). All Summit Ridge reads used the same three tiers:

1. the explicit `customerId` input, when the planner supplies it;
2. otherwise look up `MessagingSession.EndUserContactId` from `messagingSessionId`;
3. otherwise the most recent `Status = 'Active'` session with a non-null contact.

Tier 3 makes cards demo-safe when the planner calls with no arguments. Declare every
input `required=false`. **This ladder is for READS only.** Never use it to choose a
send target — see [A Card Button Has Three Possible Destinations](#a-card-button-has-three-possible-destinations).

**Format for humans in Apex, not in the LWC.** Dates converted to `'MMM yyyy'`, health
defaulted (`String.isBlank(...) ? 'Healthy' : ...`) before serialization. The LWC stays
a pure renderer.

**Scope every query to the demo.** Filter on a demo-owned field
(`AND SummitRidge_Equipment_Type__c != NULL`) so a shared org's unrelated assets never
surface. An unscoped `SELECT` in a shared demo org is a live grenade.

**Static resources: one resource per image.** Zip static resources do not serve by
sub-path here (`/resource/<zip>/<file>.png` 404s). Import each image as its own
resource.

**The LWC binding contract.** All eight cards were byte-for-byte consistent here:

```js
@api value;

connectedCallback() {
    try {
        const raw = this.value.equipmentJSON;   // MUST match the Apex DTO field name
        const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
        if (parsed.error) { this.errorMessage = parsed.error; return; }
        this.data = parsed;
    } catch (e) {
        this.errorMessage = 'Error loading equipment.';
    }
    // Resolve send target OUTSIDE the parse try/catch so a messaging miss
    // can never blank the card.
    resolveConversationContext().then((ctx) => { this.context = ctx; });
}
```

The property after `this.value.` is the Apex DTO's field name — rename `equipmentJSON`
in Apex and the card goes blank with no deploy error. The `typeof raw === 'string'`
guard exists because the platform sometimes hands the value over already parsed.

**Write actions look different, and should.** `UpgradePlan`, `BookAppointment`,
`StartRma`, `ResetRouter` have no DTO and no `show_command` — they return plain scalars
including a `confirmation` string. Cards trigger them with `acc:execute` utterances.
Reserve CLTs for reads. Template: [templates/write-action-class.cls](templates/write-action-class.cls).

---

## Generation Steps

When asked to build a CLT, follow this sequence:

### Step 0: Surface

Confirm the surface (table above). If Enhanced Chat v2, also load
`agentforce-lightning-types` before generating. If Cowork, generate display-only
buttons and label any write-back as unverified.

### Step 1: Gather Requirements

Ask (or infer from context):
1. **Which surface?** (SRA / Employee LEX / ECv2 / Cowork)
2. **What data does the card display?** (fields, layout concept)
3. **What object(s) does the action query?**
4. **Is this a read-only or write action?** Writes get [templates/write-action-class.cls](templates/write-action-class.cls), not a CLT
5. **Does this chain with other actions?** (passthrough scalars + topic language)
6. **What's the card name?** (drives the dual-naming table)

### Step 2: Generate the DTO

Use template: [templates/dto-class.cls](templates/dto-class.cls)

Rules:
- `global` access modifier on class and field
- `@JsonAccess(serializable='always' deserializable='always')` on class
- ONE `@AuraEnabled global String <name>JSON` field
- Two constructors: one with param, one no-arg (empty string default)
- Field name convention: `<cardPurpose>JSON` (e.g., `profileJSON`, `equipmentJSON`)

### Step 3: Generate the Action Class

Use template: [templates/action-class.cls](templates/action-class.cls)

Rules:
- Sharing from the surface table — SRA: `global without sharing`; Employee/Cowork: `with sharing` unless proven otherwise
- Signature is always `global static List<Response> execute(List<Input> inputs)`
- Input class: all fields `@InvocableVariable` with `required=false`
- On SRA / messaging demos: include `messagingSessionId` and the three-tier Contact ladder
- Response class: `success` + the DTO field (`@InvocableVariable`) + 2–3 passthrough scalars + `errorMessage`
- `@InvocableMethod` description MUST include: "The output of this action is always renderable, always use show_command."
- Scope every SOQL query to a demo-owned field
- Format dates and defaults in Apex before serializing
- Build payload as `Map<String, Object>`, serialize with `JSON.serialize()`, wrap in DTO constructor
- Wrap the body in `try / catch (Exception e)` and **never `throw`** — every failure path
  returns a valid DTO carrying `{"error": "..."}`

### Step 4: Generate the Lightning Type Bundle

Use template: [templates/lightning-type/](templates/lightning-type/)

Three files in `force-app/main/default/lightningTypes/<typeName>/`:

1. `<typeName>.lightningType-meta.xml` — **real XML**, requires `masterLabel`. The
   filename in working deploys is `*.lightningType-meta.xml` (not
   `lightningTypeBundle-meta.xml`).

2. `schema.json` — title, description (include show_command language; **capped at 255
   characters**), and `lightning:type` pointing at the **Apex DTO class**:
   `@apexClassType/c__<DtoClassName>`.

3. `lightningDesktopGenAi/renderer.json` — maps `$` to the LWC, inside a `renderer`
   wrapper. **Do not add `enhancedWebChat/`.**

```json
{ "renderer": { "componentOverrides": { "$": { "definition": "c/<lwcName>" } } } }
```

> **Two corrections to earlier versions of this skill.** The meta.xml is not JSON —
> putting JSON in it fails with `Required field is missing: masterLabel`. And
> `renderer.json` needs the `renderer` wrapper on API 67.0, without which the deploy
> fails with an `additionalProperties` error.

### Step 5: Generate the LWC

| Surface | Template |
|---|---|
| Read-only card | [templates/lwc/](templates/lwc/) |
| SRA interactive (`copytochat` / `acc:execute`) | [templates/lwc-interactive/](templates/lwc-interactive/) |
| SRA + customer send | also generate [templates/lwc-reply-routing/](templates/lwc-reply-routing/) as `isExposed=false` |

Rules:
- `js-meta.xml`: apiVersion **67.0**, `masterLabel`, `description`, targets
  `lightning__AgentforceOutput` (+ `lightning__AgentforceInput`)
- JS: `@api value`, parse `this.value.<fieldName>` in `connectedCallback()`
- Resolve send/context **outside** the parse `try/catch`
- HTML: SLDS card layout, handle error state
- Interactive template includes `sendOnSurface()` — branch on `this.configuration?.util`
  (ECv2) vs console APIs (SRA) vs no-op (Cowork)
- Design at chat-widget width (~380px)

### Step 6: Generate the Action and Wire It Into the Topic

Actions and their attachment to a topic are **deployable**. Generate the metadata;
fall back to the UI only if you want to.

**6a. The action** — use [templates/genAiFunction/](templates/genAiFunction/):

```
<Action_Name>.genAiFunction-meta.xml    masterLabel, invocationTarget (Apex class),
                                        invocationTargetType=apex, isConfirmationRequired
input/schema.json                       one property per @InvocableVariable input
output/schema.json                      one property per @InvocableVariable output
```

Generate both schemas **from the Apex signature**, never by hand — a stale hand-written
schema is what produces the "flattened text fields, Lightning Type missing from the
dropdown" symptom.

Apply the [display flags](#display-flags-path-a--closed) table. Inputs all get
`copilotAction:isUserInput: false`, or the agent replies "I cannot do this automatically".

**6b. The wiring** — in the `GenAiPlannerBundle`, inside the target `<localTopics>`:

1. `<localActionLinks><functionName>` — links topic to action
2. `<localActions>` — a topic-local copy whose `<source>` names the global `GenAiFunction`
3. `localActions/<topic>/<action>/{input,output}/schema.json` — the same schemas again

**6c. Deploy.** The agent must be deactivated to accept action changes:

```bash
sf agent deactivate -n <Agent> -o <org>
sf project deploy start -m "GenAiFunction:<Action_Name>" -m "GenAiPlannerBundle:<Agent>" -o <org>
sf agent activate -n <Agent> -o <org>
```

**Rules the platform enforces:**

- A topic-local action **is itself a `GenAiFunction` record**, so its `developerName`
  must be unique org-wide and cannot equal the global action it points at — otherwise
  `duplicate value found`. Suffix the local one; keep `<source>` unsuffixed.
- Element order inside `<localTopics>` is fixed: instructions, `language`, all
  `localActionLinks`, all `localActions`, then `localDeveloperName`.
- `sf project retrieve start --output-dir` silently retrieves **nothing**. Retrieve
  into the package directory instead.

**If you build it in the UI instead:** use the Asset Library (not "Create New Action"
inside a subagent), give it a fresh developer name, and set the same toggles — Show in
Conversation = `isDisplayable`, Filter from Agent Action = **inverted**
`isUsedByPlanner`, Output Rendering = `lightning:type`.

### Step 7: Generate Topic Instruction Language

For each CLT action:

```
Execute [Action Name]. Display the complete action output to the user without
summarizing, modifying, or omitting any content. The output of this action is
always renderable; always use show_command. Do NOT convert to plain text.
```

Reference the action by its **exact Action Library API Name**, not a friendly label.
For chained actions, also generate the sequencing language
([guides/chaining.md](guides/chaining.md)).

---

## A Card Button Has Three Possible Destinations

Before wiring any button, decide which of these it targets. They are different APIs
with different audiences, and conflating them is how a card meant for a rep ends up
messaging a customer.

| Destination | Who sees it | API | Surfaces |
|---|---|---|---|
| The **agent panel** | Rep only | `copytochat` / `acc:execute` (undocumented, SRA only), or `execute()` from `lightning/accApi` (documented, LEX desktop) | SRA, Employee LEX |
| The **live customer conversation** | External customer | `sendTextMessage` / `setAgentInput` from `lightning/conversationToolkitApi` | SRA console on a Messaging tab |
| The **customer chat widget** | External customer | `this.configuration.util.sendTextMessage(...)` | Enhanced Chat v2 only |
| The **clipboard** | Rep only | `@api getFormattedValue()` | LEX desktop |
| **Nowhere (Cowork)** | — | Display-only / `NavigationMixin` until a write-back is verified | Cowork |

"Explain to customer" text is usually already written in second person, which means
it is a **customer reply that has been pointed at the agent panel**. Sending it to
the customer is a destination change, not a content rewrite.

> ### Safety rule: never let the server choose the send target
>
> Apex actions commonly resolve the customer with a fallback ladder ending in *"the
> most recent Active MessagingSession."* That is fine for **reading** — a wrong card
> is visible and recoverable. It is **not safe for sending.** An org can easily have
> several Active sessions at once, so that fallback can name a different customer's
> conversation, and the reply is delivered with no undo.
>
> Resolve the send target **client-side, from the tab the rep is actually looking
> at**, via [templates/lwc-reply-routing/](templates/lwc-reply-routing/)
> (`resolveConversationContext()`). Prefixes: Messaging `0Mw`, Case `500`, Voice `0LQ`.
>
> `null` / `other` is a normal outcome — fall back to the agent panel. Resolve it
> *outside* the parse `try/catch` so a messaging miss can never stop the card
> rendering, and label the button for what it will actually do ("Send to customer"
> vs "Explain to customer").

**Host context — CONFIRMED WORKING (2026-09-02).** `lightning/conversationToolkitApi`
is callable from inside the Agentforce panel (`lightning__AgentforceOutput`). A card
rendered in the panel delivered a message into a live customer conversation. No
bridge component was needed. Keep the fallback — it's undocumented.

> ### Detect success as "did not reject", never as `=== true`
>
> The docs state these methods resolve `true` on success. **In practice
> `sendTextMessage` resolves `undefined` while genuinely delivering the message.**
> A strict `=== true` check reads a successful send as a failure — and if the caller
> falls back to the agent panel, the text is delivered to the customer *and* copied
> into the assistant draft.
>
> ```js
> return (await sendTextMessage(sessionId, { text })) !== false;   // not === true
> ```
>
> Once a messaging session is in play, don't fall back to the agent panel at all.
> Report failure on the button label ("Send failed — retry").

There is **no Apex or REST path** for a rep reply in-thread.

---

## Channel Portability

See [guides/surfaces.md](guides/surfaces.md) for the adapter table. Short version:

- Generate **only** `lightningDesktopGenAi/renderer.json`. Do not add `enhancedWebChat/`.
- ECv2 falls back to desktop config when `enhancedWebChat` is missing — a rep card
  can therefore reach an external customer without anyone opting in. Strip internal
  fields before that org is used for customer chat.
- Slack cannot render LWCs. Experience Builder is editor-only.
- Write-back APIs are mutually unavailable across surfaces. Branch at runtime on
  `this.configuration?.util` if one LWC must serve more than one channel.

**"Service Rep Assistant" is a naming trap.** Two different things live in the Service
Console:

- An **Agentforce agent** (`GenAiPlannerBundle` with topics whose actions genuinely
  execute) surfaced in the LEX panel. This is `lightningDesktopGenAi` and CLTs work —
  this is what Summit Ridge uses.
- The **Service Assistant** Lightning component on the Case page, where actions added
  "are only used as additional grounding and treated like instructions." If actions
  only ground rather than execute, there is no action output for a renderer to intercept.

Confirm which of the two you are building on by checking whether your actions execute.

---

## Interactive / Write-Back CLTs (CLT → SRA chat)

> **Sourcing caveat.** `copytochat` and `acc:execute` are **verified empirically**
> in the SRA panel. A documentation review found **no Salesforce reference
> documentation for either event**. Treat them as undocumented/internal. The
> documented equivalents are `lightning/accApi`'s `execute()` (rep-facing) and
> `configuration.util.sendTextMessage()` (ECv2).
>
> **"Dynamic Plan mode"** is retained as an empirical observation, not a cited rule.

**SRA panel only.** These events are NOT handled by the standard Agentforce / ACC
panel, Employee LEX (unless re-verified), Enhanced Chat, or Cowork.

| Event | Effect |
|-------|--------|
| `copytochat` | Drops text into the chat **input box** — rep reviews/edits before sending |
| `acc:execute` | **Auto-sends** text into chat history as if the rep typed it — agent responds |

```js
this.dispatchEvent(new CustomEvent('acc:execute', {   // or 'copytochat'
    detail: { content: 'Identity verification passed' },
    bubbles: true,
    composed: true
}));
```

**Hard requirements:**
- Event name is EXACTLY `copytochat` **or** `acc:execute` — the combined
  `"copytochat/acc:execute"` silently no-ops.
- Payload is `detail: { content: '<string>' }`; `bubbles: true` AND `composed: true`.
- SRA must be in **Dynamic Plan mode**, not Guidance Plan mode.

Use [templates/lwc-interactive/](templates/lwc-interactive/).
Working example: [examples/interactive-verification-card/](examples/interactive-verification-card/).
Deep dive: [guides/interactive-writeback.md](guides/interactive-writeback.md).

---

## Confirmation vs. Chaining: Known Platform Limitation

**The problem:** `isConfirmationRequired: true` pauses the chain for rep confirmation.
After the rep clicks Confirm, the planner sometimes does NOT resume — it treats the
confirmation as end-of-turn.

**The risk of `false`:** the planner may skip the step or auto-execute a
record-creating action without awareness.

**Workarounds:** (1) "After [action] completes, immediately proceed to [next action]"
in topic instructions; (2) accept a "continue" nudge; (3) front-load read-only CLT
actions, which chain reliably, before writes.

NGS is working on post-confirmation continuation. Design demos around this until it ships.

---

## Three-Place Instruction Layer (Non-Negotiable)

CLT rendering is non-deterministic (~40% first-attempt, GUS W-21683108). Add show
language in ALL THREE places:

| Location | Where | What to add |
|----------|-------|-------------|
| 1. `@InvocableMethod` description | Action class | "The output of this action is always renderable, always use show_command." |
| 2. Lightning Type `schema.json` `description` | LT bundle (255-char cap) | "Always use show_command to display this to the user. Do NOT convert to text." |
| 3. Topic Instructions | Agent Builder / planner | "Display the complete action output...always use show_command. Do NOT convert to plain text." |

If any one of these is missing, rendering rate drops further. Location 2 is
`schema.json`, not the meta.xml — the meta description is a short label and is easy
to overflow.

---

## File Naming Conventions

Given a card purpose like "Customer Profile" and brand prefix `pet`:

| Component | File/Folder Name |
|-----------|-----------------|
| DTO class | `CustomerProfileOutput.cls` |
| Action class | `GetCustomerProfileAction.cls` |
| Lightning Type folder | `petCustomerProfileOutput/` |
| LWC folder | `petCustomerProfileCard/` |
| LT `schema.json` `lightning:type` | `@apexClassType/c__CustomerProfileOutput` |
| GenAi output `lightning:type` | `c__petCustomerProfileOutput` |

---

## Common Pitfalls to Prevent

| Mistake | Consequence | What to do instead |
|---------|------------|-------------------|
| `@InvocableVariable` on DTO field | Agent Builder flattens to text outputs | Use `@AuraEnabled` |
| `with sharing` on SRA / EinsteinServiceAgent actions | Silent empty results | `without sharing` on that surface; `with sharing` on Employee/Cowork unless proven otherwise |
| Multiple fields on DTO | No CLT rendering | Single `<purpose>JSON` field |
| LT schema points at the folder, or GenAi `lightning:type` points at the Apex class | Silent blank card | Dual-naming table — class vs folder |
| Card `isUsedByPlanner: true` | Planner narrates the JSON as text | `isDisplayable: true`, `isUsedByPlanner: false`; lift passthrough scalars |
| Missing `@JsonAccess` | Serialization failures | Always add `serializable='always' deserializable='always'` |
| Missing no-arg constructor on the DTO | Platform deserialization fails | Always ship both constructors |
| Omitting `@InvocableVariable` on the Response's DTO field | The output never exists | `@AuraEnabled` inside the DTO, `@InvocableVariable` on the Response field |
| Deploying the GenAiPlannerBundle while the agent is active | `Cannot update record as Agent is Active` | Deactivate → deploy → reactivate |
| JSON inside `.lightningType-meta.xml` | `Required field is missing: masterLabel` | Real XML with `masterLabel`; JSON goes in `schema.json` |
| `renderer.json` without the `renderer` wrapper | `additionalProperties` deploy error on API 67.0 | Wrap `componentOverrides` in `renderer` |
| Adding `enhancedWebChat/renderer.json` | Can override a working desktop config | `lightningDesktopGenAi` only |
| Lightning Type `description` over 255 chars | `Value too long for field: Description` | Trim, keeping the show_command sentence |
| Hand-building the error JSON string | Quote/newline breaks `JSON.parse` | `JSON.serialize(new Map<String,Object>{'error' => e.getMessage()})` |
| `throw` inside an action | No output, so the card can't render | Catch and return a DTO carrying `{"error": ...}` |
| Filtering `EndUserContactId` after the query | Newest active session with a null contact returns nothing | `WHERE Status='Active' AND EndUserContactId != NULL` |
| Using the Apex session ladder as a **send** target | Wrong customer's live conversation | Client-side `resolveConversationContext()` |
| Unscoped SOQL in a shared demo org | Unrelated demo records surface | Filter on a demo-owned field |
| Zip static resource referenced by sub-path | Image 404s, blank tiles | One static resource per image |
| `isUserInput: true` on action inputs | Agent says "I cannot do this automatically" | Set all to `false` |
| Missing FLS for queried fields | Silent null values (not errors) | Include in permission set checklist |
| Combined event name `copytochat/acc:execute` | Write-back silently no-ops | Fire ONE event |
| Testing SRA write-back in the AF/ACC panel | Event never received | Test in the SRA panel with Dynamic Plan mode on |
| `sendTextMessage(...) === true` | Successful send looks like failure; duplicate into the panel | `!== false`; no panel fallback once a session is in play |
| Assuming `copytochat` works on Employee LEX / ECv2 / Cowork | Silent no-op | Surface table — those APIs are not portable |
| LDS-backed `@wire` inside ECv2 | `ldsWebruntimeOneStoreInit` (W-21533738) | Imperative Apex; see `agentforce-lightning-types` |

---

## Relationship to Other Skills

| Need | Skill |
|---|---|
| **Generate** the CLT artifacts (this skill) | `sf-clt-builder` |
| **Debug** a card that will not render (ECv2 Connection, ESD republish, ShowCommand, GUS bugs) | `agentforce-lightning-types` |
| Object-schema CLTs (Experience Builder, Prompt Builder, Mosaic) | `generating-custom-lightning-type` |
| Builder topics / GenAiFunction / PromptTemplate maintenance | `sf-ai-agentforce` |
| Agent Script `.agent` files | `sf-ai-agentscript` |
| SRA runtime diagnostics (wrong Output Rendering, missing `show_command`) | `sra-agent-debugger` |
| Full SRA demo scaffolding | `build-agentforce-service-demo` (CLT-GUIDE is a narrative companion, not a second generator) |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-22 | Initial skill creation — extracted from CLT guide + pet-travel-demo learnings |
| 2026-08-17 | Added interactive/write-back CLT support (`copytochat` / `acc:execute` events). New `guides/interactive-writeback.md`, `templates/lwc-interactive/`, and `examples/interactive-verification-card/`. Customer sandboxes ~8/22 (262.14). |
| 2026-09-02 | Corrected two template bugs (`TEMPLATE-lightningType-meta.xml` was JSON; `renderer.json` lacked the `renderer` wrapper). Rewrote Step 6 as deployable `GenAiFunction` + `GenAiPlannerBundle`. Added Summit Ridge invariants, Channel Portability, destinations / `conversationToolkitApi`, and the `!== false` success rule. |
| 2026-09-05 | **Multi-surface generator.** Trigger now covers SRA, Employee Agent LEX, Enhanced Chat v2, and Agentforce Cowork (unverified write-back). Added Step 0 surface adapter ([guides/surfaces.md](guides/surfaces.md)), dual-naming table, and closed the Path A display-flag rule from all 8 Summit Ridge card actions (`isDisplayable: true` / `isUsedByPlanner: false` on the card; passthroughs inverse). Sharing is surface-specific, not always `without sharing`. New templates: GenAiFunction schemas, write-action class, reply helper with 0Mw/500/0LQ, `sendOnSurface()` stub. LWC apiVersion 67.0. Delegates ECv2 runtime/debug to `agentforce-lightning-types`. Reference is now 8 Lightning Types, 8 reads, 4 writes, shared `summitRidgeReply`. |
| 2026-09-10 | Removed internal Slack citations. Packaged as an unofficial skill pack with installer and architecture docs. |
