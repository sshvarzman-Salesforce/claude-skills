# Card Kit — one renderer, a Lightning design system for every card

**Verified:** Global Payments Frame 9 SRA demo (Oct 2026). 13 cards, 1 LWC, 1 Apex builder, on
the Service Rep Assistant panel during live voice calls. The demo owner called the result "beautiful,
clean". The first version's coloured gradient headers were rejected as "nasty".

Templates: [templates/lwc-card-kit/](../templates/lwc-card-kit/) (renderer),
[templates/card-kit-builder.cls](../templates/card-kit-builder.cls) (Apex builder),
[templates/card-kit-action-class.cls](../templates/card-kit-action-class.cls) (a list card whose rows drill into a detail card).
Buttons: [next-action-buttons.md](next-action-buttons.md).

---

## When to use the kit instead of one LWC per card

Use it when a surface has **three or more cards** or when cards must look like one product. Adding a
card is then Apex only: a DTO, an action, a Lightning Type, and a GenAiFunction. There is no new LWC and
no new CSS. A one-off card with a bespoke layout can still use the plain `templates/lwc/`.

```
GenAiFunction A ─► Lightning Type a (schema → @apexClassType/c__CardAOutput) ─┐
GenAiFunction B ─► Lightning Type b (schema → @apexClassType/c__CardBOutput) ─┼─► renderer.json → c/acmeCard (the kit)
GenAiFunction C ─► Lightning Type c (schema → @apexClassType/c__CardCOutput) ─┘
```

- **One DTO class per card**, each with the single `@AuraEnabled global String cardJSON`. That is what
  was verified. Sharing one DTO across Lightning Types was not tested.
- Every `lightningDesktopGenAi/renderer.json` points at the **same** `c/<kitLwc>`.
- The JSON shape is the contract. The LWC never queries, formats or decides. Apex does all of it.

---

## Payload shape

```json
{
  "icon": "standard:report",
  "eyebrow": "Order history",
  "title": "Acme Outfitters",
  "subtitle": "11 orders · $4,210.00",
  "stamp": "As of 2:41 PM",
  "verdict": { "text": "3 orders are waiting on payment.", "state": "warn" },
  "summary": "Optional one-paragraph context under the verdict.",
  "blocks": [
    { "type": "stats", "title": null, "items": [ { "label": "Orders", "value": "11", "hint": "last 30 days", "state": "info" } ] },
    { "type": "list", "title": "Recent orders", "items": [
        { "primary": "Order 00012", "secondary": "Oct 21", "amount": "$842.00", "badge": "Draft", "state": "warn",
          "action": { "label": "Details", "message": "Run the Acme SRA - Get Order Details action for … with record Id 801…" } } ] }
  ],
  "reco": "Recommended next step for the rep.",
  "talkTrack": "What the rep can say, in the customer's words.",
  "actions": [
    { "label": "Generate link", "message": "Run the … action for … with record Id …", "kind": "execute", "primary": true },
    { "label": "Account summary", "message": "Run the …", "kind": "execute" },
    { "label": "Copy talk track", "message": null, "kind": "copy" }
  ],
  "layout": "record",
  "record": { "icon": "standard:case", "objectLabel": "Case", "name": "00001234", "recordId": "500…",
              "objectApiName": "Case", "url": "/lightning/r/Case/500…/view",
              "status": "Escalated", "statusState": "warn",
              "highlights": [ { "label": "Priority", "value": "High", "state": "warn" } ] }
}
```

`{"error": "…"}` alone renders the error state (`errorJson()` in the builder).

### Card anatomy, top to bottom

1. **Header.** A white Lightning card header: the object icon, a grey label, the bold title, a grey subtitle,
   and "As of h:mm" on the right. With `layout: 'record'`, the record name becomes a link and a status pill
   and highlights strip are added.
2. **Verdict.** One sentence that answers the question, coloured by state. Put the number in it
   ("11 orders in 30 days", not "High volume").
3. **Summary.** Optional context.
4. **Blocks** (below).
5. **Recommended next step.** A grey box with a blue rule, written for the rep.
6. **Say to the customer.** A white box with a grey rule, in the customer's words, with a "Copy talk track" button.
7. **Primary button.** Full width, brand blue. **Secondary buttons** come after it.

### Block catalogue

| `type` | Builder helper | Use for | Notes |
|---|---|---|---|
| `stats` | `stat(label, value, caption, state)` | 2–4 headline numbers | 2-column grid; value coloured by state |
| `fields` | `field(label, value, state)` | label / value lines | right-aligned values |
| `list` | `row(primary, secondary, amount, badge, state[, buttonLabel, message])` | records with an optional per-row button | the button runs the next action |
| `compare` | `tier(name, price, detail, estimate, note, highlight[, value])` | 2 options side by side | with `value`, tiles are **selectable** (see buttons guide) |
| `checklist` | `check(label, note, state)` | evidence / requirements | ✓ / ⚠ / ✕ icon from state |
| `progress` | `progress(label, value, bar0to100, state)` | share-of-total bars | |
| `timeline` | `event(time, who, text)` | conversation beats | `who` = Assistant/System styles as the bot |
| `summary` | `note(label, value, bullets)` + `recordLink(label, linkText, id, objectApiName)` | AI summary sections + a link that opens a record | [patterns.md §9](../references/patterns.md) |
| `path` | `step(label, complete\|current\|incomplete)` | status chevrons | record layout; `block(…, note)` adds "In X for 3 days" |
| `stages` | `stage(label, range, duration, current)` | time in each status | record layout |
| `text` | `text(label, value)` | long text (Description) | keeps line breaks |
| `details` | `field(label, value, state)` | two-column record fields | record layout |

