---
name: replicating-omnichannel-routing-flows
description: "Build from scratch OR copy across orgs an Omni-Channel escalation RoutingFlow — the recordUpdate → routeWork flow that hands a live Messaging or Voice conversation off to a human queue when an Agentforce agent calls @utils.escalate. Includes complete, verified, deployable XML for BOTH the VoiceCall and MessagingSession variants (ships as ready-to-edit templates in assets/), plus the cross-org port procedure (re-pointing the hardcoded queue Id, keeping the standard service channel, confirming the Escalated_to_Human__c flag exists, deploying Active, and wiring the messaging-vs-voice channel binding). Use whenever you need to author, build, create, port, replicate, mirror, or recreate an omni-channel escalation/routing flow — for voice OR messaging. Trigger on: \"build an omni-channel routing flow\", \"create an escalation flow for voice calls\", \"make a routeWork flow from scratch\", \"copy the escalation flow to the other org\", \"replicate routeWork flow\", \"recreate the omni-channel routing flow\", \"my agent's escalate doesn't route\", \"port RoutingFlow\"."
compatibility: "Salesforce CLI (sf) v2+; Omni-Channel + Enhanced Messaging / Service Cloud Voice; escalation flows are ProcessType=RoutingFlow"
metadata:
  version: "1.0"
  last_updated: "2026-07-26"
---

# Replicating Omni-Channel Routing Flows Across Orgs

## What this skill is for

An Omni-Channel **escalation RoutingFlow** is the flow an Agentforce (or bot) agent invokes via `@utils.escalate` to hand a live conversation off to a human. It is a tiny flow:

```
Start (input variable: recordId (String); NO triggerType — a bare Start with just a connector)
  → recordUpdate: set Escalated_to_Human__c = true on the conversation record (filter Id = recordId)
  → routeWork: route the record to a queue on a service channel
```

