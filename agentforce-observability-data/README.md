# agentforce-observability-data

A [Claude Code](https://claude.com/claude-code) skill that teaches Claude how to
**populate the Agentforce Observability dashboards (Analytics + Optimization →
Insights + Sessions & Intents) with synthetic, industry-specific sessions** that
render correctly and tell a deliberate quality story.

## Why

1. Agentforce Observability builds its dashboards and session listings off the
   **STDM** (Session Tracing Data Model) — a set of DMOs that Data Cloud models
   automatically the moment you activate Session Tracing in Setup.
2. There are two ways to get synthetic rows into those DMOs:
   - **SDO org** — the **SDO_Agentforce_Observability QBrix** recreates the STDM as
     ordinary custom objects and maps them back to the real DMOs.
   - **Any non-SDO org** (trial/sandbox/customer) — push STDM rows **straight into the
     DMOs via the Data Cloud Ingestion API** (Path 5). Fully headless (pure REST, no
     browser), and this skill ships a runnable reference implementation for it.
3. That data structure is intricate and governed by many undocumented rules
   (STDM enum vocabulary, the `Participant__c`/`ExternalSourceId` + `NOT_SET`
   requirements for Analytics, the `ssot__Bot__dlm` join that gates Optimization, the
   quality-story archetype model, and the **exact per-KPI signals** — e.g. Engagement =
   an `ACTION_STEP`, Escalation = a `CLOSED_TRANSFERRED` session-end step). **This skill
   tells Claude exactly what to take care of when generating a new dataset — and how to
   read any dashboard tile's real formula from the semantic model when a number looks
   wrong.**

Proven end-to-end on a Skywave Airlines rebrand (all Analytics + Optimization KPIs
non-zero and telling the intended quality story).

## Install

```bash
git clone <this-repo-url> ~/dev/agentforce-observability-data
ln -s ~/dev/agentforce-observability-data ~/.claude/skills/agentforce-observability-data
```

(or copy the folder into `~/.claude/skills/`). Then `/skills` should list
`agentforce-observability-data`.

## Contents

| File | What it covers |
|---|---|
| `SKILL.md` | How Observability collects data, STDM at a glance, the five data-population paths, diagnosing a widget that reads 0, onboarding-gap checklist. |
| `references/non-sdo-ingestion-api-playbook.md` | **Path 5** — push STDM rows into the DMOs via the Data Cloud Ingestion API (non-SDO orgs): the 11-object category/PK/field map, identity & render gates, the **exact KPI formulas** (Deflection/Abandon/Engagement/Success/Escalation), high-fidelity drill-down traces, and the full gotcha ledger. |
| `references/reading-the-semantic-model.md` | When a dashboard tile reads 0 (or wrong): pull the tile's real formula from the semantic model over REST, trace it to the DMO field/value it counts, and seed that — instead of guessing. |
| `references/sdo-qbrix.md` | **Path 4** per-field render mechanics (enums, `Participant__c`, `NOT_SET` sentinel, telemetry, timestamps, closure/session-end reasons). |
| `references/rebrand-seeder-playbook.md` | End-to-end recipe to re-theme the QBrix for any industry: object graph, the `ssot__Bot__dlm` gate, quality-story archetype model, conversation timing, seeder skeleton, run sequence. |
| `references/onboarding-checklist.md` | Org-readiness checks before seeding. |
| `reference-impl/` | Runnable, dependency-free Path-5 seeder: `dc_client.py` (auth + ingest + query + `read_semantic_model`), `stdm_schema.py` (11 objects + full field map), `seed_reference.py` (generator + `setup`/`push`/`verify`/`teardown` CLI). Edit `AGENT_API_NAME` + `ARCHETYPES` and run. |

## Prerequisites (org side)

- Observability stack on: Session Tracing + Optimization (Beta) toggles,
  "Agentforce Analytics Foundations" Data Kit deployed, Service Agent Data Model
  installed, Tableau Next Limited license.
- Permsets: `AgentforceInteractionExplorer`, `TableauNextLimitedViewer`, a Data
  Cloud user, `API Enabled` on the profile.
- A **deployed + activated agent whose API name matches your synthetic sessions**
  (even a barebones `start_agent`-only one) so a `ssot__Bot__dlm` row exists — this
  gates the Optimization tab.
- **Then pick your path:**
  - *SDO org* → the **SDO_Agentforce_Observability QBrix** installed. Refreshing its
    SalesforceDotCom streams needs **Dev Console** (can't be driven headless).
  - *Non-SDO org* → a **Connected App** with the `cdp_ingest_api` + `cdp_query_api`
    scopes (client-credentials flow) for the Ingestion API. Fully headless — no QBrix,
    no browser. See `reference-impl/README.md`.

## License

MIT — see [LICENSE](LICENSE).
