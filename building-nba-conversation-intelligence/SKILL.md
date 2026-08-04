---
name: building-nba-conversation-intelligence
description: "Use this skill when the user needs to build a Next Best Action (NBA) system triggered by Conversation Intelligence (CI) Signal Rules on a messaging or voice channel. Covers the full stack: screen flows (recommendation actions), Recommendation records, Conversation Intelligence Signal Rules (with keywords), and the Recommendation Strategy Flow that connects rules to recommendations. Trigger when the user mentions NBA, Next Best Action, recommendation, conversation intelligence, signal rules, keyword detection, or wants to surface guided steps to an agent during a live conversation."
metadata:
  version: "1.0"
---

# Building NBA with Conversation Intelligence Signal Rules

## Overview

This skill covers the end-to-end process of building a Next Best Action system that triggers during live conversations when specific keywords are detected. The stack has 4 layers:

```
Keyword spoken in conversation
    → CI Signal Rule fires (detects keyword on configured channel)
    → Strategy Flow receives ruleDevName, looks up Recommendation, outputs it
    → Agent sees Recommendation card in the NBA panel
    → Agent clicks → Screen Flow opens with guided resolution steps
```

## The 4 Artifacts to Build (in order)

### 1. Screen Flows (the guided steps the agent sees)
### 2. Recommendation Records (the card metadata — name, description, image, action reference)
### 3. Conversation Intelligence Signal Rules (keyword detection → fires the strategy)
### 4. Recommendation Strategy Flow (receives rule name → outputs the matching recommendation)

---

## 1. Screen Flows (Action Flows)

Simple screen flows with `processType=Flow`, `status=Active`, and a `recordId` String input variable.

**Pattern:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <processType>Flow</processType>
    <status>Active</status>
    <screens>
        <name>Screen_Guide</name>
        <label>Agent Guide</label>
        <fields>
            <name>Header</name>
            <fieldText>&lt;p&gt;&lt;b&gt;Title&lt;/b&gt;&lt;/p&gt;&lt;p&gt;Steps...&lt;/p&gt;</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <start>
        <connector><targetReference>Screen_Guide</targetReference></connector>
    </start>
    <variables>
        <name>recordId</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

Deploy via: `sf project deploy start --source-dir force-app/main/default/flows/<FlowName>.flow-meta.xml`

---

## 2. Recommendation Records

Created via Apex DML (NOT metadata deploy). Key fields:

| Field | Value |
|---|---|
| `Name` | Human-readable title shown on the card (e.g., "Lease Late Fee Waiver") |
| `Description` | One-line description shown below the title |
| `ActionReference` | The screen flow's API name (e.g., `Late_Fee_Waiver_Steps`) |
| `AcceptanceLabel` | Button text the agent clicks (e.g., "View Waiver Steps") |
| `RejectionLabel` | Dismiss label (e.g., "Dismiss") |

**`IsActionActive` is NOT writable** — it auto-resolves to `true` if the referenced flow is Active.

```apex
Recommendation r = new Recommendation(
    Name = 'Lease Late Fee Waiver',
    Description = 'Guide agent through late fee waiver eligibility and submission',
    ActionReference = 'Late_Fee_Waiver_Steps',
    AcceptanceLabel = 'View Waiver Steps',
    RejectionLabel = 'Dismiss'
);
insert r;
```

---

## 3. Conversation Intelligence Signal Rules

