---
stage: draft
release: 264
feature: real-time-context-refresh
team: service-rep-assistant
personas: [service-rep, supervisor]
epic: null
hld: null
---

# Requirements One Pager: Real-Time Context Refresh for AI-Powered Service Plans

# The Problem

When customer service reps are working a case and new information arrives (a customer reply, a system field update, or a case comment from another team member), the AI-generated service plan doesn't update automatically. Reps must **manually refresh** or **regenerate the entire plan** to incorporate the new context. This creates a disconnected experience where the plan falls out of sync with reality, leading to reps following outdated guidance, missing critical new information, and wasting time on unnecessary manual refresh cycles. In high-velocity contact centers where cases evolve rapidly, this gap erodes trust in AI guidance and forces reps to swivel between the plan UI and the case timeline to verify they have the latest context.

# Customer Signal

## Enterprise Retailer (500+ Service Reps)

This customer operates a fast-paced returns and refunds contact center where **customers frequently reply while reps are still working the case**. Today, when a customer sends a clarifying message (e.g., "I have the order number now: #12345"), the AI plan doesn't update — the rep must manually regenerate, which takes 6-8 seconds and often loses their place in the current step. During holiday peak, their reps handle **30+ chats simultaneously**, and manual refresh cycles create handle time bloat.

**What they need:** Plans that automatically refresh when new customer messages arrive on active cases, surfacing the new information inline without requiring rep action or disrupting their current step.

## Financial Services Firm (1,200+ Service Reps, Complex Case Workflows)

This customer's compliance-heavy workflows involve **multiple internal stakeholders updating case fields** (e.g., fraud review status, account verification flags). When a fraud analyst updates the `Fraud_Status__c` field from "Pending" to "Cleared", the AI plan still shows steps for escalating to fraud review — the rep must notice the field change, manually refresh the plan, and only then see the updated guidance. This creates **compliance risk** (reps following outdated steps) and **inefficiency** (average 3-4 manual refreshes per case).

**What they need:** Plans that detect when case fields configured for grounding are updated by other users or automation, and automatically refresh the relevant steps to reflect the new state.

## Telecommunications Provider (800+ Service Reps, Case Comment Collaboration)

This customer's technical support teams rely on **internal case comments** for escalations. When a Tier 2 engineer adds a comment with troubleshooting results (e.g., "Port test passed, issue is client-side router config"), the Tier 1 rep's AI plan doesn't surface this information — they must scroll through the case feed, find the comment, and **manually regenerate the plan** to get updated guidance. This adds **2-3 minutes per escalation** and frustrates reps who expect AI to "just know" what the engineer said.

**What they need:** Plans that monitor case comments and automatically refresh when new comments from internal users provide context relevant to the current service plan topic.

---

# Why This Matters

**1. Real-time responsiveness is table stakes for AI-powered guidance.** If the plan doesn't update when new information arrives, reps view it as "stale AI" and revert to manual workflows. Competitors (Cresta, Sierra) emphasize real-time plan adaptation as a core capability — without this, we lose credibility in high-velocity contact centers.

**2. Manual refresh cycles waste rep time and break flow.** Every manual regeneration takes 6-8 seconds, disrupts the rep's current step, and risks losing uncommitted work. In a 15-minute case with 3 new customer messages, that's ~25 seconds of dead time and 3 context switches — compounded across 500 reps, that's measurable productivity loss.

**3. Stale plans create compliance and quality risk.** When plans show outdated guidance (e.g., "escalate to fraud" after fraud clearance), reps may follow incorrect steps, violate SLAs, or create audit issues. Real-time refresh ensures plans always reflect the current state, reducing error rates.

# The Gap (Current vs. Target)

## Today

