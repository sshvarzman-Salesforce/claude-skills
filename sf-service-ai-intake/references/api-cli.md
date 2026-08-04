# AI Intake — API + CLI Reference

This skill composes `sf-service-voice-toolkit` (live transcript) and `sf-service-models-api` (LLM extraction). The APIs below are the metadata glue for the intake template + dispatch pattern.

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Intake Template (custom) | Metadata | `CustomObject:Intake_Template__c` (customer-defined) | `sf project deploy start --metadata CustomObject:Intake_Template__c` |
| Extraction Prompts | Metadata | `GenAiPromptTemplate` (Prompt Builder) | `sf project deploy start --metadata GenAiPromptTemplate` |
| Models (LLM Gateway) | REST | Einstein Trust Layer — `/services/data/vXX.0/einstein/llm/models/{modelName}/generations` | n/a |
| Case Classification (opt-in feature) | Metadata | `CaseClassificationSettings`, `Einstein*Settings` | `sf project deploy start --metadata CaseClassificationSettings` |
| Live Transcript Source | LWC API | `lightning/voiceToolkitApi` (agent-side) or `ConversationEntry` SOQL (record page) | n/a |

## Docs

- GenAiPromptTemplate: https://developer.salesforce.com/docs/atlas.en-us.prompt_builder.meta/prompt_builder/prompt_builder_intro.htm
- Einstein LLM Gateway: https://developer.salesforce.com/docs/einstein/genai/references/llm-gateway.html

## Notes

- Field-fill suggestions must remain **non-destructive** — write to a `Suggested_*` field or emit a UI event; never overwrite the agent's edited value.
- Prompt templates are versioned via `GenAiPromptTemplate` metadata; publish + activate before dispatch code references them.
- Case classification (Salesforce-provided ML) is separate from LLM extraction (custom prompt); pick one per field rather than blending predictions.
