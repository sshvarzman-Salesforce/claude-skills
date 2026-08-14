---
name: authoring-serviceplanner-sra-topics
description: "Build a classic ServicePlanner (Agentforce Service Rep Assistant / SRA) into a working multi-topic assistant that gives a HUMAN rep step-by-step guidance on live VoiceCalls / Messaging / Cases — AND attach a REAL custom action (prompt template or flow) to a topic, not just the OOB knowledge action. The critical, non-obvious lesson: a ServicePlanner GenAiPlannerBundle DOES accept custom generatePromptResponse/flow actions, but ONLY when they are nested as per-TOPIC <localActions> inside a <localTopics> block (with a matching per-topic <localActionLinks><functionName>) — placing the same action as a top-level <plannerActions> fails deploy with the opaque, undiagnosable error 'An unexpected error occurred ... ErrorId ... (-1341094778)'. Covers the full decomposed bundle shape, the numbered Step-instruction authoring convention (with HTML/bold + per-step customer scripting), per-topic knowledge actions, the action-name uniqueness rules, the localActions schema.json layout, and the deactivate → deploy → reactivate lifecycle. Use whenever you need to add topics or a claim/order/account-lookup action to a ServicePlanner SRA, decompose a GenAiPlannerBundle, fix the -1341094778 error, or wire a prompt-template action onto a service-planner topic. Trigger on: 'add a topic to my SRA', 'attach an action to a ServicePlanner', 'ServicePlanner custom action', 'GenAiPlannerBundle localActions', 'service rep assistant guidance steps', 'ErrorId -1341094778', 'AiCopilot__ReAct planner bundle', 'why does my planner action fail to deploy'."
compatibility: "Salesforce CLI (sf) v2+; classic ServicePlanner agent (agentDSLEnabled=false, agentType=ServicePlanner, type=InternalCopilot, template service_planner_agent__ServicePlanner, plannerType=AiCopilot__ReAct); topics wired via a decomposed GenAiPlannerBundle; EmployeeCopilot__AnswerQuestionsWithKnowledge available for the knowledge action"
metadata:
  version: "1.0"
  last_updated: "2026-08-05"
---

# Authoring ServicePlanner SRA Topics (with real per-topic actions)

## What this skill is for

A classic **ServicePlanner** agent is Salesforce's **Service Rep Assistant (SRA)** — it does NOT talk to the customer. It watches a live **VoiceCall / MessagingSession / Case** and generates an **AI-suggested, step-by-step resolution plan for the HUMAN rep**, grounded in the org's topics, knowledge, and (as this skill proves) real backing actions.

Its topics and actions live in a **decomposed `GenAiPlannerBundle`** — a directory, not a single file. This skill gives you:

1. The exact bundle shape (inline topics, per-topic knowledge + custom actions, top-level knowledge action).
2. The **numbered Step-instruction** authoring convention reps expect (HTML/bold, per-step customer scripting).
3. **THE headline lesson:** how to attach a real custom action (prompt template / flow) to a topic so it actually deploys — and the specific placement that makes deploy throw the opaque `-1341094778` error.
4. The deactivate → deploy → reactivate lifecycle.

Verified live on `ClaimSecure_Agentforce_Service_Assistant` (CommericalDemos), Active at v1, with a custom `generatePromptResponse` claim-lookup action attached to the Claim Status topic.

---

## The one thing to get right: WHERE the custom action goes

This is the whole reason the skill exists. A ServicePlanner bundle has two places an action reference can appear:

| Placement | Result |
|---|---|
| **Top-level `<plannerActions>`** + top-level `<localActionLinks>` (planner-scope action) | For a custom `generatePromptResponse`/`flow` action → **deploy fails** with the opaque, root-cause-free error `An unexpected error occurred while processing your request. ... ErrorId: ... (-1341094778)`. Only the OOB knowledge action (`standardInvocableAction` / `streamKnowledgeSearch`) is accepted at planner scope. |
| **Per-topic `<localActions>`** nested inside a `<localTopics>` block + a matching per-topic `<localActionLinks><functionName>` | ✅ **Deploys and activates cleanly** — for the knowledge action AND for custom `generatePromptResponse`/`flow` actions. The action is scoped to that one topic. |

