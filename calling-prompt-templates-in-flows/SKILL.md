---
name: calling-prompt-templates-in-flows
description: "Invoke a Salesforce prompt template DIRECTLY as a Flow action (actionType=generatePromptResponse) instead of wrapping the ConnectApi.EinsteinLLM call in an Apex invocable. Covers the exact action XML (actionName = template DeveloperName, inputs prefixed Input:<param>, output auto-stored and read as {!<element>.promptResponse}); the companion micro-pattern (a tiny Apex invocable that converts the template's text response into a Text collection so a flow can loop); AND the full 'AI-draft from a record + its parent conversation transcript' pattern — a Capability PromptFlow data provider that reads a record and calls getConvTscpForRecord on its parent VoiceCall/MessagingSession, a flex template that returns a one-line 'Subject: ...||Description: ...' response, and a screen flow that splits it with two FORMULA fields and creates a record. Use whenever a flow (RoutingFlow, screen flow, autolaunched, record-triggered, or a prompt-template data provider) must call a flex/prompt template, ground it in a record + conversation transcript, get text back, split it, and act on it. Trigger on: \"call a prompt template in a flow\", \"prompt template flow action\", \"generatePromptResponse\", \"get conversation transcript in a flow\", \"getConvTscpForRecord\", \"ground a prompt on a voice call or messaging transcript\", \"AI draft a case subject and description\", \"split the prompt response into subject and description\", \"turn the prompt response into a list\", \"loop over prompt template output\"."
compatibility: "Salesforce CLI (sf) v2+; Prompt Builder (GenAiPromptTemplate, flex/einstein_gpt__flex); Flow API v59.0+ (generatePromptResponse action type); getConvTscpForRecord (flow-only standard action). Verified on API 64.0 and 68.0."
metadata:
  version: "1.1"
  last_updated: "2026-10-14"
---

# Calling Prompt Templates Directly in Flows

## What this skill is for

A prompt template (`GenAiPromptTemplate`) can be called **directly from a Flow** as a standard action — you do **not** need an Apex class that calls `ConnectApi.EinsteinLLM.generateMessagesForPromptTemplate`. The Flow action type is **`generatePromptResponse`**, it takes the template's declared inputs, and it returns the model's answer as a **String** named `promptResponse`.

This skill captures the exact, verified wiring (ground-truthed from a working Active RoutingFlow) plus the one place Apex is still genuinely useful: **converting the template's text output into a Text collection** so a flow can loop over it. Flow has no built-in "split string into collection" operation, so a ~15-line invocable fills that single gap.

### Worked example ships in `assets/`

Real, deployed-and-Active files this skill was extracted from (copy and adapt them):

- **`assets/example-routingflow-prompt-template-action.flow-meta.xml`** — the complete working RoutingFlow: `Get_VoiceCall` → `generatePromptResponse` (calls `Lead_to_Skill_Matching`) → `apex` transformer → loop → `routeWork`. Every element referenced below is in this file verbatim.
- **`assets/PromptResponseToSkillIds.cls`** — the text→collection transformer invocable.
- **`assets/PromptResponseToSkillIdsTest.cls`** — its passing test (3 methods: happy path, stray-text tolerance, blank/null).

Pattern B (record + conversation-transcript grounding — see the Pattern B section below), the three artifacts verbatim from a working Active build:
- **`assets/inh-promptflow-get-case-and-transcript.flow-meta.xml`** — the Capability PromptFlow data provider: `Get_Case` by number → Decision → `getConvTscpForRecord` on `VoiceCall__r.Id` / `Messaging_Session__r.Id` → `AddPromptInstructions`.
- **`assets/inh-case-draft-template.genAiPromptTemplate-meta.xml`** — the flex template returning `"Subject: …||Description: …"`, data provider = the PromptFlow.
- **`assets/inh-screenflow-draft-review-create.flow-meta.xml`** — the screen flow: pick queue → `generatePromptResponse` → two split FORMULAs → review (editable) → queue-by-name → create child case → success.

### Why prefer the action over an Apex wrapper

The tempting anti-pattern is an Apex invocable that calls `ConnectApi.EinsteinLLM...`, wraps it in `try/catch`, and returns a list. It works in anonymous Apex as an admin, but:

- **It swallows failures.** A `catch` that returns an empty list turns an auth/feature/context failure into a silent "no results" — the flow proceeds with nothing and you get, e.g., a route with **empty skills** and no error to diagnose.
- **Execution-context risk.** In restricted runtimes (Omni-Channel routing transactions, automated users), the generative callout can behave differently than in an interactive admin session. The platform's own `generatePromptResponse` action is the supported path in those contexts.
- **More surface area.** A class + test + deploy + the ConnectApi input plumbing (`WrappedValue`, `applicationName`, `isPreview`) — all replaced by one Flow element.

