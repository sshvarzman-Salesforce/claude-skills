---
name: sra-latency-research
description: Research and analyze Service Rep Assistant (SRA) latency, and evaluate proposals to reduce it — especially PISA (Proactive In-Meeting Support Agent) from Salesforce AI Research as a real-time intent/insight signal. Use when investigating SRA response times, the 5-turn trigger, summary-plan generation, Agentforce round-trip latency, or any "make SRA faster" proposal. Researches internal Slack, docs, and engineering sources; produces sourced findings and a clear-eyed assessment of what a proposal can and cannot fix.
tools: [mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, mcp__plugin_google_google__docs_search, mcp__plugin_google_google__docs_get, mcp__plugin_codesearch_codesearch__search, Bash, Read, Write, Edit, Agent]
---

# SRA Latency Research

> Investigate Service Rep Assistant latency and evaluate proposals to reduce it.
> Built around the PISA-into-SRA opportunity (June 2026) but reusable for any
> SRA performance / "make it faster" question. The job is to find the facts,
> map each proposal to the SPECIFIC latency source it can (and can't) address,
> and give Chad an honest, sourced assessment — not a hype summary.

**Invocation:** `/sra-latency-research` (optional: a specific proposal, channel, or question)

---

## Background timeline (the latency/voice story goes back to Sept 2025)
This is NOT new — the latency + intent-detection + SLM thinking has a 9-month arc.
Sourced from meeting notes (cite by date):

- **Sept 24, 2025 — "Speech to Speech (Sasha) & Service Cloud"** (Chad, John Emmons,
  Aaron, Bingbing, Itai Asseo, Naveen Kodali): First latency/cost discussion.
  - SRA = LWC surface calling Agentforce via APIs; listens to transcript, passes utterances.
  - **Failed topic detection costs 90 Einstein requests each** → customers turning the
    feature OFF on Case GA due to cost. "Fail fast and cheap" principle established.
  - 4 prompts, one ~7,000 of 8,000 tokens — too big for SLMs without distillation.
  - **John Emmons' "Label Force"** (data annotation for training SLMs) + **"flash topic
    classifier"** introduced as the intent-detection direction. Prompting a 4o-mini / 4.1-nano
    might beat the classifier on cost/perf.
  - **262 strategy = 75% optimization.** Summary-plan trigger was "10 utterances" then.
- **Oct 29, 2025 — "Eng sync on SA for Voice"** (Bingbing, Jon Hanson, Kexin, Aaron):
  Voice architecture deep dive. Initial Agentforce voice latency **~10s per generation**.
  - **Transcript engines differ:** SCV = **Amazon Transcribe**; Thunderbird (TB) =
    **Einstein Speech Foundations (fronts Deepgram or similar)**. Transcription latency is
    **vendor-side (Amazon), often the main delay, NOT in SRA's control.**
  - Context-relevancy detection needed to avoid generating plans on small talk (costly).
    Then rule-based 10-utterance threshold; exploring LLM/AI relevancy + topic classification.
  - **FlashTopic Model** (fine-tuned on Qwen for topic classification) — POC Shiva Raaj Kotni,
    rolling out in AF ~Sept 6.
  - Naveen Jaini (Service Cloud Perf) = the Agentforce-voice latency-optimization expert.

## Architecture (from the Tech Deep Dive doc)
- Flow: Producer → Kafka topic → CS Event Listener → **ART Broker** → **ART Provider**
  (MS Record Actor → Conversation Catchup Skill Actor + Service Plan Skill Actor) →
  invokes **Summary Plan Generation Service** + **Dynamic Plan Service**. The
  **Service Assistant UI** (Client 2) reads Record Companion Interaction Data.
- **RC (Record Companion) life cycle:** starts on **owner-change event** (CSR joins);
  ends on **call-close/status-change event**. Mapping conversationId ↔ VC record Id is
  done via the owner-change event.
- **VC life cycle:** SCV = one VC record **per service rep** (new record on transfer →
  new RC → new SA). TB = one VC record **per call** (multiple CSRs share). This is the
  root of the warm-transfer race condition that drops plans.
- SRA serves a **record, not an agent**. Live-conversation plans use the **current
  record owner** as user context; CSR-initiated UI requests use that CSR's context.
- **⭐ James Barker's "Relevancy Gate" design (Oct 2025)** — the conceptual ancestor of
  the PISA pitch. A gate that decides "wait for more context vs. respond now" via
  Relevancy Rules (Learning Loop / Agent Session / Waiting_For_More_Context) + a
  Context Enhancer (second LLM call with full transcript). AI Agents invoked ONLY when
  the relevancy gate says relevant. So PISA's "proactive intent gate" is an 8-month-old
  idea now being formalized — not net-new.

---

## ⭐ The per-phase latency breakdown (Apr 7, 2026 — Lihang Pan's analysis, the precise numbers)
The summary/dynamic plan pipeline runs these phases. THIS is where the latency lives —
know it cold; it's the most useful artifact for any optimization conversation:

| Phase | Time | Notes |
|-------|------|-------|
| Context building (Seed Plan + Conv History + Knowledge fetch) | **4s** | sequential |
| Knowledge Summary prompt (AQWK) | **4s** | P75 |
| Topic Classification prompt | **3s** | |
| **Next Step prompt** | **15s** | ⭐ the single biggest cost — the latency-critical component |

End-to-end was **15–19s**; **Iteration 1 got it to 6–7s**. How:
- Removed the knowledge-summarization prompt (keep only chunks score > 0.6, cap chars) →
  **51% end-to-end reduction**.
- Prompt compression on topic-classification + next-step → **30% faster, 68.3% fewer tokens**
  (next-step 4.15s → 2.92s).
- **Parallel fetch** of context variables/states (was sequential).
- **Voice incomplete-request OTB topic**: classify "failure words"/incomplete utterances and
  STOP — avoids triggering the 15s next-step prompt.
- **Conversation-history compression**: keep 1 turn (MS, 2 under test), 4 turns (voice).

## ⭐⭐ The canonical pipeline diagram (Lihang Pan's Lucid chart — "after perf improvement")
The plan pipeline, phase by phase, split across **Core → AgentAPI V1Client → Off-Core Planner**,
with the 6 named Perf Improvements mapped to where they apply:

```
Start → [Conv History fetch 100ms + Seed Plan fetch 100ms + RAG Call 2.5s]  ← Perf Impr 1: PARALLEL context building
      → NamedConnection Setup 200ms → Pre-LLM Init Context 400ms
      → Topic Classifier 200ms      ← Perf Impr 3: EinsteinHyperClassifier
                                     ← Perf Impr 6: incomplete-request topic (voice) → if incomplete, END
      → Next Step / Initial Prompt 3.5s   ← Perf Impr 4&5: prompt + conv-history compression
                                          (baseline for this prompt w/o custom instruction = 1.5–2s)
      → "Pick up Action?" →
            • No → END
            • Action requires more inputs → END
            • Action requires confirmation → Confirmation Dialogue Prompt 700ms → END
            • Action doesn't require confirmation → Action preparation (schema/input) 150ms
              → Invoke core action execution (varies ms–several seconds)
```
- **Perf Impr 2 = AQWK removal** (the knowledge-summary prompt).
- **"+2.5s if restart session"** — re-doing context-var building, External OAuth token fetch,
  Agent API start session, Planner start session. Session restarts are a hidden latency tax.

**Before/after waterfall (excl. action execution, which always varies):**
| | Core (RAG) | V1Client | Off-Core planner phases | **Total** |
|---|---|---|---|---|
| **Baseline** | 2.5s | 200ms | 400ms + 200ms + **1.5s** | **4.8s** |
| **After "improvement" (regressed!)** | 2.5s | 200ms | 400ms + 200ms + **3.5s** | **6.8s** |

⚠️ **Honest read of this diagram:** the "after" next-step prompt shows **3.5s vs a 1.5–2s
baseline** — i.e. the team's *custom instruction* on the Next Step prompt ADDS ~1.5–2s. This is
the exact "sacrifice Next-Step prompt requirements for performance" tradeoff Chad + Lihang were
assigned (Apr 7). The biggest remaining lever is trimming that custom instruction. Action
execution (5–7s variable) is still on top of all these numbers and is excluded from the ≤5s target.

## Latency targets & governance (Apr 7, 2026 meeting)
- **Goal: ≤5s for plan summary** (GA targets floated 3 or 5s; beta had no hard requirement).
- "5s" defined as **a response WITHOUT taking actions** — action execution adds a **variable
  5–7s** on top and is excluded from the target.
- **Tiger Team** (Aaron Fiske) chartered: free to swap models + aggressive prompt techniques,
  1–2 week PoC to prove 5s is reachable.
- **Escalation rule:** if ~4 iterations can't hit 5s → **full architectural rethink**. (This is
  the "comprehensive architectural review" that the PISA/OpenSearch-bypass direction feeds.)
