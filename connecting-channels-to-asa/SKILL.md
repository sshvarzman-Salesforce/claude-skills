---
name: connecting-channels-to-asa
description: "The connect-the-channels map for an Agentforce Service Agent (ASA): how a live VOICE call and an in-app/web MESSAGING chat get INTO the agent (inbound omni-flow → routeWork routingType=Copilot → BotDefinition) and how the agent hands a conversation OUT to a human — to a QUEUE, to a SKILL, or DIRECT to a specific rep — on @utils.escalate. Nails the two things people get wrong every time: (1) messaging escalation binds in the agent .agent metadata but VOICE binds only in Setup (never metadata); (2) messaging must use the messaging escalation flow, never the voice one. Points at the deep-dive skills that carry the full deployable XML. Use whenever wiring voice or messaging inbound/escalation to an ASA, choosing a routeWork target (queue vs skill vs direct rep), or debugging 'my agent doesn't pick up the call/chat' or 'escalation goes nowhere'."
metadata:
  version: "1.0"
  last_updated: "2026-08-13"
---

# Connecting Voice + Messaging Channels to an ASA (inbound + escalation)

## What this skill is for

An ASA needs wiring on **both ends of a conversation**, on **both channels**:

```
                 INBOUND (customer → agent)                    ESCALATION (agent → human)
VOICE     inbound omni-flow  → routeWork Copilot → agent   |   escalation flow → routeWork QueueBased/Skills → human
                  ⤷ bound in SETUP (voice channel)         |            ⤷ bound in SETUP (voice channel)
MESSAGING inbound omni-flow  → routeWork Copilot → agent   |   escalation flow → routeWork QueueBased/Skills → human
                  ⤷ bound on the MessagingChannel metadata |            ⤷ bound in the AGENT .agent metadata
```

That's **four flows and two very different binding stories**. This skill is the map — it tells you which flow you need, which target to route to, and *where the binding lives* (metadata vs. Setup). The full deployable XML lives in the deep-dive skills; this skill keeps you from wiring the wrong thing to the wrong place.

## The deep-dive skills (this skill routes you to them)
- **`routing-inbound-messaging-to-agentforce-agent`** — INBOUND messaging: the RoutingFlow (resolve Contact from pre-chat phone → link `MessagingEndUser.ContactId` → `routeWork` Copilot), the `EmbeddedMessaging` channel with the custom pre-chat param, and the Setup-only Embedded Service deployment. Full XML in its `assets/`.
- **`replicating-omnichannel-routing-flows`** — ESCALATION (both channels): the `routeWork` `QueueBased` flows that hand a live conversation to a human queue, with complete voice + messaging XML templates in `assets/` and the queue-Id-is-org-specific porting procedure.
- **`building-voice-asa-agent`** — the ASA build spine; its step 9 sketches the inbound voice omni-flow and the per-channel escalation binding, and step 10 is the voice Setup handoff.

## The four flows at a glance

| Flow | ProcessType | Reads/links | `routeWork` target | Where it binds |
|---|---|---|---|---|
| **Voice inbound** | `RoutingFlow` | `VoiceCall.FromPhoneNumber` → `findMatchingIndividuals(Phone, Contact)` → set `VoiceCall.Contact__c` + `RelatedRecordId` | `routingType=Copilot`, `copilotId`→`BotDefinition`, `serviceChannelDevName=sfdc_phone` | **Setup** (voice channel inbound flow) |
| **Messaging inbound** | `RoutingFlow` | pre-chat `CustomerPhone` → `findMatchingIndividuals` → set **`MessagingEndUser.ContactId`** (parent) | `routingType=Copilot`, `copilotId`→`BotDefinition`, `serviceChannelDevName=sfdc_livemessage` | **`MessagingChannel.sessionHandlerFlow`** (metadata) |
| **Voice escalation** | `RoutingFlow` | update `VoiceCall.Escalated_to_Human__c=true` (+ KPI stamps) | `routingType=QueueBased`/skills, `serviceChannelDevName=sfdc_phone` | **Setup** (voice channel escalation flow) |
| **Messaging escalation** | `RoutingFlow` | update `MessagingSession.Escalated_to_Human__c=true` (+ KPI stamps) | `routingType=QueueBased`/skills, `serviceChannelDevName=sfdc_livemessage` | **Agent `.agent`** `connection` block (metadata) |

Every one is a `ProcessType=RoutingFlow` with an `isInput` `recordId` variable and a bare `start` (connector only, **no** `triggerType`). RoutingFlows **reject** `<runInMode>` — they already run system context; adding the tag fails the deploy.

