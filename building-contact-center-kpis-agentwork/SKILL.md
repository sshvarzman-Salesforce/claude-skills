---
name: building-contact-center-kpis-agentwork
description: "Build accurate contact-center KPIs (Speed-to-Answer / ASA, Calls-or-Chats-Abandoned, Accepted-by-a-genuine-HUMAN) on VoiceCall and MessagingSession, driven off the AgentWork object. Covers the custom fields (Entered_Queue_Timestamp__c, Accepted_By_Human_Timestamp__c, Abandoned__c, Speed_To_Answer_Seconds__c formula), the record-triggered AgentWork flow that stamps them, and — the whole reason this is hard — the DOUBLE-ACCEPT problem: an escalated conversation produces TWO accepted AgentWork rows (first the bot/ASA/Omni leg as an Automated Process user, then the real human after escalation), so you must gate the human stamp on UserType='Standard' AND Profile.Name != 'Einstein Agent User'. Includes the acceptor-User-lookup pattern and the auto-store-vs-queriedFields runtime-fault gotcha. Use whenever asked to compute abandoned/accepted-by-human/speed-to-answer, stamp KPI timestamps from AgentWork, or tell a real human accept apart from a bot accept."
metadata:
  version: "1.0"
  last_updated: "2026-08-13"
---

# Contact-Center KPIs from the AgentWork Object

## What this skill is for

