---
name: sra-config-analysis
description: Analyze Agentforce Service Assistant topic configurations for variance, edge cases, and quality issues. Given a topic's instructions, actions, classification, and scope, produces a comprehensive analysis covering planner behavior, action alignment, channel isolation, edge cases, and test cases. Leverages sra-expert, sra-edge-cases, sra-agent-debugger, sra-test-case-writer, sra-setup-debug, and sra-recall.
tools: [Read, Write, Edit, Bash, Agent, mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_google-workspace_vmcp-google-workspace__get_doc_as_markdown, mcp__plugin_codesearch_codesearch__search, mcp__plugin_codesearch_codesearch__blob]
---

# SRA Configuration & Behavior Analysis

> Analyze any Agentforce Service Assistant topic configuration and identify what causes non-deterministic behavior. Produces variance analysis, edge cases, test cases, and fix recommendations — grounded in SRA platform knowledge.

**Invocation:** `/sra-config-analysis [topic name or paste config]`

---

## What This Skill Does

You provide a topic configuration (instructions, actions, classification, scope). The skill:

1. **Identifies variance sources** — where different utterances or data states produce inconsistent behavior
2. **Maps edge cases** — across 7 categories (input validation, data states, system states, permissions, flow interruptions, integration failures, SRA-specific)
3. **Checks action alignment** — do action required inputs match what instructions promise?
4. **Evaluates planner impact** — how does the ReAct planner (dynamic plan prompt) interpret these instructions?
5. **Generates test cases** — mapped to the 9 prompt quality goals
6. **Produces fix recommendations** — prioritized P0/P1/P2
7. **Writes a Slack-ready summary** — for FDE team distribution

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
| ⭐ | Sample cases (screenshots or field values) | Service Console → Case record |
| ⭐ | Relevant Knowledge Articles (full text) | Knowledge tab → Article used by this topic |
| ⭐ | Sample case emails or message transcripts | Case Feed → Email thread / Messaging transcript |
| Optional | Channel context (Email, Messaging, Voice, or all) | User specifies |
| Optional | Known issues or symptoms | User describes |
| Optional | Apex code for custom actions | Developer Console or VS Code |

