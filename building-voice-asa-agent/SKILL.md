---
name: building-voice-asa-agent
description: End-to-end playbook for building a voice Agentforce Service Agent (ASA) in a demo org — the full sequence from agent-user perm set, data seeding, system-context data flows, prompt template, agent bundle authoring, live-preview checkpoint, publish/activate, through inbound + per-channel escalation routing flows and the voice-channel Setup handoff. Ties together the system-context-flow, agent-user-perms, data-library, and escalation-flow skills into one ordered build.
---

# Building a Voice ASA Agent — End-to-End Playbook

## What this skill is for

This is the **spine** of a voice Agentforce Service Agent build. It orders the pieces and points to the deep-dive skills for each. Use it when the ask is "build a voice service agent that looks up a customer's records, opens/creates something, answers FAQs, and escalates to a human."

Proven pattern (BWAM_ASA_Sean → ClaimSecure_ASA): **hub-and-spoke router, hardcoded `DemoContactId`, verification gate, prompt-template-over-PromptFlow for reads, autolaunched flow for writes, `@utils.escalate`, per-channel escalation flows, inbound omni-flow that hands the call to the bot.**

## Companion skills (read these for the details)
- **`developing-agentforce`** — the authoritative agent lifecycle (generate bundle → write `.agent` → validate → preview → publish → activate). This playbook does NOT replace its Required Steps; it sequences the surrounding infra.
- **`building-system-context-agent-data-flows`** — the read/write/verify flows (all `SystemModeWithoutSharing`), and the PromptFlow empty-results bug + fix.
- **`scoping-agent-user-permissions`** — the agent-user perm set (object Read-only, VA/MA=0, full FLS).
- **`connecting-agent-data-library`** — the GeneralFAQ subagent + shared flex template for knowledge/citations.
- **`replicating-omnichannel-routing-flows`** — the escalation RoutingFlows (voice + messaging) and channel binding.
- **`calling-prompt-templates-in-flows`** — template↔flow wiring.
- **`handling-locked-standard-objects`** — if the demo object is a locked industry object (e.g. Claim).

## Standing user requirements (apply on every build here)
- **Prefix everything** with the demo name (agent, flows, template, perm set).
- **All agent-action / prompt-template flows run system context** (`SystemModeWithoutSharing`).
- **Agent user: no ViewAll/ModifyAll** on any object; object Read-only + full field FLS.
- **Every new field on all page layouts with FLS read+write for all profiles.**
- **Related-record access via the junction first** (e.g. Contact→Claim always through `ClaimParticipant`).
- Always `--json`; always `--target-org <the demo org>` (the global default is usually a different org).

## Build sequence

