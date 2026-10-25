# Next-action buttons — a card button that runs the next action with a record Id

**Verified:** Global Payments Frame 9 SRA demo (Oct 2026), SRA panel during live voice calls. These chains
worked end to end:

- history list → **Details** on a row → dispute detail card
- terminals → **Transactions** → transactions list → **Details**
- pricing card (select a tile) → **Generate e-Signature Link** → review card → **Confirm** → success card
- dispute case card → **Escalate** → flow action → a text confirmation in the conversation

The same pattern was used on the CityBank banking SRA (list → detail).

The idea: **a button never calls Apex.** It sends one exact sentence to the assistant, and that sentence makes
the planner run exactly one action with exactly one record Id. The planner stays in charge, so the plan, the
next card and the voice suggestions stay in sync.

Event basics (`acc:execute` / `copytochat`, `bubbles` + `composed`, one event name, Dynamic Plan mode) are
in [interactive-writeback.md](interactive-writeback.md). This guide covers what sits on top of them.

---

## 1. The message convention (Apex writes it, not the LWC)

```
Run the <exact @InvocableMethod label> action for <what, in words> with record Id <Id>.
Show only that card; do not list other cards or search knowledge.
```

```apex
public static String runFor(String actionLabel, String what) {
    return 'Run the ' + actionLabel + ' action for ' + what + '. Show only that card; do not list other cards or search knowledge.';
}
// row button
{{CardBuilder}}.row(…, 'Details', {{CardBuilder}}.runFor('Acme SRA - Get Order Details',
    'the single order ' + o.OrderNumber + ' with record Id ' + o.Id));
// card button for the whole account
card.action('Pricing options', {{CardBuilder}}.runFor('Acme SRA - Get Pricing', a.Name + ' (account Id ' + a.Id + ')'), 'execute');
```

| Part | Why it is there |
|---|---|
| The exact action **label** | The planner matches action names, so a paraphrase can route to the wrong subagent. |
| "for the single …" + human words | It lets the planner (and the rep reading the chat) know which record this is. |
| `with record Id <Id>` | The planner copies it straight into the target input. No lookup, no guessing. |
| "Show only that card; do not list other cards or search knowledge." | Without it, the planner re-runs the whole subagent plan or adds a knowledge answer under the card. |

Build the message **in Apex** with the real Id. The LWC only sends what it was given.

---

## 2. Renderer behaviour (already in `templates/lwc-card-kit/`)

- **Every button fires once.** After a click the key goes into `sentKeys`. The label becomes "Sent ✓" or
  "<label> ✓" and the button is disabled. Double clicks would otherwise run the action twice.
- **Surface routing.** `configuration.util.sendTextMessage` is used when it exists (Enhanced Chat v2).
  Otherwise the card fires `acc:execute` (SRA panel).
- **Kinds.** `execute` runs the next action, `copy` puts the talk track in the rep's chat box (`copytochat`),
  and `primary` gives a full-width brand button.
- **Row buttons** live on `list` items (`item.action = {label, message}`). They use the same one-shot rule.
- **Record links** (`recordLink` in a `summary` block, or the record name in the record header) open the
  record with `NavigationMixin` `standard__recordPage`. No planner round trip is needed just to open a record.

### Selectable tiles + `{tier}`

`tier(…, value)` makes a `compare` tile selectable. The primary button's message carries a `{tier}`
placeholder, and the LWC substitutes the selected tile's `value` when the rep clicks:

```apex
card.block('compare', 'Two ways to pay', new List<Object>{
    {{CardBuilder}}.tier('Success fee', '18%', 'of what is recovered', '≈ $210 last month', 'nothing on a lost case', true,  'Success-Fee 18%'),
    {{CardBuilder}}.tier('Flat fee',    '$3.50', 'per case',          '≈ $38.50 last month', '',                     false, 'Flat-Fee $3.50')
});
card.primaryAction('Generate e-Signature Link',
    {{CardBuilder}}.runFor('Acme SRA - Review e-Signature Link', 'the {tier} tier for ' + a.Name + ' (account Id ' + a.Id + ')'));
```

The highlighted tile is pre-selected. The primary button shows "<value> selected" under its label and stays
disabled until a tile is picked.

