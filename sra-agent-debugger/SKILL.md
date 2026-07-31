---
name: sra-agent-debugger
description: Trace and analyze SRA (Service Rep Assistant) Agent sessions for a given Case ID or MessagingSession ID. Pulls GenOpPlan (Summary Plan), RecActorActionFeed, and full Data Cloud session trace (interactions, messages, steps, gateway calls, actions, grounded records, retriever requests/responses, observability spans). Includes knowledge grounding analysis and per-turn planner context inspection. Use when user asks to debug, trace, or analyze an SRA agent session.
tools: [Bash, Read, Write, Edit]
---

# sra-agent-debugger — SRA Agent Session Trace & Analysis

Pulls all agent debugging data for a **Case ID** or **MessagingSession ID**: GenOpPlan (summary plan), RecActorActionFeed (action feed with knowledge grounding analysis), and Data Cloud STDM session trace. Outputs a structured analysis-ready text file with diagnostic annotations.

## If the user hasn't given enough to proceed

When invoked without an ID, print this verbatim:

> Which session should I trace?
>
> I need:
> - **Record ID** — either a Case ID (`500...`) or a MessagingSession ID (`0Mw...`)
> - **Org alias** — the `sf` CLI alias for the target org (e.g. `mySDO`, `MetaRLUAT`)
>
> I'll pull: GenOpPlan, RecActorActionFeed (with knowledge grounding check), and Data Cloud session trace data.

## When to use

Trigger this skill when the user:
- Asks to "debug / trace / analyze / inspect" an SRA agent session
- Wants to understand what the agent did, what plan it followed, what actions it took
- Asks "what happened on case/session X" in the context of agent behavior
- Wants to check if knowledge grounding worked (citedReferences)
- Wants agent data pulled for analysis
- Provides a MessagingSession ID (`0Mw...`) and asks about agent behavior
- Asks "is knowledge being used" or "why did it say no information in your documents"
- Asks about retrieval quality or why wrong articles are being surfaced
- Wants to see what context/tools/grounding was passed to the planner on each turn
- Asks about execution timing or performance of agent actions
- Says "inform engineering" or asks to draft a message/write-up for the eng team after a trace

## Getting Started

### Prerequisites

| Tool | Required |
|---|---|
| `sf` CLI (authenticated against the target org) | yes |
| Python 3.9+ | yes |
| Data Cloud enabled on the target org | yes (for full session trace; Core SOQL works without it) |
| AIPlatform Connector data streams active | yes (for DC tables to have data) |

### Installation

Clone this repo, copy `sra-agent-debugger/` into `~/.claude/skills/`. The `scripts/` directory contains the Python trace scripts.

### Quick Start

```bash
python3 ~/.claude/skills/sra-agent-debugger/scripts/trace_session.py --id 0MwXXXXXXXXXXXXXXX --org yourOrgAlias
```

### Output Location

```
~/.claude/data/sra-agent-debugger/<org>/<record_id>/trace_<timestamp>.txt
```

### Standalone Usage

This skill works standalone — no other skills or repos required. For org setup diagnostics (permissions, configuration), see the `sra-setup-debug` skill in this same repo.

## Pipeline

The skill runs a single script that:

1. Detects input type (Case ID vs MessagingSession ID) from prefix
2. For Case IDs: resolves Case Number, queries GenOpPlan via ParentId
3. For MessagingSession IDs: queries the session directly, looks up related Case (if any)
4. Queries `RecActorActionFeed` via `RelatedRecordId` (works for BOTH Case and MessagingSession)
5. Analyzes knowledge grounding: parses `citedReferences` from feed Content JSON
6. Resolves session UUIDs — primary method: extracts UUID from feed content `_links` URLs; fallback: pattern matching in DC messages
7. For each session: queries all 12 Data Cloud tables (see Data Sources below)
8. Outputs a structured `.txt` file with diagnostic annotations

## Data Sources (12 Data Cloud Tables)

### Session Trace (STDM)
| Table | What it provides |
|-------|-----------------|
| `AiAgentSession__dll` | Session metadata: channel, start/end time, end type |
| `AiAgentInteraction__dll` | Interactions within session: type, topic, timestamps |
| `AiAgentInteractionMessage__dll` | Messages: type, content, timestamp |
| `AiAgentInteractionStep__dll` | Steps: LLM_STEP, TOPIC_STEP, ACTION_STEP with input/output |
| `AiAgentSessionParticipant__dll` | Agent identity: API name, version |

