---
name: sra-edge-cases
description: Identify edge cases and error states for Service Rep Assistant features. Use when reviewing PRDs, open questions, or designs before scrum team handoff. Covers input validation, data states, system states, permissions, flow interruptions, integration failures, and SRA-specific scenarios (plan generation, eligibility, AE session lifecycle, multi-agent routing, gater interactions).
tools: [Read]
---

# SRA Edge Cases Analysis

Identify edge cases for: $ARGUMENTS

## Context Gathering

Before generating edge cases:
1. If a PRD file path is given, read it — focus on the Scope, Target state, and Open Questions sections
2. If no file is given, ask: "What feature or flow? What's the main trigger? Which channels (Case/Message/Voice)? Any known constraints or open questions?"
3. Check `.agents/artifacts/prds/` for a matching PRD file if the feature name is recognizable

## Edge Case Categories

### 1. Input Validation
Empty/null values, special characters in case descriptions or instructions, boundary values (token limits, topic count limits, step count limits), invalid field formats, extremely long inputs (case descriptions > 32k chars, topic instructions at token budget ceiling)

### 2. Data States
Empty states (no topics configured, no actions attached, no knowledge articles), first-time org setup (no Service Plan configured at all), single record vs. bulk (1M+ cases open), stale cached plan (plan generated hours ago, case fields updated since), orphaned GenOpPlan records (case deleted after plan generated), circular topic matching (two topics with overlapping classification descriptions), pre-GA cases with GenOpPlan but no RecActorActionFeed entry (lazy backfill scenario)

### 3. System States
Plan generation timeout (LLM call exceeds SLA), partial failure during multi-step plan generation (steps 1–3 generated, step 4 fails), concurrent modifications (rep A and rep B both open same case in AE simultaneously), session expiry mid-plan (rep is on step 4 of 8, auth token expires), RECORD_HOME_LOAD fires before eligibility flow completes (race condition), plan generated but RecActorActionFeed write fails (success in GenOp, failure in feed), Data Cloud unavailable at plan generation time, AI Gateway rate limit hit during peak hours

