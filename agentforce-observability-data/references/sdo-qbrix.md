# SDO_Agentforce_Observability QBrix — install & operation

## What it deploys
- 1 Custom Application: **Agentforce Observability Demo** (`SDO_Agentforce_Observability_Demo`)
- 12 custom objects: `SDO_Analytics_AIAgent*_v2__c` + `SDO_CustomerSignalsIntelligenceData__c`
- 5 Apex helper classes:
  - `SDO_Analytics_ReportFakerController` — VF page for synthetic report generation (uses MetadataService)
  - `SDO_Analytics_SyntheticSessionSearch` — search by external UUID
  - `SDO_Analytics_QuickAccessSession` — resolve agent API name from session participant
  - `SDO_Analytics_DataStreamNavigator` — look up `DataStream` Id by name (used by "Session Data Stream" button)
  - `SDO_Analytics_SessionAudio` — upload audio file → link to VoiceCall
- 1 Data Kit: `SDO_Agentforce_Observability` (DataPackageKitDefinition v6.0)
  - 13 DataPackageKitObjects mapping each DLO → standard `ssot__AiAgent*__dlm` DMO
- N Data Streams (SalesforceDotCom connector type) — one per custom object

## Install order (per the official internal instructions)
1. Install **Data Cloud | Setup Automation** brix first (preconditions for the kit to deploy reliably)
2. Install **Agentforce Observability** brix
3. Wait 2–3 hours for STDM provisioning
4. Setup → Agent Analytics (Beta) → install **Service Agent Analytics** + **Employee Agent Analytics** (if they didn't auto-install)
5. Data Cloud → Data Streams → for each `SDO_Analytics_*_Home` stream: **Refresh Now → Full Refresh**

Approximate end-to-end time on a fresh SDO: **~2 hours**.

## Validation
- Setup → Data Kits → **Agentforce Analytics Foundations** → Deployment History → all green
- Setup → Data Kits → **SDO Agentforce Observability** → Deployment History → all green
- If anything red: re-toggle **Setup → Einstein Audit, Analytics, and Monitoring Setup → Agentforce Session Tracing** off then on. This kicks the kit redeployment.

## Where to see the data
- App Launcher → **Agentforce Studio** → Observe → Analytics — filter Agent Type = Service Agent
- App Launcher → **Agentforce Studio** → Observe → Optimization → Insights/Moments — filter Agent = `DriveMax_Support`, Date Range = 90 days

## Voice playback (optional)
Synthetic sessions have no `VoiceCall` recording. To get the audio player working in Optimization:
1. Install **ECI Base Config brix**
2. Go to any Opportunity → action **Einstein Configuration – ECI** → choose any sample Voice Call + Contact → Save (creates a placeholder VoiceCall record like `VC-00000001`)
3. In the **Agentforce Observability Demo** app → **Demo Config** tab → search by Session ID
4. In the **Session Audio File** component → select the VoiceCall → Upload Audio File
5. Click **Session Data Stream** button → on the resulting `SDO_Analytics_AIAgentSession_..._Home` stream → Refresh Now → Full Refresh
6. Audio player appears in Optimization for that session

## Demo data scope
After successful install, expect roughly:
- ~1,900 synthetic sessions
- ~9,500 synthetic interactions
- ~1,700 synthetic moments
- A handful of agents incl. `DriveMax_Support`, `At_Your_Service`, `SDO_Service_Agentforce`, `Demo_Assist_Mock_Data`, `Simple_ASA`

These show up in the Agent dropdown alongside any real agents in the org.

## Seeding your own synthetic sessions — STDM enum vocabulary (CRITICAL)

When you write your own rows into the `SDO_Analytics_AIAgent*_v2__c` custom
objects (e.g. to re-brand the stock DriveMax data for a customer demo), the
enum **string values must match the real STDM vocabulary exactly** or the
session detail view breaks in specific, misleading ways: the session still
*renders*, so it looks like a data-integrity problem, but individual fields
are wrong.

These were verified against **live AIPlatform (real-session) DMO rows** —
the decisive source. Where the internal canvas/JSON-schema docs disagree
with live data, **live data wins**: a real session that renders correctly
in the UI proves which values the UI accepts. Query to confirm in any org:
```sql
SELECT "ssot__AiAgentInteractionType__c", COUNT(*) FROM "ssot__AiAgentInteraction__dlm"
WHERE "ssot__DataSourceId__c" = 'AIPlatform_AGENT_SESSION_TRACING' GROUP BY 1
```

| Field (custom-object API name) | Correct value | Wrong value seen | Symptom if wrong |
|---|---|---|---|
| `AI_Agent_Interaction_Message_Type__c` | `Input` / `Output` | `USER_INPUT` / `AGENT_RESPONSE` | **Both chat bubbles render as the agent** — Session Log aligns by this; unknown types fall through to the agent default |
| `Ai_Agent_Interaction_Msg_Content_Type__c` | `text/plain` (or `application/json`, `audio/wav`) | `TEXT` | message rendering |
| `Ai_Agent_Interaction_Type__c` | `TURN` | `PROMPT_RESPONSE` | **Session Duration, Number of Interactions, Average Latency all show "--"** — dashboard counts TURN rows and derives metrics from them |
| `Ai_Agent_Interaction_Step_Type__c` | `TOPIC_STEP` / `LLM_STEP` / `ACTION_STEP` (also `VARIABLE_UPDATE_STEP`, `TRUST_GUARDRAILS_STEP`) | `PlannerStep`/`ActionStep`/`ResponseStep`, or the docs' `UserInputStep`/`LLMExecutionStep`/`FunctionStep` | unknown step types in the trace view |
| `AI_Agent_Session_End_Type__c` | `resolved` / `escalated` / `deflected` / `other` | `EndedNormally` | Session Flow outcome label |
| Participant role (`AI_Agent_Session_Participant_Role__c`) | `AGENT` / `USER` (live) — docs say `Owner`/`Observer` | — | participant attribution |
| Participant type (`AI_Agent_Type__c`) | `EinsteinServiceAgent` | — | — |

**Telemetry trace fields** must be non-empty (synthetic UUIDs are fine) or
the per-bubble **session trace view won't open**:
- Interaction: `Telemetry_Trace__c` + `Telemetry_Trace_Span__c`
- Step: `Telemetry_Trace_Span_Id__c` — share the parent interaction's trace
  id so the trace renders as one tree.

**Timestamps:**
- Session / SessionParticipant `End_Timestamp__c` is a plain **writable**
  DateTime (no Days/Time formula pair). Write it as a GMT instant
  (`DateTime.newInstanceGmt(...)`) so it matches the `Start_Timestamp__c`
  formula, which reads `Start_Days__c` + `Start_Time__c` as a wall-clock
  string in GMT. Writing End via `DateTime.newInstance` (running-user TZ)
  makes Start and End disagree by the TZ offset → negative duration →
  Studio hides the session. Dropping End entirely → null duration, also
  hidden. Both are real failure modes observed in the field.
- Interaction `Start_Timestamp__c`/`End_Timestamp__c` are **read-only
  formulas** built from `Start_Days__c`/`End_Days__c` + `Start_Time__c`/
  `End_Time__c` — populate the Days/Time fields, not the timestamp.
- When spreading sessions across "the last N days", start the day-offset at
  **1, not 0** — a today-date combined with an afternoon/evening time lands
  ahead of an early-morning org clock and produces future-dated sessions.
- 🚫 **Custom SObject `DateTime` fields truncate to whole SECONDS on save**
  (verified: write `12:34:56.789`, read back `.000`; formula fields are
  second-precision too — `DATETIMEVALUE` returns NULL for `HH:mm:ss.SSS`). So a
  Path-4 (SObject) trace can NEVER show the sub-second, random step timings a
  real session has. If you need **drill-down-quality "hero" sessions** with real
  millisecond timings + realistic step choreography + real `gen_ai.*`/`mgr.*`
  payloads, write those few sessions via the **Path-5 Ingestion API** (they
  coexist with the Path-4 bulk data in the same DMOs) — see the non-SDO playbook
  §12.

**Deflection / Abandon / Escalation + Session Outcome are a SEPARATE tag system**
from the `Quality_Score`/`AIE_Request_Category` (Quality-by-Intent) pair — driven
by the platform-provisioned `std_Deflection_Score_<agent>_V1` /
`std_Abandonment_Score_<agent>_V1` tags (session-level associations), and the KPIs
read the association's own `ValueText__c` + `SourceType__c='PROMPT_TEMPLATE'`, NOT
the joined tag value. **Escalation Rate is the exception** — no tag, no end-type: it
counts sessions with an interaction step where `ssot__AiAgentInteractionStepType__c='SESSION_END'`
AND `ssot__Name__c='CLOSED_TRANSFERRED'` (the session-end reason). Full recipe in the non-SDO playbook §11.

**"Untagged Intent" is NOT a defect.** It appears on real sessions too.
Intent clustering is produced downstream by the Optimization analyzer and
needs **50+ sessions** before it generates clusters — it is not something
you seed.

## Making seeded sessions actually RENDER in the dashboards (CRITICAL)

The enum section above fixes the **session detail viewer** (bubbles,
metrics, trace). Getting a session to **appear in the Analytics and
Optimization dashboards at all** is a separate, harder problem. Hard-won
findings from a full rebrand effort (Skywave airline demo), all verified
by A/B diffing in one org where DriveMax synthetic data rendered and the
new synthetic data did not:

### Know which surface you're targeting — they have different sources
- **Agent Analytics (Tableau Next)** — Overview/Usage/Quality cards. Reads
  the STDM DMOs via a managed semantic layer. **This is what the QBrix
  synthetic data populates.** Filter: Agent Type = Service Agent.
- **Optimization → Insights / Moments / Intents** — DMO + pre-baked
  tags/moments. Also populated by synthetic data. Filter: Agent =
  `<AgentApiName>`, Date Range = 90 days.
- **Optimization → Insights + Sessions & Intents** — additionally gated by
  a matching **`ssot__Bot__dlm`** row joined on `DeveloperName` = the
  session's agent api name (Requirement 3 below). DriveMax_Suppport never
  appears here because no Bot row exists for it (not a deployed agent);
  Skywave appears because its agent IS deployed. (An earlier note here
  claimed the `NOT_SET` sentinel alone was the S&I discriminator — that was
  incomplete; the Bot__dlm join is the real gate, and the cases that looked
  like "NOT_SET decides it" all also had a resolvable agent.)

### Requirement 1 — `Participant__c` must be populated (identity)
Analytics aggregates sessions by participant identity. If the participant
rows have an empty `Participant__c`, the session is **silently dropped from
Analytics** even though every other field is perfect. Match the
real-session pattern:
- AGENT participant → `Participant_Object__c = 'GenAiPlannerDefinition'`,
  `Participant__c =` the live agent's GenAiPlannerDefinition Id (query the
  latest `<AgentApiName>_v*` at runtime — it's org-specific, don't
  hardcode).
