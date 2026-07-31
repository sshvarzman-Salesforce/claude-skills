---
name: sra-analytics
description: Deploy and manage the SRA Analytics Dashboard — fleet-level Agentforce analytics across sessions, channels, knowledge quality, and dynamic plans. Supports both local Python web dashboard and in-org LWC deployment. Use when user asks about analytics, dashboard, metrics, KPIs, or fleet performance for Agentforce agents.
tools: [Bash, Read, Write, Edit]
---

# sra-analytics — SRA Fleet Analytics Dashboard

Deploys, updates, and runs the Agentforce fleet-level analytics dashboard. Two deployment modes: Python web (local dev) and in-org (LWC + Apex via ConnectApi).

## Prerequisites

| Requirement | Details |
|-------------|---------|
| `sf` CLI | Authenticated to target org (`sf org login web --alias <ALIAS>`) |
| Python | 3.9+ (for local dashboard mode only) |
| Data Cloud | Enabled on target org with STDM data flowing |
| Git access | `git.soma.salesforce.com/chad-goldsmith/agentforce-debug-tools` |
| Org features | ConnectApi CDP Query enabled, Agentforce with session telemetry |

## Getting Started

### Installation

```bash
# 1. Clone the repo
git clone git.soma.salesforce.com/chad-goldsmith/agentforce-debug-tools.git
cd agentforce-debug-tools

# 2. Copy skill into your Claude skills directory
mkdir -p ~/.claude/skills/sra-analytics
cp skills/sra-analytics/SKILL.md ~/.claude/skills/sra-analytics/SKILL.md

# 3. Verify sf CLI auth
sf org list
```

### Quick Start

```bash
# Deploy the in-org dashboard to your target org
cd agentforce-debug-tools
sf project deploy start \
  --source-dir sra-analytics/force-app/main/default/classes/SRAAnalyticsController.cls \
  sra-analytics/force-app/main/default/classes/SRAAnalyticsController.cls-meta.xml \
  sra-analytics/force-app/main/default/lwc/sraAnalyticsDashboard \
  --target-org <ORG_ALIAS>

# Or run the local Python dashboard
python3 sra-analytics/scripts/analytics.py --org <ORG_ALIAS>
```

## If the user hasn't given enough to proceed

When invoked without clear intent, print this verbatim:

> What would you like to do with SRA Analytics?
>
> I can:
> - **Deploy** the in-org dashboard to a target org (LWC + Apex)
> - **Run** the local Python web dashboard against an org
> - **Add a tile** — new metric, chart, or table to the dashboard
> - **Update filters** — add/modify top-level filter options
> - **Check data** — query Data Cloud to verify what's available
>
> I need:
> - **Org alias** — the `sf` CLI alias (e.g. `mySDO`, `MetaRLUAT`)
> - **Action** — deploy, run, add tile, or explore data

## When to use

Trigger this skill when the user:
- Asks to "deploy / run / update the analytics dashboard"
- Wants to see fleet-level metrics for Agentforce (session volume, token usage, etc.)
- Asks about knowledge quality scores, feedback data, channel breakdown
- Wants to add a new tile or filter to the dashboard
- Asks "how are my agents performing" or "show me agent analytics"
- References PRD-264, dynamic plan reporting, or fleet KPIs
- Wants to filter data by channel (messaging, voice, case) or plan type (guidance vs dynamic)

## Architecture

### Source Locations

| Component | Path (relative to cloned repo) | Purpose |
|-----------|------|---------|
| Apex Controller | `sra-analytics/apex/SRAAnalyticsController.cls` | Canonical source |
| Python Dashboard | `sra-analytics/scripts/analytics.py` | Local web dashboard |
| In-Org LWC | `sra-analytics/force-app/main/default/lwc/sraAnalyticsDashboard/` | Deployable LWC |
| In-Org Apex | `sra-analytics/force-app/main/default/classes/SRAAnalyticsController.cls` | Deployable Apex |

### Data Sources

| Source | Table/Object | What it provides |
|--------|-------------|-----------------|
| Data Cloud STDM | `AiAgentSession__dll` | Sessions, channels, end types, timestamps |
| Data Cloud STDM | `AiAgentInteraction__dll` | Interactions, topic routing |
| Data Cloud STDM | `AiAgentInteractionStep__dll` | Steps, types, duration |
| Data Cloud STDM | `AiAgentSessionParticipant__dll` | Agent identity, API names |
| Data Cloud | `GenAIGatewayRequest__dll` | Token usage, prompt templates, models |
| Data Cloud | `GenAIFeedback__dll` | Dynamic plan feedback (thumbs up/down, shown/accepted) |
| Data Cloud | `AIRetrieverRequest__dll` / `AIRetrieverResponse__dll` | Knowledge retrieval quality scores |
| Data Cloud | `ObservabilitySpan__dll` | Per-operation latency |
| Core SOQL | `GenOpPlan` | Plan outcomes, intents, topic routing |
| Core SOQL | `RecActorActionFeed` | Action feed volume |

### Key Technical Notes

- Data Cloud tables end in `__dll` (NOT `__dlm`), no `ssot__` prefix
- Fields are camelCase with `__c` suffix (e.g. `startTimestamp__c`, `aiAgentChannelTypeId__c`)
- Use `ConnectApi.CdpQuery.queryAnsiSqlV2()` for in-org queries (supports JOINs, caching)
- Chart.js static resource in org is `chartjs_v280` (not `chartjs` or `ChartJS`)
- `sf org display` returns 54-char session IDs that don't work for REST API — use in-org ConnectApi instead

