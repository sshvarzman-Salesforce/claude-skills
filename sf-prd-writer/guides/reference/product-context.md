# Product Context Reference

This section provides essential Service Rep Assistant domain knowledge that every PRD should reflect. Use this as background context when writing any section — especially scope, architecture, non-functional requirements, and dependencies.

## Product Positioning

Service Rep Assistant (SRA) is an **ambient AI Agent in the flow of work for every service rep**. It delivers real-time, turn-by-turn guidance during customer interactions across Case, Message, and Voice channels.

**CRITICAL:** SRA is **ALWAYS rep-facing, NEVER customer-facing**. All three channels (Case, Messaging, Voice) are contexts where a human service rep is using SRA as an assistant in the console sidebar. SRA does not autonomously respond to customers — it helps the human rep respond better, faster, and with better context.

## Editions & Licensing

All SRA features require specific editions and add-ons. Every PRD should reflect these in the Non-Functional Requirements section:

| Requirement | Details |
|---|---|
| **Add-On (required)** | Einstein for Service (E4S) Add-On OR Agentforce for Service (A4S) Add-On |
| **Base Edition (required)** | Service Cloud Einstein 1 Editions (E1E) OR Agentforce 1 Editions (A1E) |
| **Foundational Requirement** | Requires Foundations SKU |
| **Metering** | E4S consumes Einstein Requests; A4S covered by un-metering strategy (unbilled) |

## Prerequisites

Every SRA feature has these baseline prerequisites:
- Einstein Generative AI enabled
- Data Cloud provisioned
- Agentforce Builder access
- Service AI Grounding enabled
- Check Service Planner Eligibility Flow configured (standard flow template that gates plan generation)

## Building Blocks Vocabulary

Use these terms precisely when writing PRDs:

| Building Block | Definition |
|---|---|
| **Topics** | Configurable by admins. Each topic has a Classification Description (when to match) and Scope (what it covers). Topics are what the system matches against to select the right plan. |
| **Instructions** | Employee-facing descriptions that describe the steps for a Service Plan. These tell the AI what the plan should contain. |
| **Actions** | Agentforce Actions attached to topics. These are the executable capabilities within a plan (e.g., look up order, initiate refund). |
| **Eligibility Flow** | The "Check Service Planner Eligibility" flow template — a standard flow that gates whether plan generation should fire for a given record. |
| **Skills** | The AI capabilities within SRA: Conversation Catch Up, Service Replies, Article Recommendations, Dynamic Plans. |

## Guidance Plans vs. Dynamic Plans

These are two distinct plan types. PRDs must clearly specify which one they apply to.

| Dimension | Guidance Plans | Dynamic Plans |
|---|---|---|
| **Nature** | Checklist-style, structured | Adaptive, real-time, turn-by-turn |
| **Channels** | Case only | Case, Message, Voice |
| **Capabilities** | Single capability per plan | Multiple capabilities per plan |
| **Action Execution** | Quick Actions | Agentforce Actions |
| **Behavior** | Static once generated | Supports dynamic topic switching |
| **GA Timeline** | Winter '25 (258) | Summer '26 (262) target |

## Plan Output Structure

Dynamic Plans use a fixed 4-header structure. These are the **only** headers allowed — no additional headers can be introduced. If a header is not applicable, it is simply omitted.

1. **Gather Information** — Steps to collect context from the customer
2. **Work The Issue** — Diagnostic and troubleshooting steps
3. **Resolve The Issue** — Resolution actions (refunds, changes, escalations)
4. **Wrap Up** — Confirmation, follow-up, case closure

Each step contains: step name, Details text, developer name(s), step number, and an `is_suggested` flag.

**Step Types (identified by dev name and action_type):**
- **Standard Actions** (`action_type: "standard"`) — Manual steps for the service agent to perform. Include input/output parameters to guide the agent through execution.
- **Tool Actions** (`action_type: "tool"`) — Automated, system-executable Agentforce Actions. Shown with Confirm/Cancel buttons in the UI.
- **rag_step** — Steps sourced from Knowledge Base articles. Not from the provided actions/policies list. `is_suggested: false`.
- **suggested_step** — Dynamically created steps based on conversation context, not from actions/policies or Knowledge Base. `is_suggested: true`.

**Resolution statuses:**
- `Plan Generated` — plan was created with steps
- `Insufficient Data` — issue details alone don't provide enough context (assessed WITHOUT referencing topics, actions, or policies)
- `Issue Already Resolved` — no further action needed

## Plan Generation Pipeline

