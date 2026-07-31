---
name: sra-setup-debug
description: Diagnose why Service Rep Assistant isn't activating or working in an org. Runs automated checks for permissions, configuration, messaging setup, knowledge indexing, and action execution. Built for Forward Deployed Engineers setting up SRA in customer/sandbox orgs.
tools: [Bash, Read, Write, Edit]
---

# SRA Setup Debugger — "Why Isn't It Working?"

> Automated diagnostic for FDEs and SEs who have SRA "set up" but it's not activating,
> not generating plans, actions are failing silently, or knowledge isn't grounding.
> Runs against a target org and produces a pass/fail checklist with exact fix instructions.

## When to trigger

- User says "SRA isn't working", "agent isn't activating", "no plan generates"
- User asks "why isn't [action/knowledge/messaging] working in my org"
- User reports: component shows default intro text, actions return empty, knowledge not found
- User wants to validate their org setup before a demo
- User is setting up SRA in a new org and wants a pre-flight check

## Getting Started

**Prerequisites:**
- `sf` CLI authenticated against the target org (`sf org login` completed)
- Python 3.9+ (optional — only needed for tracer integration)

**Installation:**
Copy this skill's `SKILL.md` into your `~/.claude/skills/sra-setup-debug/` directory.

No other dependencies — this skill is purely diagnostic queries run via the `sf` CLI.

## If the user hasn't given enough to proceed

Print this verbatim:

> What org should I check?
>
> I need:
> - **Org alias** — the `sf` CLI alias for the target org (e.g. `mySDO`, `demoOrg`)
>
> Optionally:
> - **Channel** — `messaging`, `case`, or `both` (default: both)
> - **Specific symptom** — e.g. "agent not activating on messaging", "knowledge not grounding", "action returns empty"
>
> I'll run a full setup diagnostic: permissions, configuration, messaging eligibility, knowledge indexing, action execution, and Data Cloud connectivity.

## Diagnostic Pipeline

Run these checks in order. Stop at the first critical failure and report it — downstream checks depend on earlier ones passing.

### Phase 1: Agent Existence & Activation

```bash
# Is there an active Agentforce agent?
sf data query --query "SELECT Id, MasterLabel, DeveloperName, IsActive FROM BotDefinition WHERE IsActive = true" --target-org <alias>

# Is it linked to a channel?
sf data query --query "SELECT Id, BotId, ChannelType FROM BotChannel" --target-org <alias>
```

**Pass criteria:**
- At least one active BotDefinition exists
- BotChannel links it to the correct channel(s) (Messaging and/or Case)

**Common failure:** Agent created but not activated (toggle in Agent Builder)

---

### Phase 2: Permission Set Checks

The SRA runtime user runs actions. Most failures are silent perm issues.

**Important:** Orgs often have MULTIPLE Einstein Agent Users (one for SRA, one for customer-facing Agentforce Service Agent, one for Employee Agent). You must identify the correct one — the user with `ServicePlannerAgentUser` or `ServicePlannerUser` perm set is the SRA runtime user.

```bash
# Find ALL Einstein Agent profile users
sf data query --query "SELECT Id, Name, ProfileId, Profile.Name FROM User WHERE Profile.Name = 'Einstein Agent User' LIMIT 10" --target-org <alias>

# Identify the SRA runtime user (has ServicePlannerAgentUser or ServicePlannerUser)
sf data query --query "SELECT AssigneeId, Assignee.Name FROM PermissionSetAssignment WHERE PermissionSet.Name IN ('ServicePlannerAgentUser', 'ServicePlannerUser')" --target-org <alias>

# THEN check permissions on THAT user (not just any Einstein Agent User)
sf data query --query "SELECT PermissionSetId, PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = '<SRA_agentUserId>'" --target-org <alias>
```

**Common mistake:** Checking perms on `EinsteinServiceAgent User` when SRA actually runs as `ServiceAgent Agentforce` (or another user). Always identify by perm set, not by name.

