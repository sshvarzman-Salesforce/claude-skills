---
name: agentforce-lightning-types
description: >
  Debug Apex-based Custom Lightning Types (CLTs) on Agentforce chat surfaces —
  Enhanced Chat v2, Employee Agent (LEX), and Mobile. TRIGGER when a CLT renders
  as plain text, renders inconsistently, or does not render in Enhanced Chat v2 /
  a portal; when diagnosing ShowCommand vs InformCommand, ECv2 Connection / ESD
  republish, is_displayable, or known GUS bugs (W-22250928, W-21533738); or when
  working in a lightningTypes/** folder after the artifacts already exist.
  DO NOT TRIGGER to generate a new CLT from scratch — use sf-clt-builder (SRA,
  Employee LEX, ECv2, Cowork). DO NOT TRIGGER for object-based Lightning Types
  (Experience Builder / Prompt Builder — use generating-custom-lightning-type),
  MIAW (non–Chat V2), or plain LWCs on record/app/home pages.
---

# Agentforce Lightning Types

Custom Lightning Types (CLTs) let an Agentforce agent return data that the chat surface renders as a rich LWC — a card, list, form, file uploader, etc. — instead of plain text. This skill owns **runtime and debug** for Apex-based CLTs on chat surfaces (ECv2, Employee LEX, Mobile).

**To generate a new CLT** (DTO, action, Lightning Type bundle, LWC, GenAiFunction, surface adapter), use **`sf-clt-builder`**. That skill produces the artifacts; this one explains why a correctly-authored card still fails to render.

**Agentforce Cowork** has no verified CLT write-back as of 2026-09-05. Treat it as Employee LEX for the envelope (`lightningDesktopGenAi` only) and send generation to `sf-clt-builder`, which labels Cowork write-back as unverified. Do not invent APIs here.

## Pre-flight gate — verify these before debugging anything else

When a CLT doesn't render, the cause is usually **configuration around** the CLT rather than the CLT itself. Walk this list before touching schemas, instructions, or tool names — each item independently prevents rendering, and none of them surface an error.

| # | Check | Where |
|---|---|---|
| 1 | **Enhanced Chat v2 is added as a Connection on the agent** (Service Agent) | Agent Builder → Connections |
| 2 | **ESD Client Version is WebV2**, not V1 | Setup → Embedded Service Deployments |
| 3 | LightningTypeBundle deployed; renderer LWC has the `lightning__AgentforceOutput` target; bundle name matches the action's `complex_data_type_name` | metadata + action def |
| 4 | Permset on the correct run-as user covers the DTO, the action's Apex/Flow, the LT, FLS, object CRUD — **plus every Apex class the LWC calls** | see [Permission sets](#permission-sets-run-as-user--auth-context) |
| 5 | Action was created in the **Action Library first**, then added to the agent | Setup → Agentforce Actions → Actions |
| 6 | `is_displayable: True` on the displayable output | action def |
| 7 | Agent activated **and** ESD republished — after *every* change, **and again whenever a CLT renders as text** even if nothing changed | both |
| 8 | Tested on the real ECv2 surface, not only Builder preview | see [Testing](#testing) |

**#1 is the single most common cause.** A confirmed field case had a correct CLT, correct permsets, correct action wiring and correct instructions, and still rendered nothing — because ECv2 had never been added as a Connection on the Service Agent. Adding it, recommitting and republishing fixed it immediately. Without the ECv2 connection the reply degrades to `formatType: Text`, and no amount of instruction tuning will help. Do **not** add a Telephony connection alongside ECv2 on a standard Service Agent.

**#7 is the cheapest fix and is worth trying before #1.** A confirmed field case: a Service Agent on a freshly created ESD returned real action data but replied in plain prose, no card. Everything verifiable was already correct — all seven LightningTypeBundles present in the org, every renderer LWC declaring `lightning__AgentforceOutput`, the *published* action schema binding `c__<Type>` with `copilotAction:isDisplayable: true`, both `GenAiPlannerFunctionDef` and `GenAiPluginFunctionDef` junctions populated, `clientVersion: WebV2`, and the ESD published a day *after* the agent version was activated. **Republishing the ESD, changing nothing else, made the card render.** So a deployment that was created and published minutes earlier can still be in a stale publish state, and correct timestamps do not prove a good publish. Republish first: it costs seconds, needs no diagnosis, and it resolved this case without ECv2-as-a-Connection ever being the problem.

**#5 matters more than it looks:** creating the action directly inside Agent Builder (instead of building it in the Action Library and then adding it) is a known source of broken wiring. Build in the library first.

## Recommended pattern: the JSON-string DTO envelope

There are two ways the platform can bind an Apex shape to your LWC. **Default to the JSON-string envelope** — it is the pattern proven by current working deployments and documented in depth in the v2 renderer guide:

- The renderer DTO is a tiny `global` Apex class with **one** `@AuraEnabled String <name>JSON` field that holds a stringified JSON payload.
- The LWC reads `this.value.<name>JSON` and does `JSON.parse(...)` in `connectedCallback()`.
- The LightningType binds purely via `schema.json` (`@apexClassType/c__<DtoClass>`) + `renderer.json` (`definition: "c/<lwc>"`). **No `sourceType`, no `targetConfigs`, no `lightning__listType` property** in the LWC `js-meta.xml`.
- "Lists" are not a special binding mode — a list is just an array inside the JSON string. The same envelope handles a single card or a list card.

An older mechanism (`sourceType` for single / `lightning__listType` property for collection, plus a `collection`-nested `renderer.json`) appears in some Salesforce docs. Recent field testing found `targetConfigs`/`sourceType` in the renderer's `js-meta.xml` **break renderer registration**. Treat that approach as legacy — see [Alternative binding](#alternative-binding-sourcetype--lightning__listtype-legacy) and prefer the envelope.

## Configure via Agentforce Builder (Path A) or Agent Script (Path B)

CLT wire-up happens one of two ways. The first three artifacts (renderer DTO, LightningTypeBundle, LWC) are identical in both; only the action declaration, topic wiring, and deploy workflow differ.

| | Path A — Builder + GenAiFunction XML | Path B — Agent Script DSL |
|---|---|---|
| Action declared in | `.genAiFunction-meta.xml` + `output/schema.json` | `.agent` file `actions:` block |
| Wired into topic via | `GenAiPlannerBundle` XML (`localTopics`/`localActionLinks`/`localActions`) | `subagent` block in the `.agent` file |
| Action body | Flow (Apex-typed output var) or Apex Invocable | Apex Invocable (`target: "apex://..."`) |
| Deploy | `sf project deploy start` (agent **deactivated** for planner changes) | `sf agent validate` → `sf agent publish` → `sf agent activate` |

**How to tell:** if `aiAuthoringBundles/<Bundle>/<Bundle>.agent` exists and the bot has `<agentDSLEnabled>true</agentDSLEnabled>`, you're on Path B; otherwise Path A.

> Both paths support both **agent types** (`EinsteinServiceAgent`, `AgentforceEmployeeAgent`) and both **surfaces** (Enhanced Web Chat v2, in-org Lightning Agentforce panel). Agent type, surface, and path are independent dimensions. Older guidance ("use Builder, Agent Script output rendering is inconsistent") still applies if you want maximum stability, but Path B is in active use — the working LEA example below is a Path B Employee Agent.

## The binding chain (mental model)

A renderer is the end of a chain that starts at the topic instructions and ends at your LWC's `@api value`. Each link knows only about the next:

```
Topic / subagent instructions
  ↓ (planner picks the action AND decides ShowCommand vs InformCommand)
GenAiFunction (Path A) / .agent action (Path B)
  ↓ runs
Flow (Path A) / Apex Invocable (Path B) → returns the renderer DTO instance
  ↓ output declared displayable + typed to the Lightning Type
client resolves c__<lightningType> → LightningTypeBundle → renderer.json → c/<lwc>
  ↓
LWC mounts with @api value = the renderer DTO
```

The planner — not your code — makes the final call on whether the widget renders. See [ShowCommand vs InformCommand](#showcommand-vs-informcommand-the-1-silent-failure).

## End-to-end build order

1. **Renderer DTO** — tiny `global` class, one `@AuraEnabled String ...JSON` field.
2. **LWC** — parses the JSON and renders (`lightning__AgentforceOutput` [+ `lightning__AgentforceInput`]).
3. **LightningTypeBundle** — `schema.json` (→ DTO) + `lightningDesktopGenAi/renderer.json` (→ LWC).
4. **Action** — Apex Invocable (Path B) or GenAiFunction+Flow (Path A) returning the DTO as a displayable output.
5. **Deploy** in dependency order (DTO → service/flow → LT+LWC → action → permset → planner/publish).
6. **Permission set** assigned to the correct **run-as user** (agent-type dependent), covering the LWC's Apex controllers too.
7. **Render directive** on the action description + output schema description, with a minimal topic/subagent instruction.
8. **Activate the agent, republish the ESD**, then walk the pre-flight gate and test on the real surface.

## Decision tree

1. **Agentforce chat surface?** (Service Agent in Enhanced Chat v2, Employee Agent panel in LEX, or Mobile.) → Apex-based CLT (this skill).
2. **Experience Builder, Prompt Builder, or Flow Structured Outputs?** → object-based CLT (`lightning__objectType`); use `generating-custom-lightning-type`.
3. **MIAW (standard, not Chat V2)?** → Stop. CLTs are not supported.
4. **Just an LWC on a record page?** → Stop. Use a normal LWC.

## File anatomy

```
force-app/main/default/
├── lightningTypes/
│   └── Acme_AccountHealth/                       # folder name → c__Acme_AccountHealth
│       ├── Acme_AccountHealth.lightningTypeBundle-meta.xml
│       ├── schema.json                           # → @apexClassType/c__Acme_AccountHealthData
│       └── lightningDesktopGenAi/
│           └── renderer.json                     # → c/acmeAccountHealth  (ONLY this folder)
├── classes/
│   ├── Acme_AccountHealthData.cls(+meta)         # renderer DTO: global, @JsonAccess, 1 @AuraEnabled String
│   └── Acme_AccountHealthService.cls(+meta)      # @InvocableMethod; Response holds the DTO
└── lwc/
    └── acmeAccountHealth/
        ├── acmeAccountHealth.html
        ├── acmeAccountHealth.js                  # @api value; JSON.parse(value.<x>JSON)
        ├── acmeAccountHealth.js-meta.xml         # targets: AgentforceOutput + AgentforceInput
        └── acmeAccountHealth.css
```

`LightningTypeBundle`/LWC use API **63.0+** (62.0 floor for the Agentforce targets; 64.0+ to match newer bundle features). Note the three names use three different conventions on purpose: LightningType folder (`Acme_AccountHealth`), LWC bundle (lower-camel `acmeAccountHealth`), DTO class (`Acme_AccountHealthData`). They are joined by explicit references, not string matching.

## Contracts (follow exactly)

### Renderer DTO vs domain DTO — don't conflate them

| | Domain DTO (your service's working types) | **Renderer DTO** (the wire bridge) |
|---|---|---|
| Visibility | `public` is fine | **`global`** (LightningType `@apexClassType` refuses non-global) |
| Annotations | usually none | `@JsonAccess(serializable='always' deserializable='always')` + `@AuraEnabled` on the field |
| Shape | whatever fits the domain (nested, lists, maps) | **one `String` field** holding stringified JSON, nothing else |
| Reuse | heavily reused | **one per renderer; never share** |

The renderer DTO is small but load-bearing and **not substitutable** by a domain class, an inline `String` on the Response, or a shared "all renderers" DTO. The platform binds the LightningType to a *named, typed, deployed `global`* class; the action's output field must be that same Apex type; the LWC reads its `@AuraEnabled` field by literal name.

```apex
@JsonAccess(serializable='always' deserializable='always')
global class Acme_AccountHealthData {
    @AuraEnabled global String healthJSON;          // the ONLY field; LWC reads this.value.healthJSON
    global Acme_AccountHealthData(String healthJSON) { this.healthJSON = healthJSON; }
    global Acme_AccountHealthData() { this.healthJSON = ''; }   // parameterless ctor required for rehydration
}
```

**Why one JSON String instead of typed fields:** nested Apex types (lists of inner classes, maps with non-primitive keys, deep DTOs) do not reliably round-trip across the chat-client boundary; a top-level `String` always does. The LWC parses JS anyway, so the Apex "type safety" buys nothing at that boundary. When the payload shape changes you edit the LWC + JSON-building code only — the DTO, LightningType, and wiring stay frozen. Build a `Map<String, Object>` in the service, `JSON.serialize(...)` it, hand the string to the DTO. (Flat primitive-only shapes *can* use typed `@AuraEnabled` fields — the older HighlightCard example does — but prefer the envelope for anything richer.)

### Apex action (the service class)

The action's `@InvocableMethod` returns `List<Response>`; the `Response` inner class carries the displayable DTO **and** a plain-text narrative.

```apex
public with sharing class Acme_AccountHealthService {
    public class Request {
        @InvocableVariable(required=true label='Account ID') public String accountId;
    }
    public class Response {
        @InvocableVariable public Boolean success;
        @InvocableVariable public String healthAssessment;   // narrative the LLM reads → outputs.healthAssessment
        @InvocableVariable(label='Account Health Card')
        public Acme_AccountHealthData accountHealth;          // displayable DTO → outputs.accountHealth
        @InvocableVariable public String message;
    }
    @InvocableMethod(label='Get Account Health' description='Assess account health.')
    public static List<Response> execute(List<Request> requests) {
        List<Response> responses = new List<Response>();
        for (Request req : requests) {
            Response r = new Response();
            try {
                r.healthAssessment = buildNarrative(/* ... */);
                r.accountHealth = new Acme_AccountHealthData(buildHealthJSON(/* ... */));
                r.success = true; r.message = 'OK';
            } catch (Exception e) {
                r.success = false; r.message = 'Error: ' + e.getMessage();
                r.accountHealth = new Acme_AccountHealthData(           // ALWAYS populate, even on error
                    '{"error":"' + e.getMessage().replace('"','\\"') + '"}');
            }
            responses.add(r);
        }
        return responses;
    }
}
```

Annotation rules — note which join each protects:
- **`@InvocableVariable` on `Response` fields**, *not* `@AuraEnabled`. `@AuraEnabled` belongs only on the field inside the DTO class. (Swapping them breaks either planner discovery or the LWC read.)
- The DTO's displayable `Response` field must be typed as the **DTO class** (`Acme_AccountHealthData`), never `String`/`Object` — a `String` is routed as plain narrative and never renders.
- **Never leave the displayable field `null`** — a null displayable nudges the planner to InformCommand. On error, populate a sentinel `{"error":"..."}` the LWC can show gracefully.
- `Response.<field>` name **must string-match** the action's `outputs.<key>` (Path B) / GenAi `properties.<key>` (Path A).

### The narrative-and-card pairing

Return two outputs from the same action: the displayable DTO **and** either a short text narrative or 2–3 planner passthrough scalars.

`is_displayable` / `isDisplayable` is the render-tool gate. `filter_from_agent` / `isUsedByPlanner` is whether the planner may *read* that output. They are independent flags. Help articles that treat `filter_from_agent: False` as required for rendering mixed them.

**Default (verified Path A — 8/8 Summit Ridge card actions; same idea on Path B):**

| Output | Type | Displayable | Planner-visible |
|---|---|---|---|
| the card | object → `c__<lightningTypeFolder>` | **True** (`is_displayable` / `copilotAction:isDisplayable`) | **False** (`filter_from_agent: True` / `copilotAction:isUsedByPlanner: false`) |
| narrative *or* chaining scalars | string / boolean / number | False | **True** (planner uses these; it must not re-parse the card JSON) |
| `success` / `errorMessage` | boolean / string | False | False |

Hiding the card JSON from the planner is what stops it from summarizing the payload as text. Lift the two or three scalars the next action needs into their own unfiltered outputs.

Historical note: Salesforce Help still says `filter_from_agent: False` on the card. That was the old default in this skill. Working SRA deploys (and `sf-clt-builder`) use the table above. If the render tool disappears from the trace's Available Actions after filtering the card, the problem is `is_displayable`, not `filter_from_agent` — check those as two flags.

### `schema.json`

```json
{
  "title": "Acme Account Health",
  "description": "Structured payload for the Acme account health chat card.",
  "lightning:type": "@apexClassType/c__Acme_AccountHealthData"
}
```

- **`c__` prefix — strongly recommended at creation.** The **unprefixed** form (`@apexClassType/<Class>`) is a fully working configuration: it deploys cleanly, passes `sf agent validate`, and **renders correctly in a published/active BotVersion** — the working LEA reference example uses the unprefixed form and passes. The prefix only matters for two things: (1) the strict `sf agent preview --use-live-actions --authoring-bundle` validator rejects the unprefixed form with **HTTP 400** (`complex_data_type_name` validation), so if you rely on that live-actions iteration loop, use `c__`; and (2) the immutability trap below. New work should use `c__` to keep both paths open, but don't treat an existing unprefixed-but-passing bundle as broken.
- **If you hit the HTTP 400, do NOT follow its suggested "fix"** (replacing the LT reference with `@apexClassType/...` on the *action* side) — that bypasses the LightningType and the LWC never mounts. The real fix is the `c__` prefix in `schema.json`.
- **Immutability trap:** once the LightningTypeBundle is referenced by an **active BotVersion**, its `lightning:type` is immutable — redeploying a *changed* prefix fails with *"Schema update contains breaking changes."* So you can't retrofit `c__` onto a referenced bundle in place; the only forward path is a brand-new LightningTypeBundle (different API name) and updating every reference. This is the reason to pick the prefix deliberately at first creation, not because the unprefixed form fails to render.
- **Pre-flight scanner** (must return zero matches before deploy):
  ```bash
  rg -n '"@apexClassType/(?!c__)' force-app/main/default/lightningTypes --glob 'schema.json'
  ```
- The action-side reference (`complex_data_type_name` in Path B, `lightning:type` in Path A `output/schema.json`) uses `c__<lightningTypeFolderName>` (the *bundle* name) — that side does not take `@apexClassType/`.

### `renderer.json` — hard rules

```json
{
  "renderer": { "componentOverrides": { "$": { "definition": "c/acmeAccountHealth" } } }
}
```

- **Only `lightningDesktopGenAi/renderer.json`.** Enhanced Web Chat falls back to it when `enhancedWebChat/` is missing. **Do not add `enhancedWebChat/renderer.json`.** Salesforce's compatibility table lists that folder as valid for ECv2, but adding it has overridden working desktop configs and broken rendering in field testing. (Add `lightningMobileGenAi/` only if you have a verified mobile need.) The fallback is also a privacy risk: a rep-authored card can reach an external customer without anyone opting in — see `sf-clt-builder/guides/surfaces.md`.
- **Only `definition` inside the `$` override.** Adding an `attributes` block fails deploy with `unevaluatedProperties` errors. The chat renderer is intentionally minimal; property-level overrides with `attributes`/`{!$attrs...}` are an object-based-CLT feature and don't belong here.
- The top-level `"renderer"` wrapper around `componentOverrides` is required (root-level `componentOverrides` fails with `additionalProperties ... set to false`). For an input CLT, use the same shape with `"editor"` instead of `"renderer"`.

### LWC view

```javascript
import { LightningElement, api, track } from 'lwc';
export default class AcmeAccountHealth extends LightningElement {
    @api value;                 // simple @api — runtime sets it before mount; NO getter/setter
    @track data = {};
    @track errorMessage = '';
    connectedCallback() {
        console.log('#### AcmeAccountHealth input:', this.value);   // load-bearing debug breadcrumb
        try {
            if (!this.value || !this.value.healthJSON) { this.errorMessage = 'No data provided'; return; }
            const raw = this.value.healthJSON;
            const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
            if (parsed?.error) { this.errorMessage = parsed.error; return; }   // honor sentinel
            this.data = parsed;
        } catch (e) { console.error('parse error', e); this.errorMessage = 'Error loading widget'; }
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Acme Account Health</masterLabel>
    <description>Renders the Acme account health card in Agentforce chat.</description>
    <targets>
        <target>lightning__AgentforceOutput</target>
        <target>lightning__AgentforceInput</target>
    </targets>
</LightningComponentBundle>
```

- Targets must be exactly `lightning__AgentforceOutput` (+ `lightning__AgentforceInput` if it also collects input). **Do NOT add** `lightningSnapin__ChatMessage`, `targetConfigs`, or `sourceType` — they break renderer registration.
- `this.value.<fieldName>` must match the DTO's `@AuraEnabled` field name exactly. Parse in `connectedCallback()` (runs after `value` is set). Keep the `#### ...` breadcrumb and a user-visible `errorMessage` fallback.
- To send input back, see [Sending data back from the LWC](#sending-data-back-from-the-lwc). Don't reach into the parent DOM — CLTs render in a sandboxed slot.
- Design at **chat-widget width (~380px)** — every chat consumer is at that width or narrower.

### Sending data back from the LWC

Write-back is **surface-specific** — generate it with `sf-clt-builder` / `guides/surfaces.md`. Inside an **Enhanced Chat v2** CLT the runtime util lives on `this.configuration` — **not** the host page's `embeddedservice_bootstrap.utilAPI`, which is only for code running in the parent window. Use `sendTextMessage()` (or `setSessionContext()`):

```javascript
this.configuration?.util?.sendTextMessage('Selected Acme Corp', [
  { name: 'account_id',   value: { valueType: 'TextValue', textValue: this.selectedId } },
  { name: 'account_name', value: { valueType: 'TextValue', textValue: selected.name } },
]).catch((error) => { this.error = error?.body?.message || String(error); });
```

ECv2 now supports **all 8 Agent Builder custom variable types**, which supersedes the old four-fixed-key `AgentContext` constraint (`currentPage`, `search_result`, `search_filters`, `search_facets`). Define real, distinctly-named variables per selector instead of overloading a fixed key or smuggling a JSON blob through one — multiple selectors can then coexist cleanly.

Setup: in Agent Builder create each variable with a matching type, set its API name, and enable **API write access**; then reference it in the script/action as `{!@variables.account_id}`.

The variable *write* is deterministic but validation is entirely server-side — the client only checks that the payload is an array. Match `valueType` to the shape exactly: a bare unquoted string is a hard rejection of the whole request, while a bad variable name is silently dropped and surfaced only as a warning on the send-message/create-conversation response. For reliable *consumption*, reference the variable directly in the action input rather than relying on the model to read it back conversationally. To verify a send landed, inspect the `/message` network request payload or check `ConversationDefinitionEventLog` (`ContextSetup` / `PlannerActionOutput`).

For input CLTs, dispatching `valuechange` remains the mechanism — subject to the [Service Agent + ECv2 gap](#input-clts-on-service-agent--ecv2--known-gap-w-22250928).

### ⚠️ LDS-backed `@wire` adapters fail inside ECv2 (W-21533738)

`@wire` adapters backed by Lightning Data Service — `getPicklistValuesByRecordType`, `getRecord`, etc. — **fail to initialise inside the ECv2 iframe when Credential-Based User Verification is enabled**, logging `ldsWebruntimeOneStoreInit` in the console on every session. This is a confirmed platform bug (**W-21533738**), not a configuration problem: the ESW LWR chat site iframe never fully initialises the LDS store, even with chat-site membership configured correctly. Apex-backed wires and imperative Apex calls work fine — only the LDS store layer is broken.

**Workaround:** replace every LDS-backed `@wire` with an imperative `@AuraEnabled` Apex call in `connectedCallback` or an event handler (e.g. a custom method returning the same picklist values). There is no other workaround short of the fix.

## ShowCommand vs InformCommand (the #1 silent failure)

After the action runs, the planner picks one of two reply strategies:

- **ShowCommand** — emits a structured `result[]` the client uses to mount your LWC.
- **InformCommand** — plain text, empty `result[]`. Your LWC never mounts.

Most "my renderer doesn't show" bugs are the planner choosing InformCommand because the signal was weak — *not* broken code. Invoking a CLT is **probabilistic**: the LLM planner decides whether to issue the render tool call, so "Session Tracing shows the action ran" does **not** mean the CLT rendered. Product plans to make this more deterministic; until then, treat render reliability as a prompt-engineering problem once the [pre-flight gate](#pre-flight-gate--verify-these-before-debugging-anything-else) is clean.

The reliable directive is explicit + imperative + names the output + explains why. Put it in the **action's own description and the output schema's `description`** first (see [Where the instruction lives](#where-the-instruction-lives-matters-more-than-how-much-you-write)), and keep the topic/subagent instruction minimal. The product-team recommended schema-description hint is:

> "The output of this action is always renderable. Always use show_command to display this to the user. Do NOT convert to text."

A fuller directive, when a topic-level instruction is genuinely needed:

```
CRITICAL: After the "Get Account Health" action completes, you MUST present the
accountHealth output to the user. ALWAYS show the structured action output (the
Account Health card). Do NOT rewrite, restate, or summarize the health data as
plain text or bullet lists — the interactive UI is contained in the accountHealth
output and must be displayed as-is.

In your text reply alongside the card, keep it short (1-2 sentences) for coaching
color only — call out the single most pressing risk and a one-line next move.
```

What makes it work: (1) names the displayable output (`accountHealth`); (2) directive language (`MUST`, `ALWAYS`, `Do NOT`); (3) explains *why* ("the interactive UI is contained in the output"); (4) distinguishes the card from the paired narrative. Replace soft phrasing ("you should show", "summarize") — that loses to ShowCommand reliability.

**Diagnose, in this order:**

1. **`formatType` on the `/sse` stream is ground truth.** `formatType: ExperienceType` = the CLT rendered. `formatType: Text` = it fell back. If you see `Text` with everything else correct, suspect the ECv2 connection (pre-flight #1).
2. **DevTools → Network → filter `messages/stream` → response `result`.** `result: []` = InformCommand. One or more `{type:"copilotActionOutput/...", value:{...}}` = ShowCommand (the `value` is your `@api value`).
3. **Trace → Reasoning step → Available Actions** — see [`is_displayable` gates the tool's existence](#is_displayable-gates-the-render-tools-existence).
4. The chat widget runs in an **iframe** — switch the DevTools console context to the Agentforce Messaging iframe or your `#### ...` logs won't appear.

### Render tool names differ by runtime (Daisy vs Daisy++)

The Unified Planner (Daisy++) reached all NGA agents in April 2026 and renamed the render/collect tools:

| Purpose | Daisy v1 (older AgentScript) | Daisy++ v2 (newer AgentScript) |
|---|---|---|
| Render an output | `show_command` | `__show_tool_results__` |
| Collect input | `user_input` | `__user_input__` |

If a script renders correctly with `show_command`, **don't rename it on principle.** Testing the Daisy++ name is a legitimate lever while troubleshooting a non-rendering case, but validate on the real ECv2 surface and be ready to revert — one field test that combined an explicit `__show_tool_results__` reference with a blank-caption instruction made the LLM echo the tool name into the chat as literal text.

### `is_displayable` gates the render tool's existence

If `is_displayable` isn't set on the action output, `show_command`/`__show_tool_results__` **never appears in the agent's available tool list during reasoning** — the planner has no mechanism to render, no matter how correct the LWC and bundle are. Verify in the trace: Agent Builder → the **Reasoning** (LLM) step for the relevant subagent → expand **Available Actions**.

- Render tool **absent** → fix `is_displayable`, confirm the action came from the Action Library, and check planner registration (`references/ecv2-troubleshooting.md`).
- Render tool **present** but nothing renders → downstream rendering-pipeline problem (ECv2 connection, `formatType`, tool-name mismatch), not a planner/binding problem.

This check works identically on Service Agent traces, even on a surface that can't paint the card.

### Reference the action by its exact API Name

In topic instructions, action-level instructions, or `subagent.reasoning.instructions`, reference the action by the **exact API Name registered in the Action Library** — never a friendly label or a name invented while drafting the script. A mismatch leaves the planner with nothing to bind the render tool to, so the agent silently falls back to plain text with no error surfaced, while the schema hint, registration and instructions all still look correct on the page. Copy the API Name straight from Setup → Agentforce Actions → Actions, and make sure every subagent/topic that calls it also lists it in its own `actions:` block.

### Where the instruction lives matters more than how much you write

Field finding from a production engagement: moving the render/caption directive **out of `reasoning.instructions` and into the action's own `description`** raised render adherence from roughly 4/10 to 9/10, and further trimming the subagent instructions improved it again. On Daisy++ both the render decision and the caption are LLM-generated, so every extra instruction line is another lever the model can misuse — added text is not free.

Order of preference:

1. The directive on the **action `description`** plus the CLT output's schema `description` (it rides along with the output type to the planner).
2. A minimal topic/subagent instruction naming the action and the render intent — nothing more.
3. More detail only after you've measured a gap.

A confirmed bare-minimum subagent instruction that fixed a real non-rendering case:

```
reasoning:
    instructions: ->
        | Call {!@actions.Show_EA_Form} action's user_input tool to collect the forecast parameters from the user.

    actions:
        Show_EA_Form: @actions.Show_EA_Form
            with filters = ...
```

For **input** CLTs the phrase `action's user_input tool` is load-bearing per the Salesforce Help troubleshooting article, not incidental wording.

When structured instructions are warranted, prefer short flat numbered steps (EXTRACT → VALIDATE → EXECUTE → DISPLAY → FOLLOW-UP) over nested conditionals, and absolute language over hedged:

| Avoid | Use instead |
|---|---|
| "should include the component" | "ALWAYS include the returned LWC component" |
| "try to run the action" | "run the action ONLY IF validation passes" |
| "if possible, show the form" | "MUST show the form — no exceptions" |
| long nested conditionals | short, numbered, flat steps |

**Renders on turn 1, blank afterwards:** add "ALWAYS include the returned LWC component in your response on every turn", and re-check `is_displayable`/`filter_from_agent`.

**Never write instructions that suppress repeat renders** ("only show the form once", "don't repeat the form"). Builder preview resets history every session but ECv2 carries conversation history across sessions, so such an instruction looks harmless in test and kills rendering in production.

**Caption control:** the text above the card is LLM-generated (it was formerly the hardcoded "Here are the results:"), and topic instructions steer it. To suppress commentary entirely, some teams instruct "always display the raw results, do not summarize. Display the output caption text as a blank string." Test caption suppression *in isolation* before combining it with tool-name changes — the combination regressed in a real test.

### Disambiguation fallback — the `user_select` gotcha

The agent may intermittently show an out-of-the-box `user_select` disambiguation form instead of your CLT, even when the action returns a single item, and `formatType` won't read as `Inform`. Fix by adding to the agent/action configuration:

```
additional_parameter__disable_disambiguate_form: True
```

After this the message type consistently shows as `Inform` and the CLT renders every time.

## Input CLTs on Service Agent + ECv2 — known gap (W-22250928)

ECv2 renders CLTs used as action **outputs** but not as action **inputs**. On a Service Agent (Messaging license) an input CLT's form fields surface as **plain text**; the identical action renders the form on an Employee Agent (Salesforce license). Confirmed by Trust Agent triage on a cross-org repro and tracked as **W-22250928** (see also W-21683108). A support finding matches: Service Agents cannot use the `__user_input__` action at all, while Employee Agents can.

Don't design around an input CLT on Service Agent + ECv2 until this ships. Three workarounds, in order of preference:

1. **Collect conversationally, confirm with an Output CLT (recommended).** Let the agent gather the fields over normal turns, pass them into a thin Apex pass-through action, and populate an **output** CLT purely for review/correct/submit; the LWC calls Apex directly on submit. This is the officially suggested workaround and needs no new platform capability.
2. **Output CLT + typed custom variables.** Render an output CLT and send the user's selection back from the LWC — see [Sending data back from the LWC](#sending-data-back-from-the-lwc). More capable, more moving parts.
3. **Route through an Employee Agent on ECv2.** GA since the week of June 29, 2026 — Employee Agents can be deployed on Experience Cloud sites with Enhanced Chat v2, and they do render input CLTs. The quick-start UI path has been seen to fail with a server-side channel-creation error on multiple orgs; the confirmed manual alternative is inbound Omni-Channel Flow routing to the Employee Agent with a fallback queue, using Messaging Session / Messaging End User / Messaging Channel with User Verification and an ESD on Chat v2.

⚠️ **"Switch to output-only" is not a guaranteed fix.** Genuinely output-only CLTs (`is_user_input: False` on every input) have still failed to render on Service Agent + ECv2 in at least two independent orgs — the action fires, the render tool call appears in the trace, and the chat prints the literal tool name as plain text. Before concluding "it's an input CLT problem", confirm the CLT really is input-driven and rule out the ECv2 connection (pre-flight #1) and tool naming.

## Deployment (order matters)

Deploy the LightningTypeBundle + LWC **before** the action — some orgs validate the action's `lightning:type` against a deployed LT/LWC and otherwise fail with a generic "unexpected error."

**Path B (Apex/DSL):**
```bash
sf project deploy start -m "ApexClass:Acme_AccountHealthData"          # 1 renderer DTO
sf project deploy start -m "ApexClass:Acme_AccountHealthService"       # 2 service (@InvocableMethod)
sf project deploy start \                                              # 3 LT + LWC together
  -m "LightningTypeBundle:Acme_AccountHealth" \
  -m "LightningComponentBundle:acmeAccountHealth"
sf project deploy start -m "PermissionSet:Account_Health_Access"       # 4 permset
sf agent validate authoring-bundle --api-name Your_Agent              # 5 catches DSL typos
sf agent publish  authoring-bundle --api-name Your_Agent              # 6 new BotVersion
sf agent activate --api-name Your_Agent --version <N>                 # 7 activate
```
There is no `GenAiPlannerBundle` deploy on Path B — `sf agent publish` generates the bot metadata from the `.agent` file.

**Path A (Builder/Flow):** DTO → Flow → (LT + LWC) → `GenAiFunction` → permset → **deactivate agent** → `GenAiPlannerBundle` → reactivate. Planner bundles can't deploy while the agent is Active ("Agent is Active").

A package.xml manifest works too (`LightningComponentBundle`, `LightningTypeBundle`, `ApexClass`, `<version>64.0+`).

## Permission sets, run-as user & auth context

The #1 runtime permission failure is assigning the permset to the wrong user. Run-as follows **agent type**, not path. Read `bots/<Bot>/<Bot>.bot-meta.xml`:

| Agent type | Runs as | Assign permset to |
|---|---|---|
| `EinsteinServiceAgent` | the `<botUser>` (dedicated SF user) | `sf org assign permset -n <PS> --on-behalf-of <botUser>` |
| `AgentforceEmployeeAgent` | the logged-in user who opens the panel | actual end users (often via a Permission Set Group) |

The permset needs `classAccesses` for the DTO **and** every Apex service class an action targets, plus `flowAccesses` for any Flow an action targets. The trap: `sf org assign permset` with no `--on-behalf-of` gives *your* user access; the Service Agent still fails because `<botUser>` doesn't have it.

**The permset must also cover every Apex class the LWC calls client-side** — `@wire`/imperative controllers, not just the Invocable action class. A missing LWC-side controller was a real-world blocker on a live engagement: the card mounts, then every data call fails.

**Class access alone is not enough, and object access fails differently.** When the service class is `with sharing` and its SOQL runs `WITH USER_MODE` (or `WITH SECURITY_ENFORCED`), object CRUD, FLS and record sharing are all enforced against the run-as user. A permset granting every `classAccesses` but no `objectPermissions` yields an action that is callable but whose first query throws — and the agent surfaces that as a vague "I could not retrieve … due to a system issue", which reads like a rendering fault rather than a permission one. Confirmed case: a Service Agent's card actions read Asset, WorkOrder, ServiceAppointment, ServiceResource and AssignedResource, and the `<botUser>` had no access to any of them despite holding all the classes.

**Don't reach for View All to fix it.** The Einstein Agent User license **rejects `viewAllRecords` per object**; `sf org assign permset` fails with `The user license doesn't allow the permission: View All <Object>`. Check the sharing model first:

```sql
SELECT QualifiedApiName, InternalSharingModel, ExternalSharingModel FROM EntityDefinition
WHERE QualifiedApiName IN ('Account','Case','Asset','WorkOrder','ServiceAppointment')
```

An `InternalSharingModel` of `ReadWrite` means plain object read is enough for an internal bot user — no view-all required. Only `Private` objects need it, and those are usually already covered by a standard Agentforce permset (View All Case, for instance, ships with Service Planner Agent User). Also note `Read Account` requires `Read Contact`, which the deploy will reject rather than infer.

**`System.runAs` cannot verify any of this.** It enforces record sharing only, *not* object or field permissions, so a `runAs(botUser)` test passes on queries that throw for that same user at runtime. Confirmed the hard way: an appointment-tracker action passed under `runAs` with assertions, then failed in the live chat on a missing object. Don't use it as your permission gate.

Verify deterministically instead. Enumerate every object the actions need — from **both** `FROM` clauses and every relationship hop — then diff against the run-as user's effective access:

```sql
SELECT SobjectType FROM ObjectPermissions
WHERE PermissionsRead = true AND ParentId IN (
  SELECT PermissionSetId FROM PermissionSetAssignment WHERE AssigneeId = '<botUserId>'
)
```

Three traps in that enumeration:

- **Relationship hops never appear in a `FROM` clause.** `ServiceTerritory.Name` on an appointment query still requires Read ServiceTerritory, and without it SOQL fails with `Didn't understand relationship 'ServiceTerritory' in field path` — which reads like a malformed query and sends you hunting through Apex instead of the permission set. Grep for `Object.Field` traversals, not just `FROM`.
- **`ControlledByParent` objects are silently dropped.** `AssignedResource` deploys clean inside a permission set and then simply isn't granted, because it inherits from its parent and has no independent object permission. Don't count it as covered.
- **Dependency chains are rejected, not inferred.** Read Account requires Read Contact; Read ServiceTerritory requires Read OperatingHours. The deploy names the missing dependency, so iterate on the error rather than predicting it.

`CaseComment`, `EmailMessage` and `User` needed no explicit grant in this org — they resolved through the parent record and standard access.

### ECv2 execution context: authenticated vs unauthenticated

On Enhanced Chat v2, *which* user your LWC and its Apex calls run as depends on the Embedded Service Deployment configuration — this is separate from the agent-type table above.

| | Credential-Based User Verification (recommended) | No verification |
|---|---|---|
| Session runs as | the authenticated, logged-in portal user | the internal Agent User / `<botUser>` |
| `UserInfo.getUserId()` in the action | the real user's ID | the internal Agent User ID (don't treat it as contact-linked) |
| Grant access to | the authenticated user's Profile/Permission Set | the Agent User Profile |

### 🚨 The chat-site membership gotcha

**You must update Member Provisioning on the ESD's generated LWR Chat Site — not just the parent Experience Cloud portal site.** Experience Builder → the chat site → Workspace Settings → **Member Provisioning** → add the same Profiles and Permission Sets as the parent portal.

Until you do, the chat window runs in **Guest User context even with Credential-Based User Verification enabled** on the messaging channel. ECv2 iframes the ESW LWR site inside the parent portal and resolves the user session by cookie on a shared domain, so the ESW site must have the authenticated user's profile registered as a member for session resolution to work.

- After updating membership, **log out and back in** — a page refresh is not sufficient to pick up the new context. Republish the ESD, then hard-refresh or use an incognito window.
- This membership is **not exposed via the Metadata API** — it's a manual Setup step, so it won't travel with a deploy and must be redone per org. Call it out in runbooks.
- ⚠️ **Do NOT grant the Guest User profile access to Apex classes, sensitive objects, or APIs as a workaround.** That exposes a public internet endpoint — a serious security risk. The correct fix is always the chat-site membership.

Reference: [Customize Site Members](https://help.salesforce.com/s/articleView?id=platform.networks_customize_members.htm&type=5) (do it for the portal site *and* the ESD site), [Credential-Based User Verification setup](https://help.salesforce.com/s/articleView?id=service.miaw_credential_user_verification_setup.htm&type=5).

## Wire-up (Builder, Path A)

0. Build the action in the **Action Library** (Setup → Agentforce Actions → Actions → New), then add it to the agent from the library — not directly inside Agent Builder.
1. Build the action body (GenAiFunction → Flow with an Apex-typed output var, or an Apex Invocable returning the DTO).
2. In the action settings: **Show in conversation** = ON; **Output Rendering** → your CLT; for input CLTs, **Input Rendering** → your input CLT (inputs only fire on Inquire/Confirm steps).
3. In the GenAi `output/schema.json`, the displayable property needs `copilotAction:isDisplayable: true` and `lightning:type: c__<bundle>`; the Flow output variable name must match that property name exactly.
4. When you pick a CLT, "Map to Variable" may show **"Unsupported Data Type"** — benign per docs, ignore.
5. Reload the agent page before retesting; newly attached CLTs don't pick up in an open session.

### Multi-CLT actions & steering the form
A single action can wire an input filter CLT (`editor.json` + input LWC) and an output response CLT (`renderer.json` + output LWC) in separate bundles. If the planner asks for fields inline as text instead of rendering the input form, first check that this isn't the [Service Agent + ECv2 input gap](#input-clts-on-service-agent--ecv2--known-gap-w-22250928) — on that combination the fields render as plain text no matter what you write. On an Employee Agent, tune instructions to prefer the form ("present the filter form rather than asking field by field", and reference the `action's user_input tool`).

## Production: images, security & publishing

The most common "works in test, broken live (broken images / blank component)" causes:

- **CMS images:** host assets in a CMS Workspace, link it to the messaging site as a content source, and store the **full** Experience-Cloud-domain URL on the record (`https://[domain]/[sitePath]/sfsites/c/cms/delivery/media/[ContentKey]`). Relative/bare paths won't render.
- **Trust the site domain in all three:** Setup → **Trusted URLs** (CSP); Experience Builder → **Trusted Sites for Scripts**; Setup → **CORS**. Missing any = blocked images / silent LWC load failure (Service Agent).
- **Always publish** the Embedded Service Deployment after any LWC/LT change to clear the site cache, then validate in an **incognito** window as a guest.

## Local preview

**Build and validate the LWC standalone before wiring it to an agent.** Mount it against the JSON payload it will receive — a one-page `preview-harness.html` framed to ~380px works well, or use the official [Lightning Preview](https://developer.salesforce.com/docs/platform/lwc/guide/get-started-test-components.html) VS Code extension. This catches everything downstream of `value`: parsing, layout, error handling, conditional rendering. It does **not** catch ShowCommand/InformCommand — that's a runtime planner concern.

## Testing

**Builder preview now renders CLTs — with caveats.** The old blanket rule ("Agent Builder preview never renders CLTs, never trust it") is out of date as of the 262 release:

| Surface | Renders CLTs? |
|---|---|
| AEA (Employee Agent) Builder preview | Yes — always could (Salesforce license) |
| ASA (Service Agent) Builder preview, agent connected to ECv2 | **Yes, as of Aug 2026** — see the [release note](https://help.salesforce.com/s/articleView?id=release-notes.rn_agentforce_asa_clt.htm&release=262&type=5) |
| ASA Builder preview with no ECv2 connection | No — the Messaging license can't be granted Lightning Type render permission. An expected license-level ACL constraint, not a bug |
| ECv2 Connection preview / Test Enhanced Chat / real portal chat | Yes — the only surface that matches production |

Practical rule: iterate in ASA/AEA preview, then **always confirm on the real ECv2 surface** before calling it done — Setup → Embedded Service Deployments → \[deployment\] → **Test Enhanced Web Chat**, incognito, after republishing. ECv2 carries conversation history across sessions where preview resets it each time, so history-dependent instruction bugs ("don't repeat the form") only appear there. For the in-org Lightning Agentforce panel, open it on a relevant Lightning page.

Trace-based checks (Available Actions, `formatType`) are valid even on a surface that can't paint the card — use them to separate planner problems from rendering problems.

After an Apex shape change, redeploy; if the action references go stale, delete & recreate the action (Path A) or republish (Path B).

## Pre-deploy sanity check

- [Pre-flight gate](#pre-flight-gate--verify-these-before-debugging-anything-else) all 8 confirmed — especially ECv2 as a Connection, ESD on WebV2, and action built in the Action Library.
- Renderer DTO: `global`, `@JsonAccess(serializable='always' deserializable='always')`, one `@AuraEnabled String`.
- `schema.json` uses `@apexClassType/c__<Class>` (run the `rg` scanner → zero matches).
- `renderer.json`: `lightningDesktopGenAi/` only, `definition` only, no `attributes`, no `enhancedWebChat/`.
- LWC `js-meta.xml`: `AgentforceOutput` (+`Input`); no `sourceType`/`targetConfigs`/`lightningSnapin__ChatMessage`; `apiVersion` 62.0+.
- LWC: simple `@api value`, try/catch parse, `#### ...` breadcrumb, error fallback.
- (Path B) action output: `complex_data_type_name: c__<bundle>`, `is_displayable: True`, `filter_from_agent: True` on the card (planner-visible narrative/passthroughs stay `False` / unfiltered); `Response.<field>` matches `outputs.<key>`.
- (Path A) GenAi schema: card `copilotAction:isDisplayable: true` and `copilotAction:isUsedByPlanner: false`; passthroughs inverse. Flow/Apex var name matches the property name.
- The render directive lives on the action `description` + output schema `description`; topic/subagent instructions are minimal and reference the action's **exact API Name**.
- No instruction tells the agent to show the card only once.
- No LDS-backed `@wire` in the LWC (imperative Apex instead).
- Permset assigned to the right run-as user (botUser vs end users), with `classAccesses` for the DTO, the action class **and every LWC-side Apex controller**, plus `flowAccesses` — and `objectPermissions`/FLS for every object the actions query, which `WITH USER_MODE` enforces separately from class access.
- (Authenticated ECv2) ESD chat site **Member Provisioning** updated; logged out and back in; Guest User granted nothing.
- Agent activated **and** ESD republished; verified incognito on the real ECv2 surface. If a card still renders as text, republish the ESD again before diagnosing — a stale publish state produces exactly that symptom.

## Common gotchas (in order of frequency)

**Configuration / environment**

1. **ECv2 not added as a Connection on the Service Agent** → `formatType` degrades to `Text`, nothing ever renders however correct the CLT is. Check this first, always.
2. Agent activated but **ESD not republished** → live chat unchanged ("worked yesterday, not today"). Republish after every version, action, input/output or rendering change; test incognito.
3. **`is_displayable` not set** → the render tool never appears in the trace's Available Actions, so the planner has no way to render.
4. Action created inside Agent Builder instead of the **Action Library** → broken/flaky wiring.
5. ESD Client Version is **V1, not WebV2**.

**Planner / instructions**

6. Planner chose **InformCommand** (plain text, `result: []`) → the directive is missing or in the wrong place. Move it onto the action `description` + output schema `description` and trim the subagent instructions.
7. Action referenced by a **label or invented name** instead of its exact API Name → the planner can't bind the render tool; silent text fallback, no error.
8. An instruction **suppresses repeat renders** ("only show the form once") → fine in Builder preview, broken in ECv2 where history persists.
9. OOTB **`user_select` disambiguation form** appears instead of your CLT → set `additional_parameter__disable_disambiguate_form: True`.
10. Renders sometimes, plain text other times → planner non-determinism; make instructions absolute, add the "why" sentence, and check `GenAiPlannerFunctionDef` registration (W-22380404 — see `references/ecv2-troubleshooting.md`).

**Metadata / contracts**

11. LWC `js-meta.xml` missing the `lightning__AgentforceOutput` target → never renders, no error.
12. Renderer DTO is `public` not `global`, or missing `@JsonAccess` → silent failure / `@apexClassType` won't resolve.
13. `schema.json` unprefixed `@apexClassType/<Class>` → still deploys and renders in a published BotVersion (a valid, passing config), but `sf agent preview --use-live-actions` rejects it HTTP 400, and the value is immutable once referenced. Use `c__` at creation.
14. `@AuraEnabled` on the `Response` field instead of `@InvocableVariable` (or vice-versa on the DTO field) → planner can't discover the output, or LWC reads `undefined`.
15. Added `enhancedWebChat/renderer.json` → overrides the working `lightningDesktopGenAi` config and breaks rendering. Remove it.
16. `attributes` block in `renderer.json` → deploy fails `unevaluatedProperties`. Use only `definition`.
17. `sourceType`/`targetConfigs` in the LWC `js-meta.xml` → renderer registration breaks. Remove them.
18. Displayable `Response` field is `String` (or `null` on error) → routed as narrative / planner picks InformCommand. Type it as the DTO; always populate (sentinel JSON on error).
19. GenAiFunction/planner deploy fails generically → deploy LT+LWC first (Path A order); deactivate the agent for planner-bundle deploys.

**Runtime / permissions**

20. Permset assigned to your user, not `<botUser>` (Service Agent) or not to end users (Employee Agent) → "insufficient access" at runtime. Same section: `classAccesses` granted but `objectPermissions`/FLS missing → a `WITH USER_MODE` query throws and the agent reports a vague "system issue" that looks like a rendering failure.
21. **ESD chat site Member Provisioning not updated** → chat runs as Guest User even with Credential-Based User Verification on. Fix membership, then log out and back in; never grant Guest User Apex access.
22. LWC-side Apex controllers not in the permset → card mounts, every data call fails.
23. **LDS-backed `@wire`** in the LWC → `ldsWebruntimeOneStoreInit`, never initialises (W-21533738). Use imperative Apex.
24. Input CLT on Service Agent + ECv2 → form fields render as plain text (W-22250928). See the [workarounds](#input-clts-on-service-agent--ecv2--known-gap-w-22250928).
25. LWC mounts but `value` is `undefined` → `Response.<field>` ↔ `outputs.<key>` name mismatch.
26. LWC mounts, card blank → DTO field name ↔ `this.value.<field>` mismatch, or malformed JSON (visible via the try/catch + breadcrumb).
27. `console` looks empty → switch DevTools console context to the Agentforce Messaging **iframe**.
28. Images broken live but fine in test → URL not a full Experience-Cloud-domain path, or domain not in Trusted URLs / Trusted Sites for Scripts / CORS.

## Alternative binding: `sourceType` / `lightning__listType` (legacy)

Some Salesforce material documents binding the Apex shape to the LWC through the `js-meta.xml` `targetConfig` instead of the JSON envelope:

- Single record: `<sourceType name="c__<lightningTypeName>"/>`; `schema.json` `@apexClassType/c__<Class>$<Wrapper>`.
- Collection: `<property name="value" type="lightning__listType" label="value"/>`; `renderer.json` wraps the `renderer` block in an outer `collection` key.

Recent field testing (and the working LEA example) found `targetConfigs`/`sourceType` in the renderer's `js-meta.xml` **break renderer registration**, and the proven deployments use the JSON envelope for both single and list shapes. **Prefer the envelope.** Only consider this approach if you have a specific verified reason, and test it in the real surface before relying on it.

## Reference patterns & examples

- **Working reference (Path A, SRA / Employee LEX panel):** Summit Ridge — 8 Lightning Types (`summitRidge*Output`), JSON-envelope DTOs, GenAiFunction `isDisplayable: true` / `isUsedByPlanner: false` on the card, planner passthrough scalars, `lightningDesktopGenAi` only. Interactive write-back is SRA-specific (`copytochat` / `acc:execute` / `conversationToolkitApi`). Generate new cards with `sf-clt-builder`.
- **Working reference (Path B, Employee Agent):** the LEA "Sales Copilot" — `LEA_AccountHealth` (single status card) and `LEA_DailyPriorities` (list card), both using the JSON-envelope pattern (`*Data` DTO with one `*JSON` field, `LEA_*Service` Invocable with paired displayable + narrative outputs, `.agent` subagents with explicit ShowCommand instructions). Mirror its structure for any card/list renderer.
- **Reference guide:** the v2 "Custom Renderers for Agentforce" guide — deepest treatment of the binding chain, Path A/B, ShowCommand vs InformCommand, the `c__` immutability lesson, and deploy/permset checklists.
- For 8 shape recipes (carousel, item selector, add-to-cart, conditional form, file upload v1/v2, formatted URL, article cards, embedded screen flow), see `references/patterns.md`.
- For a runnable flat-shape starter, see `examples/highlightCard/` (typed-field variant — simpler than the envelope; copy and adapt).
- **When it won't render:** `references/ecv2-troubleshooting.md` — diagnostic ladder, known platform bugs with GUS IDs, planner registration checks, Daisy++ planner parameters, and the authenticated-context runbook.
- **Runnable AgentScript examples:** [agent-script-recipes → customLightningTypes](https://github.com/trailheadapps/agent-script-recipes/tree/main/force-app/main/02_actionConfiguration/customLightningTypes).

### External docs

| Resource | Link |
|---|---|
| Lightning Types developer guide | [developer.salesforce.com](https://developer.salesforce.com/docs/ai/agentforce/guide/lightning-types.html) |
| Troubleshoot Custom LWC Rendering Issues in Agentforce | [Help article 005385924](https://help.salesforce.com/s/articleView?id=005385924&type=1) |
| Lightning Types Troubleshooting in ECv2 | [Help](https://help.salesforce.com/s/articleView?id=ai.enhanced_chat_v2_lt_troubleshoot.htm&type=5) |
| ASA CLT preview release note (262) | [Help](https://help.salesforce.com/s/articleView?id=release-notes.rn_agentforce_asa_clt.htm&release=262&type=5) |
| ECv2 considerations & limitations | [Help](https://help.salesforce.com/s/articleView?id=service.miaw_considerations_and_limitations.htm&type=5) |
| Troubleshoot Enhanced Chat setup | [Help](https://help.salesforce.com/s/articleView?id=service.miaw_troubleshoot.htm&type=5) |
| Credential-Based User Verification setup | [Help](https://help.salesforce.com/s/articleView?id=service.miaw_credential_user_verification_setup.htm&type=5) |
| Customize Site Members (portal **and** ESD site) | [Help](https://help.salesforce.com/s/articleView?id=platform.networks_customize_members.htm&type=5) |
| Employee Agent setup / connect an agent to ECv2 | [Help](https://help.salesforce.com/s/articleView?id=ai.agent_employee_agent_setup.htm&type=5) · [Help](https://help.salesforce.com/s/articleView?id=ai.service_agent_deploy_enhanced_chat_v2.htm&type=5) |

## What this skill does NOT cover

- **Generating** a new CLT from scratch — use `sf-clt-builder` (SRA, Employee LEX, ECv2, Cowork adapters, templates, GenAiFunction schemas).
- Object-based CLTs for Experience Builder, Prompt Builder, or generic Einstein Agent actions — use `generating-custom-lightning-type`.
- Standard out-of-the-box Lightning Types (`lightning__textType` etc.) — no bundle needed.
- SRA `copytochat` / `acc:execute` / `conversationToolkitApi` write-back — `sf-clt-builder` owns those contracts.
- A verified Agentforce Cowork write-back API — none exists yet; do not invent one.

## Related skills

- `sf-clt-builder` — generate the artifacts and pick the surface adapter.
- `generating-custom-lightning-type` — object-based CLTs, JSON Schema, generic Einstein Agent actions.
- `developing-agentforce` / `sf-ai-agentscript` / `sf-ai-agentforce` — building the agent itself (topics, actions, `.agent` files).
- `generating-lwc-components` — general LWC patterns; this skill assumes working LWC fundamentals.
