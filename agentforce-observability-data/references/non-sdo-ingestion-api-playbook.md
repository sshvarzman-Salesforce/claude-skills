# Non-SDO org playbook — seed observability data via the Data Cloud Ingestion API

This is the **fifth data-population path** (call it **Path 5**), for orgs where
you **cannot install the `SDO_Agentforce_Observability` QBrix** (i.e. any org
that is not an SDO — trial orgs, customer sandboxes, TDX/demo orgs like
`pronto`). Instead of the QBrix's CRM-custom-objects → SalesforceDotCom-streams
→ Data-Kit machinery (Path 4), you push synthetic STDM rows **straight into the
canonical `ssot__AiAgent*__dlm` DMOs via the Data Cloud Ingestion API**.

It is **strictly simpler and more maintainable than Path 4**:
- No `SDO_Analytics_*_v2__c` custom objects, no `DataPackageKitDefinition`, no
  144 `dataSrcDataModelFieldMap` metadata files.
- **Fully headless refresh** — the Ingestion API is pure REST (JWT→CDP token).
  Contrast Path 4's SalesforceDotCom streams, which reject every non-interactive
  caller and forced the Skywave rig into a Playwright browser clicking "Refresh
  Now" in CI. Path 5 needs no browser, ever.
- Data lands in the **same canonical DMOs** the dashboards read, tagged with a
  distinct `ssot__DataSourceId__c` so it's cleanly separable from real (Path 1)
  and any other synthetic data.

> **A runnable, dependency-free reference implementation ships in this skill:
> [`../reference-impl/`](../reference-impl/)** — `dc_client.py` (auth + ingest + query +
> `read_semantic_model`), `stdm_schema.py` (the 11 objects + full field map), and
> `seed_reference.py` (generator + `setup`/`push`/`verify`/`teardown` CLI). Edit
> `AGENT_API_NAME` + `ARCHETYPES` and run it. Proven end-to-end (Skywave/pronto).
> This doc is the theory + the exact contracts + every gotcha so you can rebuild
> it in any org without re-deriving anything.

---

## 0. Decide FAST whether you even need to build

Before building anything, query what's already there. Non-SDO demo orgs sometimes
already have synthetic observability data from a prior effort — possibly stale.

```bash
# 1. Are the STDM DMOs provisioned + is there data, and from which source?
sf api request rest "/services/data/v66.0/ssot/queryv2" --target-org <ORG> --method POST \
  --body '{"sql":"SELECT ssot__DataSourceId__c src, COUNT(*) c FROM ssot__AiAgentSession__dlm GROUP BY ssot__DataSourceId__c"}'
```

Provenance decoder (`ssot__DataSourceId__c`):
| Value | Origin | Meaning |
|---|---|---|
| `AIPlatform_AGENT_SESSION_TRACING` | live runtime (Path 1) | **real** conversations |
| `UploadedFiles` | Data Cloud manual file-upload connector | synthetic, loaded via the DC UI (NOT the QBrix) |
| `Salesforce_Home` | QBrix SalesforceDotCom streams (Path 4) | QBrix synthetic |
| `Pronto_Obs_*` / your own | **this playbook (Path 5)** | your Ingestion-API synthetic |
| *(blank)* | AgentOpt analyzer / managed `sfm_*` DLOs | derived tags/moments |

```bash
# 2. If synthetic data exists, is it STALE / mis-dated? (the usual failure)
sf api request rest "/services/data/v66.0/ssot/queryv2" --target-org <ORG> --method POST \
  --body '{"sql":"SELECT MIN(ssot__StartTimestamp__c), MAX(ssot__StartTimestamp__c) FROM ssot__AiAgentSession__dlm WHERE ssot__DataSourceId__c='"'"'<their synthetic src>'"'"'"}'
```
If the max date is months old, or dates are fixed-absolute (e.g. a full calendar
year 2026-01-01→2026-12-31 with much of it now outside the dashboard's
Last-N-Days window, or **future-dated**), the data has *decayed*. Absolute
timestamps do NOT roll forward. **This playbook produces TODAY-RELATIVE data**,
which is the fix.

```bash
# 3. Are the QBrix custom objects present? (if NOT, the QBrix was never installed → Path 5 is the way)
sf data query --target-org <ORG> -q \
  "SELECT QualifiedApiName FROM EntityDefinition WHERE QualifiedApiName LIKE 'SDO_Analytics%'"
```

**Decision:** non-SDO + no `SDO_Analytics_*` objects → use this playbook. If the
org already has usable synthetic data and only the DATES are wrong, you STILL
use this playbook (regenerate today-relative + push) — there is no in-place
"re-date" shortcut because the original loader is rarely available and the
`UploadedFiles`/`sfm_*` DLOs are not writable by you (see §7).

---

## 1. The pipeline in one picture

```
spec/pronto_story.py        (the demo story: topics, intents, quality bands, messages)
        │  generate.py
        ▼
observability/out/*.csv      (11 CSVs, UUID FKs, TODAY-relative timestamps)
        │  push.py  ── Data Cloud Ingestion API (JWT→CDP, /api/v1/ingest/jobs) ──┐
        ▼                                                                        │
per-object DLO  (Pronto_Obs_<Object>_<hash>__dll)                                │
        │  DLO→DMO mapping (created once by setup_source.py)                     │
        ▼                                                                        │
ssot__AiAgent*__dlm   ◄── real Path-1 data lands here too ───────────────────────┘
        │
        ▼
Agentforce Studio → Analytics + Optimization  (filter to your agent + date range)
```