- Customer stakes: a slow product (esp. a "one-minute summary plan") discredits the team vs.
  **Google CCAI/CCAS**; named-sensitive customers (UBS, UPS-style).
- Cross-channel: voice optimizations must be **backward-compatible with MS + Case**. The
  optimizations also fix the legacy "plan must be created at case CREATION because it's too
  slow at case OPEN" problem.

## Model exploration for intent/topic classification (the SLM thread)
The hunt for a faster, cheaper intent/topic classifier has a long candidate list:
- **FlashTopic Model** (fine-tuned on **Qwen**, POC Shiva Raaj Kotni) — **DISABLED due to a
  security issue** (was being used in AF for topic classification).
- **Einstein Topic Classifier / EinsteinHyperClassifier** — current front-runner (lighter,
  smaller output tokens, faster). Bingbing's P95 test pending.
- **GPT-4o-mini / 4.1-nano, Gemini Light, a dedicated "Voice model"** — candidates for
  plan-generation/utterance-summarization (low cost + low latency).
- **Label Force** (John Emmons) — internal data-annotation platform for training SLMs.
- Note: SLMs via LLM Gateway/Prompt Builder were "not ready" (per Oded). SOX team picks up
  the Voice model work after DC1.

## SRA-for-Voice Beta scope & milestones (from the Beta Scope doc)
- **Acronyms:** SA=Service Assistant, SCV=Service Cloud Voice, TB=ThunderBird, VC=Voice Call.
- **Milestones:** M0 = TD for owner-change/status-change events (VC team) → M1 = onboard VC to
  existing pipeline via Record Companion (same Skill impl as MS) → M2 = framework-level perf
  enhancement (MS+VC) → M3 = integrate with TD, e2e → M4 = production readiness (logging/monitoring/Q3-Q4).
