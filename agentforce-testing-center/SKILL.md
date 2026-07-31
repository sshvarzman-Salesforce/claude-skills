---
name: agentforce-testing-center
description: Test and validate Agentforce Skills platform features against SRA. Tracks access requests, test scenarios, findings, and integration patterns. Use when working with Skills-enabled orgs to understand how skills interact with topics, actions, CLTs, Dynamic Plans, and Record Companion.
tools: [mcp__plugin_search_search__search, mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_search_public, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_slack_slack__slack_send_message, mcp__plugin_google-workspace_vmcp-google-workspace__get_doc_as_markdown, mcp__plugin_google-workspace_vmcp-google-workspace__search_docs, mcp__plugin_codesearch_codesearch__search, mcp__plugin_codesearch_codesearch__blob, WebFetch, Read, Write, Edit, Bash, Agent]
---

# Agentforce Testing Center

> Test, validate, and document how the Agentforce Skills platform works with Service Rep Assistant. Track access, run test scenarios, capture findings, and identify integration patterns and gaps.

**Invocation:** `/agentforce-testing-center [task or question]`

---

## Purpose

The Agentforce Skills platform (M1 pilot Aug 2026) introduces a new modular layer for agents. This skill helps us:

1. **Get access** to Skills-enabled test orgs
2. **Run structured tests** against the Skills APIs and runtime
3. **Validate SRA compatibility** — do skills work alongside topics, CLTs, Dynamic Plans?
4. **Document findings** — what works, what breaks, what's missing
5. **Feed results back** to the agentforce-skills-research skill and SRA impact analysis

---

## Access Status

### Current State
- **SDO:** Does NOT have `orgHasAgentSkillsEnabled()` — confirmed via REST API, SOQL, Tooling API checks
- **Org Farm:** Skills APIs available on 262.12 patch and 264 main
- **Feature flag:** `orgHasAgentSkillsEnabled()` must be flipped per-org

### Who to Contact for Access
- **Kumar Kasimala** (kkasimala@salesforce.com) — Platform owner, has test orgs
- **Avanthika Ramesh** (avanthika.ramesh@salesforce.com) — PM lead, interested in SRA skill patterns
- **Slack:** #agentforce-skills-coworker-collab (C0B2XJ87SBH) — active API/access conversations

### Access Request Template
When requesting access, use this framing:

> We're building SRA demos that use patterns aligned with what Skills is productizing (skill actors via Record Companion, event-driven orchestration, SKILL.md-like instruction bundles). We want to test:
> 1. Can we attach a skill to an SRA sub-agent alongside existing topic actions?
> 2. What's the token budget impact when a skill loads on top of 8 existing actions?
> 3. Do skill instructions conflict with topic instructions during plan generation?
> 4. Can skills reference the same Apex actions that are attached to the topic?

---

## Test Scenarios

Once we have access, run these in order:

### Test 1: Basic Skill Discovery (Validate API works)
```
Goal: Confirm the three-tier progressive disclosure works
Steps:
  1. Call GET /services/data/v67.0/einstein/ai-skills (list skills)
  2. Call GET /services/data/v67.0/einstein/ai-skills/{id} (describe one)
  3. Verify token cost at each tier
Expected: Tier 1 returns name+description (~100-150 tokens), Tier 2 returns full instructions
```

### Test 2: Create a Minimal Skill
```
Goal: Author a simple skill via REST API
Steps:
  1. POST /einstein/ai-skills with a basic SKILL.md (name, description, one tool)
  2. Create a version and publish it
  3. Verify it appears in the skill catalog
Skill to create:
  name: pet-travel-greeting
  description: Greet the customer and identify their pet travel needs
  tools: [Get Record]
  instructions: "Retrieve the customer profile and greet them by name."
```

