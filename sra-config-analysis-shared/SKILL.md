---
name: sra-config-analysis-shared
description: Analyze Agentforce Service Assistant topic configurations for variance, edge cases, and quality issues. Shared version for FDEs — works with customer org data provided directly (no internal Slack dependencies). Produces variance analysis, edge cases, test cases, and fix recommendations grounded in SRA platform knowledge.
tools: [Read, Write, Edit, Bash, mcp__mcp-adaptor__query, mcp__mcp-adaptor__read_file, mcp__mcp-adaptor__search, mcp__mcp-adaptor__get_service_definition]
---

# SRA Configuration & Behavior Analysis (Shared — FDE Edition)

> Analyze any Agentforce Service Assistant topic configuration and identify what causes non-deterministic behavior. Produces variance analysis, edge cases, test cases, and fix recommendations — grounded in SRA platform knowledge.
>
> **This is the shared FDE version.** It works entirely from data YOU provide (topic configs, KB articles, case emails, transcripts). No internal Slack or codesearch dependencies — safe for use with customer org data.

**Invocation:** `/sra-config-analysis-shared [topic name or paste config]`

---

## What This Skill Does

You provide a topic configuration + sample artifacts from the customer org. The skill:

1. **Identifies variance sources** — where different utterances or data states produce inconsistent behavior
2. **Maps edge cases** — across 7 categories (input validation, data states, system states, permissions, flow interruptions, integration failures, SRA-specific)
3. **Checks action alignment** — do action required inputs match what instructions promise?
4. **Evaluates planner impact** — how does the ReAct planner (dynamic plan prompt) interpret these instructions?
5. **Generates test cases** — mapped to the 9 prompt quality goals
6. **Produces fix recommendations** — prioritized P0/P1/P2
7. **Writes a Slack-ready summary** — for team distribution

---

## Input Requirements

To run this analysis, provide:

| Required | What | How to Get |
|----------|------|-----------|
| ✅ | Topic instructions (full text) | Agent Builder → Topic → Subagent Configuration |
| ✅ | Classification description | Agent Builder → Topic → Classification Description |
| ✅ | Scope | Agent Builder → Topic → Scope |
| ✅ | Actions list (names) | Agent Builder → This Subagent's Actions tab |
| ⭐ | Action configurations (inputs/outputs/settings) | Click each action → View Action |
| ⭐ | Relevant Knowledge Articles (full text) | Knowledge tab → Article used by this topic |
| ⭐ | Sample case emails or message transcripts | Case Feed → Email thread / Messaging transcript |
| ⭐ | Sample case record (field values or screenshot) | Service Console → Case record |
| Optional | Channel context (Email, Messaging, Voice, or all) | You specify |
| Optional | Known issues or symptoms | You describe |
| Optional | Apex code for custom actions | Developer Console or VS Code |

⭐ = Strongly recommended for complete analysis. Without these, the skill produces theoretical analysis only — not real-world variance detection.

### Why Sample Artifacts Matter

**You MUST provide these for a complete analysis.** They are the difference between "this could go wrong" and "here's exactly what goes wrong with this customer's real data":

| Artifact | What It Reveals |
|----------|----------------|
| **Knowledge Articles** | Whether "Answer Questions with Knowledge" retrieves useful content; whether article structure aligns with anti-dumping cadence; whether instructions reference KB steps that don't exist |
| **Case Emails (inbound)** | Real customer language that triggers classification; identifier formats the planner must parse; ambiguous phrasing that tests CSR_SIGNAL logic |
| **Message Transcripts** | Multi-turn interaction patterns; where CSR gets stuck; actual confirmation phrases used (vs magic phrases required); turn counts for HiL/INPUT_FORM flows |
| **Case Field Values** | Pre-populated vs blank fields at session start; which conditions in instructions evaluate true/false; data the planner can ground on vs data it must request |