Reliable per-conversation KPIs — **Speed to Answer (ASA)**, **Abandoned**, **Accepted by a genuine human** — on `VoiceCall` and `MessagingSession`. The timing truth lives on **`AgentWork`** (Omni-Channel's routable-work record), so the KPIs are stamped by a **record-triggered flow on AgentWork** that writes back to the parent conversation. The single hard part is telling a **real human accept** apart from a **bot/ASA/Omni accept** — get that wrong and every escalated conversation looks "answered by a human instantly."

```
Conversation escalates / routes  → AgentWork row created & accepted
   AgentWork(after save)  → is this a genuine HUMAN acceptor? (UserType=Standard AND Profile != Einstein Agent User)
        yes → stamp parent.Accepted_By_Human_Timestamp__c = AgentWork.AcceptDateTime
   Escalation flow (separate)  → stamped parent.Entered_Queue_Timestamp__c at handoff
   Abandonment flow (separate) → conversation ended, still queue-owned, never human-accepted → Abandoned__c = true
   Speed_To_Answer_Seconds__c  = (Accepted_By_Human - Entered_Queue) formula
```

## AgentWork essentials
- **`AgentWork.WorkItemId`** = the routed record's Id. Its 3-char key prefix identifies the object: **`0LQ` = VoiceCall**, **`0Mw` = MessagingSession** (confirm prefixes in-org; use `LEFT(WorkItemId,3)`).
- **`AgentWork.UserId`** = who the work was accepted by. **`AgentWork.AcceptDateTime`** = when.
- A record-triggered AgentWork flow's `$Record` does **not** expose `$Record.User.UserType` / `$Record.User.Profile.Name`. You must **Get Records on User** by `$Record.UserId` to read the acceptor's identity.
- Most AgentWork fields are **not updateable** (e.g. `AcceptDateTime`, `AssignedDateTime`). To force a re-fire in testing, update an updateable field like `TargetAcceptDateTime` (find updateable fields via `sf sobject describe --sobject AgentWork` and filter `f.updateable`).

---

## THE core problem: the double-accept (why UserType alone is not enough)

When a call/chat is escalated from an ASA to a human, Omni creates **two** accepted `AgentWork` rows on the **same `WorkItemId`**:

1. **First** — `UserId` = the **Automated Process** user (the bot/ASA/Omni leg that first "accepted" the routed work). `UserType = AutomatedProcess`, `Profile = null`.
2. **Then** — `UserId` = the **real human** after escalation. `UserType = Standard`.

Naively stamping "accepted by human" on the first accepted row is a **false positive** — it makes speed-to-answer look near-zero and marks bot-handled work as human-handled.

**Why `UserType = 'Standard'` alone is insufficient:** the **Einstein Agent User** (the ASA's own identity) is also `UserType = Standard` — identical to a real human on that axis. What distinguishes it is the **Profile**: ASA users carry Profile **`Einstein Agent User`**.

**The genuine-human gate (both conditions, AND):**
```
Get_Acceptor.UserType        EqualTo     'Standard'                 ← excludes AutomatedProcess + Integration/CloudIntegrationUser types
AND
Get_Acceptor.Profile.Name    NotEqualTo  'Einstein Agent User'      ← excludes the ASA identity (which IS Standard)
```
`UserType = 'Standard'` already excludes every automated/integration UserType, so you do **not** need extra `Contains 'Integration'` / `!= 'Salesforce API Only…'` conditions — adding them (especially with `Contains` under `and` logic) tends to invert the logic and break the rule. Two conditions, nothing more.

---

## The flow: `AgentWork_KPI_Stamp` (record-triggered on AgentWork)

`AutoLaunchedFlow`, `triggerType=RecordAfterSave`, `recordTriggerType=CreateAndUpdate`, `runInMode=SystemModeWithoutSharing`, `status=Active`.

```
Start (AgentWork, after save, create+update)
  → Decision Determine_Outcome
        rule Human_Accepted:  $Record.AcceptDateTime  IsNull false   → Get_Acceptor
        (default: No KPI Change)
  → Get_Acceptor  (recordLookup User, Id = $Record.UserId, getFirstRecordOnly, storeOutputAutomatically)
  → Decision Is_Real_Human
        rule Real_Human_Agent (AND):
            Get_Acceptor.UserType       EqualTo    'Standard'
            Get_Acceptor.Profile.Name   NotEqualTo 'Einstein Agent User'
          → Route_By_Parent_Accept
        (default: Not a Human → end, no stamp)
  → Decision Route_By_Parent_Accept  (on formula WorkItemPrefix = LEFT($Record.WorkItemId,3))
        '0LQ' → Update_VoiceCall_Accept       (VoiceCall)
        '0Mw' → Update_MessagingSession_Accept (MessagingSession)
        (default: Other Parent → end)
  → Update_*  filter Id = {!$Record.WorkItemId},
              set Accepted_By_Human_Timestamp__c = {!$Record.AcceptDateTime}
```

The acceptor lookup — note **no `queriedFields`** (see the gotcha below):
```xml
<recordLookups>
    <name>Get_Acceptor</name>
    <connector><targetReference>Is_Real_Human</targetReference></connector>
    <filters>
        <field>Id</field><operator>EqualTo</operator>
        <value><elementReference>$Record.UserId</elementReference></value>
    </filters>
    <getFirstRecordOnly>true</getFirstRecordOnly>
    <object>User</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

### ⚠️ auto-store lookup + explicit `queriedFields` = runtime fault
On a `storeOutputAutomatically=true` User lookup, adding an explicit `<queriedFields>UserType</queriedFields>` **restricts** the query to only that field. A later cross-object reference (`Get_Acceptor.Profile.Name`) then can't resolve, and the flow throws an **unhandled fault** — and only on the human path (the path that actually reaches the Profile check), so it's easy to miss in a quick bot-only test. **Fix: omit `<queriedFields>` entirely.** Auto-store retrieves every field the flow references, including the traversed `Profile.Name`. (Real fault: `CANNOT_EXECUTE_FLOW_TRIGGER` / "An unhandled fault has occurred".)

### Optional: abandonment on the same AgentWork flow
You can add an abandon path here (terminal AgentWork `Status` + `AcceptDateTime == null` → set parent `Abandoned__c = true`), but the OMERS build keeps abandonment in **separate record-triggered flows on the conversation objects** (below) — cleaner, and they fire on the conversation's own terminal state rather than AgentWork's.

---

## The KPI custom fields (on BOTH VoiceCall and MessagingSession)

| Field | Type | Set by |
|---|---|---|
| `Entered_Queue_Timestamp__c` | DateTime | the **escalation flow** at human-handoff, `{!$Flow.CurrentDateTime}` |
| `Accepted_By_Human_Timestamp__c` | DateTime | the **AgentWork flow**, from `AgentWork.AcceptDateTime` (genuine-human only) |
| `Abandoned__c` | Checkbox (default false) | the **abandonment flow** (entered queue, ended, never human-accepted) |
| `Speed_To_Answer_Seconds__c` | Formula (Number) | derived (below) |

**Speed-to-Answer formula** (seconds between queue entry and human accept; blank until both exist):
```
IF(
  AND(NOT(ISBLANK(Accepted_By_Human_Timestamp__c)), NOT(ISBLANK(Entered_Queue_Timestamp__c))),
  (Accepted_By_Human_Timestamp__c - Entered_Queue_Timestamp__c) * 86400,
  null
)
```
(DateTime subtraction yields **days**; `* 86400` → seconds.)

**Field standing rules (per the standing demo constraints):**
- FLS **Read + Edit for all internal profiles**; add all four to **every** VoiceCall + MessagingSession page layout.
- Grant object + field access through a permission set with **View All Fields + Read + Edit** (NOT View All, NOT Modify All), assigned to the agent user; include **AgentWork** object Read+Edit and the User object read the flow needs.
- ⚠️ **VoiceCall custom-field FLS is silently ignored** — VoiceCall custom fields are `permissionable=false`, so FLS is a no-op there; **object access** is the real grant and the field is readable by all by default. MessagingSession FLS is real — set it. (Memory: `voicecall-custom-fields-not-permissionable`.)

---

## The abandonment flows (one per conversation object)

Record-triggered on the conversation object itself (`RecordAfterSave`, create+update, `SystemModeWithoutSharing`, Active). Fire when the conversation **ended while still queue-owned and was never accepted by a human**:

**VoiceCall** — rule `Ended_Still_Queue_Owned` (AND):
```
$Record.CallStatus                    EqualTo 'COMPLETED'
$Record.Accepted_By_Human_Timestamp__c IsNull true
$Record.Abandoned__c                   EqualTo false
  → Set_Abandoned (inputReference $Record, set Abandoned__c = true)
```
**MessagingSession** — identical except condition (1) is `$Record.Status EqualTo 'Ended'`.

The `Abandoned__c = false` guard makes it idempotent (won't re-fire once set). Confirm the exact terminal Status strings in-org (`COMPLETED` for VoiceCall CallStatus, `Ended` for MessagingSession Status here).

---

## Deploy & verify

- Deploy fields → perm set → flows (`sf project deploy start --metadata Flow:<name> --json`). A `.flow-meta.xml` with `<status>Active</status>` cuts a **new numbered version and activates it** each deploy, obsoleting the prior.
- Confirm flow Active: `FlowDefinitionView` (regular object, column `IsActive`, **NO** `--use-tooling-api`) and tooling `Flow` (VersionNumber/Status).
- **Live proof on a real double-accept WorkItem:** null the stamp → fire the bot/Automated-Process AgentWork (stamp must stay **null**) → fire the human AgentWork (stamp must populate with `AcceptDateTime`). This is the only test that actually exercises the gate.

## Verification checklist
- All four KPI fields on both objects, on every layout; perm set (View All Fields + Read + Edit, not View/Modify All) assigned to the agent user; AgentWork Read+Edit granted.
- AgentWork flow gates on **both** `UserType='Standard'` **and** `Profile.Name != 'Einstein Agent User'`; `Get_Acceptor` has **no** `queriedFields`.
- Bot accept leaves `Accepted_By_Human_Timestamp__c` null; genuine human accept stamps it.
- Escalation flow stamps `Entered_Queue_Timestamp__c`; `Speed_To_Answer_Seconds__c` computes once both timestamps exist.
- Ended-in-queue-never-accepted conversation → `Abandoned__c = true` (and stays, idempotent).

## Gotchas (hard-won)
- **Double-accept.** Two accepted AgentWork rows per escalated conversation (Automated Process, then human). Gate the stamp or every conversation looks instantly human-answered.
- **Einstein Agent User is `UserType=Standard`.** UserType alone can't exclude the ASA identity — you need the `Profile.Name != 'Einstein Agent User'` condition too.
- **`$Record.User…` isn't available on AgentWork triggers** — do a `Get Records` on User by `$Record.UserId`.
- **auto-store + `queriedFields` = unhandled fault** on the cross-object (`Profile.Name`) reference. Omit `queriedFields`.
- **Two conditions only.** `UserType='Standard'` + `Profile != 'Einstein Agent User'`. Extra integration-user conditions (esp. `Contains` under `and`) invert the logic and break the rule.
- **VoiceCall custom-field FLS is a no-op** (permissionable=false) — object access is the grant. MessagingSession FLS is real.
- **Confirm key prefixes + terminal Status strings in-org** — `0LQ`/`0Mw` and `COMPLETED`/`Ended` are what this build saw; verify before relying on them.
- **DateTime math is in days** — multiply by 86400 for seconds in the speed-to-answer formula.
