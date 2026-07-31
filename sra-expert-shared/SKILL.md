---
name: sra-expert-shared
description: Shared SRA knowledge base for FDEs and SEs. Answers questions about Service Rep Assistant architecture, plan types, channel-specific behavior, knowledge grounding, and implementation patterns. Uses public channels and shared docs only.
tools: [mcp__plugin_slack_slack__slack_search_public, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, Read]
---

# Service Rep Assistant Expert (Shared)

> **SRA knowledge base for Forward Deployed Engineers and Solution Engineers.**
> Answers questions about SRA product architecture, plan types, channel setup,
> knowledge grounding, action configuration, and common implementation patterns.
> Built on public channels and shared documentation — no private dependencies.

**Invocation:** `/sra-expert-shared [your question]`

---

## Getting Started

**Prerequisites:**
- Slack access (for live channel search)
- Access to the SRA Beta Docs Hub (request from your PM or SRA product team)

**Installation:**
Copy this skill's `SKILL.md` into your `~/.claude/skills/sra-expert-shared/` directory.

**No other dependencies** — this skill uses Slack search and built-in knowledge only.

**Related skills (same repo):**
- `sra-setup-debug` — automated org diagnostic ("why isn't SRA working?")
- `sra-agent-debugger` — session-level trace and action analysis
- `sra-analytics` — usage metrics and reporting queries

**Shared skills repo:** https://git.soma.salesforce.com/chad-goldsmith/claude-skills

---

## What This Skill Answers

| Question Type | Example | Where it looks |
|---|---|---|
| Product fundamentals | "How do Dynamic Plans differ from Guidance Plans?" | Built-in knowledge |
| Channel setup | "How does SRA activate on Messaging?" | Built-in + Beta Docs |
| Knowledge grounding | "Why aren't my KAs showing in plans?" | Built-in + Slack |
| Action configuration | "How do I wire a custom Apex action?" | Built-in + Beta Docs |
| Troubleshooting | "Why does my plan say no relevant topics?" | Built-in + Slack patterns |
| Feature status | "Is voice GA yet?" | Slack channels |
| Best practices | "How should I structure subagents?" | Beta Docs Hub |

---

## Built-In Knowledge

### SRA Product Architecture

**What is SRA?**
Service Rep Assistant (SRA) is an employee-facing AI agent that assists human service reps during customer interactions. The rep is always the human in the loop — SRA suggests, the rep decides.

**Plan Types:**

| Feature | Guidance Plans | Dynamic Plans |
|---------|--------------|---------------|
| **What it does** | Static step-by-step plans from knowledge articles | AI-generated plans with executable actions |
| **Channels** | Case (GA) | Case (GA July 21), Messaging (GA July 21), Voice (Closed Beta) |
| **Grounding** | Knowledge Articles only | Knowledge + Actions + Instructions + Related Records |
| **Interactivity** | Rep reads and follows steps | Rep can execute actions, ask questions, redirect |
| **Agent Chat** | Optional — must enable manually from Setup page. Not proactive. | Enabled by default. Complements active workflow. |
| **Actions in plan** | Only via Quick Actions (buttons in steps) or Agent Chat | Surface directly in plan steps; can auto-execute |
| **Agent Builder** | Legacy Agentforce Builder only | Legacy Agentforce Builder only (new builder support coming) |

**Plan Structure (Dynamic Plans):**
Plans follow a 4-header model:
1. **Gather Information** — collect context, verify identity, understand the issue
2. **Work the Issue** — investigate, run actions, check policies
3. **Resolve** — take action, confirm with customer
4. **Wrap Up** — summarize, set expectations, close

**Plan Generation Pipeline:**
1. **Detect** — Customer utterances trigger eligibility check
2. **Plan** — Planner generates a plan using context (case details, knowledge, instructions)
3. **Outcome** — Plan executes steps, actions fire, rep interacts

