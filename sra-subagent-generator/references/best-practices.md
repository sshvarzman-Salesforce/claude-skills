# Agentforce Service Assistant — Subagent Best Practices

Source: "Agentforce Service Assistant Subagent Best Practices" (@salesforcedocs, last updated Jun 30, 2026). Full guidance lives in the Help article "Grounding Service Assistant with Subagents" — this file summarizes it for grounding purposes.

## Grounding with Subagents and Instructions

Service Assistant gives specific and detailed guidance to service reps so they can resolve issues. To make sure the resolution guidance is accurate and specific, create subagents and instructions that clearly detail your company policies for resolving issues.

Each subagent must represent a specific issue type you want Service Assistant to resolve, like processing returns or disputing a bill. The subagent's classification description and scope are used to match the subagent with the conversation using the call transcript. The subagent's instructions create the initial steps of the service plan. The categorization details are also used to search for and add knowledge information to plan steps.

Because subagents play a key role in service plans, define two to three issue types you want to test, then follow the guidelines below. A small, focused set makes setup and testing easier.

## Required Standard Subagents

To enable Service Assistant's reasoning and support capabilities, you must add either the General CRM or General FAQ subagent. These extend the Assistant's conversational abilities beyond the immediate conversation data. You can add both.

- **General CRM:** Enables Service Assistant to answer service reps' questions using CRM data — identify and summarize records, answer queries, aggregate data, find and query objects, update records, and draft/refine emails. By default it contains: Draft or Revise Email, Get Record Details, Answer Questions with Knowledge, Query Records, Extract Fields And Values From User Input, Query Records with Aggregate, Update Record, Get Activity Details, Identify Record by Name.
- **General FAQ:** Enables Service Assistant to answer questions based on knowledge articles, via the Answer Questions with Knowledge action and the data library assigned to the agent in Agentforce Builder.

## General Subagents and Topic Switching

When a service rep asks a question that deviates from the current plan context, Service Assistant: (1) pauses the current plan logic, (2) switches to the relevant general subagent or searches the knowledge base to generate an answer, (3) returns to the original subagent (topic switch) or continues the service plan (knowledge question answered). Same logic applies mid-call — e.g., a refund request that becomes a return/exchange triggers a switch to the appropriate subagent.

## Subagent Guidelines

| Guideline | Details |
|---|---|
| Use specific, distinct subagent names | Precise labels for the exact issue type, e.g., "Return Request" or "Credit Card Declined." Avoid catch-alls like "Case Resolution Assistant" or "Customer Assistance" — too broad to match issues accurately. |
| Provide encompassing subagent descriptions | Use a single high-level subagent ("Billing Dispute," "Transaction Declined") for a range of related issues by explicitly listing variations and keywords in the description. Incorporate the wording customers actually use. You don't need separate subagents per variation once they're defined in the description. |
| Define the scope and set boundaries | The scope tells the agent what it can and can't do. Example: *"Your job is to assist service reps in identifying the reasons behind declined transactions and providing the necessary steps to either allow the charge or secure the customer's account. You must not handle inquiries outside of declined transactions and account security."* |
| Define mandatory steps | Make mandatory first steps explicit with language like "As a first step..." or "You must first...". For any step required in every plan, use language such as "Always find this step in a plan." |
| Use clear, conditional statements | Include conditional language for every scenario that can occur while working a case, so the agent has what it needs to decide what belongs in the plan. |
| Don't tell the agent to review the knowledge base | Knowledge retrieval and grounding happens automatically through Agentforce Data Libraries. If reviewing a specific article is a mandatory step in the resolution workflow, you can explicitly instruct that. |

## Subagent Instruction Methods

Instructions typically document a single resolution step, but Service Assistant's built-in reasoning can break a multi-step instruction into individual steps — grouping related tasks into one workflow-style instruction instead of writing a separate instruction per step.

### Workflow-Based Instructions
Example: *"Make sure the customer has provided the required information, including a valid return date, customer name, and receipt or order number. After you have the required information, confirm the purchase in the return management system. In addition, send an email to the customer that the information is complete and valid."*

### Knowledge Grounding Instructions
When using knowledge grounding, write 3–5 broad instructions that outline the resolution process at a high level rather than every subtype. Each instruction can cover multiple tasks without prescribing how to execute them — e.g., "...execute the corresponding standard procedure to remove temporary blocks, clear fraud flags, or advise the customer on next steps." Service Assistant pulls the granular "how-to" detail directly from the knowledge article at runtime, so each plan step reflects the specific procedure for the situation on the call.

## Worked Examples