**0. Design + Agent Spec (HARD GATE).** Draft the Agent Spec (identity, variables incl. hardcoded `DemoContactId` + linked `VoiceCallId @VoiceCall.Id`, subagent graph, each action's target/inputs/outputs, verification factors, modality/connections). **Save it as a file and STOP for explicit user approval.** No `.agent`/flow code before approval.

**1. Agent-user perm set.** Build + deploy + assign per `scoping-agent-user-permissions`. Do this early so previews have access.

**2. Seed demo data.** Anonymous Apex creating the records the agent will read (and their junction rows — e.g. Claim + `ClaimParticipant` with `Roles`). Capture Ids. If the object is a locked standard object, pack structured detail into a long-text field (`handling-locked-standard-objects`).

**3. Read action.** Author + deploy the **system-context subflow** (privileged SOQL) + the **thin PromptFlow wrapper** + the **flex prompt template**, per `building-system-context-agent-data-flows`. Test the template resolves against the seeded persona. **This is where the empty-results bug shows — verify real rows come back.**

**4. Write + verify actions.** Author + deploy the autolaunched **create/update flow** and the **verify-identity flow** (both `SystemModeWithoutSharing`, Active). Smoke-test create returns a real record number; verify returns true for the correct factors, false otherwise.

**5. (Optional) FAQ / data library.** Add the GeneralFAQ subagent reusing a published flex template per `connecting-agent-data-library`.

**6. Author the agent bundle.**
```bash
sf agent generate authoring-bundle --json --no-spec --name "<Label>" --api-name <Api_Name> --target-org <org>
```
Write the `.agent` from the approved spec: `start_agent` router (model `sfdc_ai__DefaultEinsteinHyperClassifier`), verification subagent gating on `isVerified` with `currentTopic` round-trip, the records subagent owning read+write actions, GeneralFAQ, escalation (`@utils.escalate`), off_topic + ambiguous_question guardrail subagents (copy verbatim from the reference agent), `modality voice`, and the two `connection` blocks (see step 9).

**7. Validate → preview (CHECKPOINT).**
```bash
sf agent validate authoring-bundle --json --api-name <Api_Name> --target-org <org>   # zero errors
sf agent preview start --json --use-live-actions --authoring-bundle <Api_Name> --target-org <org>
sf agent preview send --json --authoring-bundle <Api_Name> --session-id <ID> -u "<utterance>" --target-org <org>
```
Exercise **every** capability: verify (correct + wrong factors), list records, detail on one, create a new one, FAQ, escalate. Read the traces to confirm routing + action I/O. **STOP for user approval before publishing.**

**8. Publish + activate.**
```bash
sf agent publish authoring-bundle --json --api-name <Api_Name> --target-org <org>
sf agent activate --json --api-name <Api_Name> --target-org <org>
sf agent preview start --json --api-name <Api_Name> --target-org <org>   # verify the published (not bundle) version
```

**9. Inbound + escalation routing flows.**
- **Inbound omni-flow** (`RoutingFlow`): `Get_VoiceCall(recordId)` → assign `FromPhoneNumber` → `findMatchingIndividuals`(searchFields=Phone, searchObject=Contact) → `Get_Contact`(Id In contactIds) → `Update_VC` (`Contact__c` + `RelatedRecordId` = Contact.Id) → `routeWork` **routingType=Copilot**, `copilotId` `setupReference=<Agent>/setupReferenceType=BotDefinition`, `queueId <voice queue>`, `serviceChannelDevName sfdc_phone`. Deploy Active.
- **Escalation flows are PER-CHANNEL** (see `replicating-omnichannel-routing-flows`):
  - `connection telephony.outbound_route_name = "flow://<Escalation_Voice>"` → updates `VoiceCall`, routes `sfdc_phone` → voice queue.
  - `connection messaging.outbound_route_name = "flow://<Escalation_Messaging>"` → updates `MessagingSession`, routes `sfdc_livemessage` → messaging queue.
  - **Do NOT point messaging at the voice flow** — messaging gets a `MessagingSession` recordId, not a `VoiceCall` Id; it must use the messaging flow or it fails at runtime. (This was a real, user-caught bug.)

**10. Setup handoff (voice binding is Setup-only).** Voice-channel inbound-flow + escalation-flow bindings (`SessionHandlerId`/`FallbackQueueId` on the voice channel) are **NOT API/metadata-settable** — hand the user exact Setup steps: Setup → the Service Cloud Voice channel → set inbound flow → `<Inbound_Omniflow>` and escalation flow → `<Escalation_Voice>`. Messaging escalation, by contrast, binds in the agent metadata (step 9) and takes effect on republish.

## Voice: making the agent SPEAK identifiers correctly (hard-won)

A voice agent reads any numeric string as a **quantity** — certificate number `33556` comes out "thirty-three thousand five hundred fifty-six," never "3-3-5-5-6." Formatting-only instructions ("read digit by digit") are unreliable; the model still quantifies. Two fixes, applied together:

**1. Emit a pre-spaced digit string from the backing flow, and read it verbatim.**
Have the verify/read flow return an extra **String output** that is the identifier with a space after every digit, built with nested `SUBSTITUTE` inside a `TRIM`:
```
TRIM(SUBSTITUTE(SUBSTITUTE( ... SUBSTITUTE(TRIM({!certificateNumber}),
"0","0 "),"1","1 ") ... "9","9 "))
```
(one `SUBSTITUTE` per digit 0–9). Add a corresponding `isOutput=true` String var (e.g. `certificateSpoken`), assign the formula to it in every success branch, and declare it as an action output in the `.agent`. Instruction to the agent: *"Read the `certificateSpoken` string back to the customer exactly as given — do not reformat or interpret it as a number."* The agent voices `"3 3 5 5 6"` as digits. This works for any digit-only identifier (cert #, claim #, member ID).

**2. Verify-then-speak ordering — NEVER recap a captured number before the action runs.**
The subtler bug: the agent recites the raw transcript number *before* verification, because the pre-verification recap ("Let me confirm — your certificate is 33556, verifying now…") voices the number before the flow's spaced output exists. Fix the verification subagent so that, on capturing DOB + identifier, it **calls the verify action immediately with no recap and no "I'm about to verify you"**, and speaks only *after* the action returns — leading with the success line (e.g. `"I've verified you successfully, {contact name}"`, name from the flow output) and reading the spaced string if it must read the number at all. Same principle for a submit/confirm step: **one** confirmation, then call create immediately — don't gate twice.

## Verification checklist
- Perm set assigned to the Einstein Agent User; object Read-only + full FLS; VA/MA=0.
- All action flows carry `<runInMode>SystemModeWithoutSharing</runInMode>` (the PromptFlow wrapper is the intentional exception).
- Read action returns real seeded rows in live preview (empty-results bug ruled out).
- Verify returns true/false correctly; create returns a real record number.
- Agent validates clean, previews correctly for every capability, publishes, activates; published-version preview works.
- Both RoutingFlows Active (`FlowDefinitionView ProcessType=RoutingFlow, IsActive=true`, standard API — not `--use-tooling-api`); inbound `copilotId` resolves to the agent; escalation `queueId` resolves to the right queue.
- Per-channel escalation confirmed: telephony→voice flow, messaging→messaging flow.

## Gotchas (the ones that actually cost time)
- **Empty read results** = SOQL is in the PromptFlow (user context), not the subflow. Move it. (`building-system-context-agent-data-flows`.)
- **Messaging escalation pointed at the voice flow** = runtime failure. Per-channel, always.
- **Voice binding isn't metadata** — it's a Setup handoff. Don't promise it via deploy.
- **`FlowDefinitionView` is standard API**, columns `ApiName`/`ProcessType`/`IsActive`. Querying it `--use-tooling-api` throws `INVALID_TYPE`.
- **Base a new agent version on the ACTIVE version** — retrieve the activated bundle before editing (see memory: always start from the active version).
- **Editing a Published prompt template's content requires bumping** `versionIdentifier` + `activeVersionIdentifier`, or the change won't take.
- **Voice agent voices identifiers as quantities** — fix in the flow (spaced-digit string output) + verbatim-readback instruction, not in prompt formatting alone. See the "Voice: making the agent SPEAK identifiers correctly" section.
- **Agent recites a number before verifying** = the verification subagent has a pre-verification recap. Remove it: capture → call verify immediately → speak only after the action returns.
- **`duplicate value found: <unknown>` on a Capability PromptFlow deploy** = two channel-resolution record lookups (VoiceCall + MessagingSession) each with `storeOutputAutomatically`, not `queriedFields`/`EndsWith`. Collapse to a single lookup (hardcode the contact, drop channel resolution) and it clears. (memory: `promptflow-queriedfields-duplicate`.)
