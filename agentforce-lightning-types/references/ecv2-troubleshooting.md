# Agentforce CLT — ECv2 Rendering Troubleshooting

Use this when a CLT is built correctly but doesn't render, renders inconsistently, or renders as plain text on Enhanced Chat v2. Work the ladder in order — each step is cheaper than the one after it, and step 0 plus steps 1–3 catch the large majority of real cases.

Canonical Salesforce guidance: [Troubleshoot Custom LWC Rendering Issues in Agentforce](https://help.salesforce.com/s/articleView?id=005385924&type=1) and [Lightning Types Troubleshooting in ECv2](https://help.salesforce.com/s/articleView?id=ai.enhanced_chat_v2_lt_troubleshoot.htm&type=5). Share these with Support before escalating.

---

## Diagnostic ladder

### 0. Republish the ESD before diagnosing anything

Setup → Embedded Service Deployments → the deployment → **Publish**. Do this unconditionally, before reading traces or opening DevTools. It takes seconds and requires no hypothesis.

A confirmed field case: a Service Agent whose action returned real data but replied in plain prose, with every inspectable thing already correct — LightningTypeBundles deployed, `lightning__AgentforceOutput` on every renderer, the published action schema binding `c__<Type>` with `copilotAction:isDisplayable: true`, both registration junctions populated, `clientVersion: WebV2`, and the ESD published a full day *after* the agent version was activated. A republish with no other change made the card render, and ECv2-as-a-Connection was never the problem.

The lesson: a deployment created and published minutes ago can still be in a stale publish state, and comparing ESD and agent timestamps does **not** prove a good publish. Treat "republished" as an action you took during this debugging session, not as a fact you inferred from metadata.

### 1. Environment gate (free, catches most cases)

Run the [pre-flight gate](../SKILL.md#pre-flight-gate--verify-these-before-debugging-anything-else) in the main skill. In particular:

- **Enhanced Chat v2 added as a Connection on the agent.** A confirmed real case had everything else correct — CLT, permsets, action wiring, instructions — and rendered nothing purely because ECv2 wasn't a Connection. Adding it, recommitting and republishing fixed it immediately. Without ECv2, `formatType` degrades to `Text`.
- **ESD republished after the agent was activated.** The most common "it worked yesterday" cause — but see step 0: a republish is also the fix when *nothing* changed.
- **ESD Client Version is WebV2.**

Don't add a Telephony connection alongside ECv2 on a standard Service Agent.

### 2. Did it render? (`formatType` is ground truth)

Inspect the `/sse` stream:

| `formatType` | Meaning |
|---|---|
| `ExperienceType` | The CLT rendered |
| `Text` | Fell back to plain text |
| `Inform` | Expected message type once disambiguation is disabled |

Complementary check: DevTools → Network → filter `messages/stream` → response `result`. `result: []` means InformCommand. Switch the DevTools console context to the Agentforce Messaging **iframe** or your LWC's `console.log` breadcrumbs won't appear.

Session Tracing showing the action fired proves only that the action fired — not that the CLT rendered. It's still worth confirming during development.

### 3. Was the render tool even offered?

Agent Builder → the trace → click the **Reasoning** (LLM) step for the relevant subagent → expand **Available Actions**.

| Observation | Interpretation | Next step |
|---|---|---|
| Render tool (`show_command` / `__show_tool_results__` / `user_select_record`) **not listed** | The planner has no mechanism to render — no instruction change can fix this | Check `is_displayable: True` on the output, that the action came from the Action Library, and planner registration (step 5) |
| Listed, but nothing renders | Downstream rendering-pipeline issue | ECv2 connection, `formatType`, tool naming (step 4) |

This works on Service Agent traces too, even where the preview surface can't paint the card.

### 4. Tool naming (Daisy vs Daisy++)

| Purpose | Daisy v1 | Daisy++ v2 |
|---|---|---|
| Render an output | `show_command` | `__show_tool_results__` |
| Collect input | `user_input` | `__user_input__` |

Don't rename a script that already renders. When troubleshooting, testing the other name is a reasonable lever — but validate on the real ECv2 surface and be ready to revert. Combining an explicit `__show_tool_results__` reference with a blank-caption instruction caused the LLM to echo the tool name into the chat as literal text in one real test.

### 5. Planner function registration (W-22380404)

`GenAiPlannerDefinition` existing only proves the planner exists. The action-to-planner registration lives in a separate junction table.

Find the Planner ID (starts with `16j`) via `/support/qa/planner.jsp`, or `/support/qa/copilot.jsp` → the agent → "Planner Config", or:

```sql
SELECT Id, DeveloperName, PlannerType FROM GenAiPlannerDefinition
WHERE PlannerType = 'Atlas__ConcurrentMultiAgentOrchestration'
```

Then check the junction:

```sql
SELECT Id, PlannerId, Plugin FROM GenAiPlannerFunctionDef WHERE PlannerId = '16jxxx...'
```

- **Rows returned** → registration is healthy. Look elsewhere (tool naming, `is_displayable`, rendering pipeline).
- **Empty** → this is the W-22380404 registration gap. Symptom profile: CLTs rendered on an older agent version and stopped after creating a new version and activating.

Pre-fix workaround via Workbench (Tooling API):

```
POST /services/data/v66.0/tooling/sobjects/GenAiPlannerFunctionDef
{ "PlannerId": "16jxxx...", "Plugin": "179xxx..." }

POST /services/data/v66.0/tooling/sobjects/GenAiPluginFunctionDef
{ "Function": "172xxx...", "PluginId": "179xxx..." }
```

A `DUPLICATE_VALUE` response means the platform fix is already deployed to your pod. Fixed in 260.14.5 / 262.4.x.

### 6. Planner schema fallback / type collapse

If the planner logs:

```
WARN Caught exception when trying to read primitive type from bundle so using default object
```

the CLT output type has collapsed to a generic object and the `show_command` hint is stripped, so the agent falls back to text. This is a distinct bug from the registration gap above.

---

## Daisy++ (Unified Planner) parameters

Daisy++ unified the React, Flash and Daisy reasoners into one engine and reached all NGA agents by **April 24, 2026**. Its initial rollout regressed CLT rendering (the planner wasn't issuing `show_command`); it was re-deployed **May 1, 2026** with fixes.

| Parameter | Effect | Status |
|---|---|---|
| `additional_parameter__disable_graph_runtime: True` | Reverts to the old Daisy planner (`False`/absent = Daisy++) | **Legacy — remove it.** Product advises removing the workaround on 262.4.x+. Some pods were still affected at 262.4.4, so verify before removing |
| `additional_parameter__disable_disambiguate_form: True` | Stops the OOTB `user_select` disambiguation form replacing your CLT | Use when you see that symptom |
| `additional_parameter__enable_graph_runtime: True` | Forced Daisy++ early | **Don't use.** This, or renaming the agent while switching planners, can corrupt agent metadata/versioning — the only fix is a brand-new agent |

To confirm whether a session used Daisy++, search Splunk for `atlas_v2`.

---

## Known platform bugs

| Work item | Issue | Status / workaround |
|---|---|---|
| [W-21533738](https://gus.lightning.force.com/lightning/r/a07EE00002W4JloYAF/view) | LDS-backed `@wire` adapters don't initialise in the ECv2 iframe under Credential-Based User Verification (`ldsWebruntimeOneStoreInit`) | Open. Use imperative `@AuraEnabled` Apex instead — Apex-backed wires work |
| W-22250928 | Input CLT UI doesn't render on AgentScript + ECv2; input form fields appear as plain text on Service Agents | Open. See the Input CLT workarounds in the main skill |
| W-21683108 | Input CLT (`lightning__AgentforceInput`) broken in NGA Agent Script + ECv2 | Related to the above |
| W-22380404 | CLT Lightning Type registration fails on agent publish | Fixed in 260.14.5 / 262.4.x; Tooling API workaround above |
| W-22387068 | Additional CLT rendering regression flagged May 2026 | — |
| W-22378461, W-22369498 | CLT bundling bugs for Service Agents | — |
| W-22188555 | Wire adapter investigation (Qt engagement) | — |

---

## Authenticated-context runbook (Credential-Based User Verification)

Symptom: the LWC renders but Apex calls fail, or `UserInfo.getUserId()` returns the Guest/Agent User when you expect the logged-in portal user.

1. Enable **Credential-Based User Verification** on the messaging channel.
2. Grant the authenticated user's Profile/Permission Set access to: the action's Apex class, **every Apex class the LWC calls client-side**, the Custom Lightning Type, FLS on required fields, and object CRUD.
3. **Update Member Provisioning on the ESD's generated LWR Chat Site** (Experience Builder → the chat site → Workspace Settings → Member Provisioning) with the same Profiles and Permission Sets as the parent portal site. Skipping this leaves the chat in Guest User context even with verification enabled, because ECv2 iframes the ESW LWR site and resolves the session by cookie on a shared domain — the ESW site must have the profile registered as a member.
4. Publish the ESD.
5. **Log out and log back in.** A page refresh does not pick up the new context. Hard-refresh, or verify in an incognito window.

Notes:

- ESW chat site membership is **not exposed via the Metadata API** — a manual Setup step per org. Put it in the runbook; it won't travel with a deployment.
- **Never** grant the Guest User profile access to Apex classes, sensitive objects or APIs as a workaround. That publishes an unauthenticated internet endpoint. Fix the membership instead.
- Unauthenticated deployments run as the internal Agent User: grant that profile the CLT, the action class, FLS and CRUD, and don't expect `UserInfo.getUserId()` to be contact-linked.

---

## Escalating

Before filing, have: the `formatType` value from `/sse`, a screenshot of the trace's Available Actions at the reasoning step, the `GenAiPlannerFunctionDef` query result, the agent type (ASA vs AEA) and license, the surface tested (Builder preview vs Test Enhanced Chat vs portal), and confirmation that the agent was activated and the ESD republished. Cite the relevant W- number above when the symptom matches a known bug.
