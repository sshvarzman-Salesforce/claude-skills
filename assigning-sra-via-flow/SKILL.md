---
name: assigning-sra-via-flow
description: "Wire the 'Define Your Multi-Agent Assignment Criteria' autolaunched flow that dynamically assigns which ServicePlanner Service Rep Assistant (SRA) is shown on a live VoiceCall / MessagingSession / Case, based on that record's field values. This is the OPTIONAL flow you attach in the SRA setup step 'Define Your Multi-Agent Assignment Criteria' (only needed when an org has MORE THAN ONE SRA). The whole contract is a tiny AutoLaunchedFlow: one INPUT text variable named exactly `recordId` (the interaction record Id the platform passes in), a Get Records to load that record, a Decision on its fields, and one OUTPUT text variable whose VALUE MUST BE THE SRA's AGENT API NAME (the BotDefinition/GenAiPlannerBundle DeveloperName, e.g. `CanadaPensionServiceAssistant`) — NOT a label, NOT an Id. The platform reads that single output string and shows the matching SRA. Covers the exact variable shapes, the per-channel differences (VoiceCall vs MessagingSession vs Case), how to add a new demo/brand rule, and the fact that the output-variable NAME is free (any single output String works) while its VALUE must equal the agent API name. Use whenever you need to route/assign an SRA by record field, scale up an existing assignment flow to a new brand/demo, build the assignment flow from scratch, or answer 'how does the SRA multi-agent assignment flow work / what input + output variables does it need'. Trigger on: 'SRA assignment flow', 'Define Your Multi-Agent Assignment Criteria', 'assign SRA based on record', 'which service rep assistant is shown', 'SRA assignment input output variable', 'multi-agent assignment flow ServicePlanner', 'assign SRA by API name'."
compatibility: "Salesforce CLI (sf) v2+; classic ServicePlanner SRA (agentType=ServicePlanner) with two or more SRAs in the org; assignment flow is an AutoLaunchedFlow (processType=AutoLaunchedFlow); works for VoiceCall, MessagingSession, and Case SRA surfaces"
metadata:
  version: "1.0"
  last_updated: "2026-08-14"
---

# Assigning a ServicePlanner SRA via an Autolaunched Flow

## What this skill is for

In the ServicePlanner (Service Rep Assistant) setup there is an optional step:

> **Define Your Multi-Agent Assignment Criteria** *(Optional)*
> Add an autolaunched flow to determine which agent is assigned based on the record details. If you only have one agent, you don't need to assign a flow.

That flow is the switch that decides **which SRA** appears on a given live **VoiceCall / MessagingSession / Case**, using that record's own field values. You only need it when an org has **two or more** SRAs; with one SRA the platform just uses it.

This skill is the exact, verified contract for that flow: the required input variable, the required output variable, what the output value must be, and how to extend or build one. Ground-truthed from two Active, deployed flows in CommericalDemos (`SRA_Assignment_on_VoiceCalls`, `SRA_Assignment_for_Messaging`).

## The contract (the whole thing)

The flow is a plain **`AutoLaunchedFlow`**. Its entire interface with the platform is **two variables**:

| Variable | Direction | Type | Rule |
|---|---|---|---|
| `recordId` | **Input** (`isInput=true`, `isOutput=false`) | String | **Name MUST be exactly `recordId`.** The platform passes the Id of the interaction record (VoiceCall / MessagingSession / Case) into it. |
| *(your choice)* e.g. `SRAassigned` | **Output** (`isInput=false`, `isOutput=true`) | String | The **NAME is free** — any single output String works. Its **VALUE must be the SRA's AGENT API NAME** = the `BotDefinition` / `GenAiPlannerBundle` **DeveloperName** (e.g. `CanadaPensionServiceAssistant`). The platform reads this one string and shows the matching SRA. |

> **The single most important rule:** the output string must be the **agent API name**, not the masterLabel and not a record Id. `CanadaPensionServiceAssistant` ✅ — "Canada Pension Service Assistant" ❌ — `0Xx...` ❌.
>
> **Second rule:** the input must be named **`recordId`** exactly. That's how the platform hands the record in.

