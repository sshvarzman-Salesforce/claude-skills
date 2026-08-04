---
name: routing-inbound-messaging-to-agentforce-agent
description: "Stand up INBOUND In-App/Web Messaging routing to an Agentforce (ASA) agent end to end — the RoutingFlow that receives a new MessagingSession, resolves the caller's Contact from a pre-chat phone number, links it to the conversation, and hands the session to a Copilot/BotDefinition agent — plus the EmbeddedMessaging MessagingChannel that invokes the flow (with a custom pre-chat phone parameter) and the EmbeddedServiceConfig deployment that surfaces the widget. Complements `replicating-omnichannel-routing-flows` (which covers OUTBOUND escalation routeWork to a human queue). Includes complete, verified, deployable XML for all three artifacts as ready-to-edit templates in assets/. Use whenever you need to route an inbound web/in-app chat to an Agentforce agent, build a messaging inbound omni-flow, wire a MessagingChannel to a session-handler flow, add a custom pre-chat parameter, or create an Embedded Service deployment. Trigger on: \"route inbound messaging to my agent\", \"build a messaging inbound omni-flow\", \"in-app/web chat to Agentforce\", \"MIAW routing flow to a bot\", \"add a pre-chat phone field mapped to a flow input\", \"create an embedded service deployment\", \"link a contact to a messaging session\", \"MessagingEndUser contact\"."
compatibility: "Salesforce CLI (sf) v2+; Enhanced Messaging (In-App & Web / MIAW) + Omni-Channel; Agentforce 2.0 / ASA agent published & active; inbound routing flows are ProcessType=RoutingFlow"
metadata:
  version: "1.0"
  last_updated: "2026-08-04"
---

# Routing Inbound Messaging to an Agentforce Agent

## What this skill is for

When a customer opens an **In-App or Web messaging** widget and starts a chat, Salesforce creates a `MessagingSession` and invokes the channel's **session-handler flow** to decide where the conversation goes. This skill builds the whole inbound path so a new chat lands on an **Agentforce (ASA) agent**:

```
Customer opens web/in-app chat  (fills pre-chat form: Phone, First, Last)
   → MessagingChannel (EmbeddedMessaging)  invokes its sessionHandlerFlow
      → RoutingFlow  (recordId = MessagingSession Id, CustomerPhone = pre-chat phone)
           Get MessagingSession → findMatchingIndividuals(phone) → Get Contact
           → Update MessagingEndUser.ContactId  (links the caller)
           → routeWork(routingType=Copilot → BotDefinition)   ← hands to the agent
   → EmbeddedServiceConfig  (the deployment/snippet the site embeds)
```

Three deployable artifacts, one Setup step:

| # | Artifact | Metadata type | Deployable? |
|---|---|---|---|
| 1 | Inbound routing flow | `Flow` (`ProcessType=RoutingFlow`) | ✅ full |
| 2 | Messaging channel (+ custom pre-chat param) | `MessagingChannel` | ✅ full |
| 3 | Embedded Service deployment | `EmbeddedServiceConfig` | ⚠️ needs a Setup-provisioned site first (see §4) |

**This is the INBOUND counterpart to `replicating-omnichannel-routing-flows`.** That skill routes a live conversation OUT to a human queue on `@utils.escalate` (routingType=`QueueBased`). This skill routes an inbound chat IN to a bot (routingType=`Copilot`). Same `routeWork` action, different target.

Ready-to-edit templates ship in `assets/`:
- `inbound-messaging-routingflow.flow-meta.xml`
- `embedded-messaging-channel.messagingChannel-meta.xml`
- `embedded-service-config.EmbeddedServiceConfig-meta.xml`

Use `sf` with `--json` on every command; confirm/set the target org first (see the `switching-org` skill).

---

## 1. The inbound RoutingFlow

A `ProcessType=RoutingFlow`. Structure — five elements, no decisions:

1. **Variables** — `recordId` (String, `isInput=true`) = the **MessagingSession** Id Omni passes in; `CustomerPhone` (String, `isInput=true`) = the pre-chat phone value the channel maps in.
2. **Get_MessagingSession** — `recordLookup` on `MessagingSession`, filter `Id = {!recordId}`, `getFirstRecordOnly`, `storeOutputAutomatically`. Needed to read `MessagingEndUserId`.
3. **Lookup_Contact** — `findMatchingIndividuals` action: `searchTerm = {!CustomerPhone}` (elementReference), `searchFields = Phone`, `searchObject = Contact`, `storeOutputAutomatically`.
4. **Get_Contact** — `recordLookup` on `Contact`, filter `Id In {!Lookup_Contact.contactIds}`, `getFirstRecordOnly`.
5. **Update_MessagingEndUser** — `recordUpdate` on **`MessagingEndUser`**, filter `Id = {!Get_MessagingSession.MessagingEndUserId}`, inputAssignment **`ContactId = {!Get_Contact.Id}`**.
6. **Route_to_Agent** — `routeWork` (see §3).

