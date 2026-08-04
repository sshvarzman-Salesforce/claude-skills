# CSI — Data Kit & Insight API Reference

Customer Service Insights is delivered as a **Data Cloud data-kit family**. Activation flows through the Data Cloud Connect REST layer; only some CSI features are API-addressable today.

| Feature | API | Endpoint / Object | CLI |
|---|---|---|---|
| Base data-kit activation | Connect REST | `POST /ssot/data-kits/{dataKitDevName}` | n/a — Connect REST only |
| Manage Channels (per-channel data kits) | Connect REST | `POST /ssot/data-kits/{dataKitDevName}` | n/a |
| Manage Insights | None | Setup UI only | n/a |
| Real-Time Insights | None | Setup UI only | n/a |

## Notes

- Activation is idempotent per data kit — re-POSTing succeeds and refreshes bindings.
- Data-kit dev names must match the CSI catalog exactly (case-sensitive); pull the current list from Data Cloud Setup before scripting.
- Insight configuration and real-time insight wiring have **no public API today**. Track requests via GUS/UDD if you need this in CI.
- CSI depends on the target org being a Data Cloud-enabled org with identity resolution baseline. Verify with `sf data query -q "SELECT Id FROM DataCloudObject__c LIMIT 1"` (or the equivalent DMO probe) before activation.
- Downstream: activated data kits show up under `MktDataConnectorSourceObject` and related DMOs; use those for report and insight queries.

## Related

- `sf-datacloud-connect` / `sf-datacloud-harmonize` — upstream Data Cloud plumbing.
- `sf-service-review` — CSI adoption is a data point in service maturity review.
