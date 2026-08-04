---
name: building-system-context-agent-data-flows
description: Build the backing data flows for an Agentforce Service Agent (ASA) so they read and write records in system context regardless of the agent user's sharing/perms. Covers the read pattern (prompt-template-over-PromptFlow + system-context subflow), the write pattern (autolaunched flow action), and the critical empty-results bug where a PromptFlow silently returns zero rows because it runs as the agent user.
---

# Building System-Context Data Flows for Agents

## What this skill is for

An Agentforce Service Agent (ASA) reaches data through **actions** backed by Flows and Prompt Templates. Those flows run as the **agent user**, whose license and sharing routinely block the records the demo needs to show. The fix — mandated on every build here — is: **every flow that backs an agent action or a prompt template runs in System Context without sharing.** This skill is the exact, verified mechanics for that, including the one bug that silently breaks reads.

Three flow shapes, all `<runInMode>SystemModeWithoutSharing</runInMode>`:

| Shape | processType | Used for | Agent action target |
|---|---|---|---|
| **Read** — thin PromptFlow that calls a system-context subflow | `PromptFlow` (wrapper) + `AutoLaunchedFlow` (subflow) | listing/looking up records for the model to narrate | `generatePromptResponse://<Template>` (the template calls the PromptFlow) |
| **Write** — autolaunched flow invoked directly as an action | `AutoLaunchedFlow` | creating/updating records | `flow://<Flow>` |
| **Verify** — autolaunched flow invoked directly as an action | `AutoLaunchedFlow` | identity check against a record | `flow://<Flow>` |

Verified assets ship in `assets/` — real, deployed, working flows from the ClaimSecure ASA build. Read them; do not reinvent the structure.

---

## ⚠️ THE BUG THAT WILL BITE YOU: PromptFlow can't run system context

**Symptom:** your read action returns **zero rows** even though the records exist and you can query them yourself. The agent says "you have no open claims" when the customer has four.

**Root cause:** A `PromptFlow` (a flow with `<triggerType>Capability</triggerType>`, used as a prompt-template data provider) **CANNOT be set to `SystemModeWithoutSharing`** — the deploy is rejected. It **always runs as the executing user** (the agent user). If the records are owned by someone else (e.g. the seeding admin) and the object OWD is Private / ControlledByParent while the agent user has no ViewAll, the SOQL returns nothing. No error, no fault path — just an empty list the model faithfully reports.

**THE FIX (verified):** Do **not** put the privileged SOQL in the PromptFlow. Instead:

1. Put the query in a separate **autolaunched subflow** with `<runInMode>SystemModeWithoutSharing</runInMode>`.
2. Have the thin PromptFlow **call that subflow** via a `<subflows>` element (`storeOutputAutomatically=true`), passing inputs and reading the subflow's output variables.
3. The PromptFlow just appends the subflow's returned text into `$Output.Prompt`.

The subflow runs system-context; the PromptFlow is a dumb wrapper. This is the single most important thing in this skill.

---

## The READ pattern (two flows + one template)

### Flow A — the system-context subflow (does the real work)
`assets/example-system-context-read-subflow.flow-meta.xml` (real: `ClaimSecure_Read_Open_Claims`).

- `processType = AutoLaunchedFlow`, `<runInMode>SystemModeWithoutSharing</runInMode>`, `status = Active`.
- **Claim access is always via `ClaimParticipant` — never a direct Contact→Claim lookup.** `Get_Open_Claims` is a `recordLookup` on `ClaimParticipant` filtered `ParticipantContactId EqualTo {!contactId}`, `getFirstRecordOnly=false`, `storeOutputAutomatically`.
- **Cross-object fields are read through the `Claim.` relationship name** (the Master-Detail relationship, NOT `ClaimId.`): in the loop, `{!Loop_Claims.Claim.Name}`, `{!Loop_Claims.Claim.ClaimType}`, `{!Loop_Claims.Claim.Status}`, `{!Loop_Claims.Claim.EstimatedAmount}`, `{!Loop_Claims.Claim.ClaimReason}`, `{!Loop_Claims.Claim.Summary}`.
- Loop → decision `Is_Open_Status` (filter to open statuses, `conditionLogic 1 OR 2 OR ...`) → assignment that increments a counter and **concatenates a text block** into an output string (`claimsText`), then loops. `noMoreValues` → set `openClaimCount`.
- Output variables (`isOutput=true`): the built text (`claimsText`) and a count (`openClaimCount`). The count lets the wrapper branch on "none found."

### Flow B — the thin PromptFlow wrapper
`assets/example-promptflow-thin-wrapper.flow-meta.xml` (real: `ClaimSecure_Get_Open_Claims`).

