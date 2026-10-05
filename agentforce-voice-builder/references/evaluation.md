# Evaluate behavior, latency, and voice quality

Use for regression tests, reviews, benchmarks, and release decisions. This is a proposed rubric and test method, not a Salesforce product requirement or an executed evaluation.

## Run the right test for the claim

Use the portable cases in [../assets/call-tests.csv](../assets/call-tests.csv), adapted to actual capabilities. Each case has a fixture, caller utterance, semantic route, expected behavior, failure condition, and test layer. A fixture supplies synthetic facts; the agent must not manufacture facts beyond it. Run with fresh sessions unless the case specifies a sequence.

- **Text and tool simulation:** Wording, routing, grounding, refusal to invent outputs, missing input, and action status. Does not measure audio.
- **Action integration:** Permission boundaries, real output schema, idempotency, freshness, and failures in an authorized test environment.
- **Real voice calls:** Pronunciation, listening, endpointing, barge-in, mood, dead air, tag rendering, transfer, and call timing.

Include successful tasks, negative cases, caller corrections, unsupported requests, accents/noise where relevant, and peak-load scenarios within authorized capacity. Repeat representative cases to expose variation. Keep held-out cases separate from prompt-tuning examples.

## Hard failures

Any fabricated task-critical fact, unauthorized action/disclosure, identity substitution, false completion or transfer claim, duplicated non-idempotent side effect, or ignored explicit human-escalation request blocks a release recommendation for the affected capability. Escalation unavailability must be handled honestly with the configured fallback. Good style scores cannot cancel these failures.

## Quality rubric

Rate each dimension 1–5 with an observed example: 1 = frequent failure; 3 = usable with notable friction; 5 = consistently clear and appropriate. For non-applicable dimensions, state why; do not silently count them as passing.

| Dimension | Observable evidence |
| --- | --- |
| Task completion | Correct result or useful honest fallback, with necessary confirmations. |
| Grounding and precision | Facts and action status match authoritative outputs; dates, units, and identity remain correct. |
| Concision and turn design | Understandable turns, answer first, no unnecessary capability lists or repeated offers. |
| Tone and empathy | Warmth suited to the caller; no forced cheer or invented personal feelings. |
| Audible intelligibility | Names/numbers understood, usable pace, tags not spoken literally, no overlapping progress speech. |
| Recovery and handoff | Handles clarification, correction, interruption, failure, and escalation without loops. |

A reasonable **proposed** quality goal is an average of at least 4/5 with no dimension below 3 and no hard failure. Agree on thresholds for the deployment; do not call this “80% human likeness.” Require actual listeners/audio evidence for audible scores. Automated graders should cite observable evidence and be calibrated against human review.

## Performance and outcome scorecard

Record agent/model/version, dates, sample counts, scenario mix, cache/load conditions, and measurement layer. Report p50/p95 connection and turn latency, action timing, answer-completion time, and interruption recovery when available. Separate failures/timeouts and missing telemetry from successful timings.

Track task success, routing accuracy/confusion, grounded-answer rate, duplicate-action rate, transfer success, abandonment, and caller feedback where observable. Do not optimize containment by resisting valid escalation. A faster result that is wrong fails acceptance.

For an A/B comparison, hold scenarios, integration behavior, and load constant; change one relevant factor where practical. Include difficult cases and report the quality/latency tradeoff. An anecdote or transcript-only review is not proof of p95 improvement.

## Results record

For each case: `case ID | agent version | execution layer | actual route/actions | actual output or audio reference | pass/fail/not run | evidence | issue and proposed fix`.

Conclude with changes that passed, failures remaining, checks not run, and the next evidence needed. Do not label an agent production-ready from a prompt review or a structurally valid skill package alone.
