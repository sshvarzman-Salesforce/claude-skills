---
name: generating-clt-components
description: Build, deploy, and reliably invoke Custom Lightning Types (CLTs) from Agent Script. Covers the LWC envelope-unwrap pattern that makes a CLT renderable in both Agent Builder and Embedded Messaging, the Apex+Flow wrapper required to feed it from a GenAiFunction, the Agent Script ergonomics that make the planner actually call the action, and the failure modes (planner skips action, payload arrives but card is blank, Setup preview crashes, Embedded Messaging shows nothing after agent edits). TRIGGER when the user wants to render a custom card/component from an agent action, debug a CLT that "doesn't render," port a CLT to a new agent, or asks "why isn't my action being called."
---

# generating-clt-components — Building & rendering Custom Lightning Types from Agent Script

A Custom Lightning Type (CLT) is the only reliable way to display a custom-designed UI component (cart, carousel, file uploader, recommendation card, confirmation receipt) inside Agentforce conversations. Unlike plain text replies, CLT output **bypasses Atlas's final-response paraphraser** and renders verbatim — that's why every demo-grade UI in Agentforce ships through a CLT and not through styled markdown.

This skill encodes the end-to-end recipe from a working production demo (AcmeRetail FDE engagement, two custom CLTs in service: `checkoutReview_46d7f6` for an order-change cart, `asaCarousel` for a TV-selection carousel, plus a third that **failed** — `exchangeCheckout` — and was abandoned). The lessons from the failure are baked in.

**Provenance:** verified 2026-05-26 against agent `EnhancedChatV2Test` on `agentforce-sandbox` (org `00Dxxxxxxxxxxxxxxx`), Atlas v2 planner, Embedded Messaging V2 deployment.

## When to use

Trigger this skill when the user:
- Wants to **render a custom UI** (cart, carousel, picker, receipt, confirmation card) in an Agentforce conversation, not just a text bubble.
- Has a **non-rendering CLT** — payload looks right in Apex/Flow logs, but the card is blank in chat.
- Has a **CLT that the planner refuses to call** — Atlas replies with text only, no `ACTION_STEP` ever fires.
- Says **"my CLT preview is broken in Setup"** — the Lightning Type Builder shows blank or errors.
- Wants to **port a working CLT to a new agent or new field shape** — needs the value-handling pattern that survives both Builder preview and runtime.
- Asks **"why doesn't my action get invoked"** in a multi-step Agent Script flow.

## When NOT to use

- User wants to build the LWC visual design from scratch with no agent integration → that's plain LWC dev, no CLT needed.
- User is replacing the chat launcher itself (the floating button/banner) → use `agentforce-embedded-launcher`.
- User is debugging an existing chat session's runtime trace (which actions fired, why a topic was chosen) → use `agentforce-investigator-fullstack`.
- User is on Embedded Messaging V1 (legacy Live Chat) — CLT plumbing differs; this skill is V2 only.

## The four-layer stack you must build for every CLT