`block()` **skips empty item lists**, so build blocks unconditionally and let empty data disappear.

---

## Visual rules (the "clean Salesforce" look)

| Rule | Why |
|---|---|
| **The header is white** with an SLDS object icon. Never use a coloured or gradient header band. | Coloured bands read as a custom app rather than Salesforce. The demo owner rejected an amber header on sight. |
| **Colour carries state only:** the verdict banner, badges, pills, stat values and checklist icons. | A card's mood comes from its data, not its theme. |
| Section titles are a **grey band** (`#f3f3f3`), in sentence case at 0.8125rem/600. | Matches record page sections. |
| Main button: `#0176d3`, hover `#014486`, radius `0.25rem`, no shadow. Row buttons are SLDS neutral (white, `#c9c9c9` border, blue text). | Standard Lightning buttons. |
| Selection (tiles, radios): brand blue `#0176d3` on `#eef4ff`. | Standard Lightning selection colour. |
| Card: `1px #dddbda` border, radius `0.25rem`, shadow `0 2px 2px rgba(0,0,0,.1)`. | The lightning-card frame. |
| Designed for a **~380px panel**: grids of 2 columns at most (3 for record highlights), `0.8125rem` body text. | The SRA panel width. |

| Token | Value |
|---|---|
| Text / weak text | `#181818` / `#5c5c5c` |
| Borders / dividers | `#dddbda` / `#e5e5e5` |
| Brand / hover / link | `#0176d3` / `#014486` / `#0b5cab` |
| ok | text `#1c6b3f`, icon `#2e844a`, bg `#ebfbef` |
| warn | text `#8c4b02`, icon `#dd7a01`, bg `#fef5e7` |
| fault | text `#8e030f`, icon `#ea001e`, bg `#fef1ee` |
| info | text `#014486`, icon `#0176d3`, bg `#eef4ff` |

Icon colours inside a state use `--slds-c-icon-color-foreground-default`. The template CSS already does this.

---

## Icons: check the name before you use it

A wrong `standard:` name renders an **empty square** and raises no error. Check names against the org's own sprite:

```powershell
$o = sf org display -o <alias> --json | Out-String | ConvertFrom-Json
$svg = (Invoke-WebRequest -UseBasicParsing -Uri ($o.result.instanceUrl + '/_slds/icons/standard-sprite/svg/symbols.svg') `
        -Headers @{ Authorization = "Bearer $($o.result.accessToken)" }).Content
'account','report','currency','dispute' | ForEach-Object { "$_ = " + $svg.Contains("id=""$_""") }
```

These names were verified in Oct 2026 (632 standard icons): `account`, `report`, `currency`, `case`, `contract`,
`approval`, `pricebook`, `asset_object`, `device`, `orders`, `product`, `payment_gateway`, `messaging_session`,
`task`, `entitlement`, `service_contract`, `work_order`, `record_signature_task`. **These do NOT exist:**
`standard:dispute` and `standard:signature`.

| Card | Icon used |
|---|---|
| Customer / account 360 | `standard:account` |
| History / analytics list | `standard:report` |
| Money item (chargeback, payment) | `standard:currency` |
| Devices / terminals | `standard:device` |
| Transactions / orders | `standard:orders` |
| Pricing | `standard:pricebook` |
| Review before sending | `standard:record_signature_task` |
| Success / sent | `standard:approval` |
| Enrollment / SLA milestones | `standard:entitlement` |
| Case / escalation | `standard:case` |

---

## Record layout (`layout: 'record'`)

Use `.record(icon, objectLabel, name, recordId, status, statusState, highlights)` when the card **is** one
record, such as a case or an order. The header gains the record name, which opens the record in a console tab
through `NavigationMixin` `standard__recordPage`, plus a status pill and a highlights strip. Pair it with
`path`, `stages`, `details` and `text` blocks.

**Time in status:** read `CaseHistory WHERE Field = 'Status'` oldest first. Each change ends the previous
status and starts the next one, and the first status starts at `CreatedDate`. The current status runs to now,
or to `ClosedDate`. If history disagrees with the field (tracking was switched on later), trust the field.
Note that the current stage then has no real start time. The value is computed when the card renders and
does not tick while the card is open.

---

## Writing rules

- Format dates, money and durations **in Apex**, in the customer's time zone (`TZ` in the builder).
- Refer to a contact by **first name**, never he/she, in the verdict, talk track and AI summaries.
- Write the talk track as something the rep would actually say to the customer.
- Every card action returns a one-line `plannerSummary` of real numbers. The planner quotes it in its reply,
  so the chat text and the card agree.

## Before you deploy

- [ ] Every card calls `.icon('standard:…')`, and every name is checked against the sprite.
- [ ] No hex outside the palette table, and no gradients.
- [ ] Each Lightning Type's `renderer.json` points at the kit LWC, and each `schema.json` at that card's DTO.
- [ ] Apex test: build each card, `JSON.deserializeUntyped(toJson())`, assert the block types and that
      button messages contain the target action label and record Id.
- [ ] **Run the test class on its own after the deploy.** In a production org,
      `deploy --test-level RunSpecifiedTests` reported *Succeeded* while the class had failing methods, and a
      broken card went live (Oct 2026).
- [ ] Hard-refresh the console after an LWC deploy (Ctrl+Shift+R). The panel caches the old CSS.
