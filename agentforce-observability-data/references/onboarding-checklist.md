# Agentforce Observability — onboarding gap checklist

Run through in order. Stop at the first miss; downstream items depend on the earlier ones.

## 1. Org-level toggles
**Setup → Einstein Audit, Analytics, and Monitoring Setup**
- [ ] Agentforce Session Tracing & Data Model: ON
- [ ] Agentforce Optimization (Beta): ON
- [ ] Default Dataspace selected
- [ ] Tableau Next license available (visible in Setup → Permission Sets as `TableauNextLimitedViewer` / "Tableau Next Limited Consumer")

## 2. Foundations data kit
**Setup → Data Kits → Agentforce Analytics Foundations → Deployment History**
- [ ] All deployments succeeded
- [ ] If failed: re-toggle Session Tracing OFF then ON, wait for redeploy

## 3. STDM provisioning complete
After step 1, allow ~1 hour. To confirm:
```bash
# On-core SSOT proxy, regular session token
curl -s "$SF_INSTANCE/services/data/v66.0/ssot/metadata?entityType=DataModelObject" \
  -H "Authorization: Bearer $SF_TOKEN" | grep -c "AiAgent"
```
Should return at least 11 matches.

## 4. Tableau Next Agent Analytics app installed
**Setup → Agent Analytics (Beta)**
- [ ] Service Agent Analytics — Installed
- [ ] (optional) Employee Agent Analytics — Installed

If install button is greyed out, STDM provisioning is incomplete (see step 3). If it shows but install fails, the org may not have Salesforce Foundations ($0 SKU) — activate via Foundations self-serve link.

## 5. User permission sets
The user who will demo:
- [ ] `AgentforceInteractionExplorer` — for Optimization tab (Insights/Moments/Sessions)
- [ ] `TableauNextLimitedViewer` — for Analytics tab
- [ ] Data Cloud User equivalent (e.g. `xDO_DataCloud_Base_PSG` or out-of-the-box "Data Cloud User") — for SQL access
- [ ] User profile has **API Enabled = true** (else Tableau Next metric cards won't load)

## 6. Sandbox-only steps (skip for production / dev / trial orgs)
After sandbox refresh, the Ingestion API connector loses its auth:
- [ ] Setup → Data Cloud Setup → Ingestion API → AgentOpt → click **Activate**
- [ ] Re-toggle Session Tracing + Optimization OFF/ON to reactivate streams

## 7. Optional: synthetic data
If demo needs visible data fast, install the **SDO_Agentforce_Observability QBrix** (and its prereq Data Cloud | Setup Automation). After install, refresh each `SDO_Analytics_*_Home` data stream in Data Cloud → Data Streams. See [`sdo-qbrix.md`](sdo-qbrix.md).

If demo can wait, drive real conversations against an existing agent (Builder preview, or Agent API via a tool like `af-conversation-primer`). STDM picks them up automatically.

## What to verify when "no data shows up"

Symptom → likely gap:
- Optimization tab empty → step 5 (perm set) or step 1 (Optimization toggle off)
- Analytics tab "No data" → step 5 (Tableau Next perm set) + step 4 (app install)
- Tableau Next metric cards fail to load → step 5 (API Enabled on profile)
- DMOs are empty in queryv2 → step 1 + step 3 (Session Tracing not on, or provisioning incomplete)
- Foundations kit deployment history empty → step 1 toggles never turned on
- Synthetic SDO data not appearing → SDO data streams need Full Refresh after custom-object load