A CLT is not just an LWC. It's a **stack of four metadata pieces** that all have to line up. Every "my CLT doesn't render" bug traces back to one of these four layers being mis-named, mis-wired, or stale.

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — LightningTypeBundle                              │
│  force-app/main/default/lightningTypes/<typeName>/          │
│    ├── schema.json                                          │
│    ├── enhancedWebChat/renderer.json                        │
│    └── lightningDesktopGenAi/renderer.json                  │
│  Registers the type "c__<typeName>" in the org's type       │
│  registry. Without this, the GenAiFunction output schema    │
│  fails validation with "property type not found."           │
└─────────────────────────────────────────────────────────────┘
                             │
                             │  references via lightning:type=c__<typeName>
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — GenAiFunction                                    │
│  force-app/main/default/genAiFunctions/<Function_Name>/     │
│    ├── input/schema.json   (Details: string)                │
│    ├── output/schema.json  (CheckoutDetails: c__<typeName>) │
│    └── <Function_Name>.genAiFunction-meta.xml               │
│  Output schema's lightning:type MUST match the bundle name. │
│  copilotAction:isDisplayable=true is mandatory or the       │
│  planner won't show_command the result.                     │
└─────────────────────────────────────────────────────────────┘
                             │
                             │  invocationTargetType = flow
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — Flow + Apex wrapper class                        │
│  force-app/main/default/flows/<Function_Name>.flow-meta.xml │
│  force-app/main/default/classes/<TypeName>Data.cls          │
│  An Apex @AuraEnabled class with one String field           │
│  (e.g. checkoutReview_46d7f6JSON) holding the JSON payload. │
│  An autolaunched Flow assigns the Details input string into │
│  that Apex field, returns the Apex object as the Flow       │
│  output variable named CheckoutDetails (matching the        │
│  GenAiFunction output property name).                       │
└─────────────────────────────────────────────────────────────┘
                             │
                             │  CheckoutDetails.<typeName>JSON
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4 — LWC component                                    │
│  force-app/main/default/lwc/<typeName>/                     │
│    ├── <typeName>.js   (envelope-unwrap + builder fallback) │
│    ├── <typeName>.html                                      │
│    ├── <typeName>.css                                       │
│    └── <typeName>.js-meta.xml                               │
│  Receives the Apex object via @api value, unwraps the JSON  │
│  envelope, normalizes data, renders the markup.             │
└─────────────────────────────────────────────────────────────┘
```

If you are debugging "CLT doesn't render," **read those four boxes in order**. The bug is always in one of them.

## The load-bearing LWC pattern (the single most common reason CLTs fail)

This is the lesson that took a full day of debugging on the AcmeRetail demo to discover. **The LWC `value` property cannot be a plain `@api`.** Both Setup preview and runtime envelope wrapping break it.

### What fails

```js
// BROKEN — this is what we wrote first for exchangeCheckout, and it never worked
import { LightningElement, api } from 'lwc';
export default class extends LightningElement {
    @api value;  // ← plain api property

    connectedCallback() {
        const json = this.value.exchangeCheckoutJSON;  // ← assumes one envelope shape
        this.parsed = JSON.parse(json);
    }
}
```

Two things go wrong:

1. **Setup preview** — the Lightning Type Builder renders the LWC with `value=null` to show a preview. `this.value.exchangeCheckoutJSON` throws on null, the preview is blank. To the developer it looks like the bundle is broken.
2. **Runtime envelope** — the platform sometimes wraps the Apex output in `{ value: { exchangeCheckoutJSON: "..." } }`, sometimes in `{ exchangeCheckoutJSON: "..." }` directly, sometimes nested under the GenAiFunction output property name (e.g. `{ CheckoutDetails: { exchangeCheckoutJSON: "..." } }`). A single-shape unwrap fails on two of three deliveries.

### What works (use this verbatim)

The pattern that survived production:

```js
import { LightningElement, api } from 'lwc';

const __APEX_ENVELOPE_FIELD = "checkoutReview_46d7f6JSON";    // ← match your Apex class field name
const __NESTED_ENVELOPE_CONTAINER = 'CheckoutDetails';          // ← match your GenAiFunction output property name

function __buildDefaultViewModel() {
  return { /* … shape every template binding expects … */ };
}

function __normalizeCheckoutModel(payload) { /* … coerce every field, defaulting nulls/missing … */ }

function __peelValueWrapper(parsed) {
  // Handles { value: {…} } wrapping that Embedded Messaging sometimes adds
  if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
    const keys = Object.keys(parsed);
    if (keys.length === 1 && keys[0] === 'value' && parsed.value && typeof parsed.value === 'object') {
      return parsed.value;
    }
  }
  return parsed;
}

function __parseEnvelopeField(fieldValue) {
  if (typeof fieldValue !== 'string' || !fieldValue.trim()) return null;
  try { return __normalizeCheckoutModel(__peelValueWrapper(JSON.parse(fieldValue))); }
  catch { return null; }
}

