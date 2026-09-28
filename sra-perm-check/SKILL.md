---
name: sra-perm-check
description: >-
  Validate AND provision a Salesforce org's Service Rep Assistant (SRA) / Service Assistant permissions against the official Salesforce Help permission requirements — per persona (Service Assistant Admin, Service Rep, ServicePlanner/agent runtime user) and per channel (Case, Messaging, Voice). CHECK mode maps each doc-required permission to its exact API name, identifies the rep and agent-runtime users automatically, queries the org, and emits a pass/fail scorecard with the sneaky gotchas flagged. SETUP mode provisions the perms for an SE: asks for the admin/human user, the planner (agent runtime) user, and the channels to demo, then assigns the standard SRA perm sets and creates + assigns the custom access perm sets on the correct identities (dry-run/validate by default, --apply to write, auto-verifies). Use when someone asks "did I set up SRA permissions correctly", "set up / provision SRA perms for me", "why is the agent panel erroring / not firing", "check my SRA/Voice/Messaging perms", or "we should perm-check this org".
tools: [Bash, Read, Write, Edit]
---

# SRA Permission Checker

> Doc-anchored permission validator for Service Rep Assistant / Service Assistant.
> Answers one question definitively: **"Are the permissions the official docs require
> actually assigned, on the correct users?"** — before you go chasing config or platform bugs.

This skill exists because "it's a perms issue" sends FDEs down a rabbit hole of adding
permissions that are *already there* or adding them to the *wrong user*. The single most
common real gaps are subtle: a permission on the **rep** that belongs on the **agent runtime
user**, the "**View All** Voice and Video Calls" vs "View Voice and Video Calls" trap, and
**eligibility-flow direct access** (which the `Run Flows` permission does NOT satisfy).

## When to trigger

- "Check my SRA permissions" / "did I set up the perms right?"
- "Agent panel errors when I type" / "We couldn't send your request. Try again." / "SRA not firing"
- "Validate this org against the SRA permission docs"
- Setting up SRA on a new customer/trial/SDO org by hand (no Qbrix) and want a pre-flight
- Someone says "we should perm-check this" or "is there a perm checker"
- **"Set up / provision the SRA perms for me"** / "do the perm setup" / "assign the SRA perm
  sets" → **SETUP mode** (see below): ask for admin user, planner user, and channels, then
  provision. Defaults to dry-run; requires `--apply` to write.

**Not this skill:** broad activation/knowledge/action failures → `sra-setup-debug`. Session
behavior/trace → `sra-agent-debugger`. Voice narrative/telephony → `agentforce-voice-expert`.

## If the user hasn't given enough to proceed

> Which org should I permission-check?
>
> I need:
> - **Org alias** — the `sf` CLI alias (e.g. `mySDO`, `KatsSDO`)
>
> Optionally:
> - **Channel** — `case`, `messaging`, `voice`, or `all` (default: all)
>
> I'll identify the rep + agent-runtime users and produce a pass/fail scorecard against the
> official Salesforce permission docs.

## Quick start

```bash
python3 "$HOME/.claude/skills/sra-perm-check/scripts/check_perms.py" --org <alias> --channel all
```

Flags:
- `--org` (required): sf CLI alias, authenticated (`sf org login web --alias <alias>`)
- `--channel` (optional): `case` | `messaging` | `voice` | `all` (default `all`)
- `--rep-user` (optional): a specific rep User Id to check (default: all `ServicePlannerUser` assignees)
- `--json` (optional): emit raw JSON instead of the scorecard table

The script is read-only. It never modifies the org.

## Setup mode (provisioning) — `setup_perms.py`

The WRITE counterpart to the checker. Assigns the standard SRA perm sets and creates +
assigns the custom access perm sets **on the correct identities, per channel**. It is the
same permission model as the checker, applied.

### Ask the SE these three things first (print verbatim if not provided)

