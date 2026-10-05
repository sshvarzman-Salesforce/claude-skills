# Source decisions and version-sensitive features

Read this before using a model identifier, feature flag, routing setting, or voice control from the source guide.

## Primary source

[Voice Agent Best Practices Guide: Latency Optimization and Personality Design](https://docs.google.com/document/d/1rhwqSTqCru1rtpLWr2Sm1_a3E-z9yA0gBe9ZXe6Ulk8/edit?tab=t.0), read October 2, 2026. The document body calls itself *Voice Agent Optimization Guide*. Its update-date field is empty; its September release reference has no year. The complete tab text was reviewed, including the system appendix, casual-persona sample, and Chit Chat workaround. Embedded screenshots and linked audio recordings were not evaluated; do not reconstruct configuration missing from text or claim an audio comparison was performed.

This skill is a synthesis, not a verbatim export. Keep the source's two priorities: reduce delay across the call pipeline and make spoken responses natural. The evaluation rubric, failure scenarios, action contracts, and implementation safeguards are additions to make those priorities testable.

## Decisions that prevent conflicting instructions

| Source section or claim | Treatment in this skill |
| --- | --- |
| 1.1 direct routing is gated and coming in September | Check the actual org and channel. Minimize hops only after preserving required connection context, identity, and escalation. No release promise. |
| 1.2 Hyperclassifier router | Candidate for fast classification; confirm template, model availability, and routing accuracy. Keep business actions in the selected subagent. |
| 1.3 token streaming | Verify voice-channel support end to end. Text/API streaming does not prove earlier audible speech. |
| 1.3 dynamic indicator; static message blank | Guide-specific configuration to verify in the current builder. Test the audible result before prescribing the toggle. |
| 1.3 beep-boop default of six seconds | Historical guide claim, not a universal setting. Do not invent missing configuration. Current public descriptions need careful reconciliation; see below. |
| 1.4 GPT 4.1 preferred; avoid Gemini | Historical recommendation. Compare currently available models on representative task accuracy, call latency, and tool reliability. No provider ban. |
| 1.4 same prompt/subagent model removes extra reasoning | Treat as a hypothesis for a controlled experiment; confirm with traces rather than promising a fixed saving. |
| 1.4 cache FAQs; move DML async | Use freshness and access boundaries for caching; defer only writes that the current spoken answer does not depend on. |
| 2.1 always contract | Prefer natural contractions; preserve clarity, accessibility, quoted wording, and required disclosures. |
| 2.2 exactly one changing tag vs sustained emotion | At most one tested tag in the default service persona. Choose mood appropriately; repeated reassurance is better than forced variation during distress. |
| 2.3 fixed event capabilities, name, Amy Sweet voice | Event-demo examples only. Use the actual business capabilities, verified name variable, and an available voice. Never advertise an unsupported action. |
| 2.4 no first-person emotion vs casual appendix emotion claims | Default service persona avoids claims of personal feelings. The casual appendix is an alternate style experiment, not an additional instruction layer. |
| 2.6 narrate lookups every turn | Narrate a real lookup sparingly. Do not pretend a lookup occurred or add a hedge to every known fact. |
| 2.7 omit timezones and years | Use natural spoken dates, but include timezone/year when necessary to remove ambiguity. |
| 2.8 80% human-likeness hard gate | Replace an undefined self-score with a listener rubric and explicit acceptance criteria. Never report a measured score without evaluation. |
| 2.9 no AI disclosure vs welcome saying AI agent and persona saying human | Be transparent about being an AI assistant; follow the deployment's disclosure wording and never claim to be human. |
| Appendix Markdown default | Developer-facing artifacts may use Markdown. Caller-facing speech should be plain spoken language. |
| Appendix event-topic prohibitions | Carry over business scope; do not universally block identity-related or accessibility questions that are legitimate service requests. |
| Appendix specific instructions override global rules | Local style exceptions cannot override grounding, identity, access, or truthful action status. |

## Configuration fragments from the guide

These are provenance records, **not deployable examples**. Verify syntax, placement, entitlement, and runtime support against the current org before use.

```text
model_config:
    model: "model://sfdc_ai__DefaultEinsteinHyperClassifier"

additional_parameter__disabled_topics: "Chit_Chat"
```

The guide's replacement Chit Chat subagent routes non-small-talk requests to an event-specific `Voice_FAQ_Search_HE`. Do not copy that name or catch-all rule into another business. Inspect confusion cases; distinguish greetings, greetings plus service requests, genuine small talk, out-of-scope requests, and ambiguous intents. Verify a supported way to modify the standard topic before disabling it.

## Public documentation checked October 2, 2026

- [Salesforce: model configuration](https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-model.html). Multiple models are supported. The documented HyperClassifier restrictions include no before/after-reasoning hooks and only the transition tool. Verify model choices at use time.
- [Salesforce: Agent Script blocks](https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html). Voice controls include fillers and turn-taking. The page describes `beepboop_config.max_wait_time_ms` in terms of inbound automated-tone analysis, unlike the guide's waiting-audio description. Resolve the discrepancy using current schema and observed runtime behavior before changing it.
- [Salesforce: Voice best practices](https://help.salesforce.com/s/articleView?id=ai.agentforce_voice_best_practices.htm&language=en_US&type=5). Check telephony/context requirements, transcription, and actual voice behavior for the deployment.
- [Salesforce: latency troubleshooting](https://help.salesforce.com/s/articleView?id=005391243&language=en_US&type=1). Voice includes additional channel stages; streaming availability differs by channel. Its caveat about voice conflicts with the supplied guide's blanket streaming advice, so verify the specific implementation.
- [ElevenLabs: audio tags](https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-do-audio-tags-work-with-eleven-v3-and-v4). Provider-level tag support does not establish support in every Salesforce integration or for every voice/tag combination.

Prefer observed org capabilities plus current vendor documentation for implementation details. If unavailable, provide a clearly marked design proposal and a short verification list; continue independent prompt and test work. Do not silently invent CLI flags, metadata elements, model IDs, setup paths, or guaranteed timing improvements.