function __unwrapApexEnvelope(raw) {
  if (raw == null) return raw;
  // Sometimes the platform pre-stringifies the Apex object
  if (typeof raw === 'string') {
    try { return __normalizeCheckoutModel(JSON.parse(raw)); }
    catch { return null; }
  }
  if (typeof raw !== 'object') return null;

  const peeled = __peelValueWrapper(raw);
  // Shape A: peeled object IS the Apex envelope ({ checkoutReview_46d7f6JSON: "…" })
  if (peeled && __APEX_ENVELOPE_FIELD in peeled) {
    return __parseEnvelopeField(peeled[__APEX_ENVELOPE_FIELD]);
  }
  // Shape B: peeled object wraps the Apex envelope under the GenAiFunction output name
  // ({ CheckoutDetails: { checkoutReview_46d7f6JSON: "…" } })
  const nested = peeled && peeled[__NESTED_ENVELOPE_CONTAINER];
  if (nested && typeof nested === 'object' && __APEX_ENVELOPE_FIELD in nested) {
    return __parseEnvelopeField(nested[__APEX_ENVELOPE_FIELD]);
  }
  // Shape C: already a normalized payload
  return __normalizeCheckoutModel(peeled);
}

// Builder fallback — Setup preview sets value=null. Without this, the preview is blank
// and developers think the bundle is broken.
const BUILDER_FALLBACK_JSON = "{\"orderTotal\":\"$0\",\"itemCount\":0, … }";   // realistic sample
let __builderFallbackParsed;
function __getBuilderFallback() {
  if (__builderFallbackParsed !== undefined) return __builderFallbackParsed;
  if (BUILDER_FALLBACK_JSON && BUILDER_FALLBACK_JSON !== '__BUILDER_FALLBACK_PAYLOAD__') {
    try { __builderFallbackParsed = __normalizeCheckoutModel(JSON.parse(BUILDER_FALLBACK_JSON)); }
    catch { __builderFallbackParsed = null; }
  } else {
    __builderFallbackParsed = null;
  }
  return __builderFallbackParsed;
}

export default class extends LightningElement {
  _value;

  @api
  get value() { return this._value != null ? this._value : __getBuilderFallback(); }
  set value(v) {
    this._value = __unwrapApexEnvelope(v);
    // Re-run connectedCallback so any @track state hydrated from this.value picks up
    // edits the parent makes after the initial paint. Guard on isConnected so the first
    // synchronous assignment during element setup is a no-op.
    if (this.isConnected && typeof this.connectedCallback === 'function') {
      try { this.connectedCallback(); } catch (err) { console.error('connectedCallback re-hydrate failed', err); }
    }
  }
}
```

The four invariants:
1. **`@api` on getter/setter, not plain property.** This is what lets you intercept `value=null` and substitute the builder fallback.
2. **Three-shape envelope unwrap** (`raw apex` / `{ value: … }` / `{ <NestedContainer>: … }`). Two shapes fail in production.
3. **Builder fallback is a real, complete payload.** Setup preview renders it when `value` is null. Without it, `c__<type>` shows blank in Setup → Lightning Type → Preview.
4. **Re-run `connectedCallback` on setter.** Embedded Messaging mutates `value` after first paint when the parent agent updates the message; without re-hydration, the card is stuck on first-render data.

A copy-pasteable, full-working version of this LWC lives at `templates/clt-lwc-template.js` in this skill.

## The Apex + Flow wrapper that feeds the CLT

The GenAiFunction can in theory call Apex directly (`invocationTargetType: apex`), but **every working CLT in production wraps the Apex call in a Flow.** The reason: the Flow lets you declaratively format the JSON string before assigning it into the Apex object, and the Flow's `Variables` block is what registers the output as a renderable Apex type for the GenAiFunction. Apex-direct shipping has been observed to silently drop the renderable flag.

### Apex data class (1 file, ~10 lines)

```apex
@JsonAccess(serializable='always' deserializable='always')
global with sharing class CheckoutReview_46d7f6Data {
    @AuraEnabled global String checkoutReview_46d7f6JSON;
}
```

Field name is **load-bearing** — it must match the `__APEX_ENVELOPE_FIELD` constant in the LWC. Convention: `<lwc_name>JSON`.

### Autolaunched Flow (assigns Details input → Apex field)

The Flow has:
- One **input variable** `Details` (String).
- One **output variable** `CheckoutDetails` (Apex type → `CheckoutReview_46d7f6Data`, isOutput=true).
- One **assignment** `CheckoutDetails.checkoutReview_46d7f6JSON = SUBSTITUTE({!Details}, "\\\"", "\"")`.

The `SUBSTITUTE` is **mandatory.** Atlas occasionally emits the JSON with double-escaped quotes (`\\"` instead of `\"`) when the planner upstream emitted it as a raw string. Without the substitute, the LWC's `JSON.parse` throws on the malformed input and the CLT renders blank.