The plan generation flow follows this sequence:

**Detect** → **Plan** → **Outcome**

1. **Detect:** New case, email, message, or voice utterance triggers the pipeline. The Check Service Planner Eligibility Flow gates whether plan generation should fire.
2. **Plan:** System grounds the plan using the 5 data sections (Issue Details, Topic, Actions, Policies, Knowledge Base) — all processed through the Einstein Trust Layer. The model uses a **deliberation pattern**: three simulated experts independently analyze the problem, propose plans, review each other's proposals, refine based on feedback, then vote on the best plan. This pattern produces the highest quality output.
3. **Outcome:** Structured JSON plan output with 4-header structure delivered as turn-by-turn guidance in the SRA panel.

## Product Roadmap (Reference)

| Release | Milestone | Key Capabilities |
|---|---|---|
| Winter '25 (258) | Guidance Plans GA | Case-only, checklist-style plans |
| Spring '26 (260) | Dynamic Plans Beta | Case + Messaging channels, adaptive plans |
| Summer '26 (262) | Dynamic Plans GA Target | Case + Messaging + Voice, Service Replies, Case Insights, Knowledge Recommendations, Engagement Sentiment, Conversation Catch Up |

## Prompt Architecture

The plan generation prompt follows a three-tier privilege model:
1. **Privileged instructions** (top level, highest privilege)
2. **Program section** (enclosed in `<PROGRAM_TAG>` tags) — contains plan generation logic
3. **Data section** (enclosed in `<DATA_TAG>` tags, lowest privilege) — contains the 5 grounding data sections

The **Data section** (what gets grounded) has 5 parts in this order:
1. **Issue Details** — transcript, case description, conversation context
2. **Topic** — the matched topic with classification description and scope
3. **Actions for Service Plan** — available Agentforce Actions (standard + tool types)
4. **Policies for Service Plan** — business rules and procedures
5. **Knowledge Base Information** — ranked by relevance (first items most relevant, last may not be)

**Why this matters for PRDs:** Any feature that adds data to the prompt (like related record grounding) is adding to the Data section and competing for token budget with these 5 existing sections. PRDs should acknowledge this and specify that field-level selection (not full objects) is essential.

## Plan Output JSON Schema

The actual JSON output from plan generation has this structure:

```json
{
  "high-level summary": ["Human-readable summary of step 1", "..."],
  "plan": [
    {
      "header": "Gather Information | Work The Issue | Resolve The Issue | Wrap Up",
      "header sequence": 1,
      "steps": [
        {
          "step name": "Descriptive name of the action/policy/step",
          "Details": "What agent needs to do, specific info to use, context for execution",
          "dev name": ["Action_XXX | Policy_XXX | Tool_XXX | rag_step | suggested_step"],
          "step number": 1,
          "is_suggested": false
        }
      ]
    }
  ],
  "resolutionStatus": "Plan Generated | Insufficient Data | Issue Already Resolved",
  "prompt_injection_detection": {
    "prompt_injection_detected": false,
    "reasoning": "Explanation"
  }
}
```

**Dev name conventions:**
- `Action_XXX` / `Policy_XXX` / `Tool_XXX` — step is based on a provided action or policy
- `rag_step` — step sourced from Knowledge Base (is_suggested: false)
- `suggested_step` — dynamically created step not from actions/policies/KB (is_suggested: true)

## Prompt Optimization Context

The plan generation prompt has been through rigorous optimization. Reference these when discussing performance, token budgets, or generation latency:

**Optimization Results (by Alexandre Galas):**

| Version | Tokens | AI Gateway | Quality | N/A Failures | Key Tradeoff |
|---|---|---|---|---|---|
| Baseline (original) | 9,289 | 25s | Baseline | 17/124 | Full deliberation, verbose |
| Optimized + deliberation (winner) | 1,895 | 11s | Highest | 9/124 | 80% token reduction, best quality |
| No expert pattern + fixes | 1,521 | 13s | Good | 10-17/124 | Best speed/quality tradeoff without deliberation |
| Under 100 words, no deliberation | 1,110-1,121 | Fast | Low | 18-20/124 | Too aggressive — quality drops |