Use the native action to **call** the template. Use Apex only to **post-process** the text if the flow needs a shape Flow can't produce itself (a collection).

## The pattern (two elements)

```
… → [generatePromptResponse action]  → [apex: text→collection]  → [Loop] → …
      Lead_to_Skill_Matching             PromptResponseToSkillIds    SkillIdList
      out: .promptResponse (String)      in: promptResponse
                                         out: skillIds (List<String>) → SkillIdList
```

The Apex step is **optional** — include it only when you must loop over the response or otherwise need a non-String shape. If you just want to display or store the text, reference `{!<element>.promptResponse}` directly.

---

## 1. The `generatePromptResponse` action (the important part)

This is the complete, deployable `<actionCalls>` element for calling a flex prompt template whose DeveloperName is `Lead_to_Skill_Matching`, passing one input (`recordId`), and getting the text back:

```xml
<actionCalls>
    <name>Lead_to_skill_matching_using_AI</name>          <!-- free element name; how you reference the output -->
    <label>Lead to skill matching using AI</label>
    <locationX>176</locationX>
    <locationY>158</locationY>
    <actionName>Lead_to_Skill_Matching</actionName>        <!-- = the GenAiPromptTemplate DeveloperName -->
    <actionType>generatePromptResponse</actionType>        <!-- THE action type for prompt templates -->
    <connector>
        <targetReference>Prompt_Response_to_Skill_Ids_Action_1</targetReference>
    </connector>
    <flowTransactionModel>CurrentTransaction</flowTransactionModel>
    <inputParameters>
        <name>Input:recordId</name>                        <!-- input names are prefixed "Input:" -->
        <value>
            <elementReference>Get_VoiceCall.RelatedRecordId</elementReference>
        </value>
    </inputParameters>
    <nameSegment>Lead_to_Skill_Matching</nameSegment>      <!-- = actionName / template DeveloperName -->
    <storeOutputAutomatically>true</storeOutputAutomatically>
</actionCalls>
```

### The five rules that make it work

| Element | Value | Why |
|---|---|---|
| `actionType` | **`generatePromptResponse`** | The action type Flow uses for any prompt template. Not `apex`, not `flow`. |
| `actionName` **and** `nameSegment` | the **`developerName`** of the `GenAiPromptTemplate` | This is what binds the action to your template. Both tags carry the template dev name. |
| `inputParameters[].name` | **`Input:<paramName>`** | Inputs are prefixed `Input:`. The `<paramName>` must equal the template input's `referenceName` minus nothing — e.g. a template input `<referenceName>Input:recordId</referenceName>` is passed as `Input:recordId`. |
| `storeOutputAutomatically` | **`true`** | Auto-stores the result; you then read the text as `{!<element name>.promptResponse}`. Leave `outputParameters` empty. |
| output reference | **`{!<element name>.promptResponse}`** | The response text lives in a String output called `promptResponse`. Here: `{!Lead_to_skill_matching_using_AI.promptResponse}`. |

> **Input name = the template's `referenceName`.** Open the template metadata (`genAiPromptTemplates/<Name>.genAiPromptTemplate-meta.xml`) and read each `<inputs><referenceName>`. If it says `Input:recordId`, the flow input name is exactly `Input:recordId`. Case-sensitive.

> **Output is always `promptResponse` (String).** Every flex template exposes its generation as a single String output named `promptResponse` when `storeOutputAutomatically=true`. There is no separate "text" or "generations" field to dig into at the flow layer.

### Building it in the Flow Builder UI (equivalent to the XML above)

1. Add an **Action** element. In the action picker, filter by type / search the template's label — prompt templates appear as their own action category (not under Apex).
2. Select the template. The **Input** fields shown are the template's declared inputs (e.g. `recordId`); set each to a resource (e.g. `{!Get_VoiceCall.RelatedRecordId}`).
3. Leave "manually assign variables" off so the output stores automatically.
4. Downstream, reference **`{!<ActionApiName>.promptResponse}`**.

---

## 2. The companion Apex: text → Text collection (only if you must loop)

Flow can't split `"id1,id2,id3"` into a collection, so a tiny invocable does exactly that and nothing else. Verified class:

```apex
public with sharing class PromptResponseToSkillIds {

    public class Request {
        @InvocableVariable(required=true label='Prompt Response Text')
        public String promptResponse;
    }
    public class Result {
        @InvocableVariable(label='Skill Ids')
        public List<String> skillIds;
    }

    @InvocableMethod(label='Prompt Response to Skill Ids'
        description='Converts the comma-separated Skill Id text from the prompt template into a text collection to loop on.')
    public static List<Result> convert(List<Request> requests) {
        List<Result> results = new List<Result>();
        for (Request req : requests) {
            Result res = new Result();
            res.skillIds = parseIds(req == null ? null : req.promptResponse);
            results.add(res);
        }
        return results;
    }

    // Split on commas/whitespace/newlines; keep only Id-shaped tokens (15/18 alnum)
    // so stray model prose can never leak into the loop / downstream lookup.
    @TestVisible
    private static List<String> parseIds(String text) {
        List<String> ids = new List<String>();
        if (String.isBlank(text)) return ids;
        for (String part : text.split('[,\\s]+')) {
            String v = (part == null) ? '' : part.trim();
            if (String.isNotBlank(v) && (v.length() == 15 || v.length() == 18) && v.isAlphanumeric()) {
                ids.add(v);
            }
        }
        return ids;
    }
}
```

**Design notes worth reusing:**
- Keep it a **pure transformer** — input String, output collection. No callouts, no DML, no `try/catch` that hides errors. It can't be the thing that silently fails.
- **Filter defensively** to the shape you expect (here: 15/18-char alphanumeric Salesforce Ids). The whole reason to keep the LLM's raw text out of a `Get Records`/loop is that one stray label or code-fence token breaks the downstream element. Adjust the filter to your payload (e.g. keep all trimmed non-blank tokens if the response is arbitrary strings).
- **Design the template to emit parse-friendly text**: instruct it to return ONLY the values, comma-separated, no prose/quotes/brackets/newlines, with a concrete example. Then this parser is trivial and robust.

### Wiring the Apex step in the flow

```xml
<actionCalls>
    <name>Prompt_Response_to_Skill_Ids_Action_1</name>
    <label>Prompt Response to Skill Ids Action 1</label>
    <actionName>PromptResponseToSkillIds</actionName>        <!-- = the Apex class name -->
    <actionType>apex</actionType>
    <connector><targetReference>Loop_Skill_Ids</targetReference></connector>
    <flowTransactionModel>Automatic</flowTransactionModel>
    <inputParameters>
        <name>promptResponse</name>                          <!-- = the @InvocableVariable name -->
        <value>
            <elementReference>Lead_to_skill_matching_using_AI.promptResponse</elementReference>
        </value>
    </inputParameters>
    <outputParameters>
        <name>skillIds</name>                                <!-- = the @InvocableVariable name -->
        <assignToReference>SkillIdList</assignToReference>   <!-- your Text collection variable -->
    </outputParameters>
</actionCalls>
```

In the UI, the Apex invocable appears under its `@InvocableMethod` **label** (e.g. "Prompt Response to Skill Ids"), *not* the class name — but the metadata `actionName` is the **class name** (`PromptResponseToSkillIds`).

---

## End-to-end example (the verified RoutingFlow this skill was extracted from)

> Full deployable file: **`assets/example-routingflow-prompt-template-action.flow-meta.xml`** (+ the two Apex files). This diagram is that flow.

Skills-based Omni-Channel routing that asks a prompt template which skills a caller needs:

```
Start
  → Get_VoiceCall            recordLookup: VoiceCall WHERE Id = {!recordId}   (to reach the related Lead)
  → generatePromptResponse   Lead_to_Skill_Matching, Input:recordId = {!Get_VoiceCall.RelatedRecordId}
                             out: {!Lead_to_skill_matching_using_AI.promptResponse}  ("id1,id2,id3")
  → apex                     PromptResponseToSkillIds, promptResponse = {!...promptResponse}
                             out skillIds → SkillIdList  (Text collection)
  → Loop_Skill_Ids           over SkillIdList
        → Get_Skill          Skill WHERE Id = {!Loop_Skill_Ids}
        → Build_Skill_Requirement   assign rvar fields + Add rvar to SkillRequirements
  → (no more values) routeWork   SkillsBased, skillRequirementsResourceItem = {!SkillRequirements}
```

Key take-aways this flow proves:
- The template is called with **no Apex wrapper** — `generatePromptResponse` + `Input:recordId`.
- The **only** Apex is the String→collection transformer.
- Pass the record Id the template actually needs via a resource (`{!Get_VoiceCall.RelatedRecordId}`) — never hardcode a test Id into the action input (a hardcoded Id makes the flow "work" for one record and silently ignore the lookup you added).

