# Sample Output: Variance Analysis

> This is a sample output from `sra-config-analysis-shared` using a fictional topic configuration. It demonstrates the structure and depth of analysis the skill produces.

---

# Variance Analysis: Order Status & Tracking — Messaging Channel

**Date:** 2026-06-24
**Customer:** Acme Retail
**Agent:** Service Assistant (Version 8)
**Topic:** Order Status & Tracking
**Channel:** Messaging

## Executive Summary

This topic has **9 variance sources** (2 CRITICAL, 3 HIGH, 3 MEDIUM, 1 LOW). The primary variance drivers are: (1) the Lookup_Order action requires an Order Number but instructions tell the agent to "look up the order" without specifying where the number comes from, and (2) the refund eligibility check uses a 30-day window but no instruction tells the agent what to do when the order is on day 29 vs day 31.

---

## Variance Sources (Ranked)

### CRITICAL

#### V1: Action-Instruction Misalignment — Lookup_Order requires Order Number, instructions don't mention it

**Source:** Instruction 2 + Lookup_Order action config

**The Problem:**
Instruction 2 says: "Look up the customer's order and share the current status."
Lookup_Order action has: `Order_Number` (Required, Collect from user).

The instruction implies the agent can just "look up the order" — but the action requires the CSR to provide an Order Number via INPUT_FORM. If the customer said "where's my package?" without an order number, the agent tells the CSR to look it up, then the CSR sees a blank form with no guidance.

**Planner Impact:**
- Phase 2C scores Lookup_Order: Relevance=2, Input Availability=0 (no order number in context), Policy Alignment=2, Output Usefulness=2, Non-Substitution=2 → Score=8 → Executes
- But Input Availability should drop the score below 8 since the required input isn't available
- Variance: sometimes planner fires the action (CSR gets form), sometimes it asks for order number first (depending on how strictly it evaluates input availability)

**Test Case:**
| Input A | Input B | Expected: Same | Actual: Different |
|---------|---------|----------------|-------------------|
| "Customer wants order status, order #12345" | "Customer wants to know where their package is" | Both should reach order lookup | A fires action immediately; B may stall or present blank form |

**Severity:** CRITICAL — CSR gets an unexplained form or agent stalls with no recovery path.

---

#### V2: Refund Eligibility Boundary — No instruction for edge cases

**Source:** Instruction 4 + Check_Refund_Eligibility action

**The Problem:**
Instruction 4 says: "If the customer requests a refund, check eligibility. Orders over 30 days are not eligible."

Check_Refund_Eligibility returns `eligible: true/false` based on order date. But:
- No instruction for what to say when `eligible: false` (just "not eligible"? offer alternatives?)
- No instruction for orders at exactly 30 days (is day 30 eligible or not?)
- No instruction for orders with partial shipments (item A shipped day 5, item B shipped day 28)

**Planner Impact:**
The planner's Phase 2D (Response Formation) must generate a response for `eligible: false` — but the only grounded content is "orders over 30 days are not eligible." Different runs produce different responses:
- Run 1: "Unfortunately the order is past the 30-day refund window."
- Run 2: "The order isn't eligible for a refund. Would you like me to check exchange options?"
- Run 3: "I'm unable to process a refund for this order. Let me connect you with a supervisor."

None of these are "wrong" but they're inconsistent. Run 3 escalates unnecessarily.

**Severity:** CRITICAL — inconsistent customer experience on a high-emotion interaction (refund denial).

---

### HIGH

#### V3: Authentication assumed but not enforced

**Source:** Instruction 1

**The Problem:**
Instruction 1 says: "Verify the customer's identity before proceeding."
But no instruction defines:
- What "verify" means (name + email? order number? last 4 of card?)
- What to do if verification fails
- Whether to use the Verify_Customer action or just ask the CSR to confirm

**Severity:** HIGH — different CSRs interpret "verify" differently; agent may skip verification entirely on some runs if it classifies the utterance as CONT rather than a new procedural step.

---

#### V4: "Share the current status" — ambiguous output scope

**Source:** Instruction 2

**The Problem:**
After Lookup_Order returns, instruction says "share the current status." The action returns 12 fields (order date, items, tracking number, carrier, estimated delivery, ship date, address, payment method, subtotal, tax, shipping cost, total).

"Current status" could mean:
- Just the tracking status ("Shipped — in transit")
- Status + estimated delivery
- Full order summary (all 12 fields)

**Planner Impact:** The planner's groundedness rule says response must come from metadata/context — all 12 fields ARE available context. Without a constraint instruction, the LLM may dump all fields or select different subsets on different runs.

**Severity:** HIGH — inconsistent information density across runs.

---

#### V5: Channel-specific language without guard

**Source:** Instruction 5

**The Problem:**
Instruction 5 says: "If the customer needs to return an item, email them the return shipping label."

