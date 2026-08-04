# ITSM Core Processes — API + CLI Reference

Coverage complements `sf-service-incident-management` (major-incident lifecycle) with the rest of the ITSM object family.

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Problem Management | Metadata, REST | `Problem` (std sObject); `CustomObject:Problem` for fields | `sf project deploy start --metadata CustomObject:Problem` |
| Change Management | Metadata, REST | `ChangeRequest` (std sObject); `CustomObject:ChangeRequest` | `sf project deploy start --metadata CustomObject:ChangeRequest` |
| Broadcast Communications | REST | `Broadcast`, `BroadcastTopic` (std sObjects — data only) | `sf data import bulk` (not metadata-deployable) |
| Swarming (Slack collab) | REST | `Swarm`, `SwarmMember` (std sObjects — data only) | Setup via Slack + UI; records via `sf data` |
| Customer Asset / Asset Hierarchy | Metadata, REST | `Asset` (std sObject; hierarchy via `ParentId` / `RootAssetId`) | `sf project deploy start --metadata CustomObject:Asset` |
| Knowledge for ITSM (KCS) | Metadata | `KnowledgeSettings` (org-level); `Knowledge__kav` articles are data | `sf project deploy start --metadata KnowledgeSettings` |
| Service Catalog | REST (Partial) | `ServiceCatalog`, `ServiceCatalogItem`, `ServiceCatalogCategory` (std sObjects — records only, no dedicated metadata type confirmed) | Records via `sf data`; watch for future metadata type |

## Docs

- Problem: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_problem.htm
- ChangeRequest: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_changerequest.htm
- Broadcast: https://help.salesforce.com/s/articleView?id=sf.incident_broadcast.htm&type=5
- Swarming: https://help.salesforce.com/s/articleView?id=sf.service_swarming_overview.htm&type=5
- Asset: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_asset.htm
- KnowledgeSettings: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_knowledgesettings.htm
- Service Catalog: https://help.salesforce.com/s/articleView?id=sf.service_catalog_overview.htm&type=5

## Notes

- Standard sObjects here (`Incident`, `Problem`, `ChangeRequest`, `Asset`) are deployable via `CustomObject` metadata **only for the field/layout extensions** — the base object exists in the target org already.
- Broadcasts, Swarms, and Service Catalog items are **data-only**. Plan seeding through `sf data import bulk` with external IDs for idempotency (see `sf-service-data-api-operations`).
- Swarming requires the Slack integration — see `service-itsm-swarming-configure` (org enablement) and `service-itsm-teams-*` for the Teams-based variant.
- KCS knowledge sits on the same `Knowledge__kav` object as Service Cloud knowledge; ITSM-specific tagging happens through data categories.
- Service Catalog metadata type may land in a future release — check current developer docs before scripting deploys.
