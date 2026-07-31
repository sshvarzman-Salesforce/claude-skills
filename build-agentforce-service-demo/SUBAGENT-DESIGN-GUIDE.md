# Subagent Design Guide — Combine vs Separate Decision

**When to use:** You have multiple knowledge articles or use cases and need to decide:
- ONE subagent covering all variations? OR
- MULTIPLE separate subagents?

**Source:** Alberto's design strategy (`references/alberto-design-strategy.md`)

---

## The Analysis Process

### Step 1: Identify the Core Workflow
For each knowledge article or use case, extract the high-level workflow:
- Authenticate
- Identify root cause
- Execute resolution procedure
- Confirm outcome
- Send notification

### Step 2: Compare Workflows
Ask: Do these articles follow the **same general sequence of steps** but differ only in:
- Root cause?
- Condition type?
- Subtype of the same problem?

**If YES → COMBINE into one subagent**

**Example:**
- "Credit Card Declined - Insufficient Funds"
- "Credit Card Declined - Suspected Fraud"
- "Credit Card Declined - Travel Block"

All follow: authenticate → check reason code → execute resolution → confirm

**RECOMMENDATION:** ONE subagent (Transaction Declined) covering all 3 subtypes

---

**If NO → KEEP SEPARATE**

**Example:**
- "Process Product Return" (authenticate → verify order → issue RMA → apply concession)
- "Process Product Exchange" (authenticate → verify order → check availability → create exchange order)

Different workflows, different outcomes, different data requirements.

**RECOMMENDATION:** TWO separate subagents

---

## The One-Sentence Test

**Ask:** Can I describe all these use cases with one sentence starting with "Guide service reps in helping customers resolve..."?

**Example 1 (Combine):**
✅ "Guide service reps in helping customers resolve declined credit card transactions, including insufficient funds, suspected fraud, travel blocks, incorrect card details, and daily spending limits."