A copy-pasteable Flow XML is at `templates/clt-flow-meta.xml`.

### GenAiFunction wiring

The function has:
- **Input** `Details: string` (free-form JSON string the planner emits).
- **Output** `CheckoutDetails: c__<typeName>` with:
  - `copilotAction:isDisplayable: true` (mandatory)
  - `lightning:isPII: false`
  - `copilotAction:isUsedByPlanner: true` (lets the planner reason about whether to call it)
  - `copilotAction:useHydratedPrompt: false`
- The function's `.genAiFunction-meta.xml` references `flow://<Function_Name>` as the invocation target.

A copy-pasteable schema set is at `templates/genai-function/`.

### LightningTypeBundle (registration)

`force-app/main/default/lightningTypes/<typeName>/schema.json`:
```json
{ "type": "object", "properties": { "<typeName>JSON": { "type": "string" } } }
```

Plus two renderer JSONs (`enhancedWebChat/renderer.json` and `lightningDesktopGenAi/renderer.json`) that point the chat surface and the Builder preview to the same LWC. Both files have the same content:

```json
{ "lwc": { "name": "c/<typeName>" } }
```

**Without `enhancedWebChat/renderer.json` the CLT will not render in Embedded Messaging chat** — only in Agent Builder preview. We discovered this when our `c__fileUploadResponse` type fell back to the platform's default uploader because our bundle was missing this file. A copy-pasteable bundle is at `templates/lightning-type-bundle/`.

## Agent Script — making the planner actually call the action

This is where most CLT failures show up at *demo time*, not at *deploy time*. The CLT works in isolation, but the agent never invokes it.

### Action declaration in Agent Script

Inside the subagent's `actions:` block (the LIST of actions the planner sees), and again at the topic-level `actions:` block (the FUNCTION definition), declare the action like this:

```
# In the subagent's reasoning.actions: block (planner-visible list)
Checkout_Summary: @actions.Checkout_Summary
    with Details = ...

# In the subagent's `actions:` block at the bottom (function definition)
actions:
    Checkout_Summary:
        description: "Renders the order-change checkout review CLT inline. Shows line items, extra charges, FIRST member benefits, contact, and payment. The output is always renderable — use show_command. Wraps the existing checkoutReview_46d7f6 LWC via the Checkout_Summary GenAiFunction + Flow."
        label: "Checkout Summary"
        require_user_confirmation: False
        include_in_progress_indicator: True
        progress_indicator_message: "Summarising the cart..."
        source: "Checkout_Summary"
        target: "flow://Checkout_Summary"

        inputs:
            "Details": string
                description: |
                  JSON cart payload (single string). Shape: { … realistic sample shape … }. Normal JSON, not escaped.
                label: "Details"
                is_required: True
                is_user_input: False
        outputs:
            CheckoutDetails: object
                description: "Renderable checkout review CLT — always show via show_command."
                label: "CheckoutDetails"
                complex_data_type_name: "c__<typeName>"
                filter_from_agent: False
                is_displayable: True
```

The output's `complex_data_type_name` MUST be `c__<typeName>` exactly matching the LightningTypeBundle directory name. **Off-by-one casing or pluralization here is the single most common deploy-time error** ("property type c__exchangeCheckout not found in registry").

### Phase instruction — making the planner actually call it

Atlas v2 has a "one tool per turn unless instructed otherwise" bias. The planner will happily emit your phase's text and skip the action call if it thinks the text alone satisfies the user-visible portion of the instruction. We saw this in the AcmeRetail demo's Phase 2 (file uploader) — text emitted, action never invoked.

**The pattern that works:**

1. Lead with a mandate sentence that names the action: *"You **MUST** invoke `{!@actions.Checkout_Summary}` on this turn. Do not reply with text alone — the action call is mandatory."*
2. Make the action call **step 1**, the text **step 2**. Atlas processes numbered steps in order; reversing this lets it stop after step 1 and skip the tool.
3. Include the exact JSON payload to pass as `Details` in a fenced ```json``` block.
4. End with **STOP AND WAIT** so the planner knows not to chain into another action.