- USER participant → `Participant_Object__c = 'MessagingEndUser'`,
  `Participant__c =` a real `MessagingEndUser` Id (prefix `0PA`). Rotate
  across several so Analytics shows multiple distinct users. NOTE: anonymous
  chat users are `MessagingEndUser`, **not** `005`/User — DriveMax happened
  to use `005`/User but the real EnhancedMessaging pattern is
  `MessagingEndUser`. Either renders.

### Requirement 2 — use the literal `NOT_SET` sentinel, not empty/null
This is the subtle one that blocks rendering even after Participant__c is
fixed. DriveMax and real sessions populate several optional fields with the
**literal string `NOT_SET`** rather than leaving them blank. Seeding them
empty (or stripping `NOT_SET` to `''` when copying real data) keeps the
session out of Analytics. The three confirmed-decisive SESSION fields:
- `Individual__c`, `Session_Owner_Object__c`, `Variable__c`
Also set for full fidelity: `Previous_Session_Id__c` (and the equivalents
the real data shows as `NOT_SET` on participant/interaction rows).
- **Do NOT** set `Related_Voice_Call__c` to `NOT_SET` — it's a real lookup
  to `VoiceCall` and a string value fails insert with `Invalid id: NOT_SET`.
  Leave it null (DriveMax does too).
