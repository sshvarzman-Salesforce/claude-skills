---
name: sra-engineer
description: Service Assistant engineering expert — architecture, setup, debugging, integration patterns, Dynamic Plans framework, knowledge grounding, prompt pipeline, testing frameworks, and development workflows. Engineering-focused guidance for building and troubleshooting SRA.
tools: [mcp__mcp-adaptor__doc_search, mcp__plugin_google-workspace_vmcp-google-workspace__get_doc_content, mcp__plugin_codesearch_codesearch__search, mcp__plugin_codesearch_codesearch__blob, mcp__plugin_codesearch_codesearch__tree, mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_channel, mcp__plugin_slack_slack__slack_read_thread, Read, Bash, Agent]
---

# Service Assistant Engineer

> **Engineering-focused SRA expertise.** Architecture deep-dives, development setup, debugging workflows, integration patterns, testing frameworks, and implementation guidance. For engineers building, extending, and troubleshooting Service Assistant (formerly Service Planner).

**Invocation:** `/sra-engineer [your question]`

---

## What This Skill Does

You have an engineering question about Service Assistant. The skill:

1. **Understands the technical context** — routes to architecture docs, code repos, and engineering channels
2. **Provides implementation guidance** — setup steps, code pointers, integration patterns
3. **Debugs issues** — traces, logs, permission troubleshooting, common failure modes
4. **Points to testing frameworks** — Jupyter, LangSmith, E2E testing patterns
5. **Cites engineering resources** — Confluence, Google Docs, Git repos, Slack channels

**Example questions this skill handles:**
- "How do I set up a local Service Assistant development environment?"
- "What's the architecture of Dynamic Plans? How does the prompt pipeline work?"
- "How do I debug why knowledge grounding isn't working?"
- "What are the BPOs (Business Process Objects) for Actionable Plans?"
- "How do I configure a custom context variable in Dynamic Plan Service?"
- "What testing frameworks are available for validating prompts?"
- "How does the React Planner component work?"
- "What's the difference between Guidance Plans and Dynamic Plans from an engineering perspective?"
- "How do I access Service Assistant logs in Splunk?"
- "What's the session management flow for Dynamic Plans?"

---

## Core Engineering Resources

### 1. Service Assistant Knowledge Sharing (Master Doc)
**Document ID:** `1n2HBMjISdLPIo0VoeDdSZWlG0Hu4oC_gR1y8z56rxpU`  
**Link:** https://docs.google.com/document/d/1n2HBMjISdLPIo0VoeDdSZWlG0Hu4oC_gR1y8z56rxpU/edit?tab=t.0

Master document with links to ALL Service Assistant engineering resources including:
- Architecture diagrams and code pointers
- Demo videos and code walkthroughs
- Prompt pipeline details (Topic Prompt, Next Step Prompt)
- Dynamic Plans framework (Context Variable Service, Session Management Service)
- Testing frameworks (Jupyter, LangSmith)
- Debugging guides with required permissions
- Setup runbooks and org configuration guides

**Key Sections:**
- **Guidance Plans** — High-level overview, architecture, prompts
- **Actionable Plans** — BPOs, sequence diagrams, code walkthrough
- **Dynamic Plans** — Dynamic Plan Service, Actor Framework, Connect APIs, Prompt Pipeline
- **Testing Frameworks** — Guidance Plans testing, Dynamic Plans E2E testing, Jupyter local dev
- **Debugging & Logs** — Master debugging guide with permissions
- **Setup** — Development runbooks, org setup, Adaptive Experience metadata

### 2. Service Assistant Home (Confluence)
**URL:** https://confluence.internal.salesforce.com/spaces/SERVICEPLANS/pages/925545058/Service+Assistant+Home+formerly+Service+Planner

Confluence space covering:
- Product overview and feature documentation
- Release planning and roadmap
- Team structure and ownership
- Engineering standards and best practices

### 3. service-shared-ai-context (Git Repository)
**URL:** https://git.soma.salesforce.com/service-cloud/service-shared-ai-context/tree/main  
**README:** https://git.soma.salesforce.com/service-cloud/service-shared-ai-context/blob/main/README.md