> I'll provision the SRA permissions for you. I need three things:
>
> 1. **Admin / human user** — the user you'll *demo* with (the human who opens the record and
>    types in the panel). Id, username, or full Name. (Can be several, comma-separated.)
> 2. **Planner (agent runtime) user** — the Einstein Agent user SRA runs as. Id/username/Name.
>    *(Optional — I'll auto-detect the `ServicePlannerAgentUser` assignee if you skip it.)*
> 3. **Channels to demo** — `case`, `messaging`, `voice` (any combination), or `all`.
>
> I'll run a **dry-run first** (validates the perm-set metadata against your org, writes
> nothing), show you the plan, then you re-run with `--apply` to provision.

### Run it

```bash
# 1) preview — writes nothing, but VALIDATES perm-set metadata via a check-only deploy:
python3 "$HOME/.claude/skills/sra-perm-check/scripts/setup_perms.py" \
    --org <alias> --admin-user <id|username|Name> --channels voice

# 2) provision for real (then it auto-verifies with check_perms.py):
python3 "$HOME/.claude/skills/sra-perm-check/scripts/setup_perms.py" \
    --org <alias> --admin-user <id|username|Name> --channels voice,messaging --apply
```

Flags: `--org` (req), `--admin-user` (req, comma-sep), `--planner-user` (optional; auto-detect
if omitted), `--channels` (`case|messaging|voice|all`), `--prefix` (custom perm set name prefix,
default `SRA_`), `--apply` (write; **default is dry-run**), `--api-version` (default 62.0).

### What it provisions

| Persona | Perm set | Grants |
|---|---|---|
| human/admin | `ServicePlannerUser` (assign) | Service Planner User |
| human/admin | `CopilotSalesforceUser` (assign) | Access Agentforce Default Agent |
| planner | `ServicePlannerAgentUser` (assign) | Service Planner Agent User |
| planner | `Data Cloud User` (assign, by label) | Data Cloud User (manual-assign req) |
| planner | `<prefix>Agent_Voice_Access` (create) | `CanAccessCE` + `ViewAllCalls` |
| human/admin | `<prefix>Voice_Eligibility_Flow_Access` (create) | direct FlowDefinition access to the Voice eligibility flow |
| planner | `<prefix>Agent_Messaging_Access` (create) | `CanAccessCE` + MessagingSession Read (+ MessagingEndUser Read) + View All Fields |
| human/admin | `<prefix>Messaging_Eligibility_Flow_Access` (create) | direct FlowDefinition access to the Messaging eligibility flow |

### Safety model (state this to the user)

- **Dry-run by default.** No writes. It still runs a **check-only metadata deploy** so perm-set
  errors surface *before* you commit. Only `--apply` writes.
- **Idempotent.** Existing assignments are detected and skipped. **Never deletes** anything.
- **Auto-verify.** After `--apply` it runs `check_perms.py` per channel and prints the scorecard.
- **Not sufficient alone for Voice.** Perms ≠ working SRA. After provisioning, confirm a
  **default agent is set on the Voice tab** of Service Assistant Setup (mandatory since 262;
  its absence throws "We couldn't send your request. Try again."). The script prints this reminder.

## The two users you MUST distinguish

SRA runs across **two** identities. Getting a permission onto the wrong one is the #1 cause
of "I added everything and it still fails."

| User | How to identify | What runs as it |
|---|---|---|
| **Service Rep** (human) | Assigned `ServicePlannerUser` perm set | Opens the record page, types in the panel, sees plans |
| **ServicePlanner / agent runtime user** (Einstein Agent license) | Assigned `ServicePlannerAgentUser` perm set; username usually `agentforce_service_assistant@…ext` | Monitors the conversation, generates plans, executes actions |

Always resolve BOTH by permission set, never by name.

## Official permission requirements (source of truth)

Anchored to these Salesforce Help articles (re-fetch to confirm currency — they're a JS SPA,
so render in a browser; a plain fetch returns a "CSS Error"):

| Doc | URL id |
|---|---|
| Mandatory Permissions for Service Assistant | `service.sp_permissions_mandatory.htm` |
| Service Assistant for Case | `service.sp_permissions_case.htm` |
| Service Assistant for Messaging | `service.sp_permissions_messaging.htm` |
| Service Assistant for Voice | `service.sp_permissions_voice.htm` |

### Base — Mandatory (ALL channels)