**How Classification Works:**
- Topic classifier reads ONLY `Case.Subject` + `Case.Description`
- Custom fields in Service AI Grounding are NOT used for classification
- If routing info lives in custom fields → use a record-triggered Flow to append classification tokens to Description

---

### Channel-Specific Behavior

#### Case Channel
- **Simplest setup** — fewest moving parts
- **Context variable:** `ContactId` (auto-populated from the Case record)
- **Activation:** Case assigned to an agent-enabled Omni-Channel queue
- **No eligibility flow needed** — activates on case assignment

#### Messaging Channel (MIAW / Embedded Chat v2)
- **Most complex** — #1 source of setup failures
- **Context variable:** `currentRecordId` → resolves to **MessagingSession ID** (NOT ContactId!)
- **Contact resolution:** Apex must query `MessagingSession.EndUserContactId`
- **Activation:** Customer sends messages → Eligibility Flow returns `isEligible = true` → agent activates after ~5 utterances
- **Auto-Start Dynamic Plans:** Optional toggle in Setup page. When enabled, plan starts automatically after eligibility + 5 messages — no "Start Plan" button shown to rep.
- **Extra perm required:** `AgentMessagingAccess` (without it, agent can't read Conversation Entries)
- **Critical gotcha:** `ContactId` is Case-only. Using it on messaging → null → actions fail silently.
- **Service Replies:** Independent capability — plan steps do NOT ground on service replies, and vice versa. They coexist in the component but don't share context.

#### Voice Channel (Service Cloud Voice)
- **Context variable:** `currentRecordId` → resolves to **VoiceCall ID**
- **Contact resolution:** `VoiceCall.RelatedRecordId` (may be Contact, Lead, or Account)
- **Activation:** Call routed through IVR/Flow → lands in agent-enabled queue
- **Extra perms:** Service Cloud Voice User, telephony adapter access
- **Transcript:** Requires real-time streaming from telephony adapter for during-call context

#### Contact Resolution Pattern by Channel

```apex
// Case — direct (already on the context)
Id contactId = ContactId; // context variable

// Messaging — resolve from MessagingSession
MessagingSession ms = [SELECT EndUserContactId FROM MessagingSession WHERE Id = :currentRecordId];
Id contactId = ms.EndUserContactId;

// Voice — resolve from VoiceCall
VoiceCall vc = [SELECT RelatedRecordId FROM VoiceCall WHERE Id = :currentRecordId];
Id contactId = vc.RelatedRecordId; // may be Contact, Lead, or Account
```

---

### Knowledge & Grounding

**How Knowledge Works in SRA:**
1. Knowledge Articles are published and indexed into a Data Library
2. When a plan generates, the planner retrieves relevant articles via vector search
3. Retrieved content is injected into the plan generation prompt
4. Plan steps reference the knowledge (citations appear in Guidance Plans, not always in Dynamic)

**Why Knowledge Fails (Common Causes):**

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Articles not appearing in plans | Summary field is blank | Fill the Summary field — it drives retrieval matching |
| Articles exist but aren't indexed | Data Categories assigned without category visibility on agent perm set | Grant Data Category visibility, rebuild search index |
| Only partial steps from long article | Token budget limits how much is injected | Break 15+ step articles into smaller focused articles |
| Wrong article pulled | Title/Summary keywords mislead retrieval | Rewrite Summary with customer-voice keywords |
| "No information in your documents" | LLM fallback — knowledge retrieval returned nothing | Check indexing, Summary field, category visibility |

**System Knowledge vs. Runtime Knowledge (Dynamic Plans):**

Dynamic Plans retrieve knowledge via TWO paths:

| Path | When | Query | In prompt for... |
|------|------|-------|-----------------|
| **System knowledge** | Once at plan start | Case Subject + Description (HLS) | Every turn (persists in context) |
| **Runtime knowledge** | Every turn | User's latest message + topic | That turn only (re-fetched each time) |

**Important:** Citations currently only track runtime knowledge. If the agent answers correctly but shows `citedReferences: []`, it may be using system knowledge — this is a known gap, not hallucination. Verify by comparing the answer against published articles manually.

**Knowledge Article Best Practices:**
- Keep Summary field filled with customer-voice keywords (how a rep would describe the issue)
- One article per procedure (not mega-articles with 20+ steps)
- Use `FAQ_Question__c` custom field for trigger phrases
- Avoid Data Categories unless necessary (they add a permission dependency)
- Rebuild search index after publishing new articles

---

### Action Configuration

**How Actions Work:**
- Actions are Apex Invocable Methods or Flows registered in Agent Builder
- They execute as the `EinsteinServiceAgent User` (NOT the logged-in rep)
- All permission checks happen against the agent user's permission sets

**Common Action Patterns:**

| Pattern | Implementation |
|---------|---------------|
| Read customer data | Apex `without sharing` + query by Contact/Case ID |
| Execute a business process | Flow or Apex triggered by action, returns structured result |
| Display a card (CLT) | Action returns data + Output Rendering configured with Lightning Type |
| External callout | Apex + Named Credential + Remote Site Setting |

**Why Actions Fail Silently:**

| Failure | Root Cause | Fix |
|---------|-----------|-----|
| 0 rows returned | `with sharing` on Apex (agent user has no record sharing) | Switch to `without sharing` |
| Fields return null | Missing FLS on agent user's permission set | Grant field Read access |
| "I cannot do this automatically" | `isUserInput: true` on action inputs | Set to `false` in Apex class |
| Action never fires | Not mapped to topic, or topic description doesn't match conversation | Add to topic, rewrite description |
| Card renders as text | Output Rendering not configured, or missing `show_command` directive | Set Lightning Type + add render instruction |
| Generic error | Agent user can't access Apex class | Add Apex class to permission set |

**Asset Library Caching Gotcha:**
> If you add new `@InvocableVariable` fields to an Apex class AFTER it was first added to
> Asset Library, Agent Builder still sees the OLD schema. Fix: **delete** the action from
> Asset Library (not just the topic), then re-add. Do NOT version — just delete and re-add.

---

### Permission Model

**Two users matter:**

| User | Role | What it needs |
|------|------|--------------|
| **EinsteinServiceAgent User** | Executes actions at runtime | Object/field access, Apex class access, sharing rules don't apply if `without sharing` |
| **CSR (Service Rep)** | Sees the plan in their console | Service Planner Agent User perm set, channel-specific perms |

**Critical Permission Sets:**

| Permission Set | Purpose | Without it... |
|---|---|---|
| Service Planner Agent User | CSR can see/interact with plans | No Service Assistant component visible |
| Service Planner Builder | Admin can configure Service Assistant | Setup page inaccessible |
| Prompt Template User | Rep can view Case Catch-Up card | Card doesn't render for that rep |
| Prompt Template Manager | Admin can configure insight prompt templates | Can't activate/edit templates |
| AgentMessagingAccess | Agent reads Conversation Entries | No transcript context on messaging |
| Data Cloud Architect / User | Session traces + advanced grounding | Traces fail (SRA still works) |
| Apex class access (on agent perm set) | Agent can invoke custom actions | Generic failure, no clear error |
| Object/Field access (on agent perm set) | Agent can read/write data | Silent null fields or 0 rows |
| Data Category Visibility | Agent can access categorized KAs | Articles skip indexing silently |

**Licensing (GA — July 21, 2026):**

| License | What it unlocks |
|---------|----------------|
| Agentforce for Service (or Agentforce 1) | Base platform |
| Service Planner Add-On | Service plans (guidance + dynamic) |
| Service Assistant Adaptive Experience Add-On | Agent Chat + Case Catch-Up & Insights |

---

### Agent Chat

**What it is:** A two-way chat interface in the Service Assistant component. Reps can ask questions, request clarification, search knowledge, or ask the agent to perform actions.

**Behavior by plan type:**

| Aspect | Dynamic Plans | Guidance Plans |
|--------|--------------|----------------|
| **Enabled by** | Default (auto with dynamic plans) | Manual toggle on Setup page |
| **Agent proactivity** | Yes — plan adapts, suggests actions | No — rep must ask for everything |
| **Actions in plan steps** | Yes — Agentforce Actions surface in steps | No — only Quick Actions (buttons) in steps |
| **Actions via chat** | Yes | Yes (requires standard subagent) |
| **Conversation tied to** | Record (all reps see same thread) | Record (all reps see same thread) |

**Standard subagents (extend chat capabilities):**

| Subagent | What it adds |
|----------|-------------|
| **General CRM** | Get Record Details, Query Records, Draft Email, Update Record, Answer Questions with Knowledge, Identify Record by Name, General FAQ |
| **General FAQ** | Answer Questions with Knowledge only (subset of General CRM) |

Without at least one subagent, chat only works within current plan + record context.

**Key considerations:**
- Chat thread is shared across all reps working the same record
- English only (no translation support)
- On messaging, chat is only available during active session
- Chat does NOT have context from Case Catch-Up & Insights or Service Replies
- Quick Actions (guidance plan step buttons) cannot be invoked from agent chat

---

### Case Catch-Up & Insights

**What it is:** A card in the Service Assistant component showing AI-generated case context. Works as a **standalone capability** — no agent setup required.

**Requirements (minimal):**
1. Service Assistant turned on from Setup page
2. Service Assistant LWC added to case record page
3. Activate each insight's prompt template in Prompt Builder

**Four insights:**

| Insight | Data Source | Prompt Template |
|---------|-----------|-----------------|
| **Engagement Summary** | Case Subject + Description (customizable) | Summarize Case Engagement |
| **Opening Sentiment** | Customer Signals Intelligence (must be configured) | None (generated by CSI directly) |
| **Account Summary** | Account Name + Description (customizable) | Summarize Related Account |
| **Analytics** (Health Score 0-100) | Case age, reopens, escalations, SLA, sentiment | Calculate Case Health Score |

**Critical behaviors:**
- Card generates **once** when first rep opens the case — never refreshes
- Data is locked at generation time — updates to case/account don't propagate
- All reps see the same card regardless of their individual permissions
- If first rep lacks CSI access, sentiment is permanently omitted for that case
- Supported with BOTH guidance and dynamic plans
- Does NOT draw down flex credits

**Health Score formula (default weights):**
- Ticket Age: 25% (0 at ≥72h)
- Customer Sentiment: 25% (POSITIVE=100, NEGATIVE=20)
- Reopens: 10% (0=100, 2+=low)
- SLA Status: 40% (compliant with time remaining vs violation)
- Penalties: -50 if currently escalated, -5 if past escalation

---

### Multiple Service Assistant Agents

You can deploy **up to 100 specialized agents**, each with its own subagents, instructions, and data libraries. Use this to specialize by business unit, product, or service category.

---

### LLM Fallback & Guardrails

**The Problem:** Without explicit control, the LLM will improvise answers from training data when knowledge retrieval returns nothing. This produces plausible-sounding but potentially wrong responses.

**2-Layer Control Pattern:**

1. **Instruction 0 (highest priority):**
   > "ONLY answer questions using information from your knowledge base and approved actions. If you cannot find relevant information in your documents, say: 'I don't have specific information about that in our knowledge base. Let me connect you with a specialist.'"

2. **Action description reinforcement:**
   > "Search the knowledge base for [topic]. ONLY cite information found in the results. Do not supplement with general knowledge."

**Why Layer 2 matters:** Instructions can be overridden by strong user prompts. The action description is processed at a different stage and provides a second guardrail.

---

## Live Knowledge Sources

### Slack Channels (Public — Searchable)

| Channel | What's discussed | Channel ID |
|---------|-----------------|------------|
| #service-assistant-pm-se-ta-ea-fde-collab | SE/FDE questions, setup issues, field feedback, workarounds | C08E300HPUK |
| #temp-sra-fde-pioneers | FDE implementation teams, beta testing, advanced debugging | C0AN1E181M3 |
| #sc-service-planner-eng | Core eng team — plan generation, knowledge grounding, patch releases, Splunk patterns, gates | C06TPK97CCE |

**How to search:**
- Use Slack search with keywords + channel filter
- Look for threads with PM responses (Chad Goldsmith, Lihang Pan, Bingbing Wu) for authoritative answers
- Recent messages (last 30 days) are most relevant for feature status

### SRA Dynamic Experience Beta Docs Hub

**Hub document:** https://docs.google.com/document/d/14U2OGYFGe4S4GOECMBWgvzSyfAu1snjtMkPA__WfnxQ/edit

| Document | What it covers | Doc ID |
|----------|---------------|--------|
| Implementation Guide — Case | Full setup for Case channel | `1ptRJz7ckEc-LnLtXZH6-gKK3dDzbdFBo3_lCmqAzeVQ` |
| Implementation Guide — Messaging | Full setup for Messaging channel | `18o7dnDlgxTwt0eIgQUHW51VDTxDWSQPLtyw4Yiboi3E` |
| Implementation Guide — Voice | Full setup for Voice channel | `1z1hrQGfz551bWVu3qe9hfpScii0d2t3uc0wCG7qqk3Y` |
| Subagent Best Practices | Topic/subagent design patterns | `16sALqGbEuzmNK6ygye6VFCkWXb1dktUOE3cR6uRLhbU` |
| Subagent Design Implementation Guide | Step-by-step subagent setup | `1RZAEWpd3m2lrP78X0nXgyOi4H-74BwSl81MjBl-Am5s` |
| ADL Grounding Best Practices | Autonomous Data Library configuration | `1y1lu7fphcX93k_Qh4CwUe6-kbXH0kfX5C1ATrwufRBs` |
| Knowledge Article Optimization | How to write KAs for SRA retrieval | `1dt338oWnfskwmKQcyX0mI5MJfc339F3kHYhyg4Z3ycs` |
| SRA & Knowledge 101 (Slides) | Overview deck for knowledge grounding | `1w4yQCHEXnUyZQREaYte5Vg49bP3IC1x25ldvjPZ9k2w` |
| KA Grounding Evaluator Prompt | External evaluator for KA quality | `1DeZhbi-9CK2B4O6w3ySvOzv3C3JdHyya2bh9eBOCAEk` |
| Multiple Agent Experience | Multi-agent orchestration (pre-GA) | `1uL0RKkmIINotERVheY_qYd5BOnEvCwtWyGDiX5J3OvQ` |
| Case Catch-Up & Insights | Case context feature (pre-GA) | `1YzdjcJ_L4ASKwjUeZ0dbEF5mYDF456fV4K7K6BDcfEs` |

**Gemini Gems (AI-powered helpers):**
- [Subagent Generator](https://gemini.google.com/gem/1HjREqV7pc9lZk3lgWHzgpkUtkwt7S67Y) — generates topic/subagent configs
- [KA Evaluator](https://gemini.google.com/gem/1trRbj1EXq1JjoXvZIBXZlwWnay_ZGpE9) — evaluates KA quality for SRA grounding

> INTERNAL ONLY — implementation guides shared with customers in PDF format only.

### SRA GA Documentation (Pre-Release)

**Repo:** https://git.soma.salesforce.com/alberto-ruiz/sra-ga-docs (Alberto Ruiz — CX)

| Document | What it covers |
|----------|---------------|
| Service Assistant Feature Overview | Plan types comparison, channel matrix, all features with GA/preview status |
| Agent Chat for Service Assistant | Framework, subagents (General CRM / General FAQ), dynamic vs guidance behavior, setup |
| Case Catch-Up & Insights | 4 insights, prompt templates (full text), health score formula, setup steps |

**GA date: July 21, 2026** — full docs will be on Salesforce Help at that time.

---

## How to Use This Skill

### Step 1: Ask your question
Ask anything about SRA — product behavior, setup, debugging, channel differences, best practices.

### Step 2: The skill searches
Based on your question type:
- **Product fundamentals** → Built-in knowledge (instant)
- **Setup/config** → Built-in + Beta Docs references
- **"Why isn't X working?"** → Built-in patterns + Slack channel search
- **Feature status** → Slack channel search (recent messages)
- **Best practices** → Beta Docs Hub references

### Step 3: Get a sourced answer
Every answer includes:
- Direct answer first (no burying the lede)
- Source cited (doc link, Slack channel, built-in knowledge)
- Date of info (when known)
- Staleness flag (if info is >2 weeks old on a fast-moving topic)
- Next steps suggested (when actionable)

---

## Quick Reference: "I need to..."

| I need to... | Do this |
|---|---|
| Set up SRA on a new org | Read the Implementation Guide for your channel (Case/Messaging/Voice) |
| Debug why SRA isn't activating | Use `sra-setup-debug` skill (automated diagnostics) |
| Trace what happened in a session | Use `sra-agent-debugger` skill with the Case/Session ID |
| Understand why knowledge isn't grounding | Check: Summary field filled? Data Categories visible? Search index rebuilt? |
| Wire a custom Apex action | Apex `without sharing`, `@InvocableMethod`, inputs with `isUserInput = false`, add to Asset Library → Topic |
| Get Contact on Messaging | `currentRecordId` → query `MessagingSession.EndUserContactId` |
| Get Contact on Voice | `currentRecordId` → query `VoiceCall.RelatedRecordId` |
| Display a CLT card | Configure Output Rendering with Lightning Type name + add `show_command` to action description |
| Prevent LLM improvisation | 2-layer: Instruction 0 "only from knowledge" + action description reinforcement |
| Report on SRA usage | Use `sra-analytics` skill for Data Cloud STDM queries |
| Get org enabled for beta | Submit org ID via intake form (ask your PM for the current form link) |

---

## Cross-References

| Skill | Purpose | Repo |
|---|---|---|
| `sra-setup-debug` | Automated org diagnostic — "why isn't SRA working?" | [claude-skills](https://git.soma.salesforce.com/chad-goldsmith/claude-skills) |
| `sra-agent-debugger` | Session trace — "what did the agent do on case X?" | [claude-skills](https://git.soma.salesforce.com/chad-goldsmith/claude-skills) |
| `sra-analytics` | Usage metrics — "how many plans generated last week?" | [claude-skills](https://git.soma.salesforce.com/chad-goldsmith/claude-skills) |
| `sf-clt-builder` | Custom Lightning Type card generation | [claude-skills](https://git.soma.salesforce.com/chad-goldsmith/claude-skills) |
| `build-agentforce-service-demo` | Full demo build process — SFDX, deploy, Agent Builder setup, CLT cards | [sf-demo-skills](https://git.soma.salesforce.com/chad-goldsmith/sf-demo-skills) |

**Shared skills repo:** https://git.soma.salesforce.com/chad-goldsmith/claude-skills
**Demo skills repo:** https://git.soma.salesforce.com/chad-goldsmith/sf-demo-skills

---

## Important

- This skill provides **read-only knowledge** — it doesn't modify orgs or deploy code
- Beta Doc links are INTERNAL — share with customers as PDF exports only
- Channel search results reflect real-time state — info freshness varies
- When in doubt, cross-reference with the official Implementation Guide for your channel
- For private/roadmap questions, escalate to your SRA PM contact