### ⚠️ RecActorActionFeed & GenOpPlan — Verified Field Reference (in-org, mySDO, 2026-07-27)

> Empirically confirmed while building the Employee Interaction Tracking feature. **Older query examples further down in this doc use pre-verification field names** (`Body`, `Type`, `ParentId`, `InsertedById`, `Parent.AiAgentSession__c`) — prefer the verified names below.

**RecActorActionFeed real fields:**

| Use | Correct field | NOT |
|-----|---------------|-----|
| Parent record (Case/MessagingSession) | `RelatedRecordId` | ~~`ParentId`~~ |
| The human user | `CreatedById` / `CreatedBy.Name` | ~~`InsertedById`~~ |
| The skill/agent feature (not a user!) | `SenderId` → `RecActorFeatureDef` | — |
| Action content | `Content` | ~~`Body`~~ |
| Status | `Status` | — |
| (there is **no** `Type` field) | — | ~~`Type`~~ |

**Query-context limitations (why GenOpPlan is the primary analytics source):**

- `RecActorActionFeed` throws `Invalid type: RecActorActionFeed` in static SOQL → must use dynamic `Database.query()` + `@SuppressWarnings('PMD')`.
- Not supported in `@AuraEnabled(cacheable=true)` or Execute Anonymous ("sObject type ... is not supported in this context") → use `cacheable=false`, and even then treat it as a **try/catch fallback only**.
- No `GROUP BY` aggregates → fetch rows and count into a `Map` in Apex.
- No `LIKE` on Id fields (`ParentId LIKE` → "invalid operator on id field") → filter with `String.startsWith()` after the query.
- **`GenOpPlan` is reliable in all contexts** (incl. Execute Anonymous): `GenOpPlan.CreatedById` = user who ran the plan; `GenOpPlan.ParentId` = Case/MessagingSession. Make it the primary source; use RecActorActionFeed only for extra action detail.
- **`GenOpPlan.FeedbackKey` does NOT join to `GenAIFeedback`** (tested: no matching rows). `GenAIFeedback` only populates on explicit user feedback → unreliable for confidence scoring. Use `AIRetrieverResponse__dll` quality/relevance scores instead.

**Record-type detection via ID prefix:** `500`=Case, `0MW`/`0Mw`=MessagingSession, `0LQ`=VoiceCall, `ka0`=Knowledge, `005`=User, `003`=Contact, `001`=Account.

**LWC deploy gotcha:** the bundle folder must contain **only** `.css/.html/.js/.js-meta.xml`. Stray temp files (`*-employee.js`, `*.bak`, `temp.js`) cause `Leading decorators must be attached to a class declaration` / `Missing semicolon` deploy errors.

> ⚠️ **Stale path in Quick Start above:** the actual layout is `sra-analytics/apex/SRAAnalyticsController.cls` (canonical) and a separate `sra-analytics-deploy/main/default/{classes,lwc}/` deploy folder — **not** `sra-analytics/force-app/main/default/...`. Reconcile LWC edits from the deploy folder back to canonical `sra-analytics/lwc/` before committing.

## Dashboard Tiles

Current tiles (20 total):

### Summary KPIs (always visible)
- Total Sessions, Total Steps, Avg Steps/Session, Error Rate, Prompt/Completion/Total Tokens

### Guidance Plan Tiles (filtered by Plan Type = Guidance or All)
- Session Volume Over Time (line chart)
- Step Type Breakdown (doughnut chart)
- Session End Types (pie chart)
- Channel Breakdown (pie chart)
- Intent Distribution (table)
- Plan Outcomes by Topic (table)
- Prompt Template Usage (table)
- Action Usage (table + bar chart)
- Topic Breakdown (table)
- Step Performance / Duration (table)
- Inter-Step Latency (table — avg gap between consecutive steps)
- Observability Spans (table)
- Case Session Summary (table)
- Feed Volume (line chart)
- Token Usage Over Time (line chart)

### Dynamic Plan Tiles (filtered by Plan Type = Dynamic or All)
- Dynamic Plan Feedback banner (thumbs up/down, positive rate, shown/accepted)
- Plan Feedback by User (table with resolved user names)

### Shared Tiles (always visible)
- Knowledge Retrieval Quality KPIs (green banner)
- Knowledge Quality Scores per Article (table with color-coded quality)

## Filters

| Filter | Field | Values |
|--------|-------|--------|
| Date Range | `startTimestamp__c` | Start/End date pickers |
| Agent | `p.aiAgentApiName__c` | Dynamic from org data |
| Channel | `s.aiAgentChannelTypeId__c` | All, Messaging, Voice, Case (Web/Core), Builder (Test) |
| Plan Type | Client-side visibility toggle | All, Guidance (Topic-Routed), Dynamic (ServicePlans) |

## Commands

### Deploy In-Org Dashboard

```bash
# From the cloned agentforce-debug-tools repo root:
sf project deploy start \
  --source-dir sra-analytics/force-app/main/default/classes/SRAAnalyticsController.cls \
  sra-analytics/force-app/main/default/classes/SRAAnalyticsController.cls-meta.xml \
  sra-analytics/force-app/main/default/lwc/sraAnalyticsDashboard \
  --target-org <ORG_ALIAS>
```

### Run Local Python Dashboard

```bash
# From the cloned agentforce-debug-tools repo root:
python3 sra-analytics/scripts/analytics.py --org <ORG_ALIAS>
# Opens http://127.0.0.1:8090
```