> ⚠️ **THE CHANNEL MUST BE ACTIVE OR THE RULES ARE INVISIBLE IN THE UI.** This applies to **BOTH Voice and Messaging** channels. A CI Signal Rule is bound to a `ConversationChannelId`, and the Conversation Intelligence Signal Rules Setup page filters the rule list **by channel** — it only lists rules whose channel is **active** (`MessagingChannel.IsActive = true`). Rules created (correctly, via REST, returning HTTP 201) against an **inactive** channel are real records in the org but **will not appear in Setup**, so it looks like nothing was created.
>
> - **Voice channels** are typically already active (the phone/PSTN channel is live), so voice CI rules show up immediately — this is why voice "just works."
> - **Messaging channels** (especially a freshly-built In-App & Web `EmbeddedMessaging` channel) are often `IsActive = false` until their **Embedded Service deployment is activated in Setup**. Until then their CI rules are hidden.
>
> **Before telling the user the rules are done, verify the target channel is active:** `SELECT Id, DeveloperName, IsActive FROM MessagingChannel WHERE Id = '<channelId>'`. If `IsActive = false`, either (a) activate the channel — for In-App & Web, activate its Embedded Service deployment in Setup (Setup → Embedded Service Deployments → the deployment → Activate; the embedded site is Setup-wizard-provisioned, not metadata-deployable) — or (b) point the rules at an already-active channel. The records don't need rebuilding; activation is purely what makes them **visible and live**.

**Object:** `ConvIntelligenceSignalRule` — queryable but NOT DML-createable via standard Apex.

**Creation method:** REST API via Apex callout:

```apex
String base = URL.getOrgDomainUrl().toExternalForm();
String token = UserInfo.getSessionId();
Http h = new Http();

String body = JSON.serialize(new Map<String,Object>{
    'DeveloperName' => 'Late_Fee_Lease_Rule',    // MUST match what strategy flow checks
    'Label' => 'Late Fee Lease Rule',
    'IsActive' => true,
    'Service' => 'KeywordMatch',
    'ParticipantRole' => 'AgentOrCustomer',       // or 'Agent' or 'Customer'
    'ActionType' => 'LaunchNBA',
    'ConversationChannelId' => '<channel_Id>',    // query MessagingChannel for the Id
    'Criteria' => '1 OR 2 OR 3 OR 4 OR 5 OR 6'  // matches N sub-rules by order
});

HttpRequest req = new HttpRequest();
req.setEndpoint(base + '/services/data/v62.0/sobjects/ConvIntelligenceSignalRule');
req.setMethod('POST');
req.setHeader('Authorization', 'Bearer ' + token);
req.setHeader('Content-Type', 'application/json');
req.setBody(body);
HttpResponse res = h.send(req);
// res.getStatusCode() == 201 on success
```

**Sub-rules (keywords):** stored in `ConvIntelligenceSignalSubRule`:

```apex
String subBody = JSON.serialize(new Map<String,Object>{
    'ConvIntelligenceSignalRuleId' => '<ruleId>',
    'Type' => 'Keyword',
    'Operator' => 'Equals',
    'OperandValue' => 'late fee',     // the keyword phrase
    'Order' => 1                       // matches the Criteria position (1 OR 2 OR ...)
});

HttpRequest subReq = new HttpRequest();
subReq.setEndpoint(base + '/services/data/v62.0/sobjects/ConvIntelligenceSignalSubRule');
subReq.setMethod('POST');
subReq.setHeader('Authorization', 'Bearer ' + token);
subReq.setHeader('Content-Type', 'application/json');
subReq.setBody(subBody);
h.send(subReq);
```

**Finding the channel Id:** Query `MessagingChannel` or check existing rules:
```apex
List<ConvIntelligenceSignalRule> existing = [SELECT ConversationChannelId FROM ConvIntelligenceSignalRule WHERE IsActive=true LIMIT 1];
```

---

## 4. Recommendation Strategy Flow (CRITICAL — the connector)

This is a `RecommendationStrategy` process type flow. It receives the fired rule's developer name and outputs the matching Recommendation record.

### CORRECT Variables (v3 — user-corrected pattern)

| Variable | Type | Input/Output | Notes |
|---|---|---|---|
| `recordId` | String | Input | The MessagingSession or conversation record Id |
| `ruleDevName` | String | Input | **The CI rule developer name that fired — USE THIS DIRECTLY in decisions** |
| `intelligenceSignals` | Apex (`EnhancedChannel__IntelligenceSignals`) | Input | Signal metadata from CI |
| `matchedKeywords` | String Collection | Input | Keywords that triggered |
| `ConversationKey` | String | Input | Conversation identifier |
| `outputRecommendations` | SObject Collection (Recommendation) | **Output** | What the agent sees |
| `DefaultOutputRecommendations` | SObject Collection (Recommendation) | Internal | Empty collection for clearing |