**If artifacts are missing, the skill will ask:**
> To complete this analysis, I need sample artifacts from the customer org. Can you provide:
> 1. **A relevant Knowledge Article** — the full text of an article this topic would retrieve (e.g., the troubleshooting guide for this product)
> 2. **A sample case email or message transcript** — a real or representative customer interaction that would trigger this topic
> 3. **A case record screenshot** — showing field values (Subject, Description, Status, Contact Email, any custom fields referenced in instructions)
>
> These let me trace exactly how the planner processes real inputs — not just theoretical paths.

---

## Input Modes

This skill supports two input modes. Use whichever fits your situation:

### Input Mode: Paste (default)

Copy/paste topic instructions, action configs, KB articles, and case data directly into the conversation. The skill parses and analyzes whatever you provide.

### Input Mode: Org-Connected

If you have **MCP Adaptor** connected to the customer org, tell the skill and it will pull configs directly:

```
/sra-config-analysis-shared [topic name] — connected to org
```

The skill will query:

| What | How |
|------|-----|
| Topic instructions | Query `GenAiPlannerDefinition` / `BotVersion` for topic config |
| Action configs | Query `GenAiFunction` for action definitions, inputs, outputs |
| KB articles | Query `Knowledge__kav` (or custom article type) for published articles assigned to this topic's data library |
| Case data | Query `Case` for a sample case matching this topic's classification |
| Context variables | Query `GenAiContextVariable` for variables referenced in instructions |

**Requirements for org-connected mode:**
- MCP Adaptor configured and authenticated to the target org
- API access to the objects above (most require Setup access or API-enabled profile)
- If the org uses custom Knowledge article types, you may need to specify the object name

**Fallback:** If MCP Adaptor can't access something (permissions, custom objects), the skill falls back to asking you to paste that piece manually. You can mix modes — e.g., pull topic config from org but paste a transcript manually.

---

## Analysis Framework

### Phase 1: Configuration Extraction

Parse the provided configuration into structured components (from paste OR org query):
- **Topic metadata** — name, API name, classification, scope
- **Instructions** — numbered, with channel guards and conditional logic identified
- **Actions** — name, description, inputs (required/optional), outputs (CLT/text), HiL settings
- **Context variables** — referenced in instructions
- **Channel behavior** — which instructions apply to which channel

### Phase 2: Variance Analysis

Apply SRA domain knowledge to identify variance sources:

#### 2a. Planner Reasoning Variance (Dynamic Plan Prompt — ReAct/Java Planner)
The Java planner uses a **ReAct loop** (Think → Act → Observe) with a structured dynamic plan prompt. On each turn, the planner scans three equal-weight metadata sources (Procedural Instructions → Policies → Tools), selects ONE atomic next step, scores available tools, and generates a grounded response. Key variance points:
- **CSR_SIGNAL ambiguity** — planner classifies utterances as EXPLICIT_CONFIRM (step complete) or DATA_ONLY (step incomplete). Ambiguous CSR language causes inconsistent step advancement.
- **Multiple PI entries matching same state** → planner must atomize and merge; redundant conditions waste tokens and may produce different `pi_*` labels across runs
- **Instruction-action misalignment** — instructions (PI) promise one thing; tool scoring evaluates something else. Tool may score < 8 and fall back to MANUAL unexpectedly.
- **PROACTIVE_MODE vs STOP-AND-WAIT instructions** — planner's core objective says "never wait passively" but instructions may say "STOP AND WAIT." Direct conflict.

**NOTE:** The 4-header model (Gather Info / Work Issue / Resolve / Wrap Up) and deliberation pattern (3 experts) apply to **Guidance Plans only**, NOT to the dynamic plan prompt used by SRA today.

#### 2b. Action-Instruction Misalignment
Compare what instructions PROMISE vs what actions REQUIRE:
- Instructions say "X is enough to proceed" but action requires X + Y + Z
- Instructions say "execute action" but action has "Collect data from user" on missing inputs
- Instructions say "display output" but action uses CLT rendering (double-display risk)

#### 2c. Channel Isolation
Check every instruction for channel guards:
- Guarded instructions: correctly scoped
- Unguarded instructions: apply to ALL channels — check for channel-specific language ("in response", "in the chat", "on the page")

