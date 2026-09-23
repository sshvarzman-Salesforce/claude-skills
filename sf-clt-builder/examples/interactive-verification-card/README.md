# Interactive Verification Card — example scaffold

A complete, deploy-ready interactive CLT for the **Service Rep Assistant** panel. The card shows
an identity-verification checklist; the rep clicks **Pass**, **Fail**, or **Draft note**, and the
card writes the result **back into the SRA chat** — no typing required.

This is the first CLT in the skill that uses the **write-back events**
(`copytochat` / `acc:execute`). See `../../guides/interactive-writeback.md`.

## What's inside

```
classes/
  VerificationOutput.cls            single-JSON-field DTO (@AuraEnabled)
  GetVerificationCardAction.cls     @InvocableMethod, without sharing, 3-tier Contact resolve
lightningTypes/sraVerificationOutput/
  sraVerificationOutput.lightningType-meta.xml
  lightningDesktopGenAi/renderer.json   → maps to c/sraVerificationCard
lwc/sraVerificationCard/
  sraVerificationCard.js/.html/.js-meta.xml
```

## Which button fires which event

| Button      | Event         | Effect                                                        |
|-------------|---------------|---------------------------------------------------------------|
| Pass        | `acc:execute` | Auto-sends "Identity verification passed …" → agent advances  |
| Fail        | `acc:execute` | Auto-sends "Identity verification failed …" → agent advances  |
| Draft note  | `copytochat`  | Drops an editable stub into the input box for the rep         |

## Deploy

```bash
sf project deploy start --source-dir force-app --target-org <alias>
```

## Agent Builder setup

This can be **deployed** as `GenAiFunction` + `GenAiPlannerBundle` metadata rather than clicked
together — see Step 6 of the main `SKILL.md`. The UI steps below are the equivalent by hand, and
are still useful for verifying what a deploy produced.

1. Topics → your topic → **New Agent Action** → Apex → Invocable Method → `GetVerificationCardAction`.
2. Inputs: `customerId`, `messagingSessionId` → **isUserInput: false**.
3. Outputs:
   - `verification` → Show in conversation ✅, Filter from agent action ✅, Output Rendering → **Verification Card**.
   - `success`, `errorMessage` → Show ☐, Filter ☐.

   > Remember that **Filter from agent action HIDES** the output from the planner
   > (`isUsedByPlanner: false`). Filter the card so the agent doesn't re-narrate it as text.
   > But Agent Builder rejects a save where *every* output is filtered —
   > *"Disable the Filter from agent action setting for at least one output"* — so leave the
   > scalar plumbing unfiltered. If a follow-up action needs a value from the card, add a flat
   > passthrough output for it rather than unfiltering the card.
4. `isConfirmationRequired`: **false** (read-only display).
5. Add show_command language to Topic Instructions (see main SKILL.md, Step 7).
6. Permission Set (rep user **and** EinsteinServiceAgent User): Apex access to both classes;
   FLS read on Contact.FirstName/LastName/Phone/Email.

## Prerequisites for the write-back to work

- **SRA panel** (not the standard Agentforce/ACC panel).
- **SRA in Dynamic Plan mode** (not Guidance Plan mode).
- Platform build with the events: SDB43 internal now; customer sandboxes ~2026-08-22 (262.14).

## Demo script (60 sec)

1. Rep opens a messaging case; SRA plan runs and renders the Verification Card.
2. Rep confirms the checklist with the caller, clicks **Pass**.
3. "Identity verification passed …" auto-posts to chat; SRA proceeds to the next plan step.
4. (Alt) Click **Draft note** to show the `copytochat` variant — text lands in the input box,
   rep edits, then sends.
