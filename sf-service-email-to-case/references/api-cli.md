# Email-to-Case — API + CLI Reference

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Email-to-Case Settings | Metadata | `EmailToCaseSettings` (inside `CaseSettings`) | `sf project deploy start --metadata CaseSettings` |
| Routing Address | Metadata | `EmailServicesAddress` | `sf project deploy start --metadata EmailServicesAddress` |
| Email Service (On-Demand E2C) | Metadata | `EmailServicesFunction` | `sf project deploy start --metadata EmailServicesFunction` |
| Auto-Response Rules | Metadata | `AutoResponseRules:Case` | `sf project deploy start --metadata AutoResponseRules:Case` |
| Email Templates | Metadata | `EmailTemplate` | `sf project deploy start --metadata EmailTemplate` |
| Email Message | REST | `EmailMessage`, `EmailMessageRelation` (data) | `sf data query -q "..."` |

## Docs

- CaseSettings: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_casesettings.htm
- EmailServicesAddress: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_emailservicesaddress.htm
- EmailServicesFunction: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_emailservicesfunction.htm

## Notes

- The **On-Demand** flavor (`EmailServicesFunction`) is the default; the on-premise flavor requires the Email-to-Case agent, which is deprecated for new implementations.
- `EmailServicesAddress` is the routing address; the domain part must be pre-configured in the org before the deploy will accept it.
- Threading uses `Thread-Id`/`References` headers; changing threading tokens mid-migration will break existing case correlation.
