# Agentforce Service Assistant — Subagent Design Strategy

Source: "Agentforce Service Assistant Subagent Design Strategy" (@salesforcedocs, last updated Jun 17, 2026). This doc explains *why* the design rules in `best-practices.md` and `generator-prompt.md` work the way they do — the reasoning-anchor model behind dynamic plans.

Note: this doc references "cases," but the content applies to all Service Assistant supported objects: Case, Messaging, and Voice.

## Why Subagent Structure Matters More in Dynamic Plans

In the previous Service Assistant experience, guidance plans were static checklists that didn't change once generated. In the dynamic experience, a service plan is a live, evolving issue resolution workflow — Service Assistant monitors the record continuously, performs a fresh search of grounding sources at every step, and adapts guidance as new information arrives.

The subagent's description and scope are the **reasoning anchor** for the entire plan. They define what issue Service Assistant thinks it's resolving, which knowledge articles it searches, and what boundaries it respects at each step. A vague subagent produces a vague, unfocused dynamic plan. A well-defined subagent produces one that stays on track even as the conversation evolves. A single subagent can serve as the resolution framework for many variations of the same issue — that's the core strategy.

## One Subagent for Many Issue Variations

You don't need a separate subagent for every specific subtype of an issue. Create one high-level subagent that explicitly lists its variations in the description field. Service Assistant uses the description to match cases and search for relevant knowledge articles, so when subtypes are defined there, the same subagent handles a wide range of related cases.

This matters most with knowledge grounding: your knowledge articles already contain the specific how-to details for each variation. The subagent's job is to categorize the issue broadly and point Service Assistant in the right direction — articles fill in the granular procedural steps at runtime.

- **Subagent Label:** The broad issue category used for initial record classification using the record details data.
- **Description:** The primary reasoning anchor. Summarize the subagent's purpose and explicitly list specific subtypes and keywords to optimize semantic matching and knowledge retrieval.
- **Scope:** The reasoning boundaries. Explicitly define what the subagent handles and what it does not, to prevent irrelevant knowledge retrieval and model hallucinations.
- **Instructions:** A 5–7 step high-level resolution framework. Outline the general workflow logic (e.g., verify, identify, escalate) rather than granular procedures, which are sourced dynamically from knowledge articles.

### Example: Payroll Issues

Payroll problems come in many forms — not paid at all, direct deposit to the wrong account, hours calculated incorrectly, an incorrect deduction. You don't need a separate subagent for each. One well-structured subagent covers all of them, with the description explicitly listing the subtypes: missing paychecks, direct deposit errors, overtime miscalculations, incorrect deductions, W-2 discrepancies.

When a case comes in with a Subject like "employee says overtime wasn't paid correctly," Service Assistant matches it to this subagent because that variation is captured in the description. The instructions don't need to prescribe the exact resolution steps — the knowledge articles provide that. The instructions tell Service Assistant the goal at each stage; during plan generation, Service Assistant pulls the specific procedural steps from the matching knowledge articles.

| Subagent Part | Example | Why |
|---|---|---|
| Label | Payroll Issue | A broad category label is preferred — it gives Service Assistant a clear classification. Knowledge articles add the specificity to plan steps. |
| Description | Assist service reps in helping employees resolve payroll discrepancies and payment concerns. Questions are related to payroll processing errors, including missing or late paychecks, incorrect direct deposit routing, overtime and hours miscalculations, incorrect tax withholdings, unauthorized or incorrect deductions, and year-end W-2 discrepancies. | Each variation listed expands the matching criteria. Naming specific subtypes creates a stronger semantic signal, so Service Assistant precisely pairs case data with the most relevant knowledge articles. |
| Scope | Your job is to assist service reps in identifying the root cause of the payroll issue and guiding them through the steps to investigate, escalate if needed, and resolve the discrepancy. You must not handle inquiries outside of payroll processing, compensation, and deductions. | The scope sets a boundary that prevents the agent from reasoning outside its intended domain — reduces guidance from unrelated context and filters out irrelevant knowledge articles during retrieval. |

## Why the Description Is the Match Signal

Service Assistant reads the case Subject and Description fields to assign a subagent, looking for the best semantic match against your subagent descriptions. The more precisely the description names the variations of an issue, the more accurately Service Assistant classifies incoming cases.

A vague description like "help service reps resolve payroll issues" gives a weak signal — Service Assistant might match the right subagent but lacks context to distinguish, say, a missing paycheck from an incorrect tax withholding. That ambiguity dilutes the knowledge article search: instead of surfacing highly relevant articles, Service Assistant retrieves a broader, less targeted set, producing a less focused service plan.

## Subagent Instructions

- **Without knowledge grounding:** instructions must be detailed and comprehensive — each one spells out exactly what to do and how.
- **With knowledge grounding:** instructions provide the high-level framework only. Service Assistant pulls granular how-to details from knowledge articles at runtime — you don't need to write every procedure into the instructions themselves.

Each instruction should answer one question about the resolution workflow: what must happen first, what needs to be confirmed, what the rep identifies here, what action gets taken, or what closes the case. That maps to 5–7 instructions defining:

- The general workflow stage ("verify identity and confirm pay period")
- What the rep is trying to determine at this step ("identify the source of the error")
- Conditional language signaling which variation applies ("based on the type of discrepancy reported")
- Mandatory steps using explicit language ("As a first step," "You must")
- Outcome-oriented directives ("execute the corresponding resolution procedure")

