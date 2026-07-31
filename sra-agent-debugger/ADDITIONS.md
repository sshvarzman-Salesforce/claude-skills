# SRA Tracer — Additions & Enhancements

Hey! Here's a summary of what I've added to the SRA session tracing tool. The core architecture is the same — SOQL for RecActorActionFeed/GenOpPlan, Data Cloud SSOT API for the session trace — but I've extended it significantly.

---

## Bug Fix: Data Cloud Queries (Critical)

The Data Cloud queries were failing with `400 BAD_REQUEST — table does not exist` because the table/field naming convention changed:

| Before (broken) | After (working) |
|-----------------|-----------------|
| `ssot__AiAgentInteractionMessage__dlm` | `AiAgentInteractionMessage__dll` |
| `ssot__AIAgentSession__dlm` | `AiAgentSession__dll` |
| `ssot__FieldName__c` | `fieldName__c` (camelCase, no prefix) |

**Pattern**: Drop the `ssot__` prefix on both tables and fields. Suffix is `__dll` not `__dlm`. Fields go camelCase.

This affected the Apex controller (`SRAAgentDebuggerController.cls`) and the Python scripts.

---

## New Data Sources (3 additional DC tables)

Beyond the original 9 tables, I'm now querying:

### 1. `AIRetrieverRequest__dll` — Knowledge Retrieval Queries
Shows exactly what query text was sent to the Data Library on each turn.

Key fields:
- `queryText__c` — the search query (e.g., "check loyalty. Pet_Travel_Booking")
- `retrieverApiName__c` — which retriever was used
- `requestInfoText__c` — contains `noOfResults` count
- `traceId__c` — links to observability spans

### 2. `AIRetrieverResponse__dll` — What the Data Library Returned
The actual retrieved chunks with relevance scoring.

Key fields:
- `resultText__c` — the content chunk returned
- `scoreNumber__c` — relevance score (0-1)
- `sourceRecordId__c` — the KA record ID (e.g., `ka0...`)
- `aIRetrieverRequestId__c` — FK to the request

### 3. `ObservabilitySpans__dll` — Execution Waterfall
Full distributed tracing from the Atlas Reasoning Engine.

Key fields:
- `operationName__c` — e.g., `run.interaction`, `run.topic.MyTopic_16jHo...`, `run.action.MyAction_179Ho...`, `run.llmstep`
- `traceId__c` / `spanId__c` / `parentSpanId__c` — parent-child tree
- `durationNanos__c` — execution time
- `statusCode__c` — OK or error

These are linked to sessions by timestamp range (session start → end).

---

## Session UUID Resolution from Feed Content

The old approach tried to find the DC session by matching the MessagingSession ID in message text — unreliable. I added a fallback that extracts the session UUID directly from the `_links` URLs in RecActorActionFeed content:

```
.../sessions/019ef228-90d0-7cbd-9a3d-186ac2cf52bb/messages
```

This regex-based extraction is the most reliable resolution method since every agent response includes the session URL.

---

## Local HTML Viewer (`viewer.py`)

A standalone Python web viewer that runs the full trace pipeline and serves a tabbed dark-mode UI locally.

```bash
python3 viewer.py --id 0MwHo000000vnLUKAY --org mySDO
# Opens at http://127.0.0.1:8080
```

Features:
- Input field at top to trace new record IDs without restarting
- POST to `/trace` endpoint for programmatic use
- All data exported as JSON (`/json` endpoint)

### Tabs:

| Tab | What it shows |
|-----|--------------|
| **AI Summary** | Auto-generated narrative: conversation timeline, actions invoked (dev names), plan summary, knowledge grounding assessment |
| **Diagnostics** | Automated pass/fail checks: knowledge failures, action errors, CLT render failures, gateway anomalies |
| **Dynamic Plan** | Step-by-step execution: type, name, topic, timing, input/output (from `AiAgentInteractionStep`) |
| **Transcript** | Conversation messages (from `AiAgentInteractionMessage`) |
| **Knowledge Grounding** | citedReferences analysis from RecActorActionFeed |
| **Source Attribution** | Cross-referenced: dev names active, context vars populated, KA sources vs LLM-only responses |
| **Context & Grounding** | **(NEW)** Per-turn planner context — see below |
| **RecActorActionFeed** | Raw feed entries |
| **Summary Plan** | GenOpPlan data |
| **Gateway Calls** | All LLM calls: feature, model, template, token counts |
| **Actions** | ToolCall metadata from gateway |
| **Raw JSON** | Full trace data as JSON |

---

## Context & Grounding Tab (the big one)

This tab shows **exactly what was passed to the planner service on every turn**. Each turn is collapsible and shows:

1. **User Utterance / Instruction** — what triggered the turn
2. **Context Entity** — `MessagingSession`, `Case`, etc.
3. **Available Tools** — full list of actions with descriptions available that turn
4. **Knowledge Grounding** — the actual knowledge content injected into the `KNOWLEDGE_DATA_TAG` section (or "None" if empty — immediately tells you grounding didn't fire)
5. **Conversation History** — accumulated context growing each turn (prior action inputs/outputs, agent responses, topic selections)
6. **Seed Steps** — pre-configured planning steps
7. **Tool Calls & Results** — action invocations and responses in the message history
8. **Prompt Variables** — template variables

Plus a **Knowledge Retrieval Calls** table showing:
- Query text sent to Data Library
- Which retriever was used
- Number of results returned
- Top relevance score
- Expandable rows with individual results (score, record ID, content preview)

This is where you go to answer: "Why did the agent say X?" or "Why didn't it use knowledge?" — you can see exactly what the planner had to work with.

---

## Renamed to "SRA Tracer"

Updated everywhere:
- LWC toolbar utility label
- FlexiPage masterLabel
- HTML viewer title
- Python script references

---

## File Locations

```
# Python scripts (local tooling)
~/.claude/skills/sra-agent-debugger/scripts/trace_session.py   # Core tracing logic
~/.claude/skills/sra-agent-debugger/scripts/viewer.py          # HTML viewer

# Org components (deployed)
force-app/main/default/classes/SRAAgentDebuggerController.cls  # Apex controller
force-app/main/default/lwc/sraAgentDebugger/                   # LWC component
force-app/main/default/flexipages/SRA_Agent_Debugger.flexipage-meta.xml
force-app/main/default/flexipages/Service_Console_2_UtilityBar.flexipage-meta.xml
```

---

## Quick Diagnostic Insight from This Session

The retriever data immediately revealed that for a pet travel booking session, the Data Library was returning completely irrelevant articles (hotel cancellation procedures, score disclosure reports) with scores of 0.5-0.7. The agent correctly fell back to action-based responses rather than KB, but this explains why `citedReferences` is always empty for this topic — there's no pet travel Knowledge Article published, or its Summary field doesn't match the retrieval queries.
