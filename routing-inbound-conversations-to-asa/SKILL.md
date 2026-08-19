---
name: routing-inbound-conversations-to-asa
description: Build or fix an inbound Omni-Channel RoutingFlow that hands a live VoiceCall or MessagingSession to an Agentforce Service Agent (ASA / copilot). Covers the routingType=Copilot pattern, the MANDATORY fallback queue, dual-channel Contact linking, and the voice-vs-messaging differences. Use whenever a call/chat needs to be routed TO an Agentforce agent (not escalated to a human — that is the replicating-omnichannel-routing-flows skill).
---

# Routing inbound conversations to an Agentforce Service Agent (ASA)

## What this skill is for

An **inbound RoutingFlow** is what Omni-Channel runs when a new VoiceCall or MessagingSession arrives, to decide **who** picks it up. To route the conversation to an **Agentforce Service Agent** (ASA — the bot/copilot answers first, before any human), the flow's `routeWork` action uses **`routingType=Copilot`** and points at the agent's `BotDefinition` — **plus a REQUIRED fallback queue**.

This is the mirror image of the `replicating-omnichannel-routing-flows` skill:
- **That skill** = *escalation* (agent/bot → human **queue**), `routingType=QueueBased`, invoked via `@utils.escalate`.
- **This skill** = *inbound* (channel → **ASA agent**), `routingType=Copilot`, invoked by the channel's inbound-flow assignment.

Two flows, one per channel: a **Voice** variant (VoiceCall, `sfdc_phone`, links `VoiceCall.Contact__c`) and a **Messaging** variant (MessagingSession, `sfdc_livemessage`, links `MessagingEndUser.ContactId`).

Ready-to-edit, verified templates ship in `assets/`:
- `assets/inbound-asa-voice.flow-meta.xml`
- `assets/inbound-asa-messaging.flow-meta.xml`

Both are ground-truthed from the live, Active CitiBank flows `CitiBank_ASA_Inbound_Voice` / `CitiBank_ASA_Inbound_Messaging`.

---

## THE headline lesson: `routeWork` to a copilot still REQUIRES a fallback queue

The single most common failure: authoring a `routingType=Copilot` `routeWork` with only the copilot target and **no queue**. It looks logically complete — you're routing to the agent, why name a queue? — but the platform **requires a fallback `queueId` + `queueLabel` anyway**. Omni needs a queue to fall back to when the agent can't take the work (capacity, offline, decline, timeout). Without it, routing fails.

So a copilot `routeWork` carries **both**:

| Purpose | Params |
|---|---|
| Primary target (the ASA agent) | `routingType=Copilot`, `copilotId`, `copilotLabel` |
| **Required** fallback | `queueId` (a real `00G…` Group.Id), `queueLabel` |
| Channel | `serviceChannelDevName`, `serviceChannelId`, `serviceChannelLabel` |
| Work record | `recordId` |

If you copy an escalation flow and just "swap QueueBased for Copilot," you'll drop the queue and it breaks. Keep the queue.

---

## The `routeWork` action — copilot routing, per channel

### Voice (`sfdc_phone`)

```xml
<inputParameters><name>recordId</name><value><elementReference>recordId</elementReference></value></inputParameters>
<inputParameters><name>serviceChannelLabel</name><value><stringValue>Phone</stringValue></value></inputParameters>
<inputParameters><name>serviceChannelDevName</name><value><stringValue>sfdc_phone</stringValue></value></inputParameters>
<inputParameters><name>routingType</name><value><stringValue>Copilot</stringValue></value></inputParameters>
<inputParameters><name>copilotLabel</name><value><stringValue>CitiBank ASA</stringValue></value></inputParameters>
<inputParameters>
    <name>serviceChannelId</name>
    <value><setupReference>sfdc_phone</setupReference><setupReferenceType>ServiceChannel</setupReferenceType></value>
</inputParameters>
<inputParameters>
    <name>copilotId</name>
    <value><setupReference>CitiBank_ASA</setupReference><setupReferenceType>BotDefinition</setupReferenceType></value>
</inputParameters>
<!-- REQUIRED fallback queue -->
<inputParameters><name>queueLabel</name><value><stringValue>General Voice</stringValue></value></inputParameters>
<inputParameters><name>queueId</name><value><stringValue>00GKc000000wPROMA2</stringValue></value></inputParameters>
```

