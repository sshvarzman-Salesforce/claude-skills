# HighlightCard — Runnable CLT Scaffold

A minimal, working Apex-based custom Lightning Type that renders a card (title, description, image, link) inside an Agentforce chat window. Use this as the starting point for any "single-record-shaped output" CLT — copy, rename, expand the shape.

## What's in here

```
force-app/main/default/
├── lightningTypes/
│   └── highlightCard/
│       ├── schema.json                       # references c__HighlightCardData
│       └── lightningDesktopGenAi/renderer.json  # ONLY this folder. ECv2 falls back to it.
├── classes/
│   ├── HighlightCardData.cls                 # global class, @AuraEnabled, @JsonAccess
│   └── HighlightCardData.cls-meta.xml
└── lwc/
    └── highlightCard/
        ├── highlightCard.html
        ├── highlightCard.js                  # @api value, @api readOnly
        ├── highlightCard.js-meta.xml         # target: lightning__AgentforceOutput
        └── highlightCard.css
```

## Deploy

Drop into a project under `force-app/main/default/` and run:

```bash
sf project deploy start \
  --source-dir force-app/main/default/lightningTypes/highlightCard \
  --source-dir force-app/main/default/classes/HighlightCardData.cls \
  --source-dir force-app/main/default/classes/HighlightCardData.cls-meta.xml \
  --source-dir force-app/main/default/lwc/highlightCard
```

Org must be on **API 64.0 or later** for `LightningTypeBundle` metadata.

## Wire to an agent action

1. **Apex Invocable path** (recommended for static / fully agent-driven content):
   - Add an `@InvocableMethod` that returns `List<HighlightCardData>` (or a wrapper class with a `HighlightCardData` field).
   - In Setup → Agentforce → \[your agent\] → Topics → Actions, create a new agent action from the Apex method.
   - Set **Output rendering** = `HighlightCard` (the LWC name).
   - Set **Show in conversation** = ON.

2. **Flow path** (recommended when the SE/admin wants to assemble the card without code):
   - Create an autolaunched flow.
   - Add a flow output variable typed `c__HighlightCardData`.
   - Build the flow to populate that variable.
   - Create the agent action from the flow; same wire-up as above.

3. **Permissions**:
   - Grant the agent user access to the `HighlightCardData` Apex class via permission set.
   - For Service Agent (Chat V2): the Embedded Service Deployment site must have CORS configured to your my-domain.

## Test

- Builder preview **can** render CLTs as of the 262 release (AEA always; ASA when the agent is connected to ECv2). Still confirm on the real surface before calling it done.
- Service Agent: Setup → Embedded Service Deployments → \[your deployment\] → **Test Enhanced Web Chat** (incognito, after republishing the ESD).
- Employee Agent: Open a record page in LEX, open the Agent Assist panel, ask the agent something that triggers the action.

To generate a production card (envelope DTO, GenAiFunction flags, surface adapter), use `sf-clt-builder` rather than expanding this typed-field scaffold.

## Adapt this scaffold to your shape

1. Rename folders & class: `highlightCard` → `myType`, `HighlightCardData` → `MyTypeData`.
2. Update `schema.json`'s `lightning:type` to `@apexClassType/c__MyTypeData` (single record: `@apexClassType/c__MyController$MyWrapper`).
3. Edit `MyTypeData.cls` to match your shape — keep `global`, `@AuraEnabled`, and `@JsonAccess`.
4. Update the LWC to render your fields.
5. If you need user input, add an `editor.json` and a second LWC with target `lightning__AgentforceInput`. The input LWC must dispatch `valuechange` events to send data back to the agent.

## Pattern shortcuts

If your shape matches one of the 8 reference patterns (carousel, item selector, form, file upload, etc.), see `../../references/patterns.md` for the data contract — don't reinvent.