Repository automating workspace context setup for core and near-core Service Assistant engineering:
- Dotfiles and environment configuration
- Shared AI context setup for engineers
- Boilerplate reduction for development workflows
- Owned by Annie Zhang (yuxi.zhang@salesforce.com)

### 4. Alternative Public Documentation
When internal resources are unavailable:
- **Help Documentation:** https://help.salesforce.com/s/articleView?id=service.sp_intro.htm&type=5
- **Release Notes:** https://help.salesforce.com/s/articleView?id=release-notes.rn_asp.htm&release=254&type=5
- **Trailhead Quick Look:** https://trailhead.salesforce.com/content/learn/modules/agentforce-service-planner-quick-look

---

## Architecture Overview

### Product Architecture
Service Assistant (formerly Service Planner) consists of several key architectural layers:

1. **Frontend Layer**
   - React Planner (UI component for plan rendering)
   - Lightning Web Components (LWC) for canvas logic
   - Platform events for real-time updates

2. **Service Layer**
   - Dynamic Plan Service (prompt pipeline orchestration)
   - Context Variable Service (session state management)
   - Session Management Service (conversation context)
   - Response and Request Service (API gateway)

3. **Integration Layer**
   - Connect APIs (UI, SOBA team integrations)
   - Off-core provider and broker (ART Provider, ServicePlanSkillActor)
   - Knowledge Grounding Integration
   - Data Cloud integration (File-Based Data Kit)

4. **Prompt Pipeline**
   - Topic Prompt (intent classification)
   - Next Step Prompt (reasoning and action selection)
   - Knowledge Grounding (retrieval and context injection)
   - Compressed Prompt (performance optimization)

5. **Backend Services**
   - Dynamic Plan Framework
   - Actor Framework (RecActorAction Feed)
   - OOTB Topic handling
   - Access checks and security

### Key Components

#### Guidance Plans
- **What:** Pre-structured plans based on case context
- **Architecture:** Lucid diagram available in master doc
- **Prompt Structure:** servicePlansGuidanceUnifiedType.yaml
- **Code Location:** NGS team repo (see master doc for pointers)

#### Actionable Plans
- **What:** Executable steps with BPO integration
- **BPOs:** Business Process Objects (see Confluence link in master doc)
- **Sequence Diagram:** Available in Confluence
- **Documentation:** https://confluence.internal.salesforce.com/spaces/NGS/pages/1159530514/Actionable+Plans