Example, transcribed from a working production demo:

```
# PHASE 4 — CHECKOUT CART (After product selection)
When user selects any TV from the carousel, you MUST invoke
{!@actions.Checkout_Summary} on this turn. Do not reply with text alone — the
action call is mandatory.

1. Run {!@actions.Checkout_Summary} to display the order-change cart. The output
   is always renderable. Always use `show_command` to display the result. Pass
   `Details` as this exact JSON:
   ```json
   {"orderTotal":"$820.00","itemCount":1, … full payload … }
   ```
2. Acknowledge the selection in one short line: "Great choice. Here's your order
   change summary:"
3. STOP AND WAIT for the user to click Confirm Order.
```

The full source of the AcmeRetail demo's Order_Management subagent (4 phases × 2 CLT calls) lives in `templates/example-agent-script-AcmeRetail.md` for reference.

## The two operational rules nobody tells you

These two rules turn a working CLT into a *reliably* working CLT in front of customers.

### Rule 1: Always re-publish the Embedded Messaging deployment after activating a new agent version

When you publish a new agent version (Setup → Agentforce → Agents → Publish), the **agent gets a new version number** but the **Embedded Messaging deployment continues serving the old version** until you republish the deployment too. Customers on the live site will keep hitting the old planner — including old action declarations, old phase instructions, old CLT references. We've seen "my CLT doesn't render" turn out to be "the chat is still on the previous agent version where the CLT didn't exist yet."

After every agent publish:
1. Setup → Embedded Service Deployments → your deployment → Edit
2. Bump the version (or just hit Save)
3. Publish

Wait ~30 seconds for the new bundle to propagate, then test. The fastest way to verify: open chat, append `?launcherTrace=1` to the URL, watch the console for the agent version printed during `onEmbeddedMessagingFirstBotMessageSent` — it should match what you just published.

### Rule 2: Every LWC change requires a deploy AND a hard-refresh of the chat

LWCs are cached aggressively by both the platform and the browser. A `sf project deploy start -d force-app/main/default/lwc/<typeName>` is necessary but not sufficient. To see your edit:

1. Deploy the LWC: `sf project deploy start -d force-app/main/default/lwc/<typeName> -o <org-alias>`.
2. Hard-refresh the page hosting the chat (Cmd-Shift-R on Mac, Ctrl-Shift-R on Windows). Soft-refresh keeps the cached LWC.
3. If still not seeing the change: open chat → close → reload → reopen. The Embedded Messaging iframe sometimes pins the LWC version on first launch.
4. Last resort: `sf project deploy start -d force-app/main/default/lightningTypes/<typeName>` as well — sometimes the bundle's renderer.json caches stale.

### Rule 3: Three org-setup toggles that block rendering before you ever reach the LWC

These are easy to miss because they live in Setup, not in your metadata, so a clean deploy hides them. Confirm all three before you blame the LWC or the planner:

1. **Switch Web (v2) → Chat V2.** Setup → Embedded Service Deployments → your deployment → **Embedded Service Deployment Settings**. The deployment must be on **Chat V2**, not the older Web (v2) mode — CLT rendering plumbing only exists on Chat V2.
2. **Confirm the agent has a Connection of type "Enhanced Chat (v2)".** Open Agent Builder → your agent → **Connections** and verify an **Enhanced Chat (v2)** connection is listed (add it if missing). This is the channel the Embedded Messaging surface uses to deliver the CLT — without it the planner can run the action but the rendered card has no route to chat, so it silently never appears. A type mismatch here (e.g. an older Web/v2 connection, or no connection at all) produces the same blank-card symptom as a broken LWC, so check it *before* you touch metadata. **The trace fingerprint:** when this connection is missing the planner reports `__supports_result_display__ = False`, and the action's result-display is gated off with `Action <subagentName,actionName> result-display eligible=False (reason=capability_gate_missing)`. If you see either line in the trace, the cause is the missing connection — not the LWC, Flow, or schema.
3. **Enable Show_Commands.** Without it the planner can run the action but never surfaces (`show_command`) the renderable result, so the card silently never appears.

