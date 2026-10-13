# reference-impl — a runnable Path 5 observability seeder

Dependency-free (urllib only) reference for seeding **all** Agentforce observability
dashboards in a non-SDO org via the Data Cloud Ingestion API. Read it, then adapt the
config for your demo. Proven end-to-end (Skywave); genericised here.

```
dc_client.py       Data Cloud client — client-credentials auth → CDP token exchange,
                   Ingestion CRUD (connection/schema/stream/mapping), ingest jobs,
                   query, DMO metadata, and read_semantic_model() (read a tile's rule).
stdm_schema.py     The 11 STDM objects: cols, PKs, categories, event-time fields, and
                   the full DLO→DMO field map. Set PREFIX per demo.
seed_reference.py  Generator + CLI (setup/push/verify/teardown). Edit AGENT_API_NAME +
                   ARCHETYPES. Builds the row graph with every KPI-driving signal.
```

## Prereqs (one-time)
1. Org toggles + Foundations Data Kit + Tableau Next license + Service Agent Data Model
   + permsets — see `../references/onboarding-checklist.md`.
2. A Connected App with `cdp_ingest_api` + `cdp_query_api` (+ `api`) scopes, client-
   credentials flow + run-as user. Export `DC_CONSUMER_KEY/DC_CONSUMER_SECRET/DC_INSTANCE_URL`.
   (Full auth recipe: the sibling `sf-datacloud-api-auth` skill.)
3. **Deploy + publish + activate** an agent whose api name == `AGENT_API_NAME`, and turn
   on **Agentforce Optimization**. This is what (a) creates the `ssot__Bot__dlm` row that
   gates the whole Optimization tab, and (b) auto-provisions the `std_Deflection_Score` /
   `std_Abandonment_Score` tag-defs the seeder references for Deflection/Abandon. Without
   it those two rates read 0 (the seeder warns).

## Run
```bash
export DC_CONSUMER_KEY=... DC_CONSUMER_SECRET=... DC_INSTANCE_URL=https://<myorg>.my.salesforce.com
python3 seed_reference.py setup   --target-org <alias>     # 11 sources/streams/mappings (idempotent)
python3 seed_reference.py push    --target-org <alias> -n 200
python3 seed_reference.py verify  --target-org <alias>     # DMO counts + engagement/escalation signals
# re-run push daily (UPSERT, today-relative timestamps) to keep the data in-window.
```
Gate on the **DMO row counts** from `verify`, not the ingest job state. The Analytics tab
(Tableau Next) then re-materialises on its own slower lag.

## Which part feeds which tile (the whole point)
| KPI / view | Signal the generator seeds |
|---|---|
| Unique Sessions | one `AiAgentSession` per conversation (+ `ExternalSourceId` = org id) |
| Engagement Rate | every TURN has an **`ACTION_STEP`** → session is "engaged" |
| Success Rate | engaged interaction with **no** `errorMessageText` on any step; failing archetypes set an error |
| Deflection Rate | `std_Deflection_Score` assoc, `ValueText='4'/'5'`, `SourceType='PROMPT_TEMPLATE'` |
| Abandon Rate | `std_Deflection_Score='0'..'2'` and/or `std_Abandonment_Score='true'` |
| Escalation Rate | `SESSION_END`-type step named **`CLOSED_TRANSFERRED`** |
| Quality by Subagent/Intent | `Quality_Score` (1-5) + `AIE_Request_Category_<agent>` tags on each moment |
| Sessions & Intents / Moments / Insights | the moment rows + `ssot__Bot__dlm` join (deployed agent) |
| Session Outcome | derived from the above (score 4-5=Deflected, <3/true=Abandoned, CLOSED_TRANSFERRED=Escalated) |

The exact tile formulas are in `../references/non-sdo-ingestion-api-playbook.md` §11; how to
read any tile's formula from the model is in `../references/reading-the-semantic-model.md`.

## Adapting
- Edit `ARCHETYPES` (topic, intent, quality, outcome, action, action_fails, weight) to your
  story. Outcome ∈ `deflected` / `abandoned` / `escalated`.
- Every archetype fires an action → ~100 % engagement. For a lower engagement rate, add an
  archetype with a no-action turn (e.g. off-topic).
- `USER` participants use `MessagingEndUser` if the org has any, else active `User` (`005`)
  — both render; the identity that matters for the agent dropdown is the **AGENT**
  participant's GenAiPlannerDefinition id.
- For a millisecond-precise, step-by-step **drill-down "hero"** session (vs the compact
  traces here), follow `../references/non-sdo-ingestion-api-playbook.md` §12 — same objects,
  richer per-step payloads + timings.
- This is a starting point, not a turnkey product: verify target field names in your org
  (`DC.dmo_metadata(dmo)`) if a mapping 400s, and eyeball the dashboard after the semantic
  layer re-materialises.
