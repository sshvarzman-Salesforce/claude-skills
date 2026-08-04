# Entitlements & Milestones — API + CLI Reference

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Entitlement Process (SLA timers) | Metadata | `EntitlementProcess` | `sf project deploy start --metadata EntitlementProcess` |
| Milestone Types | Metadata | `MilestoneType` | `sf project deploy start --metadata MilestoneType` |
| Entitlement Templates | Metadata | `EntitlementTemplate` | `sf project deploy start --metadata EntitlementTemplate` |
| Entitlement Settings | Metadata | `EntitlementSettings` | `sf project deploy start --metadata EntitlementSettings` |
| Business Hours | Metadata | `BusinessHoursSettings` + `BusinessProcess` where applicable | `sf project deploy start --metadata BusinessHoursSettings` |
| Entitlement (record) | REST | `Entitlement` (std sObject) | `sf data create record --sobject Entitlement` |
| Case Milestone (runtime) | REST | `CaseMilestone` (data-only) | `sf data query -q "..."` |

## Docs

- EntitlementProcess: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_entitlementprocess.htm
- MilestoneType: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_milestonetype.htm
- Entitlement: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_entitlement.htm

## Notes

- `EntitlementProcess` versions are **immutable once active** — deploy new versions rather than editing.
- Milestone triggers evaluate against `BusinessHours`; verify time-zone alignment before rollout.
- `CaseMilestone` records are created by the platform when a Case enters an entitlement — do not create them directly.
