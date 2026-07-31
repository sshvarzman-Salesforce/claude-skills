# SRA Slack Channel Registry

> **Customization Note:** This registry is specific to Service Rep Assistant. If you're a PM for a different product, replace this file with your product's key Slack channels.

These are the key Slack channels for Service Rep Assistant context. Use `slack_read_channel` on relevant channels when looking for recent discussions, and include channel-scoped searches via `slack_search_public_and_private` with `in:<channel_id>` filters.

| Channel | ID | What it covers |
|---|---|---|
| A3 Record Companion | `C0A99FLAE1G` | Core SRA product channel — feature discussions, bugs, releases |
| Service Assistant for Conversations | `C08DEK0ND0B` | Messaging channel (MIAW) specific SRA discussions |
| Service Assistant for Voice | `C09K1CCKL8J` | Voice channel specific SRA discussions |
| FDE Collaboration | `C0AN1E181M3` | Forward Deployed Engineers — customer-facing implementation feedback, gap reports |
| SE Collaboration | `C08E300HPUK` | Solution Engineers — pre-sales feedback, competitive insights, customer asks |
| Service Assistant Engineering | `C06TPK97CCE` | Engineering-wide discussions, architecture decisions, cross-team coordination |
| Service Assistant PM Leads | `C078Y9DEDEE` | PM leadership — roadmap, prioritization, strategy |
| Service Assistant Leads | `C07DVDVH26A` | Cross-functional leads — PM + Eng + UX alignment |
| NGS Engineering | `C06NDLHQJD7` | Next-Gen Service (planner service, plan generation pipeline) |
| Sox Engineering | `C02CLRPJT1R` | Sox eng team — service orchestration |
| SPA SF Engineering | `C02P450NJ84` | SPA SF eng team — UI components, LWC, service plan rendering |
| SOBA Engineering | `C05UAR03WHY` | SOBA eng team — testing framework, quality metrics |
| SOUP Engineering | `C041YHQ8LQ0` | SOUP eng team |
| Agentforce | `C0981N8RC57` | Agentforce platform discussions — cross-product coordination, platform capabilities |
| Agentforce Builder | `C088HG7U448` | Agent Builder product — NGA, topics, actions, configuration UX |
| Agentforce Big Impact | `C07RDL9CLDR` | High-impact Agentforce initiatives — strategic decisions, cross-team alignment |
| Agentforce Innovation | `C06DZ4J5T4K` | Agentforce innovation — new capabilities, platform evolution, emerging patterns |

**Customer channels — Meta:**

| Channel | ID | What it covers |
|---|---|---|
| sra-meta (primary) | `C0ALH8U1EAE` | Meta SRA implementation channel — product gaps, configuration issues, FDE support |
| meta-af-service-q1-engagement | `C0A1Z1YCD28` | Meta Agentforce for Service Q1 engagement — reporting requirements, GA readiness |
| meta-af-service (general) | `C0AMM90TLRJ` | Meta Agentforce for Service general channel |
| Meta SRA reporting DM group | `C0B2EQY6LAX` | DM group: Chad, Sehar, Dan Franasiak, Lihang, Sophia, Manjeet — Meta SRA metrics and RecActorActionFeed reporting |

**Customer channels — EA (Electronic Arts):**

| Channel | ID | What it covers |
|---|---|---|
| temp-ea-poc-service-assistant-blockers | `C0A5B2HAJSU` | EA SRA POC blockers — Dynamic Plans pilot, consumption issues, feature gaps, value KPIs |

**Additional channels:** There are also per-capability channels following the naming pattern `service-assistant-capabilities-*` (e.g., `service-assistant-capabilities-dynamic-plans`, `service-assistant-capabilities-service-replies`). Search for `service-assistant-capabilities-` + the relevant skill name when researching a specific SRA capability.

## Research strategy by channel type

| Research need | Which channels to check |
|---|---|
| **Customer quotes, named VOC, feature asks** | **Google Drive: Customer & Enablement Call Notes folder** (search first — richest source of first-hand signal) |
| Customer feedback, field evidence | FDE Collaboration (`C0AN1E181M3`), SE Collaboration (`C08E300HPUK`) |
| Engineering feasibility, architecture | NGS Engineering (`C06NDLHQJD7`), Service Assistant Engineering (`C06TPK97CCE`), Sox/SPA/SOBA/SOUP per domain |
| Product strategy, roadmap, prioritization | PM Leads (`C078Y9DEDEE`), Leads (`C07DVDVH26A`) |
| Channel-specific features (Messaging) | Service Assistant for Conversations (`C08DEK0ND0B`) |
| Channel-specific features (Voice) | Service Assistant for Voice (`C09K1CCKL8J`) |
| General SRA product context | A3 Record Companion (`C0A99FLAE1G`) |
| Agentforce platform, NGA, Agent Builder | Agentforce (`C0981N8RC57`), Agentforce Builder (`C088HG7U448`), Agentforce Big Impact (`C07RDL9CLDR`), Agentforce Innovation (`C06DZ4J5T4K`) |
| Capability-specific (Dynamic Plans, SR, etc.) | `service-assistant-capabilities-*` channels |
| Prior art, historical PRDs | Google Drive: Previous PRD Documents folder |
| Beta requirements, customer onboarding | Google Drive: Beta Documents folder |
