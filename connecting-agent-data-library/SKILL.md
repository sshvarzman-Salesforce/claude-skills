---
name: connecting-agent-data-library
description: Connect an Agentforce Service Agent (ASA) to an Agentforce Data Library (ADL) so it can answer general FAQ questions from knowledge articles with citations ("show resources"). TWO wiring paths exist — a bot-level `knowledge:` binding written by the builder when you select a Data Library on the agent, AND a prompt-template/Einstein-retriever path. Both are documented here; pick the one that matches how the agent was set up.
---

# Connecting an Agentforce Service Agent to a Data Library

## The one thing to understand

There are **two distinct ways** a Data Library reaches an agent, and earlier versions of this skill wrongly claimed only the template path exists. Both are real:

1. **Bot-level `knowledge:` binding (what the Agentforce Builder writes).** When you open the agent in the builder and connect a Data Library (e.g. select the "ALL KBAs" ADL), the platform adds a **bot-level `knowledge:` block** to the agent YAML / `.agent`:
   ```
   knowledge:
       rag_feature_config_id: "ARFPC_1JDgL000008RroPWAS"
       citations_url: "https://<your-domain>.lightning.force.com/"
       citations_enabled: True
   ```
   This IS a bot-level ADL binding. `rag_feature_config_id` (prefix **`ARFPC`** = an internal **AiRagFeatureConfig** record) is the RAG feature config backing the selected data library — created/managed by the builder, not something you author by hand or resolve via a public Connect/Tooling endpoint (`connect/ai/rag/feature-configs/<id>` returns NOT_FOUND; `AiRagFeatureConfig`/`RetrievalSummaryDefinition` aren't SOQL-exposed here). `citations_url` is your org's Lightning domain (where "show resources" links resolve). `citations_enabled: True` turns on citations globally for the agent's knowledge answers.

2. **Prompt-template + Einstein-retriever path (author-by-hand).** A `GeneralFAQ` subagent whose action targets a flex prompt template that references an Einstein retriever:
   ```
   subagent GeneralFAQ
      └─ action → generatePromptResponse://<FlexTemplate>
                      └─ template body references {!$EinsteinSearch:<RetrieverName>.results}
                      └─ templateDataProviders: invocable://getEinsteinRetrieverResults/<RetrieverName>
                             └─ the Einstein retriever IS the data library's search index
   ```
   To give an agent the **same** library/citations/domain as another agent this way, **reuse that agent's already-published flex template** — no new library, retriever, or template. Copy the subagent + action, point at the same `generatePromptResponse://<Template>`, done.

**Which one do you have?** If someone connected the library in the builder UI, you'll see the bot-level `knowledge:` block — that's the binding, and it's enough on its own for the agent to ground answers in that library with citations. The template/retriever path is the alternative for agents wired purely in Agent Script without touching the builder's data-library picker. They are not mutually exclusive; an agent can carry the `knowledge:` block AND route a subagent to a retriever-backed template.

> **⚠️ Correction note (do not repeat the old mistake):** prior text said "there is NO bot-level ADL binding" and "connects to an agent purely through a prompt template — never through a bot-level setting." That was **false** — the builder's `knowledge:` block is exactly a bot-level binding. Both paths are valid.

## Facts (verified)
- Data-library SObjects (`AiDataLibrary`, `EinsteinRetriever`, `GenAiDataLibrary`, `EinsteinDataLibrary`, `LibraryFolder`, …) are **NOT SOQL-queryable** — every probe returns `INVALID_TYPE`. Don't try to query the library; inspect the **template** instead (`GenAiPromptTemplate` metadata) to find the retriever reference.
- The retriever reference lives in the template's `<templateDataProviders>` as `invocable://getEinsteinRetrieverResults/<RetrieverName>` and in the body as `{!$EinsteinSearch:<RetrieverName>.results}`. That `<RetrieverName>` (e.g. `KA_ALL_KBA_1Cx_Lhx69f54148`) is the data library's index.
- The template is `type = einstein_gpt__flex`, `visibility = Global`, `status = Published`. Because it's Global/Published, multiple agents can target it simultaneously.
- Citations / "show resources" come from the **action's `citations` output**, not from a template flag (`isCitationEnabled` can even be false on the template). The subagent surfaces sources when the action returns `citations`.

## How to add the FAQ capability to an agent

### 1. Find the source template + retriever
Read the reference agent's `.agent` for its FAQ action target, then read that template's metadata:
```bash
sf project retrieve start --json --metadata GenAiPromptTemplate:<TemplateName> --target-org <org>
```
Confirm `type einstein_gpt__flex`, `status Published`, and note the `<referenceName>EinsteinSearch:<RetrieverName></referenceName>`. That's the ADL you're reusing.

### 2. Add the router route
In `start_agent`, add both an instruction and a transition action. Route **only general/how-things-work questions** to FAQ — never the member's own account records:
```
| Route to GeneralFAQ ONLY for GENERAL questions about <domain>'s plans, benefits, coverage, policies, procedures, or how things work. Never route to GeneralFAQ for the member's OWN <records>, statuses, or account-specific details — those go to <the records subagent>.
...
go_to_GeneralFAQ: @utils.transition to @subagent.GeneralFAQ
```

### 3. Add the GeneralFAQ subagent (copy verbatim from the reference agent)
```
subagent GeneralFAQ:
    label: "General FAQ"
    description: "Answers members' general questions by searching knowledge articles ..."
    reasoning:
        instructions: ->
            | Your job is solely to answer questions about <domain> ... by searching knowledge articles.
            | If the question is too vague, ask a clarifying question.
            | If you cannot answer even after clarifying, ask if they want to escalate to a live specialist.
            | Never provide generic information unless retrieved from knowledge articles.
            | Include sources in your response when available, otherwise proceed without them.
        actions:
            Answer_Questions_with_KBAs: @actions.Answer_Questions_with_KBAs
                with "Input:User_Query" = ...
                with outputLanguage = ...
                with citationMode = ...
                with isPreviewOnly = ...

    actions:
        Answer_Questions_with_KBAs:
            label: "Answer Questions with KBAs"
            description: "Finds resources to answer the user's questions with KBA answers"
            target: "generatePromptResponse://<SharedFlexTemplate>"
            inputs:
                "Input:User_Query": string   # required
                outputLanguage: string       # optional
                citationMode: string         # optional
                isPreviewOnly: boolean        # optional
            outputs:
                promptResponse: string        # is_displayable: True
                generationId: string
                citations: object             # complex_data_type_name: "@apexClassType/AiCopilot__GenAiCitationOutput"
```
The `citations` output (that exact `@apexClassType/AiCopilot__GenAiCitationOutput` type) is what powers "show resources."

### 4. Validate, publish, activate
```bash
sf agent validate authoring-bundle --json --api-name <Agent>
sf agent preview start --json --use-live-actions --authoring-bundle <Agent>   # confirm it routes to GeneralFAQ and the knowledge action fires
sf agent publish authoring-bundle --json --api-name <Agent>
sf agent activate --json --api-name <Agent>
```

## Verify
- Preview: a general "how does X work" question routes to `GeneralFAQ`, the knowledge action invokes, and (if the library has matching articles) a grounded answer with citations comes back.
- The agent shares the **same** retriever/library/domain as the reference agent because it targets the same published template.

## The bot-level `knowledge:` path (builder-connected libraries)

If the library was connected via the Agentforce Builder's data-library picker, the binding is the `knowledge:` block on the agent — you generally **don't hand-author it**; you select the library in the UI and re-publish/activate the agent. If you retrieve the `.agent` afterward you'll see the block appear. Points to remember:

- `rag_feature_config_id: "ARFPC_…"` is generated by the platform for the chosen library — treat it as opaque. It maps to an internal AiRagFeatureConfig; there is no supported public read endpoint for its contents in these orgs, so don't block on "what does the id point to." What it points to is *the data library you selected in the UI*.
- `citations_url` must be your org's Lightning base domain so "show resources" links resolve.
- `citations_enabled: True` is what makes the agent surface citations for knowledge-grounded answers at the bot level (distinct from the action-output `citations` in the template path).
- Because this is a bot-level setting, it applies across the agent's knowledge answering — you don't also need a per-subagent retriever template just to get grounded FAQ answers from that library. You can still add a `GeneralFAQ` subagent for routing/instruction control, but the grounding itself flows from the `knowledge:` binding.
- **Editing it in metadata is fragile** — the id is org-specific and builder-owned. Prefer connecting/disconnecting the library in the builder over editing the block by hand, then retrieve to capture the resulting YAML.

## Gotchas
- **A bot-level ADL binding DOES exist** — the builder's `knowledge:` block (`rag_feature_config_id` / `citations_url` / `citations_enabled`). If someone connected the library in the UI, that block is the connection. The template/retriever reference is a *separate, additional* way to reach a library, not the only way.
- **Reuse, don't recreate.** Same library = same published flex template. Creating a new template/retriever would make a *different* library connection.
- **The library must actually contain relevant articles.** Reusing another agent's template reuses its *article corpus*. If that library holds, say, banking KBAs and your agent is health-insurance, the FAQ will correctly answer "no matching article" for health questions until health KBAs are published **into that same library**. Wiring being correct ≠ content being present.
- **Citations come from the action output**, not a template toggle — keep the `citations` output on the action.
- **Route narrowly.** FAQ is for general/policy/how-things-work questions only; the member's own records go to the records subagent. Make that explicit in both the router and the FAQ instructions.