### Test 3: Attach Skill to SRA Sub-Agent (Critical)
```
Goal: Test if a skill can coexist with existing topic configuration
Steps:
  1. Use existing Pet Travel Booking topic (8 actions, CLT outputs, context variables)
  2. Attach the pet-travel-greeting skill to the same sub-agent
  3. Start a messaging session and observe:
     - Does plan generation still work?
     - Are skill instructions visible in the planner context?
     - Do existing action descriptions conflict with skill instructions?
     - Does CLT rendering still fire?
Expected: Plan generation works but with higher token usage
Risk: Instruction collision between skill and topic
```

### Test 4: Token Budget Measurement
```
Goal: Quantify the cost of skills on SRA plan generation
Steps:
  1. Run a standard pet demo session WITHOUT any skills attached → capture token usage
  2. Attach one skill → run same scenario → capture token usage
  3. Attach two skills → run same scenario → capture token usage
  4. Compare: baseline vs +1 skill vs +2 skills
Metrics: Plan generation tokens, total session tokens, time-to-first-plan
```

### Test 5: Skill + Dynamic Plan Interaction
```
Goal: Understand how skills interact with Dynamic Plans (SRA's core feature)
Steps:
  1. Start a messaging session that triggers a Dynamic Plan
  2. Mid-plan, does the skill remain available?
  3. Can the planner reference skill instructions while executing a plan step?
  4. Does skill context clear when expected (topic exit)?
Questions to answer:
  - Do skills add instructions to the plan context or are they separate?
  - Can a skill's execute_tool be called as part of a Dynamic Plan step?
  - What happens if skill instructions say "do X" but plan says "do Y"?
```

### Test 6: Skill + CLT Rendering
```
Goal: Test if CLT output rendering works when actions are called via skill's execute_tool
Steps:
  1. Create a skill that references GetPetProfile (which has CLT output rendering configured)
  2. Execute the skill → does the CLT card render in the sidebar?
  3. Compare: same action called via topic (normal) vs via skill execute_tool
Expected: CLT rendering likely DOES NOT work via execute_tool (skill runtime proxies the call,
  but CLT rendering is configured per-action in Agent Builder, not in the skill)
This would confirm Challenge #2 from our SRA impact analysis.
```

### Test 7: Record Companion + Skills Coexistence
```
Goal: Understand if RC skill actors and Agentforce Skills can operate simultaneously
Steps:
  1. Have Record Companion fire Conversation Catchup (event-driven)
  2. Have an Agentforce Skill fire on the same session (intent-driven)
  3. Do they conflict? Do they share context? Does the agent see both?
Questions:
  - Does RC's actor framework know about Agentforce Skills?
  - Can an Agentforce Skill trigger a RC skill actor (or vice versa)?
  - Is there shared state between them?
```

---

## Testing Center Quick Reference

### What It Does
- Tests non-deterministic agent responses at scale before deployment
- Previews topic classification for test utterances
- Explores action sequences at scale
- AI-generated test cases (from metadata + CRM data)
- LLM judge evaluates expected vs actual response (score 0-5, ≥3 = PASS)

### Enablement
- **Sandbox:** Auto-enabled where Agentforce is available
- **Non-sandbox:** Turn on perm `TestingCenterUI` from blacktab
- **Prod:** NOT recommended (no mocking — data-change actions alter real data)
- **Prerequisites:** Agentforce activated, test utterances in CSV template format, file upload enabled

### Limits
- Max test cases per job: **500**
- Max jobs per hour: **10**
- ~5 seconds per test case (varies)
- Keep evaluations to 20-30 test cases for faster results (shared queue)

### Evaluation Method
- **Topic & Action:** Exact match (expected vs actual)
- **Response:** LLM judge scores 0-5 (≥3 = PASS)
- Expected Response categories: (1) clear utterance → specific response, (2) unclear → expect clarifying questions, (3) real-time inquiry → high-level description of expected behavior

