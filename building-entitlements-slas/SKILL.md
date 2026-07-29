---
name: building-entitlements-slas
description: "Build a complete Salesforce Entitlement Management / SLA stack end-to-end and deploy ALL of it as metadata + data via the CLI — Business Hours, Milestone Types, breach/violation actions (Workflow Field Updates), the Entitlement Process (with milestones + time triggers), and the Entitlement record that links an Account to the process. Corrects the common false belief that EntitlementProcess is Setup-UI-only: it IS deployable metadata. Trigger whenever the user mentions entitlement process, entitlement record, SLA, SLA process, milestone, milestone type, milestone breach/violation action, service level agreement, case SLA, MilestoneType, or asks to create/deploy/replicate any of these (especially across multiple orgs). Ships verified, deployable XML for every artifact in assets/."
compatibility: "Salesforce CLI (sf) v2+; Service Cloud / Entitlement Management enabled; EntitlementProcess, MilestoneType, Workflow (field update) are Metadata API types; Entitlement + BusinessHours are data objects; runtime process object is SlaProcess"
metadata:
  version: "1.0"
  last_updated: "2026-07-28"
---

# Building Entitlements & SLAs (Milestones, Breach Actions, Entitlement Processes)

## What this skill is for

Entitlement Management is how Salesforce enforces **Service Level Agreements (SLAs)** on Cases. The full stack is five layers. This skill builds and **deploys all of them from the CLI** — no Setup UI clicking required.

```
Business Hours            (WHEN the SLA clock runs — e.g. 24/7, or 9-5 M-F)
   ▲ referenced by
Milestone Type            (a NAMED, reusable target — "First Response", "Case Closed")
   ▲ referenced by name inside
Entitlement Process       (SObjectType=Case; ordered milestones, each with
   │                       minutesToComplete + timeTriggers = the SLA definition)
   │  each timeTrigger fires ▼
Breach / Violation Action (a Workflow Field Update run when a milestone is
   │                       missed — e.g. set a "SLA Compliant" checkbox to false)
   ▼ instantiated per-customer by
Entitlement record        (links an Account [+ optionally Contact/Asset/Product]
                           to the SlaProcess; this is what Cases attach to)
```

**Runtime vs. metadata name — the #1 gotcha:** the metadata type you deploy is **`EntitlementProcess`**. At runtime the SAME thing is the **`SlaProcess`** object (that is what `Entitlement.SlaProcessId` points to, and what you SOQL-query). They are the same process, two names.

## ⚠️ Myth to unlearn

**EntitlementProcess is NOT "Setup-UI-only" / API-blocked.** An earlier attempt in this project wrongly concluded that and only produced a runbook. That was wrong. `EntitlementProcess` is a first-class **Metadata API type** — author the `.entitlementProcess-meta.xml`, `sf project deploy start`, done. Everything in this skill deploys headless.

## Prerequisites (check these first, in order)

1. **Target org set / confirmed.** This project uses explicit `--target-org <alias>` on every command (default is `MainSDOSean`, which is usually NOT what you want). See the `switching-org` skill.
2. **Entitlement Management is enabled** in the org (Setup → Entitlement Settings). SDO / Service demo orgs already have it on. If `SlaProcess` / `Entitlement` don't exist as objects, it's off.
3. **The `Case` object exists** (always true) — EntitlementProcess is almost always `SObjectType=Case`.
4. **You know what field the breach action sets.** Demo/SDO orgs ship a standard checkbox `SDO_Service_SLA_Compliant__c` on Case (this is what the verified example toggles to `false`). If the org doesn't have it, either pick an existing field or create one first (`generating-custom-field` skill) and deploy it BEFORE the workflow field update.

## The CLI launcher (this environment)

`sf` is not on PATH here — always launch through node. Wrap in a shell function and always pass `--json`:

```bash
SF() { "/c/Program Files/sf/client/bin/node.exe" --no-deprecation "/c/Program Files/sf/client/bin/run.js" "$@"; }
```

Parse JSON with a `node -e` filter (do NOT pipe through `jq`). **Deploy/retrieve commands must run from inside the DX project root** — if you generated the project into a `proj/` subdir, `cd` into it via a subshell: `(cd C:/tmp/ent/proj && SF project deploy start ...)`.

---

## Build order (dependencies flow downward — deploy in THIS order)

Deploy bottom-up so every reference resolves. You can bundle several types into one deploy, but a milestone referenced by the process must exist, and a field update referenced by a time-trigger must exist, at deploy time.