#### 2d. Temporal/State Variance
Identify where the SAME utterance produces different behavior based on:
- Case field state at session start (pre-populated vs blank)
- Session history (first turn vs subsequent)
- Prior verification attempts (counter state)
- Time since last interaction

#### 2e. Classification Boundary
Check classification description against instruction coverage:
- Does classification attract utterances the instructions can't handle?
- Are product/category exclusions enforced in instructions?
- Is there overlap with other topics?

#### 2f. Knowledge Article Alignment (if KB provided)
Compare the Knowledge Article content against instructions:
- Does the article structure match what instructions expect? (e.g., numbered steps that can be delivered one-at-a-time)
- Does the article contain information for ALL conditions in instructions, or only some?
- Are there steps in the article that NO instruction references? (orphan knowledge — planner may hallucinate steps from it)
- Is the article length within the 65K truncation limit?
- Does the article use the same terminology as the instructions? (mismatch = retrieval may fail)

#### 2g. Real Interaction Trace (if transcript/email provided)
Walk through the provided sample interaction turn-by-turn:
- What would the planner do on Turn 1 with this exact input?
- Which instruction conditions are met/unmet based on real case field values?
- Where does the CSR's natural language differ from what instructions expect?
- Where would INPUT_FORMs appear that the CSR doesn't expect?
- How many LLM calls would this interaction consume? (approaching 8-call limit?)

### Phase 3: Edge Cases

Systematically generate edge cases across all 7 categories:

1. **Input Validation** — empty fields, special characters, boundary values, ambiguous text
2. **Data States** — pre-populated vs blank, stale data, conflicting values between fields and utterance
3. **System States** — plan generation timeout, concurrent modifications, session expiry
4. **Permissions** — action permissions vs topic visibility, FLS restrictions
5. **Flow Interruptions** — page refresh mid-flow, navigation away, session restart
6. **Integration Failures** — action returns empty, action times out, action returns error
7. **SRA-Specific** — plan generation lifecycle, multi-agent routing, gater interactions, RecActorActionFeed persistence

### Phase 4: Test Cases

Generate test cases mapped to the **9 Dynamic Plan Quality Goals**:

| # | Goal | What We're Testing |
|---|------|--------------------|
| 1 | Determinism | Same inputs → same NEXT step and EXECUTION_TYPE on repeated runs |
| 2 | Exhaustivity | All relevant PI/Policy/Tool sources discovered in Phase 2A scan |
| 3 | Conciseness | ###RESPONSE is actionable, ≤2048 tokens, no filler |
| 4 | Atomicity | NEXT step is ONE atomic task |
| 5 | Tool Selection | Correct tool scored ≥8 and selected for AUTO steps |
| 6 | Step Advancement | CSR_SIGNAL correctly classified (EXPLICIT_CONFIRM → COMPLETE; DATA_ONLY → INCOMPLETE) |
| 7 | Self-Contained Steps | ###RESPONSE includes all specifics CSR needs to act |
| 8 | No Duplication | Completed steps not re-proposed |
| 9 | Issue State Awareness | Planner checks conversation history; respects prior work |

**Additional test dimensions:**
- **PROACTIVE_MODE compliance** — Does planner propose next step without being asked?
- **Groundedness** — Is ###RESPONSE grounded in metadata only?
- **Persona** — Agent speaks TO CSR, not AS CSR?
- **Intent classification** — CONT vs NEW vs ASK correctly identified?
- **8-call limit safety** — Complex flows don't exhaust LLM calls before resolution?

For each variance source, write at least one test case that DEMONSTRATES the variance.

### Phase 5: Trace Prediction

For each critical variance source, predict what a session trace would show:
- Where INPUT_FORM_PRESENTED appears unexpectedly
- Where planner re-plans mid-session due to unexpected state
- Where the 8-call limit would be hit
- Token usage patterns (instruction loading overhead)

### Phase 6: Setup Issues

Check for configuration-level problems:
- Knowledge sources connected? (if knowledge action is attached)
- Action inputs aligned with context variable mappings?
- HiL (confirmation) gates appropriate?
- Channel routing consistent?
- Product/entity exclusions enforced?