⭐ = Strongly recommended for complete analysis. Without action configs, the skill can still analyze instruction logic but cannot identify action-instruction misalignment (the #1 variance source).

### Why Sample Artifacts Matter

The skill MUST ask for these if not provided — they are the difference between theoretical analysis and real-world variance detection:

| Artifact | What It Reveals |
|----------|----------------|
| **Knowledge Articles** | Whether "Answer Questions with Knowledge" retrieves useful content; whether article structure aligns with anti-dumping cadence; whether instructions reference KB steps that don't exist |
| **Case Emails (inbound)** | Real customer language that triggers classification; identifier formats the planner must parse; ambiguous phrasing that tests CSR_SIGNAL logic |
| **Message Transcripts** | Multi-turn interaction patterns; where CSR gets stuck; actual confirmation phrases used (vs magic phrases required); turn counts for HiL/INPUT_FORM flows |
| **Case Field Values** | Pre-populated vs blank fields at session start; which conditions in instructions evaluate true/false; data the planner can ground on vs data it must request |

**Prompt to user if artifacts are missing:**
> To complete this analysis, I need sample artifacts from the org. Can you provide:
> 1. **A relevant Knowledge Article** — the full text of an article this topic would retrieve (e.g., the troubleshooting guide for this product)
> 2. **A sample case email or message transcript** — a real or representative customer interaction that would trigger this topic
> 3. **A case record screenshot** — showing field values (Subject, Description, Status, Contact Email, any custom fields referenced in instructions)
>
> These let me trace exactly how the planner processes real inputs — not just theoretical paths.

---

## Analysis Framework

### Phase 1: Configuration Extraction

Parse the provided configuration into structured components:
- **Topic metadata** — name, API name, classification, scope
- **Instructions** — numbered, with channel guards and conditional logic identified
- **Actions** — name, description, inputs (required/optional), outputs (CLT/text), HiL settings
- **Context variables** — referenced in instructions
- **Channel behavior** — which instructions apply to which channel

Save raw extraction to: `topics/<topic-slug>-raw.md`

### Phase 2: Variance Analysis (sra-expert + sra-recall)

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

### Phase 3: Edge Cases (sra-edge-cases)

Systematically generate edge cases across all 7 categories:

1. **Input Validation** — empty fields, special characters, boundary values, ambiguous text
2. **Data States** — pre-populated vs blank, stale data, conflicting values between fields and utterance
3. **System States** — plan generation timeout, concurrent modifications, session expiry
4. **Permissions** — action permissions vs topic visibility, FLS restrictions
5. **Flow Interruptions** — page refresh mid-flow, navigation away, session restart
6. **Integration Failures** — action returns empty, action times out, action returns error
7. **SRA-Specific** — plan generation lifecycle, multi-agent routing, gater interactions, RecActorActionFeed persistence

### Phase 4: Test Cases (sra-test-case-writer)

Generate test cases mapped to the **9 Prompt Quality Goals**:

| # | Goal | What We're Testing |
|---|------|--------------------|
| 1 | Determinism | Same inputs → same plan on repeated runs |
| 2 | Exhaustivity | All relevant steps included; no irrelevant steps |
| 3 | Conciseness | Steps are direct imperatives, no filler |
| 4 | Atomicity | One discrete action per step |
| 5 | Dev Name Assignment | Correct action dev names on plan steps |
| 6 | Step Advancement | Correct CSR_SIGNAL classification (EXPLICIT_CONFIRM vs DATA_ONLY) |
| 7 | Self-Contained Steps | All specifics included |
| 8 | No Duplication | No redundant steps |
| 9 | Issue State Awareness | Completed steps not re-included |

For each variance source, write at least one test case that DEMONSTRATES the variance — paired inputs that should produce the same output but don't.

### Phase 5: Trace Prediction (sra-agent-debugger)

For each critical variance source, predict what a session trace would show:
- GenOpPlan step count vs actual execution turns
- Where INPUT_FORM_PRESENTED appears unexpectedly
- Where planner re-plans mid-session due to unexpected state
- Token usage patterns (instruction loading overhead)

### Phase 6: Setup Issues (sra-setup-debug)

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
3. **Test case set** — ready for Testing Center CSV or manual validation
4. **Slack post** — formatted for FDE team distribution

Save to: `findings/<topic-slug>-variance-analysis.md`

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

### Variance Analysis (findings/<topic-slug>-variance-analysis.md)

```markdown
# Variance Analysis: [Topic Name] — [Channel]

**Date:** [today]
**Agent:** [agent name] (Version [X])
**Topic:** [topic name]
**Channel:** [Email/Messaging/Voice/All]
**Org:** [org identifier]

**Skills Applied:** sra-expert, sra-edge-cases, sra-agent-debugger, sra-test-case-writer, sra-setup-debug, sra-recall

## Executive Summary
[2-3 sentences: how many variance sources, root causes, severity distribution]

## Variance Sources (Ranked)
### CRITICAL
#### V1: [Title]
- The Problem
- Planner Impact
- Trace Signature
- Test Case

### HIGH
...

## Edge Cases
[By category]

## Test Cases
[Mapped to 9 quality goals]

## Setup Issues
[Checklist]

## Recommendations
### P0 — Fix Before Production
### P1 — Fix Before Scale  
### P2 — Improve Quality
```

### Slack Post (findings/<topic-slug>-slack-post.md)

Formatted for Slack distribution. Includes:
- Skills attribution line
- Severity-grouped findings
- Top recommendations
- Offer to walk through or run test cases

---

## Domain Knowledge (from sra-recall)

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

**INPUT ≠ COMPLETION:** A step is NEVER complete just because inputs are available. Requires explicit confirmation OR successful tool execution. This is why "magic phrase" dependencies create variance — the planner needs unambiguous EXPLICIT_CONFIRM to advance.

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
- **MAX_LLM_CALLS_PER_REQUEST = 8:** Hard limit per user turn. After 8 LLM calls, planner stops with error.
- **LLM Response limit: ~2048 tokens.** Truncated if exceeded.
- **Action output truncation: ~65,000 characters.**
- **128K total context window** for the underlying model.
- **Groundedness check on every response** — ungrounded responses get rewritten.
- **Model:** Currently GPT4Omni (llmgateway__GPT4Omni_11_20).

### Java Planner Retirement → Python Planner (Daisy/Daisy++/Unified Planner)

**Name aliases (all the same thing):** Daisy = Atlas = Python Planner = Reasoner = Daisy++ = Unified Planner

**Target cutover:** October 2026. SRA currently on Java Planner + Legacy Builder.

| Dimension | Java Planner (SRA today) | Python Planner (future) |
|---|---|---|
| Runtime | JVM | Python-based |
| Reasoning | ReAct loop | Multi-step planning, better chain-of-thought |
| Model routing | SFAP endpoint | Different LLM Gateway routing |
| Action timeout | 90s | **75s** — silent breaking change |
| Token/base64 | Correct | **Bug:** corrupts base64 chars (blocks migration) |
| HyperClassifier | No | Yes — mid-flow reclassification risk (W-22372560) |
| PI sensitivity | Baseline | Different false-positive rates |

**Migration blockers:**
1. Custom agent type `ServicePlanner` not supported in NGA
2. Base64 token corruption in Daisy++
3. Action timeout regression (75s vs 90s) — requires full action audit

**Pre-migration requirements:**
- Audit all Apex/Flow actions for runtime (75-90s range = will silently break)
- Test HyperClassifier impact on multi-subagent flows
- PI filtering regression testing between endpoints

**GA Guidance Plans:** Uses LLM Gateway ONLY — no AF action execution. Not affected by planner or builder differences at all.

- **Daisy Planner architecture:** State Machine / Agent Graph with programmatic hooks, guided determinism, multi-agent orchestration (SOMA/MOMA). Topics become "Nodes" with onInit, Before Reasoning, Guided Reasoning, Execute Actions, After Tool Hook, Transition lifecycle.
- **System 1 (LLM):** Creative brain for text generation, summarizing, classifying.
- **System 2 (Graph):** Executive function that double-checks LLM output against rules. Imposes business rules programmatically.
- **Key migration concern:** Moving from topics to nodes is a *product behavior change* requiring systematic validation — regression testing, hypothesis testing (10+ rounds), benchmarking (eVerse).

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
- **Prompts are FORKED:** Guidance Plans and Dynamic Plans use retrieved knowledge completely differently at the prompt layer. Same retriever infra, different consumption.
- **NGS (Chad's team)** — expert in Dynamic Plans knowledge retrieval
- **Sox (Chad's team)** — expert in Guidance Plans knowledge retrieval
- Retriever platform team (`#tmp-retrievers-trust`) owns the shared infra

**Variance sources in knowledge retrieval:**
- Summary field blank → retrieval misses (vector has nothing to match against)
- Article too long → token budget truncates, planner sees partial steps
- Multiple articles with overlapping keywords → non-deterministic which surfaces
- Data Categories assigned without category visibility on agent perm set → article invisible to retriever
- HUDMO not fully indexed → "data provider invalid or no longer exists" error
- Cross-org retriever query differences (sandbox vs prod can generate different JOIN conditions)
- Web Search Retriever results vary across sessions/users (provider-side variability)

**Channels for knowledge/retriever research:**
- `#tmp-retrievers-trust` (`C08ALF5TMS9`) — retriever infra bugs, hybrid_search issues
- `#enterprise-knowledge-for-service-cloud-enablement` (`C0A05CP17K8`) — EK + Service Cloud setup
- Data Cloud Unstructured (`C06AVRSNPEZ`) — EK announcements, connector releases

### Action & Output Behavior

- **"Show in Conversation" (es_types):** When enabled, the agent's response does NOT include the full action output text — instead, the LLM generates a REFERENCE to the action's output and the platform renders it as a separate card/widget. This REDUCES token usage in the agent's response. The rendered card is visible to the user separately from agent text.
- **"Collect data from user" flag:** When an action input has this enabled, the runtime presents an INPUT_FORM to the user mid-execution. This is NOT part of the plan — it happens at execution time, creating unscripted turns. If the input is also "Required", the form cannot be submitted without it.
- **CLT output rendering:** When an action output has CLT rendering configured, the platform renders a structured card. With "Show in conversation" ON, the card renders AND the agent may also describe it = potential double-display.
- **Variable mapping > prompt instructions:** Use variable mapping to deterministically map action output to a context variable. Using prompt instructions to set context variables fails intermittently because the LLM may not reliably extract/set the value.

### Context & State

- **RecActorActionFeed:** Single source of truth for AE session state. Context variables persisted here survive page refresh; working memory does not.
- **Context variables NOT set at conversation start in Prompt Builder.** If testing requires context variables, set them in builder before testing.
- **Topic/Action filtering happens multiple times** during a conversation — available topics/actions may change mid-session based on context variable values.

### Prompting & Variance Sources

- **Customers prompt planner via:** topic classification descriptions, topic instructions, action descriptions, action input descriptions, action output descriptions. ALL of these are in the LLM's context and affect behavior.
- **Nondeterminism is inherent** — "quite novel for customers, especially when they are used to a deterministic system such as Einstein Bots."
- **Token budget:** Each action description, instruction, and grounding document consumes tokens. More instructions = less room for case-specific context = higher risk of hitting response truncation.
- **Citations flow:** Action returns with citationsEnabled=True → sent to external citations service → trimmed to relevant ones → planner renders. Response citations are NOT viewable in plan tracer.

### FDE Lessons Learned (Meta, SIA, Calix, EA, Pearson)

**Instruction Design:**
- Flat, sequential instructions ONLY — nested IF/THEN degrades consistency
- Atomic step markers between steps; mandatory first steps explicit in topic + action descriptions
- Use `"After the action completes, immediately proceed to [next step name]"` — NOT open-ended "let me know"
- **Limits:** ~10 topics, ~10 instructions per topic recommended

**CLT Rendering Fix:** Add `"The output of this action is always renderable. Always use show_command."` to topic AND action instructions. Without this, LLM may skip rendering (W-21683108).

**CLT Button = Platform Gap:** Cannot trigger utterances, write context vars, or signal planner. Clipboard-copy → paste is the only workaround. `setSessionContext()` works in ESD (customer-facing) but NOT confirmed for SRA panel.

**Summary Plan Grounding:** Can hallucinate, compound errors. Can be DISABLED (262.6+). Request disable for inconsistency issues.

**Plan Triggering:** ONLY from user utterances. Case Feed posts/comments don't trigger. SRA = co-pilot, not auto-pilot.

**Knowledge:** Dual-article pattern (human + AI-optimized, different Data Categories). ServicePlanner needs published-only access. ADL field config matters — verify via Splunk.

**Permissions:** ServicePlannerUser needs Unmetered PSL + `View Setup and Configuration`. Custom Apex: `with sharing` to avoid metering.

**Messaging:** Only transcript available OOTB. Hyperforce migration can silently break SRA (Falcon instance gap).

**Deployment:** Bot + BotVersion + GenAiPlannerBundle in package.xml. Sandbox refresh resets Beta perms.

**DO NOT USE screen flows** — lose state on refresh. Use auto-launched flows + CLT instead.

**Scope:** Can't read attachments/images. URLs in Messaging break classification. Add General FAQ topic to all implementations.

### Limits Quick Reference

| What | Limit | Impact |
|------|-------|--------|
| LLM calls per turn | 8 | Error after exceeding |
| LLM response | ~2048 tokens | Truncation |
| Action output | ~65,000 chars | Truncation |
| Context window | ~128K tokens | Hard model limit |
| Topics | ~10 recommended | Consistency degrades beyond |
| Instructions per topic | ~10 recommended | Complexity degrades plan quality |

### Source Code (Internal)

The Java planner lives in the **gitcore monorepo** (core-262-public repository):

| File | Purpose |
|------|---------|
| `GenAiPlannerEntityRepository.java` | Entity/planner resolution |
| `SessionManagementServiceImpl.java` | Session lifecycle |
| `StandardContextVariableBuilder.java` | Context variable handling |
| `DynamicPlanStartServiceImpl.java` | Plan start logic |

**REST API (PlannerApiController):**
- `POST /planner/{plannerName}/sessions` — create session
- `POST /sessions/{session-id}/messages/stream` — send message (streaming)
- `DELETE /sessions/{session-id}` — end session

### Resources

- **Slack:** #planner-service-support (C04M12AQZM2) — planner team support channel (troubleshooting)
- **Slack:** #sc-service-planner-eng (C06TPK97CCE) — eng team, code changes, PRs, planner code pointers
- **Support Playbook:** Troubleshooting React Planner (AKA Java Planner) — covers prompting issues, session start errors, citations, truncation, escalation, filtering, permissions, URL redaction, context variables, model identification
- **Planner Evolution deck:** Java Planner → Python Daisy Planner architecture comparison, testing strategy for migration
- **Dynamic Plan Prompt:** Full structured reasoning template (Phase 1-3, CSR_SIGNAL classification, tool scoring, groundedness enforcement) — the actual system prompt driving the ReAct loop's Think step

---

## Rules

- **READ-ONLY** — Never modify the org, agent, topic, or action configuration. Analysis only.
- **Always cite the specific instruction/action** that causes each variance
- **Always include test cases** — abstract analysis without concrete examples isn't actionable
- **Always predict trace behavior** — what would sra-agent-debugger show?
- **Distinguish "wrong" from "inconsistent"** — wrong = agent does something harmful. Inconsistent = agent does different valid things. Both are variance but severity differs.
- **Don't assume intent** — if instructions are ambiguous, flag it as ambiguous. Don't guess what the author meant.
- **Rate severity honestly** — not everything is CRITICAL. Use the severity definitions.
- **Feed back learnings** — if this analysis reveals new SRA platform behavior, save to sra-recall memory