One **IngestApi connection per STDM object** (the proven "one object per
connection" pattern). Eleven objects → eleven connections/streams/DLOs/mappings,
all created once by `setup_source.py`, then `push.py` re-pushes rows on every
refresh (streams are `UPSERT`).

---

## 2. Prerequisites & auth (the ONLY manual gate)

### 2.1 Connected App for JWT→CDP (one-time, ~10 min)
The Ingestion API is on the Data Cloud **edge** (`<tenant>.c360a.salesforce.com`),
which a plain sf-CLI token cannot reach. You need a JWT-bearer Connected App with
CDP scopes. See the `sf-datacloud-api-auth` skill for the full recipe; the short
version proven on pronto:

1. Generate a keypair, deploy a minimal Connected App with the cert:
   ```bash
   mkdir -p .secrets && printf '.secrets/\n' >> .gitignore
   openssl req -x509 -nodes -newkey rsa:2048 -keyout .secrets/dc.key -out .secrets/dc.crt \
     -days 730 -subj "/C=DE/O=<Org>/CN=<org>-dc-ingest"
   # .connectedApp-meta.xml with <certificate> = base64 cert (no headers/newlines),
   # <scopes>Api</scopes> + <scopes>RefreshToken</scopes>, callbackUrl http://localhost.
   sf project deploy start --target-org <ORG> --source-dir <app dir>
   ```
2. **The CDP scopes are NOT deployable** (confirmed on API v67: the `<scopes>`
   enum rejects `CdpIngestApi`/`CdpQueryApi`). This is the one manual gate —
   4 clicks in Setup → App Manager:
   - App → ▼ → **Edit** → add OAuth scopes **cdp_ingest_api** + **cdp_query_api** → Save.
   - App → ▼ → **Manage** → **Edit Policies** → Permitted Users = "Admin approved
     users are pre-authorized", IP Relaxation = "Relax IP restrictions" → Save.
   - Manage → **Profiles** → add **System Administrator** → Save.
   - Setup → **OAuth and OpenID Connect Settings** → "Allow Authorization Code and
     Credentials Flows" = ON (usually already on).
3. Retrieve the consumer key (`sf project retrieve start --metadata "ConnectedApp:<ApiName>"`
   → the `<consumerKey>` appears on retrieve; it is NOT deployable/queryable).
   Store creds in `.secrets/dc.env` (gitignored):
   ```
   export DC_CONSUMER_KEY='...'
   export DC_USERNAME='<admin username>'
   export DC_LOGIN_URL='https://login.salesforce.com'
   export DC_KEY_FILE="$(dirname ${BASH_SOURCE[0]})/dc.key"
   ```
4. Verify the chain works before anything else:
   ```bash
   ./observability/scripts/test-auth.sh   # prints the *.c360a.salesforce.com host + a token + a 200
   ```

The JWT→CDP chain (both scripts already do this): JWT-bearer POST
`/services/oauth2/token` → core token + core instance_url; then POST
`<core>/services/a360/token` grant `urn:salesforce:grant-type:external:cdp` →
CDP token + the `*.c360a.salesforce.com` host. DC token TTL ~8h.

### 2.2 STDM must be provisioned + the agent must be deployed
- **Session Tracing / STDM DMOs** must exist (Setup → Einstein Audit, Analytics,
  and Monitoring → Agentforce Session Tracing ON). Step 0's query proves this —
  if `ssot__AiAgentSession__dlm` errors "Invalid type", provision it first (see
  the onboarding checklist).
- **The Bot join gate** (Optimization Insights + Sessions & Intents): a matching
  **`ssot__Bot__dlm`** row must exist for your agent's api name (joined on
  `ssot__DeveloperName__c`). That DMO is fed from real `BotDefinition` records via
  the `BotDefinition_Home` stream, so it exists only for a **deployed + activated**
  agent. Verify:
  ```bash
  sf data query --target-org <ORG> -q "SELECT ssot__DeveloperName__c, ssot__Label__c FROM ssot__Bot__dlm"
  ```
  If your target agent isn't listed, deploy + **activate** a barebones agent with
  that exact api name, then refresh `BotDefinition_Home` (see
  `rebrand-seeder-playbook.md` §1b). On pronto the agent
  `Merchant_Shopper_Agent_Observability_2` was already deployed+active, so this
  was free — always check first.

---

## 3. The Ingestion API contract (verbatim — the #1 time-sink if wrong)

Implemented in `~/dev/pronto/observability/scripts/dc_client.py`. Two hosts —
mixing them up is the top 404 cause:

- **Core proxy** `https://<instance>.my.salesforce.com/services/data/v62.0/ssot/...`
  (Core token) — connection, schema, data-stream, mapping CRUD.
- **CDP edge** `https://<tenant>.c360a.salesforce.com/api/v1|v2/...`
  (CDP token) — ingest jobs + query. `ssot/*` on the CDP tenant **404s**.

Use API version **v62.0** for the `/ssot/*` calls (what the reference scripts ship).

### Step A — create the connection (= the "source")
```
POST <core>/services/data/v62.0/ssot/connections?connectorType=IngestApi
{"connectorType":"IngestApi","label":"<Name>","name":"<Name>"}
```
Returns a **hash-suffixed** `name` (e.g. `<Name>_f4aef2c1_...`) + an `id`.
🔑 **The name you SUBMITTED** (`<Name>`) is the `sourceName` used later for ingest
jobs. **The RETURNED hash-suffixed name** is `connectorDetails.name` in the stream
POST. **Do not swap them** — the returned hashed name 404s forever as `sourceName`.
Idempotent: GET `?connectorType=IngestApi`, match on `label`.

### Step B — PUT the object schema (declares the DLO's fields)
```
PUT <core>/.../ssot/connections/{id}/schema
{"schemas":[{"label":"<Object>","name":"<Object>","schemaType":"IngestApi",
  "fields":[{"name":"<f>","label":"<f>","dataType":"Text|Number|Date|DateTime"}]}]}
```
`schemaType` literal **`"IngestApi"`** (NOT `StreamingApp`, NOT `INGESTAPI`).
PK is NOT declared here. One object per connection.

### Step C — create the data stream (materializes the DLO)
```
POST <core>/.../ssot/data-streams
{"name":"<StreamBase>","datastreamType":"INGESTAPI",
 "connectorInfo":{"connectorType":"IngestApi",
   "connectorDetails":{"name":"<RETURNED conn name>","events":["<Object>"]}},
 "dataLakeObjectInfo":{"label":"<StreamBase>","category":"<Profile|Engagement|Related>",
   "dataspaceInfo":[{"name":"default"}],
   "dataLakeFieldInputRepresentations":[{"name":"<pk>","label":"<pk>","dataType":"Text","isPrimaryKey":true}]
   /* Engagement ONLY: add "eventDateTimeFieldName":"<a DateTime field>" */ },
 "refreshConfig":{"refreshMode":"UPSERT"}}
```
- `datastreamType` UPPERCASE `INGESTAPI`; nested `connectorType` camelCase
  `IngestApi` (they intentionally differ).
- `connectorDetails.events` **REQUIRED** (missing → INTERNAL_ERROR).
- Supply **ONLY the PK** in `dataLakeFieldInputRepresentations` (listing all
  fields → "Illegal argument"; the DLO auto-expands to the schema fields).
- The resulting stream/DLO name is auto-suffixed `<StreamBase>_<event>_<hash>` —
  GET `/ssot/data-streams?limit=200` + match to find the real DLO name.

### Step D — map the DLO → canonical DMO
```
POST <core>/.../ssot/data-model-object-mappings?dataspace=default
{"sourceEntityDeveloperName":"<DLO>__dll","targetEntityDeveloperName":"ssot__AiAgentX__dlm",
 "fieldMapping":[{"sourceFieldDeveloperName":"id__c","targetFieldDeveloperName":"ssot__Id__c"}]}
```
- **DLO field names carry `__c`** (source side); target DMO fields are their real
  api names. The DLO's materialized PK MUST appear in `fieldMapping` (else 400
  "Unable to find Primary Key of DLO").
- Re-POST the same pair → `DUPLICATE_DLO_TO_DMO_MAPPING` (safe, ignore).
- Multiple sources may map to one DMO — that's exactly how synthetic coexists
  with real in the same DMO.

### Step E — push rows (CDP edge)
```
POST  <cdp>/api/v1/ingest/jobs   {"object":"<Object>","sourceName":"<SUBMITTED name>","operation":"upsert"}  → job id
PUT   <cdp>/api/v1/ingest/jobs/{id}/batches   Content-Type: text/csv   <raw CSV, header row = field names>   → 202
PATCH <cdp>/api/v1/ingest/jobs/{id}   {"state":"UploadComplete"}
```
Retry only **404** (connection propagation, ~30-90s) and **409** (a job already
open). **Rows land async** (1-4 min for ~13K rows on pronto). **Gate on the DMO
row count, NOT the job state** — the job stays `InProgress` well after rows are
queryable.

Verify rows: `POST <cdp>/api/v2/query {"sql":"SELECT COUNT(*) FROM <DLO>__dll"}`
and the same against `ssot__AiAgentX__dlm WHERE ssot__DataSourceId__c LIKE '<prefix>%'`.

---

## 4. The 11 STDM objects — categories, PKs, and DLO→DMO field maps

This is the table that cost the most time to get right. **Each DLO's `category`
MUST equal its target DMO's category** or the mapping 400s: *"Cannot map DLO type
X to DMO type Y."* Categories verified live from pronto's DMO metadata
(`GET /ssot/metadata?entityType=DataModelObject&entityName=<dmo>` → `.metadata[0].category`):

