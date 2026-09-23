# CLT surface adapters

The Apex envelope (global DTO, one `@AuraEnabled` JSON string, `lightningDesktopGenAi`
renderer, `lightning__AgentforceOutput` LWC) is the same on every surface. Channel
folder, write-back API, sharing, and run-as user are not. Pick the surface in Step 0
of the builder skill, then apply this adapter.

Salesforce publishes one compatibility table:
[Lightning Type UI Configuration](https://developer.salesforce.com/docs/platform/lightning-types/guide/lightning-types-ui-config.html).

| Channel folder | Editor | Renderer | Surface |
|---|---|---|---|
| `lightningDesktopGenAi` | Yes | **Yes** | Agentforce panel in Lightning Experience, including the Service Console |
| `lightningMobileGenAi` | Yes | **Yes** | Employee agent on mobile; Enhanced Chat v2 on mobile |
| `enhancedWebChat` | Yes | **Yes** | Customer-facing Enhanced Chat **v2** only |
| `experienceBuilder` | Yes | **No** | Experience Builder — editors only |

**Default: generate only `lightningDesktopGenAi/renderer.json`.** Do not add
`enhancedWebChat/`. The compatibility table lists that folder as valid, and ECv2
falls back to desktop when it is missing, but adding it has overridden working
desktop configs in field testing.

Requires `LightningTypeBundle` on API **64.0+** (this skill's LWC templates use
**67.0**). The action must return an Apex class — a bare `String` bypasses the LWC.

---

## Adapter table

| Surface | Channel folder | Write-back | Sharing | Run-as / permset | Also load |
|---|---|---|---|---|---|
| **Service Rep Assistant** (LEX panel, actions execute) | `lightningDesktopGenAi` only | `copytochat` / `acc:execute` (undocumented, SRA + Dynamic Plan). Messaging send via `lightning/conversationToolkitApi` | `without sharing` | EinsteinServiceAgent user **and** the rep | — |
| **Employee Agent LEX panel** | same | `execute(utterance, botId)` from `lightning/accApi` (documented, LEX desktop). Do **not** assume `copytochat` works | `with sharing` unless proven otherwise | logged-in user (Permission Set Group) | `agentforce-lightning-types` for planner/render |
| **Enhanced Chat v2** (customer widget) | same; **do not add** `enhancedWebChat/` | `this.configuration?.util.sendTextMessage(...)`. Context: `setSessionContext([...])` | portal user (credential verification) or botUser | permset on the user the session actually runs as | **`agentforce-lightning-types`** — ECv2 Connection, ESD WebV2, republish, W-22250928, W-21533738 |
| **Agentforce Cowork** | treat as Employee LEX until proven | **None verified.** Buttons are display-only or `NavigationMixin`. Any write-back must be labelled unverified | `with sharing`; logged-in user | same as Employee | builder skill only; do not invent APIs |

Write-back APIs are mutually unavailable. `lightning/accApi` is a module import that
exists only in LEX desktop. `this.configuration` is injected in the ECv2 iframe and
does not exist on the desktop panel. `copytochat` / `acc:execute` are SRA-panel
listeners. A component hard-wired to any one of these is silent on the others.
To share one renderer, branch at runtime: `this.configuration?.util` first, then
SRA events, else no-op.

---

## Silent desktop → ECv2 fallback (privacy)

The docs state: *"If `enhancedWebChat` isn't configured, it uses the configuration
defined in `lightningDesktopGenAi`."* A card authored for a **rep** can therefore
render to an **external customer** in Enhanced Chat v2 without anyone opting in.
Whether rep-only fields are stripped on that path is **not documented**.

Before an org that hosts a rep card is used for customer chat:

- Strip internal notes, margins, churn risk, agent-facing guidance, and RMA
  judgements from the payload — or ship a second, customer-safe Lightning Type.
- Do not treat "we never added `enhancedWebChat/`" as an opt-out. It is the
  opposite: missing that folder *enables* the fallback.

---

## Per-surface notes

### Service Rep Assistant

Summit Ridge (8 Lightning Types) is the verified Path A reference. Confirm you are
on the **Agentforce agent in the LEX panel** (topics whose actions execute), not
the Case-page Service Assistant component (actions there are grounding only).

Send targets resolve client-side from the focused console tab
(`templates/lwc-reply-routing/`): Messaging `0Mw`, Case `500`, Voice `0LQ`. The
Apex "latest Active MessagingSession" ladder is for **reads only**.

`sendTextMessage` success is `!== false`. Once a messaging session is in play, do
not fall back to the agent panel — a successful send otherwise duplicates into
the assistant draft.

### Employee Agent LEX

Same envelope and channel folder. Planner render behaviour is owned by
`agentforce-lightning-types` (ShowCommand vs InformCommand). Interactive buttons
should use `lightning/accApi`; re-verify `copytochat` before relying on it.

### Enhanced Chat v2

Same envelope. Load `agentforce-lightning-types` before generating and before
calling the card done:

1. ECv2 added as a Connection on the agent
2. ESD client version WebV2
3. Republish the ESD after every change — a stale publish renders as plain text
4. Input CLTs do not render on Service Agent + ECv2 (W-22250928)
5. LDS-backed `@wire` fails in the ECv2 iframe (W-21533738) — imperative Apex only
6. Chat-site Member Provisioning must include the authenticated profile

No LDS `@wire`. No `copytochat`. No `conversationToolkitApi`.

### Agentforce Cowork

Unverified as of 2026-09-05. Generate the same envelope as Employee LEX
(`lightningDesktopGenAi`, `with sharing`, logged-in user). Do **not** wire
`copytochat`, `acc:execute`, `conversationToolkitApi`, or
`configuration.util.sendTextMessage`. Buttons navigate (`NavigationMixin`) or
are display-only. If a write-back is later proven, document the API and the
surface that accepted it — do not copy SRA events over on speculation.

---

## What does not travel

| Target | Why |
|---|---|
| Slack / Slackbot | Renders Block Kit, not DOM. Mosaic widgets are Beta and still do not render on Block Kit. |
| Experience Builder | Editor-only. Cannot render output CLTs. |
| MIAW Chat v1 | CLTs are not supported. Upgrade to Enhanced Chat v2. |
| Standard Agentforce / ACC panel (non-SRA) | `copytochat` / `acc:execute` are not received. |

---

## Sharing / run-as (copy this into the action class comment)

```
SRA / EinsteinServiceAgent  → global without sharing
Employee Agent / Cowork     → with sharing (logged-in user)
ECv2 authenticated          → with sharing; permset on the portal user
ECv2 no verification        → the internal botUser; grant that user, not Guest
```

`sf org assign permset` with no `--on-behalf-of` grants *your* user. A Service
Agent still fails because `<botUser>` does not have the classes or FLS.
