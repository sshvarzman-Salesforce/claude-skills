---
name: agentforce-skills-research
description: Research Agentforce configuration patterns — topics, actions, instructions, CLTs, knowledge, planner behavior. Searches Salesforce docs, Trailhead, internal repos (git.soma), Slack channels, and Google Docs to find working examples, known issues, and best practices.
tools: [mcp__plugin_search_search__search, mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_search_public, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_google_google__docs_search, mcp__plugin_google_google__docs_get, mcp__plugin_codesearch_codesearch__search, mcp__plugin_codesearch_codesearch__blob, mcp__plugin_codesearch_codesearch__tree, mcp__plugin_codesearch_codesearch__history, WebFetch, Read, Write, Edit, Agent]
---

# Agentforce Skills Research

> Research how to configure, debug, and optimize Agentforce features — topics, actions, instructions, Custom Lightning Types, knowledge grounding, planner behavior, and more. Pulls from external docs, internal repos, Slack, and Google Docs.

**Invocation:** `/agentforce-skills-research [your question]`

---

## What This Skill Does

You ask a question about building or configuring Agentforce. The skill:

1. **Searches broadly** — external docs (Salesforce Help, Trailhead, developer docs), internal repos (git.soma), Slack channels, and Google Docs
2. **Finds working examples** — real implementations, not just theory
3. **Identifies known issues** — GUS bugs, platform quirks, workarounds
4. **Writes a research artifact** — saves findings to `.agents/artifacts/<topic>-research.md` for future reference
5. **Summarizes key findings** — concise answer with sources

---

## Example Questions

- "How do I configure action chaining in a topic?"
- "What's the correct way to set up a CLT output rendering?"
- "How does the planner decide which action to run next?"
- "What are the known issues with isConfirmationRequired and chain continuation?"
- "How do I set up knowledge grounding with Data Library?"
- "What's the difference between GenAiFunction and GenAiPlannerBundle metadata?"
- "How do context variables work across actions?"
- "What's the best practice for error handling in Apex actions for Agentforce?"
- "How do I make the agent stop asking 'Can I proceed?' before running an action?"
- "What instruction patterns make the planner more reliable?"

---

## Research Pipeline

### Phase 1: Understand the Question

Classify the question into one or more areas:

| Area | What to Search | Key Sources |
|------|----------------|-------------|
| **Topic Configuration** | Topic instructions, scope, classification | Salesforce Help, Trailhead, git.soma examples |
| **Action Setup** | GenAiFunction metadata, Apex patterns, Flow actions, confirmation | Internal repos, CLT-GUIDE.md, REBUILD-AGENT.md |
| **Instructions & Prompting** | Instruction text, sort order, planner directives | Slack (eng channels), working demos |
| **Custom Lightning Types** | DTO pattern, LWC rendering, Lightning Type bundles | CLT-GUIDE.md, pet-travel-demo repo |
| **Knowledge & Grounding** | Data Library, article setup, ADL config, citation behavior | Salesforce Help, Slack, Google Docs |
| **Planner Behavior** | Action sequencing, chain continuation, context handling | Slack (NGS eng), GUS bugs, internal docs |
| **Permissions & Access** | Permission sets, sharing, FLS, Einstein Agent User | Salesforce Help, troubleshooting docs |
| **Deployment & Metadata** | sfdx structure, retrieve/deploy, bundle quirks | git.soma repos, sf CLI docs |

### Phase 2: Search Sources

Search in this priority order. Stop when you have a confident answer — don't search everything if the first source answers it.

#### Source 1: External Docs (Web Search)
```
Search: site:help.salesforce.com OR site:developer.salesforce.com OR site:trailhead.salesforce.com
Query: "agentforce" + [specific topic]

Key PDF (download and read locally):
- Agentforce Implementation Guide (Customer-Facing Agents) — 119 pages, updated Apr 2026
  https://resources.docs.salesforce.com/rel1/doc/en-us/static/pdf/agentforce_implementation_customer.pdf
  Local copy: /tmp/agentforce_implementation_customer.pdf
  Covers: Ideate (p.8-20), Build (p.21-60 — subagents, actions, grounding, permissions),
  Test (p.61-91 — planning, core testing, iteration), Deploy (p.92-111 — connections, routing,
  escalation, website), Monitor (p.112-119 — observability, optimization, session tracing)
```

Good for: Official API docs, metadata reference, setup instructions, release notes, end-to-end implementation guidance.

#### Source 2: Internal Repos (Codesearch)
```
Search git.soma for:
- Working Agentforce configurations (genAiPlannerBundles, genAiFunctions)
- Apex action patterns (@InvocableMethod with Agentforce annotations)
- Lightning Type bundles
- Demo repos with topic instructions
```

Key repos to check:
- `chad-goldsmith/pet-travel-demo` — full working CLT demo
- `chad-goldsmith/sf-demo-skills` — demo patterns + best practices
- `alberto-ruiz/sra-ga-docs` — CX team's SRA GA landing page (all things Service Rep Assistant)
  Live: https://git.soma.salesforce.com/pages/alberto-ruiz/sra-ga-docs/
- Search broadly for `genAiFunction` or `GenAiPlannerBundle` across all repos

Good for: Working code examples, real configurations, patterns that actually deploy.

#### Source 3: Slack (Internal Discussions)
```
Channels to search:
- #agentforce-skills-coworker-collab (C0B2XJ87SBH) — PRIMARY for skills platform updates, APIs, timeline
- #service-assistant-engineering (C06TPK97CCE)
- #sc-service-planner-eng
- #sc-service-planner-leads (C07DVDVH26A)
- #ngs-engineering (C06NDLHQJD7)
- #spa-sf-engineering (C02P450NJ84)
- #help-262-summer26-release
- #soba-engineering (C05UAR03WHY)
- #ai-club (C058L05637W) — cross-cutting AI patterns, agent architecture, tooling, internal adoption
```