## Pattern B — AI-draft from a record + its PARENT CONVERSATION TRANSCRIPT (verified, API 68)

This is the high-value pattern: a screen flow where an agent/rep picks an option, an LLM
**drafts text grounded in a record and the transcript of its parent VoiceCall or
MessagingSession**, the human reviews/edits it, and the flow creates a record. Three
artifacts, each with a precise contract. (Ground-truthed from a working Active build;
assets ship in `assets/inh-*`.)

```
Screen flow                      Flex template                 Capability PromptFlow (data provider)
──────────                       ─────────────                 ─────────────────────────────────────
Get parent record (by Id)                                      input: CaseNumber (the human key, NOT an Id)
Screen: pick an option   ──┐                                   Get_Case  WHERE CaseNumber = {!CaseNumber}
generatePromptResponse ────┼─► INH_Case_Draft_New  ──► flow:// INH_Get_Case_details_and_parent_Conversation
  Input:Case_Number          │   Input:Case_Number  ─────────────► param CaseNumber = {!$Input:Case_Number}
  Input:Escalation_Queue_Name │   Input:Escalation_Queue_Name     AddPromptInstructions: case fields
                             │   (queue name used in TEXT only)   Decision on parent:
2 FORMULA fields split      │   body ends with EXACT format:        VoiceCall__r.Id not null →
  {!...promptResponse}      │   "Subject: <x>||Description: <y>"       getConvTscpForRecord(VoiceCall__r.Id)
Review screen (editable)    │   CONTEXT: {!$Flow:...Prompt}           Messaging_Session__r.Id not null →
Get queue by NAME (Group)   │                                         getConvTscpForRecord(Messaging_Session__r.Id)
Create record, OwnerId=queue│                                       default → "No interaction linked"
Success screen w/ number ◄──┘                                     each branch → AddPromptInstructions(.conversationTranscript)
```

### B1. The data-provider PromptFlow (reads the record + transcript)

- `processType=PromptFlow`, `start.triggerType=Capability`. **ONE input** — the human-facing
  key (e.g. `CaseNumber`), NOT a record Id. Resolve the record inside the flow. This keeps
  the whole thing self-contained; never make the caller shuttle resolved Ids in.
- `Get_Case` → `recordLookup` `WHERE CaseNumber = {!CaseNumber}`, `getFirstRecordOnly=true`,
  `storeOutputAutomatically=true`. Query the parent lookups so you can dereference them.
- Append case fields with an `AddPromptInstructions` assignment:
  `assignToReference = $Output.Prompt`, `operator = Add`, value a `<stringValue>` with
  `{!Get_Case.CaseNumber}` / `.Subject` / `.Description` / `.Type` etc.
- **Decision gates the transcript action** so `getConvTscpForRecord` only runs when a parent
  exists. Two rules + a default:
  - rule 1: `{!Get_Case.VoiceCall__r.Id}` `IsNull false` → voice transcript branch
  - rule 2: `{!Get_Case.Messaging_Session__r.Id}` `IsNull false` → messaging transcript branch
  - default: an `AddPromptInstructions` saying "No interaction linked".
- The transcript action (one per branch):
  ```xml
  <actionCalls>
      <name>Get_Conversation_Transcript_for_Record_Action_1</name>
      <actionName>getConvTscpForRecord</actionName>
      <actionType>getConvTscpForRecord</actionType>
      <flowTransactionModel>CurrentTransaction</flowTransactionModel>   <!-- REQUIRED -->
      <inputParameters>
          <name>recordId</name>
          <value><elementReference>Get_Case.VoiceCall__r.Id</elementReference></value>  <!-- __r.Id, NOT the __c lookup value -->
      </inputParameters>
      <storeOutputAutomatically>true</storeOutputAutomatically>
  </actionCalls>
  ```
  then an `AddPromptInstructions` appends `{!Get_Conversation_Transcript_for_Record_Action_1.conversationTranscript}`.
- **`getConvTscpForRecord` is flow-only** (Apex cannot call it) and returns the transcript for
  BOTH VoiceCall and MessagingSession — see the `conversation-transcript-action` memory.

### B2. The flex template (returns a splittable one-liner)

- `type=einstein_gpt__flex`, `status=Published`. For a **FRESH** template, **do NOT hand-manage
  `versionIdentifier`/`activeVersionIdentifier`** — omit both and let the server assign the
  version on deploy. (The retrieve→set-hash→redeploy dance is only needed when EDITING an
  already-published template's content; and you cannot REMOVE inputs from a published template
  — "No value present" / unsafe-change — create a new template dev name instead.)
