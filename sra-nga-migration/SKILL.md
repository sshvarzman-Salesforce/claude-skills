---
name: sra-nga-migration
description: Track the migration of Service Rep Assistant (SRA) from the legacy Agentforce Builder (GenAiPlannerBundle / Dynamic Plans) to Next Gen Agent (NGA / Agent Script). A living status tracker — milestones, blockers, decisions, owners, timeline, and impact on existing legacy SRA work. Use when asked about SRA→NGA migration status, what changes in NGA, who owns a piece, or to log/update migration progress from new materials (Slack, docs, meeting notes).
tools: [mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_google_google__docs_search, mcp__plugin_google_google__docs_get, mcp__plugin_codesearch_codesearch__search, Read, Write, Edit, Agent]
---

# SRA → NGA Migration Tracker

> Living record of the Service Rep Assistant migration from **legacy Agentforce Builder**
> (GenAiPlannerBundle, Dynamic Plans, ACC rendering engine) to **Next Gen Agent (NGA /
> Agent Script)**. Purpose: track status, milestones, blockers, decisions, owners, timeline,
> and impact on in-flight legacy SRA work. Keep it sourced and dated; separate confirmed
> facts from open questions.

**Invocation:** `/sra-nga-migration` (optional: a question, channel, or "log this update")

---

## Official sources of truth (check these before relying on the tracker)
- **Atlas Migration Canvas** (Slack F0B4KB951B8) — the live status board (Still Pending /
  Completed, blocker vs. not-a-blocker, owners, TD links). PRIMARY for current status.
- **Google Doc:** "SRA Migration to NGA/Atlas & Agentforce Dependencies"
  `docs.google.com/document/d/1i-l859tWXRVzHB6S44f2x8jLImH_jHwZSDz9gMQsYrU` (the narrative +
  requirements + dated updates).
- **NGA + Atlas Migration Research** doc: `docs.google.com/document/d/1U4GkbJv65sZAZtedD53EaDI7E_Nj1xEGW5GWW-_F27E`
- **SRA Atlas Migration Exploration** (Lihang Pan): https://git.soma.salesforce.com/pages/l-pan/SRA-Atlas-Migration-Exploration/index.html — live exploration/testing site for SRA on Atlas

## Terminology
**NGA** = the whole new stack: new **planner** (aka **Daisy / Daisy++ / Atlas / Python Planner**)
+ new Agent Builder + new Agent types + **Agent Script**. SRA today runs on the **Java Planner**
(legacy GenAiPlannerBundle / Dynamic Plans, ACC rendering engine) — which is **being deprecated**
(the forcing function for migration).

## Why migrating (beyond "forced to")
Forced by deprecation of old-style Agents (AI Cloud team) — but real upside too:
- Live on supported code (Java Planner gets no more fixes/improvements).
- **Model:** 4.0→4.1; multi-model topic classification, customer-configurable.
- **Agent Graph / deterministic capabilities** (Agent Script hooks) → less hallucination, more
  predictable, faster (not always relying on the LLM).
- **Better debugging/tracing:** Preview for templates, AI panel to draft/refine metadata, new
  trace section (see why the agent chose each path).
- **SRA-specific freebies:** Voice Agent features, **citations for free**, **multi-lang for
  free**, knowledge retrieval **in parallel** with topic (perf win).
- New Builder + **Agent API v2 (lower latency)** only work with NGA/Atlas.
- Unified customer experience (no two-functionality split).

---

## Current status
_Last updated from official doc: 6/10/2026_

| Dimension | Status | Notes |
|-----------|--------|-------|
| Overall phase | 🟡 POC in progress | PoC re-attempt of SRA on Daisy++ planned for **264** to re-evaluate gaps (first attempt was Dec 2025) |
| Decision: migrate vs. keep legacy | ✅ Migrating (forced) | Old-style Agents being deprecated |
| Migration tool | 🟡 Exists, needs eval | Old→NGA tool ready on **260.13**; SRA must evaluate completeness for SRA-type agents (auto vs. manual?) |

## Migration plan (phases)
1. 🟡 **PoC** — show SRA can run on Daisy++ even with features missing.
2. ⬜ **Get delivery of blocking issues** (System Prompt Override, Quick Actions, Context Manipulation).
3. ⬜ **Implement the SRA half** of each issue (delivery ≠ done; still need to write/test the tweaks):
   - Write prompt-override text
   - Use new metadata API (replace old slow queries)
   - Write Quick Action setup UI
   - Use new context-manipulation API
4. ⬜ **Migration tool evaluation** — how well does old→Agentscript tool handle SRA-type agents;
   identify gaps / customer-effort areas.
5. ⬜ **Tooling evaluation** — Testing Center existing ≠ SRA works with it.

---

## Blockers / dependencies
_Official **Atlas Migration Canvas** (Slack F0B4KB951B8) is the live status board — classifies
TRUE blockers vs. "not a blocker." Reconciled below (canvas + 6/10 doc)._