**Example 2 (Don't Combine):**
❌ "Guide service reps in helping customers resolve declined credit card transactions and process product returns."
→ These are two fundamentally different topics. Split into 2 subagents.

---

## Recommendation Format (Always Present to User)

Before generating detailed subagent output, present this analysis:

```
I've analyzed your knowledge articles. Here's what I found:

Articles reviewed:
- [Article 1 title/topic]
- [Article 2 title/topic]

Workflow analysis:
- [Article 1] describes: [brief workflow]
- [Article 2] describes: [brief workflow]

RECOMMENDATION: [Combine into X subagent(s) / Keep as Y separate subagents]

REASONING:
[Articles 1, 2] share the same general workflow (authenticate → identify → resolve)
and differ only in [root cause]. These are variations of the same concept and should
be ONE subagent with subtypes listed in the description.

OR

[Article 1] describes [action type] while [Article 2] describes [different action].
These are fundamentally different workflows and should be SEPARATE subagents.

Proposed structure:
- Subagent Name: [Name]
  Covers: [variation 1, variation 2, variation 3]

Shall I proceed with this structure?
```

**DO NOT generate detailed instructions until user confirms structure.**

---

## Common Mistakes

### Mistake 1: Over-Fragmenting
Creating one subagent per tiny variation:
- ❌ "Insufficient Funds Decline" (separate subagent)
- ❌ "Fraud Decline" (separate subagent)
- ❌ "Travel Block Decline" (separate subagent)

**Fix:** ONE "Transaction Declined" subagent covering all 3 as subtypes

### Mistake 2: Generic Catch-Alls
Creating overly broad subagents:
- ❌ "Account Issues"
- ❌ "Customer Problems"
- ❌ "Payment Inquiries"

**Fix:** Break into specific categories (Credit Card Declined, Payment Method Update, Billing Address Change)

### Mistake 3: Combining Unrelated Processes
Mixing fundamentally different workflows:
- ❌ "Returns and Exchanges" (different workflows, different outcomes)
- ❌ "Password Reset and Account Unlock" (different security implications)

**Fix:** Separate subagents even if they seem thematically related

---

## Design Patterns from Alberto's Examples

### Pattern: Variations of One Workflow → ONE Subagent
**Example:** Transaction Declined
- Subtype 1: Insufficient Funds (execute: advise customer, offer payment plan)
- Subtype 2: Suspected Fraud (execute: verify customer, lift fraud flag)
- Subtype 3: Travel Block (execute: note travel dates, remove block)

**Workflow is identical** (authenticate → ID reason → resolve → confirm)
**Only the resolution procedure differs** by subtype

### Pattern: Different Outcomes → SEPARATE Subagents
**Example:** Returns vs Exchanges
- Return: customer wants refund (issue RMA → refund payment)
- Exchange: customer wants different item (check availability → create new order)

**Workflows diverge** after identification step
**Outcomes are fundamentally different** (money back vs new product)

---

## Worked Examples

### Example 1: Payroll Issues (COMBINE)

**Articles:**
- Missing Paycheck
- Direct Deposit to Wrong Account
- Overtime Calculated Incorrectly
- Incorrect Tax Deduction

**Workflow analysis:**
- All follow: verify employment → identify error type → locate discrepancy → initiate correction → confirm outcome
- Differences: error type only (missing payment vs routing error vs calculation error vs withholding error)

**Recommendation:** COMBINE into ONE "Payroll Issue" subagent

**Description:**
```
Assist service reps in helping employees resolve payroll discrepancies and payment 
concerns. Questions are related to payroll processing errors, including missing or 
late paychecks, incorrect direct deposit routing, overtime and hours miscalculations, 
incorrect tax withholdings, unauthorized or incorrect deductions, and year-end W-2 
discrepancies.
```

---

### Example 2: Benefits Issues (SEPARATE)

**Articles:**
- Benefits Enrollment Issue
- Benefits Claim Denied

**Workflow analysis:**
- Enrollment: confirm status → review elections → determine correction path → process correction
- Claim: verify coverage → review claim denial → identify reason → appeal or accept

**Workflows diverge:** Enrollment fixes election records; claims deal with coverage disputes

**Recommendation:** SEPARATE into TWO subagents
1. "Benefits Enrollment Issue"
2. "Benefits Claim Dispute"

---

## Quick Decision Tree

```
Start: Multiple articles/use cases to structure

↓
Do they share the SAME general workflow?
(e.g., authenticate → identify → resolve → confirm)

YES → Do they differ only in subtypes/conditions?
      (e.g., root cause, reason code, error type)
      
      YES → COMBINE into ONE subagent
            ↓
            List all subtypes in description
            
      NO → Different steps in the middle?
           ↓
           Are outcomes fundamentally different?
           (refund vs new product, enrollment vs claim)
           
           YES → SEPARATE subagents
           NO  → COMBINE (conditional instructions handle variations)

NO → SEPARATE subagents
     ↓
     Each gets its own workflow-specific instructions
```

---

## Testing Your Decision

After structuring, test with the **one-sentence test**:

✅ **Good (combine worked):**
"Guide service reps in helping customers resolve declined credit card transactions, including insufficient funds, suspected fraud, travel blocks, incorrect card details, and daily spending limits."

❌ **Bad (should have separated):**
"Guide service reps in helping customers with account issues including password resets, billing disputes, profile updates, and product returns."
→ These are 4 different workflows; split into 4 subagents.

---

## When in Doubt

**Default to COMBINING** if:
- Same workflow structure
- Differences are subtypes/conditions
- Knowledge articles exist (they'll fill the subtype-specific detail)

**Default to SEPARATING** if:
- Different outcomes
- Different data requirements
- Different escalation paths
- Different compliance/security implications

---

## Related

- `references/alberto-design-strategy.md` — Full reasoning-anchor model
- `references/alberto-best-practices.md` — 3 worked examples
- `BEST-PRACTICES.md` — Section on "One Subagent for Many Variations"