### Example: Credit Card Declined
- **Topic Name:** Credit Card Declined
- **Classification Description:** Assist service reps in helping customers resolve declined credit card transactions. Questions are related to authorization failures, including declining reason codes such as insufficient funds, suspected fraud, incorrect card details, travel blocks, and daily spending limits.
- **Scope:** Your job is to assist service reps in identifying the reasons behind declined transactions and providing the necessary steps to either allow the charge or secure the customer's account. Make sure they gather the correct transaction details, verify account ownership, and follow all standard company procedures. You must not handle inquiries outside of declined transactions and account security.
1. Make sure the customer has provided the required authentication information: Full Name, Last 4 digits of the card, and Answer to Security Question. This step must always be in a plan for cases dealing with financial data.
2. Ask the customer to provide the specific details of the declined attempt, including the Merchant Name, Transaction Amount, and Date of Attempt.
3. Check the "Available Credit" and "Account Balance" against the transaction amount. Confirm the account is not in arrears or over the credit limit.
4. Examine the account for any active "Suspected Fraud" flags or blocks. Clear the flag only after the customer explicitly verifies the transaction details you read back to them.
5. Verify if the "Card Lock" or "Freeze" feature is currently active in the customer's profile settings. Direct the customer to the mobile app to deactivate this setting if found.
6. Search the Authorization Log in the system using the card details. Locate the specific decline entry to identify the system Response Code.
7. If the response code indicates "NSF" or "Credit Limit Exceeded," review the current available credit. Advise the customer that a payment is required to free up the line of credit before the transaction can proceed.
8. If the response code is Suspected Fraud, follow the Fraud Verification Script. Read the merchant name and amount to the customer. If they confirm it is valid, remove the temporary block and ask them to retry the transaction.
9. If the decline is International Restriction, check if a travel notice is on file. If no notice exists, verify the customer's location and add a Travel Note to the account to allow future charges in that region.
10. If the decline is Invalid CVV or "Invalid Expiration Date," advise the customer to check the physical card and re-enter the correct numbers. Do not ask them to read the CVV to you.
11. If the decline reason is Card Status: Inactive or Closed, check if the customer has activated their new card. If the card is closed, inform them that the transaction cannot be processed and check for eligibility to reopen or reissue.
12. Always be sure to thank the customer for choosing our company and provide a link to our survey on the service to help improve future assistance.
13. After resolving the decline, send the customer a "Transaction Status Update" notification via email confirming that the block has been lifted or outlining the next steps required.

### Example: Processing Returns
- **Topic Name:** Processing Returns
- **Classification Description:** Assist service reps in helping customers navigate the return process, including eligibility checks, return labels, refunds, and exchanges. Questions are related to return requests, which includes proof of return, return windows, product condition, and refund status.
- **Scope:** Assist service reps with customer questions related to returns processing. Provide the best steps using the instructions to resolve this inquiry.
1. Make sure the customer has provided the required information: Order Number, Item Name, and Reason for Return. This step is required to locate the purchase in the system.
2. Ensure all returns comply with the 30-day policy window unless an override is authorized by a manager.
3. If the customer provides the Order Number, search the Order Management System (OMS). If the purchase cannot be found, ask for the email address used at checkout to locate the transaction.
4. Check the "Order Date." If the order was delivered more than 30 days ago, inform the customer that the item is outside the return window. If it is within 30 days, proceed to condition verification.
5. Check that the product is in the right condition to be returned. Ask the customer if the item is "unworn and in original packaging." If the item is damaged or worn, inform them that a partial restocking fee may apply.
6. If the return is approved, generate a prepaid shipping label in the system. Verify the customer's current email address before sending the label.
7. Ask the customer if they prefer a refund to the original payment method or store credit. If they choose store credit, advise them that the funds will be available immediately upon receipt of the return scan.
8. If the customer cannot print the label, offer to mail a physical label to their address or provide a QR code they can show at the shipping carrier's drop-off location.
9. If the customer is unsatisfied with the return policy or the restocking fee, offer to raise the issue to a manager. Document the customer's specific concerns in the case notes.
10. Always be sure to thank the customer for choosing our company and provide a link to our survey on the service to help improve future assistance.
11. Always send the customer the "Return Instructions" email, which includes the tracking number, packing guidelines, and the generated shipping label.

### Example: Travel Documentation
- **Topic Name:** Travel Documentation
- **Classification Description:** Assist service reps in helping customers navigate the visa application process, including required documents, application procedures, document validity, submission process, processing times, and embassy contact information.
- **Scope:** Your job is to assist service reps in providing customers with the visa application process and related travel documents. Make sure they have all the right documents, information, and follow all the rules and procedures. You must not provide legal advice or handle inquiries outside of visa applications.
1. If the customer has all the required documents, verify their validity and completeness in the verification portal.
2. Always check if the customer needs a visa and vaccinations for their destination.
3. For questions about the submission process, tell the customer where and how to submit the application both in the company's travel verification portal and through the destination country's visa website. Always include a link to the official embassy website for the destination country for detailed information and application procedures.
4. When you have confirmed the visa requirements, always provide the customer with a checklist of all required documents such as a passport, port entry forms, visa application form, recent passport photos, and proof of travel.
5. If the destination country requires additional documents such as a letter of invitation or proof of financial means, inform the customer and provide guidance on how to obtain these.
6. Provide travel tips and advice on what to expect during the visa interview, if required.
7. Always be sure to thank the customer for choosing our company and provide a link to our survey on the service to help improve future assistance.
8. Always send the customer our submission processes for travel documents.
