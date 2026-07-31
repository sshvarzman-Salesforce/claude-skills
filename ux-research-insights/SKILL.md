---
name: ux-research-insights
description: >
  Access and synthesize UX Research & Insights findings for Service Cloud product decisions.
  Searches R&I studies, PAC readouts, voice-of-customer data, and the Service Cloud Insights Digest.
  Grounded in validated findings from PAC sessions, discovery research, and usability studies.
  Use when you need customer evidence to support a PRD, design decision, roadmap pitch, or meeting prep.
tools: [mcp__plugin_google_google__docs_search, mcp__plugin_google_google__docs_get, mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_search_search__search, Read, Write, Edit, Agent]
---

# UX Research & Insights — Service Cloud

> Pull validated customer evidence from UX Research & Insights studies to support product decisions, PRDs, roadmap pitches, and meeting prep.

**Invocation:** `/ux-research-insights [your question or topic]`

---

## What This Skill Does

You ask a question about what customers think, need, or struggle with. The skill:

1. **Searches R&I studies** — Google Docs, the Insights Digest, PAC readouts, discovery research
2. **Checks the grounded knowledge base** — pre-indexed findings from validated studies (see below)
3. **Finds supporting evidence** — direct quotes, participant counts, validated patterns
4. **Writes a research brief** — saves to `.agents/artifacts/ri-<topic>.md` for reuse
5. **Returns actionable findings** — concise, citable, ready for a PRD or deck

---

## Example Questions

- "What do customers think about SRA latency?"
- "What evidence supports the human-in-the-loop pattern?"
- "What are the top knowledge retrieval pain points for service reps?"
- "What did PAC customers say about resolution-based pricing?"
- "What research backs the 'actions from a single pane of glass' direction?"
- "What do reps think about real-time coaching during calls?"
- "What's the customer evidence for intelligent queue management?"
- "What research exists on tenure-based UI adaptivity?"
- "What did DPD say about dynamic plans?"
- "What's the evidence that Tier 1 work is going away?"

---

## Research Sources (Priority Order)

### Source 1: Grounded Knowledge Base (Local — Check First)

Pre-indexed findings from validated studies. Always check here before searching externally.

```
~/.aisuite/notebook/2026-07-08/ux-research-sra-synthesis.md
```

This contains synthesized findings from:
- Service Cloud PAC (May 2026, 13 customer executives)
- Voice Guidance & Coaching Discovery (Apr 2026, 11 interviews)
- SRA MAC Overwatch Research (2025, PAC + research sessions)
- My Agent Console Review with DPD (Dec 2025)
- Service Cloud Insights Digest (July 2024, curated reference)

### Source 2: Google Docs (R&I Reports)

```
Search patterns:
- "Service Cloud" + [topic] + "research"
- "PAC" + "Service Cloud" + [topic]
- "discovery research" + "service" + [topic]
- Researcher names: Nicholas Feinig, Deepshikha Singh, Max Wenger, Jenny Williams
```

Key documents by ID:
| Study | Google Drive ID |
|-------|-----------------|
| Service Cloud PAC Key Takeaways (May 2026) | `1nS4adAnSzgYu7nrWJsXz3IEZrQl-gjIn6ohRjBDWB9k` |
| Voice Guidance & Coaching Discovery (Apr 2026) | `1NFDborYBusCoipegZGiqoccbtRwORyMbyfIa0m1rUnM` |
| My Agent Console Review — DPD (Dec 2025) | `1l1EL9YF9QX6qo6sULLvoBwrrIzsfbBzk3IAzr_UKEKQ` |
| Service Cloud Insights Digest | `12qbNnaqJlqKRXXwU80Bt7yjItzltRZ267JPMyVEjPUY` |
| Service Cloud PAC: My Agent Console (Nov 2025) | `1wTdwDJO8E3uEMCzSR8uWUXXYyDoJdi3YiVPQTX8IS7A` |
| My Agent Console follow up (Sep 2025) | `1nGGgS6o1x_wVXrdJpLGTEgvmthb1xGAwP5ayf15lgBQ` |
| Service Cloud PAC FY26Q4 | `1A-1t6HRE-8WV1sps1E-zaPndDt81BzMCDBLT6O8cYVE` |
| Voice of the Field FY25: Service Cloud Cut | `1N6JpW6vXlZONrO1xHHJAGix3Mrt9VD4jQNYhLwomys4` |
| Chad / Deepshikha: Service Reps JTBD Research | `1SQsdKJlqD7wFkKVx83FQJ4jaVfInYXehyMg3vk2EPLs` |
| Service Reps JTBD: Validated Findings (PPTX) | `12lFP8t33nr6zX4JGnXoU5VoekinjQuL5` |