### Phase 7: Recommendations & Output

Produce:
1. **Variance summary table** — all sources ranked by severity
2. **Fix recommendations** — P0 (before production), P1 (before scale), P2 (quality improvement)
3. **Test case set** — ready for Testing Center or manual validation
4. **Slack post** — formatted for team distribution

---

## Severity Classification

| Severity | Definition | Example |
|----------|-----------|---------|
| **CRITICAL** | Agent produces wrong action or unscripted behavior | Action requires inputs instructions don't mention |
| **HIGH** | Agent produces inconsistent plans across runs | AND/OR logic conflicts |
| **MEDIUM** | Agent produces suboptimal but not wrong behavior | Ambiguous confirmation handling |
| **LOW** | Agent behavior is correct but confusing to CSR | Draft vs send language |

---

## Output Format

### Variance Analysis

```markdown
# Variance Analysis: [Topic Name] — [Channel]

**Date:** [today]
**Customer:** [customer name]
**Agent:** [agent name] (Version [X])
**Topic:** [topic name]
**Channel:** [Email/Messaging/Voice/All]

## Executive Summary
[2-3 sentences: how many variance sources, root causes, severity distribution]

## Variance Sources (Ranked)
### CRITICAL
#### V1: [Title]
- The Problem
- Planner Impact
- Real-World Example (from provided artifacts)
- Test Case

### HIGH
...

## Real Case Walkthrough
[Turn-by-turn trace of the provided sample interaction against this config]

## Edge Cases
[By category]

## Test Cases
[Mapped to 9 quality goals]

## Knowledge Article Assessment
[If KB provided: alignment issues, truncation risk, terminology gaps]

## Setup Issues
[Checklist]

## Recommendations
### P0 — Fix Before Production
### P1 — Fix Before Scale  
### P2 — Improve Quality
```

### Slack Post

Formatted for team distribution. Includes:
- Severity-grouped findings
- Top recommendations
- Real case example
- Offer to walk through or run test cases

---

## Domain Knowledge (Built-In — No External Dependencies)

Key platform facts that inform this analysis:

### SRA Platform Positioning (Check FIRST)

SRA is a **custom employee-facing agent** — NOT a generic Agentforce agent:

| Dimension | SRA Is | SRA Is NOT |
|---|---|---|
| Agent type | Custom employee-facing assistant | AEA (Agentforce for Everyone Agent) |
| Builder | **Legacy Agentforce Builder** | New Agentforce Builder (NGA) |
| Script | ❌ Not supported (requires NGA) | Agent Script |
| Planner | **Legacy Java/ReAct planner** | Python Daisy planner |
| Rendering | **ACC rendering engine** (SPA SF team) | ACC Panel |
| UI surface | **Embedded LWC panel** in rep's console | AEA popout panel |

**System Prompts:** SRA prompts live in Prompt Builder but are NOT customer-accessible. Customers cannot modify temperature, model, or prompt text. They control behavior ONLY through topic instructions, action configs, and knowledge articles. Exceptions: Case Catch-Up & Insights, and individual Agentforce Actions (action-level prompt templates).

If a feature requires NGA, AEA, Agent Script, or the new builder → SRA does NOT support it today. Always validate Agentforce features against this matrix before including in analysis.

### SRA Is ALWAYS Rep-Facing

SRA (Service Rep Assistant) is an **employee-facing agent only**. It renders in the CSR's Agentforce sidebar and suggests actions/responses to the rep. The customer NEVER sees SRA output directly — only what the rep chooses to type/send. This means:
- "Show in conversation" renders to the **rep's sidebar**, not to the customer
- Anti-dumping enforcement is about controlling what the rep sees/does, not about hiding from the customer
- INPUT_FORMs appear to the **rep**, not the customer
- CLT cards render in the **rep's console**, not in the customer's chat

Do NOT frame SRA findings as "customer-facing" or speculate about customer visibility. The customer channel (email, messaging, voice) is between the rep and customer — SRA sits beside the rep.