| # | Artifact | Metadata type | File | Notes |
|---|---|---|---|---|
| 1 | Business Hours | (usually pre-exists) | — | Query the default; only create if you need a custom calendar |
| 2 | Milestone Type(s) | `MilestoneType` | `<Label>.milestoneType-meta.xml` | One per named target. Reusable across processes |
| 3 | Breach/violation field | `CustomField` | — | Only if the target field doesn't exist yet |
| 4 | Breach action | `Workflow` (field update) | `<Object>.workflow-meta.xml` | The action a missed milestone fires |
| 5 | Entitlement Process | `EntitlementProcess` | `<Name>.entitlementProcess-meta.xml` | Milestones + time triggers live here |
| 6 | Entitlement record | `Entitlement` (data) | — via `sf data create record` / Apex | Links Account → SlaProcess |

In practice steps 2 + 4 + 5 can go in a single `sf project deploy start` (deploy resolves intra-package references). Step 6 is data, done after the process is Active.

---

## 1. Business Hours

Almost always reuse the org default. Query it — do **not** hardcode an Id across orgs (Ids are per-org).

```bash
SF data query -q "SELECT Id, Name, IsDefault, IsActive FROM BusinessHours WHERE IsDefault=true AND IsActive=true LIMIT 1" --target-org <ALIAS> --json
```

> **Do not** try to retrieve `BusinessHours` as a member of an EntitlementProcess manifest — it errors with `Missing metadata type definition in registry for id 'BusinessHours'`. Query it via SOQL and reference the Id only on the **Entitlement record** (step 6). The EntitlementProcess XML itself does not name business hours; the process uses whatever BH the Entitlement/Case carries, and `useCriteriaStartTime`/`entryStartDateField` drive the clock.

To create a custom calendar, use metadata type `BusinessHours` in a normal deploy (rarely needed for demos).

---

## 2. Milestone Type

A **reusable, named** target. The Entitlement Process references it **by label**, so the label must match exactly. The label may contain spaces; the file name IS the label.

`assets/First Response Gold.milestoneType-meta.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<MilestoneType xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>First agent response target for Gold-tier customers.</description>
    <recurrenceType>none</recurrenceType>
</MilestoneType>
```

- The file name (minus `.milestoneType-meta.xml`) is the milestone's label — e.g. `Case Closed Gold.milestoneType-meta.xml`.
- Milestone Types are **org-wide + reusable** — many entitlement processes can share one. If it already exists (query below), do NOT redeploy; just reference it.
- **Milestones are independent of each other.** Each milestone on a Case runs on its own timer regardless of what the others are doing — completing one has no effect on another.

### Recurrence types — ⚠️ the metadata enum tokens are NOT the intuitive words

`recurrenceType` controls whether/how a milestone repeats on a Case. There are exactly three, and the **Metadata API deploy tokens are the same odd tokens the SOQL picklist uses** — NOT `None`/`Recurring`/`Independent`. Deploying `<recurrenceType>Recurring</recurrenceType>` **fails** with `'Recurring' is not a valid value for the enum 'MilestoneTypeRecurrenceType'` (verified 2026-07-28). Use these exact values:

| Setup UI label | Deploy token (`recurrenceType`) | SOQL `RecurrenceType` value | Behavior |
|---|---|---|---|
| **No Occurrence** (Standard, default) | `none` | `none` | Happens once. Complete it → done, never comes back. |
| **Independent** | `recursIndependently` | `recursIndependently` | Recurs; **every completion resets the timer fresh**, as long as the case still meets criteria. Use for *"respond within 2 hours of each customer message"* — the clock restarts each time. |
| **Sequential** | `recursChained` | `recursChained` | Recurs on a **fixed rhythm**. Finish early → the next window still doesn't start until the previous window closes. Finish late → the clock restarts from the late completion. Use for *"check in with the customer every 24 hours"* — can't be gamed by finishing early. |

Omitting `<recurrenceType>` entirely = `none` (No Occurrence), which is why the SOQL query shows blank/`none` for un-set milestones.

- **Criteria** is a *separate* concept, not a recurrence type: a milestone with `<milestoneCriteriaFilterItems>` (or a criteria expression) only applies to Cases that match — no match, no milestone. It can combine with any recurrence type.