### WRONG pattern (what NOT to do)
- ❌ Do NOT add an `IntelligenceRuleDevName` variable — it doesn't exist in the CI contract
- ❌ Do NOT create a formula like `IF(ISBLANK(IntelligenceRuleDevName), ruleDevName, IntelligenceRuleDevName)` — unnecessary indirection
- ❌ Do NOT add a `RuleDevNameForDecision` formula — just reference `ruleDevName` directly

### CORRECT Flow Structure

```
Start → Determine_Rule (Decision)
         ├─ Rule A matched (ruleDevName == 'Rule_A_Dev_Name') → Clear → Get Rec A → Assign Rec A
         ├─ Rule B matched (ruleDevName == 'Rule_B_Dev_Name') → Clear → Get Rec B → Assign Rec B
         └─ default → (no output, end)
```

### CORRECT Decision conditions

```xml
<decisions>
    <name>Determine_Rule</name>
    <label>Determine which CI Rule fired</label>
    <defaultConnectorLabel>No Matching Rule</defaultConnectorLabel>
    <rules>
        <name>Late_Fee_Rule_Matched</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>ruleDevName</leftValueReference>  <!-- DIRECT reference, no formula -->
            <operator>EqualTo</operator>
            <rightValue>
                <stringValue>Late_Fee_Lease_Rule</stringValue>  <!-- MUST match CI rule DeveloperName exactly -->
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Clear_Before_Late_Fee</targetReference>
        </connector>
        <label>Late Fee Rule Matched</label>
    </rules>
</decisions>
```

### Per-rule path pattern (3 elements per rule)

```xml
<!-- 1. Clear the output collection -->
<assignments>
    <name>Clear_Before_X</name>
    <assignmentItems>
        <assignToReference>outputRecommendations</assignToReference>
        <operator>Assign</operator>
        <value><elementReference>DefaultOutputRecommendations</elementReference></value>
    </assignmentItems>
    <connector><targetReference>Get_X_Recommendation</targetReference></connector>
</assignments>

<!-- 2. Look up the Recommendation by Name -->
<recordLookups>
    <name>Get_X_Recommendation</name>
    <filters>
        <field>Name</field>
        <operator>EqualTo</operator>
        <value><stringValue>Exact Recommendation Name</stringValue></value>
    </filters>
    <getFirstRecordOnly>true</getFirstRecordOnly>
    <object>Recommendation</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
    <connector><targetReference>Assign_X_Recommendation</targetReference></connector>
</recordLookups>

<!-- 3. Add to output -->
<assignments>
    <name>Assign_X_Recommendation</name>
    <assignmentItems>
        <assignToReference>outputRecommendations</assignToReference>
        <operator>Add</operator>
        <value><elementReference>Get_X_Recommendation</elementReference></value>
    </assignmentItems>
</assignments>
```

---

## Full Working Example (deployed and tested)

Reference file: `C:\Users\sshvarzman\AppData\Local\Temp\bmo-deploy\force-app\main\default\flows\Messaging_NBA_Strategy.flow-meta.xml`

This is the user-corrected v3 of the BMO Messaging NBA Strategy flow with 3 rules:
- `Late_Fee_Lease_Rule` → "Lease Late Fee Waiver" recommendation → `Late_Fee_Waiver_Steps` flow
- `Lease_Buyout_Rule` → "Early Lease Buyout" recommendation → `Lease_Buyout_Steps` flow
- `Stolen_Damaged_Vehicle_Rule` → "Stolen or Damaged Vehicle" recommendation → `Stolen_Damaged_Vehicle_Steps` flow

---

## Step-by-Step Recipe (end to end)

