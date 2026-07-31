# Agentforce Voice Expert

> Expert knowledge on Agentforce Contact Center (native voice), Voice SRA setup, troubleshooting "unable to complete request" errors, permission requirements, and Voice-specific configuration. Covers both native telephony and BYOT (Amazon Connect).

**Invocation:** `/agentforce-voice-expert [question]`

---

## What This Skill Covers

- **Native Voice Setup** — Salesforce Voice (Agentforce Contact Center with native telephony)
- **Voice SRA Requirements** — Permission sets, context variables, action configuration
- **Troubleshooting** — "Unable to complete request" error diagnosis
- **Voice vs Case vs Messaging** — Channel-specific differences for SRA
- **BYOT Setup** — Amazon Connect integration patterns
- **Common Failures** — Permission gaps, Omni-Channel routing, Contact Center config

---

## Native Voice Setup (Agentforce Contact Center)

### Official Setup Guide
**Primary Doc:** [Agentforce Contact Center - Voice | SDO Setup Guide](https://docs.google.com/document/d/1CREbnKIvxp9Fi2DOcWKsw3_8eDrQ9aySsPgKMcswSpY/edit?tab=t.0)
- Available in SDOs spun **2/21/26 or later**
- Setup time: ~30 minutes from scratch
- **Q-Brix (automated setup):** https://www.solutionswork.space/content/post/kA0Ka0000024t3GKAQ/salesforce-voice-sdo

### Required Licenses (SDO)
```
• SalesforceVoice (10 licenses per SKU)
• InboundVoiceCredits (100k minutes per SKU)
• OutboundVoiceCredits (100k minutes per SKU)
• NativeNumber10DLCGroupA
```

**Note:** These licenses are pre-enabled in SDOs from 2/21/26+. For custom orgs, add via BlackTab.

### Required Permission Sets (Human Agents)
```
• Agentforce Contact Center Admin
• Agentforce Contact Center Rep
• Agentforce Contact Center Supervisor (Salesforce Voice)
```

**Critical:** Assign to BOTH the human rep user AND the admin user setting up Contact Center.

### Setup Sequence (High-Level)
1. **Enable licenses** (pre-done in SDO)
2. **Assign permission sets** to admin user
3. **Create Contact Center** (Setup → Contact Centers → New)
4. **Add users to Contact Center**
5. **Configure Omni-Channel** (queues, routing flows)
6. **Provision phone number** (10DLC or toll-free)
7. **Configure voice channel** (inbound/outbound settings)
8. **Test with human agent** (make/receive calls)
9. **(Optional) Enable Agentforce Voice** (AI agent on voice channel)

---

## Voice SRA Requirements

### Agent Runtime User Permissions
The SRA agent runtime user (typically `ServiceAgent Agentforce` or `EinsteinServiceAgent User`) needs:

**Base SRA Permissions:**
- `ServicePlannerUser` or `ServicePlannerAgentUser` ✅
- `Agent_Knowledge_Access` ✅

**Voice-Specific Permissions:**
- `Service Cloud Voice User` (or equivalent) ❌ **COMMONLY MISSING**
- OR one of these SDO variants:
  - `SDO_Service_All_Voice`
  - `SDO_Service_SCV_Access`
  - `Agentforce Contact Center Rep`

**Why it fails without this:** Agent cannot read `VoiceCall` or `ConversationEntry` objects → silent failure → generic error message.

### Context Variable: currentRecordId
**Critical difference from Case:**
- **Case Channel:** `ContactId` context variable is auto-populated
- **Messaging Channel:** `currentRecordId` → resolves to `MessagingSession.Id`
- **Voice Channel:** `currentRecordId` → resolves to `VoiceCall.Id`

**Common mistake:** Actions written for Case use `ContactId` directly. On Voice, `ContactId` is `null`.

**Fix:** Use `currentRecordId` and resolve Contact in Apex:
```apex
@InvocableVariable
public String currentRecordId; // VoiceCall Id on Voice channel

// In action logic:
VoiceCall vc = [SELECT Id, RelatedRecordId, CallerId 
                FROM VoiceCall 
                WHERE Id = :currentRecordId];
// RelatedRecordId may be Contact, Lead, or Account depending on caller matching
```

### Agent Builder Configuration
**Channels Tab:**
- Voice channel must be **enabled**
- Link to Voice Contact Center
- (Optional) Voice-specific eligibility flow

**Context Variables:**
- `currentRecordId` must be available (auto-configured in 264+)
- Do NOT rely on `ContactId` for Voice

**Actions:**
- All action inputs must use `currentRecordId` (not `ContactId`)
- All actions need Voice object permissions on agent runtime user

---

## Common "Unable to Complete Request" Root Causes

This is the #1 Voice SRA error. Generic message hides the real failure.

### Diagnostic Priority Order

#### 1. Agent Runtime User Missing Voice Permissions (90% of cases)
**Symptom:** Generic error on first Voice SRA activation

**Check:**
```bash
# Find the SRA runtime user
sf data query --query "SELECT AssigneeId, Assignee.Name FROM PermissionSetAssignment WHERE PermissionSet.Name IN ('ServicePlannerAgentUser', 'ServicePlannerUser')" --target-org <alias>

# Check Voice permissions on that user
sf data query --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = '<agent_user_id>' AND (PermissionSet.Name LIKE '%Voice%' OR PermissionSet.Label LIKE '%Contact Center%')" --target-org <alias>
```

**Fix:**
```bash
# Assign Voice permission set to agent runtime user
sf data create record --sobject PermissionSetAssignment --values "PermissionSetId=<voice_perm_set_id> AssigneeId=<agent_user_id>" --target-org <alias>
```

**Common permission set IDs:**
- `SDO_Service_All_Voice`
- `SDO_Service_SCV_Access`
- `Agentforce Contact Center Rep`

#### 2. Agent Not Enabled on Voice Channel (5% of cases)
**Symptom:** Agent works on Case/Messaging, not Voice

**Check:**
- Agent Builder → [Agent Name] → **Channels** tab
- Verify **Voice** is in the enabled list
- Check if there's a Voice-specific eligibility flow

**Fix:** Enable Voice channel in Agent Builder

#### 3. Omni-Channel Routing Not Configured (3% of cases)
**Symptom:** Voice call connects, but agent never activates

**Check:**
```bash
# Verify Omni-Channel queue exists
sf data query --query "SELECT Id, DeveloperName, QueueId FROM ServiceChannel WHERE IsActive = true" --target-org <alias>
```

**Required Components:**
- **Inbound Routing Flow** — routes incoming calls to queue
- **Escalation Flow** (for Agentforce Voice) — hands off AI → human
- **Queue** — agent must be assigned and logged into Omni-Channel

**Common mistake:** Queue exists but agent isn't logged into Omni-Channel with Phone presence.

#### 4. VoiceCall Record Not Creating (1% of cases)
**Symptom:** Call happens but no VoiceCall record

**Check:**
```bash
sf data query --query "SELECT Id, CallStartDateTime, FromPhoneNumber, ToPhoneNumber FROM VoiceCall ORDER BY CreatedDate DESC LIMIT 5" --target-org <alias>
```

**If 0 records:** Telephony adapter issue (Contact Center → Settings → check connection status)

#### 5. Action Execution Failure (<1% of cases)
**Symptom:** Agent activates, but specific actions fail with generic error

**Root Causes:**
- Action uses `ContactId` (Case-only variable) → null on Voice
- Agent runtime user missing FLS on custom fields
- Action tries to write to read-only objects

**Debug:** Get session ID from VoiceCall record, then:
```bash
sf data query --query "SELECT Id, ErrorMessage__c, ErrorType__c, RequestData__c FROM AiAgentSession__dll WHERE SessionId__c = '<session_id>'" --target-org <alias> --api-version 61.0
```

---

## Voice vs Case vs Messaging (SRA Differences)

| Requirement | Case | Messaging (MIAW/ECv2) | Voice |
|------------|------|----------------------|-------|
| **Context variable for record** | `ContactId` ✅ | `currentRecordId` (→ MessagingSession Id) | `currentRecordId` (→ VoiceCall Id) |
| **Contact resolution** | Direct via `ContactId` | Apex: `MessagingSession.EndUserContactId` | Apex: `VoiceCall.RelatedRecordId` or participant lookup |
| **Required perm sets (agent user)** | Base Agentforce perms | Base + `AgentMessagingAccess` | Base + `Service Cloud Voice User` |
| **Channel config** | Omni-Channel routing to queue | Embedded Service + Messaging Channel + Eligibility Flow | Voice Channel + Contact Center config |
| **Transcript access** | Case Comments / Feed | Conversation Entries (needs messaging access perm) | VoiceCall transcript (ConversationEntry or Transcript__c) |
| **Agent activation trigger** | Case assigned to agent-enabled queue | Customer sends message → eligibility flow → agent session | Call routed → IVR/flow hands to agent |
| **CLT rendering** | Service Console (standard) | Embedded chat widget + Service Console | Service Console (during/after call) |
| **Common silent failure** | Works fine (fewest moving parts) | `ContactId` returns null (Case-only variable) | Voice perms not assigned, transcript not accessible |

---

## Troubleshooting Playbook

### Scenario 1: "Works on Case, not on Voice"
**Diagnosis:**
1. Check if agent runtime user has Voice permissions
2. Check if actions use `ContactId` (should be `currentRecordId`)
3. Verify Voice channel enabled in Agent Builder

**Most likely:** Missing Voice permission set on agent runtime user.

### Scenario 2: "Voice call connects, but no agent activation"
**Diagnosis:**
1. Check Omni-Channel routing (is agent logged in with Phone presence?)
2. Check if Voice queue is linked to agent in Agent Builder
3. Check if inbound routing flow is configured

**Most likely:** Omni-Channel flow not routing to agent-enabled queue.

### Scenario 3: "Agent activates but shows generic error immediately"
**Diagnosis:**
1. Get session ID from VoiceCall record
2. Query `AiAgentSession__dll` for error details
3. Check agent runtime user object/field permissions

**Most likely:** Agent runtime user missing object access or FLS.

### Scenario 4: "Agent works intermittently on Voice"
**Diagnosis:**
1. Check for race conditions (VoiceCall record not created yet?)
2. Check Omni-Channel flow delays
3. Check if Contact matching is failing (RelatedRecordId is null)

**Most likely:** Contact matching failing → RelatedRecordId null → actions can't resolve customer.

---

## BYOT (Amazon Connect) Setup

### When to Use
- Customer requires Amazon Connect (existing contract, specific features)
- GovCloud deployments (Amazon-bundled PCC SKU not available)
- Multi-channel contact center (Amazon handles routing, Salesforce handles CRM)

### Setup Runbook
**Document:** "Partner Contact Center Amazon BYOT Run Book" (Andy Cather, July 2026)
- Posted in `#pen-pastries-n-pantry-picks` (Slack message 1784133242.316869)
- Covers both AWS Console and CLI paths
- Labels steps as "Claude" (automatable) or "Human" (browser-only)

### Key Differences from Native Voice
| Aspect | Native Voice | BYOT (Amazon Connect) |
|--------|-------------|----------------------|
| **Setup complexity** | ~30 min automated | Manual, cross-console (AWS + SFDC) |
| **Phone number provisioning** | Salesforce native | AWS Connect |
| **Telephony adapter** | Salesforce-managed | AWS integration |
| **Licensing** | Salesforce Voice SKU | Partner Contact Center SKU |
| **Typical use case** | Net-new, Salesforce-native deployments | Existing AWS footprint, GovCloud |

---

## Key Resources

### Documentation
- **Native Voice Setup Guide:** https://docs.google.com/document/d/1CREbnKIvxp9Fi2DOcWKsw3_8eDrQ9aySsPgKMcswSpY/edit
- **Voice Setup Q-Brix:** https://www.solutionswork.space/content/post/kA0Ka0000024t3GKAQ/salesforce-voice-sdo
- **Voice Implementation Guide (Help):** https://help.salesforce.com/s/articleView?id=service.voice_intro.htm

### Slack Channels
- `#serviceplansvoice-slack-agentforce` — Voice SRA engineering
- `#voice-plans` — Voice planning and architecture
- `#gps-bb-contact-center` — GPS Contact Center discussions
- `#technical-partner-contact-center` — Partner integrations (BYOT)
- `#csg-emea-voice-community` — EMEA Voice community
- `#q-branch-sdo` — SDO releases and Voice setup issues

### Key People (from Slack research)
- **Andy Cather** (WAR5LDG5S) — BYOT runbook author, GPS Voice SME
- **Neil Armstrong** (W012TTQDDF0) — Contact Center enablement lead
- **Ashish Seth** (U085RJ2215E) — Voice product leadership
- **Srikanth Subramanian** (U0825NDAN2G) — Voice engineering leadership
- **Liz Jarvis** (U01GM5LT5BK) — SDO Voice setup support (COE Demos)

---

## Launch Timeline & Stats

### GA: February 2026 (Spring '26 Release)
- **SDO Availability:** 2/21/26+
- **Native Voice:** GA (Agentforce Contact Center)
- **Agentforce Voice (AI agent on voice):** Beta → GA in 264

### Performance (as of July 2026)
From Kishan Chetan post (Slack 1782925524.109839):
- **Agentforce Contact Center:** 800+ deals closed (80+ native CCaaS), $287M PG YTD
- **Agentforce Voice:** 45 customers live, 392k production calls in last 30 days
- **Global Rollout:** Dynamic Voice Routing GA in UK, EU, ANZ (July 2026)
- **SignalWire → FreeSWITCH Migration:** Complete (zero call drops, $800K/year savings)

### Recent Enhancements (Summer 2026)
- Workforce Engagement (WFM + QM) in AFCC Plus SKU
- Metered telephony billing (per-minute tracking)
- Sub-second latency for IVR play prompt
- Number porting, outbound engagement, payment integration

---

## Common Gotchas (From Field Feedback)

### 1. "User doesn't show in Contact Center node"
**Cause:** Missing permission sets OR user already assigned to another call center
**Fix:** Assign `Agentforce Contact Center Rep` perm set, verify not in another Contact Center

### 2. "Screen pop not working on inbound call"
**Cause:** Omni-Channel flow not configured OR agent not logged into Phone presence
**Fix:** Build Omni-Channel flow → route to queue → ensure agent is logged in

### 3. "Qbrix fails to install"
**Causes:**
- Dependent brix `QBrix-1-xDO-Service-Base` requires `Customer Service Incident Management` enabled
- Messaging channel conflict with existing `HiddenPrechatUserId` variable
**Fix:** Enable CSIM in Setup → install base brix first → then Voice brix

### 4. "Intermittent screen pop delays"
**Cause:** Too many cases in Omni-Channel queue (Service Insights data generation)
**Workaround:** Move non-voice cases to user ownership (not queue ownership)

### 5. "SDO Voice setup breaks existing Voice config"
**Warning from Andy Cather:** Do NOT add native voice to an existing Voice org. Spin fresh SDO.
**Reason:** License conflicts, Contact Center overlaps, routing flow collisions.

---

## Example Usage

### Question: Agent runtime user permissions
```
/agentforce-voice-expert What permissions does the SRA agent runtime user need for Voice?
```
→ Returns: Base SRA perms + Voice-specific (`Service Cloud Voice User`), diagnostic queries, assignment command

### Question: "Unable to complete request" error
```
/agentforce-voice-expert Why am I getting "unable to complete your request" on Voice SRA?
```
→ Returns: 5-step diagnostic checklist, most common causes, session trace query

### Question: Voice vs Case differences
```
/agentforce-voice-expert How is Voice SRA different from Case SRA?
```
→ Returns: Channel comparison table, context variable differences, Contact resolution patterns

### Question: BYOT setup
```
/agentforce-voice-expert How do I set up Voice with Amazon Connect?
```
→ Returns: BYOT runbook link, key differences from native, typical use cases

---

## Changelog

| Date | Change |
|------|--------|
| 2026-07-23 | Initial skill creation — consolidated native voice setup, Voice SRA troubleshooting, channel differences, BYOT patterns from Slack research and field feedback |

---

## Related Skills

- **`sra-expert`** — General SRA knowledge (plan generation, knowledge grounding, CVS account)
- **`sra-engineer`** — SRA architecture, development setup, debugging workflows
- **`sra-setup-debug`** — Automated SRA setup diagnostics (runs against target org)
- **`sra-agent-debugger`** — Agent Script/NGA debugging, trace interpretation

**When to use this skill vs others:**
- **Use `agentforce-voice-expert`** for: Voice channel setup, Voice SRA config, "unable to complete request" errors, native telephony vs BYOT
- **Use `sra-expert`** for: General SRA product questions, roadmap, plan generation, CVS account
- **Use `sra-engineer`** for: Code architecture, development setup, Jupyter testing
- **Use `sra-setup-debug`** for: Running live diagnostics against an org (permissions, actions, knowledge)