Note: Python dashboard has auth issues on some orgs (54-char session token). In-org deployment is preferred.

### Query Data Cloud Directly (Explore)

```apex
ConnectApi.CdpQueryInput input = new ConnectApi.CdpQueryInput();
input.sql = '<YOUR SQL>';
ConnectApi.CdpQueryOutputV2 output = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
```

## Adding a New Tile

1. **Add data class** in `SRAAnalyticsController.cls`:
   ```apex
   public class MyNewData {
       @AuraEnabled public String fieldA;
       @AuraEnabled public Integer fieldB;
   }
   ```

2. **Add @AuraEnabled method** with standard signature:
   ```apex
   @AuraEnabled(cacheable=true)
   public static List<MyNewData> getMyNewData(String startDate, String endDate, String agentName, String channelType) {
       String dateFilter = buildDateFilter(startDate, endDate, 's.startTimestamp__c');
       String agentFilter = buildAgentFilter(agentName);
       // Query uses: dateFilter + agentFilter + buildChannelFilter(channelType)
   }
   ```

3. **Import in LWC JS** and add to `Promise.allSettled`:
   ```javascript
   import getMyNewData from '@salesforce/apex/SRAAnalyticsController.getMyNewData';
   // Add @track property, add to Promise.allSettled array, add result handler
   ```

4. **Add HTML section** with table/chart markup

5. **Deploy** to target org

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Chart.js not found | Wrong resource name | Use `chartjs_v280` (no namespace) |
| 401 on Python dashboard | sf CLI 54-char session token | Use in-org deployment instead |
| "table does not exist" | Wrong naming (`ssot__` prefix or `__dlm` suffix) | Use bare name + `__dll` suffix |
| Empty tile data | Sharing model on Apex class | Ensure `without sharing` if needed |
| Channel filter no results | Channel values differ by org | Query `SELECT DISTINCT s.aiAgentChannelTypeId__c FROM AiAgentSession__dll s` to check |
| Knowledge quality empty | No AIRetrieverResponse data | Verify Data Library is configured with quality monitoring |

## Querying Session & Actor History for Customer Engineers

### Use Case
Customer engineers need to see what happened in a specific SRA session: what actions fired, what CLTs rendered, what the agent said, and what the final outcome was.

### Data Sources for Session History

| Source | What It Shows | Access Method |
|--------|---------------|---------------|
| `AiAgentSession__dll` | Session metadata: start/end time, channel, end type, agent name | Data Cloud query (ConnectApi or SOQL on `__dll`) |
| `AiAgentInteraction__dll` | Interactions within session: topic, intent, routing | Data Cloud query |
| `AiAgentInteractionStep__dll` | Individual steps: type, output, duration, order | Data Cloud query |
| `RecActorActionFeed` | SRA-specific: CLT rendering, action feed items, actor output | Core SOQL (NOT Data Cloud) |
| `GenOpPlan` | Plan metadata: outcome, intent, topic | Core SOQL |
| `GenAIGatewayRequest__dll` | Token usage, prompt templates, model calls | Data Cloud query |
| `ObservabilitySpan__dll` | Per-operation latency, parent/child spans | Data Cloud query |

### Query 1: Get Session Overview (Data Cloud)

**Option A: Find sessions by parent record (Case/Messaging/Voice)**
```sql
SELECT aiAgentSessionId__c, startTimestamp__c, endTimestamp__c,
       aiAgentChannelTypeId__c, aiAgentSessionEndTypeId__c
FROM AiAgentSession__dll
WHERE relatedRecordId__c = '<CASE_ID or MESSAGING_SESSION_ID or VOICECALL_ID>'
ORDER BY startTimestamp__c DESC
```

**Option B: Find session by session ID**
```apex
// Via ConnectApi in Apex
ConnectApi.CdpQueryInput input = new ConnectApi.CdpQueryInput();
input.sql = @
SELECT 
    s.aiAgentSessionId__c AS sessionId,
    s.startTimestamp__c,
    s.endTimestamp__c,
    s.aiAgentChannelTypeId__c AS channel,
    s.aiAgentSessionEndTypeId__c AS endType,
    s.relatedRecordId__c AS parentRecordId,
    p.aiAgentApiName__c AS agentName
FROM AiAgentSession__dll s
LEFT JOIN AiAgentSessionParticipant__dll p 
    ON s.aiAgentSessionId__c = p.aiAgentSessionId__c
WHERE s.aiAgentSessionId__c = '<SESSION_ID>'
@;
ConnectApi.CdpQueryOutputV2 output = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
System.debug(output.data);
```

**Via sf CLI:**
```bash
sf data query \
  --query "SELECT aiAgentSessionId__c, startTimestamp__c, endTimestamp__c, aiAgentChannelTypeId__c, relatedRecordId__c FROM AiAgentSession__dll WHERE relatedRecordId__c = '<CASE_ID>'" \
  --target-org <ALIAS> \
  --api-version 61.0
```

**Key Field:** `relatedRecordId__c` = the Case, MessagingSession, or VoiceCall ID (this is the parent record)

### Query 2: Get All Steps in Session (Data Cloud)

**The Relationship Hierarchy:**
```
AiAgentSession__dll (session)
    └─ AiAgentInteraction__dll (interaction) 
           └─ AiAgentInteractionStep__dll (steps)
```

**Join Keys:**
- `AiAgentInteraction__dll.aiAgentSessionId__c` → `AiAgentSession__dll.id__c`
- `AiAgentInteractionStep__dll.aiAgentInteractionId__c` → `AiAgentInteraction__dll.id__c`