1. **Ask the user:** How many recommendations/rules? What keywords per rule? What channel?
2. **Create screen flows** — one per recommendation, with guided steps and `recordId` input
3. **Deploy screen flows** — `sf project deploy start --source-dir`
4. **Create Recommendation records** via Apex DML — Name must match what the strategy flow looks up
5. **Find the channel Id** — query `ConvIntelligenceSignalRule` for an existing active rule's `ConversationChannelId`, or query messaging channel objects
6. **Create CI Signal Rules** via REST API (`/sobjects/ConvIntelligenceSignalRule`) — one per topic
7. **Create Sub-Rules (keywords)** via REST API (`/sobjects/ConvIntelligenceSignalSubRule`) — one per keyword per rule
8. **Create the Strategy Flow** — `processType=RecommendationStrategy`, variables as documented above, decision on `ruleDevName` directly
9. **Deploy strategy flow** — must be Active
10. **Verify** — query all rules, recommendations, and flows; test in live messaging

---

## Common Mistakes to Avoid

| Mistake | Fix |
|---|---|
| Adding `IntelligenceRuleDevName` variable | Don't. CI passes rule name in `ruleDevName` directly |
| Creating a formula to resolve the rule name | Don't. Reference `ruleDevName` in decision conditions directly |
| Trying to insert `ConvIntelligenceSignalRule` via DML | Can't — use REST API via HttpRequest |
| Setting `IsActionActive` on Recommendation | Can't — auto-resolves from the flow's Active status |
| Mismatching rule DeveloperName in strategy vs CI rule | The string in the decision condition MUST equal the CI rule's DeveloperName exactly (case-sensitive) |
| Mismatching Recommendation Name in strategy vs record | The string in the recordLookup filter MUST equal the Recommendation record's Name exactly |

---

## Querying Existing CI Rules

```apex
// Rules
List<ConvIntelligenceSignalRule> rules = [SELECT Id, DeveloperName, Label, IsActive, ActionType, ConversationChannelId FROM ConvIntelligenceSignalRule];

// Sub-rules (keywords)
List<ConvIntelligenceSignalSubRule> subs = [SELECT Id, ConvIntelligenceSignalRuleId, Type, Operator, OperandValue FROM ConvIntelligenceSignalSubRule];
```

---

## Channel Reference

To find the right `ConversationChannelId`:
- For messaging: query `MessagingChannel` or get it from an existing rule
- The channel Id for "Messaging_for_In_App_Web" in the BMO org is `0MjKj0000008V3QKAU`
- Voice channels use `VoiceChannel` or the telephony config Id

⚠️ **The channel must be ACTIVE (`MessagingChannel.IsActive = true`) for its CI rules to appear in the Setup UI — true for BOTH voice and messaging channels.** See the warning at the top of §3. An inactive messaging channel (e.g. a not-yet-activated In-App & Web deployment) hides its rules even though the records exist.

---

## Verification Checklist

After building:
- [ ] All screen flows deployed and Active (`FlowDefinitionView.IsActive = true`)
- [ ] All Recommendation records created with `IsActionActive = true`
- [ ] All CI Signal Rules created with `IsActive = true` and correct `ConversationChannelId`
- [ ] **The target channel is ACTIVE** (`MessagingChannel.IsActive = true`) — required for the rules to show in the CI Setup UI, for BOTH voice and messaging channels. If inactive (common for a new In-App & Web messaging channel), activate its Embedded Service deployment in Setup first.
- [ ] All sub-rules (keywords) created with correct `ConvIntelligenceSignalRuleId`
- [ ] Strategy flow deployed, Active, and `processType=RecommendationStrategy`
- [ ] Strategy flow variables: `ruleDevName` (Input String), `outputRecommendations` (Output SObject Collection Recommendation), `ConversationKey`, `intelligenceSignals`, `matchedKeywords`, `recordId`, `DefaultOutputRecommendations`
- [ ] Decision conditions reference `ruleDevName` DIRECTLY (no formula)
- [ ] Rule DeveloperName strings in decision conditions exactly match CI rule DeveloperNames
- [ ] Recommendation Name strings in recordLookup filters exactly match Recommendation record Names