Local PDF (requires Python extraction):
| Study | Path |
|-------|------|
| SRA MAC Overwatch Research (51 slides) | `~/Downloads/Service Rep Assistant MAC Research.pdf` |

### Source 3: Slack (R&I Channel)

```
Channel: #ri-insights-service (C01U4EZS0U8)
```

Good for: Real-time insights, research roadmap updates, office hours notes, quick customer quotes.

### Source 4: R&I Experience Cloud Site (Limited Access)

```
URL: https://uxresearch.my.site.com/ResearchInsights/s/
```

Note: Requires SSO authentication. Cannot be accessed programmatically. Use for manual browsing only. Studies hosted here that aren't in Google Drive:
- Knowledge Challenges: Literature Review (Deepshikha Singh, Nov 2025)
- State of Service Product Survey: Channels Cut (Max Wenger & Nicholas Feinig, Mar 2026)

### Source 5: Service Cloud Insights Digest Links

The Digest (Source 2 above) contains links to dozens of additional studies organized by topic:
- Generative AI (Service Planner vision, ESA pilot, email summaries, copilot for supervisors)
- Intelligence Products (Service Intelligence, Customer Intelligence/VOC)
- Adoption (consultation, entitlements, NPS analysis, MAO metric bias)
- Market Opportunities (QA TAM, User TAM automation exposure, Data Cloud + SC)

---

## Grounded Knowledge Base — Key Findings Index

### Theme: SRA / Service Rep Assistant

| Finding | Source | Evidence Strength |
|---------|--------|-------------------|
| SRA praised for upfront context surfacing | PAC May 2026 (GeneDx) | Strong — direct customer quote |
| Human-in-the-loop gates = right balance | PAC May 2026 (ISN) | Strong — explicit praise |
| Latency is a dealbreaker — reps will abandon slow tools | PAC May 2026 (ISN) | Strong — direct warning |
| Multi-system parallel research bot desired | PAC May 2026 (Toyota) | Strong — specific request |
| SRA as NBA replacement = multi-year goal | PAC May 2026 (ESRI) | Moderate — aspirational |
| Setup documentation critical for adoption | PAC May 2026 (ESRI) | Moderate — barrier identified |
| Too much automation power = dangerous for frontline | PAC May 2026 (Rithum) | Moderate — concern, not blocker |

### Theme: Knowledge & Information Retrieval

| Finding | Source | Evidence Strength |
|---------|--------|-------------------|
| Guidance is scattered across 5+ systems | Voice Research Apr 2026 (11 interviews) | Strong — universal across participants |
| Manual search takes 5-7 min, causes holds | Voice Research Apr 2026 | Strong — observed pattern |
| Wrong triage at start = wrong path for entire call | Voice Research Apr 2026 | Strong — failure mode |
| Three modes: verbatim scripts, guided workflows, talking points | Voice Research Apr 2026 | Strong — validated taxonomy |
| Cognitive overload from multitasking (listen + navigate + read + empathize) | Voice Research Apr 2026 | Strong — universal |
| Dead air from manual search hurts QA scores | Voice Research Apr 2026 | Strong — measured impact |
| Bullet points over paragraphs — always | Voice Research Apr 2026 | Strong — unanimous preference |

### Theme: Console & Workspace (My Agent Console / MAC)

| Finding | Source | Evidence Strength |
|---------|--------|-------------------|
| Right functionality, wrong experience arrangement | MAC Research (UX + R&I) | Strong — key takeaway |
| MAC must deliver value before mass SRA automation | MAC Research | Strong — strategic finding |
| Customers want intelligent work prioritization (no "hunting") | MAC Research (PAC + interviews) | Strong — multiple sources |
| Actions from single pane of glass — don't divide attention | MAC Research | Strong — clear demand |
| Customization: fields, thresholds, rules must be configurable | MAC Research | Strong — minimum requirement |
| Pivot from process-oriented → content-rich design | MAC Research | Strong — design direction shift |
| Racetrack > Kanban (but needs evolution) | MAC Research | Moderate — directional |
| "Don't ship our org chart" — outcome over architecture | MAC Research | Strong — messaging guidance |
| MAC naming is problematic (signals new SKU) | MAC Research | Moderate — naming concern |
| Overwatch = CSR unblocks ASAs from behind the scenes | MAC Research | Strong — validated concept |
| Persona confusion: supervisor vs rep still unclear | MAC Research | Moderate — emerging |
| Some businesses don't want reps making queue decisions | MAC Research | Moderate — segment-specific |

