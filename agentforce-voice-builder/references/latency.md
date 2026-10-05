# Diagnose and improve call latency

Use for slow connection, dead air, slow routing, retrieval, or action execution. Derived primarily from source guide Part 1; measurement discipline and failure boundaries below are engineering additions.

## Establish the measured problem

Get representative successful, slow, and failed calls. Record agent version, model, telephony path, locale, test scenario, concurrency, and cache state. Correlate timestamps without copying customer secrets into reports.

| Metric | Start → end | Interpretation |
| --- | --- | --- |
| Connection latency | call initiation → first audible greeting | Includes telephony, routing, connection flow, and greeting generation. |
| Turn-response latency | caller's last audible speech → first relevant audible reply | Includes endpointing, transcription, reasoning, actions, and speech delivery. |
| Acknowledgment latency | caller stops → first useful acknowledgment | Keep separate from substantive answer; a filler is not task completion. |
| Action latency | action invocation → usable result | Split integration/network, Apex/Flow, and downstream work if traced. |
| Answer-completion latency | caller stops → answer finishes | Detect long speeches that hide behind a quick first token. |
| Interruption recovery | caller interruption → agent stops and responds to revised intent | Needs audio/channel evidence, not just a text transcript. |

Report sample counts, p50 and p95 for comparable scenarios, and failures separately. Do not compute exact stage attribution from missing spans or add overlapping spans as if sequential. Prefer client/audio timing for audible metrics; server token timestamps are proxies. Set proposed targets with the owner based on the call type and baseline; no universal Salesforce SLA is asserted here.

## Follow the critical path

1. **Connect and inbound Omni-Channel Flow.** Inventory handoffs and pre-greeting work. Keep required identity, routing context, and escalation data. Remove unused branches; defer nonessential enrichment. Reduce repeated reads/writes and use selective queries. Evaluate direct routing only when its supported context contract meets the use case.
2. **Endpointing and transcription.** Measure the delay after speech ends. If tuning is supported, balance responsiveness against cutting off hesitant callers, names, and numbers. Test noise and corrections. Fix demonstrated domain-term recognition errors; avoid indiscriminate keyword boosting.
3. **Topic/subagent classification.** Keep routing focused on intent selection. Remove business I/O from the router. Test a supported fast classifier against intent confusion, especially a greeting preceding a real request. Retain permitted transition operations. Consult source-notes before applying HyperClassifier settings.
4. **Reasoning and model calls.** Remove irrelevant repeated instructions, redundant model round trips, and oversized action responses. Compare eligible models with the same cases. Test model alignment between prompt and subagent only when traces support that hypothesis. Retain accuracy and required permission checks.
5. **Retrieval.** Index fields needed to answer the question; filter by product/event, locale, current publication state, and user access where applicable. Limit irrelevant chunks, preserve provenance, and distinguish no results from retrieval failure. Benchmark cold and warm retrieval independently.
6. **Apex, Flow, and integrations.** Simplify wrappers; fetch only required fields; avoid redundant sequential calls. Parallelize only independent work supported by the implementation. Keep authorization, side-effect ordering, governor limits, timeouts, and error handling intact.
7. **Speech delivery and perceived waiting.** Verify end-to-end token/audio streaming rather than assuming it. Use one short, truthful acknowledgment or a supported progress indicator for real work. Avoid repeated fillers, overlapping speech, and claims of success before results. Tune any waiting sound using the current documented setting and listening evidence; do not assume beep-boop semantics.

## Cache and asynchronous work

For FAQ caching, specify key scope (including tenant, locale, content version and access where needed), freshness/TTL, invalidation, miss/eviction fallback, and observable hit rate. Do not reuse personalized data across users or serve stale transactional availability from a generic FAQ cache. Conversation variables can retain verified results only while they remain valid.

Defer analytics or noncritical bookkeeping when the response does not depend on the write. If an appointment or order change is queued, say it is pending; completion requires durable confirmation. Use supported job/status handling and reconciliation. A timeout after a write may mean the write succeeded: check status or use a verified idempotency mechanism before retrying.

## Return a prioritized recommendation

Use `observation → evidence → likely cause → smallest change → expected metric → accuracy/context risk → verification` for each finding. Label hypotheses. Lead with the biggest measured critical-path delay, not the easiest setting to change. Compare before and after with the same workload and report regressions as well as improvements. If no traces are available, produce an instrumentation plan and provisional changes without fabricated timings.