**To build one from scratch**, see [§ Build an escalation RoutingFlow from scratch](#build-an-escalation-routingflow-from-scratch) below — it has the complete, verified XML for both channels and ready-to-edit templates in `assets/`.

These flows **cannot be blindly copied** between orgs because they embed **org-specific queue Ids** (a `Group.Id`, which differs in every org). A straight metadata copy deploys a flow that routes to a queue Id that doesn't exist in the target org — it validates, deploys, and then silently fails to route at runtime. This skill is the procedure to port one correctly.

There is one flow **per channel**: a Messaging variant (updates `MessagingSession`, routes on `sfdc_livemessage`) and a Voice variant (updates `VoiceCall`, routes on `sfdc_phone`).

> **Escalation (this skill) vs. inbound-to-ASA (a different skill).** This skill covers `routeWork` with **`routingType=QueueBased`** — routing to a **human queue**. To route the *other* direction — an inbound VoiceCall/MessagingSession **to an Agentforce Service Agent (copilot)** — use the `routing-inbound-conversations-to-asa` skill: that one uses **`routingType=Copilot`** with `copilotId`/`copilotLabel` **plus a REQUIRED fallback `queueId`+`queueLabel`** (a copilot `routeWork` still mandates a fallback queue). Don't conflate the two `routingType`s.

## Anatomy — what is org-specific vs. portable

| Element | Portable as-is? | Notes |
|---|---|---|
| `processType` = `RoutingFlow` | ✅ | Same in every org |
| Bare `start` (connector only, **no** `triggerType`) + input variable `recordId` (String, isInput) | ✅ | Same |
| `recordUpdate` target object (`MessagingSession` / `VoiceCall`) | ✅ | Channel-determined, not org-determined |
| Field set on update (e.g. `Escalated_to_Human__c = true`) | ⚠️ | Field **must exist + be FLS-readable/editable** in target org first |
| `routeWork` param `serviceChannelDevName` + `serviceChannelId` (`sfdc_livemessage`, `sfdc_phone`) | ✅ | Standard dev names, stable across orgs |
| `routeWork` param `routingType` = `QueueBased` | ✅ | Same |
| `routeWork` param `queueId` (the `Group.Id`, a `stringValue`) | ❌ | **Org-specific — MUST be re-pointed** |
| `routeWork` param `queueLabel` / any label referencing the queue | ❌ | Swap to match the target queue |
| Flow API name (`Escalation_flow_from_<Agent>_to_Queue_<channel>`) | ❌ | Rename to the target agent |

## Procedure

Use `sf` with `--json` on every command. Set/confirm the target org first (see the `switching-org` skill).

### 1. Retrieve the source flow definition
Prefer Tooling API so you get the resolved metadata regardless of local project state:
```bash
sf data query --use-tooling-api --json \
  -q "SELECT Id, Metadata FROM Flow WHERE Definition.DeveloperName='<SourceFlowName>' AND Status='Active' LIMIT 1"
```
Or, if you have a DX project, `sf project retrieve start --metadata Flow:<SourceFlowName> --json`.

### 2. Extract the org-specific tokens from the source
From the retrieved XML/metadata record:
- `queueId` (18/15-char `00G...`) and any `queueLabel`.
- `serviceChannelDevName` (`sfdc_livemessage` for messaging, `sfdc_phone` for voice).
- The `recordUpdate` object + the field being set (e.g. `Escalated_to_Human__c`).

### 3. Prepare the TARGET org (pre-checks)
```bash
# a) Find the destination queue Id(s) in the target org. Match by the queue's
#    DeveloperName (queues are usually named consistently, e.g. SDO_Service_Messaging /
#    SDO_Service_Voice_Call), NOT by Id.
sf data query --json \
  -q "SELECT Id, DeveloperName, Name, Type FROM Group WHERE Type='Queue' AND DeveloperName IN ('<MsgQueueDevName>','<VoiceQueueDevName>')"

# b) Confirm the service channels exist (they almost always do in an Omni/SCV org).
sf data query --json \
  -q "SELECT Id, DeveloperName, MasterLabel FROM ServiceChannel WHERE DeveloperName IN ('sfdc_livemessage','sfdc_phone')"

# c) Confirm the update field exists on the target object; create + FLS it if missing.
sf data query --use-tooling-api --json \
  -q "SELECT QualifiedApiName FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName='MessagingSession' AND QualifiedApiName='Escalated_to_Human__c'"
```
If the field is missing, create it (`generating-custom-field` skill), grant FLS to the relevant profiles, and deploy **before** the flow — the flow's `recordUpdate` will fail to deploy against a field that doesn't exist.

### 4. Build the target flow
Copy the source XML into the target DX project under `flows/`, then swap ONLY the org-specific tokens. `sed` + a stray-reference check is the safe way:
```bash
cp <source>.flow-meta.xml <TargetFlowName>.flow-meta.xml
sed -i "s/<SOURCE_QUEUE_ID>/<TARGET_QUEUE_ID>/g; s/<SOURCE_QUEUE_LABEL>/<TARGET_QUEUE_LABEL>/g" <TargetFlowName>.flow-meta.xml
# Rename the interviewLabel / label if they name the source agent.
# CRITICAL: prove there are zero leftover source-org references before deploying:
grep -c "<SOURCE_QUEUE_ID>\|<SourceAgentName>" <TargetFlowName>.flow-meta.xml   # must print 0
```
Keep `serviceChannelDevName`, `processType`, `recordUpdate` object/field, and the `recordId` input unchanged.

### 5. Deploy the flow Active
```bash
sf project deploy start --metadata Flow:<TargetFlowName> --json
```
Confirm it deployed Active:
```bash
sf data query --use-tooling-api --json \
  -q "SELECT ProcessType, Status FROM FlowDefinitionView WHERE ApiName='<TargetFlowName>'"
```

### 6. Wire the flow to the channel — the binding differs by channel

**This is the step people miss.** Deploying the flow Active does nothing until the channel is told to use it.

- **Messaging → bind in the agent metadata.** In the agent's `.agent` file, the `connection customer_web_client` (or equivalent messaging connection) block carries the escalation binding:
  ```
  connection customer_web_client:
      adaptive_response_allowed: True
      outbound_route_name: "flow://<TargetFlowName_messaging>"
      outbound_route_type: "OmniChannelFlow"
      escalation_message: "Please hold while I transfer you to a representative."
  ```
  Re-publish + re-activate the agent (see `developing-agentforce`).

- **Voice → bind in Setup, NOT in agent metadata.** The `connection telephony.outbound_route_name` in the `.agent` often points to an **inbound** omni-flow (the flow that brings the call to the agent), not the voice escalation flow — do not overwrite it or you break inbound voice. Voice escalation is wired at the Service Cloud Voice / Omni-Channel voice-channel layer in Setup. If it's not metadata-deployable in the org, hand the user the exact Setup steps: Setup → the voice channel's flow assignment → set the escalation flow.

### 7. Verify
- `FlowDefinitionView` shows `ProcessType=RoutingFlow`, `Status=Active`.
- The `routeWork` queueId resolves to a real `Group` in the target org (re-query by Id to confirm).
- End-to-end: trigger the agent's escalate on each channel and confirm the conversation lands in the correct queue and `Escalated_to_Human__c` flips to true.

## Gotchas (hard-won)

- **Queue Ids are per-org.** The #1 failure. Always look the target queue up by `DeveloperName` and swap the Id. A copied flow with the source Id validates and deploys — it just doesn't route.
- **`serviceChannelDevName` is standard** (`sfdc_livemessage`, `sfdc_phone`) and portable; don't "fix" it.
- **The update field must exist first.** Create + FLS `Escalated_to_Human__c` (or whatever field the flow sets) on the target object before deploying the flow.
- **Messaging binds in metadata; voice binds in Setup.** They are not symmetric. Leave the telephony `outbound_route_name` alone (it's usually the inbound flow).
- **Prove zero stray references** with `grep -c` after the `sed` swap. Labels, `interviewLabel`, and description strings often still name the source org/agent/queue.
- **The agent script itself usually needs no edit** for escalation — it already calls `@utils.escalate`; the flow binds at the channel layer, not in the escalation subagent YAML.

---

## Build an escalation RoutingFlow from scratch

Use this when there is no source flow to copy — you're authoring the escalation flow fresh in an org (voice or messaging). Two ready-to-edit templates ship with this skill:

- `assets/escalation-routingflow-voice.flow-meta.xml` — VoiceCall → phone queue
- `assets/escalation-routingflow-messaging.flow-meta.xml` — MessagingSession → messaging queue

Both are verified against the working CommericalDemos flows `Escalation_flow_from_BWAM_ASA_to_Queue_voice` / `..._messaging` (look there for a live example if you need more detail).

### The full VoiceCall flow (canonical, deployable)

This is the complete, real structure — nothing omitted. A RoutingFlow escalation flow is exactly three moving parts: an input `recordId` variable, a `recordUpdate`, and a `routeWork` action call. The `start` is bare (just a connector — **no `triggerType`**; the platform invokes it via `@utils.escalate`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionCalls>
        <name>Route_to_Voice_Queue</name>
        <label>Route to Voice Queue</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <actionName>routeWork</actionName>
        <actionType>routeWork</actionType>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>recordId</name>
            <value><elementReference>recordId</elementReference></value>
        </inputParameters>
        <inputParameters>
            <name>serviceChannelLabel</name>
            <value><stringValue>Phone</stringValue></value>
        </inputParameters>
        <inputParameters>
            <name>serviceChannelDevName</name>
            <value><stringValue>sfdc_phone</stringValue></value>
        </inputParameters>
        <inputParameters>
            <name>routingType</name>
            <value><stringValue>QueueBased</stringValue></value>
        </inputParameters>
        <inputParameters>
            <name>queueLabel</name>
            <value><stringValue>General Voice</stringValue></value>   <!-- ← target queue label -->
        </inputParameters>
        <inputParameters>
            <name>serviceChannelId</name>
            <value>
                <setupReference>sfdc_phone</setupReference>
                <setupReferenceType>ServiceChannel</setupReferenceType>
            </value>
        </inputParameters>
        <inputParameters>
            <name>queueId</name>
            <value><stringValue>00GgL00000GQjJIUA1</stringValue></value>   <!-- ← target queue Group.Id -->
        </inputParameters>
        <nameSegment>routeWork</nameSegment>
        <offset>0</offset>
        <versionString>2.0.0</versionString>
    </actionCalls>
    <apiVersion>67.0</apiVersion>
    <areMetricsLoggedToDataCloud>false</areMetricsLoggedToDataCloud>
    <environments>Default</environments>
    <interviewLabel>Escalation flow to Voice Queue {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Escalation flow to Voice Queue</label>
    <processType>RoutingFlow</processType>
    <recordUpdates>
        <name>Update_VoiceCall</name>
        <label>Update VoiceCall</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector><targetReference>Route_to_Voice_Queue</targetReference></connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value><elementReference>recordId</elementReference></value>
        </filters>
        <inputAssignments>
            <field>Escalated_to_Human__c</field>
            <value><booleanValue>true</booleanValue></value>
        </inputAssignments>
        <object>VoiceCall</object>
    </recordUpdates>
    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector><targetReference>Update_VoiceCall</targetReference></connector>
    </start>
    <status>Active</status>
    <variables>
        <name>recordId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

> The full asset file also carries three `<processMetadataValues>` (`BuilderType`, `CanvasMode`, `OriginBuilderType`) and the complete set of empty `routeWork` `inputParameters` (agentLabel, botId, skillOption, …). Those are cosmetic/optional — the platform accepts the flow without them — but keeping them matches what Flow Builder writes and avoids a diff if the flow is later opened in the UI.

### Voice vs. messaging — the only differences

Everything above is the voice flow. The messaging flow is **identical** except for four values:

| Parameter | Voice | Messaging |
|---|---|---|
| `recordUpdate` `<object>` | `VoiceCall` | `MessagingSession` |
| `serviceChannelDevName` + `serviceChannelId` (`setupReference`) | `sfdc_phone` | `sfdc_livemessage` |
| `serviceChannelLabel` | `Phone` | `Messaging` |
| `queueId` / `queueLabel` | voice queue | messaging queue |

### `routeWork` parameter reference (the ones that matter)

| Param | Value | Notes |
|---|---|---|
| `recordId` | `elementReference` → `recordId` | The conversation record being routed |
| `routingType` | `QueueBased` | **Note the name is `routingType`, not `routeType`** |
| `serviceChannelDevName` | `sfdc_phone` / `sfdc_livemessage` | `stringValue` |
| `serviceChannelId` | `setupReference` = same dev name, `setupReferenceType` = `ServiceChannel` | Both this **and** `serviceChannelDevName` are set |
| `queueId` | `Group.Id` (`00G…`) as a `stringValue` | Org-specific — the thing you swap |
| `queueLabel` | queue's display label | Org-specific |
| `serviceChannelLabel` | `Phone` / `Messaging` | Display only |

`routeWork` also accepts many empty params for other routing targets (`agentId`, `botId`, `skillOption`, `routingConfigId`, …) — leave them empty/absent for QueueBased queue routing.

### From-scratch checklist

1. Copy the matching template from `assets/` into your DX project's `flows/` folder; rename the file to your flow's API name.
2. Query the target queue: `SELECT Id, DeveloperName, Name FROM Group WHERE Type='Queue'`. Fill in `queueId` + `queueLabel`.
3. Confirm the conversation object has `Escalated_to_Human__c` (or your chosen flag) and the running user has FLS-edit. Create + FLS it first if missing.
4. Update `<label>` and `<interviewLabel>` to match the file name.
5. `sf project deploy start --metadata Flow:<YourFlowName> --json` — it deploys **Active** because `<status>Active</status>` is in the XML.
6. Wire it to the channel per [§6 above](#6-wire-the-flow-to-the-channel--the-binding-differs-by-channel): messaging binds in the agent's `.agent` `connection` block (`outbound_route_type: OmniChannelFlow`); **voice binds in Setup** at the SCV/Omni voice-channel layer, not in metadata.
7. Verify: `FlowDefinitionView` shows `ProcessType=RoutingFlow`, `Status=Active`; trigger `@utils.escalate` and confirm the conversation lands in the queue and the flag flips.