### GenAI Gateway
| Table | What it provides |
|-------|-----------------|
| `GenAIGatewayRequest__dll` | LLM calls: feature, model, template, token counts |
| `GenAIGatewayResponse__dll` | LLM responses: timestamps |
| `GenAIGtwyRequestMetadata__dll` | Tool calls: action names, arguments |
| `GenAIGtwyObjRecord__dll` | Grounded records: KA record IDs, content |

### Knowledge Retrieval
| Table | What it provides |
|-------|-----------------|
| `AIRetrieverRequest__dll` | Query text sent to Data Library, retriever name, trace ID |
| `AIRetrieverResponse__dll` | Retrieved chunks: content, relevance score, source record ID |

### Observability
| Table | What it provides |
|-------|-----------------|
| `ObservabilitySpans__dll` | Execution waterfall: operation names (`run.interaction`, `run.topic.*`, `run.action.*`, `run.llmstep`), durations, parent-child span tree, status codes |

### Important: Table/Field Naming Convention

- Tables: NO `ssot__` prefix, suffix is `__dll` (not `__dlm`)
- Fields: camelCase, no `ssot__` prefix (e.g., `aiAgentSessionId__c`, `contentText__c`, `startTimestamp__c`)
- Gateway tables never had `ssot__` prefix — just the suffix changed from `__dlm` to `__dll`

## Invocation

### Text output (trace file):
```bash
python3 "$HOME/.claude/skills/sra-agent-debugger/scripts/trace_session.py" --id <record_id> --org <alias>
```

### HTML viewer (local web UI):
```bash
python3 "$HOME/.claude/skills/sra-agent-debugger/scripts/viewer.py" --id <record_id> --org <alias>
# Opens at http://127.0.0.1:8080
```

Flags:
- `--id` (required): 18-char Case ID (`500...`) OR MessagingSession ID (`0Mw...`)
- `--org` (required): sf CLI org alias
- `--max-sessions` (optional, default 3): max Data Cloud sessions to fully trace
- `--output` (optional): override output directory
- `--port` (optional, viewer only): HTTP port (default 8080)

## HTML Viewer Tabs

| Tab | What it shows |
|-----|--------------|
| **AI Summary** | Auto-generated narrative: conversation timeline, actions invoked (dev names), plan summary, knowledge grounding assessment |
| **Diagnostics** | Automated pass/fail checks: knowledge failures, action errors, CLT render failures, gateway anomalies |
| **Dynamic Plan** | Step-by-step execution from `AiAgentInteractionStep`: type, name, topic, timing, input/output |
| **Transcript** | Conversation messages from `AiAgentInteractionMessage` |
| **Knowledge Grounding** | citedReferences analysis from RecActorActionFeed |
| **Source Attribution** | Cross-referenced: dev names active, context vars populated, KA sources vs LLM-only responses |
| **Context & Grounding** | Per-turn planner context (see below) |
| **RecActorActionFeed** | Raw feed entries |
| **Summary Plan** | GenOpPlan data |
| **Gateway Calls** | All LLM calls: feature, model, template, token counts |
| **Actions** | ToolCall metadata from gateway |
| **Raw JSON** | Full trace data as JSON |

### Context & Grounding Tab (Key Debugging Tool)

Shows exactly what was passed to the planner service on every LLM turn. Each turn is collapsible:

1. **User Utterance / Instruction** — what triggered the turn
2. **Context Entity** — MessagingSession, Case, etc.
3. **Available Tools** — full list of actions with descriptions available that turn
4. **Knowledge Grounding** — actual content injected into `KNOWLEDGE_DATA_TAG` section (or "None" = retrieval returned nothing)
5. **Conversation History** — accumulated context: prior action inputs/outputs, agent responses, topics
6. **Seed Steps** — pre-configured planning steps
7. **Tool Calls & Results** — action invocations and responses in message history
8. **Prompt Variables** — template variables

Plus a **Knowledge Retrieval Calls** table:
- Query text sent to Data Library
- Retriever used
- Number of results returned
- Top relevance score
- Expandable: individual results with score, record ID, content preview