**Query steps via interaction:**
```sql
-- Get all steps for a session (via interaction join)
SELECT 
    step.name__c AS stepName,
    step.aiAgentInteractionStepTypeId__c AS stepType,
    step.startTimestamp__c,
    step.endTimestamp__c,
    step.inputValueText__c AS input,
    step.outputValueText__c AS output,
    step.subType__c
FROM AiAgentInteractionStep__dll step
JOIN AiAgentInteraction__dll interaction 
    ON step.aiAgentInteractionId__c = interaction.id__c
WHERE interaction.aiAgentSessionId__c = '<SESSION_ID>'
ORDER BY step.startTimestamp__c
```

**If you have the interaction ID directly:**
```sql
SELECT name__c, aiAgentInteractionStepTypeId__c, 
       startTimestamp__c, endTimestamp__c,
       inputValueText__c, outputValueText__c
FROM AiAgentInteractionStep__dll
WHERE aiAgentInteractionId__c = '<INTERACTION_ID>'
ORDER BY startTimestamp__c
```

**Via ConnectApi in Apex:**
```apex
ConnectApi.CdpQueryInput input = new ConnectApi.CdpQueryInput();
input.sql = @
SELECT 
    step.stepType__c AS stepType,
    step.stepName__c AS stepName,
    step.topicName__c AS topic,
    step.startTimestamp__c,
    step.endTimestamp__c,
    step.statusCode__c AS status,
    step.input__c,
    step.output__c
FROM AiAgentInteractionStep__dll step
WHERE step.aiAgentSessionId__c = '<SESSION_ID>'
ORDER BY step.startTimestamp__c ASC
@;
ConnectApi.CdpQueryOutputV2 output = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
```

**Step Types:**
- `GenAiPromptRequest` — Agent thinking/planning
- `SearchRelatedRecord` — Knowledge grounding
- `GetStepSummary` — Plan step rendering
- `ExecuteAction` — Action execution
- `GetModelResponse` — LLM call

**Status Codes:**
- `200` — Success
- `400` — Bad request
- `500` — Internal error

### Query 2b: Get Conversation Messages (Data Cloud)

**Join Keys for Messages:**
- `AiAgentInteractionMessage__dll.aiAgentSessionId__c` → `AiAgentSession__dll.id__c` (direct)
- `AiAgentInteractionMessage__dll.aiAgentInteractionId__c` → `AiAgentInteraction__dll.id__c` (via interaction)

**Option A: Get messages directly by session ID:**
```sql
SELECT aiAgentInteractionMessageTypeId__c AS messageType,
       contentText__c AS content,
       startTimestamp__c AS timestamp
FROM AiAgentInteractionMessage__dll
WHERE aiAgentSessionId__c = '<SESSION_ID>'
ORDER BY startTimestamp__c
```

**Option B: Get messages via interaction ID:**
```sql
SELECT aiAgentInteractionMessageTypeId__c AS messageType,
       contentText__c AS content,
       startTimestamp__c AS timestamp
FROM AiAgentInteractionMessage__dll
WHERE aiAgentInteractionId__c = '<INTERACTION_ID>'
ORDER BY startTimestamp__c
```

**Message Types:**
- `User` — Customer message
- `Agent` — AI agent response
- `System` — System notifications

### Query 3: Get RecActorActionFeed (Core SOQL)

**This is SRA-specific** and shows CLT rendering, action confirmations, and actor output.

```apex
// In Apex
List<RecActorActionFeed> feed = [
    SELECT Id, ParentId, Type, Body, CreatedDate, 
           InsertedBy.Name, CommentCount, LikeCount
    FROM RecActorActionFeed
    WHERE Parent.AiAgentSession__c = '<SESSION_ID>'
    ORDER BY CreatedDate ASC
];
```

**Via sf CLI:**
```bash
sf data query \
  --query "SELECT Id, Type, Body, CreatedDate FROM RecActorActionFeed WHERE Parent.AiAgentSession__c = '<SESSION_ID>' ORDER BY CreatedDate" \
  --target-org <ALIAS>
```

**Feed Types:**
- `TrackedChange` — Status updates ("Plan started", "Action completed")
- `TextPost` — Agent messages to rep
- `ContentPost` — CLT rendering (Complex Data Type)
- `CallLogPost` — Voice-specific call logs

### Query 4: Get Plan Outcome (Core SOQL)

```apex
List<GenOpPlan> plans = [
    SELECT Id, AiAgentSession__c, Outcome, Intent, Topic, 
           ChannelType, CreatedDate
    FROM GenOpPlan
    WHERE AiAgentSession__c = '<SESSION_ID>'
];
```

**Via sf CLI:**
```bash
sf data query \
  --query "SELECT Id, Outcome, Intent, Topic FROM GenOpPlan WHERE AiAgentSession__c = '<SESSION_ID>'" \
  --target-org <ALIAS>
```

**Outcomes:**
- `Resolved` — Plan completed successfully
- `Unresolved` — Plan did not complete
- `Escalated` — Handed off to human

### Query 5: Get Token Usage for Session (Data Cloud)

```apex
ConnectApi.CdpQueryInput input = new ConnectApi.CdpQueryInput();
input.sql = @
SELECT 
    g.aiAgentSessionId__c AS sessionId,
    g.aiPromptTemplateApiName__c AS promptTemplate,
    g.aiModelName__c AS model,
    SUM(g.inputTokens__c) AS totalInputTokens,
    SUM(g.outputTokens__c) AS totalOutputTokens
FROM GenAIGatewayRequest__dll g
WHERE g.aiAgentSessionId__c = '<SESSION_ID>'
GROUP BY g.aiAgentSessionId__c, g.aiPromptTemplateApiName__c, g.aiModelName__c
@;
ConnectApi.CdpQueryOutputV2 output = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
```