**Check each of the 8 critical permissions:**

| # | Permission | How to verify | Silent failure mode |
|---|-----------|---------------|---------------------|
| 1 | Apex sharing mode | Read class source: must be `without sharing` | 0 rows returned, no error |
| 2 | Perm set on BOTH users | Query PermissionSetAssignment for agent user AND CSR | Action fails only at runtime |
| 3 | Apex class access | Query SetupEntityAccess for each Invocable class | Generic failure, no "no access" msg |
| 4 | Object access (Read/Create/Edit) | Query ObjectPermissions on the perm set | SOQL returns 0 records |
| 5 | Field-Level Security | Query FieldPermissions for custom fields | Fields return null silently |
| 6 | Messaging access | Check `AgentMessagingAccess` perm set assigned | No conversation entries available |
| 7 | Context variable (currentRecordId) | Must exist in Agent Builder Context tab | Messaging actions get no record context |
| 8 | Data Category visibility | If KAs have categories, perm set needs visibility | Articles skip indexing silently |

```bash
# Apex class access check
sf data query --query "SELECT SetupEntityId, SetupEntity.Name FROM SetupEntityAccess WHERE ParentId IN (SELECT Id FROM PermissionSet WHERE Name = '<permSetName>') AND SetupEntityType = 'ApexClass'" --target-org <alias>

# Object perms check
sf data query --query "SELECT SobjectType, PermissionsRead, PermissionsCreate, PermissionsEdit FROM ObjectPermissions WHERE ParentId IN (SELECT Id FROM PermissionSet WHERE Name = '<permSetName>')" --target-org <alias>

# FLS check (custom fields)
sf data query --query "SELECT Field, PermissionsRead, PermissionsEdit FROM FieldPermissions WHERE ParentId IN (SELECT Id FROM PermissionSet WHERE Name = '<permSetName>') AND Field LIKE '%__c'" --target-org <alias>
```

---

### Phase 3: Channel-Specific Configuration

SRA behaves differently across channels. Each has its own permissions, context variables, and configuration requirements. Check the relevant channel(s) based on the symptom.

#### Channel Comparison Matrix

| Requirement | Case | Messaging (MIAW/ECv2) | Voice |
|------------|------|----------------------|-------|
| **Context variable for record** | `ContactId` ✅ | `currentRecordId` (→ MessagingSession Id) | `currentRecordId` (→ VoiceCall Id) |
| **Contact resolution** | Direct via `ContactId` | Apex: `MessagingSession.EndUserContactId` | Apex: `VoiceCall.RelatedRecordId` or participant lookup |
| **Required perm sets** | Base Agentforce perms | Base + `AgentMessagingAccess` | Base + `Service Cloud Voice` perms |
| **Channel config** | Omni-Channel routing to queue | Embedded Service + Messaging Channel + Eligibility Flow | Voice Channel + Contact Center config |
| **Transcript access** | Case Comments / Feed | Conversation Entries (needs messaging access perm) | VoiceCall transcript (ConversationEntry or Transcript__c) |
| **Agent activation trigger** | Case assigned to agent-enabled queue | Customer sends message → eligibility flow → agent session | Call routed → IVR/flow hands to agent |
| **CLT rendering** | Service Console (standard) | Embedded chat widget + Service Console | Service Console (during/after call) |
| **Common silent failure** | Works fine (fewest moving parts) | `ContactId` returns null (Case-only variable) | Voice perms not assigned, transcript not accessible |

---

#### 3A. Case Channel

Simplest channel — fewest things to break.

**Checks:**
1. Agent is linked to a Case queue via Omni-Channel routing
2. `ContactId` context variable is available (auto-populated from Case)
3. Case assignment triggers agent activation

```bash
# Verify Omni-Channel queue config
sf data query --query "SELECT Id, DeveloperName, QueueId FROM ServiceChannel WHERE IsActive = true" --target-org <alias>
```