**Key findings:**
- **Deliberation pattern is essential for quality.** The "three experts deliberate → propose → review → re-propose → vote" pattern produces the highest quality plans. Removing it saves tokens but degrades output significantly.
- **Token reduction:** 80% system prompt reduction (9,289 → 1,895) while *improving* quality
- **AI Gateway duration:** 55% faster (25s → 11s)
- **Quality metrics improved:** Topic accuracy +2.4pp, consistency +1.97pp, generation failures reduced from 17 to 9 out of 124 tests
- **Testing framework:** SOBA Testing Framework with 124 NGS test cases, 248 iterations per version. Measures: consistency, topic accuracy, dev name accuracy, latency, generation failure rate.
- **Prompt optimizer:** Uses `claude-4.6-opus-high` to forge optimized prompts
- **Plan generation model:** `sfdc_ai__DefaultOpenAIGPT4o`
- **Prompt template location:** `@core/einstein-gpt-impl/java/resources/einstein-gpt-ai/promptTemplateType/einstein_gpt/servicePlansGuidanceUnifiedType.yaml`

**Implication for PRDs:** Token budget is a real engineering constraint. When features add grounding data (related records, knowledge articles, etc.), the PRD should:
1. Acknowledge token budget impact on the Data section
2. Recommend field-level selection over full-object inclusion
3. Note that any added context competes with Issue Details, Topics, Actions, Policies, and Knowledge Base for token space
4. Flag that excessive grounding data can increase generation failures (N/A rate) or degrade quality metrics

## Beta Program Context

When writing PRDs for 262 features, reference the current beta program:
- **Beta Requirements:** Lightning Experience, English only, Email-to-Case, Service Cloud Voice, Omni-Channel Routing, Enhanced Messaging (MIAW)
- **Beta Customers:** Must be existing Einstein 1 / E4S / Agentforce 1 / A4S customers
- **Key Beta Participants:** Meta, EA (frequently cited for feedback and evidence)

---

## Agentic PDLC (APDLC)

SRA uses the **Agentic Product Delivery Lifecycle (APDLC)** — a 4-phase delivery model that replaced Advanced Planning in Service Cloud, rolled out org-wide starting June 2026. Understanding the phase model determines which artifact to produce and what level of detail to include.

**What APDLC replaces:**
- ❌ Out: 16-week planning cycles, theme decks, product briefs
- ✅ In: working prototypes, PBDs, Slack-first collaboration, open docs
- 🔒 Unchanged: V2MOM, portfolio structure, GUS as source of truth

| Phase | Name | What happens | Primary artifact |
|---|---|---|---|
| **Phase 0** | Backlog & Research | Ideation, signal gathering, problem definition. Minimal documentation — the goal is to understand the problem, not specify a solution. | **Requirements One-Pager** |
| **Phase 1** | Discovery & Prototyping | Build a working prototype to validate assumptions and derisk the solution. Ends with a prototype demo/review (leadership review) that gates entry to Phase 2. | **PBD (Product Business Document)** + working prototype |
| **Phase 2** | Consolidation & Productization | Post-prototype execution. Formerly called "Execution." Ends at release freeze. Scrum team implements based on the validated design. | **Full PRD** |
| **Phase 3** | GTM Readiness | Go-to-market: enablement, launch prep, docs, pricing, release notes. | GTM artifacts (not managed by this skill) |

**Key implications for PRDs:**
- **One-pagers** are Phase 0 artifacts. They exist to mature a concept in the backlog and support Phase 1 prototyping decisions. Phase 0 → Phase 1 is the primary use case for this skill's one-pager format.
- **PBDs** are Phase 1 artifacts — they replace theme decks and product briefs. Program/initiative-level documents (one per initiative, not per feature). Google Doc format only (table-heavy layout doesn't work in Markdown). Must be delivered 2 business days before the Phase 2 Inspection gate. AI-generatable from existing research and customer data. The 11-section structure: (1) Executive Summary, (2) Value Proposition, (3) Target Persona & Customer Benefit, (4) Market & Competitive Differentiation, (5) Adoption Criteria & Success Metrics, (6) Go-To-Market & Marketing Alignment, (7) Program DOD, (8) Proposed Team Allocation, (9) Risks, Dependencies & Assumptions, (10) Prioritized Feature List, (11) Program Artifacts. See `guides/drafting/pbd.md` for authoring guidance (in progress).
- **Full PRDs** are Phase 2 artifacts. Written after Phase 1 prototype approval. Scrum-team-ready specification with Part 1 (UX/Architect) and Part 2 (scrum team).
- Features do not always go through every phase. Straightforward or well-understood features may skip Phase 1 prototyping and go directly to Phase 2 with a one-pager as the sole pre-execution artifact.
- **GUS remains the source of truth** — all work items, epics, and stories continue to live in GUS. APDLC changes the planning artifacts, not the execution tracking system.
