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

## Per-topic action schema.json

Lives at `localActions/<Topic>/<Action>/input/schema.json` and `.../output/schema.json` — **NOT** under top-level `plannerActions/` (that folder is only for the planner-scope knowledge action).

**Input** (prompt-template action; keys are the template's input variable names; `required` lists mandatory ones; the value the member supplies gets `copilotAction:isUserInput: true`):
```json
{
  "required" : [ "ClaimNumber" ],
  "unevaluatedProperties" : false,
  "properties" : {
    "VoiceCallId" : { "title":"VoiceCallId", "description":"The Id of the VoiceCall for the current conversation, if voice.", "lightning:type":"lightning__textType", "lightning:isPII":false, "copilotAction:isUserInput":false },
    "MessagingSessionId" : { "title":"MessagingSessionId", "description":"The Id of the Messaging Session, if messaging.", "lightning:type":"lightning__textType", "lightning:isPII":false, "copilotAction:isUserInput":false },
    "ClaimNumber" : { "title":"ClaimNumber", "description":"The claim number the member wants to check, e.g. CLM-DENTAL-2001.", "lightning:type":"lightning__textType", "lightning:isPII":false, "copilotAction:isUserInput":true }
  },
  "lightning:type" : "lightning__objectType",
  "lightning:textIndexed" : true
}
```
> For a **flow** action, input keys are `Input:<flowVarName>` instead of plain names.

**Output** (generatePromptResponse = a single `promptResponse`, the text the planner surfaces to the rep):
```json
{
  "unevaluatedProperties" : false,
  "properties" : {
    "promptResponse" : { "title":"promptResponse", "description":"The rep-facing briefing generated from the matched claim.", "lightning:type":"lightning__textType", "lightning:isPII":false, "copilotAction:isDisplayable":true, "copilotAction:isUsedByPlanner":true, "copilotAction:useHydratedPrompt":false }
  },
  "lightning:type" : "lightning__objectType",
  "lightning:textIndexed" : true
}
```
Types available: `lightning__textType`, `lightning__numberType`, `lightning__booleanType`, `lightning__richTextType`, `lightning__objectType`. Always `"unevaluatedProperties": false`.

The knowledge action's own `input/output/schema.json` under both `plannerActions/<Knowledge>/` and each `localActions/<Topic>/<Knowledge>/` are the stock EmployeeCopilot schemas — copy them verbatim from an existing OOB SRA bundle (`Agentforce_Service_Assistant`, `SDO_Service_Agentforce_Service_Assistant`); do not hand-author them.

---

## Step-instruction authoring convention (what reps expect)

Each topic's `genAiPluginInstructions` are the rep's playbook. One `<genAiPluginInstructions>` per instruction; each has `description` (the text), `developerName`, `masterLabel`, `sortOrder` (all `0` is fine — order follows document order).

Convention per topic:
1. **A formatting note first** (`developerName instruction_formatting0`): *"FORMATTING: You may use HTML in every step you surface to the rep. Use `<b>bold</b>` to emphasize the claim number, status, dollar amounts, and required actions. Keep each step short and scannable."* (Encode as `&lt;b&gt;…&lt;/b&gt;` in XML.)
2. **Numbered steps**, each `description` beginning `Step N:` chronologically (`instruction_step1_0`, `instruction_step2_1`, …).
3. **Every step ends with a customer script**: `Say to the customer: "…"` — the exact words the rep speaks/types, voice + messaging.
4. Where policy/process detail is needed, tell the rep to **surface the relevant knowledge article** (the per-topic knowledge action supplies it) — never write "search the knowledge base" as a manual step.
5. Where a real action exists (e.g. Claim Status), the step should tell the planner to **use the action to retrieve real data** and forbid inventing values — e.g. *"Use the claim-status action to look up the claim by claim number; do not guess or invent claim data."* (If you attach an action but leave the step pointing only at "console tools," the planner has no instruction to call it — keep the two in sync.)
6. The topic `<scope>` states the topic's job and an explicit **negative boundary** ("You must not … — hand those to the matching topic.") so topics don't bleed into each other.

---

## Backing an action (the claim-lookup example)

The custom action's `source`/`invocationTarget` points at a real artifact. For the verified example it's a **flex GenAiPromptTemplate** `ClaimSecure_SRA_Claim_Status` that wraps a **PromptFlow** (`ClaimSecure_SRA_Get_Claim_Status`, `triggerType=Capability`) which calls an **AutoLaunchedFlow subflow** (`ClaimSecure_SRA_Read_Claim`, **SystemModeWithoutSharing**). The subflow resolves the member's Contact from the conversation — **VoiceCall.Contact__c** (custom lookup) for voice, **MessagingSession.EndUserContactId** for messaging — finds the claim by number (and confirms last-4), and returns the briefing text. Standing pattern: **data-provider reads run SystemModeWithoutSharing in the autolaunched subflow; the Capability PromptFlow stays thin.** A `flow`-type action can be attached the same way — just set `invocationTargetType=flow` and use `Input:<var>` schema keys.

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
- [ ] Custom action `developerName` is suffixed/unique; `invocationTarget`/`source`/`localDeveloperName` are the bare backing artifact dev name.
- [ ] `localActions/<Topic>/<Action>/input+output/schema.json` exist; input keys match the template vars (`Input:<var>` for flows); output is single `promptResponse` for generatePromptResponse.
- [ ] Each topic: formatting note + `Step N:` numbered instructions + per-step `Say to the customer: "…"` + a negative-boundary `<scope>`.
- [ ] Steps that have a backing action instruct the planner to USE it (not just point at console tools).
- [ ] Dry-run clean (no `-1341094778`, no `duplicate value found`) → deploy → activate → `BotVersion` Active.

## Common mistakes → fixes

| Mistake | Fix |
|---|---|
| Custom action under top-level `<plannerActions>` | Move it into the topic's `<localActions>` + add a per-topic `<localActionLinks>` |
| Concluding "ServicePlanner is knowledge-only" after `-1341094778` | Wrong root cause — it's placement; per-topic custom actions work |
| Action dev name equals a standalone `GenAiFunction` | Suffix-rename (`_179g…`) and/or delete the standalone; keep `invocationTarget` bare |
| Schema under `plannerActions/` for a per-topic action | Put it under `localActions/<Topic>/<Action>/` |
| Flow action using plain input keys | Flow input keys must be `Input:<flowVarName>` |
| Step attached to an action but text still says "use console tools" | Rewrite the step to instruct the planner to call the action |
| `Bot.DeveloperName` in BotVersion SOQL | Use `BotDefinition.DeveloperName`; don't add `--use-tooling-api` (BotVersion is a regular object) |
