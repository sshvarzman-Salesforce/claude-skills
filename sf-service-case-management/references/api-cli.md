# Case Management — API + CLI Reference

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Case (core object) | Metadata, REST, Bulk | `Case` (std sObject); `CustomObject:Case` for fields, layouts, record types | `sf project deploy start --metadata CustomObject:Case` |
| Assignment Rules | Metadata | `AssignmentRules:Case` | `sf project deploy start --metadata AssignmentRules:Case` |
| Escalation Rules | Metadata | `EscalationRules:Case` | `sf project deploy start --metadata EscalationRules:Case` |
| Auto-Response Rules | Metadata | `AutoResponseRules:Case` | `sf project deploy start --metadata AutoResponseRules:Case` |
| Support Settings | Metadata | `CaseSettings` | `sf project deploy start --metadata CaseSettings` |
| Queues | Metadata | `Queue` | `sf project deploy start --metadata Queue` |
| Case Comments / Feed | REST | `CaseComment`, `FeedItem` (data-only) | `sf data create record --sobject CaseComment` |

## Docs

- Case: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_case.htm
- AssignmentRules: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_assignmentrules.htm
- EscalationRules: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_escalationrules.htm

## Notes

- Deploy `AssignmentRules` before referencing queues that are the assignment target — the deploy validates references.
- `EscalationRules` uses **business hours** — deploy `BusinessHoursSettings` first when introducing a new business hours record.
- Case record types often gate page layouts; consolidate record-type additions with `Layout` and `Profile`/`PermissionSet` in the same deploy to avoid orphaned assignments.