| STDM object | DMO | **Category** | PK | Engagement event-time field |
|---|---|---|---|---|
| AiAgentSession | ssot__AiAgentSession__dlm | **Profile** | Id | — |
| AiAgentSessionParticipant | ssot__AiAgentSessionParticipant__dlm | **Engagement** | Id | StartTimestamp |
| AiAgentInteraction | ssot__AiAgentInteraction__dlm | **Engagement** | Id | StartTimestamp |
| AiAgentInteractionMessage | ssot__AiAgentInteractionMessage__dlm | **Engagement** | Id | MessageSentTimestamp |
| AiAgentInteractionStep | ssot__AiAgentInteractionStep__dlm | **Profile** | id | — |
| AiAgentMoment | ssot__AiAgentMoment__dlm | **Engagement** | Id | StartTimestamp |
| AiAgentMomentInteraction | ssot__AiAgentMomentInteraction__dlm | **Engagement** | Id | StartTimestamp |
| AiAgentTagDefinition | ssot__AiAgentTagDefinition__dlm | **Related** | Id | — |
| AiAgentTagDefinitionAssociation | ssot__AiAgentTagDefinitionAssociation__dlm | **Related** | Id | — |
| AiAgentTag | ssot__AiAgentTag__dlm | **Related** | Id | — |
| AiAgentTagAssociation | ssot__AiAgentTagAssociation__dlm | **Engagement** | Id | CreatedDate |

- **Engagement** DLOs additionally REQUIRE `eventDateTimeFieldName` (a DateTime
  field). Profile/Related must OMIT it.
- These categories are consistent across STDM orgs (they're baked into the
  canonical DMOs). Still, re-verify with the metadata call in a new org — a
  wrong category is a silent, misleading 400.

**The complete field-by-field DLO→DMO map** (source IngestApi field → DMO field). Every
object also carries `Id → ssot__Id__c` and `ExternalSourceId → ssot__ExternalSourceId__c`
(the latter is the Analytics gate — §5). Field api names are stable across STDM orgs but
**verify live** in a new org before trusting them (`GET
/ssot/metadata?entityType=DataModelObject&entityName=<dmo>` → `.metadata[0].fields[].name`):