- **Beta = Service Plan Skill only**; supports single CSR, warm transfer, cold transfer.
  NOT in beta: conference call, multi-party/consult.
- **Stretch goal (W-21317924): event batch processing** — instead of invoking the dynamic plan
  on every end-user message, process the first and batch subsequent messages until it completes
  (Bingbing + NGS). This is a real latency/cost lever distinct from intent detection.
- Transfer context: SCV makes 2 VC records (1 per CSR) but **1 conversation**; CSR2's plan can
  reuse the conversation via conversationId + sessionStartTime (same as MS).

## The latency model (memorize this — it's the analytical backbone)

SRA latency comes from THREE distinct sources. Conflating them is the #1 mistake
in these discussions. Always map any proposal to which one(s) it actually touches.

| # | Source | Magnitude | Nature | Fixable by an external system? |
|---|--------|-----------|--------|-------------------------------|
| 1 | **Time-to-start (5-turn wait)** | 5 conversation turns | Architectural — SRA waits to accumulate enough signal to infer **intent** before generating a summary plan | ✅ Maybe — an out-of-band intent signal could trigger earlier |
| 2 | **Summary-plan generation** | up to **40s** | Heavy generation step, runs through the Agentforce planner | ❌ No — internal to Agentforce |
| 3 | **Agentforce round trip** | **7s P95** | Platform request/response infra latency | ❌ No — anything routed THROUGH Agentforce pays this |

