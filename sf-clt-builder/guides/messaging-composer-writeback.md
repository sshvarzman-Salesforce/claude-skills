# Messaging-Channel CLTs: Post / Edit into the CUSTOMER conversation

**Status:** Standard pattern for messaging-channel CLTs. The mechanism is GA
(`lightning/conversationToolkitApi`, Spring '25, API 60.0+). Calling it from a CLT rendered in
the **Agentforce output panel** (`lightning__AgentforceOutput`) is undocumented but
**VERIFIED WORKING as of 2026-09-02** (sfdc-brendan/Unofficial-Skills) — no bridge component
needed. Treat as undocumented: wrap every call so failures resolve rather than throw.

---

## 1. Why this is separate from `copytochat` / `acc:execute`

There are TWO different conversations on a messaging session screen, and two different
write-back targets. Do not confuse them.

| You want to write into… | Use | Lands in |
|---|---|---|
| the **SRA agent chat** (rep ↔ agent) | `copytochat` / `acc:execute` DOM events | the agent sidebar chat |
| the **customer messaging composer** (agent ↔ customer) | `conversationToolkitApi` | the Enhanced Conversation composer / the live customer thread |

`copytochat` is for steering the *agent*. It never reaches the customer. For a messaging
channel where the goal is "help the rep reply to the customer," the target is the **customer
composer**, which is `conversationToolkitApi.setAgentInput`.

---

## 2. The two customer-facing actions

| Button | Function | Behavior | Default? |
|---|---|---|---|
| **Edit** (paste to composer) | `setAgentInput(recordId, { text }, true)` | Drops text into the messaging composer for the rep to review/edit, then send. `setAtCursor:true` inserts at the caret (non-destructive); `false` OVERWRITES what the rep already typed. | ✅ **Yes — the standard action.** Keeps the rep in the loop. |
| **Post** (send now) | `sendTextMessage(recordId, { text })` | Sends immediately to the customer, no review step. | ❌ Gate behind explicit config / permission. |

**Standard:** default every messaging-channel CLT to **Edit**, and use `setAtCursor: true` so it
never clobbers text the rep is mid-way through typing. Only expose **Post** when the customer
explicitly wants one-click auto-send and accepts that AI-drafted text goes to the customer with
no review. `Edit` ≈ `copytochat` (review first); `Post` ≈ `acc:execute` (fire immediately).

---

## 3. Resolve the send target CLIENT-SIDE — never from the DTO / Apex

**This is the single most important correctness rule.** A CLT LWC receives the DTO via
`@api value`, not a `recordId`. It is tempting to serialize a `messagingSessionId` into the DTO
JSON (Apex resolving "the latest Active MessagingSession"). **Do NOT do this for a SEND.**

- An org can have several Active messaging sessions at once. The server-side "latest active"
  ladder can name a **different customer's** conversation.
- A send has **no undo**. Reading the wrong card is recoverable; sending to the wrong customer is not.

So the Apex "latest Active MessagingSession" ladder is **reads only**. The send target must come
from the console tab the rep is actually looking at, resolved client-side via
`lightning/platformWorkspaceApi` and matched by Id prefix:

| Prefix | Context | Action |
|---|---|---|
| `0Mw` | Messaging Session | send / paste into the live customer conversation |
| `500` | Case | caller decides (email composer, etc.) |
| `0LQ` | Voice Call | nothing — rep reads the card aloud |
| other | — | fall back to the agent panel (`copytochat`) |

Use the shared service module `templates/lwc-reply-routing/replyRouting.js`
(`resolveMessagingSessionId()`, `replyToCustomer(sessionId, text, immediate)`) rather than
re-deriving this in each card. Call `resolveConversationContext()` OUTSIDE the card's JSON-parse
try/catch so a messaging miss can never blank the card.

---

## 4. Success detection & no-duplicate-fallback (both cause duplicate sends if wrong)

- **Check `!== false`, never `=== true`.** `sendTextMessage` resolves `undefined` while genuinely
  delivering the message. A strict `=== true` check reads a successful send as a failure.
- **Once a messaging session is in play, do NOT fall back to the agent panel.** If the send path
  "fails", report it on the button label — do not `copytochat` as a backup, or the customer gets
  the message twice. (`replyRouting.js` already resolves `false` only on a genuine refusal.)

---

## 5. The LWC contract (via the shared module)

```js
import { LightningElement, api, track } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { resolveMessagingSessionId, replyToCustomer } from 'c/replyRouting';

// ...parse this.value.<dtoJsonField> in connectedCallback() as usual...

// EDIT (standard): paste into the customer composer to review/edit before sending
async handleEdit() {
    const sessionId = await resolveMessagingSessionId();
    if (!sessionId) { this.toast('No live chat', 'Open the Messaging Session tab first.', 'warning'); return; }
    const ok = await replyToCustomer(sessionId, this.data.suggestedReply, /* immediate */ false);
    this.toast(ok ? 'Loaded into composer' : 'Could not load reply',
               ok ? 'Edit the reply, then send it yourself.' : 'The composer did not accept the text.',
               ok ? 'info' : 'error');
}

// POST (gated): send immediately to the customer
async handlePost() {
    const sessionId = await resolveMessagingSessionId();
    if (!sessionId) { this.toast('No live chat', 'Open the Messaging Session tab first.', 'warning'); return; }
    const ok = await replyToCustomer(sessionId, this.data.suggestedReply, /* immediate */ true);
    // Do NOT fall back to copytochat here — report failure only, or the customer gets it twice.
    this.toast(ok ? 'Reply sent' : 'Post failed',
               ok ? 'Your reply was posted to the customer.' : 'Try again from the composer.',
               ok ? 'success' : 'error');
}
```

Use template `templates/lwc-messaging/TEMPLATE.js` (already wired to the module) as the start.

---

## 6. Hard requirements / gotchas

- **Console app only.** The toolkit silently no-ops unless the Messaging Session is open in a
  Lightning **console** tab with the **Enhanced Conversation Component** rendered, and SRA is in
  **Dynamic Plan mode**.
- **`with sharing` on the reply-drafting controller is correct** — the composer write-back runs as
  the *rep*, NOT as EinsteinServiceAgent User. This is the OPPOSITE of the CLT *action*-class rule
  (`without sharing`). Keep the two straight.
- **Do NOT invent `lightning/conversationAgentSend`.** `lightning__conversationAgentSend` is a
  notification event you *listen* to, not a send API. The send/draft API is
  `lightning/conversationToolkitApi`.
- API **v60.0+** for the toolkit import (this skill's LWC bundles use 62.0+).
- This is the **SRA panel** path. Other surfaces use different write-back APIs entirely —
  Employee LEX = `lightning/accApi` `execute()`, Enhanced Chat v2 = `configuration.util.sendTextMessage()`.
  See `guides/surfaces.md`.