**Common issues:**
- Agent not activated on the queue (Agent Builder → Channels)
- Omni-Channel routing config not pointing to agent-enabled queue

---

#### 3B. Messaging Channel (MIAW / Embedded Chat v2)

Most complex setup — the #1 source of "it works on Case but not Messaging" questions.

**Critical checks:**

1. **Messaging Channel exists and is active**
```bash
sf data query --query "SELECT Id, MasterLabel, IsActive, MessagingChannelType FROM MessagingChannel WHERE IsActive = true" --target-org <alias>
```

2. **Embedded Service linked to Messaging**
```bash
sf data query --query "SELECT Id, DeveloperName, IsActive FROM EmbeddedServiceConfig WHERE IsActive = true" --target-org <alias>
```

3. **Eligibility Flow returns eligible**
   - Confirm the Messaging eligibility flow exists and is Active
   - Confirm it returns `isEligible = true` for the expected conditions
   - The flow controls WHETHER the agent activates on this session

4. **AgentMessagingAccess permission set assigned**
   - Without this, agent cannot read Conversation Entries
   - Symptom: agent activates but has no transcript context

5. **Context variable: currentRecordId (NOT ContactId)**
   - `ContactId` is **Case-only** — it is **NOT** populated on Messaging Sessions
   - Actions that use `ContactId` will get `null` on messaging
   - Must use `currentRecordId` (resolves to the MessagingSession Id)
   - Then resolve Contact in Apex: `MessagingSession.EndUserContactId`

6. **Omni-Channel routing for messaging queue**
   - Messaging sessions route through a queue — agent must be enabled on that queue

**The #1 messaging-specific failure:**
> "Works on Case, not on Messaging" = almost always `ContactId` context variable used
> instead of `currentRecordId`. The fix is in Apex: accept the MessagingSession ID
> and resolve the Contact from `EndUserContactId`.

**The #2 messaging failure:**
> Agent activates but shows only default intro — no plan generates. Usually the
> Eligibility Flow is missing or not returning `isEligible = true`. Can also be that
> Omni-Channel routing doesn't route to the agent-enabled queue.

---

#### 3C. Voice Channel (Service Cloud Voice)

**Critical checks:**

1. **Service Cloud Voice enabled and configured**
```bash
sf data query --query "SELECT Id, DeveloperName, IsActive FROM ContactCenter" --target-org <alias>
```

2. **Voice-specific permission sets assigned**
   - Service Cloud Voice User (or equivalent)
   - `SCV_Integration_User` for telephony adapter access
   - Base Agentforce perms on the agent user

3. **Context variable: currentRecordId → VoiceCall**
   - On voice, `currentRecordId` resolves to the `VoiceCall` record Id
   - To get the Contact: query `VoiceCall` → related participant records, or use `CallerId`
   - Apex pattern:
     ```apex
     VoiceCall vc = [SELECT Id, RelatedRecordId FROM VoiceCall WHERE Id = :voiceCallId];
     // RelatedRecordId may be Contact, Lead, or Account depending on matching
     ```

4. **Transcript availability**
   - Real-time transcript requires the telephony adapter to stream it
   - Post-call transcript stored in `ConversationEntry` or custom transcript object
   - If agent needs transcript during the call: ensure real-time streaming is configured in the Contact Center settings

5. **IVR/Flow handoff to agent**
   - Voice calls typically go through an IVR flow before reaching the agent
   - The flow must explicitly route to an agent-enabled queue
   - If the flow terminates without routing, the agent never activates

**Common voice failures:**
- Telephony adapter not connected (no transcript data)
- `VoiceCall` record not created (adapter config issue)
- Agent perms don't include Voice-specific access
- Real-time transcript not streaming (agent has no conversation context during call)
- Contact matching fails → `RelatedRecordId` is null → Apex actions can't resolve customer

---

#### Channel Diagnostic Quick-Reference