### Query 6: Get Knowledge Retrieval Quality (Data Cloud)

```apex
ConnectApi.CdpQueryInput input = new ConnectApi.CdpQueryInput();
input.sql = @
SELECT 
    resp.aiRetrieverRequestId__c AS requestId,
    resp.retrievedRecordName__c AS articleTitle,
    resp.retrievedRecordId__c AS articleId,
    resp.qualityScore__c AS quality,
    resp.relevanceScore__c AS relevance,
    resp.orderNumber__c AS rank
FROM AIRetrieverResponse__dll resp
JOIN AIRetrieverRequest__dll req 
    ON resp.aiRetrieverRequestId__c = req.id__c
WHERE req.aiAgentSessionId__c = '<SESSION_ID>'
ORDER BY resp.orderNumber__c ASC
@;
ConnectApi.CdpQueryOutputV2 output = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
```

### Query 7: Get Observability Spans (Latency Breakdown)

```apex
ConnectApi.CdpQueryInput input = new ConnectApi.CdpQueryInput();
input.sql = @
SELECT 
    span.name__c AS operation,
    span.startTimestamp__c,
    span.endTimestamp__c,
    span.durationInMilliseconds__c AS duration,
    span.parentSpanId__c AS parentSpan
FROM ObservabilitySpan__dll span
WHERE span.aiAgentSessionId__c = '<SESSION_ID>'
ORDER BY span.startTimestamp__c ASC
@;
ConnectApi.CdpQueryOutputV2 output = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
```

**Common Operations:**
- `service_plan_generation` — Plan generation latency
- `knowledge_grounding` — Knowledge retrieval latency
- `action_execution` — Action execution latency
- `llm_call` — Model inference latency

### Example: Full Session Trace for Customer Engineer

```apex
// Step 1: Get session metadata
String sessionId = '<SESSION_ID>';
ConnectApi.CdpQueryInput input = new ConnectApi.CdpQueryInput();

// Session overview
input.sql = 'SELECT s.id__c, s.startTimestamp__c, s.endTimestamp__c, s.aiAgentChannelTypeId__c, p.aiAgentApiName__c FROM AiAgentSession__dll s LEFT JOIN AiAgentSessionParticipant__dll p ON s.id__c = p.aiAgentSessionId__c WHERE s.id__c = \'' + sessionId + '\'';
ConnectApi.CdpQueryOutputV2 sessionData = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
System.debug('Session: ' + sessionData.data);

// All steps
input.sql = 'SELECT step.id__c, step.aiAgentInteractionStepTypeId__c, step.orderNumber__c, step.durationInMilliseconds__c FROM AiAgentInteractionStep__dll step JOIN AiAgentInteraction__dll interaction ON step.aiAgentInteractionId__c = interaction.id__c WHERE interaction.aiAgentSessionId__c = \'' + sessionId + '\' ORDER BY step.orderNumber__c ASC';
ConnectApi.CdpQueryOutputV2 stepsData = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
System.debug('Steps: ' + stepsData.data);

// Step 2: Get RecActorActionFeed (core SOQL)
List<RecActorActionFeed> feed = [SELECT Id, Type, Body, CreatedDate FROM RecActorActionFeed WHERE Parent.AiAgentSession__c = :sessionId ORDER BY CreatedDate];
System.debug('Feed: ' + feed);

// Step 3: Get plan outcome
List<GenOpPlan> plans = [SELECT Id, Outcome, Intent, Topic FROM GenOpPlan WHERE AiAgentSession__c = :sessionId];
System.debug('Plan: ' + plans);

// Step 4: Token usage
input.sql = 'SELECT SUM(g.inputTokens__c) AS inputTokens, SUM(g.outputTokens__c) AS outputTokens FROM GenAIGatewayRequest__dll g WHERE g.aiAgentSessionId__c = \'' + sessionId + '\'';
ConnectApi.CdpQueryOutputV2 tokenData = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
System.debug('Tokens: ' + tokenData.data);
```

### How to Share with Customer Engineers

**Option 1: Anonymous Apex (Quick Check)**
1. Copy one of the queries above
2. Developer Console → Debug → Open Execute Anonymous Window
3. Paste query, replace `<SESSION_ID>` with actual session ID
4. Click Execute, check Debug Logs

**Option 2: Workbench (SQL Interface)**
1. Go to Workbench (workbench.developerforce.com)
2. Login with org credentials
3. Queries → SOQL Query (for core objects like RecActorActionFeed, GenOpPlan)
4. Utilities → REST Explorer → POST to `/services/data/v61.0/connect/cdp/query` (for Data Cloud tables)

**Option 3: REST API (Programmatic)**
```bash
# Get session ID from recent sessions
sf data query --query "SELECT Id, Name FROM Case WHERE Subject LIKE '%<CUSTOMER_NAME>%' ORDER BY CreatedDate DESC LIMIT 1" --target-org <ALIAS>

# Use session ID to query history
sf data query --query "SELECT Id, Type, Body FROM RecActorActionFeed WHERE Parent.AiAgentSession__c = '<SESSION_ID>'" --target-org <ALIAS>
```

**Option 4: In-Org LWC (Customer Self-Service)**
Deploy a custom LWC that queries these tables and renders a timeline view. Customer engineers can access via a custom Lightning page.