### Theme: Voice Channel & Coaching

| Finding | Source | Evidence Strength |
|---------|--------|-------------------|
| Real-time guidance = "breath of fresh air" for new agents | Voice Research Apr 2026 | Strong — direct quote |
| Veterans find live coaching "annoying" — must be toggle-able | Voice Research Apr 2026 | Strong — tenure split |
| Sentiment detection must be actionable (specific tactics, not just "angry") | Voice Research Apr 2026 | Strong — design requirement |
| Coaching should focus on one topic at a time | Voice Research Apr 2026 | Strong — avoid robotic behavior |
| Gamification (streaks) motivating but risk of mechanical behavior | Voice Research Apr 2026 | Moderate — cautious positive |
| Coaching belongs at login/pre-shift, NOT during live call | Voice Research Apr 2026 | Strong — placement consensus |
| Many orgs lack transcripts — forced to listen to recordings for QA | Voice Research Apr 2026 | Strong — infrastructure gap |
| Positive reinforcement desperately needed ("kudos") | Voice Research Apr 2026 | Strong — emotional need |

### Theme: Pricing & Business Model

| Finding | Source | Evidence Strength |
|---------|--------|-------------------|
| Resolution-based pricing strongly preferred over flex credits | PAC May 2026 (CVS, Toyota, Outcomes) | Strong — enthusiastic |
| $2 AI resolution vs $20 human = instant business case | PAC May 2026 (Toyota) | Strong — direct quote |
| Risk shift to Salesforce (no charge on escalation) = competitive advantage | PAC May 2026 (multiple) | Strong — differentiator |
| "Resolution" definition unclear (FAQ = resolution?) | PAC May 2026 (Outcomes) | Moderate — open question |
| BYO LLM customers fear double-charging | PAC May 2026 (Toyota, CVS) | Moderate — concern |
| OOTB setup time claims met with skepticism | PAC May 2026 (CVS) | Moderate — trust gap |
| Data Cloud prerequisite perceived as blocker | PAC May 2026 (Rithum) | Moderate — adoption barrier |
| Pricing complexity slowing adoption across all AI products | MAC Research | Strong — strategic risk |
| Three pain points: slow to activate, slow to deploy, slow to scale | MAC Research | Strong — validated pattern |

### Theme: Contact Center & WFM

| Finding | Source | Evidence Strength |
|---------|--------|-------------------|
| Voice becoming blended feature of digital (click-to-talk in apps) | PAC May 2026 (CVS) | Strong — northstar stated |
| Pure-play CCaaS value questioned (3-5 year horizon) | PAC May 2026 (ISN) | Strong — strategic question |
| Coexistence strategy needed (phased, not rip-and-replace) | PAC May 2026 (multiple) | Strong — universal |
| WFM needs more integrations (ADP, Outlook, Field Service) | PAC May 2026 | Strong — specific asks |
| Reps handle multiple digital channels simultaneously (blended) | PAC May 2026 (Rithum, Toyota) | Strong — operational reality |
| Supervisor mobile-first = wrong bet (desk-bound always) | PAC May 2026 | Strong — unanimous |
| Agentic supervisor = "PagerDuty for contact center" | PAC May 2026 | Strong — concept resonated |

### Theme: Headless & Integrations

| Finding | Source | Evidence Strength |
|---------|--------|-------------------|
| Embedding AI into third-party systems = strategic imperative | PAC May 2026 | Strong — multiple customers |
| Trust Layer / sharing rules must follow the data | PAC May 2026 (ESRI) | Strong — non-negotiable |
| Dealer network needs customer history without SF login (Toyota) | PAC May 2026 | Strong — specific use case |
| EPIC portal embedding for healthcare (GeneDx) | PAC May 2026 | Strong — specific use case |
| Third-party bots calling INTO insurance lines, skewing metrics | PAC May 2026 (CVS, BCBNC) | Strong — emerging problem |

### Theme: Future of Service

