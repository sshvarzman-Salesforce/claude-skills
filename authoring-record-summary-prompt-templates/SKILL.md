---
name: authoring-record-summary-prompt-templates
description: "Build a RECORD SUMMARY type Salesforce prompt template (GenAiPromptTemplate type=einstein_gpt__recordSummary) that renders an AI briefing on a record's page / Record Summary component / agent record-summary — grounded in that record AND related records (parent record, parent VoiceCall/MessagingSession transcript, Contact, Account) via a Capability PromptFlow data provider. Covers how a record-summary template DIFFERS from a flex template: type=einstein_gpt__recordSummary, a <relatedEntity>Object</relatedEntity> binding, an SObject input (apiName=objectToSummarize, definition=SOBJECT://<Object>, referenceName=Input:<Object>, required=true) instead of a String recordId, the data-provider param mapping recordId={!$Input:<Object>.Id}, and the <fileDroppingStrategy> element. Reuses the same self-contained PromptFlow + getConvTscpForRecord transcript grounding as flex templates. Use whenever asked to build a record summary / record-page AI summary / 'summarize this case/account/contact' prompt template, or convert a flex template into a record-summary one. Trigger on: 'record summary prompt template', 'einstein_gpt__recordSummary', 'summarize this record', 'AI summary on the record page', 'Record Summary component', 'relatedEntity', 'objectToSummarize', 'SOBJECT:// input', 'turn my flex template into a record summary'."
compatibility: "Salesforce CLI (sf) v2+; Prompt Builder (GenAiPromptTemplate type einstein_gpt__recordSummary); Flow API v59.0+ Capability PromptFlow; getConvTscpForRecord (flow-only). Verified on API 68.0, CommericalDemos."
metadata:
  version: "1.0"
  last_updated: "2026-10-15"
---

# Authoring Record Summary Prompt Templates

## What this skill is for

A **Record Summary** prompt template is a `GenAiPromptTemplate` of
`type=einstein_gpt__recordSummary`. It renders an AI-written summary of **one record**
on that record's page (the Einstein **Record Summary** component / "Summarize" on the
record, and agent record-summary surfaces). It is bound to a specific object and
receives the **record itself** as input — not a free String.

This is a DIFFERENT template type from a `einstein_gpt__flex` template (see the
companion skill `calling-prompt-templates-in-flows`, Pattern B). The grounding engine —
a Capability **PromptFlow** data provider that reads the record + related records +
`getConvTscpForRecord` transcript — is **identical and reusable**. Only the template
wrapper changes. This skill is the record-summary wrapper; reuse the flex skill's
PromptFlow guidance for the data provider.

> **Verified reference ships in `assets/`:** `inh-record-summary-template.genAiPromptTemplate-meta.xml`
> — a working Active `einstein_gpt__recordSummary` template on Case whose data provider
> is a Capability PromptFlow that reads the INH child case, its PARENT case, the parent's
> VoiceCall/MessagingSession transcript, the Contact, and the Account, and emits a
> 4-section specialist briefing (Situation / What to focus on / Key facts / Flags).
> `inh-record-summary-context.flow-meta.xml` is that PromptFlow.

---

## The five things that make it a RECORD SUMMARY template (not flex)

Diff a record-summary template against a flex one and exactly these differ:

| Element | Record Summary (`einstein_gpt__recordSummary`) | Flex (`einstein_gpt__flex`) |
|---|---|---|
| `<type>` | **`einstein_gpt__recordSummary`** | `einstein_gpt__flex` |
| `<relatedEntity>` | **present** — the object the summary renders on, e.g. `<relatedEntity>Case</relatedEntity>` | absent |
| the input | **the record itself**: `apiName=objectToSummarize`, `definition=SOBJECT://Case`, `referenceName=Input:Case`, `required=true` | a `primitive://String` (e.g. `recordId`) |
| data-provider param | maps `recordId` to the record's Id: `valueExpression={!$Input:Case.Id}` | `{!$Input:recordId}` or similar |
| `<fileDroppingStrategy>` | **present** (e.g. `{"dropFilesBy":"LAST_MODIFIED_DATE","dropFileStartingWith":"OLDEST"}`) | absent |

Everything else — `<content>` referencing `{!$Flow:<PromptFlow>.Prompt}`, the
`<templateDataProviders>` block pointing at `flow://<PromptFlow>`, `primaryModel`,
`status`, `visibility` — is the same.

### The exact record-summary template shape (copy this)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>INH_Record_Summary_Updated</developerName>
    <masterLabel>INH Record Summary Updated</masterLabel>
    <relatedEntity>Case</relatedEntity>                                  <!-- bind to the object -->
    <templateVersions>
        <content>You brief the specialist... Use ONLY the facts below; never invent.

{!$Flow:INH_Record_Summary_Context.Prompt}</content>
        <fileDroppingStrategy>{"dropFilesBy":"LAST_MODIFIED_DATE","dropFileStartingWith":"OLDEST"}</fileDroppingStrategy>
        <inputs>
            <apiName>objectToSummarize</apiName>                         <!-- FIXED api name -->
            <definition>SOBJECT://Case</definition>                      <!-- the record, not a String -->
            <referenceName>Input:Case</referenceName>                    <!-- Input:<Object> -->
            <required>true</required>
        </inputs>
        <isCitationEnabled>false</isCitationEnabled>
        <primaryModel>sfdc_ai__DefaultGPT5Mini</primaryModel>
        <status>Published</status>
        <templateDataProviders>
            <definition>flow://INH_Record_Summary_Context</definition>
            <label>INH Record Summary Context</label>
            <parameters>
                <definition>primitive://String</definition>
                <isRequired>false</isRequired>
                <parameterName>recordId</parameterName>
                <valueExpression>{!$Input:Case.Id}</valueExpression>      <!-- pull Id off the SObject -->
            </parameters>
            <referenceName>Flow:INH_Record_Summary_Context</referenceName>
        </templateDataProviders>
    </templateVersions>
    <type>einstein_gpt__recordSummary</type>                             <!-- the type -->
    <visibility>Global</visibility>
