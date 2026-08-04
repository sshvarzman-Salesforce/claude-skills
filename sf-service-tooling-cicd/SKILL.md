---
name: sf-service-tooling-cicd
description: Tooling API patterns for Service Cloud CI/CD. Use when introspecting or validating Service Cloud metadata — Apex coverage on routing/flow paths, Flow versions, OmniProcess definitions, validation rules, custom fields — and running async test batches in pipelines.
disable-model-invocation: true
---
# Service Cloud CI/CD (Tooling API)

## Use This Skill When

- Wiring Service Cloud metadata into a CI/CD pipeline (GitHub Actions, Jenkins, Copado).
- Enforcing Apex code coverage gates on triggers/classes exercised by routing, entitlements, or flows.
- Introspecting active Flow versions (e.g., Omni routing flow) before promoting a package.
- Auditing validation rules and custom fields on Case, VoiceCall, MessagingSession before a deploy.
- Running async test batches and blocking pipeline promotion on results.

## Core Workflow

1. **Define the pipeline stage**
   - Pre-deploy: retrieve + diff metadata, run validation and static checks.
   - Post-deploy: run async tests, evaluate coverage aggregates.
2. **Introspect the target org**
   - Query `FlowDefinition` + `Flow` to confirm the expected active version is present after deploy.
   - Query `OmniProcess` for OmniScript/Integration Procedure states.
3. **Assert coverage**
   - Query `ApexCodeCoverageAggregate` for classes/triggers on the routing/entitlement path.
   - Fail the build when coverage drops below the org-defined floor for touched classes.
4. **Audit config**
   - `ValidationRule` and `CustomField` on Case, VoiceCall, MessagingSession — snapshot before/after to detect drift.
5. **Run tests async**
   - `POST /tooling/runTestsAsynchronous` with the list of classes; poll `ApexTestRunResult` for status; publish JUnit XML.

## Deliverables

- CI stage definitions (pre-deploy checks, post-deploy asserts).
- Coverage floor per subsystem (case, entitlements, omni-routing, voice) with rationale.
- Drift detection queries for validation rules / custom fields with owning team.
- Test-run report format (JUnit + coverage summary) consumed by the CI provider.

## References

- See `references/api-cli.md` for exact Tooling API endpoints and object shapes.