- `processType = PromptFlow`, `<triggerType>Capability</triggerType>`, `status = Active`. **No `runInMode` — it can't have one.**
- Input text var (e.g. `contactId`). Optionally `Get_Contact` first if you need the contact's name.
- `<subflows>` element calls Flow A (`flowName = <subflow>`, `storeOutputAutomatically=true`, one `inputAssignments` per input).
- Assignments of `elementSubtype AddPromptInstructions` append the subflow's outputs to `$Output.Prompt` (e.g. an intro line + `{!<Subflow>.claimsText}`).
- A decision on `{!<Subflow>.openClaimCount} EqualTo 0.0` picks a "none found" prompt vs. the claims block.

### The flex prompt template
Targets the PromptFlow as a data provider and shapes the model output. For ClaimSecure it emits a two-section contract the subagent relies on: **CUSTOMER SUMMARY** (count + type/provider/status per claim) and **FULL DETAILS** (one paragraph per claim, parsing the `Summary` delimited lines). Agent action target = `generatePromptResponse://<Template>`.
See the `calling-prompt-templates-in-flows` skill for template↔flow wiring specifics.

---

## The WRITE pattern (one autolaunched flow, used directly as a `flow://` action)
`assets/example-system-context-write-flow.flow-meta.xml` (real: `ClaimSecure_Open_New_Claim`).

- `processType = AutoLaunchedFlow`, `<runInMode>SystemModeWithoutSharing</runInMode>`, `status = Active`.
- Input vars for every field the agent collects (`contactId`, `claimType`, `providerName`, `serviceDate`, `estimatedAmount` (Currency), `claimReason`). Output vars `isSuccess` (Boolean), `claimNumber`, `resultMessage` — all `isOutput=true`, phrased so the model can relay them verbatim (including the failure message).
- `Get_Contact` by `contactId` → decision `Contact_Found` (guard the not-found path to a `Set_Failure` assignment) → `Create_Claim`.
- **Generate the record name/number with a formula**, not by reading a sequence: e.g. `'CLM-' + UPPER(LEFT({!claimType},3)) + '-' + TEXT(FLOOR((NOW()-DATETIMEVALUE('2020-01-01 00:00:00'))*86400))`. Formulas also build the `Summary` block and resolve the AccountId (`IF(ISBLANK({!Get_Contact.AccountId}), '<demo account>', {!Get_Contact.AccountId})`).
- **Two `recordCreates`, in order:** first `Claim` (`storeOutputAutomatically=true`), then `ClaimParticipant` linking back — `ClaimId = {!Create_Claim}`, `ParticipantContactId = {!contactId}`, `Roles = 'Patient'`. **Claim has no direct contact lookup; the ClaimParticipant row IS the link.** `Roles` is a required multi-select set structurally (no FLS needed on it).
- Assign the success outputs after the participant is created.

### The VERIFY pattern
Same shape as write but read-only: autolaunched, `SystemModeWithoutSharing`, look up the Contact by Id, compare provided factors (e.g. `Birthdate` + a certificate/PIN field) to the record, output `isVerified` (Boolean), `contactName`, `verificationMessage`.

---

## Why system context AND a perm set both matter

Run mode governs **record/sharing** access; it does NOT grant **object-level** CRUD to the agent user for anything that runs in *user* context (like the PromptFlow wrapper, or the agent reading action outputs). So you still deploy an agent-user perm set (object Read + full FLS, ViewAll/ModifyAll = 0) — see the `scoping-agent-user-permissions` skill. With the writes in system-context flows, the agent user never needs object Create/Edit (its license blocks that anyway). Belt and suspenders: the flows read/write regardless, the perm set covers the user-context surface.

---

## Deploy & verify

```bash
sf project deploy start --json --metadata Flow:<Subflow>
sf project deploy start --json --metadata Flow:<PromptFlow>
sf project deploy start --json --metadata Flow:<WriteFlow>
```
Deploy the subflow **before** the PromptFlow that references it. All carry `<status>Active</status>` so they deploy Active. Confirm run mode landed:
```bash
grep -c "SystemModeWithoutSharing" <each flow file>   # must print 1 (except the PromptFlow, which prints 0 by design)
```
Then preview the agent with `--use-live-actions` and confirm the read returns the real rows (this is where the empty-results bug shows up if the query is still in the PromptFlow).

## Gotchas (hard-won)
- **PromptFlow ≠ system context.** If your read is empty, the SOQL is in the wrong flow. Move it to the subflow.
- **`Claim.` not `ClaimId.`** for cross-object field reads from ClaimParticipant.
- **Always ClaimParticipant-first** for Contact→Claim; there is no direct lookup.
- **`Roles` on ClaimParticipant is required**, multi-select, no FLS — set it to a literal (`Patient`) in the create.
- **Order the creates**: parent (`Claim`) before child (`ClaimParticipant`), and reference `{!Create_Claim}` (the record var) as the child's master-detail Id.
- **Phrase output messages for the model** — the failure `resultMessage` should literally tell the model what to say and to offer escalation.