---

## 3. Planner side: three places, or the button lands in the wrong place

**a. Every subagent's instructions get a BUTTON MESSAGES rule** (put it in each subagent, because a message
can land in any of them):

> BUTTON MESSAGES: card buttons send messages like "Run the Acme SRA - Get Order Details action for the
> single order 00012 with record Id 801…. Show only that card; do not list other cards or search
> knowledge." When a message names an action this way, call exactly that action, pass the record Id from
> the message into the matching input (order record Id into Order ID, account Id into Account ID), and
> display only that card. Do not run other actions, list everything again, or search knowledge for a
> button message.

**b. Routing:** the description of the subagent that owns the target action says
*'…and whenever a message says "Run the Acme SRA - Get Order Details action"'*. Drill-down target actions
also go into **every subagent whose cards have a button for them**, as per-topic `localActions` (see
`authoring-serviceplanner-sra-topics`). Otherwise the planner routes correctly and then has no action to call.

**c. Target action inputs:**

| Input | `copilotAction:isUserInput` | Description says |
|---|---|---|
| The Id a button passes (Dispute ID, Terminal ID, Case Record ID) | **`true`** (verified on GP and CityBank) | "The <object> record Id from the button message ('…with record Id …'). A number or name also works." |
| Context inputs the action resolves itself (Account ID, Record ID) | `false` | "Optional; defaults to the customer on this conversation." |

Actions that fire on their own from the conversation should have **no required inputs**. Resolve the record
in Apex. `isUserInput: true` on an auto-fired action is what produces "I cannot do this automatically" (see
the Common Pitfalls row in SKILL.md).

---

## 4. Review → Confirm → Success without `isConfirmationRequired`

`isConfirmationRequired: true` often ends the turn after the rep clicks Confirm (see SKILL.md). Instead:

1. **The pricing card**: the primary button runs the **Review** action with the chosen tier.
2. **The review card** (read-only; `record_signature_task` icon): it lists what the rep must disclose, and its
   **Confirm** button runs the **write** action. A "Change tier" button goes back to pricing.
3. **The success card** (`approval` icon), for example "Signature link generated successfully".

All three actions keep `isConfirmationRequired: false`. The review card **is** the confirmation.

**Fire it from the conversation too.** Add the trigger phrases to the subagent steps so the chain moves
without a click. Guard against loops:

> As soon as the customer chooses a tier or agrees to go ahead ("let's do the flat fee", "let's continue",
> "ok", "go ahead", "confirm the price model"), call Review with the chosen tier. Treat a bare "ok" or "let's
> continue" as a choice **only while the pricing card is the latest card and no link has been generated
> yet**. Once the link is generated, never call Review or Generate again for "ok" or "thanks". If the rep
> says "let me send you the link" before the review card is on screen, call Generate directly. The
> customer's verbal agreement is the confirmation.

---

## 5. When a card is overkill: a flow action that returns a sentence

For a one-step write whose result is a sentence (assign to a queue, change an owner), skip the card. Use a
**flow** GenAiFunction (`invocationTargetType` = `flow`) with a text output marked
`isDisplayable: true` **and** `isUsedByPlanner: true`. The planner shows it in the conversation as is.

```json
"properties": { "message": { "title": "Message", "lightning:type": "lightning__textType",
  "copilotAction:isDisplayable": true, "copilotAction:isUsedByPlanner": true } }
```

- The schema property names are the **bare flow variable names** (`recordId`, `message`).
- The flow returns something like `Case {Id} was escalated successfully to {Queue Name} Queue`, plus a
  "could not be escalated" message on the not-found and fault paths.
- The card button that starts it sends a matching sentence, e.g. `Escalate case <Id> to P1 Dispute queue`.
  The action description says to call it for that message and pass the Id.
- Grant the flow to the agent user's permission set (`flowAccesses`).

---

## 6. Test every button

- **Apex:** assert each button message contains the target action label **and** the record Id.
- **Live:** click every button once in the real SRA panel, and check that exactly one card appears with no
  knowledge answer under it. Also say each trigger phrase once to check the conversational path.
- If a click shows "Sent ✓" but nothing runs, check that the target action is in the subagent the message
  routed to (§3b) before anything else.
