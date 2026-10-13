# Diagnosing a dashboard widget that reads 0 — read the rule, don't guess

The **Analytics** tab (Tableau Next) renders every KPI/graph from a **Semantic Model**
(a "SDM" — Semantic Data Model). Each tile is a *metric* → *measure* → *calculated
field* chain whose formula defines **exactly** what rows it counts. When a widget shows
`0` (or a wrong number) for your seeded data, the fast path is **not** to A/B against
live sessions — it's to **read the widget's formula out of the semantic model** and then
seed a row that satisfies it.

> This was the unlock for the Skywave "Escalation Rate = 0" hunt: after days of
> comparing to a live Voice agent (and two wrong theories — session end-type, then the
> `escalate_to_human` router tool), one REST call to the semantic model gave the literal
> rule: *a `SESSION_END`-type interaction step named `CLOSED_TRANSFERRED`*. Seed that,
> refresh, done.

## Why this works
- The dashboards don't compute anything ad-hoc; they read named metrics from a
  `SemanticModel`. The model is the single source of truth for "what does this tile
  count."
- `SemanticModel` is **NOT a Metadata-API type** (`sf project retrieve -m SemanticModel`
  → `Unknown type: SemanticModel`). But it **is** exposed over REST — the same endpoints
  the "Salesforce Tableau Semantics" VS Code extension (`forcedotcom/tableau-dx`) uses.
- Everything below is authenticated GET — read-only, safe to run against any org.

## Step 1 — list the semantic models
```bash
sf api request rest '/services/data/v67.0/ssot/semantic/models' -o <org> \
  | jq -r '.items[] | "\(.apiName)\t\(.label)\t(base: \(.baseModels[]?.apiName // "-"))"'
```
Match the **label** to the model name the dashboard shows (Analytics → the tile's
Edit/Details, or the "Semantic DX" model title). Note the `baseModels` — a model like
`*_Extension_e11` usually **inherits** its calc fields from a base (`*_SDM_e11`); the
formula may live in the base, so pull both if needed.

> Finding which model a specific widget uses, if the UI doesn't say: the
> `AnalyticsWorkspace` and `AnalyticsVisualization` metadata **are** retrievable
> (`sf project retrieve start -m AnalyticsVisualization:<name>`), and each `.uaviz`
> carries `<dataSource>` (= the SDM apiName) and `<fieldName>` (= the metric/measure it
> plots). Workspaces list their SDM assets under `assetType=SemanticModel`.

## Step 2 — pull the full model definition
```bash
sf api request rest '/services/data/v67.0/ssot/semantic/models/<apiName>' -o <org> > model.json
jq -r 'keys[]' model.json
```
Relevant keys (each is an array of objects; a calc field's formula is in its
**`expression`**):
- `semanticMetrics` — the dashboard-facing metrics (wrap a measure + filter + time
  dimension + additional dimensions).
- `semanticCalculatedMeasurements` — measures (e.g. `Escalated_Sessions_clc`,
  `Escalation_Rate_clc`).
- `semanticCalculatedDimensions` — row-level/session-level derived fields (e.g.
  `Escalation_Status_clc`). **This is usually where the real condition lives.**
- `semanticDataObjects` — the logical objects and their mapping to physical DMO fields.
- `semanticRelationships`, `semanticModelFilters`, `semanticParameters`, `baseModels`.

## Step 3 — extract the formula chain for the failing tile
Search all calc fields for a keyword and print their formulas (HTML-unescape the
`expression`):
```bash
python3 - <<'PY'
import json, html
m = json.load(open('model.json'))
kw = 'escal'   # the tile's name/keyword
for key in ('semanticMetrics','semanticCalculatedMeasurements','semanticCalculatedDimensions'):
    for it in (m.get(key) or []):
        blob = (it.get('apiName','')+it.get('label','')).lower()
        if kw in blob:
            expr = html.unescape(it.get('expression') or it.get('formula') or '')
            print(f"[{key}] {it.get('apiName')}  ({it.get('label')})\n    {expr}\n")
PY
```
Then **follow the chain**: metric → its `measure` → that measure's `expression`
(references other measures/dimensions) → each referenced calc dimension's `expression`.
Keep resolving `[Bracketed_Names]` until you bottom out on a **physical DMO field +
literal value**.

