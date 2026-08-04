# Tooling API — Service Cloud CI/CD Reference

All Tooling API. No `sf project deploy` — these are read/execute operations against org state.

| Feature | Object / Endpoint | Purpose |
|---|---|---|
| Apex Code Coverage | `ApexCodeCoverageAggregate` (GET) | Class/trigger coverage for Apex on routing/entitlement/flow paths |
| Flow Introspection | `FlowDefinition` + `Flow` (GET) | Confirm active flow version (e.g., Omni routing flow) after deploy |
| OmniProcess Query | `OmniProcess` (GET) | OmniScript / Integration Procedure definitions and active version |
| Validation Rules | `ValidationRule` (GET) | Rules on Case, MessagingSession, VoiceCall — drift audit |
| Custom Fields | `CustomField` (GET) | Custom-field inventory on service sObjects — drift audit |
| Run Async Tests | `POST /services/data/vXX.0/tooling/runTestsAsynchronous/` | Fire async Apex test batches |
| Test Run Result | `ApexTestRunResult`, `ApexTestResult`, `AsyncApexJob` (GET) | Poll for status, publish JUnit |

Docs:
- ApexCodeCoverageAggregate: https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_apexcodecoverageaggregate.htm
- Flow: https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_flow.htm

## CLI equivalents

The Salesforce CLI wraps most of these:

| Task | CLI |
|---|---|
| Async test run | `sf apex run test --async --tests <classes>` |
| Test coverage report | `sf apex run test --code-coverage --result-format json` |
| Get test results | `sf apex get test --test-run-id <id>` |
| Query any Tooling object | `sf data query --use-tooling-api -q "..."` |

## Notes

- `ApexCodeCoverageAggregate` returns coverage as of the last test run; force fresh data by running tests first.
- Prefer synthetic queries against `FlowDefinition.ActiveVersion` over parsing metadata for "is the right version live?" checks — Tooling gives you a first-class answer.
- Async test polling: `AsyncApexJob.Status` → `Completed`, then read `ApexTestRunResult` for pass/fail/coverage summary.
- For pipeline speed, submit tests by suite (`ApexTestSuite`) rather than name-list — easier to maintain in code review.