After changing any of these, re-publish the agent **and** the Embedded Messaging deployment (Rule 1). (Source: CLT Builder field notes, M. Tallis, 2026-06.)

## Failure mode catalogue — symptom → cause → fix

| Symptom | Likely cause | Fix |
|---|---|---|
| **CLT doesn't render** — chat shows nothing where the card should be | Planner never called the action (no `ACTION_STEP` in DC trace) | Trace via `agentforce-investigator-fullstack` skill, look at the turn's steps. If no ACTION_STEP for your function, the phase instruction is too soft — apply the "MUST invoke" pattern above. |
| **CLT doesn't render**, but DC shows the action *was* called | Apex/Flow returned, but LWC isn't unwrapping the envelope shape it received | Open browser devtools while chat is open, inspect the LWC's `value` property in the Lightning inspector. Check which of the three envelope shapes you got. Make sure your unwrap covers it (see "Load-bearing LWC pattern" above). |
| **Setup preview is blank** when you open the Lightning Type → Preview | LWC has plain `@api value` (not getter/setter) and Setup is calling the LWC with `value=null` | Convert to getter/setter pattern with `BUILDER_FALLBACK_JSON` constant. |
| **"property type c__\<x\> not found in registry"** at deploy time | LightningTypeBundle missing or its directory name doesn't match the GenAiFunction output schema | Verify `force-app/main/default/lightningTypes/<typeName>/` exists with `schema.json` + both renderer JSONs. Verify `complex_data_type_name: "c__<typeName>"` in the agent script exactly matches the directory name (case-sensitive). |
| **CLT renders in Builder preview, but blank in Embedded Messaging chat** | LightningTypeBundle is missing `enhancedWebChat/renderer.json` | Add the renderer JSON. Embedded Messaging is a different chat surface than the Builder preview — each surface has its own renderer file. |
| **CLT never renders; trace shows `__supports_result_display__ = False` or `result-display eligible=False (reason=capability_gate_missing)`** | Agent has no **Enhanced Chat (v2)** Connection, so the planner's result-display capability gate is off and the renderable result is never surfaced | Agent Builder → your agent → **Connections** → add an **Enhanced Chat (v2)** connection (Rule 3, item 2), then re-publish the agent and the Embedded Messaging deployment. |
| **Agent doesn't call the action even after publish** | Embedded Messaging deployment still on old agent version | Re-publish the Embedded Messaging deployment (see Rule 1 above). |
| **JSON.parse error in LWC console** but payload looks right in agent log | Atlas double-escaped the JSON when emitting the Details input | Verify the Flow has `SUBSTITUTE({!Details}, "\\\"", "\"")` on the assignment. |
| **"AsaFileUploadData" classname instead of yours in network payload** | The wrong CLT type registered for the action — platform fell back to default | Double-check the GenAiFunction's `output/schema.json` — the `lightning:type` must be `c__<typeName>`. Also check the Lightning Type Builder's renderer.json for typos. |
| **CLT works on Builder agent but not Embedded Messaging guest user** | Guest user missing perm-set assignments to the underlying Apex class / managed object | Assign `<TypeName>Data` Apex class via SetupEntityAccess (anonymous Apex script in `templates/grant-guest-perms.apex`). |
| **Agent edits stuck — old text still showing** | Cached planner bundle on the deployment | Same as Rule 1: re-publish the EMessaging deployment. |
| **Card appears, then disappears mid-conversation** | Embedded Messaging dropped the `value` because the LWC threw on the second invocation | The LWC's setter must guard `connectedCallback` re-run with `try/catch` and `isConnected` — see invariants in "Load-bearing LWC pattern." |
| **Agent Script rejects the action output's complex data type** — planner forces the fully-qualified form `"@apexClassType/c__<typeName>Data?isAuraEnabled=true"` but the script keeps erroring until you give it the stripped `"c__<typeName>"` | The action was added to the agent while the type was still registered under the Apex-class-qualified name; the planner pins that form and won't accept the stripped registry name | Re-register the action so it picks up the stripped type: **(1)** delete the action from the agent, **(2)** add it to the library in Setup, **(3)** add it back to the agent, **(4)** save and re-publish the Embedded Messaging deployment, then test. The `complex_data_type_name` should now accept `"c__<typeName>"`. (Source: CLT Builder field notes, M. Tallis, 2026-06.) |

