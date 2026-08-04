# Incident Management — API + CLI Reference

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Incident (core object) | Metadata, REST | `Incident` (std sObject); `CustomObject:Incident` for fields | `sf project deploy start --metadata CustomObject:Incident` |
| Incident Related Item | REST | `IncidentRelatedItem` (data) | `sf data create record --sobject IncidentRelatedItem` |
| Broadcast Communications | REST | `Broadcast`, `BroadcastTopic` (data-only) | `sf data import bulk` |
| Case ↔ Incident link | REST | `CaseRelatedIssue` (junction; data-only) | `sf data create record --sobject CaseRelatedIssue` |
| Swarming | REST | `Swarm`, `SwarmMember` (data-only) | UI/Slack setup + `sf data` |
| Problem (post-incident) | Metadata, REST | `Problem` (std sObject); `CustomObject:Problem` | `sf project deploy start --metadata CustomObject:Problem` |
| Change Request (fix action) | Metadata, REST | `ChangeRequest` (std sObject); `CustomObject:ChangeRequest` | `sf project deploy start --metadata CustomObject:ChangeRequest` |

## Docs

- Incident: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_incident.htm
- CaseRelatedIssue: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_caserelatedissue.htm
- Broadcast: https://help.salesforce.com/s/articleView?id=sf.incident_broadcast.htm&type=5

## Notes

- Standard sObjects (`Incident`, `Problem`, `ChangeRequest`) — deploy `CustomObject:<Name>` **only for field/layout extensions**; the base object exists in the target org already.
- `Broadcast`, `Swarm*`, and Service Catalog records are **data-only** — no metadata deploy path today.
- For the full ITSM object graph (Problem, Change, Broadcast, Swarming, Asset hierarchy, Service Catalog), see `sf-service-itsm-processes`.
- For agentic ITSM enablement, see the `service-itsm-*` skill family.
