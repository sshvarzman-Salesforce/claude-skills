# Interactive / Write-Back CLTs (CLT → SRA chat)

**Status:** Working and verified in the Service Rep Assistant panel (2026-08).
Treat as undocumented/internal: Salesforce publishes no reference for these events.
Customer sandboxes from ~2026-08-22 (targeting 262.14).

---

## What this unlocks

Historically CLTs were **one-directional**: an action returns a card, the card renders, done.
A CLT could not push anything back into the agent conversation.

That gap is now closed **for the Service Rep Assistant panel**. A CLT's LWC can fire a DOM
custom event that the SRA panel (`agentResponse` / DRE listener) catches and injects into the
chat. This turns a static card into an **interactive, proactive** control surface — buttons in
the card can drive the next plan step.

This is the core of the "make SRA more proactive" workstream (GA blocker for Meta / EA / Singapore).

---

## The two events

| Event name    | Behavior                                                                                  |
|---------------|-------------------------------------------------------------------------------------------|
| `copytochat`  | Drops the text into the **chat input box**. Rep reviews / edits, then sends manually.     |
| `acc:execute` | **Auto-sends** the text into chat history as if the rep typed it. Agent responds at once. |

## The verified contract

```js
// copytochat — populate the input box for rep review
handleCopy() {
    const content = { content: 'Customer verification passed' };
    this.dispatchEvent(new CustomEvent('copytochat', {
        detail: content,
        bubbles: true,
        composed: true
    }));
}

// acc:execute — auto-send straight to the agent
handlePost() {
    const content = { content: 'Customer verification passed' };
    this.dispatchEvent(new CustomEvent('acc:execute', {
        detail: content,
        bubbles: true,
        composed: true
    }));
}
```

---

## Gotchas (each of these broke a tester in the thread)

1. **Do NOT use the combined name `"copytochat/acc:execute"`.** It silently no-ops. Fire ONE
   event: either `copytochat` OR `acc:execute`.
2. **Payload field is `detail.content`** — an object `{ content: '...' }`. (`detail.text` was
   floated early but the shipped contract uses `content`.)
3. **`bubbles: true` AND `composed: true` are required** so the event crosses shadow boundaries
   and reaches the SRA panel listener. Omitting either = event never received.
4. **SRA panel only.** These events are NOT handled by the standard Agentforce / ACC panel.
   Testing in the AF panel produces no effect. (Long-term ACC-panel support is a separate effort
   via `accInteractiveBlock` / DRE — not shipped.)
5. **SRA must be in Dynamic Plan mode**, not Guidance Plan mode. If SRA doesn't pop / the button
   does nothing, check the Service Assistant plan-mode setting first.
6. `copyToClipboard(...)` (OS clipboard) is independent of these events — don't confuse a working
   clipboard copy with a working chat write-back.

---

## When to reach for each event in a demo

- **`copytochat`** — suggested-reply chips, draft responses the rep should review/personalize
  before sending. Safer, keeps the human in the loop.
- **`acc:execute`** — decisive selections that should immediately advance the plan: Pass/Fail
  verification, seat/option pick, "yes proceed". Snappier demo beat, less rep friction.

## Demo patterns this enables

- **Verification card** → Pass / Fail buttons post the outcome and trigger the next plan step
  (the canonical thread example).
- **Option selector** → clicking a seat / plan / product sends "I'll take 14C" proactively.
- **Suggested replies** → `copytochat` chips the rep can edit before sending.

---

## Interplay with the rest of the skill

- The interactive LWC still targets `lightning__AgentforceOutput` and (for good measure)
  `lightning__AgentforceInput`. The rest of the four-layer architecture (single-JSON-field DTO,
  `without sharing` action, Lightning Type bundle) is unchanged — you're just adding button
  handlers + event dispatch to the LWC.
- Because the CLT itself now drives the follow-up utterance, you can sometimes side-step the
  fragile post-confirmation chain continuation (see `chaining.md`): instead of relying on the
  planner to auto-resume after a Confirm, the rep clicks a card button that fires `acc:execute`
  with the exact next utterance.
