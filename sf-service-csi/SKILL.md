---
name: sf-service-csi
description: Customer Service Insights (CSI) — Data Cloud-powered service analytics for Service Cloud. Use when activating CSI data kits, wiring channels into the service semantic model, and planning insight surfaces.
disable-model-invocation: true
---
# Customer Service Insights (CSI)

## Use This Skill When

- Activating Customer Service Insights on a Data Cloud org for service analytics.
- Provisioning the base data kit and channel-specific extensions (voice, messaging, case).
- Deciding what insights to surface into agent, supervisor, or leader views.
- Reasoning about the boundary between CSI (Data Cloud analytics) and Service Cloud reporting.

## Core Workflow

1. **Verify Data Cloud prerequisites**
   - Confirm Data Cloud is provisioned and the CSI license is active.
   - Confirm identity resolution / DMO baseline exists before installing kits.
2. **Activate the base data kit**
   - Install the CSI base data kit via Connect REST to seed DMOs and mappings.
3. **Wire channels**
   - Install per-channel data kits (Voice, Messaging, Case) to bring source data under the CSI semantic model.
4. **Curate insights**
   - Insight configuration and real-time insights are Setup-UI-driven today; catalogue what surfaces (agent, supervisor, exec).
5. **Route insights to consumers**
   - Decide surfacing target: Console component, Analytics tab, external BI, Slack alert.

## Deliverables

- CSI enablement checklist with license + Data Cloud prereqs.
- Data-kit installation order (base → channel extensions).
- Insight-to-consumer mapping with owning role.
- Gaps between CSI-provided insights and custom analytics that still need CRM Analytics or Data Cloud Insights Studio.

## References

- See `references/api-cli.md` for the Connect REST endpoints and known API/no-API rows.
