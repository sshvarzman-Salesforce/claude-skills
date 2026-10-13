---
name: agentforce-observability-data
description: >
  How Agentforce Observability collects data, what STDM looks like under the hood,
  and the five ways to get conversation rows into the dashboards. Includes the
  SDO_Agentforce_Observability QBrix architecture (custom-objects → SalesforceDotCom
  data streams → Data Kit DMO mappings) AND the non-SDO path (push synthetic STDM
  rows straight into the DMOs via the Data Cloud Ingestion API — for orgs that
  can't install the QBrix).
  TRIGGER when: user asks how Optimization/Insights/Analytics get their data, wants
  to populate observability dashboards for a demo, asks about the SDO Observability
  brix or "Agentforce Analytics Foundations" data kit, wants to seed/refresh
  observability data in a NON-SDO org (trial/sandbox/demo org) where the QBrix can't
  be installed, or wants to understand why synthetic and real sessions appear together.
  DO NOT TRIGGER when: extracting raw STDM parquet for analysis (use
  sf-ai-agentforce-observability), authoring agents (use developing-agentforce), or
  general Data Cloud ingestion (use sf-datacloud-prepare).
license: MIT
metadata:
  version: "1.1.0"
---

# agentforce-observability-data: How the Observability Data Model is Populated

Agentforce Observability surfaces **Analytics** (Tableau Next dashboards) and **Optimization** (Insights / Moments / Sessions & Intents) inside Agentforce Studio. Both read from the same **Session Tracing Data Model (STDM)** — a set of `ssot__AiAgent*__dlm` Data Model Objects in Data Cloud.

## STDM at a glance — 11 canonical DMOs

```
ssot__AiAgentSession__dlm                       (one row per conversation)
ssot__AiAgentSessionParticipant__dlm            (the agent or user in that session)
ssot__AiAgentInteraction__dlm                   (a single user-turn / agent-turn pair)
ssot__AiAgentInteractionMessage__dlm            (the actual message text, both sides)
ssot__AiAgentInteractionStep__dlm               (planner/action step inside an interaction)
ssot__AiAgentMoment__dlm                        (a flagged subset of interactions)
ssot__AiAgentMomentInteraction__dlm             (Moment ↔ Interaction junction)
ssot__AiAgentTopic__dlm                         (topic catalog)
ssot__AiAgentTag__dlm                           (tag values)
ssot__AiAgentTagDefinition__dlm                 (tag schema)
ssot__AiAgentTagAssociation__dlm                (which tag attached to what)
ssot__AiAgentTagDefinitionAssociation__dlm      (tag schema linkage)
```

Plus a few `ssot__AiAgent*Action__dlm` and `ssot__AiAgentGenerativeAiUsage__dlm` for action tracing and token accounting.

These DMOs are **created by the "Agentforce Analytics Foundations" Data Kit** that Salesforce ships and deploys when you toggle **Setup → Einstein Audit, Analytics, and Monitoring Setup → Agentforce Session Tracing**. Verify status at *Setup → Data Kits → Agentforce Analytics Foundations → Deployment History*. If failed, re-toggle Session Tracing to redeploy.

## The five data-population paths

> Paths 1-4 assume the platform's own pipelines (real runtime, analyzer, Agent
> API, or the SDO QBrix). **Path 5 is for orgs that CAN'T install the QBrix** (any
> non-SDO: trial, sandbox, TDX/demo orgs) — you push synthetic STDM rows straight
> into the canonical DMOs via the Data Cloud Ingestion API. See Path 5 below and
> the full [`references/non-sdo-ingestion-api-playbook.md`](references/non-sdo-ingestion-api-playbook.md).

### Path 1: Real Agentforce conversations (the production source)

Connector: `AIPlatform` (system-managed, Salesforce writes — not customer-writable).

When a real session runs against any Agentforce agent (Builder, Voice, MIAW, NGC, WhatsApp, etc.), the Agentforce runtime emits events. Five `AIPlatform` data streams pick them up automatically and land them in the canonical DMOs:

```
AiAgentSession              → ssot__AiAgentSession__dlm
AiAgentInteraction          → ssot__AiAgentInteraction__dlm
AiAgentInteractionMessage   → ssot__AiAgentInteractionMessage__dlm
AiAgentInteractionStep      → ssot__AiAgentInteractionStep__dlm
AiAgentSessionParticipant   → ssot__AiAgentSessionParticipant__dlm
```