| Persona | Required (verbatim from doc) | API name / match |
|---|---|---|
| Service Assistant Admin | `Service Planner Builder` perm set | PS `ServicePlannerBuilder` |
| **Service Rep** | `Service Planner User` perm set | PS `ServicePlannerUser` |
| **Service Rep** | `Access Agentforce Default Agent` perm set | PS `CopilotSalesforceUser` |
| Agent runtime user | `Service Planner Agent User` | PS `ServicePlannerAgentUser` |
| Agent runtime user | `Agentforce_Service_Assistant Permissions` (auto-assigned; don't remove) | PS name starts with `Agentforce_Service_Assistant` |
| Agent runtime user | `Data Cloud User` perm set (**must be manually assigned**) | PS label = `Data Cloud User` |

### Voice (additive)

**Voice Call Access (Required)** — on the **agent runtime user**, via a custom perm set
(doc's recommended name: *Agent Voice Access*):

| Requirement (doc) | API name | Field |
|---|---|---|
| Access Conversation Entries | `PermissionsCanAccessCE` | app perm |
| **View All Voice and Video Calls** | `PermissionsViewAllCalls` | app perm |

> ⚠️ Trap: reps often grant "View Voice and Video Calls" — the doc requires the **"View ALL"**
> variant (`PermissionsViewAllCalls`), and it goes on the **agent user**, not the rep.

**Eligibility Flow Access (Required)** — the rep + admin need **direct access to the Voice
Call eligibility flow**. `Run Flows` does **NOT** satisfy this. ✅ This IS SOQL-queryable —
`SetupEntityAccess` with **`SetupEntityType = 'FlowDefinition'`** and `SetupEntityId` = the
flow's `FlowDefinitionView.DurableId` (a `300…` id), joined to the rep's assigned perm sets.
(Fix: restrict the flow's default access + custom perm set "Voice Call Eligibility Flow
Access" assigned to rep & admin; or assign the flow to their profile. Note: the perm set
need not be named that — any assigned perm set that grants the flow counts.)

**Native telephony (Agentforce Contact Center) — additional perms on the AGENT RUNTIME user:**

| Requirement | Perm set (Name) | Why |
|---|---|---|
| Agentforce Contact Center Rep (Salesforce Voice) | `ContactCenterAgentNativeCCaaS` | Native voice access for the runtime user — required for the agent to operate on the voice call, not just the human rep |
| **Prompt Template User** | `EinsteinGPTPromptTemplateUser` | Gold-reference requirement for Voice + prompt templates; a real gap we hit (perms looked "done" without it) |
| Data Cloud User | label `Data Cloud User` | Base mandatory, but re-verify on the runtime user for voice — must be **manually** assigned |

> ⚠️ These go on the **agent runtime user**, not the human rep. Native voice was our field case
> where every "obvious" perm was present but Prompt Template User and the runtime user's Contact
> Center Rep were the last two to reconcile against the gold reference.

### Messaging (additive)

**Messaging Session Access (Required)** — on the **agent runtime user**, via a custom perm
set (doc's recommended name: *Agent Messaging Access*):

| Requirement (doc) | API name | Field |
|---|---|---|
| Access Conversation Entries | `PermissionsCanAccessCE` | app perm |
| Messaging Sessions object: **Read + View All Fields** | `ObjectPermissions` on `MessagingSession` | `PermissionsRead` + `PermissionsViewAllRecords`/`ViewAllFields` |

**Eligibility Flow Access (Required)** — same pattern as Voice (custom perm set "Messaging
Eligibility Flow Access"). ⚠️ Manual check.

**Optional — Service Replies:** standalone; needs `Service Replies User` + Prompt Template
perms. Greyed-out toggle = missing **EinsteinSRAgentforce** add-on (license gate, not perms).

### Case (additive)

Simplest channel. Base Mandatory is sufficient for read-only plan drafting; `ContactId`
context variable is auto-populated. No channel-specific object/flow perm block in the doc
beyond Mandatory + (if used) Knowledge Grounding and Agent Action perms.

### Knowledge Grounding (all channels, if grounding is used)

| Persona | Requirement | Match |
|---|---|---|
| Agent runtime user | Custom PS "Agent Knowledge Access": Allow View Knowledge; Knowledge object Read + View All Records + View All Fields; **Data Category Visibility** for the articles' categories | app perm `PermissionsViewKnowledge`; `ObjectPermissions` on `Knowledge__kav`; data-category visibility ⚠️ manual |
| Service Rep | Custom PS "Service Rep Knowledge Access": Knowledge Read/View All/View All Fields + Allow View Knowledge (needed only for **citations** to show) | same |

### Agent Actions (all channels, if custom actions are used)

All actions execute as the **agent runtime user**. For each custom action confirm on that user:
- **Apex class access** to every class the action calls (missing → generic error) — `SetupEntityAccess` type `ApexClass`
- **Apex sharing**: query classes should be `without sharing` (with sharing → 0 rows, silent)
- **Object perms** Read (+ Create/Edit if it writes)
- **FLS** Read on every field the action reads (missing → blank values, silent)
- `Run Flows` (`PermissionsRunFlow`) for flow actions, or per-flow access
- Manual-confirmation actions require the **Unmetered User Based AI** permission set license on the rep

## When perms PASS but SRA still fails — the pivot playbook (field-hardened 2026-09-24)

The most valuable thing this skill can do is tell you **"stop adding permissions — it's not perms."**
A full field case (KatsSDO, native Voice, pod USA1272 / 262.14.22) had **every documented
permission correct on both users** and SRA still didn't fire with *"We couldn't send your request.
Try again."* Here is how we proved it wasn't perms and where the real cause was — use this exact
sequence before you ever escalate "it's a perms bug."

### Signals that look like failures but are NOT (don't chase these)

| Signal | Looks like | Reality |
|---|---|---|
| **`GenOpPlan = 0` on Voice** | "planner never ran" | **EXPECTED on Voice.** Voice SRA *skips the summary plan* — it does NOT create a GenOpPlan like Case/Messaging do. Zero GenOpPlan on voice is normal, not a failure signal. |
| **`RecActorActionFeed = 0` on Voice** | "no actions ever" | Consistent with no engagement, but not itself a perm signal — verify with the event log below. |
| **`IsSuccessful = False`** on ConversationDefinitionEventLog rows | "errors" | Red herring — it's unpopulated and shows on successful rows too. Filter on `LogType`/`EventLabel`, not this. |
| **VoiceCall owned by the auto-process user** | "ownership bug" | Real known bug (auto-proc user assigned instead of rep/admin) — but **check it, don't assume it**. In our case the VoiceCall + Case were correctly owned by the rep. Rule it out; don't chase it. |

### The queries that actually tell you if the agent is receiving input

Data Cloud agent-telemetry DMOs (`AiAgentSession__dll`, `GenAIGatewayRequest__dll`, etc.) are
**often absent** on hand-provisioned / trial orgs (base Data Cloud can be on — `ssot__` DMOs exist —
while the GenAI Gateway telemetry DMOs do not). When they're missing, use the **core** objects:

```bash
# Sessions (does the agent even open a session per call?)
sf data query --target-org <alias> --query \
 "SELECT Id, ConversationDefinitionId, StartTime, EndTime, WasSessionEngaged, HasErrorLogs FROM ConversationDefinitionSession ORDER BY StartTime DESC LIMIT 20"

# Event log — the decisive trace. Correct fields are LogType + EventLabel (NOT 'EventType').
sf data query --target-org <alias> --query \
 "SELECT Id, ConversationDefinitionSessionId, ChannelType, LogType, EventLabel, LoggedTime FROM ConversationDefinitionEventLog ORDER BY LoggedTime DESC LIMIT 50"
```

**What a WORKING (engaged) session looks like** (we saw this on EmbeddedMessaging): ContextSetup →
`InputMessage` (the user utterance) → topic classification → INFORM / action → `FULLY_RESOLVED`.

**What a BROKEN voice session looks like** (our case): ContextSetup with **empty
`$System.ConversationContext = []`** → "Message sent: Hi! I'm your helpful bot." → CancelDialog.
**No `InputMessage`, no DetectedIntent, no engagement.** The agent greets and then hears nothing.

**The killer diagnostic — ChannelType distribution across the event log.** Ours was
`None=446, EmbeddedMessaging=411, Voice=0`. **Zero voice-channel events** while the same agent
fully engaged on messaging = the agent is fine; **the voice input never reaches it.**

### Root cause when the agent engages on Messaging but never on Voice

**The real-time voice transcript is not being delivered to the agent as conversation input.**
Tell-tale combo: live transcript renders in the Service Console **but** `ConversationEntry = 0`
and the agent's `$System.ConversationContext = []`.

**Why the transcript shows yet the agent gets nothing — two DIFFERENT transcription paths:**
1. **"Turn On Call Transcription"** (Setup → Call Recording and Transcription) = **post-call**
   transcription *"for quality and training purposes"* (its own description). This is why the
   console *displays* a transcript. Having it ON does **not** feed the agent.
2. **Real-time transcript streaming to the live conversation** = writes `ConversationEntry` turns
   into the conversation the agent monitors → this is the agent's input. If this isn't happening,
   the agent never hears the caller. Check the **"Transcription" tab** (real-time enablement, not
   the post-call toggle), the Contact Center real-time transcription config, and whether a
   `ConversationChannelDefinition` exists (empty = no live conversation stream wired).

> **Bottom line for the perm-checker:** if the scorecard is all ✅ and Voice still fails, the
> failure is **downstream of permissions** — most likely the real-time transcript isn't reaching
> the agent (ConversationEntry=0 + empty ConversationContext + Voice=0 event-log rows). Do NOT
> add more perms. Escalate with: *"agent proven working on Messaging, receives zero input on
> Voice, real-time transcript not delivered to conversation."*

### Escalation framing (say this, not "planner never fires")

> "SRA agent is published, active, and **provably works on EmbeddedMessaging** (topic classification
> + FULLY_RESOLVED). On **Voice**, the session opens, sends its welcome, and receives **zero input** —
> `$System.ConversationContext = []`, `ConversationEntry = 0`, no Voice-channel event-log rows.
> Real-time voice transcript is not delivered to the agent as conversation input (post-call
> transcription is ON and renders in the console, but the live stream isn't reaching the
> conversation). Perms/config/eligibility verified complete. Pod/release: <pod> / <release>."

## Output — scorecard

Print per-persona, per-channel pass/fail. Example:

```
🔐 SRA Permission Check — KatsSDO   (channel: voice)
Rep user(s): Maren Batt (005…WysH)   |   Agent runtime user: ServicePlanner User (005…gnfR)

BASE — Mandatory
  Rep      Service Planner User ................. ✅
  Rep      Access Agentforce Default Agent ...... ✅
  Agent    Service Planner Agent User ........... ✅
  Agent    Agentforce_Service_Assistant Perms ... ✅
  Agent    Data Cloud User ...................... ✅

VOICE
  Agent    Access Conversation Entries .......... ✅ (KAT_SRA_perms)
  Agent    View ALL Voice and Video Calls ....... ✅ (KAT_SRA_perms)
  Rep      Eligibility flow DIRECT access ....... ⚠️ MANUAL — Run Flows does NOT satisfy this
           Flow: KAT_Check_Service_Plan_Eligibility_for_VoiceCall (active)

VERDICT: Permissions compliant except the eligibility-flow direct-access item (manual).
If the panel still errors, it is NOT a documented permission gap → check enablement
(Agent Chat / Adaptive add-on) and the failed request's network response body.
```

Rules:
- ✅ present · ❌ missing (will break) · ⚠️ manual/uncertain (state exactly how to check by hand)
- Always name WHICH perm set grants a passing check (so they can trace it)
- Always say which USER each row applies to
- Never report a result you didn't get from a live query — mark unqueryable items ⚠️ manual
- End with a VERDICT that tells them whether perms are the likely cause or they should pivot

## Gotchas this skill was built to catch (from the field)

1. **Right permission, wrong user.** `Access Conversation Entries` / `View All Voice` belong
   on the **agent runtime user**, not the rep. Reps add them to themselves and it still fails.
2. **"View All Voice and Video Calls"** (`PermissionsViewAllCalls`) — not the non-"All" perm.
3. **Eligibility-flow access ≠ Run Flows.** The doc is explicit: the eligibility flow does
   NOT run off the `Run Flows` permission; the rep needs direct flow access. Check it via
   `SetupEntityAccess` `SetupEntityType='FlowDefinition'` (NOT `'Flow'` — that returns 0 and
   fools you into thinking there's no access). The granting perm set can have any name.
4. **`VoiceCall` object access is not in `ObjectPermissions`.** It's governed by the
   `PermissionsViewAllCalls` user permission — don't conclude "no VoiceCall read" from an
   empty `ObjectPermissions` query; that's a query artifact, not a finding.
5. **Data Cloud User must be manually assigned** to the agent user — it is NOT auto-added.
6. **Greyed-out "Service Replies for Service Assistant"** = missing **EinsteinSRAgentforce**
   add-on (license gate), not a permission-set problem.
7. Perm-set membership can appear inconsistent between a filtered query and a full-list query
   if output is truncated — always recount with `SELECT COUNT()`.
8. **`viewAllFields` is NOT a valid `.permissionset` metadata element** (as of v62.0) even though
   `PermissionsViewAllFields` is a real `ObjectPermissions` field. Setup mode grants object
   **Read** via metadata deploy, then sets **View All Fields** with a data update on the
   `ObjectPermissions` record post-deploy. Don't try to put it in the perm-set XML.
9. **MessagingSession Read depends on MessagingEndUser Read.** Granting only `MessagingSession`
   fails deploy with `Permission Read MessagingSession depends on permission(s): Read
   MessagingEndUser`. Setup mode grants both. (The dry-run/check-only deploy is what surfaces
   dependency + element errors like this *before* you write — always dry-run first.)
10. **Perm-set NAMES are cosmetic — compare CONTENTS.** Customers rename/consolidate the doc's
    granular sets (e.g. one `KAT - SRA perms` instead of Agent Voice/Messaging/Knowledge Access).
    Never match a gold reference by perm-set name; compare **effective permissions**
    (`PermissionsCanAccessCE`, `PermissionsViewAllCalls`, object perms, flow access). A rename is
    not a gap; a missing *effective permission* is.
11. **`GenOpPlan = 0` on Voice is EXPECTED, not a failure.** Voice SRA skips the summary plan.
    Do not treat zero GenOpPlan / zero RecActorActionFeed on voice as a perm signal — they're
    normal. (Case/Messaging DO create GenOpPlan; voice does not.)
12. **Perms all-green ≠ working SRA — pivot, don't pile on perms.** Our worst field time-sink was
    adding perms that were already correct. When the scorecard is all ✅ and it still fails, the
    cause is downstream (real-time transcript not reaching the agent, enablement/license gate,
    platform). See "When perms PASS but SRA still fails" above and STOP adding permissions.
13. **Two transcription paths.** "Turn On Call Transcription" = post-call (quality/training),
    which makes the console *show* a transcript but does NOT feed the agent. Real-time streaming
    to the live conversation (→ `ConversationEntry`) is what the agent consumes. Console transcript
    present + `ConversationEntry = 0` = real-time transcript not reaching the agent — a config
    issue, never a perm fix.
14. **Verify agent input via core objects when DC telemetry DMOs are absent.**
    `ConversationDefinitionSession` / `ConversationDefinitionEventLog` are queryable on core even
    when `AiAgentSession__dll` etc. don't exist. Correct fields: `LogType` + `EventLabel` (NOT
    `EventType`), `ChannelType`, `WasSessionEngaged`, `HasErrorLogs`. A `ChannelType` breakdown
    showing engaged Messaging rows but **zero Voice rows** proves the agent isn't receiving voice
    input — not a perm problem. Ignore `IsSuccessful` (unpopulated red herring).

## Related skills

- `sra-setup-debug` — broader "why isn't it working" (activation, config, knowledge, actions)
- `agentforce-voice-expert` — Voice/telephony/contact-center narrative
- `sra-agent-debugger` — full session trace for behavior debugging