</GenAiPromptTemplate>
```

Key joins:
- The **input `referenceName`** is `Input:<Object>` (e.g. `Input:Case`); the body/data-provider
  reference the Id as `{!$Input:Case.Id}`. The `apiName` is the fixed literal
  `objectToSummarize`.
- The **data-provider flow** still takes a `recordId` String param — the template feeds it
  `{!$Input:Case.Id}`. So a PromptFlow written for a flex template (String `recordId` input)
  is reused verbatim; you only rewrap it.

---

## The data provider (reuse the flex Pattern B PromptFlow)

The grounding flow is a Capability **PromptFlow** (`processType=PromptFlow`,
`start.triggerType=Capability`) with **one `recordId` String input**, that:

1. `Get_<Record>` by `Id = {!recordId}`, `storeOutputAutomatically=true`, querying the
   lookups you want to dereference (`ParentId`, `ContactId`, `AccountId`, …).
2. `AddPromptInstructions` assignments (`$Output.Prompt` `Add` `<stringValue>`) that append
   the record + related-record context using cross-object merge fields
   (`{!Get_Case.Parent.Subject}`, `{!Get_Case.Contact.Name}`, `{!Get_Case.Account.Name}`, …).
3. A **Decision** that gates `getConvTscpForRecord` on the parent interaction
   (`{!Get_Case.Parent.VoiceCall__c}` IsNull false → voice; `…Parent.Messaging_Session__c`
   IsNull false → messaging; default → "no interaction linked"), each branch appending
   `{!<Action>.conversationTranscript}`. `getConvTscpForRecord` needs
   `<flowTransactionModel>CurrentTransaction</flowTransactionModel>` and is flow-only.
4. A final `AddPromptInstructions` with the TASK (the sections you want the summary to produce).

Full PromptFlow authoring detail (merge-field grounding, transcript gating, gotchas) lives in
`calling-prompt-templates-in-flows` **Pattern B** — do not duplicate it; this skill is just
the record-summary wrapper.

---

## Lifecycle

1. Write + deploy the **PromptFlow** data provider (Active).
2. Write the record-summary template `status=Draft`, deploy. For a FRESH template, do NOT
   hand-manage `versionIdentifier`/`activeVersionIdentifier` — the server assigns on deploy.
3. Retrieve the deployed template to read the server `versionIdentifier`, then set
   `<status>Published</status>` + top-level `<activeVersionIdentifier>` = that hash, and
   redeploy — otherwise it is "No active template version". (Same flex-template publish dance;
   see `flex-prompt-template-active-version-identifier` memory.)
4. **Surface it**: the record-summary template appears as the Einstein **Record Summary**
   content for its `<relatedEntity>` object. Add the Record Summary / prompt-template
   component to that object's Lightning record page (admin step), or invoke the template with
   the record Id programmatically.

---

## Smoke-test (Rule 0)

Record-summary templates are callable via `ConnectApi.EinsteinLLM.generateMessagesForPromptTemplate`
with the SObject input. Pass `Input:<Object>` as a WrappedValue whose value is the record Id (the
platform resolves the SObject). Confirm the briefing is grounded in the real record + transcript,
not generic. Verified call shape:

```apex
Map<String,ConnectApi.WrappedValue> inp = new Map<String,ConnectApi.WrappedValue>();
ConnectApi.WrappedValue v = new ConnectApi.WrappedValue(); v.value = '<recordId>';
inp.put('Input:Case', v);
ConnectApi.EinsteinPromptTemplateGenerationsInput req = new ConnectApi.EinsteinPromptTemplateGenerationsInput();
req.additionalConfig = new ConnectApi.EinsteinLlmAdditionalConfigInput();
req.additionalConfig.applicationName = 'PromptBuilderPreview';
req.isPreview = false; req.inputParams = inp;
String out = ConnectApi.EinsteinLLM.generateMessagesForPromptTemplate('<TemplateDevName>', req).generations[0].text;
```
(If the SObject input won't resolve from a bare Id in your org, test instead by adding the
Record Summary component to the record page and viewing it there.)

---

## Gotchas

- **`{!Get_<Record>.Owner.Name}` is NOT dereferenceable in a Flow** — `OwnerId` is a polymorphic
  User/Group lookup, so a merge field through `.Owner.Name` fails deploy with
  `field integrity exception: invalid reference`. Drop it or resolve the owner another way.
  Standard lookups (`Parent`, `Contact`, `Account`) dereference fine with `storeOutputAutomatically`.
- **The input apiName is the literal `objectToSummarize`** and the definition is
  `SOBJECT://<Object>` — not a String. Using a String input makes it a flex template, not a
  record summary, and it won't bind to the Record Summary component.
- **`<relatedEntity>` must match the object** the record page is for, or the template won't be
  offered as that object's Record Summary.
- **Converting a flex template to record-summary**: you cannot flip `<type>` on a published
  flex template cleanly (input shape changes from String to SObject = unsafe change). Create a
  NEW template dev name with the record-summary shape; keep the same PromptFlow.
- Reuse everything else from `calling-prompt-templates-in-flows` Pattern B (transcript gating,
  merge-field grounding, the publish version dance).