#### Dynamic Plans
**High-Level Components:**
- **In Action:** Case, Messaging Session, Voice Call
- **Actor Framework:** RecActorAction Feed, ServicePlanSkillActor
- **Off-core Integration:** art-provider (https://git.soma.salesforce.com/service-cloud-realtime/art-provider/tree/main/src/main/java/com/salesforce/scrt/v2/art/provider)
- **Broker:** art-broker (https://git.soma.salesforce.com/service-cloud-realtime/art-broker/tree/main)

**Dynamic Plan Service Backend:**
- Context Variable Service (session state)
- Session Management Service (recorded demo available)
- Response and Request Service (API layer)

**Prompt Pipeline:**
- Topic Prompt: https://salesforce.quip.com/2y5AAkvSGWtO
- Next Step Prompt: https://salesforce.quip.com/VbbAAoioGfgi
- Knowledge Grounding Integration: See master doc (recording start to 22:40)
- Performance Enhancements: Compressed Prompt optimization

#### Knowledge Grounding
- **Integration:** Agentforce Data Libraries, custom search indexes
- **Architecture:** Lucid diagram available
- **Custom Retriever:** DMO (Data Model Object) configuration
- **HTML Strip Options:** For knowledge article rendering
- **Multi-source Support:** Salesforce Knowledge, SharePoint, Google Drive, 15+ sources via Data 360

#### OOTB Topics
- **Access Checks:** Security model for topic visibility
- **UI Spike:** SF/SPA team documentation (https://salesforce.quip.com/ogW7ArRHkgbG)
- **Record Companion:** Context-aware topic suggestions

---

## Development Setup

### Prerequisites
1. **Service Plan Development Runbook:** https://salesforce.quip.com/yBxfAo7vyIXX
2. **Service Assistant Org Setup Guidance:** https://salesforce.quip.com/sGzJAGMeXC0P
3. **Agentforce Dev/Testing using Salesforce Workspaces:** https://salesforce.quip.com/j4FSAHMToeAK
4. **Adaptive Experience Metadata Setup:** https://salesforce.quip.com/jDYgAP5pumbv

### Permission Sets Required
- **Service Planner Builder** (includes "View Setup and Configuration")
- **Service Planner User** (for end users)
- **Service Rep Knowledge Access** (for knowledge grounding)
- **Data Cloud User / Data Cloud One** (for Data Cloud integration)

### Environment Configuration
1. **Stable Testing Environment:** SDB3 recommended over main
2. **Voice Call Org Setup:** See master doc for specific configuration
3. **Custom Metadata Records:** Required for configuration
4. **Lightning Knowledge:** Required with Enhanced Knowledge Settings

### Code Repositories
- **NGS Team Repo:** https://git.soma.salesforce.com/service-cloud/ngs-team (see SERVICE_PLAN.md)
- **ART Provider:** https://git.soma.salesforce.com/service-cloud-realtime/art-provider
- **ART Broker:** https://git.soma.salesforce.com/service-cloud-realtime/art-broker
- **service-shared-ai-context:** https://git.soma.salesforce.com/service-cloud/service-shared-ai-context

---

## Testing Frameworks

### Guidance Plans Testing
- **E2E Testing:** See master doc for comprehensive framework
- **Test Documentation:** NGS Dynamic Plan Prompt testing E2E KT Masterdoc

### Jupyter Testing
- **Local Dev Testing:** Jupyter Script Local Dev Testing guide available
- **Recorded Session:** NGS 262 In Person Planning: Day 1 - 2026/02/23 (Recording 3)
- **Use Case:** Prompt iteration, knowledge grounding validation, response quality testing

### LangSmith Framework
- **Purpose:** Prompt versioning, A/B testing, performance tracking
- **Integration:** See master doc for setup guide

### Testing Best Practices
1. **Case Requirements:** Must have both Subject AND Description fields to generate service plan
2. **Multi-intent Cases:** <10% of cases — require special handling/testing
3. **Knowledge Access:** Verify permissions for knowledge retrieval
4. **Stable Environment:** Use SDB3 over main for more predictable results

---

## Debugging & Troubleshooting

### Master Debugging Guide
**Link:** https://salesforce.quip.com/agcIAjGjUm0a  
Comprehensive guide on debugging Guidance Plans including:
- Required permissions
- Log access procedures
- Common failure modes
- Troubleshooting decision trees

### Debug Dynamic Plans
**Guide:** Debug Dynamic Plan and Planner Service with Session Id  
Available in master doc with step-by-step instructions.

### Common Issues

#### 1. Service Plan Not Generating
**Symptoms:** No plan appears after case creation  
**Root Causes:**
- Case missing Subject or Description (BOTH required)
- Insufficient information in case fields
- Knowledge grounding permission issues
- Multi-intent case (conflicting signals)

**Debugging Steps:**
1. Verify Case.Subject and Case.Description are populated
2. Check Service Planner User permission set assigned
3. Validate knowledge access permissions
4. Review Splunk logs for retrieval failures
5. Check for multi-intent indicators

#### 2. Quick Actions Not Appearing
**Symptoms:** Work Summaries or Summarize Case action missing  
**Root Causes:**
- Quick Action metadata not deployed
- Permission set missing Quick Action access
- Dynamic Plans addon not enabled

**Debugging Steps:**
1. Verify Quick Action metadata exists in org
2. Check permission set assignments
3. Validate Dynamic Plans addon license
4. Review custom metadata configuration

#### 3. Knowledge Grounding Not Working
**Symptoms:** Plans don't reference knowledge articles  
**Root Causes:**
- Data Library not configured
- Custom retriever configuration missing
- Knowledge article permissions
- Confidence threshold filtering (0.6 default)
- Custom search index not built

**Debugging Steps:**
1. Verify Data Library setup and indexing status
2. Check custom retriever DMO configuration
3. Validate knowledge article permissions
4. Review AIRetrieverRequest/Response__dll logs
5. Test confidence threshold (try lowering from 0.6 to 0.5)
6. Verify custom search index health

### Logging & Tracing

#### Splunk Access
- **EDL Logs:** `EDL[USER_MSG]` and `EDL[HLS]` events show planner service data
- **Retriever Logs:** `RetrieverResponseFilter` shows retrieved/retained records
- **Session Logs:** Search by Session ID for full conversation trace

#### Data Library Tables
- **AIRetrieverRequest__dll:** Knowledge retrieval queries
- **AIRetrieverResponse__dll:** Retrieved articles and scores
- **Note:** May not capture custom Apex action retrievals

#### Platform Events
Monitor platform events for:
- Plan generation triggers
- Action execution results
- Session state changes
- Error conditions

---

## Integration Patterns

### Voice Call Integration
**Setup Guide:** Available in master doc (Voice Call Org Setup)  
**Objects:** Case + VoiceCall (two objects per interaction)  
**Pattern:** Case creation from voice calls triggers plan generation

### Data Cloud Integration
**Component:** File-Based Data Kit (FBDK) for Service Cloud  
**Purpose:** Multi-source knowledge access (SharePoint, Google Drive, etc.)  
**Configuration:** Custom metadata + Data Cloud One license

### Service Insights
**Purpose:** Analytics and performance tracking  
**Integration:** Platform events feed Service Insights dashboards  
**Setup:** See master doc for configuration

### Multi-Agent Scenarios
**Challenge:** CVS use case — 8 LOBs, multiple agents active per interaction  
**Pattern:** One agent per Case record, orchestration via custom logic  
**Future:** Agent-to-agent handoff patterns in development

---

## Performance & Optimization

### Prompt Optimization
**Compressed Prompt Pattern:**
- Token reduction strategies
- Field-level selection over full objects
- 5-section Data grounding model optimization

**Performance Metrics:**
- AI Gateway 55% faster with optimizations
- Token budget constraints for grounding data
- CLT rendering optimizations

### Knowledge Grounding Performance
- **Parallel Retrieval:** NGA's parallel knowledge+topic retrieval
- **Agent API v2:** Lower latency vs. v1
- **Model Upgrades:** 4.0 → 4.1 → 4.5 Haiku (quality vs. latency tradeoffs)

### Latency Research
See `sra-latency-research` skill for:
- Per-phase pipeline analysis
- NGA latency improvements
- Model upgrade impacts

---

## Key Engineering Channels

### Primary Engineering Channels
- **#service-plans-engineering** — Main engineering discussion
- **#service-plans-eng-design** — Architecture and design decisions
- **#service-plans-model-experimentation** — Prompt testing and model evaluation
- **#service-cloud-ai-powerups** — AI tools and engineering productivity
- **#service-assistant-java-atlas-migration** — NGA/Agent Script migration

### Specialized Channels
- **#sra-quick-action-migration-to-nga** — Quick Actions NGA migration
- **#serviceplansvoice-slack-agentforce** — Voice integration
- **#voice-plans** — Voice-specific engineering
- **#ai-platform-eng** — Platform-level AI engineering

### Cross-Team Collaboration
- **#service-plans-product-ai-collab** — PM & Engineering sync
- **#service-plans-ai-cloud-service-cloud-collab** — AI Cloud integration
- **#service-assistant-pm-se-ta-ea-fde-collab** — Broad cross-functional

---

## Key Engineering Contacts

From the research and master doc:

- **Annie Zhang** (yuxi.zhang@salesforce.com) — service-shared-ai-context repo owner, AI tools
- **Alberto Ruiz** (alberto.ruiz@salesforce.com) — CX team, SRA GA docs, configuration expert
- **Lihang Pan** — Dynamic Plans architecture, NGA research, CLT variable injection
- **Bingbing Wu** — Engineering leadership
- **Wenqing Dai** — CVS requirements, engineering lead
- **Gautam Vasudev** — Engineering
- **Aaron Fiske** — Agent files, SERVICE_PLAN.md author
- **Fabienne Dorson** (fdorson@salesforce.com) — Service Assistant features

---

## Known Limitations & Considerations

### Field Requirements
- **Case Subject + Description:** BOTH required to generate service plan (not negotiable)
- **Flow Automation:** Often requires record-triggered flow to auto-populate these fields

### Multi-Intent Cases
- **Frequency:** <10% of cases
- **Challenge:** Conflicting signals in case description
- **Handling:** Special logic required, no OOTB solution

### Summarize Case Quick Action
- **Issue:** Doesn't always show even with correct configuration
- **Investigation:** Active debugging; check custom metadata + permission sets

### External Sharing
- **Slack Connect:** Cannot post to externally shared channels (Slack Connect)
- **Workaround:** Internal-only channels required

### Testing Environment Stability
- **SDB3:** More stable than main for development/testing
- **Recommendation:** Use SDB3 for pre-production validation

---

## Related Skills

When deeper expertise is needed, delegate to:

| Skill | When to delegate |
|---|---|
| `sra-expert` | General SRA questions, product fundamentals, roadmap |
| `sra-setup-debug` | Complex setup issues, permission troubleshooting |
| `sra-agent-debugger` | Agent Script debugging, NGA-specific issues |
| `sra-test-case-writer` | Writing test cases, test framework setup |
| `sra-latency-research` | Deep latency analysis, performance optimization |
| `sra-nga-migration` | NGA/Agent Script migration questions |

**General rule:** Use `sra-engineer` for architecture, development setup, code pointers, integration patterns, and engineering workflows. Delegate to specialists for deep troubleshooting, test case writing, or migration-specific questions.

---

## Usage Examples

### Architecture Deep-Dive
```
/sra-engineer How does the Dynamic Plans prompt pipeline work? What are the components?
```
→ Explains Topic Prompt + Next Step Prompt flow, cites Quip docs, points to Context Variable Service and Session Management Service, links to Lucid diagrams.

### Development Setup
```
/sra-engineer How do I set up a local dev environment for Service Assistant?
```
→ Walks through Service Plan Development Runbook, lists prerequisites (permission sets, org prefs), points to service-shared-ai-context repo, explains dotfiles setup.

### Integration Question
```
/sra-engineer How does Voice Call integration work with SRA?
```
→ Explains Case + VoiceCall object pattern, points to Voice Call Org Setup guide in master doc, cites #serviceplansvoice-slack-agentforce channel.

### Debugging Issue
```
/sra-engineer Knowledge grounding isn't returning any articles. How do I debug this?
```
→ Provides debugging decision tree: Check Data Library indexing → Validate custom retriever DMO → Review AIRetrieverRequest/Response__dll logs → Test confidence threshold → Verify permissions. Cites Master Debugging Guide.

### Code Location
```
/sra-engineer Where is the ServicePlanSkillActor implemented?
```
→ Points to art-broker repo: https://git.soma.salesforce.com/service-cloud-realtime/art-broker/tree/main. Explains Actor Framework role, suggests searching for class in repo.

### Testing Framework
```
/sra-engineer What testing frameworks are available for validating prompts?
```
→ Lists Jupyter (local dev), LangSmith (A/B testing), E2E framework (master doc). Provides links to Jupyter Script Local Dev Testing guide and recorded KT session.

### Performance Optimization
```
/sra-engineer How can I reduce latency in plan generation?
```
→ Explains Compressed Prompt pattern, token reduction strategies, parallel retrieval in NGA, Agent API v2 benefits. References sra-latency-research skill for deep analysis.

---

## Answer Quality Standards

Every engineering answer should:
1. **Cite engineering resources** — Confluence, Quip, Git repos, master doc sections
2. **Provide code pointers** — File paths, class names, method names where applicable
3. **Link to diagrams** — Lucid, architecture diagrams, sequence diagrams
4. **Reference channels** — Where to ask follow-up questions or get real-time help
5. **Include setup steps** — Concrete, actionable instructions when applicable
6. **Note permissions** — Required permission sets, org prefs, security settings
7. **Flag known issues** — Limitations, workarounds, active investigations

**Avoid:**
- ❌ Generic architecture descriptions without specific code/doc references
- ❌ Answering setup questions without linking to runbooks
- ❌ Debugging guidance without log locations or trace procedures
- ❌ Integration patterns without repo links or class names

---

## Changelog

| Date | Change |
|---|---|
| 2026-07-08 | **Initial skill creation** — Engineering-focused SRA expertise based on Service Assistant Knowledge Sharing master doc, Confluence space, service-shared-ai-context repo. Architecture overview, development setup, testing frameworks, debugging guides, integration patterns, performance optimization, engineering channels, and key contacts. Companion to sra-expert (product/PM focus) with engineering-specific deep-dives. |