```
AiAgentSession (Profile):          AiAgentChannelType→ssot__AiAgentChannelType__c,
  AiAgentSessionEndType→ssot__AiAgentSessionEndType__c, StartTimestamp→ssot__StartTimestamp__c,
  EndTimestamp→ssot__EndTimestamp__c, IndividualId→ssot__IndividualId__c,
  PreviousSessionId→ssot__PreviousSessionId__c, SessionOwnerObject→ssot__SessionOwnerObject__c,
  VariableText→ssot__VariableText__c
AiAgentSessionParticipant (Engagement, evt=StartTimestamp): AiAgentSessionId→ssot__AiAgentSessionId__c,
  AiAgentApiName→ssot__AiAgentApiName__c, AiAgentVersionApiName→ssot__AiAgentVersionApiName__c,
  AiAgentTemplateApiName→ssot__AiAgentTemplateApiName__c, AiAgentType→ssot__AiAgentType__c,
  AiAgentSessionParticipantRole→ssot__AiAgentSessionParticipantRole__c, ParticipantId→ssot__ParticipantId__c,
  ParticipantObject→ssot__ParticipantObject__c, ParticipantAttributes→ssot__ParticipantAttributeText__c,
  StartTimestamp→ssot__StartTimestamp__c, EndTimestamp→ssot__EndTimestamp__c
AiAgentInteraction (Engagement, evt=StartTimestamp): AiAgentSessionId→ssot__AiAgentSessionId__c,
  TopicApiName→ssot__TopicApiName__c, AiAgentInteractionType→ssot__AiAgentInteractionType__c,
  SessionOwnerId→ssot__SessionOwnerId__c, SessionOwnerObject→ssot__SessionOwnerObject__c,
  StartTimestamp→ssot__StartTimestamp__c, EndTimestamp→ssot__EndTimestamp__c,
  TraceId→ssot__TelemetryTraceId__c, SpanId→ssot__TelemetryTraceSpanId__c
AiAgentInteractionMessage (Engagement, evt=MessageSentTimestamp): AiAgentSessionId→ssot__AiAgentSessionId__c,
  AiAgentInteractionId→ssot__AiAgentInteractionId__c, AiAgentSessionParticipantId→ssot__AiAgentSessionParticipantId__c,
  AiAgentInteractionMessageType→ssot__AiAgentInteractionMessageType__c,
  AiAgentInteractionMsgContentType→ssot__AiAgentInteractionMsgContentType__c,
  ContentText→ssot__ContentText__c, MessageSentTimestamp→ssot__MessageSentTimestamp__c
AiAgentInteractionStep (Profile): aiAgentInteractionId→ssot__AiAgentInteractionId__c,
  AiAgentInteractionStepType→ssot__AiAgentInteractionStepType__c, name→ssot__Name__c,
  inputValueText→ssot__InputValueText__c, outputValueText→ssot__OutputValueText__c,
  startTimestamp→ssot__StartTimestamp__c, endTimestamp→ssot__EndTimestamp__c,
  prevStepId→ssot__PrevStepId__c, errorMessageText→ssot__ErrorMessageText__c,
  attributeText→ssot__AttributeText__c
AiAgentMoment (Engagement, evt=StartTimestamp): AiAgentSessionId→ssot__AiAgentSessionId__c,
  AiAgentApiName→ssot__AiAgentApiName__c, AiAgentVersionApiName→ssot__AiAgentVersionApiName__c,
  RequestSummaryText→ssot__RequestSummaryText__c, ResponseSummaryText→ssot__ResponseSummaryText__c,
  StartTimestamp→ssot__StartTimestamp__c, EndTimestamp→ssot__EndTimestamp__c
AiAgentMomentInteraction (Engagement, evt=StartTimestamp): AiAgentMomentId→ssot__AiAgentMomentId__c,
  AiAgentInteractionId→ssot__AiAgentInteractionId__c, StartTimestamp→ssot__StartTimestamp__c
AiAgentTagDefinition (Related): Name→ssot__Name__c, DeveloperName→ssot__DeveloperName__c,
  DataType→ssot__DataType__c, SourceType→ssot__SourceType__c, Status→ssot__Status__c,
  Description→ssot__Description__c, CreatedDate→ssot__CreatedDate__c
AiAgentTagDefinitionAssociation (Related): AiAgentApiName→ssot__AiAgentApiName__c,
  AiAgentTagDefinitionId→ssot__AiAgentTagDefinitionId__c, CreatedDate→ssot__CreatedDate__c
AiAgentTag (Related): AiAgentTagDefinitionId→ssot__AiAgentTagDefinitionId__c,
  Value→ssot__Value__c, Description→ssot__Description__c, CreatedDate→ssot__CreatedDate__c
AiAgentTagAssociation (Engagement, evt=CreatedDate): AiAgentSessionId→ssot__AiAgentSessionId__c,
  AiAgentMomentId→ssot__AiAgentMomentId__c, AiAgentTagId→ssot__AiAgentTagId__c,
  AiAgentTagDefinitionAssociationId→ssot__AiAgentTagDefinitionAssociationId__c,
  AssociationReasonText→ssot__AssociationReasonText__c, ValueText→ValueText__c,
  SourceType→SourceType__c, AiAgentSessionStartTimestamp→AiAgentSessionStartTimestamp__c,
  CreatedDate→ssot__CreatedDate__c
```
Note: on `AiAgentTagAssociation`, `ValueText`/`SourceType`/`AiAgentSessionStartTimestamp`
map to targets **without** the `ssot__` prefix (they're extension fields — see §11). The
inconsistent source-field casing (`aiAgentInteractionId`, `name`, `inputValueText` on the
Step object) mirrors the real ingest schema — keep it. Corrections that bit us (inferred
names that were WRONG — the reason "verify live" matters):

| Object | I guessed | Correct DMO field |
|---|---|---|
| Interaction | `ssot__TraceId__c` / `ssot__SpandId__c` | **`ssot__TelemetryTraceId__c`** / **`ssot__TelemetryTraceSpanId__c`** |
| SessionParticipant | `ssot__ParticipantAttributes__c` | **`ssot__ParticipantAttributeText__c`** |
| InteractionStep | `ssot__PreviousStepId__c`, `ssot__AgentId__c` | **`ssot__PrevStepId__c`**; **no AgentId field exists** — drop it (map `attributeText`→`ssot__AttributeText__c` instead) |

**Boolean-typed DMO fields reject a Text IngestApi field** → mapping 400s
*"type Text is different from ... Boolean"*. On pronto `ssot__IsActive__c`
(Tag, TagDefinitionAssociation) is Boolean. Easiest fix: **omit the boolean
field from the mapping** (IsActive/IsFallback/IsPassed aren't needed to render).
If you truly need a boolean, declare the IngestApi field as `Number` (0/1) — but
omitting is simpler and proven.

---

## 5. The synthetic row shape — enums & identities that must be exact

Verified against pronto's live rendering data. A wrong enum renders the session
but breaks specific UI fields (see `sdo-qbrix.md` for the symptom table). The
generator (`generate.py`) already emits all of this correctly:

| Field | Correct value(s) |
|---|---|
| message type (`AiAgentInteractionMessageType`) | `Input` / `Output` |
| message content type | `text/plain` |
| interaction type (`AiAgentInteractionType`) | `TURN` (+ exactly one `SESSION_END` per session) |
| step type (`AiAgentInteractionStepType`) | `TOPIC_STEP` / `LLM_STEP` / `ACTION_STEP` (+ `SESSION_END`) |
| participant role | `AGENT` / `USER` |
| participant type (`AiAgentType`) | `EinsteinServiceAgent` |
| channel (`AiAgentChannelType`) | e.g. `Whatsapp` (whatever the demo channel is) |
| session end type | `resolved` / `escalated` (blank also renders; escalation is often modeled as a topic) |

**Identities (org-specific — resolve at runtime). 🚨 THIS IS THE #1 "data is in
the DMOs but the agent isn't in the dashboard dropdown" bug — get it EXACTLY right:**
- **AGENT participant `ParticipantId`** = the agent's **GenAiPlannerDefinition Id**,
  and **`ParticipantObject` = `GenAiPlannerDefinition`** (NOT the BotDefinition
  Id, NOT an empty ParticipantObject). The Analytics/Optimization **agent picker
  resolves agents by this planner identity** — a BotDefinition Id (`0Xx...`) with
  an empty ParticipantObject makes the session land in the raw DMO and even render
  a Sessions & Intents detail, **but the agent NEVER appears in the Agent dropdown**,
  so nothing shows. Verified by A/B diff on pronto: the real agent that DOES
  appear uses `ParticipantObject='GenAiPlannerDefinition'` + a planner id; the
  synthetic set that did NOT appear used a Bot id + empty object.
  - Use the **15-char** form of the planner id (the real rendering rows are
    15-char; an 18-char id also works but match live data to be safe).
  - Query: `SELECT Id, DeveloperName FROM GenAiPlannerDefinition WHERE DeveloperName LIKE '<agent api name>%'`
    → truncate the 18-char Id to 15. (On pronto: `16jWs000000jLDBIA2` → `16jWs000000jLDB`.)
  - ⚠️ **Do NOT trust a pre-existing synthetic set as the pattern to copy** — the
    stale `UploadedFiles` data on pronto used a Bot id + empty object and had
    NEVER rendered in the dropdown either. Always A/B against a REAL agent's
    participant rows (`ssot__DataSourceId__c='AIPlatform_AGENT_SESSION_TRACING'`)
    that you can SEE in the dropdown, not against other synthetic data.
- **USER participant `ParticipantId`** = rotate across real active `005` User Ids
  (`SELECT Id FROM User WHERE IsActive=true LIMIT 25`), **`ParticipantObject` =
  `User`** (again NOT empty — the real rendering rows use `User`). (Anonymous chat
  users are `MessagingEndUser` `0PA...` in genuine EnhancedMessaging data, but
  `005`/`User` is what pronto's rendering data uses and it works.)
- Participant `AiAgentTemplateApiName` = `SvcCopilotTmpl__EinsteinServiceAgent`
  (Skywave leaves this empty on the AGENT row; both render — non-blocking).
- All `AiAgentApiName` / `AiAgentVersionApiName` = the agent's api name (the same
  string that must exist in `ssot__Bot__dlm`).
- 🚨 **`ssot__ExternalSourceId__c` = the org's 18-char Id, on EVERY row of EVERY
  object.** This is the **Analytics-tab render gate** (separate from the
  Optimization gates above). The Tableau-Next Analytics semantic layer scopes/
  joins records by ExternalSourceId; leave it NULL and the agent shows in
  **Optimization / Sessions & Intents but NEVER in the Analytics tab** (Analytics
  reads the materialized layer, Optimization reads the DMOs live). Verified on
  pronto: every row that renders in Analytics — both real AIPlatform data AND
  Skywave synthetic — carries `ssot__ExternalSourceId__c` = the org id; the
  synthetic rows that were absent from Analytics had it NULL. Set it to
  `sf org display --json → result.id` (18-char) on all 11 objects (schema field +
  DLO→DMO map → `ssot__ExternalSourceId__c`). After fixing, allow the Analytics
  semantic layer to re-materialize (own cadence — can lag hours; not instant).
  **CONFIRMED on pronto: this + the app-version update made the synthetic agent
  render in the Analytics tab (it already rendered in Optimization).**

> **The A/B diff query that finds this class of bug** (run it whenever data is in
> the DMOs but the dashboard shows nothing / the agent isn't in the picker):
> ```
> -- shape of an agent that DOES render (a real one you can see in the dropdown):
> SELECT ssot__ParticipantId__c, ssot__ParticipantObject__c, ssot__AiAgentType__c
> FROM ssot__AiAgentSessionParticipant__dlm
> WHERE ssot__AiAgentApiName__c='<a REAL agent>' AND ssot__AiAgentSessionParticipantRole__c='AGENT' GROUP BY 1,2,3
> -- vs YOUR synthetic agent — every field must match the real shape:
> SELECT ssot__ParticipantId__c, ssot__ParticipantObject__c, ssot__AiAgentType__c
> FROM ssot__AiAgentSessionParticipant__dlm
> WHERE ssot__AiAgentApiName__c='<your agent>' AND ssot__AiAgentSessionParticipantRole__c='AGENT' GROUP BY 1,2,3
> ```
> Extend the same diff to `ssot__ExternalSourceId__c` on the SESSION object — it
> must equal the org id on rendering rows, and NULL-on-yours is the Analytics-tab
> blocker. The BEST reference is a REAL agent in the SAME org that you can see in
> Analytics (e.g. pronto's `Pronto_Customer_Service_Assistant`), not another org's
> synthetic data.

**Timestamps:** Ingestion-API DateTime fields want **ISO-8601 UTC**
(`2026-07-15T09:00:00.000Z`). (This differs from the legacy `UploadedFiles` DLOs
that stored `YYYY-MM-DD HH:MM:SS.000 UTC` — a DateTime IngestApi field parses
ISO-8601.) Write **TODAY-RELATIVE** dates: spread `daysBack` over 1..N (N = the
dashboard window you demo, e.g. 180), never day 0 (an afternoon time today can
land in the future vs an early-morning org clock). This is the whole point —
absolute dates decay; today-relative dates always fall in-window.

**Referential integrity:** every cross-object link is a **text-UUID FK**
(`AiAgentSessionId`, `AiAgentInteractionId`, `AiAgentMomentId`, `AiAgentTagId`,
`AiAgentTagDefinitionAssociationId`, …). No Salesforce Ids as FKs → the graph
resolves in any org, no Id remapping. The generator asserts 0 dangling FKs.

**Render gates (all must hold):**
1. **AGENT participant = planner-id identity** — `ParticipantId` = the
   GenAiPlannerDefinition Id AND `ParticipantObject='GenAiPlannerDefinition'`;
   USER participant = a `005` Id AND `ParticipantObject='User'`. A populated
   `ParticipantId` alone is NOT enough — the OBJECT type + the right kind of id
   are what put the agent in the dashboard's Agent dropdown (see §5). This is the
   most common "data present, dashboard empty" cause.
2. Optional session fields carry the literal `NOT_SET` sentinel (Individual,
   PreviousSessionId, SessionOwnerObject, Variable) — NOT empty/null. (Do NOT set
   `RelatedVoiceCall` to `NOT_SET` — it's a real lookup; leave null.)
3. A matching `ssot__Bot__dlm` row for the agent api name (Optimization/Sessions).
4. A `Quality_Score` (1-5) tag associated to every moment (all quality charts).
5. **`ssot__ExternalSourceId__c` = the org id on every row (the ANALYTICS-tab
   gate).** Without it, Optimization/Sessions render but the Analytics tab never
   shows the agent. See §5.
6. **The Agent Analytics app must be current** (an old version renders a thin/
   different dashboard and lags the agent dropdown) — Setup → Agent Analytics →
   update; see §8. (Org action, not data.)

---

## 6. The quality story (what makes it a DEMO, not just data)

The Optimization analyzer NEVER scores synthetic data, so **every quality signal
is pre-baked**. Two tag definitions (matching what DriveMax ships):
- `AIE_Request_Category_<AgentApiName>` (Source_Type `Generated`) — the **Intent**
  dimension.
- `Quality_Score` (Source_Type `Predefined`, Integer) — 5 reusable tags valued
  1..5, ONE associated per moment. Drives Average Quality Score / Quality-by-
  Subagent / Quality-by-Intent (5≈High … 1≈Very Low).

**The moment is the unit of the dashboard.** Each moment = one row in Sessions &
Intents and one data point in Quality-by-Intent. It carries a request/response
summary, a MomentInteraction junction (whose interactions' `TopicApiName` is the
**subagent**), and exactly two tag associations (intent + score).

Design the story with **weighted archetypes** `(topic, intent-bucket,
[minScore,maxScore], weight)`. Put the failing capability where it surfaces under
**Quality-by-Intent**, and let the subagent it rolls up under read Medium (so the
presenter drills subagent → intent to find the culprit). See
`rebrand-seeder-playbook.md` §3 for the archetype method and
`~/dev/pronto/observability/spec/pronto_story.py` for a complete worked example
(food-delivery: transactional intents score 4.2-4.5, self-service-enablement
intents bottom out at ~1.5).

**Conversation timing** (two independent intervals — get this right or latency
metrics/transcripts look robotic):
- Agent latency = interaction Start→End = **2-4s** (this is what the dashboard
  reports as Average Agent Latency).
- User think/away gap = BETWEEN interactions, right-skewed: ~70% 15-75s, ~30%
  90-300s. Does not affect the latency metric.

---

## 7. Coexisting with pre-existing / stale data; teardown

- Your data is tagged with a distinct `ssot__DataSourceId__c` per object
  (`Pronto_Obs_<Object>_<hash>` — each object gets its own because each needs its
  own IngestApi connection). To find/verify/wipe YOUR data, match the **prefix**
  (`LIKE 'Pronto_Obs%'`), not one literal value.
- **You cannot write to a `UploadedFiles` or `Salesforce_Home` or `sfm_*` DLO**
  — those are system/other-connector-managed (`POST /api/v1/ingest/jobs` →
  `404 NOT_FOUND` by design). That's why a prior effort's synthetic data can't be
  "re-dated in place"; you stand up your OWN source and (optionally) retire theirs.
- **Retiring stale synthetic data** (e.g. old `UploadedFiles` sessions polluting
  aggregates): delete the stale streams' **DLO→DMO mappings FIRST**, then the
  streams (`DELETE /ssot/data-streams/{name}?shouldDeleteDataLakeObject=true`),
  then the connections. Removing a DLO's mapping + the DLO drops those rows from
  the canonical DMO, leaving real + yours. If you skip the mapping delete, the
  stream delete 412s `CANNOT_DELETE_ENTITY`. (Or just leave it and filter to your
  agent + date range in the demo — the fresh data renders correctly regardless.)
- **Teardown of your own source** (`teardown_source.py`): mappings → streams →
  connections, same order. Stream deletes are async — retry connection deletes
  after a pause (they 400 `DEPENDENCY_EXISTS` until the stream is gone).

---

## 8. Gotcha ledger (everything that cost time on pronto — pre-solved here)

| Symptom | Cause | Fix |
|---|---|---|
| **data is in the DMOs but the agent is NOT in the dashboard's Agent dropdown / nothing renders** | AGENT participant used a BotDefinition Id (`0Xx...`) + empty `ParticipantObject` | Use the **GenAiPlannerDefinition Id** + `ParticipantObject='GenAiPlannerDefinition'` (15-char id); USER = `005` id + `ParticipantObject='User'`. A/B-diff against a REAL agent that DOES show — never copy a pre-existing synthetic set (it may never have rendered either). §5. |
| `Cannot map DLO type: Engagement, to DMO type: Engagement` | DLO created with wrong `category` (e.g. `Other`) vs the DMO's real category | Create each DLO with the DMO's exact category (§4 table). |
| stream create `400 INTERNAL_ERROR ... Please try again` (persistent, on long object names) | auto stream name `<base>_<event>_<hash>` overflows the platform's name limit | Use a SHORT stream base for long objects (e.g. `Pronto_Obs_TagDefAssoc`); the connection name (= sourceName) stays full. |
| mapping `400 ... type Text is different from ... Boolean` | IngestApi field is Text, DMO field is Boolean | Omit the boolean field from the mapping (or declare it Number 0/1). |
| a stream/DLO resolves to the WRONG object's DLO | prefix collision: `find_stream_dlo("...AiAgentTag")` matched `...AiAgentTagDefinition` | Match `name == base or name.startswith(base + "_")` (boundary-aware). |
| `sourceName` ingest job `404` forever | used the connection's RETURNED hash-suffixed name as `sourceName` | Use the SUBMITTED name for `sourceName`; the returned name only for `connectorDetails.name`. |
| DMO shows 0 rows right after push | ingestion is async | Wait 1-4 min; gate on DMO count, not job state (stays `InProgress`). Participant/step landed last on pronto. |
| stream DELETE `412 CANNOT_DELETE_ENTITY` | the DLO is still mapped to a DMO | DELETE the DLO→DMO mapping first, then the stream. |
| connection DELETE `400 DEPENDENCY_EXISTS` | stream delete is async, not finished | Wait, re-run the teardown (deletes what remains). |
| `ssot/*` on the CDP tenant → `404` / `INVALID_AUTH_HEADER` on the core proxy with a raw token | wrong host, or raw curl vs the on-core proxy | `/ssot/*` = core host; `/api/v1|v2/*` = c360a host. For read-only ad-hoc, `sf api request rest "/services/data/v66.0/ssot/queryv2" ...` auto-auths the on-core proxy (no JWT). |
| CDP scopes won't deploy in the Connected App | `<scopes>` enum rejects `CdpIngestApi`/`CdpQueryApi` (v66/v67) | Add them in Setup → App Manager → Edit (the one manual gate, §2.1). |
| Python urllib `CERTIFICATE_VERIFY_FAILED` (macOS Python.framework) | no CA bundle | `dc_client.py` prefers `certifi`, else falls back to an unverified context (TLS to *.salesforce.com only). |
| session-detail bubbles both show as agent / duration "--" / trace won't open | STDM enum mismatch in seeded data | Use the exact enums in §5 (message Input/Output, interaction TURN, steps TOPIC/LLM/ACTION). |
| data shows in **Optimization / Sessions & Intents** but NOT in the **Analytics** tab (agent absent from the Analytics Agent dropdown) | **`ssot__ExternalSourceId__c` is NULL on your synthetic rows.** Analytics (Tableau Next materialized semantic layer) scopes/joins by ExternalSourceId; Optimization (live DMO read) doesn't. Every row that renders in Analytics (real AND Skywave synthetic) has ExternalSourceId = the org id. | Set `ExternalSourceId` = the 18-char org id (`sf org display --json`) on EVERY row of EVERY object; map it → `ssot__ExternalSourceId__c` (all 11). Rebuild + re-push, then wait for the semantic layer to re-materialize. §5. |
| the Analytics dashboard looks thin/old vs a known-good org (only Effectiveness; no Quality/Health/Trust/Voice sub-tabs; "Performance Overview" not "Agent Performance") | **OLD Agent Analytics app version.** It's a versioned platform app; an old build renders a different/thinner dashboard and can lag the agent dropdown. (pronto was **v2.8**; latest **5.2**.) | Setup → Agent Analytics → **UPDATE the app** (2.8→5.2 gave the rich dashboard). Org action, not data. Ensure `TableauNextLimitedViewer` assigned + profile API Enabled. |

---

## 9. Run sequence (copy-paste)

```bash
cd <repo>                                   # e.g. ~/dev/pronto
# 0. one-time: Connected App + scopes (§2.1), then:
./observability/scripts/test-auth.sh        # must print the c360a host + a 200
python3 observability/scripts/setup_source.py   # idempotent: 11 sources+streams+mappings

# generate + load (repeat this pair anytime to refresh — today-relative)
USERS=$(sf data query --target-org <ORG> -q "SELECT Id FROM User WHERE IsActive=true LIMIT 25" --json | jq -r '[.result.records[].Id]|join(",")')
python3 observability/scripts/generate.py --sessions 500 --days 180 --user-ids "$USERS"
python3 observability/scripts/push.py
sleep 180
python3 observability/scripts/verify.py     # counts, date window, quality story, Bot gate
# then: Agentforce Studio → Optimization/Analytics → filter agent + Last N Days
```

**Refresh = re-run `generate.py` + `push.py`** (streams are UPSERT; same PKs
overwrite). Pure API, no browser — schedule it in cron/CI if you want it
always-fresh. There is deliberately no dependency on a running agent, the
analyzer, or any UI step after the one-time §2.1 gate.

---

## 10. Files to copy (the reference implementation)

From `~/dev/pronto/observability/` (all portable — only identities/story are
org-specific, and those live in the two `spec/` files):

| File | Role |
|---|---|
| `scripts/dc_client.py` | DC client: JWT→CDP + Ingestion API CRUD + ingest lifecycle. Org-agnostic. |
| `scripts/jwt_signer.py` | RS256 signer for `test-auth.sh`. |
| `scripts/test-auth.sh` | Verify the token chain. |
| `scripts/setup_source.py` | Idempotent source/stream/mapping stand-up. Reads `spec/stdm_schema.py`. |
| `scripts/generate.py` | Emit the STDM CSVs (today-relative). Reads `spec/pronto_story.py`. |
| `scripts/push.py` | Push CSVs via ingest jobs. |
| `scripts/verify.py` | DMO-level verification. |
| `scripts/teardown_source.py` | Remove the source (mappings→streams→connections). |
| `spec/stdm_schema.py` | **The 11 objects' schema + categories + DLO→DMO field maps.** Portable (verify target field names in a new org). |
| `spec/pronto_story.py` | **The demo story.** Rewrite per industry/agent (topics, intents, quality bands, message samples, identities). |

To retheme for a new org/industry: copy the tree, rewrite `spec/pronto_story.py`
(story + `AGENT_API_NAME` + `AGENT_BOT_ID` + channel), re-point `.secrets/dc.env`,
re-verify target field names in `spec/stdm_schema.py`, run §9.

---

## 11. The Analytics rate KPIs — exact formulas (Deflection / Abandon / Escalation / Engagement / Success + Session Outcome)

> Verified on `si` (Skywave), 2026-08. This whole section was a **documentation gap** —
> the older refs only cover the `AIE_Request_Category` + `Quality_Score` (Quality-by-
> Intent) pair. The rate KPIs are a *separate* mechanism, and getting them off 0 for
> synthetic data has non-obvious requirements.

### 11.0 What each rate counts (verbatim from the semantic model)

**These formulas were pulled straight from the org's SDM** (see
[`reading-the-semantic-model.md`](reading-the-semantic-model.md) — `GET
/ssot/semantic/models/{apiName}`). They are the ground truth; seed to them. Two are
**tag-driven** (Deflection/Abandon) and two are **structural** (Engagement/Success —
NOT tags), which is the single most common seeding mistake:

| KPI | Formula (SDM) | So to make it non-zero, seed… |
|---|---|---|
| **Unique Sessions** (denominator) | `COUNTD(session_id)` | one `AiAgentSession` row per conversation |
| **Unique Interactions** (Success denom.) | `COUNTD(IF InteractionType='TURN' THEN interaction_id)` | `TURN` interactions |
| **Engagement Rate** | `Engaged / Unique Sessions`; a session is **engaged** iff any interaction has a step with `ssot__AiAgentInteractionStepType__c='ACTION_STEP'` | ≥1 `ACTION_STEP` in the session's trace. **Structural — NOT a tag.** |
| **Success Rate** | `COUNTD(interaction that is engaged AND has NO error) / Unique TURN Interactions`; error = a step with a non-empty `ssot__ErrorMessageText__c` (≠ `NOT_SET`) | engaged interactions (ACTION_STEP) with a clean `ErrorMessageText`; put a real error string on failed ones to *lower* the rate. **Structural — NOT a tag.** |
| **Deflection Rate** | `Deflected / Unique Sessions`; **deflected** = NOT escalated AND abandonment score ∈ {FALSE, Unsure} AND deflection score ≥ 4 | `std_Deflection_Score` assoc `ValueText='4'/'5'` + `std_Abandonment_Score` `'false'`, `SourceType='PROMPT_TEMPLATE'` |
| **Abandon Rate** | `Abandoned / Unique Sessions`; **abandoned** = NOT escalated AND (deflection score < 3 OR abandonment score = TRUE) | `std_Deflection_Score` `'0'..'2'` and/or `std_Abandonment_Score` `'true'` |
| **Escalation Rate** | `Escalated / Unique Sessions`; **escalated** = a step with `StepType='SESSION_END'` AND `Name='CLOSED_TRANSFERRED'` (see the escalation bullet below) | a `SESSION_END`-type closure step named `CLOSED_TRANSFERRED` |
| **Task Resolution Rate** | `FULLY_RESOLVED / scored`, keyed on a `TaskResolution` **content-quality detector** on a `Generation` step | *advanced* — needs `AiContentQualityCategory` rows; stays 0 for a normal synthetic seed. Leave it, or seed the detector rows if the demo needs it. |

Notes that bite: **Engagement & Success are per-*interaction*/step, not per-tag** — a
session with topics but no `ACTION_STEP` reads 0 % engagement no matter how many tags it
has. Deflection/Abandon read the tag value via the "latest session scorer" join, so keep
one scorer per session (don't stack conflicting score associations). The exact
`Is_Interaction_With_Errors` / `Is_Latest_Session_Scorer` sub-calcs are in the SDM if you
need to disambiguate — pull them the same way.

**Session Outcome is derived from two PLATFORM-provisioned score tags, NOT from
`ssot__AiAgentSessionEndType__c` alone.** For every agent api name in the org, Data
Cloud auto-provisions a Predefined tag-definition pair (whether or not you seed
anything):

| DeveloperName | DataType | Values |
|---|---|---|
| `std_Deflection_Score_<AgentApiName>_V1` | Number | `0`–`5` |
| `std_Abandonment_Score_<AgentApiName>_V1` | Text | `true` / `false` / `unsure` |
| `std_Quality_Score_<AgentApiName>_V1` | Number | `1`–`5` |
| `std_Session_Notes_<AgentApiName>_V1` | LightningType | free text |

`Session_Outcome_Base_clc` (a Tableau-Next / semantic-model calc — **not queryable via
`/ssot/`**, so you can only eyeball it in the dashboard) maps:
- **Deflected** = Deflection score 4–5
- **Abandoned** = Abandonment `true`  OR  Deflection score < 3
- **Ambiguous** = Deflection score = 3
- **Escalated** = the session has an **interaction step with
  `ssot__AiAgentInteractionStepType__c='SESSION_END'` AND `ssot__Name__c='CLOSED_TRANSFERRED'`**
  — the session-end reason. This is the escalation signal. The exact semantic-model calc
  (retrievable — see the "reading the semantic model" note below):
  ```
  Escalation_Status = { FIXED session : MAX( IF
      ( [Interaction Step].[Ai_Agent_Interaction_Step_Type]='SESSION_END'
        OR DATEDIFF('HOUR', {FIXED session: MAX([Interaction].[End_Timestamp])}, NOW()) >= 24 )
      AND [Interaction Step].[Name]='CLOSED_TRANSFERRED' THEN TRUE ELSE FALSE END )}
  Escalated Sessions = COUNTD(sessions where Escalation_Status);  Escalation Rate = Escalated / Unique Sessions
  ```
  `CLOSED_TRANSFERRED` / `CLOSED_ACTION` / `CLOSED_USER_REQUEST` are the three
  `SessionEndReason` closure codes; the optimization runtime maps `ESCALATED →
  CLOSED_TRANSFERRED`. Three traps, all live-disproven:
    1. **NOT the session end-type** — `ssot__AiAgentSessionEndType__c='Escalated'` does
       *nothing* (real escalated sessions are end-type `NOT_SET`).
    2. **NOT the `__human__` topic and NOT the `escalate_to_human` router tool** — the
       router's `gen_ai.output.tool_names="escalate_to_human"` is the runtime *cause*, but
       the SDM keys on the downstream **session-end reason** (`CLOSED_TRANSFERRED`). A
       synthetic set with 52 `__human__` + `escalate_to_human` sessions read **0 %** until
       the `CLOSED_TRANSFERRED` closure step was added.
    3. **No `std_Escalation` tag** exists — it's not a tag KPI.
  So to seed an escalated session: give its `SESSION_END` interaction a step with
  `AiAgentInteractionStepType='SESSION_END'` and `Name='CLOSED_TRANSFERRED'`. Setting the
  step type to `SESSION_END` satisfies the OR-branch, so sessions <24 h old still count
  (otherwise the session must have ended ≥24 h ago). Non-escalated sessions get
  `CLOSED_ACTION` (resolved) / `CLOSED_USER_REQUEST` (user-ended) so they never read as
  escalated. Escalated sessions should also carry **no** deflection/abandonment score (a
  deflection 4-5 would classify them Deflected).
  > **Reading the semantic model itself:** the Escalation/Session-Outcome calcs live in a
  > `SemanticModel` (Tableau Next "SDM") that is **not in the Metadata API**, but IS
  > retrievable via REST: `GET /services/data/v67.0/ssot/semantic/models` (list) and
  > `GET …/ssot/semantic/models/{apiName}` (full JSON — `semanticCalculatedDimensions` /
  > `semanticCalculatedMeasurements`, each with an `expression` = the formula). Call it with
  > `sf api request rest '<path>' -o <org>`. This is how the escalation formula above was
  > recovered. (The VS Code "Salesforce Tableau Semantics" extension, `forcedotcom/tableau-dx`,
  > uses the same endpoints.)

**🔑 THE #1 GOTCHA — the tag-driven KPIs read the association's OWN denormalized fields,
not the joined tag-row value.** A tag association carries `ValueText__c` (the score value,
e.g. `"5"` / `"false"`) and `SourceType__c` (`'PROMPT_TEMPLATE'` for analyzer output). The
**Deflection / Abandon / Session-Outcome / Quality** KPIs read **`ValueText__c` +
`SourceType__c`** (Engagement & Success are NOT tag-driven — they're structural; see the
KPI formula table below). If you only link the tag row (leaving
`ValueText__c`/`SourceType__c` null — the naïve approach), the associations render for
Quality-by-Intent but are **invisible** to those KPIs — they then count only the handful of
real analyzer-scored sessions (≈0.6 %). A/B
against a real analyzer association: `OutcomeType__c` and `ssot__IsPassed__c` are NULL on
real rows (don't bother), but `ValueText__c` is always populated and `SourceType__c` =
`PROMPT_TEMPLATE`. So on EVERY synthetic score association set:
- `ValueText__c` = the value (`"0".."5"` for deflection; **lowercase** `"true"/"false"`
  for abandonment — matches the analyzer, even though the tag ROW value is `TRUE/FALSE`).
- `SourceType__c` = `'PROMPT_TEMPLATE'`.

**Association grain = SESSION-level** (`AiAgentSessionId` set, `AiAgentMomentId` + 
`AiAgentInteractionId` NULL) — confirmed valid + rendering. One deflection + one
abandonment association per session.

**Recipe (extends `spec/stdm_schema.py`'s `AiAgentTagAssociation` object):**
1. Add `ValueText` + `SourceType` to the `AiAgentTagAssociation` schema `cols` + `map`
   (`ValueText → ValueText__c`, `SourceType → SourceType__c` — note: NO `ssot__` prefix
   on these two target fields).
2. Resolve at runtime (org-specific ids): the two `std_` def ids, one tag-value row per
   value (`SELECT ssot__Value__c, ssot__Id__c FROM ssot__AiAgentTag__dlm WHERE
   ssot__AiAgentTagDefinitionId__c=<def>` — there are many rows per value, take any one),
   and the `ssot__AiAgentTagDefinitionAssociation__dlm` id per def+agent.
3. Query the LIVE synthetic session ids fresh (they drift on every SObject reseed) and
   derive each session's scores from its end-type: Completed→(defl 4-5, aband false)=
   Deflected; Abandoned→(defl 0-2, aband true)=Abandoned; Escalated→**no score** (skip;
   escalation is driven by the `CLOSED_TRANSFERRED` session-end step, not a score tag —
   and any deflection 4-5 would reclassify it Deflected). Push session-level associations
   with stable UUID5 ids (UPSERT-safe).
4. Distribution is set by the population's end-type mix (tune the SObject seeder / the
   generator). Target e.g. ~60 % Deflected / ~30 % Abandoned / ~10 % Escalated.

**⚠️ Adding `ValueText`/`SourceType` to an ALREADY-MAPPED DLO:** the DLO→DMO field
mapping is **create-only** — you can't add field pairs via the API once the mapping has
dependents (`PUT`=405, `DELETE`=500/412 while the DLO carries data, and re-`POST`
`DUPLICATE_DLO_TO_DMO_MAPPING`). Options: (a) `PUT` the expanded schema (adds the fields
to the DLO — that IS allowed) then add the two field mappings **by hand in the Data Cloud
UI** (Data Streams → the DLO → Data Mapping); or (b) teardown + recreate that one source.
The manual UI mapping is fastest. On a clean first install, include `ValueText`/
`SourceType` in the schema+map from the start and it's a non-issue.

## 12. High-fidelity single sessions (realistic drill-down "hero" traces)

The bulk synthetic population can be lo-fi (it only drives aggregate charts), but a demo
usually needs a few **drill-down-quality** sessions. Two hard-won rules:

**Custom SObject `DateTime` fields truncate to whole seconds on save** (verified: write
`12:34:56.789`, read back `12:34:56.000`). So the SDO/QBrix (Path 4) trace can NEVER show
the sub-second, random step timings a real session has — formula fields are second-
precision too (`DATETIMEVALUE` returns NULL for `HH:mm:ss.SSS`). **Millisecond timings
require Path 5** (Ingestion-API DateTime fields preserve ms from ISO-8601). Write the
hero sessions via Path 5 even in an org that otherwise uses Path 4 — they coexist in the
same DMOs under a distinct `ssot__DataSourceId__c`.

**Match a REAL current-agent trace field-for-field** (dump one live: find a recent
`agent_router` `LLM_STEP` and its interaction). What matters:
- **IDs are real UUIDs** — use deterministic UUID5 (namespace + a stable key) so a daily
  re-push UPSERTs the same rows instead of duplicating. NOT readable strings.
- **Per-turn step spine:** `VARIABLE_UPDATE_STEP` ("variable assignment") → `TOPIC_STEP`
  (the subagent) → `LLM_STEP` name=`agent_router` (the routing "reasoning", every turn) →
  `LLM_STEP` name=`<subagent>` → `ACTION_STEP`(s) (real action api names) →
  `TRUST_GUARDRAILS_STEP` name=`InstructionAdherence`. Router setup actions
  (resolve/get_bookings/…) appear on the first turn only.
- **Session-closure step (SESSION_END):** give each session's `SESSION_END` interaction a
  step with `AiAgentInteractionStepType='SESSION_END'` and `Name` = the `SessionEndReason`
  — `CLOSED_TRANSFERRED` (escalated), `CLOSED_ACTION` (resolved), or `CLOSED_USER_REQUEST`
  (user-ended). This is what the **Escalation Rate** reads (see §11); without it escalation
  is 0 no matter what the turn steps say.
- **Payloads are compact double-quote JSON** (verified field-for-field against live
  AIPlatform rows — NOT python-repr single-quote dicts. An earlier version of this
  playbook said python-repr; that was wrong). Emit with `json.dumps(dict, separators=(",",":"))`:
  - `LLM_STEP.InputValueText` = `{"af.request_id":"<32hex>","gen_ai.request.model":
    "llmgateway__GPT41","gen_ai.input.messages":"<JSON string of role/content messages>",
    "gen_ai.request.id":"<uuid>","af.prompt_template_dev_name":"Atlas__AgentGraphReasoningPrompt"}`
    (the `gen_ai.input.messages` VALUE is itself a nested JSON string — `json.dumps`
    escapes it correctly).
  - `LLM_STEP.OutputValueText` (router turn) = `{"gen_ai.response.finish_reasons":"tool_calls",
    "gen_ai.output.tool_names":"go_to_<subagent>"|"escalate_to_human","gen_ai.response.id":
    "chatcmpl-<id>","mgr.output.payload_type":"llm_event"}` — `gen_ai.output.tool_names` names
    the transition tool (`go_to_…` handoff, or `escalate_to_human` = the runtime *cause* of an
    escalation). Realistic trace detail, but note the **Escalation Rate KPI does NOT read this**
    — it reads the `CLOSED_TRANSFERRED` session-end step (§11). A wrap-up / non-routing LLM step
    finishes `"stop"` and omits `tool_names`.
  - `ACTION_STEP.InputValueText` = `{"af.request_id":"<32hex>","mgr.tool.argument_keys":
    "<comma-separated INPUT KEY NAMES>"}` (just the key names, not the values).
  - `ACTION_STEP.OutputValueText` = `{"mgr.output.payload_type":"tool_event",
    "mgr.tool.status":"success"|"error","mgr.tool.has_structured_output":"True|False",
    "mgr.tool.has_raw_output":"True"}` (status `error` for a failed action; also set
    `ErrorMessageText`).
  - `VARIABLE_UPDATE_STEP` in/out = **empty string** (not `{}`).
  - `Attribute`/`AttributeText` = `{"internalTraceId":"<32hex>","internalSpanId":"<16hex>"}`.
- **Timings:** seed step durations in ms from a real session (actions ~150–650 ms, LLM
  ~0.5–1.5 s, guardrail ~80–600 ms, a deliberately hung failed action can be ~15–20 s);
  `VARIABLE_UPDATE`=0 ms; `TOPIC_STEP` spans the whole turn; chain with a few-ms inter-
  step gap; 15–75 s (attentive) / 90–300 s (stepped-away) user gaps BETWEEN turns. Use a
  seeded RNG so the "random" timings are deterministic → the daily re-push reproduces the
  same shape and only rolls the dates.
- **Keep them on top of the list:** date them relative to NOW (e.g. now − 45/165/300 min),
  not a fixed clock time, and re-push daily. The bulk population goes further back.

**Ingestion-API ops facts (Path 5 in practice):**
- The API supports `operation:"delete"` (POST a job with a CSV of just the PK column) —
  use it to purge a prior generation of rows (e.g. after switching id schemes) without
  tearing down the source.
- **One open ingest job per source at a time** — back-to-back jobs on the same object
  (e.g. a delete then a push) 409 until the first drains; retry after a pause.
- After an SObject Full-Refresh the DMO reconcile takes **~5–7 min** — query the session
  distribution to confirm the new data landed BEFORE running the outcome-scoring step
  (it needs the CURRENT session ids).

A worked implementation (Skywave): `~/dev/is_interactive_skywave/scripts/datacloud/
hero_obs/` — `dc_ingest.py` (client-credentials variant of `dc_client.py`), `stdm_schema.py`
(+ ValueText/SourceType on TagAssociation, + errorMessageText on Step), `hero_story.py`
(the scripted heroes + real payload builders), `seed_heroes.py` (`setup`/`push`/`outcomes`/
`verify`/`teardown`). Its daily re-push + outcomes run from a GitHub Actions cron.
