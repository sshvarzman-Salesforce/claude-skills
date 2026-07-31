# SRA Action Setup Reference

> Provides complete Agent Builder action configuration for Service Rep Assistant subagent actions. Always gives the full setup with all checkboxes, inputs, outputs, and rendering settings.

**Invocation:** When the user asks for "action setup", "action configuration", "how to configure [action name]", or "give me the full setup for [action]"

---

## How It Works

When the user requests action configuration details:

1. **Read the canonical reference first:**
   ```
   /Users/chad.goldsmith/pet-travel-demo/skill/REBUILD-AGENT.md
   ```

2. **Find the action** in Step 4 (Action 1 through Action 8)

3. **Return the COMPLETE configuration** including:
   - Basic settings (label, description, confirmation, progress indicator)
   - ALL input variables (API name, label, description, require, collect, variable mapping)
   - ALL output variables (API name, label, description, filter checkbox, show in conversation checkbox, output rendering)
   - Critical notes about Filter rules and Output Rendering
   - Context variable mappings where applicable

4. **Use the exact table format** from REBUILD-AGENT.md - don't summarize, don't skip checkboxes

---

## Format Template

Use this structure for EVERY action setup response:

```markdown
# [Action Name] - Complete Action Setup

## Basic Settings

**Invocable Method:** [Label] (`[ClassName]`)
**Agent Action Label:** [Label]
**Description:**
```
[Full description text from REBUILD-AGENT.md]
```
**Confirmation Required:** [☐ Off / ✅ On]
**Progress Indicator Message:**
```
[Progress text]
```

---

## Input Variables

### [Input 1 Name]

| Field | Value |
|-------|-------|
| **API Name** | `apiName` |
| **Label** | Label Text |
| **Description** | Description text |
| **Require user to provide value** | [☐ / ✅] |
| **Collect from user before running action** | [☐ / ✅] |
| **Variable** | [Variable name or N/A] |

[Repeat for each input]

---

## Output Variables

### [Output 1 Name]

| Field | Value |
|-------|-------|
| **API Name** | `apiName` |
| **Label** | Label Text |
| **Description** | Description text |
| **Filter from agent** | [☐ Off / ✅ On] |
| **Show in conversation** | [☐ Off / ✅ On] |
| **Output Rendering** | [Type or —] |

> [Include critical notes about filter rules and rendering from REBUILD-AGENT.md]

[Repeat for each output]

---

## Summary

[Bullet list of key configuration points]
```

---

## Actions Available

The REBUILD-AGENT.md reference contains these Pet Travel actions:

1. **Get Customer Profile** → NOW: **Get Pet Travel Customer Profile**
2. **Check Pet Manifest**
3. **Pet Booking**
4. **Loyalty Perk**
5. **Generate Boarding Pass**
6. **Get Destination Weather**
7. **Draft or Revise Email** (standard action)
8. **Answer Questions with Knowledge** (standard action)

---

## Key Rules

✅ **Always read REBUILD-AGENT.md first** - don't guess from memory  
✅ **Include ALL checkboxes** - Require, Collect, Filter, Show in Conversation  
✅ **Include critical notes** - Filter rules, Output Rendering warnings from the reference  
✅ **Use exact descriptions** - don't paraphrase action descriptions  
✅ **Show context variable mappings** - when inputs map to `currentRecordId` or other context vars  

❌ **Never give partial configs** - "I'll give you the basics" is not acceptable  
❌ **Never skip output rendering settings** - CLT outputs MUST specify the Lightning Type  
❌ **Never skip filter checkboxes** - they determine what the agent can see  

---

## Example Usage

**User:** "give me the action setup for Check Pet Manifest"

**Response:**
1. Read `/Users/chad.goldsmith/pet-travel-demo/skill/REBUILD-AGENT.md`
2. Find "### Action 2: Check Pet Manifest" (around line 104)
3. Return the complete table with ALL fields from that section
4. Include the notes about filter rules and Output Rendering

---

## When Action Isn't in REBUILD-AGENT.md

If the user asks for an action that isn't documented in REBUILD-AGENT.md:

1. **Check if it's a new action** - search the pet-travel-demo codebase for the Apex class
2. **Read the Apex class** to understand inputs/outputs
3. **Follow the same format** but note that it's not in the canonical reference yet
4. **Suggest updating REBUILD-AGENT.md** with the new action config

---

## Related

- **REBUILD-AGENT.md** - The canonical reference (single source of truth)
- **sra-agent-debugger** - For tracing agent sessions after actions are configured
- **sf-clt-builder** - For building the Custom Lightning Types that actions output
