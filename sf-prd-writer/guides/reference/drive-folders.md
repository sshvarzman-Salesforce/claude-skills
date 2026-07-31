# Google Drive Reference Folders

These folders contain historical PRDs, beta documentation, architecture references, presentation decks, and demo videos. Use `docs_search` or `docs_get` to access specific documents when deeper context is needed.

| Folder | Link | What it covers |
|---|---|---|
| **Shared PRD Google Docs (OUTPUT)** | [Drive Folder](https://drive.google.com/drive/folders/1iugu24A3_xt6o-l6ofxo2TqkuZfZdeQI) | **All new PRD Google Docs are created here.** Shared with the PM team. Always pass `folder_id: "1iugu24A3_xt6o-l6ofxo2TqkuZfZdeQI"` when calling `docs_create`. Also search here when looking for the latest version of a PRD Doc. |
| **Chad SRA Docs** | [Drive Folder](https://drive.google.com/drive/folders/1oonsD3OBh9fnegg8FT4TOtnjFndhzJMb) | Chad's working SRA documents — Gemini meeting notes, customer session logs, beta feedback trackers (e.g. EA daily scrum), architecture references, and working docs for active features. **Search here first** for recent meeting notes, action items, and in-progress working docs before checking the broader folders. |
| **Service Assistant Beta Docs (INTERNAL)** | [Drive Folder](https://drive.google.com/drive/folders/1YC2AgI5pANbQDLs4l-N3TQkXprYPavNL) | **⭐ PRIMARY BETA DOCS FOLDER** — Implementation guides, subagent best practices, knowledge grounding guides, pre-GA feature docs. [Landing Page Doc](https://docs.google.com/document/d/14U2OGYFGe4S4GOECMBWgvzSyfAu1snjtMkPA__WfnxQ/edit?tab=t.0). **Search here first** for beta setup instructions, implementation patterns, and feature enablement guides. Contains closed beta docs for Case, Messaging, Voice, multiple agent experience, case catch-up/insights, subagent design patterns, ADL grounding, and knowledge article optimization. |
| Beta Documents | [Drive Folder](https://drive.google.com/drive/folders/1dLNp5UDyi_2KVdJWu3OpKytUpcVh87vN) | Legacy beta program docs folder — setup guides, customer onboarding, beta requirements, known limitations, feedback trackers. **NOTE:** For current beta docs, use the "Service Assistant Beta Docs (INTERNAL)" folder above. |
| Previous PRD Documents | [Drive Folder](https://drive.google.com/drive/folders/1Hg-c0GixGEOHzoF5SEnrADRiFIyXNv6I) | Historical PRDs for prior SRA features — useful for tone matching, scope precedent, and understanding what's already been built |
| PM Deck Folder | [Drive Folder](https://drive.google.com/drive/folders/1SSfpt1zwSFjKJMYDJkPS2GbKej3IZ_WO) | Presentation decks — feature pitches, roadmap reviews, stakeholder alignment decks, customer-facing materials |
| Demo Videos | [Drive Folder](https://drive.google.com/drive/folders/1G3KUn4kobNc0CdJOOfA-ib4n6ZAPCFQr) | Product demo recordings — feature walkthroughs, use case demonstrations, customer presentations, internal training videos |
| Customer & Enablement Call Notes | [Drive Folder](https://drive.google.com/drive/folders/1S6jSrpPEGv0e5HLmPwlLX3fAVaJL4Z8J) | Gemini-generated notes from customer discovery calls, support enablement sessions, beta syncs, and internal working sessions — primary source for customer signal, named quotes, feature asks, and VOC evidence |

**When to use Google Drive sources:**
- **New PRD (Full research):** Search the Previous PRD Documents folder for prior art on the same feature area. Check if a similar feature was previously scoped, deferred, or partially built.
- **Customer Signal / Business Case:** **Search the Customer & Enablement Call Notes folder first** when looking for named customer quotes, specific feature requests, pain points, or VOC evidence. These notes are the richest source of first-hand customer signal and should be checked on every Full research pass.
- **Beta/rollout planning:** Reference Beta Documents for current beta requirements, customer setup patterns, and known limitations that may affect rollout strategy.
- **Tone/style matching:** Pull a recent PRD from the folder to calibrate voice, section depth, and formatting conventions.
- **Business case evidence:** Search PM Deck Folder for prior pitches, customer value props, and executive summaries that can inform the Business Case section.
- **Use case examples:** Reference Demo Videos to see how features are positioned and demonstrated to customers — useful for Scenarios and JTBD sections.

## Customer-Facing Documentation

Official Salesforce Help documentation provides the customer perspective on existing features. Use this to understand how features are explained to end users and ensure PRD terminology aligns.

| Documentation | Link | What it covers |
|---|---|---|
| Service Plans Help | [Salesforce Help](https://help.salesforce.com/s/articleView?id=service.sp_intro.htm&type=5) | Customer-facing documentation for Service Plans — setup, configuration, feature descriptions, limitations, prerequisites |

**When to use Help documentation:**
- **Terminology alignment:** Check how features are named and described in customer-facing docs. Use the same terminology in PRDs to maintain consistency.
- **Prerequisites validation:** Reference existing setup instructions to understand what customers must configure before using a feature.
- **Gap identification:** Compare what's already documented vs. what your PRD proposes. Call out net-new capabilities vs. enhancements to existing features.
- **Limitations context:** Check documented limitations and known issues that may be prerequisites or dependencies for your feature.
- **User journey understanding:** See how customers are guided through setup and usage — informs Current User Journeys section.

## Key Beta Implementation Guides (Internal Only)

**⚠️ IMPORTANT:** These are INTERNAL employee-only docs. All implementation guides must be shared with customers in PDF format only.

**Landing Page:** [Service Assistant Dynamic Experience Beta Docs](https://docs.google.com/document/d/14U2OGYFGe4S4GOECMBWgvzSyfAu1snjtMkPA__WfnxQ/edit?tab=t.0)

### Implementation Guides by Channel

| Guide | Doc Link | What it covers |
|---|---|---|
| Adaptive Experience for Case (Closed Beta) | [Doc](https://docs.google.com/document/d/1ptRJz7ckEc-LnLtXZH6-gKK3dDzbdFBo3_lCmqAzeVQ/edit?usp=sharing) | Case channel setup, configuration, dynamic plans for case records |
| Service Assistant for Messaging (Closed Beta) | [Doc](https://docs.google.com/document/d/18o7dnDlgxTwt0eIgQUHW51VDTxDWSQPLtyw4Yiboi3E/edit?usp=sharing) | Messaging channel setup, MIAW integration, messaging-specific features |
| Service Assistant for Voice (Closed Beta) | [Doc](https://docs.google.com/document/d/1z1hrQGfz551bWVu3qe9hfpScii0d2t3uc0wCG7qqk3Y/edit?usp=sharing) | Voice channel setup, Service Cloud Voice integration, voice-specific features |

### Subagent & Knowledge Grounding Resources

| Guide | Doc Link | What it covers |
|---|---|---|
| Subagent Best Practices | [Doc](https://docs.google.com/document/d/16sALqGbEuzmNK6ygye6VFCkWXb1dktUOE3cR6uRLhbU/edit?usp=sharing) | Subagent design patterns, when to use subagents, anti-patterns |
| Subagent Design Implementation Guide | [Doc](https://docs.google.com/document/u/0/d/1RZAEWpd3m2lrP78X0nXgyOi4H-74BwSl81MjBl-Am5s/edit) | Step-by-step subagent implementation, metadata setup, testing |
| ADL Grounding Best Practices | [Doc](https://docs.google.com/document/u/0/d/1y1lu7fphcX93k_Qh4CwUe6-kbXH0kfX5C1ATrwufRBs/edit) | Agentforce Data Layer grounding patterns, data selection, performance optimization |
| Knowledge Article Optimization Best Practices | [Doc](https://docs.google.com/document/d/1dt338oWnfskwmKQcyX0mI5MJfc339F3kHYhyg4Z3ycs/edit?usp=sharing) | How to structure knowledge articles for optimal SRA ingestion and retrieval |
| SRA & Knowledge 101 - Crafting Articles | [Slides](https://docs.google.com/presentation/d/1w4yQCHEXnUyZQREaYte5Vg49bP3IC1x25ldvjPZ9k2w/edit?usp=sharing) | Presentation deck on knowledge article authoring for Service Plans |
| Subagent Generator (Gemini Gem) | [Gem](https://gemini.google.com/gem/1HjREqV7pc9lZk3lgWHzgpkUtkwt7S67Y?usp=sharing) · [Prompt Doc](https://docs.google.com/document/u/0/d/18uR-heWoE7padTff36TmBQ-j2UJHCYsFWfaqTGmNKKw/edit) | Generates subagents according to guidelines and best practices. Upload articles or describe scenarios. |
| Knowledge Article Evaluator (Gemini Gem) | [Gem](https://gemini.google.com/gem/1trRbj1EXq1JjoXvZIBXZlwWnay_ZGpE9?usp=sharing) · [External Prompt](https://docs.google.com/document/d/1DeZhbi-9CK2B4O6w3ySvOzv3C3JdHyya2bh9eBOCAEk/edit?usp=sharing) | Evaluates knowledge articles for Agentforce + SRA optimization. Upload articles for structure evaluation. |

### Pre-GA Release Feature Documentation

| Guide | Doc Link | What it covers |
|---|---|---|
| Multiple Agent Experience (Beta Pre-Release) | [Doc](https://docs.google.com/document/d/1uL0RKkmIINotERVheY_qYd5BOnEvCwtWyGDiX5J3OvQ/edit?usp=sharing) | Multi-agent orchestration, routing logic, agent switching |
| Case Catch-Up & Insights (Beta Pre-Release) | [Doc](https://docs.google.com/document/d/1YzdjcJ_L4ASKwjUeZ0dbEF5mYDF456fV4K7K6BDcfEs/edit?usp=sharing) | Case catch-up summary feature, insights generation, UI integration |

**When to use these beta docs:**
- **PRD research for beta/closed-beta features:** Reference the specific channel guide (Case/Messaging/Voice) to understand current implementation, prerequisites, and limitations
- **Subagent PRDs:** Check Subagent Best Practices and Design Implementation Guide for patterns, anti-patterns, and metadata structure
- **Knowledge grounding PRDs:** Reference ADL Grounding Best Practices and Knowledge Article Optimization guides for grounding patterns and data selection strategies
- **Multi-agent / orchestration PRDs:** Reference Multiple Agent Experience doc for routing logic and agent switching patterns
- **Pre-release feature context:** Check the Pre-GA docs to understand what's in flight and how new PRDs relate to or depend on those features

**⚠️ Access Note:** If you cannot access these docs when needed, note it explicitly in your response: "I cannot access [doc name] ([link]). Manual check required."

## Record Companion Architecture Documents

The Record Companion (A3) is the UI container that powers Adaptive Experience — the framework within which SRA skills (Dynamic Plans, Service Replies, Conversation Catch Up, etc.) render. These documents describe the component architecture, session lifecycle, and rendering contracts.

| Folder | Link | What it covers |
|---|---|---|
| Record Companion Docs | [Drive Folder](https://drive.google.com/drive/folders/13Hgefo1VOzU2iSi4SPFqDwA0tD6HtFRW) | A3 Record Companion architecture — UI container, session lifecycle, skill rendering, component structure, channel-specific behaviors |

**When to use Record Companion docs:**
- When a PRD involves UI rendering behavior (how steps appear, visual differentiation, plan panel layout)
- When a PRD touches session lifecycle (when plans start/end, what triggers re-generation, channel transitions)
- When a PRD involves cross-skill interactions (Dynamic Plans + Service Replies + Conversation Catch Up coexisting in the panel)
- When understanding how Adaptive Experience skills are surfaced to reps across Case, Message, and Voice channels