### Common Customer Engineer Questions

**Q: "Which employee ran this session?" (Human rep, not the AI agent)**

The human employee is found by resolving from the parent record (Case, MessagingSession, or VoiceCall):

```apex
// Step 1: Get the parent record ID from GenOpPlan
List<GenOpPlan> plans = [
    SELECT Id, ParentId, CreatedBy.Name, ChannelType 
    FROM GenOpPlan 
    WHERE AiAgentSession__c = :sessionId
];

String parentId = plans[0].ParentId; // Case, MessagingSession, or VoiceCall Id
String channelType = plans[0].ChannelType;

// Step 2: Query parent record based on channel
if (channelType == 'Case') {
    // Case channel - get case owner
    List<Case> cases = [
        SELECT Id, Owner.Name, Owner.Email, OwnerId 
        FROM Case 
        WHERE Id = :parentId
    ];
    System.debug('Employee: ' + cases[0].Owner.Name);
    
} else if (channelType == 'Messaging') {
    // Messaging channel - get agent from MessagingSession
    List<MessagingSession> sessions = [
        SELECT Id, AgentId, Agent.Name, Agent.Email 
        FROM MessagingSession 
        WHERE Id = :parentId
    ];
    System.debug('Employee: ' + sessions[0].Agent.Name);
    
} else if (channelType == 'Voice') {
    // Voice channel - get agent from VoiceCall
    List<VoiceCall> calls = [
        SELECT Id, UserId, User.Name, User.Email 
        FROM VoiceCall 
        WHERE Id = :parentId
    ];
    System.debug('Employee: ' + calls[0].User.Name);
}
```

**Quick version via sf CLI:**
```bash
# Step 1: Get parent record ID
sf data query --query "SELECT ParentId, ChannelType FROM GenOpPlan WHERE AiAgentSession__c = '<SESSION_ID>'" --target-org <ALIAS>

# Step 2: Query based on channel type
# For Case:
sf data query --query "SELECT Owner.Name, Owner.Email FROM Case WHERE Id = '<PARENT_ID>'" --target-org <ALIAS>

# For Messaging:
sf data query --query "SELECT Agent.Name, Agent.Email FROM MessagingSession WHERE Id = '<PARENT_ID>'" --target-org <ALIAS>

# For Voice:
sf data query --query "SELECT User.Name, User.Email FROM VoiceCall WHERE Id = '<PARENT_ID>'" --target-org <ALIAS>
```

**Alternative: Query RecActorActionFeed InsertedById**
The human rep who interacted with the feed:
```apex
List<RecActorActionFeed> feed = [
    SELECT InsertedBy.Name, InsertedBy.Email, Type, CreatedDate
    FROM RecActorActionFeed 
    WHERE Parent.AiAgentSession__c = :sessionId
    ORDER BY CreatedDate ASC
    LIMIT 1
];
System.debug('Employee: ' + feed[0].InsertedBy.Name);
```

**Q: "What actions fired in this session?"**
```apex
// Query AiAgentInteractionStep__dll WHERE stepType = 'ExecuteAction'
input.sql = 'SELECT step.aiAgentInteractionStepOutput__c FROM AiAgentInteractionStep__dll step JOIN AiAgentInteraction__dll interaction ON step.aiAgentInteractionId__c = interaction.id__c WHERE interaction.aiAgentSessionId__c = \'' + sessionId + '\' AND step.aiAgentInteractionStepTypeId__c = \'ExecuteAction\'';
```

**Q: "What knowledge articles were grounded?"**
```apex
// Query AIRetrieverResponse__dll with article names
input.sql = 'SELECT resp.retrievedRecordName__c, resp.qualityScore__c FROM AIRetrieverResponse__dll resp JOIN AIRetrieverRequest__dll req ON resp.aiRetrieverRequestId__c = req.id__c WHERE req.aiAgentSessionId__c = \'' + sessionId + '\'';
```

**Q: "Why did the plan fail?"**
```apex
// Query GenOpPlan for outcome + last RecActorActionFeed for error message
List<GenOpPlan> plans = [SELECT Outcome FROM GenOpPlan WHERE AiAgentSession__c = :sessionId];
List<RecActorActionFeed> lastFeed = [SELECT Body FROM RecActorActionFeed WHERE Parent.AiAgentSession__c = :sessionId ORDER BY CreatedDate DESC LIMIT 1];
```

**Q: "How long did each step take?"**
```apex
// Query AiAgentInteractionStep__dll with duration
input.sql = 'SELECT step.aiAgentInteractionStepTypeId__c, step.durationInMilliseconds__c FROM AiAgentInteractionStep__dll step JOIN AiAgentInteraction__dll interaction ON step.aiAgentInteractionId__c = interaction.id__c WHERE interaction.aiAgentSessionId__c = \'' + sessionId + '\' ORDER BY step.orderNumber__c';
```

### User Interaction Tracking (For SRA Tracer UI)

#### Use Case: Case → Users → User Actions Drill-Down

**Goal:** In the SRA tracer UI, user selects a Case ID from dropdown, sees which employees interacted with it, filters by employee, then sees every action that employee took (questions asked, actions approved/rejected, messages sent).

#### Step 1: Get All Sessions for a Case

