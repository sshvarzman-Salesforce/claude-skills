# Omni-Channel Routing — API + CLI Reference

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Routing Configuration | Metadata | `RoutingConfiguration` | `sf project deploy start --metadata RoutingConfiguration` |
| Service Channel | Metadata | `ServiceChannel` | `sf project deploy start --metadata ServiceChannel` |
| Presence Configuration | Metadata | `PresenceUserConfig` | `sf project deploy start --metadata PresenceUserConfig` |
| Presence Statuses | Metadata | `PresenceDeclineReason`, `PresenceStatus` (labels on `PresenceUserConfig`) | `sf project deploy start --metadata PresenceDeclineReason` |
| Queue | Metadata | `Queue` | `sf project deploy start --metadata Queue` |
| Skills (skill-based routing) | Metadata | `Skill` | `sf project deploy start --metadata Skill` |
| Omni Supervisor / Live Agent Config | Metadata | `LiveAgentSettings`, `LiveChatButton` | `sf project deploy start --metadata LiveAgentSettings` |
| Work Item (runtime) | REST | `AgentWork`, `PendingServiceRouting` (data-only) | `sf data query -q "..."` |

## Docs

- RoutingConfiguration: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_routingconfiguration.htm
- ServiceChannel: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_servicechannel.htm
- PresenceUserConfig: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_presenceuserconfig.htm

## Notes

- `ServiceChannel` names are load-bearing — renaming after Flows/Apex reference them breaks routing.
- `RoutingConfiguration` defines capacity units; changing a live configuration under load can starve agents momentarily.
- Skills-based routing requires `Skill` metadata + `SkillUser` records — the records are data (`sf data`), not metadata.
- Omni-Channel Flow routing uses a Flow of type `Routing` — deploy alongside `RoutingConfiguration` when they reference each other.