1. Rep opens a case and generates an AI service plan based on the initial case state (description, fields, prior history).
2. Plan renders with steps grounded in the case data snapshot from step 1.
3. While the rep works the plan, **new information arrives**: customer sends a message, another user updates a field, or an internal comment is added.
4. The plan **does not update** — it continues to show steps based on the stale snapshot from step 1.
5. Rep notices the new information (or doesn't), **manually regenerates** the entire plan, waits 6-8 seconds, and loses their place.
6. The new plan reflects the latest context, but the manual refresh cycle repeats whenever new information arrives.

## Target

1. Rep opens a case and generates an AI service plan based on the initial case state.
2. Plan renders with steps grounded in the case data snapshot from step 1.
3. While the rep works the plan, **new information arrives**: customer sends a message, another user updates a field, or an internal comment is added.
4. The system **detects the new information** and evaluates whether it's relevant to the current plan topic (using the same relevance logic as initial generation).
5. If relevant, the plan **automatically refreshes** the affected steps inline — new steps may be added, existing steps may be updated or removed, and the rep sees a subtle indicator (e.g., "Updated based on customer reply").
6. The rep continues working the plan with the latest context, **without manual refresh** — the plan stays synchronized with case reality in real time.

---

# Who Benefits

| Persona | Pain Today | Desired Outcome |
|---------|------------|-----------------|
| Customer Service Rep | Must manually refresh plans when new information arrives; wastes 6-8 seconds per refresh; risks following outdated guidance | Plans update automatically when customers reply, fields change, or comments arrive — guidance always reflects current case state |
| Admin / Builder | No control over which events trigger plan refresh; all-or-nothing manual refresh behavior | Configure which case events (customer messages, field updates, comments) should trigger automatic plan refresh per topic |
| Quality / Compliance Lead | Reps follow stale plan steps that don't reflect latest case state (e.g., escalating to fraud after fraud clearance) | Real-time plan refresh ensures reps always follow current guidance, reducing compliance risk and error rates |
| Customer | Experiences delays while rep manually refreshes plan or follows outdated steps that don't account for new information customer just provided | Reps respond faster with guidance that already incorporates the customer's latest message — smoother, more accurate resolutions |

---

# Jobs to be Done

* As a **Customer Service Rep** resolving a customer issue across multiple interactions, I need the AI service plan to automatically refresh when new customer messages, field updates, or case comments arrive, so that I always have the most current guidance without wasting time on manual refresh cycles or risking following outdated steps.

* As an **Admin / Builder** configuring AI service plan topics, I need to specify which case events (customer messages, field updates, comments) should trigger automatic plan refresh for each topic, so that plans update intelligently based on what's relevant to the topic's scope rather than refreshing on every minor change.

* As a **Quality / Compliance Lead** auditing service interactions, I need assurance that AI plans always reflect the current case state (not stale snapshots), so that reps follow accurate guidance and compliance risks from outdated steps are eliminated.

* As a **Customer** interacting with a service rep, I need the rep to have guidance that already accounts for the new information I just provided (e.g., order number, clarification, updated details), so that I don't have to repeat myself or wait while the rep "updates their system."

---

# Scope

**In Scope**
* **Automatic plan refresh triggers** — detect when configured case events occur (customer message, field update, case comment) and evaluate relevance to current plan topic
* **Inline step updates** — refresh affected steps without full plan regeneration; add new steps, update existing steps, or remove steps as needed
* **Admin configuration** — per-topic settings to specify which event types trigger refresh (customer messages: yes, field updates: specific fields, comments: internal only)
* **Rep notification** — subtle UI indicator when plan refreshes (e.g., "Updated based on customer reply" badge on affected steps)
* **Relevance evaluation** — use same topic classification logic as initial generation to determine if new information is relevant to current plan topic

**Out of Scope**
* **Cross-topic plan switching** — if new information changes the topic (e.g., billing question becomes technical issue), still requires manual topic change (future: auto-topic switching)
* **Plan version history** — no UI for reviewing prior plan versions before refresh (future: plan timeline / audit log)
* **Refresh for external integrations** — only detects events within Salesforce platform (case object); external system updates require Salesforce field updates to trigger refresh
* **Throttling edge cases** — if 10+ events fire in rapid succession (e.g., bulk field update), current behavior refreshes once with latest state; future: smarter batching logic
* **Voice channel real-time refresh** — initial release targets Case and Messaging channels; Voice refresh requires transcript segment streaming architecture (separate PRD)

---

# Success Metrics

| Metric | Current State | Target |
|--------|---------------|--------|
| **Manual plan refresh rate** | 3.2 refreshes per case on average (Enterprise Retailer, high-velocity) | < 0.5 refreshes per case (80%+ cases self-refresh automatically) |
| **Handle time reduction (refresh wait)** | ~20-25 seconds per case wasted on manual refresh cycles (3 refreshes × 6-8s each) | < 5 seconds per case (only edge cases require manual refresh) |
| **Plan staleness incidents** | High — qualitative feedback from 3 beta customers (reps following outdated steps due to missed refreshes) | Near zero — plan always reflects current case state within 2 seconds of event |
| **Rep satisfaction with plan accuracy** | TBD — measure baseline via survey ("Does the plan reflect the latest information?" 1-5 scale) | > 4.2 / 5.0 ("Plan almost always has the latest context") |
| **Admin adoption of refresh config** | 0% (feature doesn't exist) | > 70% of topics configure at least one auto-refresh trigger within 30 days of GA |

---

# Open Questions

| Question | Notes |
|----------|-------|
| Should refresh happen on **every** customer message, or only when the message changes the topic/intent? | Lean toward every message for simplicity; topic relevance check prevents unnecessary regeneration. Validate latency with 100+ message/hour test cases. |
| What's the right UI indicator for "plan just refreshed"? | Options: (1) badge on affected steps, (2) toast notification, (3) subtle highlight animation. UX to prototype and test with beta customers. Avoid intrusive notifications that break rep flow. |
| How do we handle refresh during **active step execution** (rep is mid-action)? | Proposal: queue refresh until current step completes; don't interrupt in-progress actions. Edge case: what if current step becomes irrelevant due to new info? Flag for UX review. |
| Should internal comments from **all users** trigger refresh, or only specific roles (e.g., Tier 2 engineers)? | Start with all internal users; admins can configure comment author filters per topic if needed. Validate with Telecom customer (their use case). |
| What happens if auto-refresh **fails** (API timeout, service degradation)? | Fallback: show stale plan + banner "Plan refresh failed — click to retry manually." Log failure for monitoring. Engineering to define retry logic and circuit breaker thresholds. |

---

# Customer References

* **Enterprise Retailer** — 500+ reps, high-velocity returns/refunds contact center, handles 30+ chats simultaneously during peak, needs real-time refresh for customer messages
* **Financial Services Firm** — 1,200+ reps, compliance-heavy workflows, multiple internal stakeholders updating case fields, needs refresh for field updates to avoid compliance risk
* **Telecommunications Provider** — 800+ reps, Tier 1/Tier 2 collaboration via case comments, needs refresh for internal comments to surface escalation results

---

**Note:** This is a **sanitized example** created for the `sf-prd-writer` skill documentation. Customer names are generalized. Real PRDs written by the skill include:
- Specific customer names (when appropriate for internal sharing)
- Slack message links as inline citations
- Competitive intelligence references (where relevant)
- GUS epic links and dependencies (after alignment)
