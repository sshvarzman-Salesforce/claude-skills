---
name: connecting-agent-data-library
description: Connect an Agentforce Service Agent (ASA) to an Agentforce Data Library (ADL) so it can answer general FAQ questions from knowledge articles with citations ("show resources"). The connection is entirely at the prompt-template level via an Einstein retriever — there is NO bot-level ADL binding. Reuse one published flex template across agents to share the same library, retriever, citations, and Salesforce domain.
---

# Connecting an Agentforce Service Agent to a Data Library

## The one thing to understand

**An Agentforce Data Library connects to an agent purely through a prompt template — never through a bot-level setting.** There is no "attach data library to agent" field in the `.agent` file or `BotDefinition`. The wiring is:

```
subagent GeneralFAQ
   └─ action → generatePromptResponse://<FlexTemplate>
                   └─ template body references {!$EinsteinSearch:<RetrieverName>.results}
                   └─ templateDataProviders: invocable://getEinsteinRetrieverResults/<RetrieverName>
                          └─ the Einstein retriever IS the data library's search index
```

So to give an agent the **same** data library, citations, and Salesforce domain as another agent, you **reuse that agent's already-published flex template**. Nothing new to create — no new library, retriever, or template. Copy the subagent + action, point at the same `generatePromptResponse://<Template>`, done.

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

## Gotchas
- **No bot-level ADL binding exists.** If you're looking for a place to "attach the library to the agent," stop — it's the template's retriever reference.
- **Reuse, don't recreate.** Same library = same published flex template. Creating a new template/retriever would make a *different* library connection.
- **The library must actually contain relevant articles.** Reusing another agent's template reuses its *article corpus*. If that library holds, say, banking KBAs and your agent is health-insurance, the FAQ will correctly answer "no matching article" for health questions until health KBAs are published **into that same library**. Wiring being correct ≠ content being present.
- **Citations come from the action output**, not a template toggle — keep the `citations` output on the action.
- **Route narrowly.** FAQ is for general/policy/how-things-work questions only; the member's own records go to the records subagent. Make that explicit in both the router and the FAQ instructions.