## Shortcut: the CLT Builder (accelerator, not a replacement)

Before hand-building all four layers, know that the **CLT Builder** can scaffold most of them for you and deploy straight to your org:

- **Builder:** https://agentforce-clt-builder-e4e03ec84f1a.herokuapp.com/builder
- It generates the LightningTypeBundle, a standalone flow action, and the supporting metadata, then deploys it.

It's a real time-saver for layers 1–3, but treat its output as a starting point, not the finished CLT:

- **Don't bolt the generated flow action on as-is.** If you already have an action whose Apex/Flow produces your JSON output, **merge** the two flows so the payload is passed deterministically into the LWC — rather than running the Builder's action and yours separately.
- **Match your JSON to the Builder's expected shape.** Copy an example payload from the Builder and use it as the exact target format for your existing LWC's output (this is also your `BUILDER_FALLBACK_JSON`).
- The **load-bearing LWC pattern** above (three-shape envelope unwrap, getter/setter, builder fallback) still applies — the Builder does not give you that resilience for free.

If you used the Builder, you can skip to **Step 7 (wire into Agent Script)** below and use steps 1–6 as a checklist to verify what the Builder produced. (Source: CLT Builder field notes, M. Tallis, 2026-06.)

## Step-by-step: build a new CLT from scratch

Skill consumer reading this section: assume you have a designed-but-not-yet-built UI mockup and a description of what data it should show.

1. **Sketch the JSON payload first.** Decide every field the LWC binds to in its template. Make a realistic sample value as a JSON string — this is your `BUILDER_FALLBACK_JSON`.

2. **Build the LWC.** Copy `templates/clt-lwc-template.{js,html,css,js-meta.xml}` into `force-app/main/default/lwc/<typeName>/`. Replace placeholders:
   - `__APEX_ENVELOPE_FIELD` constant → `<typeName>JSON`
   - `__NESTED_ENVELOPE_CONTAINER` → your GenAiFunction's output property name (e.g. `CheckoutDetails`)
   - `BUILDER_FALLBACK_JSON` → your sample payload
   - `__buildDefaultViewModel` → return the shape your template binds to
   - `__normalizeCheckoutModel` → coerce every field to its expected type with safe defaults

3. **Build the LightningTypeBundle.** Copy `templates/lightning-type-bundle/` into `force-app/main/default/lightningTypes/<typeName>/`. Update the `lwc.name` in both renderer JSONs to `c/<typeName>`.

4. **Build the Apex data class.** Copy `templates/clt-data-class.cls` into `force-app/main/default/classes/<TypeName>Data.cls`. Rename the field to `<typeName>JSON` (case-sensitive).

5. **Build the Flow wrapper.** Copy `templates/clt-flow-meta.xml` into `force-app/main/default/flows/<Function_Name>.flow-meta.xml`. Update:
   - `<apexClass>` to your Apex data class
   - `<assignToReference>` to `<OutputVarName>.<typeName>JSON`
   - The output variable name to match what your GenAiFunction expects

6. **Build the GenAiFunction.** Copy `templates/genai-function/` into `force-app/main/default/genAiFunctions/<Function_Name>/`. Update `output/schema.json`'s `lightning:type` to `c__<typeName>`.

7. **Wire into Agent Script.** Copy the action declaration block from "Agent Script — making the planner actually call the action" above. Match the `target:` to `flow://<Function_Name>`.

8. **Add the test class.** Copy `templates/clt-data-class-test.cls` and the corresponding ShowCLT test class. CLTs require 75% Apex code coverage to deploy.

9. **Deploy everything in one shot:**
   ```
   sf project deploy start \
     -d force-app/main/default/lwc/<typeName> \
     -d force-app/main/default/lightningTypes/<typeName> \
     -d force-app/main/default/classes/<TypeName>Data.cls \
     -d force-app/main/default/classes/<TypeName>DataTest.cls \
     -d force-app/main/default/flows/<Function_Name>.flow-meta.xml \
     -d force-app/main/default/genAiFunctions/<Function_Name> \
     -o <org-alias>
   ```

