---
name: sf-clt-builder
description: Build Custom Lightning Type (CLT) cards for Agentforce Service Rep Assistant — generates Apex DTOs, action classes, LWC renderers, Lightning Type bundles, and Agent Builder configuration checklists
tools: [Bash, Read, Write, Edit]
---

# Custom Lightning Type (CLT) Builder for Service Rep Assistant

Generates CLT card components for the **Agentforce Service Rep Assistant (SRA)** sidebar. CLTs render rich visual cards (LWC) in the SRA Dynamic Plans messaging surface instead of narrating action results as text.

**Surface:** Service Rep Assistant sidebar — messaging channel with Dynamic Plans  
**Reference implementation:** `~/pet-travel-demo/` (working 5-action CLT demo)  
**Universal demo skill:** `~/sf-demo-skills/SKILL.md` (project setup, deploy, auth)  
**Best practices:** `~/sf-demo-skills/BEST-PRACTICES.md` (topics, instructions, sequencing)

---

## When to Use This Skill

Activate when the user asks to:
- Build a CLT / Custom Lightning Type / card / visual output for an SRA action
- Add a rendered output to an existing Agentforce action
- Create a new action that should display a card in the SRA sidebar
- Make an action "show a card" or "render in the sidebar"
- Build an action chain where some steps render visual cards

**Do NOT use for:** actions that return plain text only, actions for surfaces other than SRA (e.g., Copilot, external agents), or LWC components not targeted at `lightning__AgentforceOutput`.

---

## Core Architecture: The Single-JSON-Field DTO Pattern

Every CLT has four layers. Generate them in this order:

```
1. CLT DTO (Apex class)        — Single @AuraEnabled String field holding serialized JSON
2. Action Class (Apex)          — @InvocableMethod returning Response that contains the DTO
3. Lightning Type Bundle        — Maps Apex DTO → LWC renderer
4. LWC Component                — Renders the card from this.value.<fieldName>
```

### The Critical Rule

**ONE field. ONE serialized JSON string. `@AuraEnabled` — NOT `@InvocableVariable`.**

Multiple `@InvocableVariable` fields on the DTO get flattened into separate text outputs by Agent Builder schema introspection, which breaks CLT rendering entirely.

---

## Generation Steps

When asked to build a CLT, follow this sequence:

### Step 1: Gather Requirements

Ask (or infer from context):
1. **What data does the card display?** (fields, layout concept)
2. **What object(s) does the action query?** (Contact, Custom Object, etc.)
3. **Is this a read-only or write action?** (determines `isConfirmationRequired`)
4. **Does this chain with other actions?** (determines topic instruction language)
5. **What's the card name?** (drives class names, LWC name, Lightning Type name)

### Step 2: Generate the DTO

Use template: [templates/dto-class.cls](templates/dto-class.cls)

Rules:
- `global` access modifier on class and field
- `@JsonAccess(serializable='always' deserializable='always')` on class
- ONE `@AuraEnabled global String <name>JSON` field
- Two constructors: one with param, one no-arg (empty string default)
- Field name convention: `<cardPurpose>JSON` (e.g., `profileJSON`, `weatherJSON`, `seatMapJSON`)

### Step 3: Generate the Action Class

Use template: [templates/action-class.cls](templates/action-class.cls)

Rules:
- `global without sharing` — EinsteinServiceAgent User has no sharing access
- Input class: all fields `@InvocableVariable` with `required=false`
- Include `messagingSessionId` input for Contact resolution fallback
- Response class: `success` (Boolean) + the CLT output field + `errorMessage` (String)
- `@InvocableMethod` description MUST include: "The output of this action is always renderable, always use show_command."
- Build payload as `Map<String, Object>`, serialize with `JSON.serialize()`, wrap in DTO constructor
- Error case: still return a valid DTO with `{"error": "..."}` so the LWC can render an error state

### Step 4: Generate the Lightning Type Bundle

Use template: [templates/lightning-type/](templates/lightning-type/)

Three files in `force-app/main/default/lightningTypes/<typeName>/`:
1. `<typeName>.lightningType-meta.xml` — JSON format with title, description (include show_command language), and `lightning:type` reference
2. `lightningDesktopGenAi/renderer.json` — maps `$` to the LWC definition

### Step 5: Generate the LWC

Use template: [templates/lwc/](templates/lwc/)

Rules:
- `js-meta.xml`: targets include `lightning__AgentforceOutput` (and optionally `lightning__AgentforceInput`)
- JS: `@api value` receives the DTO, parse `this.value.<fieldName>` in `connectedCallback()`
- HTML: SLDS card layout, handle error state gracefully
- CSS: minimal, let SLDS do the work

### Step 6: Generate the Agent Builder Checklist

After generating code, ALWAYS output a manual setup checklist (these steps cannot be automated):

