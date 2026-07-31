# Full PRD Draft

> **APDLC Context:** A full PRD is a **Phase 2** artifact in the Agentic Product Delivery Lifecycle (APDLC). It is written after a **Phase 1** prototype has been approved and validated at leadership review. The full PRD hands off the confirmed design to the scrum team for bottoms-up planning and execution. If a Phase 1 prototype does not exist yet, start with a [Requirements One-Pager](one-pager.md) instead — that is the Phase 0 artifact. Features that are straightforward enough to skip Phase 1 prototyping may go directly to a full PRD, but this should be an explicit decision, not a default.

Draft the full PRD following the standard two-part structure. Use a tone that is precise, evidence-backed, and focused on business problems and customer outcomes.

**Critical**: Avoid over-solutioning. Focus on:
- **What** customers need to accomplish
- **Why** it matters (business value, customer impact)
- **What** problems exist today
- **What** outcomes we're trying to achieve

Let engineering determine **how** to implement. When technical details appear in the examples, they describe "what needs to happen" not "how to build it."

**ANTI-SOLUTIONING GUIDELINES:**
- ❌ DON'T prescribe technical architecture, API designs, database schemas, or implementation patterns
- ❌ DON'T specify which services, classes, or components should be created
- ❌ DON'T dictate the technical "how" (e.g., "use a REST API endpoint", "create a new Apex class")
- ✅ DO describe business capabilities and user-facing behaviors
- ✅ DO specify constraints, limits, and business rules that affect the solution
- ✅ DO describe success criteria from a customer/business perspective
- ✅ DO cite existing patterns or technologies only as reference points, not mandates

**Example of over-solutioning (BAD):**
> "Create a new REST API endpoint at /api/v1/plans that accepts POST requests with a JSON payload containing case_id and plan_type. The endpoint should call PlanGenerationService.generatePlan() and return a 201 status code with the plan ID."

**Example of outcome-focused requirement (GOOD):**
> "Customer service reps need the ability to manually trigger action plan generation for a case when the automated triggers don't fire or when they want to regenerate a plan with updated context. The system should provide immediate confirmation that generation has started and notify the rep when the plan is ready to review."

## Frontmatter

Every PRD file starts with a YAML frontmatter block — before any metadata links, before the Administrative table:

```markdown
---
stage: draft
release: 264
feature: step-level-feedback
team: service-rep-assistant
personas: [service-rep, supervisor]
epic: null
hld: null
---
```

**Required fields:**
- `stage` — `draft` | `in-review` | `released-to-eng` | `shipped`. Update as the PRD advances.
- `release` — the release number (e.g., `264`)
- `feature` — kebab-case feature slug matching the filename (e.g., `step-level-feedback`)
- `team` — product team that owns this feature (e.g., `service-rep-assistant`)
- `personas` — YAML list of primary personas this feature serves (use kebab-case: `service-rep`, `supervisor`, `admin`)

**Optional fields (add when known):**
- `epic` — GUS epic W-number (e.g., `W-12345678`). Set to `null` until created.
- `hld` — link to HLD/architecture doc when one exists. Set to `null` if none yet.