**Customer-side action: none.** The flow is purely server-side once the toggles are on. You **cannot delete** rows from these streams via Bulk Ingestion — the connector rejects writes (`404` from `/api/v1/ingest/jobs`). RTBF policies are the only customer-facing erasure mechanism for this data.

### Path 2: AgentOpt — derived tags (also system-managed)

Connector: `AgentOpt` (system-managed). Four DLOs:

```
AgentOpt_Tag_F173B7AD           → ssot__AiAgentTag__dlm
AgentOpt_Tag_Def_F173B7AD       → ssot__AiAgentTagDefinition__dlm
AgentOpt_Tag_Association_*      → ssot__AiAgentTagAssociation__dlm
AgentOpt_Tag_Def_Association_*  → ssot__AiAgentTagDefinitionAssociation__dlm
```

The hex suffix is org-specific and cycles per Optimization deployment. AgentOpt is the **Optimization analyzer's output channel** — it tags Moments with quality scores, request categories, etc. Also not customer-writable.

### Path 3: Generate sessions via Agent API (the supported synthetic path)

Run real Agent API conversations against an existing agent. Each `POST /einstein/ai-agent/v1/agents/{id}/sessions` produces genuine STDM rows that flow through Path 1.

This is what tools like the **af-conversation-primer** repo (`SFDC-Assets/af-conversation-primer`) do — drive an LLM-powered persona to chat with the agent over Agent API; sessions land in STDM organically.

**Indistinguishable from real production** because they *are* real sessions. Topic-Quality scores etc. are produced by the Optimization analyzer downstream.

### Path 4: SDO_Agentforce_Observability QBrix (the bulk-loaded synthetic path)

This is the path used by the SE demo brix. Three-stage pipeline:

```
1. CRM custom objects (sObjects, populated via Data Loader / Apex)
   ─ SDO_Analytics_AIAgentSession_v2__c           ~1,900 rows
   ─ SDO_Analytics_AiAgentInteraction_v2__c       ~9,500 rows
   ─ SDO_Analytics_AIAgentInteractionMessa_v2__c
   ─ SDO_Analytics_AIAgentInteractionStep_v2__c
   ─ SDO_Analytics_AIAgentMoment_v2__c
   ─ SDO_Analytics_AIAgentMomentInteractio_v2__c
   ─ SDO_Analytics_AIAgentSessionParticipa_v2__c
   ─ SDO_Analytics_AIAgentTag_v2__c
   ─ SDO_Analytics_AIAgentTagDefinition_v2__c
   ─ SDO_Analytics_AIAgentTagAssociation_v2__c
   ─ SDO_Analytics_AIAgentTagDefinitionAss_v2__c

2. Data Cloud "SalesforceDotCom" data streams (one per custom object)
   ─ SDO_Analytics_AIAgentSession_v2_c_Home       (DLO: ..._Home__dll)
   ─ SDO_Analytics_AiAgentInteraction_v2_Home
   ─ ...
   These pull custom-object rows into a DLO on a refresh schedule.

3. SDO_Agentforce_Observability Data Kit (DataPackageKitDefinition)
   Contains 13 DataPackageKitObjects, each mapping one SDO DLO to a
   canonical ssot__AiAgent*__dlm DMO. Same DMO that Path 1 writes to.
```

The kit is `MarketDataKit` /  `DataPackageKitDefinition` metadata type. Each kit object looks like:
```xml
<DataPackageKitObject>
    <parentDataPackageKitDefinitionName>SDO_Agentforce_Observability</parentDataPackageKitDefinitionName>
    <referenceObjectName>ssot__AiAgentSessionParticipant__dlm</referenceObjectName>
    <referenceObjectType>MktDataModelObject</referenceObjectType>
</DataPackageKitObject>
```

Result: synthetic and real rows live in the **same DMO** and are indistinguishable to the Tableau Next dashboards. Filter by date range to separate them by approximation.