Sequential example (`assets/Reoccurring Response every within 48 hours Gold.milestoneType-meta.xml`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<MilestoneType xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Gold Banking customer: maintain a 48-hour response rhythm until the case is resolved.</description>
    <recurrenceType>recursChained</recurrenceType>
</MilestoneType>
```

Check what already exists:
```bash
SF data query -q "SELECT Id, Name, RecurrenceType FROM MilestoneType" --target-org <ALIAS> --json
```

---

## 3 & 4. Breach / Violation Action (Workflow Field Update)

A milestone "violation" is modeled as a **time trigger inside the milestone** (step 5) that fires an **action**. The most common action is a **Workflow Field Update** on Case. The field update is standard `Workflow` metadata, filed per object.

Verified example — `assets/Case.workflow-meta.xml` (sets the SDO SLA-compliant checkbox to false when a milestone is breached):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
    <fieldUpdates>
        <fullName>Set_SLA_Not_Compliant</fullName>
        <name>Set SLA Not Compliant</name>
        <field>SDO_Service_SLA_Compliant__c</field>
        <operation>Literal</operation>
        <literalValue>false</literalValue>
        <protected>false</protected>
        <notifyAssignee>false</notifyAssignee>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>
</Workflow>
```

Key points:
- `<fullName>` is the API name (**no spaces**); `<name>` is the label (spaces OK). The EntitlementProcess time-trigger references the **API name** (`Set_SLA_Not_Compliant`).
- `operation` = `Literal` + `literalValue` for a constant; use `Formula`+`formula` or `LookupValue` for dynamic values.
- `field` must exist on the object and be writable. Create + FLS it first if missing.
- Other valid milestone action types besides `FieldUpdate`: `EmailAlert`, `FlowAction`, `OutboundMessage`, `Task` — same `<actions>` shape, different `<type>`.
- **Deploy `Workflow` before the EntitlementProcess** so the time-trigger reference resolves. A single deploy that contains both also works (same package).

---

## 5. Entitlement Process (the SLA definition itself)

This is the core artifact. `SObjectType=Case`, one or more ordered `<milestones>`, each with `minutesToComplete` and (optionally) `timeTriggers` that fire actions on breach.

**VERIFIED, DEPLOYED** example (`assets/EntitlementProcess.entitlementProcess-meta.xml` is a ready-to-edit copy). The file name is the process name and may contain spaces — e.g. `Gold Banking customer.entitlementProcess-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EntitlementProcess xmlns="http://soap.sforce.com/2006/04/metadata">
    <SObjectType>Case</SObjectType>
    <active>true</active>
    <description>Gold Banking customer SLA process: prioritized first response, recurring updates, and case-closure targets. Violations set the case SLA to not compliant.</description>
    <entryStartDateField>Case.CreatedDate</entryStartDateField>
    <exitCriteriaFilterItems>
        <field>Case.IsClosed</field>
        <operation>equals</operation>
        <value>true</value>
    </exitCriteriaFilterItems>
    <milestones>
        <milestoneName>First Response Gold</milestoneName>
        <minutesToComplete>1440</minutesToComplete>
        <timeTriggers>
            <actions>
                <name>Set_SLA_Not_Compliant</name>
                <type>FieldUpdate</type>
            </actions>
            <timeLength>0</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
        </timeTriggers>
        <useCriteriaStartTime>false</useCriteriaStartTime>
    </milestones>
    <milestones>
        <milestoneName>Reoccurring Response every within 48 hours Gold</milestoneName>
        <minutesToComplete>2880</minutesToComplete>
        <timeTriggers>
            <actions>
                <name>Set_SLA_Not_Compliant</name>
                <type>FieldUpdate</type>
            </actions>
            <timeLength>0</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
        </timeTriggers>
        <useCriteriaStartTime>false</useCriteriaStartTime>
    </milestones>
    <milestones>
        <milestoneName>Case Closed Gold</milestoneName>
        <minutesToComplete>7200</minutesToComplete>
        <timeTriggers>
            <actions>
                <name>Set_SLA_Not_Compliant</name>
                <type>FieldUpdate</type>
            </actions>
            <timeLength>0</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
        </timeTriggers>
        <useCriteriaStartTime>false</useCriteriaStartTime>
    </milestones>
</EntitlementProcess>
```

### Field-by-field

| Element | Meaning |
|---|---|
| `SObjectType` | `Case` (Entitlement processes run on Cases) |
| `active` | `true` to deploy it live. **A process cannot be edited via metadata once it has instances** — see versioning gotcha below |
| `description` | Free text |
| `entryStartDateField` | When the SLA clock starts, e.g. `Case.CreatedDate` |
| `exitCriteriaFilterItems` | When a Case LEAVES the process (here: `Case.IsClosed = true`). Alternatively use `exitCriteriaBooleanFilter` + numbered filter items for AND/OR logic |
| `milestones` | Ordered list. Each is a target the Case must hit |
| `milestones.milestoneName` | **MUST exactly match a MilestoneType label** (step 2) |
| `milestones.minutesToComplete` | SLA target in minutes (1440 = 24h, 2880 = 48h, 7200 = 5 days) |
| `milestones.timeTriggers` | Actions fired relative to the milestone target time |
| `timeTriggers.timeLength` + `workflowTimeTriggerUnit` | **`0` Minutes = fire exactly at the target** → i.e. **at breach** if the milestone is still incomplete. Positive = after; the platform also supports pre-breach warnings |
| `timeTriggers.actions.name` | API name of the field update / alert / flow (`Set_SLA_Not_Compliant`) |
| `timeTriggers.actions.type` | `FieldUpdate` \| `EmailAlert` \| `FlowAction` \| `OutboundMessage` \| `Task` |
| `useCriteriaStartTime` | `false` unless the milestone uses a milestone-criteria-based start |

> **Optional milestone gating:** a `<milestoneCriteriaFilterItems>` / `<businessHours>` block per milestone lets a milestone apply only to certain Cases or use a specific calendar. Omitted here (all milestones always apply, inheriting the Entitlement's business hours).

### ⚠️ Versioning gotcha (why an EDIT deploy can fail)

A **standard** (fresh) entitlement process deploys with no version elements — exactly as above. But once a process is **in use** (has Entitlements/Cases against it), Salesforce treats it as **versioned** and a plain re-deploy of the same name may be rejected or silently create issues. If you must change a live process:
- add `<isVersionDefault>`, `<versionMaster>`, `<versionNumber>`, `<versionNotes>` and deploy a NEW version, **or**
- for demo orgs, delete the Entitlement records first, redeploy the process, then recreate the Entitlements.

For a brand-new process (the common case), the simple un-versioned XML above is correct.

---

## 6. Entitlement record (links Account → process)

Created as **data** (not metadata), after the process is Active. This is what Cases actually attach to. Resolve every Id per-org first.

```bash
SF() { "/c/Program Files/sf/client/bin/node.exe" --no-deprecation "/c/Program Files/sf/client/bin/run.js" "$@"; }

# a) runtime process Id — query SlaProcess (NOT EntitlementProcess), which has NO
#    VersionNumber / IsVersionDefault columns; SELECT only Id, Name, IsActive.
SF data query -q "SELECT Id, Name, IsActive FROM SlaProcess WHERE Name='Gold Banking customer'" --target-org <ALIAS> --json
# b) default business hours (step 1)
# c) the Account to entitle
SF data query -q "SELECT Id, Name FROM Account WHERE Name='Lauren Bailey' LIMIT 1" --target-org <ALIAS> --json

# create it
SF data create record --sobject Entitlement \
  --values "Name='Gold banking customer entitlement' AccountId=<ACCT_ID> SlaProcessId=<SLAPROCESS_ID> BusinessHoursId=<BH_ID> StartDate=2026-07-28" \
  --target-org <ALIAS> --json
```

Entitlement key fields:
| Field | Notes |
|---|---|
| `Name` | Display name of the entitlement |
| `AccountId` | Required — the entitled account |
| `SlaProcessId` | The `SlaProcess` Id from (a) — this is the link to your deployed process |
| `BusinessHoursId` | Usually the org default |
| `StartDate` | When entitlement coverage begins (date, e.g. `2026-07-28`) |
| `EndDate` | Optional coverage end |
| `ContactId` / `AssetId` / `Product2Id` | Optional narrower scoping |
| `Type` | Optional picklist (Phone Support, Web Support, …) |

For many records or richer logic, use anonymous Apex DML instead of `data create record`.

---

## Deploying it all

Author steps 2, 4, 5 into one DX project, then a single deploy:

```bash
SF() { "/c/Program Files/sf/client/bin/node.exe" --no-deprecation "/c/Program Files/sf/client/bin/run.js" "$@"; }
(cd C:/tmp/ent/proj && SF project deploy start \
  --metadata "MilestoneType" "Workflow:Case" "EntitlementProcess:Gold Banking customer" \
  --target-org <ALIAS> --json)
```

Deploy to a **second org** by repeating with a different `--target-org` — the metadata is fully portable (unlike routing flows, entitlement metadata has **no hardcoded Ids**). Only step 6 (the Entitlement record) needs per-org Ids re-resolved.

---

## Verification checklist

```bash
SF() { "/c/Program Files/sf/client/bin/node.exe" --no-deprecation "/c/Program Files/sf/client/bin/run.js" "$@"; }
# process is live
SF data query -q "SELECT Id, Name, IsActive FROM SlaProcess WHERE Name='Gold Banking customer'" --target-org <ALIAS> --json
# milestones attached to it (note: SlaProcessMilestone column names vary by org/version;
# if a SELECT errors on a column, drop it — the deploy result is the real confirmation)
SF data query -q "SELECT Id, MilestoneType.Name FROM SlaProcessMilestone WHERE SlaProcess.Name='Gold Banking customer'" --target-org <ALIAS> --json
# entitlement wired up
SF data query -q "SELECT Id, Name, Account.Name, SlaProcess.Name, BusinessHours.Name, StartDate FROM Entitlement WHERE Name='Gold banking customer entitlement'" --target-org <ALIAS> --json
```

- [ ] `SlaProcess` exists and `IsActive=true`
- [ ] Milestone Types exist (query `MilestoneType`)
- [ ] Field update `Case.Set_SLA_Not_Compliant` exists (retrieve `Workflow:Case`, or Setup → Field Updates)
- [ ] Entitlement record links the right Account → the SlaProcess → business hours
- [ ] (Optional live test) create a Case, set `EntitlementId`, watch milestones appear on the Case and the breach action fire when a target passes

---

## Gotchas (hard-won)

| Gotcha | Reality |
|---|---|
| "EntitlementProcess must be built in Setup / it's API-blocked" | **False.** It's a deployable Metadata API type. Deploy it. |
| Confusing `EntitlementProcess` (metadata) with `SlaProcess` (runtime object) | Same thing, two names. Query `SlaProcess`; deploy `EntitlementProcess`. |
| `SELECT VersionNumber / IsVersionDefault FROM SlaProcess` | Those columns don't exist on `SlaProcess`. Use `Id, Name, IsActive`. |
| Adding `BusinessHours` to the EntitlementProcess manifest | Errors: `Missing metadata type definition in registry for id 'BusinessHours'`. Query BH via SOQL; reference its Id only on the Entitlement record. |
| `recurrenceType` set to `Recurring`/`None`/`Independent` (the intuitive words) | Deploy fails: `not a valid value for the enum 'MilestoneTypeRecurrenceType'`. The tokens are `none` / `recursIndependently` / `recursChained` (Sequential). See recurrence table in §2. |
| Milestone `milestoneName` ≠ MilestoneType label | Must match **exactly** (case + spaces). Mismatch = deploy/runtime failure. |
| Time-trigger `actions.name` ≠ field-update API name | Must match the `<fullName>` of the Workflow field update (no spaces). |
| `timeLength` confusion | `0` + `Minutes` fires **at the target** (= breach). Positive fires after; use for follow-up escalations. |
| Editing a process that already has instances | Versioned → plain re-deploy may fail. Add version elements or clear Entitlements first (see §5). |
| Field update targets a nonexistent/read-only field | Create + FLS the field and deploy it **before** the Workflow. |
| Deploy run from wrong dir | "does not contain a valid Salesforce DX project" — `cd` into the actual project root (often a `proj/` subdir) via subshell. |
| Hardcoding Ids across orgs | Metadata is portable (no Ids). Only the Entitlement **record** (`AccountId`, `SlaProcessId`, `BusinessHoursId`) needs per-org Id resolution. |

---

## Ready-to-edit assets

- `assets/First Response Gold.milestoneType-meta.xml` — MilestoneType template (No Occurrence)
- `assets/Reoccurring Response every within 48 hours Gold.milestoneType-meta.xml` — Sequential (`recursChained`) MilestoneType (verified)
- `assets/Case.workflow-meta.xml` — breach-action field update (verified)
- `assets/Gold Banking customer.entitlementProcess-meta.xml` — full 3-milestone process (verified, deployed to two orgs)
- `assets/create-entitlement.sh` — resolve Ids + create the Entitlement record

Copy an asset into a DX project's matching folder (`milestoneTypes/`, `workflows/`, `entitlementProcesses/`), swap names/minutes/fields, deploy in the order above.