### Current Planner: Java/React Planner (Dynamic Plan Prompt)

**The Dynamic Plan Prompt is how we inject into and control the Java/ReAct planner.** Architecture diagram (also shows closed-circuit grounding for Guidance Plans): https://lucid.app/lucidspark/66b7cd57-02d1-489b-a879-0ba9fb4d7279/edit?page=0_0&invitationId=inv_198d4572-a2fe-4332-8edf-fce12411af7d#

- **Architecture:** ReAct loop (Think → Act → Observe) with a **structured reasoning framework** inside the Think step. The LLM outputs `###REASONING` + `###RESPONSE` sections following a multi-phase pipeline.
- **ONE step per turn:** ORDERING contains exactly ONE step — the next PENDING step. The planner structurally advances one atomic step at a time. This is the native plan cadence.
- **Non-deterministic by design:** "Execution is non-deterministic and completely dependent on LLM capabilities." Same input can select different actions across runs.
- **Cannot transition between topics** within a session in the current Java planner.

#### Dynamic Plan Prompt — Phase Structure

| Phase | Purpose | Variance Impact |
|-------|---------|-----------------|
| 1: Understand | Review conversation history, verify step completion | Checks CSR_SIGNAL for COMPLETE vs INCOMPLETE |
| 2A: Discover | Scan ALL three metadata sources (PI → Policies → Tools) | Order matters: PI scanned FIRST |
| 2B: Select | Choose NEXT_STEP, validate atomicity | Single step selected; multi-source merge |
| 2C: Tool Plan | Score tool (0-10), validate parameters | Execute only if score ≥ 8 |
| 2D: Response | Draft message implementing NEXT_STEP | Must be grounded in metadata |
| 3: Self-Correct | Verify alignment, up to 3 retry cycles | Built-in self-correction |

#### Three Metadata Sources (EQUAL WEIGHT)

1. **Policies** (`policies`) — Array of strings with `name: X description: ...` format. Topic instructions that define rules/workflows.
2. **Procedural Instructions** (`procedural_instructions`) — Array of plain text strings. Topic instructions that define step-by-step procedures. Split into atomic steps, assigned `pi_<verb>_<target>` labels.
3. **Tools** (`function_outputs`) — Array of objects where keys = function names. Actions available to the agent.

**Key:** All three are scanned, atomized, and merged. Steps from different sources with same verb+target are MERGED into one step with multiple sources. Order in metadata is ARBITRARY — planner evaluates semantic merit, not position.

#### CSR_SIGNAL Classification (Critical for Variance)

| Signal | Meaning | Step Status |
|--------|---------|-------------|
| EXPLICIT_CONFIRM | CSR said "done"/"verified"/"completed"/"confirmed" | → can mark COMPLETE |
| DATA_ONLY | CSR provided info but NO completion word | → must stay INCOMPLETE |

**INPUT ≠ COMPLETION:** A step is NEVER complete just because inputs are available. Requires explicit confirmation OR successful tool execution.

#### Intent Classification

| Intent | Trigger | Behavior |
|--------|---------|----------|
| CONT | Affirms, provides info, or unclear | Resume last proposed step |
| NEW | Explicit redirect ("instead", "actually") | Match new direction from ORDERING |
| ASK | Question (what/how/why/?) | Answer directly, skip step logic |

#### Tool Scoring (0-10)

Tools execute ONLY if score ≥ 8 AND Relevance > 0 AND Policy Alignment > 0:
- Relevance (0-2): Does tool address the step?
- Input Availability (0-2): Are parameters available?
- Policy Alignment (0-2): Is usage permitted?
- Output Usefulness (0-2): Does it advance resolution?
- Non-Substitution (0-2): No better alternative?

#### Key Constraints

