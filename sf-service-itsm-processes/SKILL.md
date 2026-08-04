---
name: sf-service-itsm-processes
description: Core ITSM objects and processes on Service Cloud beyond Incident — Problem management, Change Request, Broadcast, Swarming records, Asset hierarchy, KCS Knowledge, Service Catalog. Use when designing the ITSM object model or wiring these processes together.
disable-model-invocation: true
---
# Service Cloud ITSM — Core Processes

## Use This Skill When

- Designing an ITSM implementation that goes beyond `Incident` (see `sf-service-incident-management`).
- Modeling Problem → Change → Release lifecycle and their linkage to Incidents.
- Wiring Broadcast communications from incidents to affected users.
- Setting up Swarming as a collaboration surface for major incidents (Slack-based).
- Structuring the Asset hierarchy and mapping incidents/cases to CIs.
- Publishing KCS (Knowledge-Centered Service) knowledge alongside ITSM records.
- Standing up a Service Catalog for request fulfilment.

## Core Workflow

1. **Establish the object graph**
   - Incident ↔ Problem ↔ ChangeRequest as first-class ITSM objects.
   - Asset ↔ ParentId/RootAssetId hierarchy — link CIs to Incidents.
   - Broadcast + BroadcastTopic for cross-user comms.
   - Swarm + SwarmMember for real-time collab (Slack-integrated).
   - KCS via `KnowledgeSettings` + the `Knowledge__kav` article model.
   - Service Catalog: `ServiceCatalog`, `ServiceCatalogItem`, `ServiceCatalogCategory` (records, no dedicated metadata type today).
2. **Design lifecycle**
   - Incident → Problem: define the promotion criteria (recurrence, blast radius).
   - Problem → Change: define the RCA-to-fix handoff.
   - Broadcast: define who authors, who receives, cadence.
3. **Deployability**
   - Metadata-deployable: `Incident`, `Problem`, `ChangeRequest`, `Asset` (as `CustomObject`); `KnowledgeSettings`.
   - Data-only: `Broadcast`, `BroadcastTopic`, `Swarm`, `SwarmMember`, Service Catalog records — seed via `sf data`.
4. **Wire integrations**
   - Slack: Swarming requires Slack app install + user linkage.
   - Broadcasts often surface in-app + email; verify notification-target model.
5. **Reporting**
   - Cross-object dashboards: incidents by CI, MTTR by problem, change-caused incidents.

## Deliverables

- Object graph with ownership and record types.
- Lifecycle table (Incident → Problem → Change) with promotion criteria.
- Metadata vs data-only inventory and load order.
- Slack/Swarming enablement checklist.
- Service Catalog structure with initial category/item seed.

## References

- See `references/api-cli.md` for the full object → metadata type → CLI mapping.
- Related: `sf-service-incident-management` (major incident intake), `service-itsm-*` skills (agentic ITSM setup).