> If you hit `-1341094778` on a ServicePlanner bundle, you almost certainly put a custom action in `<plannerActions>`. Move it into the topic that uses it as a `<localActions>` entry. Do NOT waste time re-checking schema JSON, naming, or the backing artifact — the error is purely about placement. (An earlier investigation mis-concluded that ServicePlanner is "knowledge-action-only." It is not — it's "custom actions are per-topic only.")

---

## Agent identity check (confirm you actually have a ServicePlanner)

```bash
sf data query --target-org <ORG> --json \
  -q "SELECT DeveloperName, AgentType, AgentTemplate FROM BotDefinition WHERE DeveloperName='<Agent>'"
```
Classic ServicePlanner: `AgentType=ServicePlanner`, template `service_planner_agent__ServicePlanner`. Bundle `plannerType` = `AiCopilot__ReAct`. Topics are in `GenAiPlannerBundle:<Agent>` (same dev name as the agent).

`BotVersion` is a **regular** object (query WITHOUT `--use-tooling-api`); the relationship is **`BotDefinition`**, not `Bot`:
```bash
sf data query --target-org <ORG> --json \
  -q "SELECT BotDefinition.DeveloperName, VersionNumber, Status FROM BotVersion WHERE BotDefinition.DeveloperName='<Agent>' ORDER BY VersionNumber DESC"
```

---

## Decomposed bundle anatomy

On disk under `genAiPlannerBundles/<Agent>/`:

```
<Agent>.genAiPlannerBundle          # the XML: topics inline, action refs, top-level knowledge action
plannerActions/<KnowledgeAction>/input+output/schema.json     # top-level (planner-scope) action schemas — knowledge only
localActions/<Topic>/<Action>/input+output/schema.json        # per-topic action schemas (knowledge AND custom)
```

The `<Agent>.genAiPlannerBundle` XML contains, in order:
- `<description>`
- ONE top-level `<localActionLinks><genAiFunctionName>…</genAiFunctionName></localActionLinks>` → the planner-scope **knowledge** action (`AnswerQuestionsWithKnowledge_16jg…`).
- one `<localTopicLinks><genAiPluginName>…</genAiPluginName></localTopicLinks>` **per topic**.
- one `<localTopics>` block **per topic** — the full topic definition (below).
- `<masterLabel>`
- ONE top-level `<plannerActions>` = the knowledge action (`<source>EmployeeCopilot__AnswerQuestionsWithKnowledge</source>`, `invocationTarget=streamKnowledgeSearch`, `invocationTargetType=standardInvocableAction`).
- `<plannerType>AiCopilot__ReAct</plannerType>`

### A `<localTopics>` block

```xml
<localTopics>
    <fullName>ClaimSecure_SRA_Claim_Status</fullName>
    <canEscalate>false</canEscalate>
    <description>… when to route here + keyword list …</description>
    <developerName>ClaimSecure_SRA_Claim_Status</developerName>

    <!-- instructions: one <genAiPluginInstructions> per step (see convention below) -->
    <genAiPluginInstructions> … </genAiPluginInstructions>

    <language>en_US</language>

    <!-- one link per action attached to THIS topic -->
    <localActionLinks><functionName>AnswerQuestionsWithKnowledge_179g…</functionName></localActionLinks>
    <localActionLinks><functionName>ClaimSecure_SRA_Claim_Status_179g…</functionName></localActionLinks>

    <!-- per-topic knowledge action -->
    <localActions>
        <fullName>AnswerQuestionsWithKnowledge_179g…</fullName>
        <developerName>AnswerQuestionsWithKnowledge_179g…</developerName>
        <invocationTarget>streamKnowledgeSearch</invocationTarget>
        <invocationTargetType>standardInvocableAction</invocationTargetType>
        <isConfirmationRequired>false</isConfirmationRequired>
        <isIncludeInProgressIndicator>true</isIncludeInProgressIndicator>
        <localDeveloperName>AnswerQuestionsWithKnowledge</localDeveloperName>
        <masterLabel>Answer Questions with Knowledge</masterLabel>
        <progressIndicatorMessage>Getting answers</progressIndicatorMessage>
        <source>EmployeeCopilot__AnswerQuestionsWithKnowledge</source>
    </localActions>

    <!-- the CUSTOM action (prompt template here; a flow works the same way) -->
    <localActions>
        <fullName>ClaimSecure_SRA_Claim_Status_179g…</fullName>
        <description>… what the action does + when the planner should call it …</description>
        <developerName>ClaimSecure_SRA_Claim_Status_179g…</developerName>   <!-- SUFFIXED, must be unique in the org -->
        <invocationTarget>ClaimSecure_SRA_Claim_Status</invocationTarget>   <!-- BARE backing artifact dev name -->
        <invocationTargetType>generatePromptResponse</invocationTargetType> <!-- or 'flow' -->
        <isConfirmationRequired>false</isConfirmationRequired>
        <isIncludeInProgressIndicator>true</isIncludeInProgressIndicator>
        <localDeveloperName>ClaimSecure_SRA_Claim_Status</localDeveloperName> <!-- BARE -->
        <masterLabel>ClaimSecure SRA Claim Status</masterLabel>
        <progressIndicatorMessage>Looking up the claim</progressIndicatorMessage>
        <source>ClaimSecure_SRA_Claim_Status</source>                        <!-- BARE backing artifact dev name -->
    </localActions>

    <localDeveloperName>ClaimSecure_SRA_Claim_Status</localDeveloperName>
    <masterLabel>Claim Status and EOB</masterLabel>
    <pluginType>Topic</pluginType>
    <scope>Your job is to guide the service rep, step by step, through … You must not … — hand those to the matching topic.</scope>
</localTopics>
```

### Action-name uniqueness (causes `duplicate value found` if wrong)

- The custom action's `developerName`/`functionName` **must be unique** — it CANNOT equal a standalone `GenAiFunction` of the same name in the org (→ `duplicate value found: <unknown> …`), and an inline `<localTopics>` `developerName` cannot equal a standalone `GenAiPlugin` of the same name.
- Winning pattern (from OOB Bot-style bundles): **suffixed** `developerName`/`fullName` (e.g. `…_179gL000002XmmI`) with **bare** `invocationTarget` / `source` / `localDeveloperName` pointing at the actual backing artifact (the prompt template or flow dev name).
- If a same-named standalone `GenAiFunction` already exists and is not needed, delete it (move it out of the deploy path and destructive-delete from the org) before deploying the bundle.

---

## Per-topic action schema.json — ⚠️ THE #1 THING PEOPLE GET WRONG

Lives at `localActions/<Topic>/<Action>/input/schema.json` and `.../output/schema.json` — **NOT** under top-level `plannerActions/` (that folder is only for the planner-scope knowledge action).

**DO NOT hand-author these schemas from a guess of the field names.** A `generatePromptResponse` action's schema is NOT "one property per prompt-template input var." It has a **fixed, platform-generated shape** that you must reproduce exactly, or the action silently fails to bind — the planner shows the action but it never returns data, and there is NO deploy error to tell you why. **The single most common failure is using the bare input-var name as the property key instead of the `Input:`-prefixed key, and omitting the platform's standard companion properties.** (Verified by diffing a broken hand-authored action against a working one the platform generated — the ONLY differences were these schema keys.)

### The authoritative way to get a correct schema: let the platform generate it

The reliable path is to **add the action in the Agent Builder UI once, then retrieve the bundle** (`sf project retrieve start -m GenAiPlannerBundle:<Agent>`) and copy the platform-written `input/output/schema.json` into your project. Hand-author only if you match the shapes below verbatim.

### Correct **input** schema for a `generatePromptResponse` (prompt-template) action

The user-supplied prompt-template input becomes a property keyed **`Input:<VarName>`** (the `Input:` prefix is REQUIRED and must match the template's `<referenceName>Input:<VarName></referenceName>`), and the platform always adds two standard companion properties: `outputLanguage` and `isPreviewOnly`. Do NOT add `lightning:textIndexed` at the object level (the platform omits it for these actions).

```json
{
  "required" : [ "Input:DisputeLast4" ],
  "unevaluatedProperties" : false,
  "properties" : {
    "Input:DisputeLast4" : {
      "title" : "DisputeLast4",
      "description" : "The Last 4 digits of the Dispute number",
      "lightning:type" : "lightning__textType",
      "lightning:isPII" : false,
      "copilotAction:isUserInput" : true
    },
    "outputLanguage" : {
      "title" : "Output language",
      "description" : "Optional. Specify the response language using the appropriate two-character language code or five-character locale code (for example, en_US, en_GB, es, es_MX).",
      "lightning:type" : "lightning__textType",
      "lightning:isPII" : false,
      "copilotAction:isUserInput" : false
    },
    "isPreviewOnly" : {
      "title" : "Preview Only",
      "description" : "Resolves the prompt template without generating an LLM response.",
      "lightning:type" : "lightning__booleanType",
      "lightning:isPII" : false,
      "copilotAction:isUserInput" : false
    }
  },
  "lightning:type" : "lightning__objectType"
}
```
- `required` lists the `Input:`-prefixed key(s) the member must supply.
- The value the customer/rep supplies (the last-4, the claim number) is the `Input:<VarName>` property with `copilotAction:isUserInput: true`.
- If the prompt template also takes conversation context (VoiceCallId / MessagingSessionId) as **prompt inputs**, they too are `Input:VoiceCallId` / `Input:MessagingSessionId` with `copilotAction:isUserInput: false`. (Better: resolve those inside the backing flow from the conversation record, so the action needs only the one user-supplied input.)

### Correct **output** schema for a `generatePromptResponse` action

Two fixed properties — `promptResponse` and `generationId` — both with `isDisplayable: false` and `isUsedByPlanner: true`. Do NOT set `isDisplayable: true` (the platform uses `false`; the planner reads the response, it isn't rendered raw), and do NOT add `lightning:textIndexed`.

```json
{
  "unevaluatedProperties" : false,
  "properties" : {
    "promptResponse" : {
      "title" : "Prompt Response",
      "description" : "The prompt response generated by the action based on the specified prompt and input.",
      "lightning:type" : "lightning__textType",
      "lightning:isPII" : false,
      "copilotAction:isDisplayable" : false,
      "copilotAction:isUsedByPlanner" : true,
      "copilotAction:useHydratedPrompt" : false
    },
    "generationId" : {
      "title" : "Prompt Generation ID",
      "description" : "The unique identifier for the prompt generation associated with this action invocation.",
      "lightning:type" : "lightning__textType",
      "lightning:isPII" : false,
      "copilotAction:isDisplayable" : false,
      "copilotAction:isUsedByPlanner" : true,
      "copilotAction:useHydratedPrompt" : false
    }
  },
  "lightning:type" : "lightning__objectType"
}
```

### The `<localActions>` block for a working prompt-template action

A `generatePromptResponse` action carries **NO `<source>` element** (that's only on the knowledge action). `invocationTarget` and `localDeveloperName` are the **bare** prompt-template dev name; the `developerName`/`fullName` are suffixed-unique. It MUST be linked from the topic via a matching `<localActionLinks><functionName>`:

```xml
<localActionLinks>
    <functionName>Complaints_SRA_Dispute_Lookup_179gL000002aY3d</functionName>
</localActionLinks>
...
<localActions>
    <fullName>Complaints_SRA_Dispute_Lookup_179gL000002aY3d</fullName>
    <description>This is the action which gives back the Dispute Details after providing the last 4 digits of the dispute's number</description>
    <developerName>Complaints_SRA_Dispute_Lookup_179gL000002aY3d</developerName>
    <invocationTarget>Complaints_SRA_Dispute_Lookup</invocationTarget>   <!-- BARE prompt-template dev name -->
    <invocationTargetType>generatePromptResponse</invocationTargetType>
    <isConfirmationRequired>false</isConfirmationRequired>
    <isIncludeInProgressIndicator>true</isIncludeInProgressIndicator>
    <localDeveloperName>Complaints_SRA_Dispute_Lookup</localDeveloperName>   <!-- BARE -->
    <masterLabel>Complaints SRA Dispute Lookup</masterLabel>
    <progressIndicatorMessage>Getting Dispute Details</progressIndicatorMessage>
    <!-- NO <source> for generatePromptResponse -->
</localActions>
```

> **If you author the action but forget the matching `<localActionLinks><functionName>`, the action is an inert orphan** — it deploys, the agent activates, and the action is simply never available to the topic. This is a silent failure with no error. Always pair every `<localActions>` with a `<localActionLinks>`.

Types available: `lightning__textType`, `lightning__numberType`, `lightning__booleanType`, `lightning__richTextType`, `lightning__objectType`. Always `"unevaluatedProperties": false`.

The knowledge action's own `input/output/schema.json` under both `plannerActions/<Knowledge>/` and each `localActions/<Topic>/<Knowledge>/` are the stock EmployeeCopilot schemas — copy them verbatim from an existing OOB SRA bundle (`Agentforce_Service_Assistant`, `SDO_Service_Agentforce_Service_Assistant`); do not hand-author them.

## The backing prompt template + flow (the working contract)

The `generatePromptResponse` action points at a **flex GenAiPromptTemplate** (`type=einstein_gpt__flex`) whose single user input is declared as:
```xml
<inputs>
    <apiName>DisputeLast4</apiName>
    <definition>primitive://String</definition>
    <masterLabel>DisputeLast4</masterLabel>
    <referenceName>Input:DisputeLast4</referenceName>   <!-- this is why the schema key is Input:DisputeLast4 -->
    <required>true</required>
</inputs>
```
The template pulls the record data from a **Capability PromptFlow data provider** — a flat flow (NO subflow, NO loop) that does one Get Records and appends the result to `$Output.Prompt`:
```xml
<templateDataProviders>
    <definition>flow://Complaints_SRA_Get_Dispute</definition>
    <label>Complaints SRA Get Dispute</label>
    <parameters>
        <definition>primitive://String</definition>
        <isRequired>true</isRequired>
        <parameterName>DisputeLast4</parameterName>
        <valueExpression>{!$Input:DisputeLast4}</valueExpression>   <!-- template input → flow input -->
    </parameters>
    <referenceName>Flow:Complaints_SRA_Get_Dispute</referenceName>
</templateDataProviders>
```
and the template body references the flow output with `{!$Flow:Complaints_SRA_Get_Dispute.Prompt}`.

**Keep the data-provider flow FLAT.** The working flow is: `Start (triggerType=Capability)` → `Get Records` (filter `Contact__c EqualTo <hardcoded demo contact Id>` AND `Name EndsWith <last4>`, `getFirstRecordOnly=true`) → `Decision` on `Id IsNull` → two `Assignment`s (`elementSubtype=AddPromptInstructions`, operator `Add` to `$Output.Prompt`): a full-detail block on the found branch, a "NO MATCHING DISPUTE FOUND" line on the default branch. No subflow, no loop, no collection iteration. Flow Get Records has **no LIKE operator** — the "ends with last 4" match uses the `EndsWith` filter operator directly in the query (`Like`/`LikeString` are invalid `FlowRecordFilterOperator` values).

**Isolation-test trick (how to prove the action wiring works independent of the flow):** temporarily publish a template version whose body hardcodes a literal dispute block (and drop the `templateDataProviders`). If the agent then surfaces that literal via the action, the action ↔ template binding is correct and any remaining problem is in the flow; restore the `{!$Flow:...}` reference + data provider afterward.

---

## Step-instruction authoring convention (what reps expect)

Each topic's `genAiPluginInstructions` are the rep's playbook. One `<genAiPluginInstructions>` per instruction; each has `description` (the text), `developerName`, `masterLabel`, `sortOrder` (all `0` is fine — order follows document order).

Convention per topic:
1. **A formatting note first** (`developerName instruction_formatting0`): *"FORMATTING: You may use HTML in every step you surface to the rep. Use `<b>bold</b>` to emphasize the claim number, status, dollar amounts, and required actions. Keep each step short and scannable."* (Encode as `&lt;b&gt;…&lt;/b&gt;` in XML.)
2. **Numbered steps**, each `description` beginning `Step N:` chronologically (`instruction_step1_0`, `instruction_step2_1`, …).
3. **Every step ends with a customer script**: `Say to the customer: "…"` — the exact words the rep speaks/types, voice + messaging.
4. Where policy/process detail is needed, tell the rep to **surface the relevant knowledge article** (the per-topic knowledge action supplies it) — never write "search the knowledge base" as a manual step.
5. Where a real action exists (e.g. Claim Status), the step should tell the planner to **use the action to retrieve real data** and forbid inventing values — e.g. *"Use the claim-status action to look up the claim by claim number; do not guess or invent claim data."* (If you attach an action but leave the step pointing only at "console tools," the planner has no instruction to call it — keep the two in sync.)
6. **To surface a STANDARD console quick action (e.g. the `Email` / `Case.SendEmail` action) in the plan, you do it with INSTRUCTION TEXT ONLY — there is NO metadata action attachment for it.** A standard quick action already lives on the record page; the SRA only decides whether to *mention* it in the generated plan. This is fundamentally different from a custom `generatePromptResponse`/`flow` action (§ Backing an action) — do **not** add a `<localActions>` entry or a schema for a quick action, and don't look for one. How you phrase the instruction is what makes the action actually appear as a step:
   - **Make the action its own explicit directive, not a mid-sentence aside.** *"Surface the **Email** quick action as part of the plan"* buried inside a longer sentence tends to get dropped/paraphrased away. Lead the step with it: *"ALWAYS surface the **`Email`** quick action as an explicit step: **Open the Email quick action on this case** and send the customer a written confirmation."*
   - **Name the action by its exact console label** (the label the rep sees — e.g. `Email`, not `SendEmail`), bolded, and **name it again at the end of the step** so the model can't lose it.
   - Then say what the action's content should contain (the recap fields) and close with the `Say to the customer: "…"` script as usual.
   - Verified live: adding these leading, explicitly-named Email steps to the Complaints SRA dispute topics is what made the **Email** quick action reliably show in the generated service plan; the earlier "to do this, tell the rep to open the Email quick action…" mid-sentence phrasing did not surface it consistently.
7. The topic `<scope>` states the topic's job and an explicit **negative boundary** ("You must not … — hand those to the matching topic.") so topics don't bleed into each other.

---

## Backing an action (the claim-lookup example)

The custom action's `invocationTarget` (and `localDeveloperName`) point at a real artifact — for a `generatePromptResponse` action that's a prompt template; there is **no `<source>`** element. For the verified example it's a **flex GenAiPromptTemplate** `ClaimSecure_SRA_Claim_Status` that wraps a **PromptFlow** (`ClaimSecure_SRA_Get_Claim_Status`, `triggerType=Capability`) which calls an **AutoLaunchedFlow subflow** (`ClaimSecure_SRA_Read_Claim`, **SystemModeWithoutSharing**). The subflow resolves the member's Contact from the conversation — **VoiceCall.Contact__c** (custom lookup) for voice, **MessagingSession.EndUserContactId** for messaging — finds the claim by number (and confirms last-4), and returns the briefing text. Standing pattern: **data-provider reads run SystemModeWithoutSharing in the autolaunched subflow; the Capability PromptFlow stays thin.**

> For a simpler demo (like the Complaints dispute lookup) the data provider can be a single FLAT Capability PromptFlow with no subflow — see [The backing prompt template + flow](#the-backing-prompt-template--flow-the-working-contract) above.

A `flow`-type action (`invocationTargetType=flow`) is attached the same way and also uses `Input:<var>` schema keys. **Both** action types key their input schema `Input:<VarName>` — this is not flow-specific.

---

## Build → deploy → activate lifecycle

1. Author/patch the `<Agent>.genAiPlannerBundle` XML + the `localActions/<Topic>/<Action>/…/schema.json` files.
2. **Deactivate** the agent (a ServicePlanner is usually Active; you cannot redeploy topics under some states):
   `sf agent … ` or via Setup. (In practice: deploy the bundle, then re-activate — the platform handles the version bump.)
3. **Dry-run**:
   `sf project deploy start --dry-run --metadata GenAiPlannerBundle:<Agent> --target-org <ORG> --json`
   - `-1341094778` → a custom action is in `<plannerActions>`; move it into the topic.
   - `duplicate value found` → action/topic dev name collides with a standalone `GenAiFunction`/`GenAiPlugin`; suffix-rename or delete the standalone.
4. **Deploy**:
   `sf project deploy start --metadata GenAiPlannerBundle:<Agent> --target-org <ORG> --json`
5. **Activate**:
   `sf agent activate --api-name <Agent> --target-org <ORG> --json`
6. **Verify** Active + version:
   `sf data query --target-org <ORG> --json -q "SELECT BotDefinition.DeveloperName, VersionNumber, Status FROM BotVersion WHERE BotDefinition.DeveloperName='<Agent>' ORDER BY VersionNumber DESC"`

> `sf` CLI on this setup: `"/c/Program Files/sf/client/bin/node.exe" "/c/Program Files/sf/client/bin/run.js" <cmd> --json` and always pass `--target-org <ORG>` (global default may be a different org). Filter noise with `grep -v "punycode\|DeprecationWarning\|update available\|npm warn"`.

---

## Verification checklist

- [ ] Agent is `AgentType=ServicePlanner`, bundle `plannerType=AiCopilot__ReAct`.
- [ ] Bundle has one `<localTopicLinks>` + one `<localTopics>` per topic; one top-level `<plannerActions>` = the knowledge action only.
- [ ] Every topic carries the per-topic knowledge action (`localActions` + `localActionLinks`).
- [ ] Any custom action is a **per-topic `<localActions>`** with a matching `<localActionLinks><functionName>` — NEVER a top-level `<plannerActions>`.
- [ ] Custom action `developerName` is suffixed/unique; `invocationTarget`/`localDeveloperName` are the bare backing artifact dev name. A `generatePromptResponse` action has **NO `<source>`** (only the knowledge action does).
- [ ] `localActions/<Topic>/<Action>/input+output/schema.json` exist and match the platform shape: input property key is **`Input:<VarName>`** (NOT the bare var name) + the `outputLanguage` and `isPreviewOnly` companions, no object-level `lightning:textIndexed`; output has **both** `promptResponse` AND `generationId`, each with `copilotAction:isDisplayable:false`. When unsure, add the action in the UI once and retrieve the generated schema.
- [ ] Each topic: formatting note + `Step N:` numbered instructions + per-step `Say to the customer: "…"` + a negative-boundary `<scope>`.
- [ ] Steps that have a backing action instruct the planner to USE it (not just point at console tools).
- [ ] To surface a STANDARD quick action (e.g. `Email`): instruction text only — NO `<localActions>`/schema; the step LEADS with the action, names it by its exact console label (bolded) at least twice, then states the recap content.
- [ ] Dry-run clean (no `-1341094778`, no `duplicate value found`) → deploy → activate → `BotVersion` Active.

## Common mistakes → fixes

| Mistake | Fix |
|---|---|
| Custom action under top-level `<plannerActions>` | Move it into the topic's `<localActions>` + add a per-topic `<localActionLinks>` |
| Concluding "ServicePlanner is knowledge-only" after `-1341094778` | Wrong root cause — it's placement; per-topic custom actions work |
| Action dev name equals a standalone `GenAiFunction` | Suffix-rename (`_179g…`) and/or delete the standalone; keep `invocationTarget` bare |
| Schema under `plannerActions/` for a per-topic action | Put it under `localActions/<Topic>/<Action>/` |
| **Input schema keyed by the bare var name** (`DisputeLast4`) | Must be **`Input:DisputeLast4`** — the `Input:` prefix is required and must match the template's `<referenceName>`; applies to prompt-template AND flow actions |
| Input schema missing `outputLanguage` / `isPreviewOnly`, or has object-level `lightning:textIndexed` | Add both companion properties (`isUserInput:false`); remove `lightning:textIndexed` — the platform doesn't emit it for these actions |
| Output schema with `isDisplayable:true`, or missing `generationId` | Use `isDisplayable:false` on `promptResponse`; add the second `generationId` property (both `isUsedByPlanner:true`, `useHydratedPrompt:false`) |
| Action authored but **no matching `<localActionLinks><functionName>`** | The action is an inert orphan — deploys and activates but is never invoked, with no error. Add the link. |
| Hand-authoring the action schema from memory | Add the action in Agent Builder once, retrieve the bundle, copy the platform-generated `input/output/schema.json` verbatim |
| `<source>` element on a `generatePromptResponse`/`flow` action | Remove it — `<source>` is only for the OOB knowledge action; custom actions use `invocationTarget` + `localDeveloperName` only |
| Step attached to an action but text still says "use console tools" | Rewrite the step to instruct the planner to call the action |
| Adding a `<localActions>` entry / schema for a standard quick action (e.g. `Email`) | Don't — a standard quick action is surfaced by INSTRUCTION TEXT only; there is no metadata attachment for it |
| Quick action doesn't appear in the plan because it's mentioned mid-sentence | Make it a leading, explicit directive and name the action by its exact console label (bolded) at least twice in the step |
| `Bot.DeveloperName` in BotVersion SOQL | Use `BotDefinition.DeveloperName`; don't add `--use-tooling-api` (BotVersion is a regular object) |

## Related: choosing WHICH SRA is shown (multi-agent assignment)

Authoring a topic/bundle is *what one SRA does*. Deciding *which SRA appears* on a live VoiceCall / MessagingSession / Case (the Setup step **Define Your Multi-Agent Assignment Criteria**, needed only when an org has 2+ SRAs) is a separate autolaunched flow: input `recordId`, one output String whose **value is the SRA's agent API name** (`BotDefinition.DeveloperName`). See the **`assigning-sra-via-flow`** skill for that flow's exact contract, per-channel differences, and how to scale it to a new brand.
