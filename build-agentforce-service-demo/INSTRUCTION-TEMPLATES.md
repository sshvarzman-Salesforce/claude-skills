# Instruction Templates by Pattern

Copy-paste these templates when writing subagent instructions. Choose the pattern that matches your use case.

**Source:** Alberto's topic strategy + Chad's demo patterns

---

## Pattern 1: KB-Grounded Subagent (3-5 Instructions)

**Use when:** Knowledge article exists with full procedural detail

**Instruction count:** 3-5 high-level only  
**Detail level:** Framework outline (KB fills gaps at runtime)

### Template

```
Instruction 1 (Sort: 1): Authenticate & Gather Context
[Authenticate field 1], [authenticate field 2], and [authenticate field 3]. Ask for 
[specific detail 1], [specific detail 2], and [date/time context].

Instruction 2 (Sort: 2): Verify & Check Status
Check [system field 1] and [system field 2] against [condition]. Confirm [status 
requirement]. Verify if [flag/setting] is currently active in [location].

Instruction 3 (Sort: 3): Identify Root Cause
Search [system/log] using [lookup fields]. Locate the [record type] to identify 
the [classification field].

Instruction 4 (Sort: 4): Execute Resolution
Based on the identified [category/code/condition] (such as [type A], [type B], 
[type C]), execute the corresponding standard procedure to [goal 1], [goal 2], 
or advise the customer on the required next steps to [outcome].

Instruction 5 (Sort: 5): Confirm & Close
After resolving [issue], send [notification type] via [channel] confirming [outcome] 
or outlining the next steps required.

[Optional] Instruction 6 (Sort: 6): Survey
Thank the customer for their time and send the post-interaction survey link.
```

---

### Example: Transaction Declined (KB-Grounded)

```
Instruction 1: Make sure the customer has provided the required authentication information: 
Full Name, Last 4 digits of the card, and Answer to Security Question. Ask the customer 
to provide the specific details of the declined attempt, including the merchant name, 
transaction amount, and date of attempt.

Instruction 2: Check the "Available Credit" and "Account Balance" against the transaction 
amount. Confirm the account is not in arrears or over the credit limit. Verify if the 
"Card Lock" or "Freeze" feature is currently active in the customer's profile.

Instruction 3: Search the Authorization Log in the system using the card details. Locate 
the specific decline entry to identify the system Response Code.

Instruction 4: Based on the identified response code (such as NSF, Suspected Fraud, 
International Restriction, Invalid CVV, or Card Status), execute the corresponding 
standard procedure to remove temporary blocks, clear fraud flags, or advise the customer 
on the required next steps to allow the transaction.

Instruction 5: After resolving the decline, send the customer a "Transaction Status Update" 
notification via email confirming that the block has been lifted or outlining the next 
steps required.
```

---

## Pattern 2: No-KB / Action-Driven Subagent (6-10 Instructions)

**Use when:** No knowledge article, or action-heavy flow

**Instruction count:** 6-10 detailed  
**Detail level:** Full procedural detail (spell everything out)

### Template

```
Instruction 1 (Sort: 1): Get Customer Profile
[Action-driving text for profile lookup - mentions action name if applicable]

Instruction 2 (Sort: 2): Authenticate & Verify
Make sure the customer has provided [required field 1], [required field 2], and 
[required field 3]. Verify [eligibility condition] and confirm [status requirement].

Instruction 3 (Sort: 3): Gather Issue Details
Ask the customer for [specific detail 1], [specific detail 2], and [specific detail 3]. 
[If applicable:] Search [system/log] using [lookup fields] to locate [relevant record].

Instruction 4 (Sort: 4): Identify Root Cause
Check [system field 1] and [system field 2] against [condition]. Confirm [status check]. 
Locate the [record type] to identify the [classification field].

Instruction 5 (Sort: 5): Execute Resolution
Based on the identified [category/code/condition]:
- If [condition A], then [action A: specific steps]
- If [condition B], then [action B: specific steps]
- If [condition C], then [action C: specific steps]

Instruction 6 (Sort: 6): Apply Concession (if applicable)
[Action-driving text for concession/perk/benefit based on customer tier or issue severity]

Instruction 7 (Sort: 7): Generate Deliverable
[Action-driving text for creating output — boarding pass, confirmation, RMA, etc.]

Instruction 8 (Sort: 8): Send Confirmation
Send [notification type] via [channel] confirming [outcome details] and [next steps if any].

[Optional] Instruction 9 (Sort: 9): Survey
Thank the customer and send the post-interaction survey link.

Instruction 10 (Sort: 10): Render Backstop (if using CLT cards)
When an action has a renderable output, display the complete action output to the user 
without summarizing, modifying, or omitting any content. The output is always renderable; 
always use show_command. Do NOT convert the output to plain text.
```

---

### Example: Credit Card Declined (No-KB, Full Detail)

*(See `references/alberto-best-practices.md` for full 13-instruction example)*

**Key characteristics:**
- Every condition spelled out (NSF → advise payment, Fraud → verify transaction, etc.)
- Every verification step explicit (check card lock, search auth log, verify CVV, etc.)
- No KB to fill gaps, so instructions cover ALL policies and procedures

---

## Pattern 3: Hybrid (Action-Driven + KB-Assisted)

**Use when:** Most flow is actions, but one or two steps reference knowledge