Use this tab to answer: "Why did the agent say X?", "Why didn't it use knowledge?", "What did the planner have to work with?"

## Output (text mode)

The script writes a structured text file at:
```
~/.claude/data/sra-agent-debugger/<org>/<record_identifier>/trace_<timestamp>.txt
```

Sections:
1. **Record metadata** (Case or MessagingSession details)
2. **GenOpPlan** (Summary Plan) — intent, topic, plan header, plan summary steps
3. **RecActorActionFeed** — action feed content with knowledge grounding annotations
4. **Knowledge Grounding Analysis** — summary of citedReferences across all feed entries
5. **Per-session trace:**
   - **Quick Glance** — routing info at a glance (utterance, topic, switches, actions)
   - Session header (agent, channel, timestamps, end type)
   - Dynamic Plan steps (type, name, topic, duration, status, input/output)
   - Transcript (message type, timestamp, content)
   - Knowledge Retrieval (query text, retriever, results with scores and record IDs)
   - Execution Waterfall (span tree with durations and status)
   - Gateway calls (feature, model, tokens)
   - Action metadata (tool calls)
   - Grounded records
6. **Source Attribution** — dev names, context vars, KA sources, LLM-only responses
7. **Diagnostic Summary** — automated checklist of common failure patterns

## After running

Read the output file and provide analysis. Apply these diagnostic patterns:

### Source Attribution — What to Look For

1. **KA-grounded vs. LLM-only ratio** — If the agent gave an answer but Source Attribution shows LLM_ONLY, the agent improvised from training data. Every policy/procedure answer should trace back to a specific KA record ID.

2. **Dev names present** — Confirm the expected topic, actions, and prompt templates appear. Missing dev names = the planner didn't select that topic/action.

3. **Context variables populated** — If an action received `currentRecordId` or `messagingSessionId` but NOT `ContactId`, that's correct for messaging. If both are blank, the context variable isn't mapped in Agent Builder.

4. **Grounded records** — Cross-reference with published articles: is the RIGHT article here? If wrong, title/summary keywords are misleading retrieval.

5. **Prompt template dev names** — If you see `streamKnowledgeSearch` but no grounded records, the search ran but returned nothing.

### Knowledge Retrieval Diagnostics (NEW)

Use `AIRetrieverRequest` + `AIRetrieverResponse` data:

| Symptom | What to check | Fix |
|---|---|---|
| Retriever returns irrelevant articles (high score, wrong content) | Query text vs. article Summary field keywords | Rewrite article Summary with customer-voice keywords matching how the planner phrases queries |
| Retriever returns 0 results | `requestInfoText` shows `noOfResults: 0` | Check: article published? Data Library connected? Retriever API name correct? |
| Right article exists but low score | Article Summary too generic or doesn't contain trigger phrases | Add FAQ_Question__c field, rewrite Summary to match query patterns |
| Multiple retriever calls with identical queries | Planner is re-searching each turn (normal for ReactInitialPrompt) | Not a bug — each interaction re-retrieves. Focus on whether results improve with conversation context |

### Execution Timing Diagnostics (NEW)

Use `ObservabilitySpans` data:

| Pattern | Indicates |
|---|---|
| `run.action.*` > 2000ms | Slow Apex/Flow execution — check callouts, SOQL, loops |
| `run.llmstep` > 3000ms | LLM latency spike — check token count, model selection |
| `run.interaction` much larger than sum of child spans | Orchestration overhead or queuing |
| `statusCode` = ERROR on any span | Execution failure — correlate with step error messages |
| Many `run.topic.*` spans (>3) | Excessive topic switching — review topic descriptions for overlap |

### Knowledge Grounding Failures

| Symptom | Likely Cause | Fix |
|---|---|---|
| `citedReferences: []` in feed | Data Library can't find the article | Check: Summary field blank? Title too generic? Article not published? |
| Agent says "no information in your company documents" but gives an answer | LLM improvised from training data; knowledge retrieval returned nothing | Confirm via citedReferences; fix article Summary field |
| `citedReferences` present but wrong article pulled | Title/Summary keywords don't match the query | Rewrite Summary with customer-voice keywords; add FAQ_Question__c trigger phrases |
| No RecActorActionFeed entries at all | Session didn't trigger plan generation | Check topic description matches the utterance; confirm agent is active |
| `KNOWLEDGE_DATA_TAG` section empty in Context tab | Data Library returned results but below confidence threshold, OR no retriever configured for topic | Check retriever responses — if scores < 0.7, improve article discoverability |
| `citedReferences: []` BUT answer is correct/grounded | **System knowledge** (not runtime) — see below | Not a bug — known citation gap (GUS a07EE00002cbR64YAE) |