Also read the **metric wrapper** itself (`semanticMetrics`): it can add a `filter`
(e.g. `AI Agent Interaction Type != SESSION_END`), a `timeDimension` (which timestamp
the tile buckets on — matters for date-window visibility), and `additionalDimensions`.
A tile can read 0 because of the metric filter, not the measure.

## Step 4 — translate the formula to "what row must exist"
Formulas are Tableau-style. The patterns you'll see:
- `{ FIXED [Obj].[Key] : AGG(...) }` — a **Level-Of-Detail** aggregate computed per
  `Key` (usually per session). `MAX(IF cond THEN 1/TRUE ...)` = "TRUE if **any** child
  row satisfies `cond`."
- `[Logical_Object].[Logical_Field] = 'VALUE'` — a condition on a physical DMO column.
  Resolve `[Logical_Object].[Logical_Field]` → the `ssot__..._dlm.ssot__..._c` column via
  `semanticDataObjects` (or the STDM schema in `stdm_schema.py`). The **value** is the
  literal you must write into that column.
- `COUNTD(IF [SomeStatus] THEN [Session_Id] END)` — counts sessions where the derived
  status is true.
- `DATEDIFF('HOUR', {FIXED session: MAX(end_ts)}, NOW()) >= 24` — a time clause; note
  whether it's `AND` (hard requirement) or `OR` (a fallback you can sidestep).

Now you know the exact row: which DMO, which column, which value.

## Step 5 — seed it, refresh, verify
1. Add/adjust the row in your generator (Path 4 SObject seeder / Path 5 Ingestion API).
2. Refresh: Path 4 → Full-Refresh the relevant `SDO_Analytics_*_Home` stream; Path 5 →
   re-push (UPSERT).
3. Verify at the **DMO** level (not the dashboard, which lags): query the CDP `/query`
   API for the exact condition the formula tests, e.g. distinct sessions with a step
   `Name='CLOSED_TRANSFERRED' AND StepType='SESSION_END'`. When the DMO count matches
   your target, the tile will render once the Tableau Next layer re-materializes
   (minutes-to-hours lag — the DMO count is your real confirmation).

## Worked example — the Escalation Rate case
```
semanticMetrics:            "Escalation Rate"  → measure Escalation_Rate_clc,
                             filter: AI_Agent_Interaction.Type != 'SESSION_END',
                             timeDimension: AI_Agent_Session.Start_Timestamp
Escalation_Rate_clc      =  [Escalated_Sessions_clc] / [Unique_Sessions_clc]
Escalated_Sessions_clc   =  COUNTD(IF [Escalation_Status_clc] THEN [AI_Agent_Session].[AI_Agent_Session_Id] END)
Escalation_Status_clc    =  { FIXED [AI_Agent_Session].[AI_Agent_Session_Id] : MAX(
                               IF ( [AI_Agent_Interaction_Step].[Ai_Agent_Interaction_Step_Type]='SESSION_END'
                                    OR DATEDIFF('HOUR', {FIXED session: MAX([AI_Agent_Interaction].[End_Timestamp])}, NOW()) >= 24 )
                                  AND [AI_Agent_Interaction_Step].[Name]='CLOSED_TRANSFERRED'
                               THEN TRUE ELSE FALSE END )}
```
Bottoms out at: **`ssot__AiAgentInteractionStep__dlm` with
`ssot__AiAgentInteractionStepType__c='SESSION_END'` and `ssot__Name__c='CLOSED_TRANSFERRED'`**.
The `OR …>=24h` is a fallback, so setting the step **type** to `SESSION_END` makes even
<24h-old sessions count. Seed that closure step on escalated sessions → escalation
went 0 → 12%.

## Gotchas
- `expression` values are **HTML-entity-encoded** (`&#39;` = `'`, `&gt;` = `>`) — unescape
  before reading.
- Calc fields often live in the **base** model, not the extension you're looking at —
  check `baseModels` and pull the base too.
- The **metric wrapper** (`semanticMetrics`) can filter/scope independently of the
  measure — a tile can read 0 purely because of its filter or time dimension.
- API version: `…/validate` is pinned to `v67.0` in the extension; the list/get
  endpoints work on recent versions — use `v67.0`+.
- These endpoints are **read** here; the extension can also PUT/POST to deploy model
  changes (`/ssot/semantic/models` POST, `…/{apiName}` PUT) if you ever need to *change*
  a rule rather than seed to it — but seeding the data to match the shipped rule is
  almost always the right move for a demo.