### 4. Permissions & Access
Rep has read-only access to case (no write permission — can they still see the plan?), rep lacks permission to execute a Tool Action in the plan (action requires object they can't access), admin configures a topic but forgets to activate it, FLS restrictions on fields used in eligibility criteria (eligibility flow returns null instead of failing gracefully), sharing rule violation on related records used for grounding, rep transferred to different queue mid-session (agent routing locked to old assignment)

### 5. User Flow Interruptions
Rep closes browser tab mid-plan execution (session persistence — what survives?), rep navigates away from case and returns (does the plan reload from feed or regenerate?), rep clicks "Run Plan" twice in rapid succession (double-submission), rep refreshes page while Summary Plan is generating (what state does the component restore to?), Lightning component reload during active Dynamic Plan step (step completion state — lost or persisted?), rep on Voice call when call transfers to new queue (agent assignment locked — but new queue would have different routing rules)

### 6. Integration / GenAI Failures
Einstein AI Gateway unavailable (hard down vs. degraded), plan generation returns `Insufficient Data` resolution status (what does rep see?), plan generation returns `Issue Already Resolved` (rep expected a plan, gets told it's resolved — UX?), Hyperclassifier intent unavailable when Show Summary = OFF (Dynamic Plan has no grounding signal — fallback behavior?), ServicePlanSkillActor throws exception during RECORD_HOME_LOAD (error entry written to RecActorActionFeed — what does rep see?), Knowledge Base search returns zero results (plan generates with no KB grounding — quality regression not surfaced to rep), topic matching returns no match (falls to default agent — is rep informed?), GenAI response contains prompt injection attempt (injection detection flag — does plan surface to rep or get blocked?)

### 7. SRA-Specific Scenarios

#### Plan Generation Lifecycle
- **Idempotency race:** Two RECORD_HOME_LOAD events fire in rapid succession (rep double-clicks or component re-mounts) — does the system generate two plans or correctly detect the in-flight generation?
- **Gater enabled mid-session:** `SummaryPlanOnAdaptiveExperience` gater is enabled while a rep has a case open — does the existing pinned summary and the new feed entry coexist?
- **Show Summary toggled mid-pilot:** Admin changes Show Summary = OFF for Voice while a rep is mid-call — does the in-progress session respect the old setting or pick up the new one?
- **Pre-GA case lazy backfill fails:** Frontend attempts to create RecActorActionFeed backfill entry but write fails (permissions, object unavailable) — does the rep see an error or a silent empty feed?
- **Plan generation before rep opens case (legacy race):** With gater disabled, CaseAgentCaseHook still fires on case save — plan generates before any rep opens it. Rep opens case and sees a stale plan from case-create time, not case-open time.

#### Multi-Agent Routing
- **Assigned agent deactivated mid-plan:** Agent was active when plan started, deactivated while rep is mid-execution — does the system failover to default agent, and does the rep see a warning?
- **Routing field populated after component loads:** Case.Region field (used in routing criteria) is null at T=0 when component loads, populated at T+5s — rep is locked to default agent even though correct agent could now be determined
- **Agent switch between Summary and execution:** Summary Plan used Agent A, re-evaluation at Run Plan selects Agent B — Agent B doesn't have the matching topic — plan generation fails in a loop
- **No routing rules match, default agent also inactive:** Routing engine can't assign any agent — what does the rep see? Silent failure vs. explicit error?
- **150-agent limit reached:** Admin tries to add agent 151 to a Service Assistant Template — is the limit enforced at config time with a clear error, or does it fail silently at runtime?

#### Eligibility & Thresholds
- **Eligibility flow throws exception:** Flow crashes instead of returning true/false — does plan generation skip gracefully or surface an error to the rep?
- **Eligibility passes but topic match fails:** Eligible case but no topic matches the issue — rep sees eligibility badge but no plan generates
- **Voice utterance threshold race:** 5-utterance eligibility threshold reached simultaneously with call transfer — does eligibility re-evaluate, and does the plan generate for the new rep or the old one?
- **Guidance mode with dynamic plan gater:** AE enabled, Dynamic Plan disabled, Summary Plan gater enabled — does the Summary Plan render in the Service Plan component (correct) or attempt to write to RecActorActionFeed (incorrect)?

#### Metering & Billing
- **Generation on case save vs. case open:** With legacy hook enabled alongside new gater (misconfiguration), both triggers fire — two GenOpPlan records created, double-metered
- **Show Summary = OFF but GenOp record still created:** If the OFF flag is checked after the generation call rather than before, a metered event fires even though no summary is shown
- **Beta org un-metering edge:** Plan generated in an A4S org (un-metered) but billed as E4S request due to license detection error at generation time

## Output Format

```markdown
# Edge Cases: [Feature Name]

**Feature:** [Name] | **PRD:** [file or "ad-hoc"] | **Date:** [Date] | **Channels:** [Case/Message/Voice]

## Summary
Total: X | Critical: X | High: X | Medium: X | Low: X

## Edge Cases by Category

### [Category Name]
| ID | Scenario | Trigger | Severity | Expected Behavior | UX / Error Message |
|----|----------|---------|----------|-------------------|--------------------|
| EC-001 | [Scenario] | [How triggered] | Critical/High/Med/Low | [What should happen] | [What rep/admin sees] |

## Must Handle Before GA
- [ ] EC-XXX — [Description] — *risk if not handled: [consequence]*

## Should Handle (Post-GA OK)
- [ ] EC-XXX — [Description]

## Open Questions Surfaced
| Question | Why it matters |
|---|---|
| [Question] | [Edge case that can't be fully specified without this answer] |
```

Severity guide:
- **Critical** — data loss, silent wrong behavior, metering/billing error, or rep stuck with no recovery path
- **High** — rep sees error but has no clear action; feature behaves incorrectly in a common scenario
- **Medium** — degraded experience, workaround exists
- **Low** — cosmetic, rare trigger, minor friction

## Best Practices

- Think from three angles: **rep** (what do they see?), **admin** (what did they misconfigure?), **platform** (what failed silently?)
- Consider scale: 1 case vs. 1M open cases; 1 rep vs. 500 concurrent reps
- Test boundaries: exactly at limits (150 agents, 10 topics, 5 utterances), just below, just above
- Every Critical and High edge case should have a corresponding AC in the PRD's Acceptance Criteria — if it doesn't, flag it
- "No error surfaced to rep" is often the worst failure mode in SRA — silent degradation erodes trust faster than visible errors

## Save Location

Save to `.agents/artifacts/edge-cases/[date]-[feature-slug].md`

## Usage Examples

```
/sra-edge-cases the Summary Plan to Message History PRD
```
→ Reads `prd-262-summary-plan-to-message-history.md`, generates edge cases focused on RECORD_HOME_LOAD, RecActorActionFeed writes, lazy backfill, and idempotency

```
/sra-edge-cases multi-agent routing — specifically the agent deactivation and routing field timing risks
```
→ Focuses on the open questions from the multi-agent routing PRD

```
/sra-edge-cases Show Summary = OFF for Voice — what breaks?
```
→ Generates edge cases for the show/hide toggle, grounding decoupling, and auto-run implications