### CRITICAL — contact linkage goes on the PARENT

Link the Contact to the **`MessagingEndUser`** (the parent of the session), setting its standard **`ContactId`** lookup. `MessagingSession.EndUserContactId` then **populates automatically** from the parent — do **NOT** write `EndUserContactId` on the session directly, and there is **no `Contact__c`** custom field on MessagingSession. Find the parent via `MessagingSession.MessagingEndUserId`.

*(This is the fork from the voice inbound flow, which reads `VoiceCall.FromPhoneNumber` and writes `VoiceCall.Contact__c` / `RelatedRecordId`. Messaging has no phone field on the record — phone arrives as a pre-chat input — and links via the parent.)*

### CRITICAL — RoutingFlows reject `runInMode`

Do **NOT** add `<runInMode>SystemModeWithoutSharing</runInMode>`. A RoutingFlow already runs in system context by design; the tag triggers the deploy error:

> *"Because the &lt;flow&gt; flow is of type RoutingFlow, it can't be configured to always run in system context."*

Omit it. (This is the one exception to a blanket "all agent/action flows run system context" standing rule — it's satisfied automatically here.)

Deploy: `sf project deploy start --metadata Flow:<FlowName> --json`. It deploys **Active** because `<status>Active</status>` is in the XML.

---

## 2. The EmbeddedMessaging channel + custom pre-chat phone parameter

A `MessagingChannel` with `messagingChannelType=EmbeddedMessaging`. The three fields that wire it to the flow:

```xml
<sessionHandlerType>Flow</sessionHandlerType>
<sessionHandlerFlow>ClaimSecure_Inbound_Omniflow_to_ASA_Messaging</sessionHandlerFlow>  <!-- your §1 flow -->
<sessionHandlerQueue>SDO_Service_Messaging</sessionHandlerQueue>                          <!-- fallback queue -->
```

`sessionHandlerFlow` is the link channel → flow. `sessionHandlerQueue` is the fallback the platform uses if the flow doesn't route (Omni still wants a queue named here).

### Custom pre-chat phone parameter (deploys as metadata — no Setup handoff)

Add a `<customParameters>` block. Its `actionParameterName` binds the pre-chat phone value into the flow's `CustomerPhone` **input variable** at session start:

```xml
<customParameters>
    <actionParameterMappings>
        <actionParameterName>CustomerPhone</actionParameterName>  <!-- = the flow input var name -->
    </actionParameterMappings>
    <externalParameterName>Phone</externalParameterName>          <!-- pre-chat field key -->
    <masterLabel>Phone Number</masterLabel>
    <maxLength>18</maxLength>
    <name>CustomerPhone</name>
    <parameterDataType>String</parameterDataType>
</customParameters>
```

The channel also carries opt-out/help `messagingKeywords`, `automatedResponses`, and an `<embeddedConfig>` block (auth mode, allowed file types, EWT) — copy those from an existing EmbeddedMessaging channel in the org (e.g. `Messaging_for_In_App_Web` / `BWAM_Messaging_Channel`). See the asset for the full, deployable shape.

Deploy: `sf project deploy start --metadata MessagingChannel:<ChannelName> --json`.

---

## 3. The `routeWork` action — routing to a Copilot/agent (not a queue)

Inbound-to-agent uses `routingType=Copilot` and points `copilotId` at the agent's **`BotDefinition`**:

| Param | Value | Notes |
|---|---|---|
| `recordId` | `elementReference` → `recordId` | the MessagingSession |
| `routingType` | `Copilot` | **not** `QueueBased` (that's escalation) |
| `serviceChannelDevName` | `sfdc_livemessage` | messaging channel; `stringValue` |
| `serviceChannelId` | `setupReference` = `sfdc_livemessage`, `setupReferenceType` = `ServiceChannel` | both this + devName set |
| `serviceChannelLabel` | `Messaging` | display |
| `copilotId` | `setupReference` = `<Agent_Api_Name>`, `setupReferenceType` = `BotDefinition` | the agent |
| `copilotLabel` | e.g. `ClaimSecure ASA` | display |
| `queueId` | messaging queue `Group.Id` (`00G…`) | fallback; org-specific |
| `queueLabel` | `Messaging` | display |
| `versionString` | `2.0.0` | required on the routeWork action |

Look the agent up: `sf data query --json -q "SELECT Id, DeveloperName FROM BotDefinition WHERE DeveloperName='<Agent_Api_Name>'"` (BotDefinition **is** queryable). Look the queue up by DeveloperName: `SELECT Id, DeveloperName FROM Group WHERE Type='Queue'`.

---

## 4. The Embedded Service deployment (`EmbeddedServiceConfig`) — Setup-gated

The deployment is what a website embeds. Its XML (`deploymentFeature=EmbeddedMessaging`, `deploymentType=Web`, a pre-chat `embeddedServiceForms`, an `embeddedServiceMessagingChannel` → your channel, a `branding` set, a `site`) is authorable — the asset template has the full shape. **But it will NOT deploy standalone.** A validate-only dry-run fails with:

> *"This field requires the site type ChatterNetworkPicasso."*

Every deployment needs its **own dedicated `ChatterNetworkPicasso` site** (the widget host) plus a branding set, and **both are auto-provisioned only by Setup's "New Deployment" wizard** — they are not creatable by a metadata push, and you cannot reuse another deployment's site (bound 1:1). Each deployment owns a *pair* of `ESW_<channel>_<timestamp>` sites — one `ChatterNetwork` and one `ChatterNetworkPicasso` (the `<site>` value is the Picasso one, usually suffixed `1`).

**Runbook:**
1. Setup → Feature Settings → Service → Embedded Service → **Embedded Service Deployments → New Deployment**.
2. Choose **Messaging for In-App and Web**; select the **existing** `MessagingChannel` you deployed in §2 (do not create a new channel).
3. Finish. That mints the `ESW_<channel>_<ts>` site pair + the branding set.
4. *(Optional, for version control)* find the new Picasso site — `SELECT Name, SiteType FROM Site WHERE Name LIKE 'ESW%'` — set `<site>` in the asset XML to the `...1` (ChatterNetworkPicasso) name and the `<branding>` to the minted set, then `sf project deploy start --metadata EmbeddedServiceConfig:<Name> --json` deploys cleanly to keep the form/branding reproducible.

The pre-chat form field for phone uses `messagingChannelParameterType=Custom`, `formField=Phone`, `formFieldType=Phone` — this is what surfaces the §2 custom parameter in the widget's pre-chat UI.

---

## Build sequence

1. **Flow** — author from `assets/inbound-messaging-routingflow.flow-meta.xml`; set the agent API name, service channel (`sfdc_livemessage`), and messaging queue Id. Deploy `Flow:<name>`; confirm Active (`sf project retrieve start --metadata Flow:<name>` then grep `<status>Active</status>` — `FlowDefinitionView` is not queryable via this CLI).
2. **Channel** — author from `assets/embedded-messaging-channel.messagingChannel-meta.xml`; set `sessionHandlerFlow` = the flow, `sessionHandlerQueue`, and the custom phone `<customParameters>`. Dry-run, then deploy `MessagingChannel:<name>`.
3. **Deployment** — run the Setup wizard (§4), selecting the deployed channel. Optionally finalize the `EmbeddedServiceConfig` XML with the minted site/branding and deploy for version control.

## Verification checklist

- Flow deployed **Active**, `ProcessType=RoutingFlow`, **no** `runInMode` tag; `CustomerPhone` + `recordId` both `isInput=true`.
- Flow updates **`MessagingEndUser.ContactId`** (parent), filter on `Get_MessagingSession.MessagingEndUserId`; does **not** touch `MessagingSession.EndUserContactId`.
- `routeWork`: `routingType=Copilot`, `serviceChannelDevName=sfdc_livemessage`, `copilotId` → the agent's `BotDefinition`, `queueId` resolves to a real messaging `Group`.
- Channel deployed; `sessionHandlerFlow` = the flow; custom `CustomerPhone` param `actionParameterName` matches the flow input var name exactly.
- Deployment: ESW site pair + branding minted by the wizard; `<site>` (if version-controlled) points at the `ChatterNetworkPicasso` site.

## Gotchas (hard-won)

- **Link the parent, not the session.** Set `MessagingEndUser.ContactId`; `EndUserContactId` on the session fills in automatically. MessagingSession has no `Contact__c`.
- **RoutingFlows reject `runInMode`.** Omit the system-context tag — they already run system context. Adding it fails the deploy.
- **`routingType=Copilot` for inbound-to-agent**, `QueueBased` for escalation-to-human. `copilotId` is a `setupReference` to `BotDefinition`.
- **The custom pre-chat param deploys as metadata** — the `<customParameters>` block on the channel is enough; no Setup step for the parameter itself. `actionParameterName` MUST equal the flow's input variable name.
- **`EmbeddedServiceConfig` needs a Setup-minted `ChatterNetworkPicasso` site + branding set** — it cannot be created purely by metadata. Run the New Deployment wizard first; only then can the XML deploy (for version control).
- **Query gotchas:** `BotDefinition` is queryable; `FlowDefinitionView`, `EmbeddedServiceConfig`, `MessagingChannel.ChannelType` are **not** (`INVALID_TYPE`). Enumerate configs with `sf org list metadata --metadata-type EmbeddedServiceConfig`; read flow status via `sf project retrieve start` + grep.
