# Action Chaining with CLTs in SRA

How to build multi-step action chains where CLT cards render at each step in the Service Rep Assistant sidebar.

---

## How Chaining Works in SRA

The SRA planner executes actions in sequence based on:
1. **Topic instruction sort order** — determines the default step progression
2. **Conditional language in instructions** — "If X, then Y" lets the planner branch
3. **Action descriptions** — prerequisite language ("Before calling X, first call Y") enforces ordering
4. **Conversation context** — outputs from prior actions inform the next action's input resolution

Actions do NOT pass data forward via explicit input-to-output wiring. Instead, each action resolves its own inputs (typically via MessagingSession fallback) and the planner uses conversation context to decide what to run next.

---

## Chain Design Pattern

### Read-Only Actions Chain Reliably

Actions with `isConfirmationRequired: false` auto-execute in sequence. The planner runs one, sees the result, and proceeds to the next. CLT cards render at each step.

```
Get Customer Profile (read, auto) → Check Manifest (read, auto) → renders both cards
```

### Write Actions Break the Chain (Known Limitation)

Actions with `isConfirmationRequired: true` pause for rep confirmation. After the rep clicks "Confirm":
- **Expected:** planner resumes and runs the next action
- **Actual (current behavior):** planner sometimes treats confirmation as end-of-turn and stops

**NGS team is actively working on fixing this.** Until then, design around it.

---

## Topic Instruction Language for Chaining

### Template: Sequential Chain

```
Action Chain:
- Immediately run [Action 1] when [trigger condition].
- After [Action 1] completes, immediately run [Action 2].
- If [condition from Action 2 output], proceed to [Action 3] via the sidebar.
- After [Action 3] confirms, immediately proceed to [Action 4].
- Conclude by running [Action 5].
```

### Template: Conditional Chain

```
Action Chain:
- Run [Action 1] to check [condition].
- If [positive result], propose [Action 2] via the sidebar.
- If [negative result], inform the rep that [explanation] and stop.
- After [Action 2] completes, check eligibility for [Action 3].
```

### Key Phrases the Planner Respects

| Phrase | Effect |
|--------|--------|
| "Immediately run..." | Auto-execute without waiting for rep input |
| "After [X] completes..." | Sequence dependency — wait for prior action |
| "If [condition]..." | Conditional branching from action output |
| "...via the sidebar" | Reinforces card rendering over text narration |
| "Conclude by..." | Marks the final step in the chain |
| "Do not proceed until..." | Gating — pauses chain until condition met |

### Phrases to AVOID

| Phrase | Problem |
|--------|---------|
| "Proceed to step 3" | Planner may skip intermediate gating steps |
| "Next, do X" | Too vague — planner may reorder |
| "Run all actions" | Planner can't batch — it runs one at a time |
| "Refer to the knowledge base" | Does NOT trigger knowledge search |

---

## Workarounds for Post-Confirmation Chain Breaks

Until the NGS fix ships, use these patterns:

### 1. Instruction Reinforcement

Add explicit continuation language after every HiL step:

```
- After Pet Booking confirms successfully, DO NOT STOP. Immediately check 
  the customer's loyalty tier by running Loyalty Perk.
```

### 2. Segment the Chain

Accept that each HiL confirmation may end the turn. Design so each step stands alone:

```
Segment 1 (auto): Get Profile → Check Manifest (both CLTs render)
Segment 2 (HiL):  Pet Booking (rep confirms → record created)
Segment 3 (HiL):  Loyalty Perk (rep confirms → perk applied)
Segment 4 (HiL):  Generate Pass (rep confirms → pass generated)
```

If the planner doesn't auto-advance, the rep says "continue" or "what's next" and the planner picks up the next segment.

### 3. Front-Load CLTs

Put all read-only CLT actions first in the chain so the visual cards render before any HiL pauses. The rep sees the full picture, then confirms write actions one by one.

---

## Action Description Prerequisites

Each action's `@InvocableMethod` description can enforce ordering:

```java
// Good — tells planner when to run this action
@InvocableMethod(label='Pet Booking'
    description='Secures a pet cabin spot. Run this AFTER Check Pet Manifest 
    confirms a spot is available. Resolves Contact from messaging session.')

// Good — marks chain position
@InvocableMethod(label='Loyalty Perk'
    description='Checks loyalty tier and applies Pet Lounge pass for Gold/Platinum. 
    Run this AFTER Pet Booking succeeds.')
```

---

## Example: 5-Step Pet Travel Chain

```
Topic Instructions:

Action Chain:
- Immediately run Get Customer Profile when the conversation begins.
- Immediately run Check Pet Manifest once the customer provides a flight number.
- If a spot is available, propose Pet Booking via the sidebar.
- After booking confirms, immediately check Loyalty Perks.
- Conclude by generating the Digital Boarding Pass.

UI Priority: Always present action confirmations via the sidebar Service 
Plan buttons. Never list next steps as a numbered list in the chat.
```

Result:
```
Step 1: Get Customer Profile  → auto → CLT card renders (profile)
Step 2: Check Pet Manifest    → auto → CLT card renders (seat map)
Step 3: Pet Booking           → HiL  → Confirm button → creates record
Step 4: Loyalty Perk          → HiL  → Confirm button → applies perk
Step 5: Generate Boarding Pass → HiL → Confirm button → generates pass
```

Steps 1-2 chain reliably. Steps 3-5 may require rep nudges between HiL confirmations until the NGS fix ships.