When the user says "it doesn't work on [channel]", start here:

| Symptom | Channel | First check |
|---------|---------|-------------|
| "Works on Case, not Messaging" | Messaging | `ContactId` → switch to `currentRecordId` |
| "Works on Case, not Voice" | Voice | Voice perm sets + VoiceCall record creation |
| "Agent shows intro text only" | Messaging | Eligibility Flow + Omni-Channel routing |
| "Agent shows intro text only" | Voice | IVR flow not routing to agent queue |
| "Actions return empty on Messaging" | Messaging | `currentRecordId` resolution + `EndUserContactId` |
| "Actions return empty on Voice" | Voice | `VoiceCall.RelatedRecordId` null (contact matching) |
| "No transcript context" | Messaging | `AgentMessagingAccess` perm set |
| "No transcript context" | Voice | Real-time transcript streaming not configured |

---

### Phase 4: Knowledge & Grounding

```bash
# Are Knowledge Articles published AND validated?
sf data query --query "SELECT Id, Title, PublishStatus, ValidationStatus, IsLatestVersion, IsVisibleInPkb FROM Knowledge__kav WHERE PublishStatus = 'Online' LIMIT 10" --target-org <alias>

# Data Library connected? Check search index chunks
sf data query --query "SELECT COUNT(Id) FROM KA_SA_Data_Library_chunk__dlm" --target-org <alias> --api-version 61.0

# Check if specific article is indexed (if user provides a keyword)
sf data query --query "SELECT Id, ContentText__c FROM KA_SA_Data_Library_chunk__dlm WHERE ContentText__c LIKE '%<keyword>%' LIMIT 5" --target-org <alias> --api-version 61.0
```