```apex
// Find all sessions on a Case
String caseId = '<CASE_ID>';
ConnectApi.CdpQueryInput input = new ConnectApi.CdpQueryInput();

// Option A: For Case channel (uses GenOpPlan.ParentId)
List<GenOpPlan> plans = [
    SELECT Id, AiAgentSession__c, CreatedDate, CreatedBy.Name
    FROM GenOpPlan 
    WHERE ParentId = :caseId
    ORDER BY CreatedDate DESC
];

// Get unique session IDs
Set<String> sessionIds = new Set<String>();
for (GenOpPlan p : plans) {
    if (p.AiAgentSession__c != null) {
        sessionIds.add(p.AiAgentSession__c);
    }
}

// Option B: For Messaging/Voice (uses AiAgentSession__dll.relatedRecordId__c)
// (Only if Case was ALSO a MessagingSession or VoiceCall parent)
input.sql = 'SELECT id__c, startTimestamp__c, endTimestamp__c FROM AiAgentSession__dll WHERE relatedRecordId__c = \'' + caseId + '\'';
ConnectApi.CdpQueryOutputV2 sessions = ConnectApi.CdpQuery.queryAnsiSqlV2(input);
```

**For Tracer UI:** Populate dropdown with Case IDs. On selection, run this query to get `sessionIds` list.

---

#### Step 2: Get All Users Who Interacted with Those Sessions

**Source:** `RecActorActionFeed` (SRA-specific feed) shows which users interacted with the case during SRA sessions.

```apex
// Get all unique users from RecActorActionFeed for these sessions
List<RecActorActionFeed> allFeed = [
    SELECT Id, InsertedById, InsertedBy.Name, InsertedBy.Email, 
           Type, CreatedDate, Body
    FROM RecActorActionFeed
    WHERE ParentId = :caseId
    ORDER BY CreatedDate ASC
];

// Dedupe users
Map<Id, String> userMap = new Map<Id, String>();
for (RecActorActionFeed f : allFeed) {
    if (!userMap.containsKey(f.InsertedById)) {
        userMap.put(f.InsertedById, f.InsertedBy.Name + ' (' + f.InsertedBy.Email + ')');
    }
}

System.debug('Users who interacted: ' + userMap.values());
```

**For Tracer UI:** Show list of users (names + emails) who interacted with this Case. Make it filterable/clickable.

**Note:** `InsertedById` = the human rep user. `ParentId` = Case ID.

---

#### Step 3: Filter by User — Get All Actions for That User

Once user selects a specific employee, show everything they did:

```apex
// Filter feed items by selected user
String selectedUserId = '<USER_ID>'; // From dropdown selection

List<RecActorActionFeed> userActions = [
    SELECT Id, Type, Body, CreatedDate, 
           Status, CommentCount, LikeCount,
           RelatedRecordId // The specific action/CLT/step this relates to
    FROM RecActorActionFeed
    WHERE ParentId = :caseId
      AND InsertedById = :selectedUserId
    ORDER BY CreatedDate ASC
];

// Parse each action type
for (RecActorActionFeed action : userActions) {
    if (action.Type == 'TextPost') {
        System.debug('User asked: ' + action.Body);
    } else if (action.Type == 'ContentPost') {
        System.debug('User received CLT: ' + action.Body); // JSON rendering data
    } else if (action.Type == 'TrackedChange') {
        System.debug('Status update: ' + action.Body);
    } else if (action.Type == 'ActionConfirm') {
        System.debug('User approved action: ' + action.RelatedRecordId);
    }
}
```

**For Tracer UI:** Display as timeline:
- **Timestamp** (CreatedDate)
- **Action Type** (TextPost = question, ContentPost = CLT card shown, ActionConfirm = approved/rejected)
- **Body** (message text or JSON data)
- **Status** (if available — approval status, completion status)

**Action Types Reference:**
| Type | What It Means | How to Parse |
|------|--------------|--------------|
| `TextPost` | User sent a message/question to SRA | `Body` = text content |
| `ContentPost` | SRA rendered a CLT card | `Body` = JSON with `complex_data_type_name`, `rendering_data` |
| `TrackedChange` | Status update (plan started, action completed) | `Body` = status text |
| `CallLogPost` | Voice-specific call log | `Body` = call metadata |
| `ActionConfirm` | User approved/rejected an action | `RelatedRecordId` = action ID, `Status` = approved/rejected |

---

#### Step 4: Get Detailed Context for Each Action

To show WHAT the user was responding to (e.g., "User approved action 'Update Case Status'"), you need to join with:

**For Action Confirmations:**
```apex
// Get action details from GenAiFunction (action definition)
String actionId = action.RelatedRecordId;
List<GenAiFunction> actions = [
    SELECT Id, DeveloperName, Description 
    FROM GenAiFunction 
    WHERE Id = :actionId
];
System.debug('User approved: ' + actions[0].DeveloperName);
```

**For CLT Rendering:**
```apex
// Parse ContentPost body (JSON format)
if (action.Type == 'ContentPost') {
    Map<String, Object> cltData = (Map<String, Object>) JSON.deserializeUntyped(action.Body);
    String cltType = (String) cltData.get('complex_data_type_name');
    System.debug('CLT Type: ' + cltType); // e.g., "solutionCard", "orderSummary"
}
```

**For Messages (TextPost):**
```apex
// Body is plain text
System.debug('User said: ' + action.Body);
```

---

#### Step 5: Get Session-Level Context (What Plan Was Running)

To show "User approved action during Plan X on Session Y":