10. **Grant permissions so BOTH the agent's user and the Embedded Messaging guest can run the CLT.** A clean deploy does *not* grant access — the Apex data class (and the Flow behind it) are locked down by default, and the CLT silently renders blank for any principal that lacks access. You must grant **two** principals, because they are two different users:

    **a) The user** — the agent's running/builder user (and your own user while testing in Agent Builder). In Agent Builder the CLT executes as *you*, so without this even the Builder preview comes back blank. Grant via a permission set (recommended) or the user's profile:
    - Setup → **Permission Sets** → (new or existing PS) → **Apex Class Access** → add `<TypeName>Data`.
    - Same PS → **Flow Access** → enable `<Function_Name>` (and any objects/fields the JSON payload reads).
    - Assign the permission set to the agent's running user and to yourself.

    **b) The Embedded Messaging guest user (Sites)** — Embedded Messaging delivers the chat through a Site, so live chat runs as the **Site Guest User**, NOT as a logged-in user. This is the principal that breaks most often — the "works in Builder, blank in chat" symptom in the catalogue. It needs the SAME Apex class / Flow access:
    - Setup → **Embedded Service Deployments** → your deployment → note the **Site** it serves through.
    - Setup → **Sites** → that site → **Public Access Settings** (opens the Guest User Profile) → **Apex Class Access** → add `<TypeName>Data`; then **Flow Access** → enable `<Function_Name>`.
    - Or, scripted + idempotent: run [`templates/grant-guest-perms.apex`](templates/grant-guest-perms.apex) (`sf apex run -f templates/grant-guest-perms.apex -o <org-alias>`), which assigns the Apex class to the guest user's profile permission set via `SetupEntityAccess`. Re-run it per Apex class if your CLT has more than one.

    Grant **both**. Granting only the user makes the Builder preview work while live chat stays blank; granting only the guest makes chat work while the Builder preview stays blank.

11. **Add to the agent**: open Agent Builder → your agent → Topics → the topic that owns the new action → Actions → "+ Add Action" → pick the GenAiFunction. Write a clear description and example.

12. **Publish the agent.**

13. **Re-publish the Embedded Messaging deployment** (Rule 1).

14. **Test in chat with `?launcherTrace=1`.** Verify the action fires (browser console) and the LWC renders.

15. **If it doesn't render**: walk through the Failure mode catalogue above. The bug is in one of the four layers; the catalogue tells you which.

## Reference assets in this skill

- [`templates/clt-lwc-template.js`](templates/clt-lwc-template.js) — the load-bearing LWC pattern, copy-paste ready, all four invariants in place.
- [`templates/clt-lwc-template.html`](templates/clt-lwc-template.html) — minimal HTML scaffold using the `value.*` bindings.
- [`templates/clt-lwc-template.css`](templates/clt-lwc-template.css) — reset + neutral styling.
- [`templates/clt-lwc-template.js-meta.xml`](templates/clt-lwc-template.js-meta.xml) — exposes the LWC for use by Lightning types.
- [`templates/clt-data-class.cls`](templates/clt-data-class.cls) — the @AuraEnabled wrapper class.
- [`templates/clt-data-class-test.cls`](templates/clt-data-class-test.cls) — minimal test for 75% coverage.
- [`templates/clt-flow-meta.xml`](templates/clt-flow-meta.xml) — autolaunched Flow that bridges Details input → Apex field.
- [`templates/lightning-type-bundle/`](templates/lightning-type-bundle/) — schema.json + both renderer JSONs.
- [`templates/genai-function/`](templates/genai-function/) — input + output schemas + meta.xml.
- [`templates/example-agent-script-AcmeRetail.md`](templates/example-agent-script-AcmeRetail.md) — the full AcmeRetail Order_Management subagent showing two working CLTs (Checkout_Summary + TV_Selection_Form).
- [`templates/grant-guest-perms.apex`](templates/grant-guest-perms.apex) — anonymous Apex script to assign Apex class access to the Embedded Messaging guest user.
- [`README.md`](README.md) — same content reformatted for casual reading without invocation context.

## Feedback / questions

#agentforce-fde-team-anz-toolbox on Slack.