The output variable NAME genuinely doesn't matter to the platform (it takes whatever single output String the flow exposes). In practice these flows use different names per channel — that's cosmetic, not required:
- Voice flow: output `SRAassigned`
- Messaging flow: output `SRAAPIName`

## Flow shape

```
Start (bare — no trigger; it's an autolaunched flow the platform invokes)
  → Get Records: load the interaction record WHERE Id = {!recordId}   (getFirstRecordOnly=true, storeOutputAutomatically)
  → Decision: branch on the record's field value(s)
        ├─ Brand A matches → Assignment: set <outputVar> = "Agent_A_ApiName"
        ├─ Brand B matches → Assignment: set <outputVar> = "Agent_B_ApiName"
        └─ Default Outcome → (leave output null → platform falls back / shows no specific SRA)
```

Per channel, only the **object** and the (cosmetic) **output-var name** differ:

| Channel | `recordId` is a… | Get Records `<object>` | Field commonly keyed on | Output var used |
|---|---|---|---|---|
| Voice | VoiceCall Id | `VoiceCall` | `Customer_Demo__c` (or any field) | `SRAassigned` |
| Messaging | MessagingSession Id | `MessagingSession` | `Customer_Demo__c` | `SRAAPIName` |
| Case | Case Id | `Case` | any Case field | (any output String) |

> The keying field is **whatever you decide** — origin, brand, record type, a custom `Customer_Demo__c`, etc. In these demo flows it's a **plain TEXT field `Customer_Demo__c`** (not a picklist), so the Decision does a free-text `EqualTo` string compare. If your field is a picklist, compare against the picklist API value the same way.

## Verified variable XML (copy these verbatim)

**Input — must be `recordId`:**
```xml
<variables>
    <name>recordId</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>true</isInput>
    <isOutput>false</isOutput>
</variables>
```

**Output — name is your choice; value carries the agent API name:**
```xml
<variables>
    <name>SRAassigned</name>          <!-- messaging flow uses SRAAPIName; either is fine -->
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
</variables>
```

## Get Records (load the record the platform passed in)

```xml
<recordLookups>
    <name>Get_VoiceCall</name>                 <!-- Get_Messaging_Session / Get_Case for other channels -->
    <label>Get VoiceCall</label>
    <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
    <connector><targetReference>Check_Demo_field_On_VC</targetReference></connector>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Id</field>
        <operator>EqualTo</operator>
        <value><elementReference>recordId</elementReference></value>
    </filters>
    <getFirstRecordOnly>true</getFirstRecordOnly>
    <object>VoiceCall</object>                  <!-- MessagingSession / Case -->
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

## Decision + Assignment (one branch per SRA)

Decision rule — compare the loaded record's field to a brand value:
```xml
<rules>
    <name>OMERS_Demo</name>
    <conditionLogic>and</conditionLogic>
    <conditions>
        <leftValueReference>Get_VoiceCall.Customer_Demo__c</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue><stringValue>OMERS</stringValue></rightValue>
    </conditions>
    <connector><targetReference>Assign_OMERS_SRA</targetReference></connector>
    <label>OMERS Demo</label>
</rules>
```

Assignment — set the output var to the **agent API name**:
```xml
<assignments>
    <name>Assign_OMERS_SRA</name>
    <label>Assign OMERS SRA</label>
    <assignmentItems>
        <assignToReference>SRAassigned</assignToReference>
        <operator>Assign</operator>
        <value><stringValue>CanadaPensionServiceAssistant</stringValue></value>   <!-- the SRA API name -->
    </assignmentItems>
