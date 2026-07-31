# Changelog — Salesforce PRD Writer Skill

All notable changes to the `sf-prd-writer` skill are documented here.

---

## [2.0.0] - 2026-05-20

### Added — Prepared for Internal Salesforce Sharing
- **Setup & Customization section** near top of `skill.md` with step-by-step instructions for other PMs
- **Parameterized product name** — Phase 1 now shows "(Customizable)" note
- **Example canvas registry** — Original author's 8 SRA canvases shown as reference; new adopters start with empty registry
- **Customization notes** throughout:
  - SRA Channel Registry (Phase 2)
  - Competitive Intelligence Registry (Product Context Reference)
  - Product-specific sections flagged for replacement
- **README.md** with quick start, feature overview, customization guide, best practices
- **CHANGELOG.md** (this file)
- Removed hardcoded user name from Administrative table template (was "Chad Goldsmith", now "TBD")

### Changed
- Title description: "Service Rep Assistant features" → "Salesforce products"
- Tone references: "Chad's standard structure" → "standard structure" (depersonalized)
- Canvas registry: Moved original author's examples to a commented reference block
- Made customization low-friction: minimal changes = 5 min, full changes = 2-3 hours

---

## [1.5.0] - 2026-05-19

### Added — Enterprise Context & Quality Gates
- **Competitive Intelligence Registry** in Product Context Reference
  - 6 competitors: Cresta, Google CCAI, Sierra, Decagon, Intercom Fin, Observe.AI
  - Per-competitor positioning guidance, known accounts, overlap assessment
  - Integration with Phase 2 Slack research (auto-search competitor mentions)
- **SRA Channel Registry** with 16 channels + IDs + purpose
  - FDE Collaboration, SE Collaboration, PM Leads, Eng teams, Agentforce channels
  - Channel-scoped search patterns in Phase 2
- **Google Drive reference folders** (Beta Docs, Previous PRDs, Record Companion architecture)
- **Research depth routing** (Step 2b): None / Targeted / Full
  - Avoids unnecessary API calls for typo fixes and date changes
  - Full research for new PRDs, expansions, major changes
- **Phase 10 — Status Dashboard**
  - Portfolio overview: format, release, stage, last modified, gaps, open questions
  - Needs Attention alerts (high gaps, stale, unresolved questions)
  - Cross-PRD alerts (token budget conflicts, dependency overlaps, customer overlap)
  - Actionable suggestions
- **Phase 2a — GUS Integration** (optional, user-initiated)
  - Query existing epics, pull context into PRD
  - Create Major Feature epics, link to parent initiatives
- **Phase 3c — Structural Fidelity Check** (one-pagers only)
  - Validates 10 sections in prescribed order, H1/H2 hierarchy, horizontal rules, table formats
  - Enforces ~80-150 line target
- **Graceful tool failure handling**
  - When Slack tools fail: note failure, proceed with user context, add `⚠️ Evidence incomplete` flag
  - Canvas read failures: skip that canvas, note which PRDs couldn't be cross-referenced, proceed
  - Never silently drop research; always tell user what couldn't be gathered
- **Boundary heuristic for technical context**
  - Clarified what belongs in PRD (constraints, data model reality, integration points)
  - vs. over-solutioning (schema changes, API implementation, service architecture)
- **One-pager line target raised** from ~70-130 to ~80-150 (customer signal depth drives this)

### Fixed
- Phase 9 / Phase 6a contradiction resolved: expansion now explicitly lifecycle-aware (pre-canvas = clean rewrite, post-canvas = incremental)

---

## [1.4.0] - 2026-05-05

### Added — One-Pager Format
- **Phase 3b — One-Pager Draft** (Requirements One-Pager format)
  - Flat `#` headers, no Part 1/Part 2 split
  - 10 sections: Problem, Customer Signal, Why This Matters, Gap (Today vs. Target), Who Benefits, JTBD, Scope, Success Metrics, Open Questions, Customer References
  - Target ~70-130 lines (condensed, not under-researched)
  - Canonical reference: `F0B05DPJDED` (Action Output-Driven Knowledge Re-Grounding)