### System Knowledge vs. Runtime Knowledge (Critical Distinction)

Dynamic Plans fetch knowledge in **two paths**:

| Path | When fetched | Query used | Persistence | Citations? |
|------|-------------|-----------|-------------|------------|
| **System knowledge** (`EDL[HLS]`) | Once at `startPlan` | HLS (High-Level Summary) from case Subject+Description | Stays in planner prompt for ALL turns via context variable | ❌ NO — not tracked in DB |
| **Runtime knowledge** (`EDL[USER_MSG]`) | Every turn | Current user message + last response topic | Changes each turn, filtered by score >0.6 and <5000 chars | ✅ YES — `citedReferences` populated |

**Why this matters for debugging:**

When a response shows `SOURCE_TYPE: MODEL_BASED` + `citedReferences: []`, it may STILL be grounded in knowledge — just system knowledge that has no citation path. Before concluding the agent improvised:

1. Check if the answer aligns with a published KA (manual comparison)
2. If it does → system knowledge grounding (no citation is expected, known gap)
3. If it doesn't → actual LLM improvisation from training data

**The citation gap bug:** Citations currently only consider runtime knowledge. When the answer comes solely from system knowledge (fetched at plan start), there's no citation and no "from knowledge" indicator. This makes grounded responses LOOK like hallucinations. Fix requires persisting system knowledge references in DB (tracked in GUS `a07EE00002cbR64YAE`).

**Splunk verification (if you have access):**
```
# System knowledge retrieval
index=coretest pod=<pod> <caseId>* "EDL[HLS]"

# Runtime knowledge retrieval  
index=coretest pod=<pod> <caseId>* "EDL[USER_MSG]"

# All EDL (knowledge) events for a case
index=coretest pod=<pod> <caseId>* "EDL"

# Error logs for a case/session
index=coretest pod=<pod> <recordId>* logLevel=SEVERE
```

**Engineering channel for trace/debugging escalation:** `#sc-service-planner-eng` (C06TPK97CCE)
- Eng team discussions on plan generation, knowledge grounding, citation bugs, patch releases
- Splunk log patterns, gate configurations, release branch testing
- Use for escalation when trace data shows platform-level issues (not config problems)

**When runtime knowledge returns nothing but system knowledge has the answer:**
- User message is too vague to retrieve (e.g., "how can I get this information?")
- But system knowledge (fetched from case Subject+Description) already has the relevant policy
- Agent answers correctly from system knowledge → `citedReferences: []` → looks like improvisation
- This is CORRECT behavior, just lacking citation visibility

### LLM Fallback Suppression (Knowledge-Only Answers)

**Problem:** When `streamKnowledgeSearch` returns 0 results, the LLM improvises an answer
from training data, prefixed with "There's no information in your company documents...
Here's some information I suggest, but it may not apply." The planner classifies this as
`SOURCE_TYPE: MODEL_BASED` — it's not grounded, not from the web, purely from model weights.

**How to identify in trace:**
- `SOURCE_TYPE: MODEL_BASED` in the planner reasoning
- `KNOWLEDGE_DATA_TAG` section is empty
- `citedReferences: []` on the response
- Response type is `Inform` with `result: []` (no action output)

**Fix — 2-layer control (topic instruction + action description):**

Layer 1 — Topic Instruction (add as Instruction 0 on the FAQ/Knowledge topic):
```
CRITICAL: You may ONLY answer questions using information retrieved from knowledge articles.
If no knowledge article is found that answers the customer's question:
- Do NOT attempt to answer from your own knowledge or training data.
- Do NOT prefix with "There's no information in your company documents" and then provide general guidance.

Never improvise, speculate, or provide information not directly sourced from a retrieved knowledge article.
```