---

## INBOUND: getting the call/chat to the agent

Both inbound flows do the same three things — read the conversation record, resolve the caller's Contact and link it, then `routeWork` to the agent — and differ only in *how the caller's phone arrives* and *which record holds the Contact link*.

`routeWork` for inbound-to-agent:

| Param | Value |
|---|---|
| `recordId` | `elementReference` → `recordId` (the VoiceCall / MessagingSession) |
| `routingType` | **`Copilot`** (not QueueBased — that's escalation) |
| `serviceChannelDevName` + `serviceChannelId` | `sfdc_phone` (voice) / `sfdc_livemessage` (messaging) |
| `copilotId` | `setupReference` = `<Agent_Api_Name>`, `setupReferenceType` = **`BotDefinition`** |
| `queueId` | a real `Group.Id` — the **fallback** queue if the agent can't take it |

Resolve the agent: `sf data query --json -q "SELECT Id, DeveloperName FROM BotDefinition WHERE DeveloperName='<Agent_Api_Name>'"` (BotDefinition is queryable).

- **Messaging inbound** — see `routing-inbound-messaging-to-agentforce-agent` for the full flow + channel + deployment. Link the Contact on **`MessagingEndUser.ContactId`** (the session's `EndUserContactId` fills in automatically; there is no `Contact__c` on MessagingSession). The channel's `sessionHandlerFlow` = this flow — that binding is **pure metadata**.
- **Voice inbound** — same shape but reads `VoiceCall.FromPhoneNumber` and writes `VoiceCall.Contact__c` + `RelatedRecordId = Contact.Id`. See `building-voice-asa-agent` step 9. The flow deploys by metadata, but **which flow the voice channel calls is a Setup binding** (below).

---

## ESCALATION: handing the conversation to a human — queue, skill, or direct rep

On `@utils.escalate` the agent invokes the channel's escalation flow. The flow flips `Escalated_to_Human__c` (and, if you're tracking KPIs, stamps `Entered_Queue_Timestamp__c` — see `building-contact-center-kpis-agentwork`) and then `routeWork`s to a human. **Three destinations**, chosen by the `routeWork` params:

### A) To a QUEUE (`routingType=QueueBased`)
The default and simplest. Route to an Omni queue's `Group.Id`.
```
routingType   = QueueBased
queueId       = <Group.Id of the queue>     (org-specific — look up by DeveloperName)
queueLabel    = <display label>
serviceChannelDevName = sfdc_phone | sfdc_livemessage
```
Full XML: `replicating-omnichannel-routing-flows` (`assets/escalation-routingflow-voice.flow-meta.xml`, `...-messaging.flow-meta.xml`).

### B) To a SKILL (skills-based routing)
Route on required skills instead of a fixed queue — Omni matches an available agent who has them.
```
routingType   = SkillsBased
serviceChannelDevName = sfdc_phone | sfdc_livemessage
skillRequirementsResourceItem = <a collection of skill-requirement rvars>
```
Build the skill-requirement collection by looping the target `Skill` Ids into `routeWork`'s skills input (the pattern in `calling-prompt-templates-in-flows` / the NewRez skills-routing flow: `Get_Skill` → build requirement rvar → `Add` to the collection → `routeWork` with `skillRequirementsResourceItem`). Use this when "who can take it" depends on capability (language, product, tier), not a static queue.

### C) DIRECT to a specific rep (agent-based routing)
Route straight to one named user (e.g. a relationship manager, a named specialist).
```
routingType   = AgentBased        (route to a specific Omni-Channel-enabled user)
userId / agentId = <the User Id>  (as a routeWork input)
serviceChannelDevName = sfdc_phone | sfdc_livemessage
fallback queueId  = <Group.Id>    (still supply a fallback in case the rep is unavailable)
```
Direct-to-rep is the most brittle — the rep must be present and Omni-available — so **always** include a fallback queue. Prefer skills-based (B) over hardcoding a user unless the demo specifically needs "always goes to *this* person."

> Whatever the target, the escalation flow's `recordUpdate` object MUST match the channel: `VoiceCall` for the voice flow, `MessagingSession` for the messaging flow. A messaging escalation gets a `MessagingSession` recordId — pointing it at the voice flow (which filters/updates `VoiceCall`) fails at runtime. **One escalation flow per channel, always.**

---

## THE BINDING — the part everyone gets wrong

Deploying a RoutingFlow Active does **nothing** until the channel is told to use it. And the two channels bind completely differently:

### Messaging — binds in metadata ✅ (Claude can do it end to end)
- **Inbound:** set `MessagingChannel.sessionHandlerFlow = <inbound flow>` (+ `sessionHandlerQueue` fallback). Deploy the channel.
- **Escalation:** set it in the **agent `.agent`** `connection` block and re-publish + re-activate the agent:
  ```
  connection customer_web_client:
      outbound_route_name: "flow://<Messaging_Escalation_Flow>"
      outbound_route_type: "OmniChannelFlow"
      escalation_message: "Please hold while I transfer you to a representative."
  ```

### Voice — binds in Setup 🧑 (NOT metadata-settable — hand the user a runbook)
Both the voice **inbound** flow and the voice **escalation** flow are bound at the Service Cloud Voice channel in **Setup** — `SessionHandlerId` / `FallbackQueueId` and the flow assignments are **not** API/metadata-writable. Do not promise a "deploy" for these; deliver a runbook:
> Setup → the Service Cloud Voice channel → set **inbound flow** → `<Voice_Inbound_Omniflow>` and **escalation flow** → `<Voice_Escalation_Flow>`.

⚠️ The voice `.agent` `connection telephony.outbound_route_name` often points at the **inbound** omni-flow (the flow that brings the call to the agent), *not* the voice escalation flow. **Do not overwrite it** to "add" voice escalation — that breaks inbound voice. Voice escalation lives in Setup; leave telephony alone.

| | Inbound bind | Escalation bind |
|---|---|---|
| **Messaging** | `MessagingChannel.sessionHandlerFlow` (metadata) | agent `.agent` `connection … outbound_route_name` (metadata) |
| **Voice** | Setup (voice channel inbound flow) | Setup (voice channel escalation flow) |

---

## Build order (per channel)
1. Confirm the field the escalation flow sets (`Escalated_to_Human__c`, plus any KPI fields) exists + FLS-editable on the conversation object — create first if missing, or the flow's `recordUpdate` won't deploy.
2. Author + deploy the inbound RoutingFlow and the escalation RoutingFlow (Active) — voice and/or messaging, from the deep-dive skills' assets. Swap the org-specific `queueId`s.
3. Bind: messaging inbound → channel metadata; messaging escalation → agent metadata (re-publish/activate); voice inbound + escalation → Setup runbook to the user.
4. Verify each flow Active (`FlowDefinitionView ProcessType=RoutingFlow, IsActive=true`, standard API — **not** `--use-tooling-api`), `copilotId` resolves to the agent, escalation `queueId`/skills/userId resolve.

## Verification checklist
- Four flows (or the two for your single channel) deployed **Active**, `ProcessType=RoutingFlow`, no `runInMode` tag, `recordId` `isInput`.
- Inbound: `routingType=Copilot`, `copilotId`→`BotDefinition`; contact linked on the right record (`VoiceCall.Contact__c` / `MessagingEndUser.ContactId`).
- Escalation: `routingType` matches the chosen target (QueueBased / SkillsBased / AgentBased); target resolves in-org; `recordUpdate` object matches the channel; fallback queue present for skills/direct-rep.
- Bindings: messaging inbound on the channel, messaging escalation in the agent metadata (re-published); voice both in Setup; telephony `outbound_route_name` left untouched.
- Per-channel confirmed end to end: a voice call reaches the agent and escalates to a human on voice; a chat reaches the agent and escalates on messaging — **never cross-wired**.

## Gotchas (hard-won)
- **Messaging escalation pointed at the voice flow = runtime failure.** Messaging gets a `MessagingSession` Id; the voice flow filters `VoiceCall`. One flow per channel.
- **Voice binding is Setup-only.** It is not metadata. Don't promise a deploy; hand the user the Setup runbook.
- **Don't overwrite telephony `outbound_route_name`** — it's usually the inbound flow. Voice escalation is a separate Setup binding.
- **Queue Ids are per-org.** A copied escalation flow validates + deploys with a stale `queueId` and then silently routes nowhere. Look the queue up by `DeveloperName` and swap the Id. (`replicating-omnichannel-routing-flows`.)
- **`routingType=Copilot` is inbound; `QueueBased`/`SkillsBased`/`AgentBased` is escalation.** Mixing them is the usual "agent won't pick up" / "escalation goes nowhere" cause.
- **`FlowDefinitionView` is standard API** (`ApiName`/`ProcessType`/`IsActive`). Querying it `--use-tooling-api` throws `INVALID_TYPE`.
- **Direct-to-rep needs a fallback queue** — a specific user is often Omni-unavailable; without a fallback the escalation dead-ends.