</assignments>
```

> **Confirm the SRA API name** before hardcoding it — it's the `BotDefinition.DeveloperName` (same as the `GenAiPlannerBundle` dev name):
> ```bash
> sf data query --target-org <ORG> --json \
>   -q "SELECT DeveloperName, MasterLabel FROM BotDefinition WHERE AgentType='ServicePlanner'"
> ```

## Building one from scratch — steps

1. **List your SRAs** and grab each `BotDefinition.DeveloperName` (the value the flow must emit). Query above.
2. **Confirm the keying field** on the target object (VoiceCall / MessagingSession / Case). If it's a picklist you'll compare against its API value; if plain text, exact string. Inspect via REST describe (`/services/data/vXX.0/sobjects/VoiceCall/describe`) — note `PicklistValueInfo` is **not** SOQL-queryable.
3. **Author the AutoLaunchedFlow**: `recordId` input (String) + one output String; bare Start → Get Records (`Id = {!recordId}`, first-record, store automatically) → Decision (one rule per brand) → an Assignment per rule setting the output = the SRA API name. Leave the Default Outcome unconnected to fall back to no specific SRA.
4. **Deploy Active**:
   ```bash
   sf project deploy start --metadata Flow:<FlowName> --target-org <ORG> --json
   ```
   (The flow XML carries `<status>Active</status>`, so it deploys Active.)
5. **Attach it in Setup** at the SRA's **Define Your Multi-Agent Assignment Criteria** step (per channel: the voice SRA surface takes the voice flow, messaging takes the messaging flow). This binding is done in Setup, not in metadata.
6. **Verify**: `SELECT ApiName, ProcessType, Status FROM FlowDefinitionView WHERE ApiName='<FlowName>'` → `AutoLaunchedFlow`, `Active`. Then open a live record whose keying field matches a rule and confirm the right SRA appears.

## Scaling up an existing flow (add a new brand/SRA)

To route a new demo/brand to a new SRA, you add **two elements + one rule** to the existing flow — you do **not** touch the input/output variables:

1. Add a new **`<assignments>`** node that sets the SAME output var to the new SRA API name.
2. Add a new **`<rules>`** to the existing Decision matching the new field value → connect it to that assignment.
3. Redeploy `Flow:<FlowName>`.

Worked example (both CommericalDemos flows): existing rules were ClaimSecure → `ClaimSecure_Agentforce_Service_Assistant` and BMO → `Complaints_Service_Assistant`; adding OMERS meant one new rule (`Customer_Demo__c EqualTo "OMERS"`) + one assignment (`SRAassigned`/`SRAAPIName` = `CanadaPensionServiceAssistant`).

## Gotchas

- **Output value = agent API name, not label.** The #1 mistake. It must equal `BotDefinition.DeveloperName`. A label or Id silently assigns nothing.
- **Input must be named `recordId`.** The platform binds the interaction record Id to that exact name; renaming it breaks the flow.
- **One flow per surface/channel.** VoiceCall, MessagingSession, and Case each attach their own flow, keyed to their own object. Don't point a `MessagingSession` Get Records at a VoiceCall Id.
- **The output-var NAME is free.** `SRAassigned` vs `SRAAPIName` is just a naming choice — the platform reads whichever single output String the flow exposes. Don't waste time "matching" a specific name.
- **Unconnected Default Outcome = silent no-assignment.** That's the intended fallback (no specific SRA), not an error — but it means a record whose field matches no rule simply gets no dynamic SRA.
- **Binding is a Setup step.** Deploying the flow Active does nothing until you attach it under *Define Your Multi-Agent Assignment Criteria*.
- **The flow only needs to exist when there are 2+ SRAs.** With a single SRA, skip it.

## Verification checklist

- [ ] `processType = AutoLaunchedFlow`, `Status = Active`.
- [ ] Input variable named exactly `recordId` (String, isInput=true).
- [ ] Exactly one output String variable (isOutput=true) — any name.
- [ ] Get Records filters `Id = {!recordId}` on the correct object for the channel.
- [ ] Every Assignment sets the output = a real `BotDefinition.DeveloperName` (SRA API name), verified against the org.
- [ ] Decision has one rule per brand/SRA; Default Outcome left as fallback.
- [ ] Flow attached in Setup at *Define Your Multi-Agent Assignment Criteria* for the right SRA/channel.
