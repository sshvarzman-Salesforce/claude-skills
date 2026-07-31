# Grounding Service Assistant with Topics & Topic Strategy

Source: "Grounding Service Assistant with Topics [Extract]" — a compiled extract covering the "Grounding Service Assistant with Topics" help article and the "Topic Strategy in Service Assistant" help article. Kept here as supplementary grounding — general topic/instruction-writing guidance that underlies the subagent generator's design rules.

## Writing Topics

### Center topics around real-world customer issues
- Provide precise, distinct labels that specify the exact case type, e.g., "Return Request," to help Service Assistant accurately categorize the case and form initial plan steps.
- Keep topics specific to a singular case category. Instead of combining concepts into a topic like "Returns and Exchanges," separate into distinct topics: "Returns" and "Exchanges."
- Keep topics broad enough to serve as meaningful categories, but avoid generic buckets. "Account Issue" or "Customer Issue" are too broad because they can cover a wide range of issues.
- Don't create topics that describe features Service Assistant is already built to perform. A topic titled "Case resolution assistance," "Draft Service Plan," or "Resolve Case" prevents Service Assistant from accurately categorizing cases that have specific issues.

### Provide descriptions and scopes that capture case subtypes and variations
Use a single high-level topic for a wide range of related issues by explicitly listing variations and keywords in the topic's Description and Scope fields.

Example — "Transaction Decline":
| Topic Part | Example |
|---|---|
| Label | Transaction Declined |
| Description | Guide service reps in helping customers resolve declined credit card transactions. Questions are related to authorization failures, including declining reason codes such as insufficient funds, suspected fraud, incorrect card details, travel blocks, and daily spending limits. |
| Scope | Your job is to assist service reps in identifying the reasons behind declined transactions and providing the necessary steps to either allow the charge or secure the customer's account. You must not handle inquiries outside of declined transactions and account security. |

Example — "Processing Returns":
| Topic Part | Example |
|---|---|
| Label | Processing Returns |
| Description | Guide service reps through processing a customer's return request, including verifying eligibility and initiating the return in the system. Questions are related to return requests, which includes proof of return, return windows, product condition, and refund status. |
| Scope | Your job is to assist service reps in processing customer return requests. This includes verifying return eligibility based on purchase date, item condition, and applicable return policies. It also includes identifying the reason for the return, determining whether a refund, exchange, or store credit applies, and guiding reps through the steps to initiate, approve, or escalate a return as needed. You must not handle inquiries outside of returns. |

When you encompass different subtypes in a description, use instructions to document the workflow process for each subtype using conditional language. Alternatively, to limit manual-transcription effort across many subtypes, leverage knowledge grounding to add subtype-specific information directly from articles to the service plan — with knowledge grounding, instructions don't need as much detail and can be broader.

### Don't write agent-function instructions
Don't create instructions that direct Service Assistant to execute its built-in reasoning, e.g.:
- "Summarize the case."
- "Analyze the case details to provide resolution guidance."
- "Draft a service plan based on the case details."
- "Use knowledge articles to create the plan."

Service Assistant performs these tasks automatically — instructions should instead document specific business processes and service policies.

### Don't combine multiple steps into a single instruction
Each instruction outlines a singular task or process required for resolving the issue.

Incorrect (multiple steps combined):
> Search the Authorization Log in the system using the card details to identify the system Response Code. Take the appropriate action based on the code: if Suspected Fraud, follow the Fraud Verification Script...; if International Restriction, check if a travel notice is on file...

Correct (broken into distinct instructions):
1. Search the Authorization Log in the system using the card details to identify the system Response Code.
2. If the response code is Suspected Fraud, follow the Fraud Verification Script. Read the merchant name and amount to the customer, and if they confirm it is valid, remove the temporary block.
3. If the decline is International Restriction, check if a travel notice is on file. If no notice exists, verify the customer's location and add a Travel Note to the account to allow future charges in that region.