- `Variable__c` is `string(255)`; a real session's variable-state JSON is
  ~1500 chars and cannot be stored — so you cannot faithfully clone it.
  Use `NOT_SET` (or a <255 char value); DriveMax leaves it `NOT_SET`/empty.

### Requirement 3 — a matching `ssot__Bot__dlm` row (Optimization + Sessions only)
The Optimization **Insights** and **Sessions & Intents** surfaces join the
session to `ssot__Bot__dlm` on `ssot__DeveloperName__c` = the session's
agent api name. No matching Bot row → the session is absent from those
surfaces (Analytics doesn't need it). `ssot__Bot__dlm` is fed by the
`BotDefinition_Home` stream from real `BotDefinition` records, so a row
exists only for **deployed** agents. If your synthetic agent isn't a real
deployed agent, deploy a barebones agent with that exact api name (then
refresh `BotDefinition_Home`) or seed the Bot row directly. See
`rebrand-seeder-playbook.md` §1b for the full treatment — this is the
long-unexplained reason DriveMax_Suppport never showed in Optimization
while Skywave did.

### Diagnosing render failures — the A/B method
Install the QBrix into the SAME org so its DriveMax data (which renders)
sits beside your data (which doesn't), then diff at the DMO level via the
on-core proxy:
```
POST <instance>/services/data/v66.0/ssot/queryv2   { "sql": "SELECT ... FROM ssot__AiAgent*__dlm ..." }
```
(uses the plain CLI session token; no JWT.) Diff your synthetic rows
against BOTH DriveMax synthetic AND your own real sessions — a field only
matters if it's consistent across *everything that renders* and absent on
yours. Beware: the DMO `COUNT()` counts empty strings as present, and
`DataSourceId='Salesforce_Home'` is shared by ALL synthetic data (DriveMax
+ yours) — separate them by joining to the participant's `AiAgentApiName`.

### Expected attrition (don't chase it)
~24% of DriveMax sessions never reach the agent-joined DMO view (sessions
whose participant rows didn't stitch). 1,914 sObject sessions → ~1,456 in
Analytics. Normal for loosely-stitched bulk data; your own seeder with
clean FKs should keep ~100%.

### Safety: scope your wipe
Once the QBrix's DriveMax data coexists with yours in the same tables, an
unfiltered `DELETE FROM SDO_Analytics_*` destroys the stock demo data. Scope
every wipe to your own `Demo_Identifier__c` value.

## Add-on: Employee Agent Data
Separate brix that adds Employee-Agent dashboards. Install it **after** the Observability brix.

## Troubleshooting
- **No data in Analytics tab:** verify Foundations data kit is fully deployed and `TableauNextLimitedViewer` perm set is assigned.
- **No data in Optimization tab:** verify `AgentforceInteractionExplorer` perm set is assigned and that the SDO data streams have completed at least one Full Refresh successfully.
- **Streams stuck in "Needs Activation":** sandbox refresh — auth doesn't replicate from prod. Re-activate via Data Cloud Setup → Ingestion API → AgentOpt → Activate.
- **DMO row count not changing after a delete:** you also need to refresh the corresponding `SDO_Analytics_*_Home` data stream (Full Refresh) to push the change from the custom object into the DLO/DMO.
- **Session renders but Duration/#Interactions/Latency are "--", or both bubbles show as the agent, or the trace won't open:** this is an STDM enum-value mismatch in your seeded data, NOT a pipeline/integrity problem — see "Seeding your own synthetic sessions" above. The session reaching the UI at all means the pipeline is healthy; the values are just wrong.
- **Synthetic sessions don't appear in Analytics/Optimization at all (real ones do):** this is the rendering problem — see "Making seeded sessions actually RENDER" above. In order of likelihood: (1) empty `Participant__c` on the participant rows (blocks Analytics); (2) optional fields left empty/null instead of the literal `NOT_SET` sentinel (blocks Analytics); (3) no matching `ssot__Bot__dlm` row for the agent api name (blocks Optimization Insights + Sessions & Intents — needs a deployed agent or a seeded Bot row, Requirement 3); (4) `Quality_Score` not associated to moments (empty quality charts); (5) date-range filter on the view. Diagnose by A/B diffing against DriveMax in the same org.
- **CLI/API can't trigger a SalesforceDotCom stream refresh** (`Connector type SalesforceDotCom is not allowed to run in non-interactive mode`, or `d360_datastream_run` rejects it): SalesforceDotCom streams only run on the CRM sync schedule or from an **interactive web session**. Use Developer Console → Execute Anonymous (a browser session has the scope; sf CLI and Data Cloud API tokens do not), or Setup → Data Cloud → Data Streams → Full Refresh.

## Internal SDO support channels
- `#q-branch-sdo` — SDO/QBrix questions
- `#q-branch-demos-qbrix-installation-issues` — install-time issues
- `#help-agentforce-optimization` — product side
- `#agentforce-analytics-help` — Tableau Next analytics side