```markdown
## Agent Builder Manual Setup (Required — cannot be deployed via metadata)

1. Deploy source: `sf project deploy start --source-dir force-app --target-org <alias>`
2. In Agent Builder → Topics → [Your Topic]:
   - REMOVE any existing version of this action
   - Click "New Agent Action"
   - Reference Action Type: **Apex**
   - Reference Action Category: **Invocable Method**  
   - Select: `<ActionClassName>`
   - Use a FRESH developer name (never reuse old auto-generated names)
3. Configure inputs:
   - All inputs: `isUserInput: false` (auto-resolved, not prompted)
4. Configure outputs:
   - `<cltField>`: Show in conversation ✅ | Filter from agent action ✅ | Output Rendering → select `<LightningTypeName>`
   - `success`: Show in conversation ☐ | Filter from agent action ✅
   - `errorMessage`: Show in conversation ☐ | Filter from agent action ✅
5. Set `isConfirmationRequired`:
   - Read-only actions: `false` (auto-executes)
   - Write actions: `true` (shows Confirm button)
6. Add show_command language to Topic Instructions (see below)
7. Assign Permission Set to BOTH the rep user AND EinsteinServiceAgent User:
   - Apex Class access for action + DTO classes
   - Object/Field access for all queried objects and fields
```

### Step 7: Generate Topic Instruction Language

For each CLT action, output the instruction text to add to topic instructions:

```
Execute [Action Name]. Display the complete action output to the user without 
summarizing, modifying, or omitting any content. The output of this action is 
always renderable; always use show_command. Do NOT convert to plain text.
```

For chained actions, also generate the sequencing language (see [guides/chaining.md](guides/chaining.md)).

---

## Confirmation vs. Chaining: Known Platform Limitation

When generating write actions in a chain, warn the user about this tension:

**The problem:** `isConfirmationRequired: true` pauses the chain for rep confirmation. After the rep clicks Confirm, the planner sometimes does NOT resume the chain — it treats the confirmation as end-of-turn.

**The risk of `false`:** Without confirmation, the planner may skip the step entirely or auto-execute a record-creating action without rep awareness.

**Current workarounds:**
1. Add explicit "After [action] completes, immediately proceed to [next action]" in topic instructions
2. Accept that reps may need to nudge with "continue" after confirming
3. Front-load read-only CLT actions (which chain reliably) before write actions

**Status:** The NGS (Next-Gen Service) team is actively working on fixing the planner's post-confirmation chain continuation. Design demos with this limitation in mind until the fix ships.

---

## Three-Place Instruction Layer (Non-Negotiable)

CLT rendering is non-deterministic (~40% first-attempt, GUS W-21683108). To maximize rendering, add show language in ALL THREE places:

| Location | Where | What to add |
|----------|-------|-------------|
| 1. `@InvocableMethod` description | Action class | "The output of this action is always renderable, always use show_command." |
| 2. Lightning Type `description` | `lightningType-meta.xml` JSON | "Always use show_command to display this to the user. Do NOT convert to text." |
| 3. Topic Instructions | Agent Builder UI | "Display the complete action output...always use show_command. Do NOT convert to plain text." |

If any one of these is missing, rendering rate drops further.

---

## File Naming Conventions

Given a card purpose like "Customer Profile":

| Component | File/Folder Name |
|-----------|-----------------|
| DTO class | `CustomerProfileOutput.cls` |
| Action class | `GetCustomerProfileAction.cls` |
| Lightning Type folder | `petCustomerProfileOutput/` (prefix with demo brand) |
| LWC folder | `petCustomerProfileCard/` (prefix with demo brand) |
| Lightning Type `lightning:type` value | `@apexClassType/c__CustomerProfileOutput` |

---

## Common Pitfalls to Prevent

When generating, automatically avoid these:

| Mistake | Consequence | What to do instead |
|---------|------------|-------------------|
| `@InvocableVariable` on DTO field | Agent Builder flattens to text outputs | Use `@AuraEnabled` |
| `with sharing` on action class | Silent empty results (EinsteinServiceAgent User) | Always `without sharing` |
| Multiple fields on DTO | No CLT rendering | Single `<purpose>JSON` field |
| Missing `@JsonAccess` | Serialization failures | Always add `serializable='always' deserializable='always'` |
| Deploying the GenAiPlannerBundle | Overwrites hand-built action config | Never deploy the bundle |
| `isUserInput: true` on action inputs | Agent says "I cannot do this automatically" | Set all to `false` |
| Missing FLS for queried fields | Silent null values (not errors) | Include in permission set checklist |

---

## Relationship to Other Skills

- **`~/sf-demo-skills/SKILL.md`** — handles project setup, SFDX structure, SF CLI auth, metadata deploy. Use that skill FIRST to scaffold the project, then use this skill to add CLT actions.
- **`~/sf-demo-skills/BEST-PRACTICES.md`** — topic/instruction best practices that apply alongside this skill's CLT-specific guidance.
- **Pet travel demo** (`~/pet-travel-demo/`) — reference implementation. When uncertain about a pattern, look at the working code there.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-22 | Initial skill creation — extracted from CLT guide + pet-travel-demo learnings |