Never track stage in the body text. After every stage change, regenerate the `README.md` manifest (see [updating-prds](../lifecycle/updating-prds.md#updating-the-readme-manifest)).

**Why enriched frontmatter:** Machine-readable metadata lets LLMs (including this skill, GUS integrations, and spec-driven dev tooling) parse PRD identity, audience, and downstream links without reading the full document. This aligns with the [spec-driven development](https://docs.google.com/document/d/17a_S58YUcQN9gyhd2GzKFVVDGxMPLhFNhAnUYuzjKVY/edit) approach where checked-in specs are context for agentic workflows.

---

## Administrative Section

| Role | Name |
|---|---|
| Theme Lead (Product) | [If applicable] |
| Initiative Lead (Product) | TBD |
| Major Feature Lead (Product) | TBD |
| Engineering Lead | TBD |
| Architect | TBD |
| UX Lead | TBD |
| CX/CDX Lead | TBD |
| Q3 & Q4 Leads | TBD |
| TPM | TBD |
| Release | [Release confirmed with user] |
| GUS Epic | [W- number if found via [gus-context lookup](../research/gus-context.md), or "TBD — create after alignment"] |
| Status | Draft |

## Spec Context

> A 2–4 sentence plain-language summary of what this PRD is trying to accomplish — written for an LLM (or a new team member) that needs to orient itself before reading the full document. Think of it as the "elevator pitch" that answers: What problem? For whom? What's the intended outcome?

**Example:**
> Service reps handling voice calls currently lose context when they need to pause a guidance plan to handle a customer tangent. This PRD defines a "step-level feedback" mechanism that lets reps mark individual plan steps as helpful, unhelpful, or skipped — giving the system signal to improve future plan generation for similar cases. The primary persona is the frontline service rep; the secondary beneficiary is the ML pipeline that uses this signal for prompt refinement.

**Rules:**
- Keep it under 75 words
- No jargon that isn't defined elsewhere in the PRD
- State the problem, the persona, and the intended outcome
- This section is for orientation only — all details live in Part 1 and Part 2
- Update this section whenever the PRD's core intent changes

---

## How to use this PRD

The PRD is a critical element to the planning process. It has two major parts that are needed at different points in the planning process.

* Part 1 - This section is critical to provide enough context to the UX and Architect stakeholders so that they can begin the design work to support more detailed planning.
* Part 2 - This section is critical to provide enough information for scrum teams to do bottoms up planning.

---

## Part 1: Major Feature Overview

### Major Feature Value Statement (the "What")

2–4 paragraphs describing:
- Current state and specific gaps/problems
- Proposed solution and what it enables
- Be precise: name the product, channel, and exact behavior being changed
- Use technical precision like Chad's examples

**Four Risks validation (run silently before drafting this section):** Before writing the Value Statement, validate the problem against all four risk dimensions. If any risk is not addressed, flag it as an Open Question.

| Risk | Question to answer | If unaddressed |
|---|---|---|
| **Value Risk** | Will customers actually use this? Does it solve a real, high-priority problem? | Flag in Open Questions: "Value risk — no confirmed customer signal for this problem" |
| **Usability Risk** | Can reps/admins figure out how to use it without training? | Flag in Open Questions: "Usability risk — rep workflow complexity not yet validated by UX" |
| **Feasibility Risk** | Can engineering build this with available technology and within the release window? | Flag in Open Questions: "Feasibility risk — engineering has not confirmed this is buildable in [release]" |
| **Viability Risk** | Does this make business sense? Does it fit within edition/pricing/legal constraints? | Flag in Open Questions: "Viability risk — edition and licensing implications not yet validated" |

### Major Feature Business Case (the "Why")

Numbered list (1-5) of concrete problems the current state causes:
1. **[Problem Category]**: Detailed description with specifics
   a. Sub-point with detail
   b. Additional context
2. **[Problem Category]**: Description
   
Include customer evidence where found:
- Example: "For example, Mastercard indicated that in its current form, they would allocate only $3 of a $10 budget to Service Assistant. However, if it could [solve problem], they would invest $7 or more."

### Scenarios (if applicable)

Visual representation or description of different use case flows showing how the feature routes/handles different contexts.

### Major Feature Initial Feature Scope

**Included (P0):**
* Bullet list of P0 capabilities
* Be specific about limits and constraints (e.g., "Support for configuring up to X agents")
* Include technical details

**Excluded:**
* What's explicitly not in scope for P0
* Why it's excluded or what release it's planned for

### Jobs to be Done

As a **[Job Performer]** resolving/performing [task], I need [capability] that:
* Allows me to [specific action]
* Lets me [specific action]
* Dynamically [specific action]
* Under certain conditions, [specific action]

So that I can [outcome with measurable impact].

### Current User Journeys / Solutions

1. **[Current Approach Name]**: Description
   - What exists today
   - **Gap**: Specific limitations with this approach
   
2. **[Another Current Approach]**: Description
   - What exists today
   - **Gaps**: 
     - i. Limitation details
     - ii. Additional limitations

### Approach (if applicable)

High-level strategy for solving the problem, broken into phases if applicable.

### UX Considerations

Key areas requiring design attention. These are outcome-focused callouts, not prescriptive solutions.

**Format (bullet list):**
* **[Design Challenge Area]**: What needs to be solved from the user's perspective
  - Context: Why this matters or what constraints exist
  - Success looks like: Observable user outcome

**Examples of good UX callouts:**
* **New information visibility**: Reps need to see when new context arrives (customer message, field update) without disrupting their current step
  - Context: High-velocity contact centers with 30+ simultaneous chats; banner notifications break flow
  - Success looks like: Rep notices new information within 2 seconds but can continue current action without interruption

* **Error state clarity**: When plan generation fails, reps need to understand what went wrong and what action to take
  - Context: Current "Generation failed" message provides no actionable guidance; reps escalate to supervisor
  - Success looks like: Rep reads error, understands root cause (e.g., "Missing required field: Account"), knows how to fix it

* **Multi-step confirmation**: Reps executing tool actions (refunds, account changes) need confidence before committing
  - Context: Current one-click execution causes accidental submissions; undo is complex
  - Success looks like: Rep reviews action details, confirms intent, sees confirmation before action executes

**Anti-pattern (over-solutioning):**
❌ "Use a blue badge in the top-right corner of the step card with a pulsing animation"
✅ "Rep needs to notice when a step updates due to new information, without disrupting their focus on the current step"

### UX Mocks

* Figma File: [Link]
* Click Through Prototype: [Link]
* Additional mockups as needed

### Internal Competitive Features (if found)

Only include this section if other Agentforce teams are building overlapping features:

* **[Team Name]**: [Brief description of their feature]
  - **Overlap**: [Degree of overlap - High/Medium/Low]
  - **Status**: [In development / Planned / GA]
  - **Slack Reference**: [Link to discussion/PRD]
  - **Recommendation**: [Collaborate / Consolidate / Differentiate / Defer]

### Relevant Research Insights

Only include competitors whose capabilities directly overlap with the feature being proposed. Reference [Competitive Intelligence Registry](../reference/competitive-intel.md) for positioning guidance.

* External Competitive Research (include only those relevant to THIS feature)
  - **Cresta**: [specific overlapping capabilities — e.g., real-time coaching, workflow enforcement]
  - **Google Agent Assist (CCAI)**: [specific overlapping capabilities — e.g., smart reply, knowledge assist]
  - **Sierra**: [specific overlapping capabilities — e.g., autonomous resolution, action execution]
  - **Decagon**: [specific overlapping capabilities — e.g., copilot suggestions, knowledge grounding]
  - **Intercom Fin**: [specific overlapping capabilities — e.g., copilot for reps, tone adjustment]
  - **Observe.AI**: [specific overlapping capabilities — e.g., real-time assist, compliance monitoring]
  
* SRA Differentiation for This Feature
  - How does this feature strengthen SRA's positioning against the listed competitors?
  - What gap does it close that competitors currently exploit?

---

## Part 2: Technical & Functional Requirements

### Requirements (Numbered)

Focus on **what** needs to happen, not **how** to implement it. Describe desired behaviors and outcomes.

**CRITICAL REQUIREMENT WRITING RULES:**
- Write from the user's or business's perspective, not the system's internal implementation
- Use outcome-based language: "Reps can...", "The system enables...", "Customers experience..."
- Avoid implementation verbs: "call", "invoke", "trigger", "execute", "query", "insert", "update"
- Specify business constraints, not technical constraints (rate limits yes, API patterns no)
- If you mention a technical term, you're probably over-solutioning—reframe as a capability

1. **[Requirement Category Name]**
   * **What needs to happen**: Describe the required behavior from a user/system perspective
   * **Why it matters**: Business justification
   * **Success looks like**: Observable outcomes
   * **Constraints**: Business rules, limits, or dependencies that engineering should know

### User Stories

| Priority | As a... | I want to... | So that... |
|----------|---------|--------------|------------|
| P0 | Admin | [capability] | [outcome] |
| P0 | CSR | [capability] | [outcome] |

### Acceptance Criteria

20+ testable outcomes organized by requirement. Each AC must describe a specific, verifiable business outcome — not implementation steps or technical assertions.

**Format:**

**Requirement 1: [Name]**
- [ ] AC 1.1: [When X happens, the user observes Y]
- [ ] AC 1.2: [Given condition A, the system enables behavior B]
- [ ] AC 1.3: [Edge case: when Z occurs, the expected outcome is W]

**Requirement 2: [Name]**
- [ ] AC 2.1: ...

**AC writing rules:**
- Use Given/When/Then or When/Then phrasing
- Describe observable outcomes, not internal system behavior
- Include edge cases and failure modes (what happens when things go wrong)
- Each AC maps to exactly one requirement — no orphan ACs
- Aim for 3–5 ACs per requirement, 20+ total across the PRD
- Include at least 3 "negative path" ACs (what the system should NOT do, or how it handles errors)

### Risks & Edge Cases

**Pre-Mortem (always run this first):** Imagine it's 6 months after launch and this feature has failed — adoption is near zero, reps hate it, or it was quietly rolled back. Write 2–3 sentences describing what went wrong. Then use those failure modes to populate the risk table below. This forces the PRD to confront the most likely failure scenarios before they happen.

> *Pre-mortem: "[Feature] shipped on time but reps ignored it because [failure reason 1]. Admins couldn't configure it correctly because [failure reason 2]. The feature was quietly disabled after [failure reason 3]."*

* **Risk: [Risk Name]**:
  - **Scenario**: Detailed description of what could happen
  - **Result**: Impact of the risk
  - **Mitigation**: How we handle/prevent it

### Questions to Refine the PRD

1. **[Open Question]**: Context and why we need to decide
2. **[Another Question]**: Context
3. **[Another Question]**: Context

### Open Questions (Alternative Format)

| Status | Question | Answer |
|--------|----------|--------|
| Open | [Question] | [Proposed answer or "TBD with rationale"] |
| Closed | [Question] | [Final decision] |

### Dependencies

* Business Dependencies: [To be completed by Product Manager]
* Technical Dependencies: [To be completed by Engineering Lead]

### UX User Journeys or Flow Diagrams

* Primary FigJam or Figma File Link: [Link]

### Architectural Concept Document

* Link to ACD / HLD: [Link]

### Comparable Features or Technologies

* [Competitor/technology comparisons]

### Non-Functional Requirements

**Edition / Addon Approach**: PE/EE/UE/UE+

**Personas / Permissions**: Table of personas and their base licenses

**Performance and scalability**: Current benchmarks and expectations

**Reliability, availability, maintainability**: Uptime expectations

**Security**: How system and data are protected

**Localization**: Local specifics support

**Usability**: Setup ease, mobile support

### Rollout Strategy

* BETA / Pilot / GA approach
* Alpha: [target]
* Beta: [target]
* GA: [target]

### Test Plan

* High-level test approach or link to test plan

### Required Content (Needed from CX)

* Release Note(s)
* UI Text
* Setup help documentation
* API developer documentation
* Trailhead
* Video
* Other (please describe)

---

## Appendix

### Key Decisions Made

* Keep a list of key decisions as the team approaches them

### Post GA Ideas & Priorities

Numbered list of 4–6 ideas for follow-on releases:
1. [Specific feature extension with detail]
2. [Another extension]

### References, Additional Resources

* Link to HLD
* Link to related PRDs
* Link to Slack discussions found during research
* Link to competitive research

---

## Document History

Always include this table at the very bottom of every full PRD — below the Appendix. It is the document change log and is required on both initial creation and all subsequent updates.

| Date | Author | Source | Summary of Changes |
|---|---|---|---|
| YYYY-MM-DD | Author Name | Initial draft | Created full PRD for [feature name] |

**Rules:**
- Add one row per update session (not per individual field). A batch of changes from one meeting = one row.
- **Date** — date the change was made
- **Author** — person who made the change; use note author when incorporating call notes or comment feedback
- **Source** — where the change came from: "Initial draft", "Gemini meeting notes — [Meeting Name]", "Canvas comment — [Author]", "Slack thread — [channel]", "Scope review", etc.
- **Summary** — one-line description of what changed in that batch
- This section is always appended as a new row; never overwrite existing rows
- Does not count toward the PRD line length estimate

---

## Review for Over-Solutioning (run after drafting)

Before finalizing the PRD, perform a self-review:

**Red flags to check for:**
- Are you describing APIs, endpoints, services, or classes? → Remove and reframe as capabilities
- Are you using technical verbs like "call", "invoke", "query", "execute"? → Rewrite with user-facing language
- Are you prescribing database schemas, data models, or storage approaches? → Remove technical details
- Are you suggesting specific technologies, libraries, or frameworks? → Only acceptable as reference examples, not requirements
- Are you dictating the architecture or implementation approach? → Focus on outcomes and constraints instead

**If you find over-solutioning:** Revise those sections to focus on what the user needs to accomplish and what business rules constrain the solution, not how to build it.

**When to include technical context (the boundary heuristic):**
The [Product Context Reference](../reference/product-context.md) contains deep technical detail (JSON schema, prompt architecture, token budgets, field names). Use this heuristic to decide what belongs in a PRD vs. what's over-solutioning:

- ✅ **Name the constraint** → "Token budget is ~1,895 tokens; any added grounding data competes for this space"
- ❌ **Don't name the solution** → "Add a new field to the JSON schema called `is_mandatory`"
- ✅ **Name the data model reality** → "Step-level completion tracking already exists (`LastModifiedBy` on step records)"
- ❌ **Don't prescribe the schema change** → "Add an `is_mandatory` boolean column to the ServicePlanStep object"
- ✅ **Name the integration point** → "Plan generation uses a 4-header structure; any enforcement must work within those headers"
- ❌ **Don't dictate the implementation** → "Insert a validation check after step 3 of the PlanGenerationService pipeline"

**Rule of thumb:** If you're telling engineering *what exists* or *what constrains them* — that's useful context. If you're telling them *what to build or change* — that's over-solutioning.
