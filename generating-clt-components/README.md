# generating-clt-components

> Build, deploy, and reliably invoke **Custom Lightning Types (CLTs)** from Agent Script in Agentforce.

A CLT is the only way to render a custom UI component (cart, carousel, picker, receipt, confirmation card) inside Agentforce conversations that **bypasses Atlas's final-response paraphraser**. Plain markdown text gets re-synthesized by the planner. CLT output renders verbatim. Every demo-grade UI in Agentforce ships through a CLT.

This skill is a recipe — the things you must build, in the order you must build them, with the lessons from a real production engagement (AcmeRetail Australia FDE) baked in. Including the failure that took a full day to debug.

## TL;DR

A working CLT requires **four pieces of metadata** lined up correctly, **two operational rules** people skip, and **one LWC pattern** that nobody documents.

- **The four pieces:** LightningTypeBundle, GenAiFunction, Apex+Flow wrapper, LWC component.
- **The two rules:** (1) republish Embedded Messaging deployment after agent publish; (2) hard-refresh the chat after every LWC deploy.
- **The pattern:** `@api` on a getter/setter (not a plain property), three-shape envelope unwrap, builder fallback JSON, re-run `connectedCallback` on setter.

If you skip any of these, the CLT renders blank, the planner skips the action, or the Setup preview crashes. The full skill at `SKILL.md` walks through each.

## Demo

End-to-end walkthrough of the AcmeRetail Red CLT pattern in a real conversation — order lookup → photo upload → curated upgrade carousel → in-chat checkout. (Demo recording not included in this repository.)

## When to read this

Use this skill when:
- You want to render a custom card/component from an agent action (not just a text bubble).
- Your CLT works in Apex/Flow logs but the chat shows nothing.
- The planner refuses to invoke your action — text-only replies, no `ACTION_STEP` fires.
- You ported a working CLT to a new agent or new payload shape and it stopped working.
- The Setup → Lightning Type → Preview is blank.

Skip this skill (use a different one) if:
- You're building the launcher button itself → `agentforce-embedded-launcher`.
- You're tracing a runtime session → `agentforce-investigator-fullstack`.
- You're on Embedded Messaging V1 — this skill is V2 only.

## How to invoke

Tell Claude what you want:

- *"Build a CLT for an order-confirmation card with customer name, shipping address, and order number"*
- *"My exchangeCheckout CLT renders blank in chat — debug it"*
- *"Why is the planner not calling my Show_Recommendation action?"*
- *"Port the AcmeRetail checkout CLT to a new agent for a different customer"*

Claude will read the skill, identify which of the four layers your problem lives in, and walk through the specific fix.

## What's inside

```
generating-clt-components/
├── SKILL.md                          ← Main skill content (loaded when triggered)
├── README.md                         ← This file
└── templates/
    ├── clt-lwc-template.js           ← Load-bearing LWC pattern, copy-paste ready
    ├── clt-lwc-template.html         ← HTML scaffold with value.* bindings
    ├── clt-lwc-template.css          ← Reset + neutral styling
    ├── clt-lwc-template.js-meta.xml  ← LWC exposure for Lightning types
    ├── clt-data-class.cls            ← @AuraEnabled wrapper class
    ├── clt-data-class-test.cls       ← Minimal Apex test for 75% coverage
    ├── clt-flow-meta.xml             ← Autolaunched Flow (Details → Apex field)
    ├── lightning-type-bundle/        ← schema.json + both renderer JSONs
    │   ├── schema.json
    │   ├── enhancedWebChat/
    │   │   └── renderer.json
    │   └── lightningDesktopGenAi/
    │       └── renderer.json
    ├── genai-function/               ← Input + output schemas + meta.xml
    │   ├── input/schema.json
    │   ├── output/schema.json
    │   └── My_Function.genAiFunction-meta.xml
    ├── example-agent-script-AcmeRetail.md ← Working production agent script (2 CLTs)
    └── grant-guest-perms.apex        ← Assign Apex class to guest user
```

## Provenance

Verified 2026-05-26 against:
- Org: `your-org.sandbox.my.salesforce.com` (org id `00Dxxxxxxxxxxxxxxx`).
- Agent: `EnhancedChatV2Test` v53, Atlas v2 planner.
- Embedded Messaging V2 deployment.
- Two CLTs in production service: `checkoutReview_46d7f6` (cart), `asaCarousel` (TV selection).
- One CLT we tried and abandoned: `exchangeCheckout` — failure baked into the lessons.

If Salesforce ships a new Atlas planner version, a new Embedded Messaging V2 SDK, or changes the CLT bundle schema, re-verify before relying on the patterns here.

## Where the lessons came from

Every paragraph in `SKILL.md` corresponds to a specific bug we hit on the AcmeRetail engagement and either fixed or worked around. The failure modes catalogue is a verbatim list of "we just spent two hours on this" entries from the project.

The most expensive lesson: **plain `@api value` does not survive both Setup preview and runtime envelope wrapping.** Our first custom CLT (`exchangeCheckout`) had this and never rendered. We wasted a day on agent-script-side fixes (rule expressions, planner gating, action position) before tracing the failure to the LWC's value handling. The skill leads with that pattern because it's the single most common silent failure.

Second most expensive: **Embedded Messaging deployment caching.** The agent publishes successfully, the new action is in the new version, but the chat is still serving the previous agent version. "It worked yesterday, broke today" turned out to be "deployment never picked up the new agent version." Republishing the deployment resolved it. This is now Rule 1.

## Feedback

`#agentforce-fde-team-anz-toolbox` on Salesforce internal Slack.

## Authored by

Hua Xu, Salesforce ANZ FDE.