**The cardinal rule:** Anything that funnels a request *through* the Agentforce
agent/planner pays the 7s P95 (and possibly the 40s gen). An external system can
ONLY help source #1 — and only by running *parallel to* Agentforce, not through it.

---

## PISA — what it is and the realistic scope

- **PISA = Proactive In-Meeting Support Agent**, an internal **Salesforce AI Research**
  prototype (AI Foundry / Incubator). Mac desktop app; ambient agent that surfaces
  real-time insights during live meetings/calls. Sub-second insight from utterance.
- **NOT** a planning/reasoning technique, not an LLM, not a Service Cloud feature.
  Internal pilot only (CKO FY27, ~Feb 2026; v2.5.x; AMER+UK; consent-gated).
- **PM: Daniel Lee** (AI Research). Sponsor: Itai Asseo.
- **The proposal (James Barker, June 2026):** bring PISA's <1s live-insight capability
  into Service Cloud for real-time channels, pitched as faster General FAQ vs. RAG.

### Honest assessment of the PISA→SRA fit (the key reframe)
- ❌ **FAQ-latency pitch is weak** — FAQ answers still route through Agentforce → still
  pay 7s P95. PISA being fast upstream doesn't remove the platform round trip.
- ❌ **Can't fix the 40s generation or the 7s round trip** — both are Agentforce-internal.
- ✅ **The real opening: source #1, the 5-turn intent wait.** PISA reads each utterance
  in real time → continuous/early **intent detection** *outside* the Agentforce round
  trip. Could let the plan trigger when confidence is reached (turn 2? turn 6?) instead
  of a hard-coded 5-turn gate. Aligns with the roadmapped "intent-based triggers replace
  the hard-coded 5-utterance trigger."
- ⚠️ **The make-or-break question:** fast ≠ accurate enough to TRIGGER. A wrong early
  trigger burns 40s generating the wrong plan — worse than waiting. So the bar is
  **intent accuracy + confidence vs. the current 5-turn approach**, not just speed.
- ⚠️ **Integration question (for eng, not AI Research):** does SRA's trigger expose a
  hook for an external system to say "start the plan now"? If it's hard-coded internally,
  there's no wire-in point for PISA's signal.

---

## Key people & channels

- **Daniel Lee** (U09DL2Q4664) — PISA PM, AI Research
- **James Barker** (U02D73W6QKB) — proposed PISA→Service Cloud
- **Neil Armstrong** (W012TTQDDF0) — SRA eng (CLT, rendering, trigger architecture)
- **Chad Goldsmith** (U01G1CJ1LUW) — SRA PM (you)
- Channels: `#ai-research-pisa-pilot` (C0ACDJ1MDJR), `#temp-sra-fde-pioneers`
  (C0AN1E181M3), `#service-assistant-adaptive-exp-acc` (C08SFQP1USF)
- PISA demo video: Slack file `F0B1HJJPUP9` (PISA_Demo.mp4, ~755MB — shows the <1s insight)

---

## Research workflow