**Instruction count:** 6-8 (mix)  
**Detail level:** Detailed for actions, high-level for KB steps

### Template (Retail Return Pattern)

```
Instruction 1 (Sort: 1): Get Customer Profile
When a customer reaches out about a product issue, immediately call [Profile Action] 
to retrieve their customer profile and loyalty tier. Display the profile card.

Instruction 2 (Sort: 2): Look Up Order
After identifying the customer, call [Order Action] with the order number the customer 
provides (or their most recent order if not mentioned). Display the order card.

Instruction 3 (Sort: 3): Troubleshoot (KB-Assisted)
When the customer describes a product issue, call [Troubleshooting Action] with the 
product name and issue description. Display the troubleshooting card. Ask: "Would you 
like to try these steps, or would you prefer to proceed with a warranty replacement?"

Instruction 4 (Sort: 4): Process Return (Action)
If troubleshooting does not resolve the issue, call [Return Action] with the order 
number and issue details. Display the return resolution card with RMA number and 
replacement order.

Instruction 5 (Sort: 5): Apply Concession (Action)
Based on the customer's loyalty tier from their profile, immediately call [Concession 
Action]. Display the concession card showing the store credit amount and delivery 
upgrade.

Instruction 6 (Sort: 6): Send Confirmation (Action)
At the end of the return flow, call [Email Action] with all return details including 
RMA number, replacement order, and concession applied. Confirm to the customer they 
will receive email confirmation.

Instruction 7 (Sort: 7): Render Backstop
When an action has a renderable output, display the complete action output to the user 
without summarizing, modifying, or omitting any content. The output is always renderable; 
always use show_command. Do NOT convert the output to plain text.
```

---

## Universal Closing Phrases

**Classification Description opening:**
```
"Guide service reps in helping customers resolve..."
```

**Scope closing:**
```
"You must not handle inquiries outside of [subagent topic]."
```

**Instruction temporal connectors:**
- "**First**, retrieve..."
- "**After identifying** the customer..."
- "**If troubleshooting does not resolve**..."
- "**Based on the customer's loyalty tier**..."
- "**Once you have confirmed**..."
- "**When the system shows**..."

**Final instruction (concluding action):**
```
"Send [notification] confirming [outcome] and [next steps]."
"Update case status to Resolved and provide the customer with [deliverable]."
"Confirm the outcome with the customer, including [details] and [next steps]."
```

---

## Conditional Language Patterns

**For branching logic:**
```
"If [condition A], then [action A]"
"When [trigger], execute [procedure]"
"Once you have [prerequisite], proceed to [next step]"
"Based on [field value], [decision logic]"
```

**Examples:**
- "If the response code indicates NSF or Credit Limit Exceeded, review the current available credit."
- "When the issue involves a direct deposit routing error, verify the customer's bank account information."
- "Once you have confirmed the enrollment record, determine the available correction path."
- "Based on the type of discrepancy reported, locate the relevant payroll detail."

---

## Mandatory Steps Language

**For steps that MUST happen:**
```
"As a first step, [action]..."
"You must first [action]..."
"This step must always be in a plan for cases dealing with [data type]."
"Always find this step in a plan."
"Make sure the customer has provided [requirements]. This step is required to [reason]."
```

**Example:**
```
Make sure the customer has provided the required authentication information: Full Name, 
Last 4 digits of the card, and Answer to Security Question. This step must always be 
in a plan for cases dealing with financial data.
```

---

## Never-Say Phrases

**Do NOT include these in instructions:**

❌ "Search the knowledge base"  
❌ "Review knowledge articles"  
❌ "Use the Answer Questions with Knowledge action"  
❌ "Create a service plan"  
❌ "Draft service plan steps"  
❌ "Summarize the case"  
❌ "Analyze the case details"

**Why:** Service Assistant does these automatically. Instructions should document business processes, not agent functions.

---

## Action-Driving Language (For Demo Actions)

**When referencing Agent Actions:**
```
"Call [Action Name] with [input fields]."
"Immediately call [Action Name] to [purpose]."
"After [prerequisite], call [Action Name] and display the [output card]."
```

**Examples:**
- "Call Get Customer Profile to retrieve their loyalty tier and purchase history."
- "After identifying the customer, call Look Up Order with the order number."
- "Immediately call Apply Concession based on the customer's loyalty tier."

---

## Best Practices Checklist

When writing instructions, verify:

- [ ] Classification Description starts with "Guide service reps in helping customers resolve..."
- [ ] Scope ends with "You must not handle inquiries outside of..."
- [ ] One instruction = one standalone, actionable step (not bundled)
- [ ] Instructions are in chronological order (sort order enforces sequence)
- [ ] Temporal connectors used ("After...", "If...", "Based on...", "Once...")
- [ ] Conditional language for branches ("If A, then B")
- [ ] Mandatory steps use "must" or "required" language
- [ ] No "search KB" or "create plan" phrases
- [ ] Final instruction states concluding action
- [ ] Survey link included (if appropriate)
- [ ] Render backstop included (if CLT cards used)

---

## Related

- `BEST-PRACTICES.md` — Full rules for instruction writing
- `references/alberto-topic-strategy.md` — Topic strategy and instruction depth
- `references/alberto-best-practices.md` — 3 worked examples
- `SUBAGENT-TEMPLATE.md` — Framework for filling these out