```apex
// Get session metadata for these actions
List<GenOpPlan> planContext = [
    SELECT Id, Topic, Intent, Outcome, AiAgentSession__c
    FROM GenOpPlan
    WHERE ParentId = :caseId
];

// Map session IDs to topics
Map<String, String> sessionToTopic = new Map<String, String>();
for (GenOpPlan p : planContext) {
    sessionToTopic.put(p.AiAgentSession__c, p.Topic);
}

// Now annotate user actions with plan context
for (RecActorActionFeed action : userActions) {
    // Find which session this action belongs to (infer from CreatedDate vs session start/end)
    // Or: use GenOpPlan.CreatedDate range to bucket actions into sessions
}
```

---

#### Example UI Flow (Tracer)

**Dropdown 1: Select Case**
```
Case-00001234 — Customer Refund Request
Case-00001235 — Product Issue Escalation
Case-00001236 — Billing Dispute
```

**Dropdown 2: Select User (after Case selected)**
```
John Smith (john.smith@example.com) — 12 interactions
Jane Doe (jane.doe@example.com) — 7 interactions
System Agent (system@salesforce.com) — 23 interactions [filter out?]
```

**Timeline View (after User selected)**
```
2026-07-23 10:15:32 — User asked: "Can we issue a refund?"
2026-07-23 10:15:45 — SRA showed CLT: Solution Card (Refund Policy)
2026-07-23 10:16:02 — User approved action: "Create Refund Case"
2026-07-23 10:16:10 — Status update: "Action completed successfully"
2026-07-23 10:17:22 — User asked: "What's the refund timeline?"
```

---

#### Complete Query for Tracer UI Backend

```apex
// Input: caseId (String), selectedUserId (String, optional)

// Step 1: Get all sessions for Case
List<GenOpPlan> plans = [
    SELECT Id, AiAgentSession__c, Topic, CreatedDate
    FROM GenOpPlan 
    WHERE ParentId = :caseId
    ORDER BY CreatedDate DESC
];

// Step 2: Get all users who interacted
List<RecActorActionFeed> allFeed = [
    SELECT InsertedById, InsertedBy.Name, InsertedBy.Email, 
           COUNT(Id) interactionCount
    FROM RecActorActionFeed
    WHERE ParentId = :caseId
    GROUP BY InsertedById, InsertedBy.Name, InsertedBy.Email
];

// Step 3: If user selected, get their actions
if (selectedUserId != null) {
    List<RecActorActionFeed> userActions = [
        SELECT Id, Type, Body, CreatedDate, Status, RelatedRecordId
        FROM RecActorActionFeed
        WHERE ParentId = :caseId
          AND InsertedById = :selectedUserId
        ORDER BY CreatedDate ASC
    ];
    
    // Step 4: Enrich with action metadata
    Set<Id> actionIds = new Set<Id>();
    for (RecActorActionFeed a : userActions) {
        if (a.RelatedRecordId != null && a.Type == 'ActionConfirm') {
            actionIds.add(a.RelatedRecordId);
        }
    }
    
    Map<Id, GenAiFunction> actionMap = new Map<Id, GenAiFunction>([
        SELECT Id, DeveloperName, Description
        FROM GenAiFunction
        WHERE Id IN :actionIds
    ]);
    
    // Return enriched data
    for (RecActorActionFeed a : userActions) {
        if (actionMap.containsKey(a.RelatedRecordId)) {
            System.debug(a.CreatedDate + ' — User ' + a.Type + ': ' + actionMap.get(a.RelatedRecordId).DeveloperName);
        } else {
            System.debug(a.CreatedDate + ' — ' + a.Type + ': ' + a.Body);
        }
    }
}
```

---

#### Additional Filters for Tracer UI

**Filter by Interaction Type:**
- All interactions
- Questions only (`Type = 'TextPost'`)
- Action approvals only (`Type = 'ActionConfirm'`)
- CLT cards shown only (`Type = 'ContentPost'`)
- Status updates only (`Type = 'TrackedChange'`)

**Filter by Time Range:**
```apex
WHERE ParentId = :caseId
  AND InsertedById = :selectedUserId
  AND CreatedDate >= :startDate
  AND CreatedDate <= :endDate
```

**Filter by Session:**
```apex
// First get session date ranges from GenOpPlan
List<GenOpPlan> sessionPlans = [
    SELECT AiAgentSession__c, CreatedDate
    FROM GenOpPlan
    WHERE ParentId = :caseId
];

// Then filter feed items by date range of selected session
// (Since RecActorActionFeed doesn't directly store session ID)
```

---

#### Data Model Summary for UI Developers

| Field | Source | Purpose |
|-------|--------|---------|
| Case ID | User dropdown selection | Parent record filter |
| Session ID | `GenOpPlan.AiAgentSession__c` | Session context (optional grouping) |
| User ID | `RecActorActionFeed.InsertedById` | Filter by employee |
| User Name | `RecActorActionFeed.InsertedBy.Name` | Display name |
| Timestamp | `RecActorActionFeed.CreatedDate` | Timeline ordering |
| Action Type | `RecActorActionFeed.Type` | Icon + label in UI |
| Action Content | `RecActorActionFeed.Body` | Message text or JSON data |
| Action Status | `RecActorActionFeed.Status` | Approved/rejected/completed |
| Related Action | `RecActorActionFeed.RelatedRecordId` | Link to action definition |
| Plan Topic | `GenOpPlan.Topic` | Session context label |

## Related

- **SRA Debugger skill** (`sra-agent-debugger`): Per-session trace and analysis
- **PRD-264**: [AE Dynamic Plan Reporting](https://git.soma.salesforce.com/chad-goldsmith/sra-prds/blob/main/prd-264-ae-dynamic-plan-reporting.md)
- **Git repo**: `git.soma.salesforce.com/chad-goldsmith/agentforce-debug-tools`
