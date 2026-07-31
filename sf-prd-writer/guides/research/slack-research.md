# Slack Research

Search Slack to ground the PRD in real evidence. Use the [SRA Channel Registry](../reference/sra-channels.md) as primary sources, then broaden with keyword searches.

**Reference materials:**
- [SRA Channel Registry](../reference/sra-channels.md) — curated list of SRA + customer channels and what each covers
- [Drive Folders](../reference/drive-folders.md) — Google Drive sources for PRDs, customer call notes, beta docs, demo videos
- [Research strategy by channel type](../reference/sra-channels.md#research-strategy-by-channel-type) — which channels to check for which research need

## Search execution

Run multiple searches in parallel:

* **Internal Competition Check**: Search for other Agentforce teams building similar/overlapping features
  * Search for PRDs, roadmaps, or feature announcements from adjacent teams
  * Look for initiatives that might compete or overlap with this feature
  * Check Einstein AI, Platform, Industries, and other Service Cloud teams
  * Flag any potential duplication or collaboration opportunities
* Search for the feature name or core concept in engineering and product channels
* Search for customer mentions, EA feedback, or beta signals related to the feature
* Search for related bugs, GUS work items, or known issues that are prerequisites or blockers
* Search for prior PRDs, HLDs, or design docs on the same product area
* Search for engineering confirmation quotes that validate the problem or architecture decisions

Use `slack_search_public_and_private` for comprehensive searches, and `slack_read_thread` to get full context from relevant discussions.

If Slack search returns strong results, include specific quotes, message links, and named sources in the Business Case and Architecture sections — just as a PM would when writing evidence-based PRDs.

**If other teams are building competitive features**, create a dedicated section in the PRD highlighting:
- What team is building what
- Degree of overlap
- Potential collaboration or consolidation opportunities
- Recommendation on whether to proceed, collaborate, or defer

If search returns no relevant results, proceed with the user's input and note where field evidence is still needed.

## Graceful degradation — when tools fail

* **Slack tools return errors / rate-limited / unavailable:** Note the failure, proceed with user-provided context, and add a flag at the end of the PRD: `⚠️ Evidence gathering incomplete — Slack research could not run. Re-invoke /sf-prd-writer to retry research and backfill evidence.`
* **Canvas read fails (portfolio cross-reference):** Skip that canvas, note which PRDs could not be cross-referenced, and proceed. Do not block the entire PRD on one unreadable canvas.
* **All Slack tools fail:** Treat it as a "thin input" scenario — make reasonable inferences, flag assumptions prominently, and deliver the PRD with clear `[NEEDS EVIDENCE]` markers in the Business Case and Customer Signal sections.
* Never silently drop research. Always tell the user what could not be gathered and why.