Notable: on the **voice** flow the agent is expressed as a **`setupReference` to `BotDefinition`** (the agent's DeveloperName, e.g. `CitiBank_ASA`) and the channel as a `setupReference` to `ServiceChannel`. `versionString` = `2.0.0` on this action.

### Messaging (`sfdc_livemessage`)

```xml
<inputParameters><name>recordId</name><value><elementReference>recordId</elementReference></value></inputParameters>
<inputParameters><name>serviceChannelId</name><value><stringValue>0N9Kc000000h7oJKAQ</stringValue></value></inputParameters>
<inputParameters><name>serviceChannelLabel</name><value><stringValue>LiveMessage</stringValue></value></inputParameters>
<inputParameters><name>serviceChannelDevName</name><value><stringValue>sfdc_livemessage</stringValue></value></inputParameters>
<inputParameters><name>routingType</name><value><stringValue>Copilot</stringValue></value></inputParameters>
<!-- REQUIRED fallback queue -->
<inputParameters><name>queueId</name><value><stringValue>00GKc000000wPRNMA2</stringValue></value></inputParameters>
<inputParameters><name>queueLabel</name><value><stringValue>Messaging</stringValue></value></inputParameters>
<inputParameters><name>copilotId</name><value><stringValue>0XxKc000000UW41KAG</stringValue></value></inputParameters>
<inputParameters><name>copilotLabel</name><value><stringValue>CitiBank ASA</stringValue></value></inputParameters>
```

Notable difference: on the **messaging** flow `copilotId` and `serviceChannelId` are **raw Id strings** (`0Xx…` copilot config Id, `0N9…` channel Id), NOT `setupReference`s. (`0Xx` is the messaging agent-config record, not the `BotDefinition` `0Xx`→ query it, see below.) No `versionString` on this action.

> Both patterns deploy and run. The voice `setupReference` form is more portable (resolves by dev name); the messaging raw-Id form is what Flow Builder writes for messaging. Either works as long as the Ids/dev names resolve in the target org.

---

## Full flow structure (both channels)

```
Start
  → resolve the phone to search on
        Voice:     Read_Voice_Call → decide (phone input? else VoiceCall.FromPhoneNumber)
        Messaging: Load_Messaging_User (MessagingEndUser by input_record.MessagingEndUserId)
  → Load_Contact_by_Phone_Number   actionType=findMatchingIndividuals, searchObject=Contact, searchFields=Phone
  → Loop_Search_Results over .contactIds → Load_Found_Contact (Contact by Id) → contact
  → Check_Found_Contact (contact != null?)
        Found:  link the Contact
                  Voice:     recordUpdate VoiceCall.Contact__c = contact.Id   (+ optional Customer_Demo__c stamp)
                  Messaging: assign MessagingEndUser.ContactId = contact.Id → Update_Messaging_User → stamp session
        No:     just stamp the conversation record (no contact link)
  → Route_to_ASA   routeWork, routingType=Copilot, copilot target + REQUIRED fallback queue
```

- **Contact resolution is the dual-channel crux** (same as everywhere): voice links the found Contact onto the custom **`VoiceCall.Contact__c`** lookup; messaging writes **`MessagingEndUser.ContactId`**, which surfaces downstream as **`MessagingSession.EndUserContactId`**. (See the `messaging-inbound-omniflow-pattern` and `linking-individuals-by-phone-in-flows` memories/skills.)
- **`findMatchingIndividuals`** is the standard phone→Contact matcher; loop its `.contactIds` and load the first.
- The **messaging** flow's input variable is **`input_record` (SObject MessagingSession)** in addition to `recordId` (String) — it reads `input_record.MessagingEndUserId` to find the MessagingEndUser. The **voice** flow only needs `recordId` + a `phone` input.

---

## Build / fix procedure

1. **Find the ASA agent + its ids.**
   ```bash
   # BotDefinition dev name (voice setupReference form):
   sf data query --target-org <ORG> --json -q "SELECT Id, DeveloperName, MasterLabel FROM BotDefinition WHERE DeveloperName='<Agent>'"
   ```
   For the **messaging** `copilotId` raw string, the value is the agent's messaging routing-config Id (`0Xx…`). The reliable way to get the exact ids/labels is to **read an already-working inbound flow in the org** (retrieve it) — or copy them from the voice flow's `BotDefinition` and let Flow Builder resolve. If unsure, author voice with the `setupReference`/`BotDefinition` form (portable) and mirror it for messaging.

2. **Find a fallback queue (REQUIRED).**
   ```bash
   sf data query --target-org <ORG> --json -q "SELECT Id, DeveloperName, Name FROM Group WHERE Type='Queue'"
   ```
   Pick the voice queue for the voice flow, the messaging queue for the messaging flow. Put its `00G…` Id in `queueId` and its label in `queueLabel`. **Do not omit this.**

3. **Confirm the messaging ServiceChannel Id** (messaging flow only):
   ```bash
   sf data query --target-org <ORG> --json -q "SELECT Id, DeveloperName FROM ServiceChannel WHERE DeveloperName='sfdc_livemessage'"
   ```

4. **Copy the matching asset** into `flows/`, rename to your flow's API name, and swap the `<<...>>` tokens. Keep `routingType=Copilot`, `serviceChannelDevName`, and BOTH the copilot target and the fallback queue.

5. **Deploy Active:**
   ```bash
   sf project deploy start --metadata Flow:<YourFlowName> --target-org <ORG> --json
   ```

6. **Wire the flow to the channel (Setup, not metadata for the assignment itself).**
   - **Voice:** the SCV/Omni voice channel's **inbound flow** is set in Setup (the voice channel → flow assignment). This is the flow that runs when a call lands.
   - **Messaging:** the messaging channel (Embedded / MIAW / etc.) names its **routing/inbound flow** in the channel config. For metadata-managed channels the flow is referenced in the channel definition; otherwise set it in Setup.
   In practice on this stack, the inbound-flow assignment per channel is **Setup-side** — deploying the flow Active does not by itself bind it; point the channel at it.

7. **Verify:**
   ```bash
   sf data query --target-org <ORG> --json -q "SELECT ApiName, ProcessType, IsActive FROM FlowDefinitionView WHERE ApiName='<YourFlowName>'"
   ```
   `ProcessType=RoutingFlow`, `IsActive=true`. Then place a test call / start a test chat and confirm it lands on the ASA agent, and that `Contact__c` / `EndUserContactId` got linked.

---

## Gotchas

- **Fallback queue is mandatory for `routingType=Copilot`.** #1 mistake. The agent is the primary target; the queue is the required fallback. Keep both.
- **Voice vs. messaging express the agent differently.** Voice = `copilotId` as `setupReference`/`BotDefinition`; messaging = `copilotId` as a raw `0Xx…` string. Don't force one form onto the other channel unless you've confirmed the id resolves.
- **`serviceChannelId`**: voice uses a `setupReference` to `ServiceChannel` (`sfdc_phone`); messaging uses a raw `0N9…` channel Id string. Both alongside `serviceChannelDevName`.
- **Messaging needs `input_record` (MessagingSession SObject) input**, not just `recordId` — it reads `MessagingEndUserId` from it.
- **Contact link target differs**: `VoiceCall.Contact__c` (custom lookup) vs `MessagingEndUser.ContactId` (→ surfaces as `MessagingSession.EndUserContactId`).
- **No `triggerType` on Start** — an inbound RoutingFlow has a bare Start with just a connector, same as escalation flows.
- **`FlowDefinitionView` is a regular object** — query it WITHOUT `--use-tooling-api` (tooling API rejects it with `INVALID_TYPE`).

## Relationship to other skills

- **Escalation (agent → human queue):** `replicating-omnichannel-routing-flows` (`routingType=QueueBased`, `@utils.escalate`).
- **Phone→Contact matching detail:** `linking-individuals-by-phone-in-flows`.
- **Messaging EndUser→Contact link + channel wiring:** the `messaging-inbound-omniflow-pattern` memory.