1. **Scope the question** — which of the 3 latency sources is in play? If a proposal
   claims to "make SRA faster," immediately ask *which source* and whether it routes
   through Agentforce (if yes → it can't beat 7s P95).
2. **Pull the facts** — search Slack (latency numbers, P95s, trigger behavior),
   internal docs, and codesearch for the SRA trigger/planner. Use the `aisuite:researcher`
   subagent (via Agent tool) for broad multi-source sweeps.
3. **Verify the numbers** — don't take a quoted latency at face value. Confirm what
   each number measures (e.g. "PISA <1s" insight-from-utterance vs. "7s P95" full
   round trip are NOT apples-to-apples; demand comparable methodology).
4. **Map proposal → latency source** — use the table above. Be explicit about what it
   can't fix. This honesty is the value of the skill.
5. **Surface the make-or-break question** — for intent-trigger proposals it's accuracy;
   for retrieval proposals it's "what does it ground against and does it port."
6. **Report** — sourced findings + the clear-eyed "here's what it actually addresses"
   verdict. Flag gaps/unverified claims rather than papering over them.

## Known facts (verified with Chad + sources, June 2026)
- 5-turn wait before SRA starts (intent collection) — hardcoded; inefficient for voice.
- Summary-plan generation: was **17s**, improved to **5-7s** (Khoa Le, Apr); worst-case tail ~40s.
- Agentforce round-trip **P95 = 7s** ("recurring 7-second latency loop" on Agentforce/Data
  Cloud retrieval — confirmed in PISA call, 00:05:55).
- Per-utterance ops: ~**8.9s P50**, 12.2s avg (Atul Wankhade transfer investigation).
- **Google CCAI experiments → 5-6s latency too** — alternatives don't escape it; the
  *architecture* (not the vendor) is the bottleneck (PISA call, 00:08:18).
- **Transcription (Deepgram) latency is OUTSIDE SRA's control** — SRA only owns
  post-transcript generation (Bingbing, Apr 6). PISA can't fix transcription either.
- Intent-based triggers (replacing hard-coded 5-utterance) are a roadmap direction.

## Eng roadmap already in flight (CCAI / art-provider, Dylan Gnatz spike, June 2026)
3-phase plan — maps directly to the latency model:
1. **LLM confidence scoring / Hyperclassifier** (~6-9 pts, target 262.12) — in-platform
   intent-confidence to act earlier instead of the 5-turn gate. PRs: art-provider #1058/#1062/#1074.
2. **Skip Summary Plan for Voice** (~6-9 pts, fast follow) — **hard date July 31 for UPS**.
   Skips the slow summary-plan generation on voice.
3. **Full V2 refactor** (30-45 pts) — ships with auto-running the Dynamic Plan for Messaging.

## PISA In Service Cloud — call outcome (June 18, 2026)
Attendees: Daniel Lee (PISA PM), James Barker, Aaron Fiske, Bingbing Wu, Neil Armstrong,
Wenqing Dai, Chad, Sridhar Raghavan. The discussion moved OFF "drop PISA in" and onto TWO
separable architectural bets to attack latency *upstream of Agentforce*:

1. **Intent detection → Einstein Topic Classifier (NOT PISA).** Lighter-weight, faster due
   to smaller output tokens (Bingbing). Targets the 5-turn wait. Formal P95 test pending
   (Bingbing's action item). PISA is NOT the intent mechanism here.
2. **Retrieval → bypass Agentforce/Data Cloud with direct calls** (e.g. **AWS OpenSearch**
   retriever API directly). This is where PISA actually contributes — Daniel offered PISA's
   team to **abstract the data source** to bypass the rigid Agentforce dependency. Chad agreed
   the hooks are the beneficial approach.

**Honest scorecard:**
- PISA's role NARROWED from "intent + insight" to **retrieval abstraction** (intent went to
  the Einstein classifier).
- PISA still can't fix: the 7s Agentforce round trip itself, transcription (Deepgram), or
  Data Cloud — those get fixed by *bypassing* them, which is the architecture bet.
- AI Research positions as **technology validator, not product owner** — "last mile" incubation.
- PISA addresses intent at 2 levels: turn-by-turn questions + long-horizon multi-turn context.

**Aligned decision:** investigate + benchmark integrating PISA knowledge retrieval AND Einstein
topic classification into the SRA pipeline to address latency.
**Action items:** Daniel (benchmark PISA vs current retrieval; schedule next-Fri deep-dive),
Bingbing (P95 test the Einstein Topic Classifier).

> Treat Chad-stated figures as ground truth; cite him. Cite the call notes
> (PISA In Service Cloud, 2026-06-18) and the named Slack threads for the rest.

## Output style
- Lead with the bottom line (what the proposal can/can't do).
- Always map to the 3-source latency model.
- Separate verified facts from claims-needing-verification.
- Name the single make-or-break question.
- Honest over optimistic — Chad values "fast-but-wrong doesn't help" realism.