On Messaging channel, the agent can't email — it can only respond in chat. No channel guard on this instruction. Planner may attempt to fire an email action on a messaging session.

**Severity:** HIGH — wrong action attempted on messaging channel.

---

### MEDIUM

#### V6: Multiple orders — no disambiguation instruction

If customer has 5 recent orders and says "where's my order?", no instruction tells the agent whether to ask which one, show all, or pick the most recent.

#### V7: Tracking number format parsing

Customers paste tracking numbers in various formats (with/without spaces, with carrier prefix). Lookup_Order may or may not accept these. No input validation guidance.

#### V8: "Connect with a supervisor" — no escalation action configured

Instruction 6 says "if the customer is unsatisfied, offer to connect them with a supervisor" but no escalation action is attached to this topic.

---

### LOW

#### V9: "Your order" vs "the order" — persona inconsistency

Agent sometimes says "your order" (speaking to customer) vs "the order" (speaking to CSR). Persona rule says speak TO the CSR, but some instructions use customer-facing language.

---

## Real Case Walkthrough

**Sample case:** "Hi, I ordered a laptop 3 weeks ago and it still hasn't arrived. Order number 78432."

```
Turn 1: Topic classified → Order Status & Tracking
  Phase 2A: Scans PI → finds "verify identity" as first step
  Phase 2B: NEXT = verify_customer_identity
  ###RESPONSE: "Verify the customer's identity before looking up the order."

  Variance risk: PROACTIVE_MODE may skip verification because order number 
  is already available → jumps to Lookup_Order

Turn 2: CSR says "verified"
  CSR_SIGNAL: EXPLICIT_CONFIRM → step COMPLETE
  Phase 2B: NEXT = lookup_order
  Phase 2C: Tool score for Lookup_Order → Order_Number="78432" available → score ≥ 8
  Action fires → returns order details

Turn 3: Action result in context
  Phase 2D: Must "share the current status" — but which fields?
  ###RESPONSE: [varies across runs — see V4]
```

---

## Edge Cases

### Input Validation
1. Order number with leading zeros ("078432" vs "78432")
2. Customer provides tracking number instead of order number
3. Customer provides multiple order numbers in one message

### Data States
4. Order exists but has no tracking yet (pre-shipment)
5. Order was cancelled but customer doesn't know
6. Order delivered but customer says "not received"

### Integration Failures
7. Lookup_Order returns timeout → no instruction for retry or fallback
8. Carrier tracking API is down → order shows "shipped" but no tracking detail

---

## Test Cases (Mapped to Quality Goals)

| # | Goal | Test | Expected | Variance Risk |
|---|------|------|----------|---------------|
| TC1 | Determinism | Same order lookup 3x | Same fields shared each time | V4: output scope varies |
| TC2 | Exhaustivity | Refund request on day 31 | Denial + alternative offered | V2: no alternative instruction |
| TC3 | Atomicity | "Look up order and check refund" | Two separate steps, not one | May collapse into single action |
| TC4 | Tool Selection | Order # in conversation | Lookup_Order scores ≥ 8 and fires | V1: input availability scoring |
| TC5 | Step Advancement | CSR says "yep" after verification | EXPLICIT_CONFIRM → advance | Ambiguous — "yep" may be DATA_ONLY |
| TC6 | Self-Contained | Refund denial response | Includes reason + next steps | V2: varies across runs |

---

## Setup Issues

| Check | Status | Notes |
|-------|--------|-------|
| Lookup_Order input aligned with instructions? | ❌ NO | Instructions don't mention Order Number requirement |
| Escalation action attached? | ❌ NO | Instruction 6 references supervisor but no action exists |
| Channel guards on email instructions? | ❌ NO | Instruction 5 uses email language on messaging |
| Refund edge cases covered? | ❌ NO | No instruction for boundary dates or partial shipments |
| Authentication method defined? | ❌ NO | "Verify identity" is ambiguous |

---

## Recommendations

### P0 — Fix Before Production

1. **Add Order Number collection to instructions** — "Ask the customer for their order number before looking up status" OR remove "Collect from user" and let the agent extract from conversation.
2. **Define refund denial response** — "If not eligible, inform the customer of the 30-day policy and offer exchange or store credit as alternatives."
3. **Add channel guard to Instruction 5** — "On Email channel: send return label via email. On Messaging: provide return label link in chat."

### P1 — Fix Before Scale

4. **Define "share current status" scope** — "Share: tracking status, estimated delivery date, and carrier name. Do not share payment details unless asked."
5. **Add escalation action** — Wire a Transfer_To_Supervisor action or remove the instruction.
6. **Define authentication method** — "Verify by asking customer to confirm: full name + email on the order."

### P2 — Improve Quality

7. **Add multi-order disambiguation** — "If customer has multiple recent orders, ask which one by listing order dates and items."
8. **Add retry instruction for action failures** — "If order lookup fails, ask the customer to verify the order number and try once more."