- Two inputs is a common shape: the data key (`Case_Number`, `referenceName=Input:Case_Number`,
  `required=true`) and a context value (`Escalation_Queue_Name`) used **in the template text
  only**, not passed to the flow.
- `templateDataProviders`: `definition=flow://<PromptFlow>`, one `parameters` entry mapping the
  flow's input to `{!$Input:Case_Number}`. Body references `{!$Flow:<PromptFlow>.Prompt}` for the
  grounded context.
- **Pin an exact, parseable output format with a single-line delimiter**:
  ```
  Respond EXACTLY in this format, with nothing before or after:
  "Subject: <one short line>||Description: <3 to 6 sentence briefing>"
  ```
  The `||` keeps it one line and makes the split trivial and robust.

### B3. The screen flow (call, split with formulas, create)

- `generatePromptResponse` action → the template; inputs `Input:Case_Number={!Get_Case.CaseNumber}`,
  `Input:Escalation_Queue_Name={!Option_Queue}`; `storeOutputAutomatically=true`.
- **Split the one response with two FORMULA resources** (no Apex needed for a fixed 2-part shape):
  ```
  Subject:      TRIM(MID(resp, FIND("Subject:", resp) + 8,
                          FIND("||", resp) - (FIND("Subject:", resp) + 8)))
  Description:  TRIM(MID(resp, FIND("Description:", resp) + 12, LEN(resp)))
  ```
  where `resp` = `{!<action>.promptResponse}`. (`"Subject:"` is 8 chars, `"Description:"` is 12.)
  Harden with `IF(FIND(...)=0, "<fallback>", <extract>)` if the model may omit a marker.
- Default the editable review-screen `LargeTextArea` fields to those formulas so the rep can edit.
- **Resolve a queue by NAME, never a hardcoded Id**: `recordLookup` on
  `Group WHERE Type='Queue' AND Name={!Option_Queue}` → set the created record's `OwnerId` to
  `{!Get_Escalation_Queue.Id}`. (A record created by a Flow does not run assignment rules, so a
  queue OwnerId set this way sticks — no second owner-update step needed.)
- Create the child record copying context from the parent (Contact, Account, `VoiceCall__c`,
  `Messaging_Session__c`, Type, etc.), Subject/Description from the edited screen fields.
- Let Flow render the **default footer** (do NOT set `allowBack`/`allowFinish`/`showFooter`
  explicitly, and never both `allowBack` and `allowFinish` false — that errors) so Next/Finish
  appear correctly.

### B4. Lessons (do it right the first time)

- **Make the data provider self-contained on the human key** (case number), not on resolved Ids
  passed by the caller. Shuttling resolved record Ids between separate agent/flow actions is
  fragile and fails silently.
- **Dereference the relationship** (`VoiceCall__r.Id`) for the transcript `recordId`; **gate** the
  transcript action behind a Decision so it never runs with a null/empty parent.
- **Queue by name**, server-owned template version, `||` delimiter, formula-split — all cleaner
  than hardcoded Ids, the version-hash dance, and newline splitting.

## Verification checklist

- [ ] Template DeveloperName matches `actionName` **and** `nameSegment` exactly (case-sensitive).
- [ ] Each `inputParameters.name` is `Input:<param>` and matches the template `<inputs><referenceName>`.
- [ ] `storeOutputAutomatically=true` and downstream reads `{!<element>.promptResponse}`.
- [ ] If looping: the transformer Apex is deployed with a passing test; `outputParameters.name` = the `@InvocableVariable` name; `assignToReference` = a collection variable of the right type.
- [ ] The template is **Active/Published** and the running user (including automated/routing contexts) can access it.
- [ ] No hardcoded record Ids in the action inputs — bind to a resource.

## Gotchas

- **Input prefix is literal `Input:`.** `recordId` alone won't bind; it must be `Input:recordId`.
- **Output is a String, not a collection.** Anything list-shaped in the model's answer is still one string until you split it — that's the whole reason for the Apex transformer.
- **Don't hide failures in Apex.** If you *do* keep an Apex-calls-ConnectApi wrapper for some reason, don't `catch` and return empty — let it throw so the flow's fault path (or the run) surfaces the error. The native `generatePromptResponse` action reports failures instead of masking them; that's another reason to prefer it.
- **Template edits need a version bump** to take effect (see the `prompt-template-version-bump` memory) — editing published content without bumping `versionIdentifier`/`activeVersionIdentifier` leaves the old version serving.
- **API version:** `generatePromptResponse` is available on modern Flow API versions; this pattern is verified on **64.0**. On older orgs, confirm the action type is recognized before authoring by hand.