- **Phase 9 — Expand One-Pager to Full PRD**
  - Adds missing full-PRD sections (Scenarios, Journeys, HLD link, NFRs, full test plan)
  - Deepens existing sections (Business Case, Requirements, ACs, Risks)
  - Preserves decision trail (Portfolio Cross-Reference, Comment Log, Key Decisions)
  - Lifecycle-aware: clean rewrite pre-canvas, incremental post-canvas
- **Format mode detection** in Phase 1
  - Keywords: "one-pager", "1-pager", "short PRD", "lightweight PRD" → one-pager mode
  - Keywords: "full PRD", "detailed PRD", "complete PRD" → full PRD mode
  - Ambiguous → ask user
- Updated output options to clarify one-pagers can be created as canvas or Google Doc too

---

## [1.3.0] - 2026-04-23

### Added — Multi-PRD Operations
- **Phase 8 — Batch Mode**
  - Update multiple PRDs in one session
  - Builds change manifest, waits for user confirmation, executes sequentially
  - Groups by PRD, reads each once, applies all changes (markdown first, canvas second)
  - Batch summary report with success/failure per change
  - Can combine with Phase 7 (comment review → batch changes)
  - Context budget awareness: warns if >15 changes or >5 PRDs
- **Phase 7 — Comment Review & Response**
  - Discovers comments via Slack search + canvas annotations
  - Presents each comment with attribution, section context, suggested action
  - Waits for user decision (accept → update PRD, reply → send message, reject → explain)
  - Actions trigger Phase 6 incremental updates
  - Appends `### Comment Review Log` to markdown Appendix
  - Reply format: threaded, clear attribution, links to PRD change
- Added comment-checking workflows to Phase 0 routing table

---

## [1.2.0] - 2026-04-15

### Added — Two-Stage Lifecycle Model
- **Phase 6a — Markdown-Only (Pre-Canvas) Clean Rewrites**
  - While no canvas exists: all changes via Write tool, full file replacement
  - No strikethroughs, no `*Added:*` markers, no change annotations
  - Consolidates prior edits into clean final state
  - Rationale: No collaboration history to preserve; markers create noise during early drafting
- **Phase 6b — Post-Canvas Incremental Updates**
  - Once canvas exists: all changes are additive or conflicting (never delete)
  - Additive = append with `*Added DATE:*` prefix
  - Conflicting = strikethrough old + blockquote replacement with `> **Updated DATE · SOURCE:**`
  - Markdown uses Edit tool; canvas uses `slack_update_canvas` with `action=append`
  - Preserves comments, edit history, collaborator changes
- **Phase 6.0 — Determine Lifecycle Stage**
  - Checks PRD Canvas Registry to determine pre-canvas vs. post-canvas
  - Routes to 6a or 6b accordingly
- **Phase 6c — Canvas Update Mechanics**
  - Never replace bold-text headers (destroys child content)
  - Sequential updates only (no parallel `slack_update_canvas` calls)
  - Re-read canvas after each update to confirm
- **Phase 6d — Keeping Markdown and Canvas in Sync**
  - Same date, source, change context in both surfaces
  - Markdown = source of truth for version control
  - Canvas = collaboration surface

### Changed
- Phase 5 now explicitly states canvas creation is **user-initiated only**
- Phase 5b added for canvas creation workflow (confirm current markdown, create, add to registry, report transition)

---

## [1.1.0] - 2026-04-08

### Added — Portfolio Intelligence
- **Phase 2b — Cross-Reference Your PRD Portfolio**
  - Scans local PRD files in `.agents/artifacts/prds/`
  - Reads known canvas PRDs from PRD Canvas Registry
  - Checks for: dependency overlap, token budget conflicts, scope overlap, rollout conflicts, shared NFRs, synergy opportunities, contradictions
  - Outputs `## Portfolio Cross-Reference` table in Appendix
  - Fallback: ad-hoc Slack search for PRDs not in registry