| Finding | Source | Evidence Strength |
|---------|--------|-------------------|
| Reps transitioning from support → proactive account health | PAC May 2026 (ESRI) | Strong — active strategy |
| Service → marketing/lead gen pipeline | PAC May 2026 (Andersen) | Strong — active strategy |
| Revenue per contact replacing cost per contact | PAC May 2026 (Saks) | Strong — metric shift |
| Tier 1 going away as automation handles routine | PAC May 2026 (Saks, consensus) | Strong — widely agreed |
| Upsell must pair with sentiment logic (don't upsell angry customers) | PAC May 2026 (Outcomes, BCBNC) | Strong — cautionary |

---

## Research Pipeline

### Phase 1: Check Grounded Knowledge

Always start by reading the synthesis file:
```
~/.aisuite/notebook/2026-07-08/ux-research-sra-synthesis.md
```

If the answer is there with strong evidence, return it immediately. Don't over-research.

### Phase 2: Search for Additional Studies

If the grounded knowledge doesn't fully answer the question:

1. **Google Docs search** — use researcher names + topic keywords
2. **Insights Digest links** — check the topic sections for relevant linked studies
3. **Slack #ri-insights-service** — recent threads, especially researcher posts
4. **Web search** — Salesforce Research "State of" reports for market data

### Phase 3: Read and Extract

When reading a new R&I study:
- Note the **methodology** (N=?, who were participants, date)
- Extract **direct quotes** (these are gold for PRDs and decks)
- Identify **validated patterns** vs. **single-participant opinions**
- Flag **evidence strength** (Strong = multiple sources/large N, Moderate = single source/small N, Weak = inference)

### Phase 4: Write Research Brief

Save to: `.agents/artifacts/ri-<topic-slug>.md`

Format:
```markdown
# R&I Brief: [Topic]
**Date:** [today]
**Query:** [original question]

## Summary
[2-3 sentence answer with evidence strength]

## Key Evidence

### [Finding 1]
- **Source:** [study name, date, researcher]
- **Methodology:** [N=, participant type]
- **Quote:** "[direct customer quote if available]"
- **Strength:** Strong / Moderate / Weak

### [Finding 2]
...

## Implications for [PRD/Design/Roadmap]
[How to use these findings]

## Gaps / Further Research Needed
[What we don't know yet]
```

### Phase 5: Return Actionable Answer

Respond with:
- The finding (1-2 sentences)
- Evidence strength and source
- A usable quote if one exists
- Pointer to the full brief

---

## Service Cloud Personas (from Insights Digest)

Use these when scoping which persona a finding applies to:

| Persona | Core JTBD | How They Use SF |
|---------|-----------|-----------------|
| **Service Agent** | Handle customer issues, document resolutions, meet KPIs | Communication platform, customer/case data, click reduction |
| **Service Supervisor** | Distribute work, monitor activity, intervene real-time, handle escalations | Omni Supervisor, reports, escalated cases |
| **Service Operations** | Training, workflow optimization, scheduling, hiring | Reporting/analytics, Knowledge authoring |
| **Service Leader** | Strategy, resource advocacy, performance accountability | Reporting/analytics, business case data |

---

## R&I Team & Channels

| Resource | Link |
|----------|------|
| Slack channel | #ri-insights-service (`C01U4EZS0U8`) |
| Channel canvas | How to request research, office hours, roadmap |
| Research Library | `https://sforce.co/49NDSjP` (thousands of reports) |
| R&I Experience Cloud site | `https://uxresearch.my.site.com/ResearchInsights/s/` (requires SSO) |
| In-app Feedback org | `https://research-iaf.lightning.force.com/` |

Key researchers for Service Cloud:
- **Nicholas Feinig** — Principal Researcher (SRA, MAC, Voice Guidance, Coaching)
- **Deepshikha Singh** — Knowledge, Service Reps JTBD
- **Max Wenger** — State of Service surveys, channels
- **Jenny Williams** — PAC coordination

---

## Rules

- **Always cite the source study, date, and methodology** — never present a finding without attribution.
- **Distinguish evidence strength** — "13 PAC executives agreed" ≠ "one participant mentioned."
- **Use direct quotes when available** — they're more compelling than paraphrases in PRDs and decks.
- **Date matters** — R&I findings from 2023 may not reflect 2026 customer sentiment. Note the date.
- **Don't conflate personas** — what a supervisor wants ≠ what a rep wants ≠ what a leader wants.
- **Don't over-index on PAC** — PAC participants are large enterprises (ESRI, CVS, Toyota, Saks). SMB needs may differ.
- **Check for contradictions** — if two studies disagree, surface both with context on methodology differences.
- **"Validated" means multiple sources or large N** — a single participant's opinion is a signal, not a finding.
- **Update the grounded knowledge base** — when you read a new study, add key findings to the synthesis file.