> ⚠️ **Re-branding the synthetic data?** If you populate the SDO custom
> objects with your own sessions (custom Apex seeder etc.), the enum
> **string values must match the real STDM vocabulary** (`Input`/`Output`,
> `TURN`, `TOPIC_STEP`/`LLM_STEP`/`ACTION_STEP`, `resolved`/`escalated`,
> role `AGENT`/`USER`) or the session detail view renders but breaks —
> both bubbles show as the agent, duration/interactions/latency show "--",
> and the trace won't open. The fields land in the DMO verbatim through the
> Data Kit mapping, so a wrong enum is invisible until the UI. Full table,
> telemetry-trace and timestamp rules in
> [`references/sdo-qbrix.md`](references/sdo-qbrix.md) → "Seeding your own
> synthetic sessions". When docs and live data disagree, live AIPlatform
> rows win.
>
> **Getting the session to RENDER in the dashboards** is a separate, harder
> problem from the enum/viewer fixes, and the two dashboard surfaces have
> DIFFERENT gates:
> - **Analytics** needs: participant rows with a populated `Participant__c`
>   (AGENT→GenAiPlannerDefinition Id, USER→MessagingEndUser Id) — empty →
>   session silently dropped — AND optional fields carrying the literal
>   `NOT_SET` sentinel, not empty/null.
> - **Optimization Insights + Sessions & Intents** additionally need a
>   matching **`ssot__Bot__dlm`** row (joined on `DeveloperName` = the
>   session's agent api name). That DMO is fed from real `BotDefinition`
>   records, so it only exists for **deployed** agents. A synthetic agent
>   that isn't deployed won't show here until you deploy a barebones agent
>   with that api name (or seed the Bot row).
> - Quality charts (Quality-by-Subagent/Intent) need a `Quality_Score` (1-5)
>   tag associated to every **moment** — pre-baked, since the analyzer never
>   scores synthetic data.
> - **Session Outcome + Deflection / Abandon / Escalation rates** are a SEPARATE
>   tag system (not Quality-by-Intent): platform `std_Deflection_Score` /
>   `std_Abandonment_Score` tags, **session-level** associations, and the KPIs read
>   the association's own **`ValueText__c` + `SourceType__c='PROMPT_TEMPLATE'`**
>   (NOT the joined tag value) — miss these and the rates read ~0. **Escalation Rate
>   is different**: no tag, and NOT the end-type — the semantic model counts a session
>   as escalated iff it has an interaction step with
>   `ssot__AiAgentInteractionStepType__c='SESSION_END'` AND `ssot__Name__c='CLOSED_TRANSFERRED'`
>   (the `SessionEndReason` closure code; `CLOSED_ACTION`/`CLOSED_USER_REQUEST` are the
>   non-escalated codes). NOT the `__human__` topic and NOT the `escalate_to_human`
>   router tool (that's the runtime *cause*; the SDM reads the downstream session-end
>   reason). Full recipe: non-SDO playbook §11.
> - **Millisecond-precise drill-down "hero" traces** are impossible via Path 4
>   (custom SObject DateTime = whole seconds) — write those few sessions via Path 5
>   (Ingestion API), coexisting with the bulk. Real step choreography + `gen_ai.*`
>   payloads + UUID ids: non-SDO playbook §12.
>
> **For a full re-theming walkthrough (any industry), see
> [`references/rebrand-seeder-playbook.md`](references/rebrand-seeder-playbook.md)**
> — object graph, the Bot__dlm gate, the quality-story archetype model,
> conversation timing, a working seeder skeleton, and the run sequence.
> Per-field render mechanics are in
> [`references/sdo-qbrix.md`](references/sdo-qbrix.md).

#### Refreshing the synthetic streams
After bulk-inserting new rows into the SDO custom objects, force a stream refresh:
*Setup → Data Cloud → Data Streams → row → ▼ → Refresh Now → **Full Refresh***. Repeat for each `SDO_Analytics_*_Home` stream.

#### Voice playback for synthetic sessions
Synthetic data omits the `VoiceCall` recording. To enable audio playback in the Optimization tab:
1. Install **ECI Base Config brix**.
2. From any Opportunity → action **Einstein Configuration – ECI** → save with a sample Voice Call + Contact (creates a placeholder `VoiceCall` record).
3. In the Demo Config tab of the SDO Observability Demo app, locate your session, set the audio file on the Session Audio component, click **Upload**.
4. Click **Session Data Stream** → on the resulting `SDO_Analytics_AIAgentSession_*_Home` stream do **Refresh Now → Full Refresh**.

### Path 5: Ingestion API (non-SDO orgs — can't install the QBrix)

For any org where the QBrix is unavailable (trial, sandbox, customer, TDX/demo
orgs), **push synthetic STDM rows straight into the canonical `ssot__AiAgent*__dlm`
DMOs via the Data Cloud Ingestion API.** No custom objects, no Data Kit, no
SalesforceDotCom streams — and, unlike Path 4, **refresh is fully headless**
(pure REST, no browser).

```
your generator ─► CSV per STDM object ─► POST /api/v1/ingest/jobs (JWT→CDP token)
   ─► one IngestApi DLO per object ─► DLO→DMO mapping ─► ssot__AiAgent*__dlm ─► dashboards
```

Skeleton (one IngestApi **connection per STDM object**; all on the Core proxy
`/services/data/v62.0/ssot/...` except the ingest jobs on the c360a edge):
```
POST /ssot/connections?connectorType=IngestApi   {connectorType,label,name}   # submitted name == sourceName
PUT  /ssot/connections/{id}/schema               {schemas:[{...,schemaType:"IngestApi",fields:[{name,label,dataType}]}]}
POST /ssot/data-streams                          {datastreamType:"INGESTAPI", connectorDetails:{name:<returned>,events:[obj]},
                                                   dataLakeObjectInfo:{category:<Profile|Engagement|Related>, PK-only fieldRep,
                                                   +eventDateTimeFieldName if Engagement}, refreshConfig:{refreshMode:"UPSERT"}}
POST /ssot/data-model-object-mappings?dataspace=default   {sourceEntityDeveloperName:<DLO>__dll, targetEntityDeveloperName:ssot__X__dlm, fieldMapping:[...]}
# then push rows on the CDP edge:
POST /api/v1/ingest/jobs  {object,sourceName:<SUBMITTED name>,operation:"upsert"} → PUT .../batches (text/csv) → PATCH .../{id} {state:"UploadComplete"}
```

Load-bearing facts (each cost real time to discover — do NOT re-derive):
- **DLO `category` MUST equal the target DMO's category** or the mapping 400s.
  Session+Step = `Profile`; Participant/Interaction/Message/Moment/MomentInteraction/
  TagAssociation = `Engagement` (these also need `eventDateTimeFieldName`);
  Tag/TagDefinition/TagDefinitionAssociation = `Related`.
- **`sourceName` = the name you SUBMITTED at connection-create**, NOT the returned
  hash-suffixed name (that 404s forever); the returned name goes in
  `connectorDetails.name`.
- **AGENT participant must use the GenAiPlannerDefinition Id +
  `ParticipantObject='GenAiPlannerDefinition'`** (USER = `005` id +
  `ParticipantObject='User'`) — this is what puts the agent in the **Optimization**
  Agent dropdown. A BotDefinition Id / empty ParticipantObject lands data in the
  DMO but the agent never appears.
- **`ssot__ExternalSourceId__c` = the org id on every row** — the **Analytics-tab**
  render gate (Tableau Next scopes by it). NULL → data shows in Optimization but
  the agent is absent from Analytics. (Also: keep the Agent Analytics app updated —
  an old version renders a thin/different dashboard.)
- These two are the "data is in the DMOs but the dashboard is empty" gotchas —
  Optimization and Analytics are different surfaces with different gates.
- Write **TODAY-RELATIVE ISO-8601 timestamps** (this is the whole point — absolute
  dates decay out of the dashboard window; that's the usual reason a pre-existing
  non-SDO synthetic set has stopped rendering).
- The **Bot join gate still applies** (Optimization/Sessions need a `ssot__Bot__dlm`
  row for the agent api name — deployed+activated agent).
- **The CDP OAuth scopes (`cdp_ingest_api`/`cdp_query_api`) are the only manual
  gate** — not deployable (v67); add in Setup → App Manager → Edit.
- Ingest is async — **gate on the DMO row count, not the ingest job state**.

**Full recipe, the 11-object category/PK/field-map table, the exact KPI formulas, the
enum & identity tables, the complete gotcha ledger, and a copy-paste run sequence are in
[`references/non-sdo-ingestion-api-playbook.md`](references/non-sdo-ingestion-api-playbook.md).
A runnable, dependency-free reference implementation (client + schema + generator/CLI)
ships in [`reference-impl/`](reference-impl/) — edit `AGENT_API_NAME` + `ARCHETYPES` and
run `setup`/`push`/`verify`.**

## Removing synthetic data

The Path 4 architecture means **you can use plain SOQL DELETE** against the source CRM custom objects, then refresh the streams:

```bash
sf data query --target-org <alias> \
  --query "SELECT Id FROM SDO_Analytics_AIAgentSession_v2__c WHERE Start_Timestamp__c < 2026-05-01T00:00:00Z" \
  --result-format csv > old_ids.csv

sf data delete bulk --target-org <alias> \
  --sobject SDO_Analytics_AIAgentSession_v2__c --file old_ids.csv
```

Then refresh the corresponding `_Home` data stream (Full Refresh). DMO row count shrinks accordingly. Cascade through all 11 SDO objects to fully purge.

For **Path 5** (Ingestion API) data, you own the source, so removal is clean:
delete the DLO→DMO **mappings first**, then the streams
(`DELETE /ssot/data-streams/{name}?shouldDeleteDataLakeObject=true`), then the
connections — that order matters (a mapped DLO can't be deleted → stream delete
412s `CANNOT_DELETE_ENTITY`; a connection with a live stream → 400
`DEPENDENCY_EXISTS`). Removing a DLO's mapping + the DLO drops those rows from the
canonical DMO. `~/dev/pronto/observability/scripts/teardown_source.py` does this.
To refresh in place instead, just re-push (streams are `UPSERT`).

For Path 1/2 data (system-managed, real conversations), use **RTBF policies** with a predicate (Setup → Data Cloud → Right To Be Forgotten Policies). There is no other supported customer-driven delete.

## Onboarding gap checklist

Verify in this order; stop at the first miss.

1. **Org-level toggles** — Setup → Einstein Audit, Analytics, and Monitoring Setup
   - Agentforce Session Tracing & Data Model: ON
   - Agentforce Optimization (Beta): ON
   - Default Dataspace: selected
2. **Foundations data kit** — Setup → Data Kits → Agentforce Analytics Foundations → Deployment History → all green. If failed, re-toggle Session Tracing.
3. **Tableau Next license** — Setup → Permission Sets → "Tableau Next Limited Consumer" exists. If missing, activate Salesforce Foundations ($0 SKU).
4. **Service Agent Data Model installed** — Setup → Agent Studio → Agent Analytics (Beta) → click **Install Service Agent Data Model**. (Older orgs labeled this as "Service Agent Analytics app".) This step is required even when STDM toggles are on and the Foundations Data Kit deployed — without it, Agentforce Studio's Sessions & Intents view stays empty even when STDM DMOs have data. Pre-req: STDM provisioning ~1h.
5. **User permission sets**
   - `AgentforceInteractionExplorer` ("Access Agentforce Optimization") — for Optimization tab
   - `TableauNextLimitedViewer` — for Analytics tab (cards fail without it)
   - `Data Cloud User` (or equivalent like `xDO_DataCloud_Base_PSG`) — for queries
   - User profile must have `API Enabled = true` (Tableau Next metric cards fail otherwise)
6. **Data Cloud Setup → Ingestion API → AgentOpt** in "In Use" state (sandbox-only re-activation step from official onboarding PDF)

For sandbox orgs only: provision Data Cloud, manually re-activate the AgentOpt connector (auth doesn't replicate from prod), re-toggle STDM and Optimization to kick off stream re-activation.

### Stuck connector: AIPlatform streams ACTIVE but `LastRefreshDate=null`

Common pattern in trial/SDO orgs after first enabling Session Tracing: the AIPlatform connector and its streams (`AiAgentSession`, `AiAgentInteraction`, `AiAgentInteractionMessage`, etc.) sit in `DataStreamStatus=ACTIVE` with `ImportRunStatus=NONE`, `LastRefreshDate=null`, `TotalNumberOfRowsAdded=null` — meaning they've been provisioned but have never run, even after real conversations exist in `Conversation` and `BotVersion` is Active. Symptoms: Sessions & Intents stays empty for hours after publishing the agent and chatting with it.

**Fix: toggle-cycle Session Tracing.** Setup → Einstein Audit, Analytics, and Monitoring Setup → Agentforce Session Tracing & Data Model → OFF → save → wait ~1 minute → ON → save.

**Critical wait time: hours, not minutes.** After the toggle cycle, the connector backfills all conversations from the entire history (not just future ones). Field-confirmed in a trial org where data appeared "a couple hours later" after the toggle cycle, with all prior conversations included. Don't conclude failure based on a 10-minute check — re-query the next day if needed.

Diagnostic query to monitor whether the connector started flowing:
```bash
sf data query --target-org <alias> -q \
  "SELECT Name, ImportRunStatus, DataStreamStatus, LastRefreshDate, TotalNumberOfRowsAdded FROM DataStream WHERE Name LIKE '%AiAgent%' ORDER BY Name"
```

Once `LastRefreshDate` flips to a non-null value and `TotalNumberOfRowsAdded > 0`, the pipeline is alive. From that point forward new conversations land within minutes, not hours.

## Key insight: all five paths converge at the same DMO

```
Path 1 (AIPlatform)  ─┐
Path 2 (AgentOpt)    ─┼──>  ssot__AiAgent*__dlm  ──>  Optimization + Analytics
Path 3 (Agent API)   ─┤                              (Agentforce Studio UI)
Path 4 (SDO QBrix)  ──┤     SalesforceDotCom DLO ──Data Kit map──┘
Path 5 (Ingestion API)┘     IngestApi DLO ──DLO→DMO map──┘   (non-SDO orgs)
```

Once you know which path produced a row, you know:
- Whether you can delete it from the customer side (Path 4: SOQL on the custom
  objects; Path 5: delete your own mappings→streams→connections; Paths 1-3: only RTBF).
- Whether the agent name comes from the live Agent record (Paths 1–3), the
  synthetic `SDO_*_v2__c.AI_Agent_Api_Name__c` field (Path 4), or your generator's
  spec (Path 5).
- Whether tags/quality scores are produced by Optimization (real-time analyzer,
  Path 1+2) or pre-baked (Paths 4+5).
- Which host loads/refreshes it: SalesforceDotCom streams need an interactive
  browser refresh (Path 4); the Ingestion API is fully headless REST (Path 5).

## When a dashboard widget / metric / graph reads 0 (or wrong) — read the rule, don't guess

The **Analytics** tiles are driven by a **Semantic Model** ("SDM"); every KPI is a
*metric → measure → calculated field* chain whose formula defines **exactly** which rows
it counts. When a widget shows `0` for your seeded data, do **not** reverse-engineer it by
A/B-ing against live sessions — **pull the widget's formula straight from the semantic
model** and seed a row that satisfies it. `SemanticModel` isn't in the Metadata API, but
it's readable over REST (the endpoints the `forcedotcom/tableau-dx` VS Code extension
uses):

```bash
# list models → match the label the dashboard shows (note baseModels — calc fields
# often live in the base, not the *_Extension_e11 you're viewing):
sf api request rest '/services/data/v67.0/ssot/semantic/models' -o <org> \
  | jq -r '.items[] | "\(.apiName)\t\(.label)"'
# pull the full definition; the formula for each calc field is its `expression`:
sf api request rest '/services/data/v67.0/ssot/semantic/models/<apiName>' -o <org> > model.json
# keys: semanticMetrics / semanticCalculatedMeasurements / semanticCalculatedDimensions
```

Follow the chain (metric → measure `expression` → calc-dimension `expression`) until it
bottoms out on a **physical DMO field + literal value**, then seed that. Real example:
`Escalation Rate` bottomed out at an interaction step with
`ssot__AiAgentInteractionStepType__c='SESSION_END'` and `ssot__Name__c='CLOSED_TRANSFERRED'`
— which took the tile from 0 → 12% once seeded. (Two earlier guesses from live-data
comparison — session end-type, then the `escalate_to_human` router tool — were both wrong;
reading the formula settled it in one call.)

**Full step-by-step (find the model, extract/trace the formula, translate the LOD to a
row, seed→refresh→verify, gotchas) → [`references/reading-the-semantic-model.md`](references/reading-the-semantic-model.md).**