Layer 2 — Action Description (on AnswerQuestionsWithKnowledge or equivalent):
> "Searches knowledge articles to answer the customer's question. If this action returns
> no results, do NOT attempt to answer from your own knowledge — instead tell the customer
> you'll connect them with a specialist and escalate. Never generate answers that aren't
> directly sourced from a returned knowledge article."

**Where each guardrail goes:**
- **Scope** = when to route (classifier) — NOT for behavioral rules
- **Description** = what the topic/action is (planner selection context) — reinforce here
- **Instructions** = how to behave during execution (guardrails) — PRIMARY location

**SRA context (employee-facing):** The rep IS the human in the loop. No escalation action
needed — just stop the agent from improvising. The rep handles it from there. For fully
autonomous customer-facing agents, also add an explicit Escalate action as a deterministic exit.

**What this does NOT do:** It doesn't disable `streamKnowledgeSearch` — the action still
fires, still retrieves when articles match. It only prevents the LLM from filling the gap
when retrieval comes back empty.

**Platform-level alternative:** As of June 2026, there is no platform toggle to hard-block
LLM fallback per-topic or per-action. It is purely instruction-driven. Per Lihang Pan (PM):
the planner exhausts Instructions → Actions → Conversation History, then attempts model-based.
The instruction is the only lever to block that last step. (No platform control planned yet.)

### Action Execution Failures

| Symptom | Likely Cause | Fix |
|---|---|---|
| Action returns empty/null data | `with sharing` on Apex class (EinsteinServiceAgent has no sharing access) | Switch to `without sharing` |
| Agent says "I cannot do this automatically" | `isUserInput: true` on action input schema fields | Set all inputs to `isUserInput: false` |
| Action fires on Case but not Messaging | `ContactId` context var used (Case-only) | Use `currentRecordId` + resolve Contact via MessagingSession.EndUserContactId |
| Field values are null/blank | Missing FLS for EinsteinServiceAgent User | Grant field Read via permission set |
| CLT card doesn't render (text narration instead) | Missing `show_command` — LLM chose text path | Add render directive to instruction; check W-21683108 |
| Output Rendering shows テキスト/Texto instead of CLT type | Wrong dropdown selection in Agent Builder | Change Output Rendering to the correct LightningType name (e.g. PetSeatMapOutput) |
| New Apex input/output not showing in Agent Builder | Agent Builder caches Apex schema on first add | Delete action from Asset Library → re-add to topic (forces schema re-read) |
| Action not in plan at all | Topic description doesn't match conversation | Rewrite from customer-intent perspective |

### Session Trace Patterns

| Pattern | Indicates |
|---|---|
| `LLM_COMPLETION_RESPONSE` after `ACTION_SUCCESS_RESPONSE` | CLT render failure — card data sent but LLM narrated it as text |
| `show_command` in step output | CLT rendered successfully |
| Gateway call with 0 completion tokens | Model refused or hit safety filter |
| Multiple TOPIC_STEP entries | Topic switching occurred — check if appropriate |
| Steps with ERROR status | Action threw exception — check Apex logs |

### Agent Says "Can I Proceed?" / Asks for Confirmation

**Root cause:** The "Require user confirmation" checkbox is CHECKED on the action in Agent Builder.

**Fix (3 layers — belt and suspenders):**
1. **Uncheck** "Require user confirmation" on the action in Agent Builder
2. **Action Description** — add: "Execute immediately without asking or confirming — never say 'Can I proceed' or 'Would you like me to'"
3. **Topic Instruction 0** — add step-chaining language: "Execute all read-only steps immediately and sequentially without pausing, narrating, or asking for confirmation between them"

The confirmation checkbox is the primary control. The instruction/description reinforcement prevents the LLM from asking anyway out of "politeness" even when the checkbox is off.

### Permissions Checklist (when action fails silently)

Check in order:
1. `copilotAction:isUserInput` — is it `true`? (set `false`)
2. **Sharing mode** — is Apex class `with sharing`? (switch to `without sharing`)
3. **FLS** — can EinsteinServiceAgent User read ALL queried fields? (silent null)
4. **Apex class access** — permission set assigned to EinsteinServiceAgent User?
5. **Record resolution** — on messaging, using `currentRecordId` (not `ContactId`)?
6. **invocationTarget** — does that class/flow exist and is it Active?

> **Mental model:** data-access failures fail SILENTLY (sharing → 0 rows, FLS → null). When the action ran but data is empty/blank, suspect PERMS before logic.