### 🔴 TRUE blockers
| Blocker | Owner | ETA | TD / link |
|---------|-------|-----|-----------|
| **System prompt override** ⭐ | Aaron Chan, Stefan Krawczyk, Anuja Verma, Shugang Kang | was Apr/May → **more delay** (Atlas in legal/security review on exposing system prompt; SRA asked for internal-team-first); 6/30 ETA per doc | TD a0nEE0000015YJpYAM · impl group #C0ASRJCBJQ7 |
| **Quick Action Setup UI in NGA builder** | Gabriel Krupa, Tulsi Patel→**Ismaen Aboubakare**, Jon Moore, Sreejesh Nair | **UX design done by end of June**, then team decides who implements | TD a0nEE0000017chVYAQ |
| **Define APIs for Agentforce metadata consumption** (replace slow queries; also req'd for Codey) | Travis Stubbendeck, Tulsi Patel | — | TD a0nEE000001DikDYAS · *needs from SRA: clear requirement doc* |
| **Special Exemption for SRA to use legacy flow** | Sreejesh Nair | target **6/19** | discussion C09B63KHW6S · *old builder no longer lets you create agents in SDB6 → blocks SRA testing* |

### 🟡 NOT blockers (but tracked — perf/correctness/customer-experience)
| Item | Owner | Note |
|------|-------|------|
| **Old→new builder auto-migration tool — DELAYED** | Travis Stubbendeck, Setu Shah, Aron Kale | "**very bad customer experience**" per canvas. Tool was said ready 260.13 but auto-migration delayed → customers may face manual work. PM: Kevin Wang. |
| **Context manipulation w/o restarting sessions** (read/update current_node + context_variables) | Aaron Chan; Magic Johnson (long-running session, ETA **7/31**); Anuja Verma + Sarah Boaz-Shelley (context update) | TD a0nEE00000195HdYAI · holds the multi-user confirmation fix |
| **Agent API V2 generic Java service support from Core** | — | TD a0nEE000001BboTYAS |

### Resolved (since first NGA eval)
- ✅ Old Agent builder → NGA migration tool ready on **260.13**
- ✅ Daisy++ orchestration profiles on custom agent type (TD a0nEE0000017xVpYAI)
- ✅ Support for **custom Agent Templates**
- ✅ Support for **other types of Agent Users**

### 🔴 New/urgent (from migration channels, late May–June 2026)
- **Old builder being turned off mid-migration** — in **SDB6** (latest changes) there's **no way
  to create an agent in the old builder**, which *blocks SRA's current testing*. SRA asked for a
  **"Special exemption for SRA to use the legacy flow"** while migrating. POC: **Sreejesh Nair**
  (define scope with NGS team). (#service-assistant-java-atlas-migration, 6/1)
- **System prompt override — legal/security concerns** surfaced; SRA asked to **enable for
  internal teams first** while those are worked through. Target was end-of-May → now **6/30 ETA**
  (Aaron Chan). (#discuss-w-21862733)
- **Quick Action migration POC changed hands:** Tulsi Patel → **Ismaen Aboubakare** (new POC,
  owns the 2 Agent-Management TDs). Script team is **amenable to treating Quick Actions like
  existing actions** (fit the script architecture, no one-off button). UX alignment needed:
  Amber Bouabdallah (SRA) + Jon Moore (Agentforce). (#sra-quick-action-migration-to-nga)

### ⭐ The multi-user confirmation problem (a deep NGA gap — origin Jan/Mar 2026)
SRA takes input from **multiple sources** (end user AND the service rep), but the Agentforce
planner assumes **"one user, one agent."** So if the AI asks to confirm an action, the **end user
can say "yes" and it's taken as confirmation** — when only the *internal rep's* "yes" should count.
SRA needs the planner to **tag context/utterance sources** and only allow execution/confirmation
on a rep utterance. This is part of the **Context Manipulation** TD (multi-user use cases:
confirmation & session sharing/switching) — Chad owes SRA detail to split that TD.
(#service-plans-ai-cloud-service-cloud-collab, Aaron Fiske 3/23)

### Regressions tracked
- ⚠️ **Topic Scope no longer exists in new planner** → `GenAiPluginDefinition` field becomes null
  on migration → **impacts Service Plan intent-classification prompt** (relies on topic scope).
- ⚠️ **AgentTemplate field missing in BotDefinition** when Agent created with NGA template
  (Bug a07EE00002VDZLVYA5, TD a0nEE0000018KSPYA2) — *was open 4/13, verify current status*.

---

## What changes for SRA in NGA
_(capture the concrete deltas as we learn them)_

| Area | Legacy (today) | NGA (target) | Migration impact |
|------|----------------|--------------|------------------|
| Plan / orchestration | GenAiPlannerBundle, Dynamic Plans | Agent Script reasoning loop | |
| Actions | localActions, build-by-hand in Agent Builder | `reasoning.actions`, `.agent` declarations | |
| CLT rendering | ACC engine, build action by hand (see sra-latency / CLT learnings) | `complex_data_type_name`, show_command (native) | |
| Deploy | `sf project deploy` (GenAiPlannerBundle) | `sf agent publish authoring-bundle` + activate | |
| Channels | Case / Messaging / Voice | | |

---

## Migration requirements (from the doc — the bar NGA must clear)

**1.1 — Inject our own, non-action-focused system prompt** ⭐ (the headline issue)
The Agentforce system prompt tries to link an **Action to everything**. But many SRA customers
have instructions meant as *"tell the human rep to do this"* (not automated, or not doable in
Salesforce). NGA **hallucinates Actions that don't exist** in this situation. On the Java planner
SRA overrides the system prompt to fix this — needs the same on the Python planner.
(TD a0nEE0000015YJpYAM)

**1.2 — Auto-migrate (or minimal-effort) old→new planner agents.** Asking customers to recreate
agents manually "will not fly."

**1.3 — More hallucinations with same inputs.** NGA testing hallucinated that inputs were already
provided / steps already completed. The fix advised ("fine-tune instructions") is a bad customer
story — a working SRA agent upgrading to NGA and getting *worse*. (Re-evaluate after 264 testing.)

### Non-NGA dependencies (SRA/Record Companion ↔ Agentforce)
- **2.1 Stateless API** — SRA wants sessions to last ~forever (months+) and to add context as the
  record progresses, from *outside* the agentic loop. Current session API is append-only + always
  triggers generation → sync problems. Want to manually manage context (esp. multi-agent). Current
  workarounds aren't NGA blockers but hurt perf/correctness. Still a "sore point."
- **2.2 Quick Actions** — native support would close a Guidance-vs-Dynamic-plan gap. Hard in
  turn-by-turn today; NGA + Agent Graph may make it feasible *if* we also get prompt/context
  control. (TD a0nEE0000017chVYAQ)

---

## Decisions log

| Date | Decision | Source | Rationale |
|------|----------|--------|-----------|
| 2026 | Migrate SRA to NGA | Official doc | Forced by Java-planner/old-Agent deprecation + platform upside |
| ~264 | Re-attempt SRA-on-NGA PoC | Official doc | Re-evaluate gaps from Dec 2025 attempt |

---

## Key people & channels
- **Agentforce contacts SRA works with:** Aaron Chan (system prompt override), Travis Stubbendeck
  (metadata API), Nathaniel Price, Magic Johnson (long-running session). Gabriel Krupa + Ismaen
  Aboubakare (Quick Actions). Anuja Verma + Sarah Boaz-Shelley (context update). Kevin Wang (PM,
  migration tool).
- **Additional NGA people:** Lihang Pan (driving migration alignment), Sreejesh Nair (legacy-flow
  exemption POC), Ismaen Aboubakare (Quick Action POC, took over from Tulsi Patel), Amber Bouabdallah
  + Jon Moore (Quick Action UX), Travis Stubbendeck + Kevin Jacovelli (metadata API), Aaron Chan
  (system prompt override), Stefan Krawczyk, Setu Shah, Aron Kale.
- **Channel registry (where migration intel lives):**
  - **#service-assistant-java-atlas-migration** (C09B63KHW6S) — PRIMARY migration channel, TD status,
    weekly sync, legacy-flow exemption.
  - **#sra-quick-action-migration-to-nga** (C0B845D9NJW) — Quick Action migration UX + implementation.
  - **#service-plans-ai-cloud-service-cloud-collab** (C073ET8GV6U) — AI-Cloud↔Service-Cloud collab;
    origin of the blocker list + the multi-user confirmation problem.
  - **#discuss-w-21862733** (C0ASRJCBJQ7) — system prompt override discussion.
  - **#technical-support-new-agent-builder-and-script** (C0AA78YCT9S) — NGA builder/script regressions.
  - **Migration canvas** — all pending TDs (linked in C09B63KHW6S, Lihang Pan 5/20).
- **Related skills:** `sra-latency-research` (NGA gives parallel knowledge+topic retrieval, Agent
  API v2 lower latency, 4.0→4.1 — direct latency overlap), `sra-pm-triage`, `caturday`.

---

## Impact on in-flight legacy SRA work
_(what migration means for things already built — so we don't lose/rebuild)_
- **CLT cards** (profile / seat-map / weather, built via build-by-hand recipe): does NGA
  render these natively? Do the DTOs/LWCs port?
- **Latency optimizations** (per-phase pipeline, prompt compression): carry over or redone?
- **Voice beta** (SCV/TB onboarding): migrates before or after NGA cutover?

---

## How to update this skill
When Chad pastes materials (Slack, docs, meeting notes):
1. Date the update and cite the source.
2. Update the **Current status** table + relevant section(s).
3. Log any new decision in the **Decisions log** with who/why.
4. Flag new blockers/open questions.
5. Keep confirmed facts separate from speculation; note Chad-stated facts as ground truth.