**Pass criteria:**
- Published articles exist (PublishStatus = 'Online')
- **ValidationStatus = 'Validated'** (CRITICAL — articles won't be grounded by AI if not validated)
- IsLatestVersion = true (only the latest version is indexed)
- Chunk count > 0 (Data Library has indexed)
- Target articles appear in chunks

**Common failures:**
- ❌ **Articles published but ValidationStatus != 'Validated'** — SILENT BLOCKER, articles won't be retrieved by agent even if published
- Articles published but Data Categories block indexing (perm 8)
- Articles published but Summary field is blank (retrieval can't match)
- Search index never rebuilt after publishing
- Data Library not connected to the agent's topic
- Articles published but IsLatestVersion = false (older version — won't be indexed)

---

### Phase 5: Action Configuration

```bash
# List all Invocable Actions available
sf data query --query "SELECT Id, DeveloperName, TargetType, IsActive FROM GenAiFunction WHERE IsActive = true" --target-org <alias>
```

**Check for each action:**

| Check | What to look for | Fix |
|-------|-----------------|-----|
| `isUserInput: true` on inputs | Agent says "I cannot do this automatically" | Set to `false` in Apex |
| Missing from topic | Action exists but never fires | Add to topic in Agent Builder |
| Output Rendering not set | Card data narrated as text | Set Lightning Type in Output Rendering |
| Asset Library stale | New inputs/outputs not showing | Delete + re-add from Asset Library |
| Action description misaligned | Agent picks wrong action or skips it | Rewrite from customer-intent perspective |

**Asset Library caching gotcha:**
> If you added new `@InvocableVariable` fields to an Apex class after it was first
> added to Asset Library, Agent Builder still sees the OLD schema. Fix: delete the
> action from **Asset Library** (not just the topic), then re-add to the topic.
> Do NOT version — just delete and re-add cleanly.

---

### Phase 6: Data Cloud Connectivity

```bash
# Can we query Data Cloud tables?
sf data query --query "SELECT Id FROM AiAgentSession__dll LIMIT 1" --target-org <alias> --api-version 61.0
```

**If this fails:**
- Data Cloud may not be enabled
- API version may be too old (need 61.0+)
- User may not have Data Cloud permissions

**Note:** Data Cloud is needed for session traces/debugging but NOT for SRA to function. If SRA works but traces don't, this is the blocker.

---

## Output Format

Print a structured diagnostic report:

```
🔍 SRA Setup Diagnostic — [org alias]
═══════════════════════════════════════

✅ Agent: Active (SDO_Service_Agentforce_Service_Assistant)
✅ Channel: Messaging + Case
⚠️ Permissions: 6/8 checks pass
   ❌ FLS: Pet_Name__c not readable by EinsteinServiceAgent User
   ❌ Data Category visibility not assigned (Knowledge won't index)
✅ Messaging Config: Eligibility flow active, channel linked
❌ Knowledge: 0 chunks indexed (rebuild search index after fixing Data Categories)
✅ Actions: 4/4 active, all inputs configured correctly
✅ Data Cloud: Connected, tables queryable

═══════════════════════════════════════
🔧 Fix List (in priority order):

1. Grant FLS Read on Pet_Name__c to the Agentforce permission set
   → Setup → Permission Sets → [name] → Object Settings → [object] → Field Permissions

2. Assign Data Category Visibility on the agent's permission set
   → Setup → Permission Sets → [name] → Data Category Visibility → Edit → assign categories
   → Then: Data Cloud → Search Indexes → Rebuild

3. After fixing #2, rebuild the search index and verify:
   sf data query --query "SELECT COUNT(Id) FROM KA_SA_Data_Library_chunk__dlm" --target-org [alias]
```

## Escalation Paths

If automated checks all pass but SRA still doesn't work:

| Symptom | Next step |
|---------|-----------|
| Agent doesn't activate at all | Check if agent is Published (not just Active). Check Omni-Channel routing config. |
| Plan generates but actions fail | Run `sra-agent-debugger` trace on a session ID to see action-level errors |
| CLT cards render as text | Output Rendering config in Agent Builder — requires exact Lightning Type name |
| Knowledge returns wrong articles | Check article Summary field (used for retrieval matching). Run tracer to see what was grounded. |
| Everything passes, still broken | Remote Site Settings, Connected App, Named Credential — check if external callouts are blocked |

## Official Implementation Guides

The canonical setup docs for each channel (INTERNAL — share with customers as PDF only):

| Channel | Implementation Guide |
|---------|---------------------|
| Case | [Agentforce Service Assistant for Case (Closed Beta)](https://docs.google.com/document/d/1ptRJz7ckEc-LnLtXZH6-gKK3dDzbdFBo3_lCmqAzeVQ/edit) |
| Messaging | [Agentforce Service Assistant for Messaging (Closed Beta)](https://docs.google.com/document/d/18o7dnDlgxTwt0eIgQUHW51VDTxDWSQPLtyw4Yiboi3E/edit) |
| Voice | [Agentforce Service Assistant for Voice (Closed Beta)](https://docs.google.com/document/d/1z1hrQGfz551bWVu3qe9hfpScii0d2t3uc0wCG7qqk3Y/edit) |

**Subagent & Knowledge Best Practices:**
- [Subagent Best Practices](https://docs.google.com/document/d/16sALqGbEuzmNK6ygye6VFCkWXb1dktUOE3cR6uRLhbU/edit)
- [Subagent Design Implementation Guide](https://docs.google.com/document/d/1RZAEWpd3m2lrP78X0nXgyOi4H-74BwSl81MjBl-Am5s/edit)
- [ADL Grounding Best Practices](https://docs.google.com/document/d/1y1lu7fphcX93k_Qh4CwUe6-kbXH0kfX5C1ATrwufRBs/edit)
- [Knowledge Article Optimization](https://docs.google.com/document/d/1dt338oWnfskwmKQcyX0mI5MJfc339F3kHYhyg4Z3ycs/edit)

**Hub doc (all links):** https://docs.google.com/document/d/14U2OGYFGe4S4GOECMBWgvzSyfAu1snjtMkPA__WfnxQ/edit

## Common Questions & FAQ (from FDE/SE Slack channels)

These are real questions that come up repeatedly. If the user describes one of these symptoms, jump directly to the answer.

---

### Q1: "SRA works on Case but not on Messaging"

**Root cause (95% of the time):** Actions use `ContactId` context variable, which is **Case-only**. On Messaging, it returns `null`.

**Fix:**
1. Switch to `currentRecordId` (resolves to MessagingSession ID on messaging)
2. In your Apex action, resolve the Contact:
   ```apex
   MessagingSession ms = [SELECT EndUserContactId FROM MessagingSession WHERE Id = :currentRecordId];
   Id contactId = ms.EndUserContactId;
   ```
3. Ensure `AgentMessagingAccess` permission set is assigned to the agent user

**Evidence:** Asked by Ian Hunter, Katie Teece, Kunal Rastogi, Sristi Agrawal — all same root cause.

---

### Q2: "Service Assistant component shows intro text only — no plan generates"

**Checklist (in order):**
1. **Eligibility Flow** — Does it exist AND return `isEligible = true`? (Messaging-specific)
2. **Omni-Channel routing** — Is the messaging queue routed to an agent-enabled queue?
3. **Agent activation** — Is the agent Published (not just Active) and linked to the channel?
4. **Utterance threshold** — Dynamic Plans on messaging trigger after ~5 customer utterances (some report 7-8 in beta)
5. **Topic classification** — Does case Subject+Description match your topic descriptions? (classifier reads ONLY Subject+Description, not custom fields)

**If messaging-specific:** The plan won't auto-generate until the conversation has enough context. Confirm the eligibility flow fires and routes correctly.

---

### Q3: "No relevant topics exist" error when plan should generate

**Root causes:**
1. **Topic description misalignment** — The classifier reads ONLY `Case.Subject` + `Case.Description`. If your routing info is in custom fields, it won't match.
2. **Workaround:** Record-triggered Flow that appends classification tokens to Description field
3. **Agent not activated** — Toggle in Agent Builder (Published + Active)
4. **Service AI Grounding** — Custom fields in SAG config are NOT used for topic classification (confirmed by eng)

---

### Q4: "Knowledge articles not grounding / plan steps don't cite articles"

**Diagnostic steps:**
1. **ValidationStatus != 'Validated'?** — ❌ **THE #1 SILENT BLOCKER**. Articles can be Published (`PublishStatus = 'Online'`) but still blocked from AI grounding if `ValidationStatus != 'Validated'`. This field is separate from publish status and MUST be set to 'Validated' for the agent to use the article. Check: `SELECT ValidationStatus FROM Knowledge__kav WHERE Id = '<articleId>'`
2. **Summary field blank?** — KA `Summary` field drives retrieval matching. If blank, article won't be found.
3. **Data Categories blocking?** — If articles have Data Categories assigned, the agent's permission set needs category visibility (silent failure)
4. **Search index not rebuilt?** — After publishing articles or changing categories, rebuild the search index
5. **Article too long?** — Plans pull limited step detail from KAs. 15+ step procedures get truncated. Break into multiple focused articles.
6. **System vs. Runtime knowledge** — Dynamic Plans have TWO knowledge paths:
   - **System knowledge** — fetched once at plan start (from case Subject+Description), stays in prompt for ALL turns, but has **NO citations** (known gap, GUS `a07EE00002cbR64YAE`)
   - **Runtime knowledge** — fetched per-turn (from user message), filtered by score >0.6, DOES produce citations
   - If the answer is correct but `citedReferences: []` → likely from system knowledge, NOT hallucination
6. **Guidance Plan vs Dynamic Plan** — Guidance Plans reliably show KB citations. Dynamic Plans may answer from system knowledge without any citation indicator.

**Verify indexing:**
```bash
sf data query --query "SELECT COUNT(Id) FROM KA_SA_Data_Library_chunk__dlm" --target-org <alias> --api-version 61.0
```

---

### Q5: "Start Plan button not showing" on Messaging or Voice record pages

**Causes:**
1. **Permission set missing** — `Service Planner Agent User` (or cloned equivalent) must be assigned to the CSR user
2. **Component not on page layout** — Service Assistant component must be added to the record page (MessagingSession or VoiceCall page)
3. **Channel not linked** — In Agent Builder → Channels, confirm the agent is linked to the correct channel
4. **Redraft Plan** specifically requires `Service Planner Builder` permission set (even cloned versions need the core permissions)

---

### Q6: "Agent works in Agent Builder test but fails in Service Console"

**Key difference:** Agent Builder uses the Agent API directly with different context than the runtime dynamic plan service.

**Common causes:**
1. **Context variables not populated** — Builder may inject test values; Console requires real record context
2. **Permissions** — Builder runs as YOU; Console runs as the EinsteinServiceAgent User (which may lack perms)
3. **Messaging Session ID** — Builder can't replicate the messaging-specific context injection
4. **Flow inputs** — If a flow requires MessagingSession ID as input, it will fail in Console if the context variable isn't mapped

**Always test in the actual channel** (Console with real Case/Messaging session), not just Builder.

---

### Q7: "Quick Actions / CLT cards not reliably showing in plan"

**Why it's intermittent:**
1. **Action description** — Must describe the action from the customer-intent perspective (what problem it solves, not what it technically does)
2. **Topic alignment** — QA must be mapped to the specific topic/subagent being used
3. **Output Rendering** — Without the exact Lightning Type name configured, card data is narrated as text
4. **`show_command` directive** — Action descriptions need the render directive for CLT cards to appear
5. **Instruction reinforcement** — Add explicit instruction: "When [scenario], use the [Action Name] action and display the result"

---

### Q8: "Dynamic Plan stuck on 'Starting the plan...'"

**Causes:**
1. **Org patch not deployed** — Check org instance and whether the latest platform patch has been applied
2. **Eligibility flow timing** — Flow may be returning `isEligible` before necessary records are created
3. **Case closed mid-plan** — If an action closes the case during execution, SRA gets stuck (known issue)
4. **Network/timeout** — Remote Site Settings or Named Credentials blocking external callouts

---

### Q9: "How do I get Contact/Customer context on Messaging?"

**Pattern by channel:**

| Channel | How to get Contact | Code pattern |
|---------|-------------------|-------------|
| Case | `ContactId` context variable (auto-populated) | Direct — no lookup needed |
| Messaging | `currentRecordId` → MessagingSession → `EndUserContactId` | `[SELECT EndUserContactId FROM MessagingSession WHERE Id = :recordId]` |
| Voice | `currentRecordId` → VoiceCall → `RelatedRecordId` | `[SELECT RelatedRecordId FROM VoiceCall WHERE Id = :recordId]` |

**Important:** You CANNOT get MessagingSession ID and push it into a SubAgent Action directly without Apex. The SubAgent doesn't have access to pass context between actions natively — use a single Apex invocable that handles the full lookup chain.

---

### Q10: "SRA setup page throws 'We couldn't load Service Assistant settings'"

**Causes:**
1. **Org not enabled for SRA** — Dynamic Plans require feature enablement (submit org ID via intake form)
2. **Org version too old** — Requires 262+ for dynamic plans
3. **Permission missing** — Admin needs Service Cloud Einstein or equivalent license
4. **Instance patch pending** — Some instances get patches on different schedules

---

### Q11: "Plan generates but agent doesn't resume after custom action"

**Pattern:** After invoking a custom flow/Apex action, SRA shows results but says "Let me know how you'd like to proceed" instead of computing the next step.

**Fixes:**
1. Add instruction: "After completing [action], immediately determine and present the next recommended step based on the results"
2. Ensure action output includes structured data the planner can act on (not just a success message)
3. This is a known UX gap — SRA sometimes waits for human confirmation after custom actions

---

### Q12: "Legacy Agentforce Builder required — new builder redirects"

**Current state (as of 264):**
- Service Assistant must be created in the **legacy Agentforce Builder**
- The new Agentforce Builder does NOT support SRA yet
- If your org auto-redirects to new builder, you may need to use a direct URL to legacy builder
- SRA moving to new Agent Builder is on the roadmap (later this year)

---

### Q13: "Case Catch-Up & Insights card not showing"

**This feature is STANDALONE** — doesn't require full SRA agent setup.

**Checklist:**
1. **Service Assistant turned on** — Setup page → must be toggled on
2. **LWC on page** — Service Assistant component must be on the Case record page
3. **Prompt templates activated** — Each insight needs its template activated in Prompt Builder
4. **Licensing** — Requires: Agentforce for Service + Service Planner Add-On + Adaptive Experience Add-On
5. **Permissions** — Rep needs `Service Planner User` + `Prompt Template User`
6. **Opening Sentiment disabled?** — Requires Customer Signals Intelligence configured (greyed out without it)
7. **Card never refreshes** — Generated once on first open. If data changed after, card shows stale info (by design)
8. **First-rep problem** — If the first rep to open the case lacks CSI/SLA access, sentiment/SLA data is permanently omitted for that case

**Does NOT require:** Data Cloud, Agentforce turned on, or agent creation.

---

### Q14: "What licenses do I need for the full SRA experience?"

| License | What it unlocks |
|---------|----------------|
| Agentforce for Service (or Agentforce 1) | Base platform |
| Service Planner Add-On | Service plans (guidance + dynamic) |
| Service Assistant Adaptive Experience Add-On | Agent Chat + Case Catch-Up & Insights |

- **Einstein for Service only?** → Contact AE to upgrade. Missing Agent Chat and Case Catch-Up.
- **Service Planner Add-On only?** → Gets plans but no chat or insights card.
- **No flex credit drawdown** for Case Catch-Up card generation.

---

### Q15: "Observability / reporting — what can we see?"

**Available today:**
- `RecActorActionFeed` — action-level feed with content JSON (queryable via SOQL)
- `GenOpPlan` — summary plan records (queryable)
- Service Insights add-on — pulls GenOpPlan* objects into Data Cloud (requires license)
- Custom LWC debuggers — community-built (Dan Franasiak's package, Olivier Rachon's tools)
- `sra-agent-debugger` skill — full session trace via Data Cloud STDM tables

**Not available yet:**
- Native analytics dashboard for Dynamic Plans in new builder (roadmap)
- Messaging Session support in automated testing tool (roadmap)
- Full conversation forensics without Data Cloud (requires STDM access)

---

## Cross-references

- **Full session trace:** use `sra-agent-debugger` skill (same repo) with a Case/MessagingSession ID for action-level debugging
- **CLT component setup:** use `sf-clt-builder` skill (same repo) for generating Custom Lightning Type cards
- **Shared skills repo:** https://git.soma.salesforce.com/chad-goldsmith/claude-skills

## Important

- **EVERY finding must come from a live org query** — NEVER report findings from session memory, prior conversations, or assumptions about what "should" be configured. If you can't query it, mark it "⚠️ Manual check needed (not queryable via SOQL)"
- NEVER modify the target org without explicit user permission
- Report findings but let the user decide what to fix
- If a check requires manual verification (Agent Builder UI), note it as "⚠️ Manual check needed" and explain HOW to check it manually
- Distinguish between "will definitely break SRA" (❌) vs "might cause issues" (⚠️)
- Always recommend fixing in priority order (agent activation → perms → config → knowledge)
- If a SOQL query errors (object not supported, field doesn't exist), note the check as "⚠️ Could not verify (API limitation)" — do NOT guess the result