- **PRD Canvas Registry** table in Phase 2b
  - Maintains list of known PRD canvases (canvas ID, title, release)
  - Auto-updates when new canvases are created
  - Used to determine lifecycle stage (pre-canvas vs. post-canvas)
- Added Research depth note to Phase 2 (always full for new PRDs, can skip for minor edits)

---

## [1.0.0] - 2026-04-01

### Added — Initial Release
- **Phase 0 — Route the Request**
  - Identify target PRD (explicit vs. ambiguous)
  - Present portfolio, wait for user selection
  - Route to appropriate phase (new, update, canvas creation, comment review, batch, status)
- **Phase 1 — Understand the Feature Idea**
  - Ask release (default 262)
  - Identify problem, personas, context
- **Phase 2 — Gather Context from Slack**
  - Internal competition check
  - Feature name, customer mentions, beta signals, bugs/blockers, prior PRDs/HLDs
  - Engineering confirmation quotes
  - Inline citations in Business Case
- **Phase 3 — Draft the PRD** (full PRD only in v1.0)
  - Administrative section with roles, release, status
  - Part 1: Value Statement, Business Case, Scenarios, Scope, JTBD, Current Journeys, Approach, UX Mocks, Internal Competitive Features, Relevant Research Insights
  - Part 2: Requirements (numbered, with What/Why/Success/Constraints), User Stories, Acceptance Criteria (20+), Risks & Edge Cases, Questions to Refine, Dependencies, UX Journeys, ACD link, Comparable Features, NFRs, Rollout Strategy, Test Plan, Required Content
  - Appendix: Key Decisions, Post GA Ideas, References
- **Phase 4 — Review for Over-Solutioning**
  - Red flags check (APIs, endpoints, services, classes, schemas)
  - Anti-solutioning guidelines enforcement
- **Phase 5 — Save and Deliver the PRD**
  - Save as markdown in `.agents/artifacts/prds/`
  - Summarize what's ready vs. what needs input
  - Offer to draft placeholder sections
- **Phase 6 — Updating an Existing PRD** (clean rewrites only in v1.0)
  - Read current file, apply changes, write back
  - Summarize what changed
- **Product Context Reference** section
  - Product positioning (ambient AI Agent in the flow of work)
  - Editions & Licensing (E4S, A4S, E1E, A1E)
  - Prerequisites (Einstein Generative AI, Data Cloud, Agentforce Builder, Service AI Grounding)
  - Building Blocks Vocabulary (Topics, Instructions, Actions, Eligibility Flow, Skills)
  - Guidance Plans vs. Dynamic Plans comparison table
  - Plan Output Structure (4-header format, step types, resolution statuses)
  - Plan Generation Pipeline (Detect → Plan → Outcome)
  - Prompt Architecture (3-tier privilege model, 5-part Data section)
  - Plan Output JSON Schema
  - Prompt Optimization Context (Alexandre Galas benchmarks: 9,289 → 1,895 tokens, 25s → 11s)
  - Beta Program Context
- **Key Principles**
  - Focus on problems, not solutions
  - Evidence-first Business Case
  - Customer outcomes over features
  - Part 1 / Part 2 split mandatory
  - Acceptance Criteria = testable outcomes
  - Risks must include mitigations
  - Post GA Ideas in Appendix
  - Inline citations
  - Always prompt for release
  - Version control friendly (markdown)
  - Collaborate, don't dictate (outcome-based requirements)

---

## Versioning

- **Major version (X.0.0)**: Breaking changes (phase reordering, format changes, removed features)
- **Minor version (x.Y.0)**: New features (new phases, new output formats, new integrations)
- **Patch version (x.y.Z)**: Bug fixes, documentation improvements, minor refinements

---

## Maintenance

This skill is maintained by Chad Goldsmith (Service Rep Assistant PM).

For questions, bugs, or feature requests:
- Slack: `#service-assistant-pm-leads`
- DM: Chad Goldsmith

Pull requests welcome (if shared in internal Salesforce repo).