### Don't tell the agent to search your knowledge articles or use actions
- Don't reference Agentforce actions in instructions — actions aren't supported in Service Assistant. For automation in service plans, use quick actions instead.
- Service Assistant uses Agentforce Data Libraries to create plan steps automatically — creating instructions to reference the knowledge base isn't needed.
- Don't include statements like "Use the Answer Questions with Knowledge action" in instructions — the action isn't supported in Service Assistant; all knowledge base steps are created by the data library.

## Topic Strategy in Service Assistant

### Topic Granularity
The detail in your instructions depends on your use cases and whether your company uses knowledge grounding through Agentforce Data Libraries.

- **Without knowledge grounding** (no articles for an issue): you must create detailed topics that specify the processes to resolve the issue manually — write these for your priority issue types, and cover variations within a single topic using conditional language ("If..., then...", "When..., then...", "Once you have...").
- **With knowledge grounding**: you don't need a granular topic for every issue type/subtype. Focus on high-level issue types (e.g., "billing dispute," "transaction declined," "payroll change") and use the topic description to encompass subtypes. One topic can then serve a wide range of articles covering different processes.

Service Assistant relies on the Subject and Description fields (text/string fields only) to review case details and match a topic, then searches for and creates plan steps directly from the relevant knowledge article(s) via your Service AI Grounding configuration. Other fields like picklists aren't used for this matching — only text/string field content.

### Structuring Topics with Knowledge Grounding
When using knowledge grounding, create topics with 5–7 instructions that outline the general resolution process — you don't need multiple granular instructions per possible subtype, since subtypes are already defined in the topic's description.

Instructions serve as a general framework describing the overall workflow for any case in that category. Standard procedures (e.g., authenticating the customer, identifying the system response code) get their own instruction; a later instruction can say "execute the corresponding standard procedure" to state the goal (removing blocks, clearing flags, advising the customer) without spelling out how — Service Assistant pulls the granular procedural detail from the knowledge articles automatically.

Example — "Transaction Decline" with knowledge grounding:
| Topic Part | Example |
|---|---|
| Label | Transaction Decline |
| Description | Assist service reps in helping customers resolve declined credit card transactions. Questions are related to authorization failures, including declining reason codes such as insufficient funds, suspected fraud, incorrect card details, travel blocks, and daily spending limits. |
| Scope | Your job is to assist service reps in identifying the reasons behind declined transactions and providing the necessary steps to either allow the charge or secure the customer's account. You must not handle inquiries outside of declined transactions and account security. |
| Instruction 1 | Make sure the customer has provided the required authentication information: Full Name, Last 4 digits of the card, and Answer to Security Question. Ask the customer to provide the specific details of the declined attempt, including the merchant name, transaction amount, and date of attempt. |
| Instruction 2 | Check the "Available Credit" and "Account Balance" against the transaction amount. Confirm the account is not in arrears or over the credit limit. Verify if the "Card Lock" or "Freeze" feature is currently active in the customer's profile. |
| Instruction 3 | Search the Authorization Log in the system using the card details. Locate the specific decline entry to identify the system Response Code. |
| Instruction 4 | Based on the identified response code (such as NSF, Suspected Fraud, International Restriction, Invalid CVV, or Card Status), execute the corresponding standard procedure to remove temporary blocks, clear fraud flags, or advise the customer on the required next steps to allow the transaction. |
| Instruction 5 | After resolving the decline, send the customer a "Transaction Status Update" notification via email confirming that the block has been lifted or outlining the next steps required. |

### Additional Guidelines
- Service Assistant automatically retrieves relevant articles based on case details and assigned topic — you don't need to add the Answer Questions with Knowledge action to topics, or write instructions that tell it to search the knowledge base. Knowledge retrieval is handled automatically by the Agentforce Data Libraries.
- **Expect summarized knowledge steps.** Service Assistant currently summarizes the information from knowledge articles to generate a service plan, including step-by-step instructions in the article itself. As a result, exact procedural details might not always appear in the plan verbatim — reps may need to consult the article via the Sources section of the component for specific guidance.
- If referencing a specific knowledge article is a mandatory resolution step, you can write an instruction that explicitly states to review that specific article.
