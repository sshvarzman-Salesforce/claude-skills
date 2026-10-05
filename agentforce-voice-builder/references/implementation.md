# Turn a voice design into a working Agentforce implementation

Use when asked to build or change an agent, action, Flow, Apex implementation, or routing configuration. This is an implementation workflow added to the source guide; it is not a Salesforce schema reference.

## Establish the actual environment

Inspect the provided project and connected org through available, authorized tools. Record the agent/version, builder or Agent Script generation, target org and environment, API/runtime version when available, telephony connection, voice provider/model, identity source, locale, escalation path, and permissions. Reuse existing project structure. If only a description is available, create a design artifact with assumptions rather than fabricated deployable metadata.

For each version-sensitive capability, record `requested behavior | observed support | evidence | configuration location | fallback`. Use source-notes.md for features that need extra verification. Discover installed CLI help and current metadata/schema before generating exact commands or elements. Keep real names from the project; label new suggested names as proposals. Do not make the skill depend on a particular Salesforce MCP server, extension, or other locally installed skill.

## Define intent and action boundaries

Create a small set of distinct subagents/topics with positive examples, exclusions, and ambiguous examples. A greeting attached to a service request should route on the request. Avoid a catch-all FAQ subagent swallowing transactional, escalation, or unsupported intents.

For each action, specify:

| Contract element | Required design decision |
| --- | --- |
| Purpose and invocation | Which intent needs it, and when an answer must wait for it. |
| Inputs | Required/optional fields, source of each, validation, missing/ambiguous-input behavior. |
| Identity and access | Trusted identity source, sharing/record/field enforcement, allowed operation. Caller statements alone cannot replace authenticated identity. |
| Outputs | Minimal grounded facts, status, safe error category, and freshness where relevant. |
| Side effects | Read vs write, confirmation requirements, retry/idempotency behavior, duplicate prevention. |
| Failure modes | Empty result, denied access, timeout, partial completion, uncertain outcome, and handoff. |
| Timing | Measured or proposed budget, progress behavior, and whether any work can safely run asynchronously. |

Authentication and authorization belong in enforceable platform/action controls as well as conversational instructions. Account for the actual execution context of Apex and Flow, including record sharing and field/object access. Use supported credentials mechanisms; keep tokens out of prompts, source files, and trace exports.

## Implement within the requested scope

Build or edit the smallest coherent set of instructions, routing definitions, variables, action contracts, Flow/Apex, and permission changes the request needs. Do not replace a working agent with a generic starter. Use assets/voice-instructions-template.md as authoring material: substitute verified details, resolve optional branches, and remove authoring notes before runtime use.

Where deterministic checks are available, use them for identity, required inputs, allowed transitions, and side-effect prerequisites. Keep conversational instructions focused on reasoning, grounding, and speech. Represent action outcomes accurately: proposed, pending, completed, failed, or unknown. Do not turn backend failures into unsupported promises.

Implement a usable handoff: trigger, supported destination, concise context summary, caller expectation, and fallback if unavailable. Pass only necessary permitted context. A request for a human should not start an endless qualification loop. Do not claim a transfer succeeded until the channel confirms it.

## Verify in layers

1. Validate supported syntax and references using installed project tooling.
2. Exercise action success, missing input, access denial, timeout, duplicate retry, and partial/unknown outcomes with appropriate focused tests.
3. Test intent routing and instruction behavior with representative utterances and actual tool outputs.
4. Make authorized test calls through the real voice channel for audio and telephony behavior. Text simulations are insufficient for latency, tags, interruptions, and transfer quality.

Use the test format supported by the installed testing tools; assets/call-tests.csv is a portable scenario catalog, not a promised native Testing Center import format. Map its semantic intents and actions to the real agent before running it.

Prepare an explicit diff, relevant verification results, and rollback/version details. Deployment, activation, phone-number reassignment, paid calls, or production data changes require authorization covering the target and effect; honor authorization already given and do not ask again needlessly. If the request is design-only, finish the design without inventing a deployment step. Stop retries when a write outcome is uncertain until status is reconciled.
