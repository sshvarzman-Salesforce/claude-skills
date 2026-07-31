# CLT Troubleshooting Guide

Common failures when building CLTs for SRA and how to fix them.

---

## Diagnosis Table

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| "I cannot do this automatically" | `copilotAction:isUserInput: true` on one or more inputs | Set ALL inputs to `isUserInput: false` in Agent Builder |
| Action executes but returns empty/null data | `with sharing` on the Apex action class | Change to `without sharing` — EinsteinServiceAgent User has no sharing rules |
| Card renders but shows "—" or blank for fields | Missing Field-Level Security on queried fields | Add all queried fields to the Permission Set for both rep + EinsteinServiceAgent User |
| Text narrated in chat instead of card rendered | Missing show_command instruction layer | Add show language in ALL 3 places (InvocableMethod, Lightning Type description, Topic Instructions) |
| Output Rendering dropdown doesn't show Lightning Type | Action was deployed via metadata bundle | Remove the action from the topic, create a brand-new one by hand in Agent Builder |
| Agent Builder shows 6+ flattened text outputs | DTO uses `@InvocableVariable` instead of `@AuraEnabled` | Rebuild DTO with single `@AuraEnabled String` field + rebuild the action in Agent Builder |
| `ContactId` not resolving in messaging | Using Case-only context variable | Use MessagingSession-based resolution (3-tier fallback pattern) |
| Card renders first time but not on retry | Planner caching stale plan state | Start a fresh messaging session — old sessions cache plan state |
| Action executes but card never appears | `Show in conversation` unchecked for CLT output | Check ✅ Show in conversation + ✅ Filter from agent action on the CLT output field |
| Card renders intermittently (~40%) | Platform non-determinism (GUS W-21683108) | Normal behavior — strengthen instruction layer, re-run. NGS team tracking. |
| Apex class not visible in Agent Builder dropdown | Missing Apex Class access on permission set | Add Apex Class access for BOTH the action class AND the DTO class |
| "No results found" but data exists in org | FLS grants Read but field is null on the record | Verify data exists: `sf data query --query "SELECT <fields> FROM <object>"` |
| Chain stops after first HiL confirmation | Known planner limitation — post-confirm chain break | Add continuation language in instructions; see [chaining.md](chaining.md) |

---

## Debugging via Session Trace

After running an action, check the session trace to determine whether `show_command` fired:

### Success Path
```
ACTION_INVOCATION → ACTION_SUCCESS_RESPONSE → show_command rendition
```
The card renders in the sidebar.

### Failure Path
```
ACTION_INVOCATION → ACTION_SUCCESS_RESPONSE → LLM_COMPLETION_RESPONSE (text narration)
```
The LLM narrated the result as text instead of emitting `show_command`. Fix by strengthening the instruction layer.

### How to Access
In the org: Setup → Messaging Sessions → select the session → Related → Conversation Events (or use RecActorActionFeed.Content query).

---

## The "Nuclear Option" — Full Action Rebuild

When the output config is hopelessly corrupted (usually from a metadata deploy that overwrote hand-built config):

1. In Agent Builder, **remove** the action from the topic entirely
2. **Delete** the GenAiFunction metadata record if it exists (Setup → Agent Actions → delete)
3. **Create a completely new Agent Action** from scratch:
   - Reference Action Type: Apex
   - Reference Action Category: Invocable Method
   - Select the Apex class
   - Use a FRESH developer name (e.g., `Get_Customer_Profile_v2`)
4. Configure all outputs fresh — the Lightning Type should now appear in Output Rendering
5. Re-add to topic with correct instructions

---

## Permission Set Checklist

For EACH CLT action, both the **rep user** AND **EinsteinServiceAgent User** need:

```
□ Apex Class Access:
  □ Action class (e.g., GetCustomerProfileAction)
  □ DTO class (e.g., CustomerProfileOutput)

□ Object Permissions:
  □ Read access on all queried objects
  □ Create access on objects written by write actions

□ Field-Level Security:
  □ Read access on EVERY field in your SOQL SELECT clause
  □ Read access on EVERY field used in WHERE clauses
  □ (Missing FLS = silent null, NOT an error — hardest to debug)

□ External Credential Principal Access:
  □ Only needed if action makes API callouts via Named Credentials
```

**Quick verify command:**
```bash
sf org open --target-org <alias> --path "/lightning/setup/PermSets/home"
```

---

## Testing Protocol

1. **Always test on the LIVE messaging console** — Agent Builder Preview NEVER renders CLTs
2. **Start a fresh messaging session** after any action or instruction change
3. **First attempt may not render** (~40% non-determinism) — run 2-3 times before investigating
4. **Check session trace** to distinguish "didn't fire show_command" from "infrastructure error"
5. **Verify data exists** before blaming CLT config — empty query results look identical to CLT failures