- **PROACTIVE_MODE:** "Propose next step proactively. Never wait passively for instructions. Anticipate what comes next."
- **Persona:** Agent speaks TO the CSR, not to the customer. "Ask the customer to..." not "Dear Customer..."
- **Seed plan NOT authoritative:** Early outline of issue, "frozen snapshot", explicitly forbidden as input for step discovery. Metadata + conversation history = authoritative.
- **Groundedness:** Response for CONT/NEW must contain ONLY metadata/context/conversations. No external knowledge for step execution.
- **MAX_LLM_CALLS_PER_REQUEST = 8:** Hard limit per user turn.
- **LLM Response limit: ~2048 tokens.** Truncated if exceeded.
- **Action output truncation: ~65,000 characters.**
- **128K total context window** for the underlying model.
- **Groundedness check on every response** — ungrounded responses get rewritten.

### Knowledge Retrieval Architecture

**How SRA retrieves knowledge at runtime:**

SRA uses **Search Knowledge action → Data Cloud Retriever → hybrid_search** — NOT prompt retrievers (ADL construct).

| Source Type | Ingestion Path |
|---|---|
| Salesforce Knowledge | Structured → DMO → Search Index → Retriever |
| SharePoint, Google Drive, OneNote | Enterprise Knowledge connector → UDLO → UDMO → HUDMO → Search Index → Retriever |
| Jira (GA Spring '26) | EK Jira connector → same HUDMO pipeline |
| Web content | EK Web Crawler → same HUDMO pipeline |
| Multiple sources | Individual retrievers → Ensemble Retriever (combines all) |

**Key facts for config analysis:**
- Retrieval is **hybrid** (vector similarity + keyword) — not keyword-only
- **Enterprise Knowledge for Agentforce** is GA (Jul 2025) — requires Data Cloud (Data 360) provisioned
- Results ranked by hybrid relevance score; result count is admin-configurable in action config
- SRA displays **citations** to the rep (article source + chunk metadata)
- **System knowledge** (fetched once at plan start from Case Subject+Description) persists all turns
- **Runtime knowledge** (fetched every turn from latest utterance + topic) is ephemeral
- Citations only track runtime knowledge — system knowledge hits show `citedReferences: []` (known gap, not hallucination)

**Prompts are FORKED between Guidance and Dynamic:**
- The prompt that consumes retrieved knowledge is completely different per plan type
- Guidance Plans and Dynamic Plans retrieve from the same infrastructure but use the content differently
- Always consider WHICH plan type when analyzing knowledge retrieval variance

**Variance sources in knowledge retrieval:**
- Summary field blank → retrieval misses (vector has nothing to match against)
- Article too long → token budget truncates, planner sees partial steps
- Multiple articles with overlapping keywords → non-deterministic which surfaces
- Data Categories assigned without category visibility on agent perm set → article invisible to retriever
- HUDMO not fully indexed → "data provider invalid or no longer exists" error

### Action & Output Behavior

- **"Show in Conversation" (es_types):** When enabled, the agent's response does NOT include the full action output text — instead, the LLM generates a REFERENCE to the action's output and the platform renders it as a separate card/widget. This REDUCES token usage in the agent's response. The rendered card is visible to the user separately from agent text.
- **"Collect data from user" flag:** When an action input has this enabled, the runtime presents an INPUT_FORM to the user mid-execution. This is NOT part of the plan — it happens at execution time, creating unscripted turns. If the input is also "Required", the form cannot be submitted without it.
- **CLT output rendering:** When an action output has CLT rendering configured, the platform renders a structured card. With "Show in conversation" ON, the card renders AND the agent may also describe it = potential double-display.
- **Variable mapping > prompt instructions:** Use variable mapping to deterministically map action output to a context variable. Using prompt instructions to set context variables fails intermittently.

### Context & State

- **RecActorActionFeed:** Single source of truth for AE session state. Context variables persisted here survive page refresh; working memory does not.
- **Context variables NOT set at conversation start in Prompt Builder.** If testing requires context variables, set them in builder before testing.
- **Topic/Action filtering happens multiple times** during a conversation — available topics/actions may change mid-session based on context variable values.

### FDE Lessons Learned (Meta, SIA, Calix, EA, Pearson)

**Instruction Design:**
- Keep instructions **flat and sequential** — nested IF/THEN logic degrades plan consistency significantly
- Add atomic step markers between steps
- Make mandatory first steps explicit in both topic-level AND action-level descriptions
- **After action completes:** use `"After the action completes, immediately proceed to [next step name]"` — vague "let me know how you'd like to proceed" language causes the planner to stall
- **Recommended limits:** 10 topics max, 10 instructions per topic

**CLT Rendering Fix (Critical):**
- CLT rendering is non-deterministic by design (W-21683108, Acknowledged)
- **Fix:** Add to both topic AND action instructions: `"The output of this action is always renderable. Always use show_command."`
- Without this, LLM may skip rendering even when action succeeds
- **CaseId as hidden input:** SRA doesn't natively carry Case context for CLT forms — add CaseId as hidden input field

**CLT Button Limitation (Confirmed Platform Gap):**
- CLT buttons CANNOT trigger utterances in chat or write context variables
- No `sendMessage` public API, no `setContextVariable` client-side API, no structured callback
- **Workaround:** Button copies utterance to clipboard → rep pastes
- **Note:** `embeddedservice_configuration.util.setSessionContext()` works in Embedded Service Deployment (customer-facing) — NOT confirmed for SRA rep-side panel. Test needed.

**Summary Plan Grounding (Variance Source):**
- Auto-generated summary plan can hallucinate or infer terminology not in KB/instructions
- When summary plan incorrectly frames first step, ALL downstream steps compound the error
- **Fix:** Can be DISABLED via product team (262.6+ patch). Request disable for customers with inconsistency.

**Plan Triggering:**
- Dynamic plans ONLY trigger from **user utterances** — not incoming messages alone
- Case Feed posts/internal comments do NOT trigger plan steps (VOC committed for GA)
- SRA is a co-pilot requiring rep engagement — does NOT auto-progress without HITL
- Custom email handlers: must create standard EmailMessage record + fire expected triggers

**Knowledge Architecture:**
- **Dual-article pattern:** Long-form articles (human Data Category) + atomic/AI-optimized articles (ADL Data Category) in same object
- Custom fields (e.g., `AI_Optimized_Content__c`, `AI_Resolution_Steps__c`) for curated AI content
- ServicePlanner User needs read access to **published articles only** — draft/archived access increases retrieval noise
- ADL field configuration matters — verify via Splunk/trace that correct fields are passed to prompt

**Permissions & Licensing:**
- **ServicePlannerUser ALSO needs Unmetered PSL** — not just end users (metering surprise)
- **`View Setup and Configuration`** permission required for ServicePlannerUser (access to RecActorFeatureDef) — security concern, product fix coming
- Custom Apex must use `with sharing` to avoid unintended flex credit metering

**Messaging Session:**
- Only chat transcript available OOTB — no related Case fields without workaround
- **Hyperforce migration risk:** Can silently break SRA on Messaging (Falcon instance gap). Validate broker deployment before go-live.
- Plan for 1-week validation window post-migration

**Deployment:**
- package.xml must include: `Bot` + `BotVersion` + `GenAiPlannerBundle` together
- Sandbox refresh resets Beta org perms (re-request from product team)
- Row lock errors on agent activation after deployment — typically self-resolve on retry

**DO NOT USE screen flows in SRA:**
- Screen flows lose state on page refresh → duplicate actions, poor UX
- Use auto-launched flows + CLT outputs instead
- Store flow progress in Case fields if resume functionality needed

**Scope Constraints:**
- SRA cannot read email attachments or embedded images
- URLs in Messaging break intent classification (HTML auto-rendering)
- General FAQ topic recommended for all implementations (prevents failures on non-matching queries)

### Limits Quick Reference

| What | Limit | Impact |
|------|-------|--------|
| LLM calls per turn | 8 | Error after exceeding |
| LLM response | ~2048 tokens | Truncation |
| Action output | ~65,000 chars | Truncation |
| Context window | ~128K tokens | Hard model limit |
| Topics | ~10 recommended | No hard limit but consistency degrades |
| Instructions per topic | ~10 recommended | Complexity degrades plan quality |

---

## How to Use This Skill

### Step 1: Gather the config
In the customer's org (Agent Builder), collect:
- Topic instructions (full text — copy/paste or screenshot)
- Classification description and scope
- Actions list + each action's config (inputs, outputs, HiL, settings)

### Step 2: Gather sample artifacts
From the customer's org or from the FDE's testing:
- A Knowledge Article this topic retrieves
- A sample inbound case email or messaging transcript
- A case record showing field values

### Step 3: Paste everything and invoke
```
/sra-config-analysis-shared Hardware Product Support

[paste topic instructions]
[paste action configs]
[paste KB article]
[paste case email or transcript]
```

### Step 4: Get your analysis
The skill produces:
- Ranked variance sources with severity
- Real case walkthrough (turn-by-turn)
- Edge cases by category
- Test cases mapped to quality goals
- Fix recommendations (P0/P1/P2)
- Slack post ready to share

---

## Differences from Internal Version

| Feature | Internal (`sra-config-analysis`) | Shared (`sra-config-analysis-shared`) |
|---------|----------------------------------|--------------------------------------|
| Slack search | ✅ Searches internal channels live | ❌ No Slack dependency |
| Codesearch | ✅ Can look up Java planner source | ❌ No codesearch dependency |
| Google Docs | ✅ Can pull Beta Docs | ❌ No Google dependency |
| Domain knowledge | ✅ Built-in + live lookup | ✅ Built-in only (comprehensive) |
| Customer data | ⚠️ Requires org access | ✅ Works from pasted/attached data |
| Output quality | Full | Full (same framework, same rigor) |

The shared version contains ALL the domain knowledge needed to produce a complete analysis. The only difference is that live lookups for new/undocumented planner behaviors are unavailable — if you hit something the skill doesn't know, escalate to #temp-sra-fde-pioneers or your SRA PM.

---

## Rules

- **READ-ONLY** — Never modify the customer's org, agent, topic, or action configuration. Analysis only.
- **Always ask for sample artifacts** — If the user only provides topic config without KB articles, case emails, or transcripts, prompt them to provide these before proceeding with analysis.
- **Always cite the specific instruction/action** that causes each variance
- **Always include test cases** — abstract analysis without concrete examples isn't actionable
- **Always include a real case walkthrough** — if sample data provided, trace it turn-by-turn
- **Distinguish "wrong" from "inconsistent"** — wrong = agent does something harmful. Inconsistent = agent does different valid things. Both are variance but severity differs.
- **Don't assume intent** — if instructions are ambiguous, flag it as ambiguous. Don't guess what the author meant.
- **Rate severity honestly** — not everything is CRITICAL. Use the severity definitions.
- **Retain customer context** — since this skill can't call Slack/codesearch, everything you learn about the customer's setup lives in the conversation. Reference it throughout.

---

## Installation

1. Copy this `SKILL.md` into your `~/.claude/skills/sra-config-analysis-shared/` directory
2. **That's it.** No other skills needed — all domain knowledge from `sra-expert`, `sra-edge-cases`, `sra-agent-debugger`, `sra-test-case-writer`, `sra-setup-debug`, and `sra-recall` is baked into this single file.
3. Works with any AI Suite / Claude Code installation

**You do NOT need to install:**
- `sra-expert` / `sra-expert-shared`
- `sra-edge-cases`
- `sra-agent-debugger`
- `sra-test-case-writer`
- `sra-setup-debug`
- `sra-recall`

This skill contains all their relevant domain knowledge internally. It references them as methodology but does not call them as separate tools.

**Optional: Org connection**
If you have MCP Adaptor connected to the customer org, the skill can pull topic instructions, action configs, and KB articles directly — no pasting needed. See "Input Mode: Org-Connected" below.

**Shared skills repo:** https://git.soma.salesforce.com/chad-goldsmith/claude-skills

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-24 | Initial shared version — forked from internal sra-config-analysis with self-contained domain knowledge, artifact collection prompts, KB alignment analysis, and real interaction trace phases |