### Next Gen Testing (Agentforce Studio)
- Open Beta targeted 12/05/2025 (258.12)
- Test Suite as metadata, custom evals, saved Test Runs, regression analysis
- Different product from Agentforce Grid (but uses Grid's flexible UI)

### Roadmap Highlights (SRA-Relevant)
- **Now:** CSV upload, topic/action/response evals, test case generation, Agent Testing API/CLI
- **May-Aug 2026:** Multi-turn testing, mocking for standard actions, state injection (conversation history), multi-modal evals (Voice), explain failures + recommend fixes
- **Sep-Dec 2026:** Autonomous testing agents, multi-agent evals, A/B testing, auto-optimization

### Key Questions for SRA Testing
1. Can we test SRA sub-agent behavior (Dynamic Plans) via Testing Center?
2. Does Testing Center support testing RC-triggered skills (event-driven, not utterance-driven)?
3. Can state injection simulate an in-progress case for mid-conversation testing?
4. How do we test CLT rendering outcomes (Testing Center is text-only)?
5. Can we use the API/CLI to run regression tests on SRA after config changes?

---

## Test Log

Track results here as tests are executed:

```
| Date | Test # | Org | Result | Notes |
|------|--------|-----|--------|-------|
| (pending access) | | | | |
```

---

## Key Questions to Answer

Priority order — answer these to inform SRA roadmap:

1. **Can skills and topics coexist on the same sub-agent without instruction collision?**
2. **What's the actual token cost of attaching a skill to an existing 8-action topic?**
3. **Does CLT output rendering work when actions are called via execute_tool proxy?**
4. **Can Dynamic Plans reference skill-provided instructions?**
5. **Is there a path to make Record Companion skill actors into proper Agentforce Skills?**
6. **Can skills carry context variable bindings? (or is that still Agent Builder only?)**
7. **What happens to HiL (isConfirmationRequired) when an action is called via skill proxy?**

---

## Reference Materials

### Local Research Artifacts
```
- ~/.aisuite/notebook/.agents/artifacts/agentforce-skills-platform-spec.md
- ~/.aisuite/notebook/.agents/artifacts/agentforce-skills-customer-agents-architecture.md
- ~/.aisuite/notebook/.agents/artifacts/agentforce-skills-m1-prd.md
- ~/.aisuite/notebook/.agents/artifacts/agentforce-skills-vs-record-companion-actor-framework.md
- ~/.aisuite/notebook/2026-06-24/agentforce-skills-impact-on-sra.md
```

### Testing Center Docs
```
- Testing Center FAQ (Internal): https://docs.google.com/document/d/1UojEBOIsdnFo5klCyC-MomG9sPj3h7SnYgmKxe3UTjw
  → Comprehensive FAQ: Next Gen Testing (Open Beta 258.12), functionality, pricing/packaging, roadmap
  → Key info: up to 500 test cases/job, 10 jobs/hour, ~5s per test case, LLM judge scores 0-5 (≥3 = PASS)
  → Roadmap: Jan-Apr (OOTB evals, custom evals, test gen, API/CLI), May-Aug (multi-turn, mocking, RAG evals,
    voice, regression), Sep-Dec (A/B testing, autonomous testing agents, auto-optimization)
  → Enablement: auto-enabled in Sandbox; non-sandbox needs "TestingCenterUI" perm from blacktab
  → Pricing: Conversation SKU ~$7.2/10 tests; Flex Credits ~$4.8/10 tests; A4X admins = unmetered
- Testing Center Help Article: https://help.salesforce.com/s/articleView?id=ai.agent_testing_center.htm&type=5
  → Customer-facing documentation (requires browser to render)
- Testing Center Demo Video: https://drive.google.com/file/d/1dZvoho4TT_VZp8UgX4A2573eBxMfS080/view
- Testing Center with Data Gen Demo: https://drive.google.com/file/d/1ypqkELnI3ryVY2WTJj5XZwLMaxTLHjDw/view
- Next Gen Testing Prototype (DF 2025): https://drive.google.com/file/d/1pelo-Yo3Imz8rwu928Sx6B_BWDr2ECJa/view
- First Call Deck: https://docs.google.com/presentation/d/1GcKmoMHSmaqzSz6Cts1gUHTInogVFlEgf1_7gQ4fXuQ/edit
- Pricing Deck: https://docs.google.com/presentation/d/1PYx73oZeCBGgzicu_09QD2jNo38081VAL1UnApmsZyQ/edit
```

### Skills Platform Docs
```
- Agentforce Implementation Guide (Customer-Facing): https://resources.docs.salesforce.com/rel1/doc/en-us/static/pdf/agentforce_implementation_customer.pdf
  → 119 pages, Apr 2026. Build (subagents, actions, grounding), Test (planning, core, iteration), Deploy, Monitor
- Platform Spec: https://docs.google.com/document/d/1pOn7zW8P-aYCH0mxKhuOW4FKCgMwE8rmPuX5dZbo29A
- Architecture Proposal: https://docs.google.com/document/d/1n9vr5grKFf1QKkpdtvZeWkIWeHrfFfUdu7oxMkTEgDY
- M1 Pilot PRD: https://docs.google.com/document/d/1fE_dz8U1mwPTdyGCk6HwHlGoXPpw0rapt4XNkEanMrc
- Record Companion Architecture: https://docs.google.com/document/d/13hXuGr5o2PZnfgRXE-D85eWNYCOZ1iAWM8sXHsudUlU/edit
- Skills Integration with Agents: https://docs.google.com/document/d/1lKu71HZvQPHSmc6AKkcVh4nF6Ez1bd8CzWEFdKbUONY/edit
- Coworker x Skills Integration: https://docs.google.com/document/d/1MqAD2uh7WwQifF-shb1oP6JmezS954e8r8Jr1Q1BXNk/edit
```

### Slack Channels
```
- #ai-testing-enablement-and-feedback (C07DNKV0WPP) — PRIMARY for Testing Center support, bugs, enablement
  → Active support channel: structured ticket format, Splunk debugging, customer issues
  → Team handles: stuck jobs, permission questions, version mismatches, event subscription issues
- #agentforce-skills-coworker-collab (C0B2XJ87SBH) — Skills platform access + API updates
- #service-assistant-prompt-builder-collab (C08UHTET1SB) — RC/Skills convergence discussions
- #agentforce-for-service-sra-skills-collab (C0ALR011W9F) — SRA skill tracking
- #service-assistant-messaging-component-skill (C0AEBTMGNCD) — Messaging component skill (264)
- #ai-club (C058L05637W) — cross-cutting AI patterns, agent architecture, tooling
```

### API Reference (once access is granted)
```
Base: /services/data/v67.0/einstein/ai-skills/

Endpoints:
  GET  /einstein/ai-skills              — List/search skills
  POST /einstein/ai-skills              — Create skill
  GET  /einstein/ai-skills/{id}         — Get skill details
  PUT  /einstein/ai-skills/{id}         — Update skill
  DELETE /einstein/ai-skills/{id}       — Delete skill
  GET  /einstein/ai-skills/{id}/versions         — List versions
  POST /einstein/ai-skills/{id}/versions         — Create version
  PUT  /einstein/ai-skills/{id}/versions/{vid}/status?action=PUBLISH  — Activate
  GET  /einstein/ai-skills/{id}/versions/{vid}/assets  — List assets
  POST /einstein/ai-skills/{id}/versions/{vid}/assets  — Upload asset

Deploy via CLI:
  sf project deploy start --metadata AgentSkill:MySkill
  sf project retrieve start --metadata AgentSkill:MySkill
```

---

## Findings Log

Document key findings as they emerge:

### (Pending — awaiting org access)

---

## Rules

- **Always log results** — even negative results ("it didn't work") are valuable
- **Compare with/without** — always test the same scenario with and without skills for comparison
- **Capture token counts** — token budget impact is the #1 question for SRA
- **Screenshot errors** — platform errors during pilot may be transient; capture them
- **Note the release** — behavior changes across patches; always note which release/patch you're testing on
- **Feed back** — update the SRA impact analysis and research artifacts with findings