## In-Org LWC Component

The same tracing logic runs in-org via:
- **Apex controller**: `SRAAgentDebuggerController.cls`
- **LWC**: `sraAgentDebugger` (accessible from Service Console utility bar as "SRA Tracer")

The Apex controller makes the same Data Cloud SSOT API calls. If the LWC shows "Data Cloud Session Trace Unavailable", check:
1. The Connected App / Named Credential for Data Cloud API access
2. The user has the correct permission set for SSOT query API
3. Table names are `*__dll` (not `__dlm`) — this was a breaking change

## Inform Engineering (Slack Message Draft)

When the user says **"inform engineering"** (or "draft a message for eng", "write up for the team", etc.) after a trace has been run, generate a Slack-ready message the user can copy/paste.

### When to trigger
- User says "inform engineering" or similar after a trace/debug session
- User asks to "write this up" or "send this to the team"
- Must have a completed trace in context (either just ran, or a specific trace file referenced)

### Message format

```
:mag: *Agent Session Issue — [short description of the problem]*

*Org:* `[org alias]` ([instance if known, e.g. NA45])
*Record:* `[MessagingSession or Case ID]` ([link if constructable])
*Session UUID:* `[DC session UUID from trace]`
*Topic/Subagent:* `[topic dev name]`
*Agent:* `[agent API name + version]`
*Timestamp:* [when the issue occurred]

---

*What happened:*
[2-3 sentence summary of the observed behavior — what the agent did wrong or unexpectedly]

*Expected behavior:*
[1-2 sentences — what should have happened]

*Root cause (from trace):*
[Technical finding — e.g. "Knowledge retrieval returned 0 results for query X", "SOURCE_TYPE: MODEL_BASED — planner bypassed knowledge", "CLT show_command not emitted", etc. Include specific evidence from the trace.]

*Relevant trace data:*
• Planner classification: `[SOURCE_TYPE value]`
• Knowledge retrieval: [# calls, # results, top score if any]
• Action execution: [which actions ran, durations]
• `citedReferences`: [populated/empty]
[Include any other trace-specific data points relevant to the issue]

---

*Trace file:* `[path to trace .txt file]`
```

### Guidelines
- Keep it factual and concise — engineering-ready, not narrative
- Always include the trace evidence that proves the finding
- Use Slack formatting (`:emoji:`, `*bold*`, `` `code` ``, `---` dividers)
- Do NOT include speculation — only what the trace shows
- If multiple issues found in one session, list them as numbered items under "What happened"
- The user will copy/paste this — make it complete and self-contained
- Non-caturday tone: professional, direct, no fun/emoji beyond standard Slack formatting markers
- Always end the message with: `_Traced with Chad's Claude SRA Trace Tool_`

### Org instance lookup (if needed)
```bash
sf org display --target-org <alias> 2>/dev/null | grep "Instance Url"
```

## Reference Channels & Docs

| Resource | Link | What it covers |
|---|---|---|
| SRA Troubleshooting Canvas | `F09S9CGPM9D` — [Slack canvas](https://salesforce.enterprise.slack.com/docs/T01G0063H29/F09S9CGPM9D) | Aggregated troubleshooting: perms, errors, demo resources, knowledge grounding setup |
| SRA PM/SE/FDE Collab Channel | `C08E300HPUK` — `#service-assistant-pm-se-ta-ea-fde-collab` | Dynamic plan troubleshooting, real-time issues, eng escalations |
| Debugging Knowledge Grounding | [Google Doc](https://docs.google.com/document/d/1fdd656LmQJrUgtYnNHBfXbDGZkKvT7ppjHd6IXOV4IY/edit?tab=t.0) | Deep-dive on knowledge grounding issues |
| Testing Knowledge in SA | [Help article](https://help.salesforce.com/s/articleView?id=service.sp_knowledge_practices.htm&language=en_US&type=5) | Official testing guide |
| Testing Knowledge (retriever) | [Help article](https://help.salesforce.com/s/articleView?id=service.sp_test_knowledge.htm&language=en_US&type=5) | Retriever troubleshooting steps |

Use these when drafting "inform engineering" messages or researching known issues. The
collab channel (`C08E300HPUK`) is the primary escalation path for SRA behavior questions.