Good for: Known bugs, workarounds, recent changes, "why doesn't X work" answers, platform behavior confirmations, AI architecture patterns.

#### Source 4: Google Docs (Internal Design Docs)
```
Search for: "Agentforce" + [topic], "Service Planner" + [topic], "GenAi" + [topic]
```

Good for: Design decisions, architecture docs, PRDs, internal specifications.

#### Source 5: Local Knowledge (Already Known)
```
Check these local files:
- ~/.aisuite/notebook/.agents/artifacts/agentforce-skills-platform-spec.md — OFFICIAL platform spec (Kumar Kasimala)
  → Architecture, SKILL.md frontmatter spec, APIs, data model, shipping OOTB skills, permissions
  → Source doc: https://docs.google.com/document/d/1pOn7zW8P-aYCH0mxKhuOW4FKCgMwE8rmPuX5dZbo29A
- ~/.aisuite/notebook/2026-06-24/agentforce-skills-impact-on-sra.md — SRA impact analysis + architecture proposal findings
  → Source doc: https://docs.google.com/document/d/1n9vr5grKFf1QKkpdtvZeWkIWeHrfFfUdu7oxMkTEgDY
  → Customer-facing agent architecture: live skills, background skills, skill scoping, execute_tool proxy
- ~/.aisuite/notebook/.agents/artifacts/agentforce-skills-customer-agents-architecture.md — Full architecture proposal extraction
  → Execution model, runtime stack, skill scoping, data model, SKILL.md spec, security
- ~/.aisuite/notebook/.agents/artifacts/agentforce-skills-m1-prd.md — M1 Pilot PRD analysis
  → Source doc: https://docs.google.com/document/d/1fE_dz8U1mwPTdyGCk6HwHlGoXPpw0rapt4XNkEanMrc
  → Timeline, scope, 5 global tools, permissions, Skill Builder, customer-facing deferred
- ~/.aisuite/notebook/.agents/artifacts/agentforce-skills-vs-record-companion-actor-framework.md — Skills vs Record Companion comparison
  → Event-driven (RC) vs intent-driven (Skills), convergence points, tension, recommended architecture
  → RC architecture docs: https://docs.google.com/document/d/13hXuGr5o2PZnfgRXE-D85eWNYCOZ1iAWM8sXHsudUlU/edit
- ~/sf-demo-skills/BEST-PRACTICES.md — design patterns and rules
- ~/sf-demo-skills/CLT-GUIDE.md — CLT implementation guide
- ~/sf-demo-skills/SUBAGENT-TEMPLATE.md — subagent creation framework
- ~/pet-travel-demo/skill/REBUILD-AGENT.md — complete action config reference
- ~/pet-travel-demo/skill/TOPIC-INSTRUCTIONS.md — topic instruction example
```

Key companion specs on git.soma (fetch via codesearch):
- `git.soma:kkasimala/skill-builder-specs/SCOPE.md` — project scope
- `git.soma:kkasimala/skill-builder-specs/specs/day1/10-skill-apis-m1/AGENT_SKILLS_ARCHITECTURE.md` — full architecture
- `git.soma:kkasimala/skill-builder-specs/specs/day1/10-skill-apis-m1/AGENT_SKILLS_API.md` — API reference
- `git.soma:kkasimala/skill-builder-specs/Skill_Execution_Agent.yaml` — reference agent

Good for: Proven patterns, things already debugged and documented, official platform architecture.

### Phase 3: Synthesize & Write

Write findings to: `.agents/artifacts/<topic-slug>-research.md`

Use this format:

```markdown
# Research: [Topic Title]
**Date:** [today]
**Query:** [original question]

## Summary
[2-3 sentence answer]

## Key Findings

### [Finding 1 Title]
- **Source:** [where this came from]
- **Detail:** [what was found]
- **Relevance:** [how this answers the question]

### [Finding 2 Title]
...

## Working Examples
[Code snippets, configurations, or screenshots that demonstrate the answer]

## Known Issues / Gotchas
[Platform bugs, non-deterministic behavior, workarounds needed]

## Sources
- [linked source 1]
- [linked source 2]
...

## Still Unknown
[What we couldn't answer — where to look next]
```

### Phase 4: Summarize

Return a concise answer to the user with:
- The key finding (1-2 sentences)
- The most important gotcha or caveat
- Pointer to the full research artifact

---

## Research Depth Levels

| User Signal | Depth | What to Search |
|-------------|-------|----------------|
| Quick question ("how do I...") | **Light** | Local knowledge + one web search. 2-min answer. |
| "Research this" / "find out about" | **Standard** | All sources, write artifact, 5-min deep dive. |
| "Thoroughly investigate" / "comprehensive" | **Deep** | Multiple search angles, cross-reference findings, verify with Slack threads, 10-min research. |

Default to **Standard** unless the user signals otherwise.

---

## Important Rules

- **Always cite sources** — never present findings without attribution
- **Distinguish confirmed from speculative** — if a behavior is only observed (not documented), say so
- **Date your findings** — platform behavior changes across releases. Note the release/date of any source.
- **Check the release** — Agentforce features change significantly between 262, 264, and beyond. Note which release a finding applies to.
- **Don't conflate Guidance Plans and Dynamic Plans** — they're different features with different behavior
- **"Works in demo" ≠ "works in production"** — note when something is demo-only or has reliability caveats
- **Save useful findings** — even if the user's question is quick, if you find something novel, save it to the artifact folder for future reference