### Conditional Language Helps
Because one subagent covers multiple variations, instructions naturally need conditional language to account for different scenarios — it gives Service Assistant enough context to decide which knowledge articles are most relevant and which resolution path to follow. Good patterns:
- "Based on the type of discrepancy reported..."
- "If the payroll run was processed but the employee wasn't included..."
- "When the issue involves a direct deposit routing error..."
- "After verifying the enrollment record, if the window has closed..."

You don't need to write out every possible branch — the conditional language signals the range of scenarios; Service Assistant combines that signal with actual case data and knowledge articles to determine what guidance to surface.

### Example: Benefits Enrollment Issue (full subagent)

| Subagent Part | Example |
|---|---|
| Description | Assist service reps in helping employees resolve benefits enrollment problems. Questions are related to open enrollment, qualifying life events, and benefits changes, including missed enrollment windows, incorrect plan selections, dependent coverage errors, HSA and FSA contribution discrepancies, and issues with benefits effective dates. |
| Scope | Your job is to assist service reps in identifying the enrollment issue, determining what correction options are available, and guiding the rep through the resolution or escalation process. You must not handle inquiries outside of benefits enrollment, plan selection, and dependent coverage. |
| Instruction 1 | As a first step, confirm the employee's current enrollment status, the benefits plan year in question, and whether the issue is related to open enrollment or a qualifying life event. |
| Instruction 2 | Review the enrollment record to determine what elections are currently on file and whether the employee's changes were submitted and processed within the required window. |
| Instruction 3 | Based on the type of issue — missed window, incorrect plan, dependent error, or contribution discrepancy — locate the relevant enrollment detail and determine the available correction path. |
| Instruction 4 | Based on the identified issue, initiate the appropriate correction: process a qualifying life event change, submit an enrollment correction request, update dependent information, or escalate to the benefits team. |
| Instruction 5 | Confirm the outcome with the employee, including the corrected elections, effective date, and any documentation required to finalize the change. |

## How It All Works Together During Plan Generation

1. **Case assigned to subagent.** Service Assistant reads the case Subject and Description, matches them against subagent descriptions, and assigns the best match (e.g., "employee reports overtime not included in last paycheck" matches Payroll Issue because "overtime and hours miscalculations" is in the description).
2. **Knowledge search performed.** Using the subagent's description and case details, Service Assistant searches the knowledge base — because "overtime and hours miscalculations" was listed as a variation, overtime-calculation articles surface as strong matches.
3. **Instructions provide the framework.** The 5–7 instructions establish the overall resolution structure. A general directive like "locate the relevant payroll detail and determine the correction path" pairs with the overtime-specific knowledge article, which supplies the exact steps.
4. **Plan steps are generated,** combining the instruction framework with procedural content from the knowledge articles into specific, actionable steps tailored to the actual case.
5. **Plan adapts as the case evolves.** This process repeats at every step of a dynamic plan — if new context emerges mid-plan, Service Assistant performs a fresh knowledge search and adapts the next step accordingly.

## Quick Reference: Subagent Structure Checklist

**Label**
- Specific enough to name the issue category clearly
- Not so narrow that it only applies to one exact subtype
- Not so broad that it's a catch-all ("Customer Issue," "General Support")

**Description**
- States the overall purpose of the subagent
- Explicitly lists the issue variations and subtypes it covers
- Uses language employees/case records actually use, not just internal system terminology
- Long enough to cover the range; doesn't need to be exhaustive

**Scope**
- States what the subagent can handle
- Explicitly states what it cannot handle
- Gives Service Assistant a clear boundary to reason within

**Instructions (with knowledge grounding)**
- 5 to 7 instructions total
- Each covers one stage of the general resolution workflow
- Uses mandatory language for required steps ("As a first step," "You must")
- Uses conditional language to signal scenario variations
- Does not prescribe exact procedures — those come from knowledge articles
- Does not tell Service Assistant to search the knowledge base

## Required Standard Subagents

Custom subagents handle the specific issue types you've defined. The required standard subagents handle everything else — CRM lookups and knowledge searches that fall outside the current plan context. You must add at least one; you can add both.

- **General CRM:** identify/summarize records, answer queries, aggregate data, find/query objects, update records, draft/refine emails. Default actions: Draft or Revise Email, Get Record Details, Answer Questions with Knowledge, Query Records, Extract Fields And Values From User Input, Query Records with Aggregate, Update Record, Get Activity Details, Identify Record by Name.
- **General FAQ:** answers questions from knowledge articles via the Answer Questions with Knowledge action, using the data library assigned to the agent in Agentforce Builder.

## Subagents and Topic Switching

When Service Assistant detects a context shift mid-plan:
1. **Pauses the current plan** — stops executing the current subagent's resolution steps and holds its place.
2. **Switches to the relevant subagent** — the General FAQ/CRM subagent for an off-topic question, or a different custom subagent if the issue itself changes.
3. **Returns to the original plan** once the side issue is resolved, continuing from where it paused.

Example: an employee reports missing overtime pay (Payroll Issue plan in progress), then mentions an HSA contribution that didn't go through during open enrollment. Service Assistant pauses the payroll plan, switches to the Benefits Enrollment Issue subagent, resolves that, then returns to the payroll plan automatically — the rep never restarts or manually navigates between issues.
