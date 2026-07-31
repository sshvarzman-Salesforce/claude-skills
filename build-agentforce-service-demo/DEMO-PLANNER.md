---
name: demo-planner
description: >
  Questionnaire-driven demo planning skill. Asks the SE what kind of Agentforce
  Service Assistant demo they need (industry, channel, use case, complexity, CLTs,
  knowledge, HiL gates) and generates a filled SUBAGENT-TEMPLATE spec ready for
  the build-agentforce-service-demo skill to execute.
tools: [Read, Write, Edit]
---

# Demo Planner — Questionnaire-Driven Spec Generator

> "What kind of demo do you need?" → answers → filled SUBAGENT-TEMPLATE.md

Sits **upstream** of the `build-agentforce-service-demo` skill. This skill asks structured questions, validates the SE's choices against known patterns, and scaffolds a complete demo spec. The builder skill then executes it.

**Companion docs:**
- `SUBAGENT-TEMPLATE.md` — the template this skill fills
- `BEST-PRACTICES.md` — constraints applied during generation
- `CLT-GUIDE.md` — referenced when CLTs are selected

---

## When to Use

- SE says "I need a new demo" / "build me a demo" / "plan a demo"
- SE asks "what should my demo look like for [industry/customer]?"
- SE wants to customize an existing demo for a specific pitch
- Before any new subagent build — always plan first

---

## Questionnaire Flow

Ask these in order. Each section builds on the previous. Use conversational tone — don't dump all questions at once.

### Round 1: The Basics

| # | Question | Options | Why |
|---|----------|---------|-----|
| 1 | **What industry is the customer?** | Financial Services / Healthcare / Retail / Travel & Hospitality / Telco / Public Sector / Tech / Other | Determines persona, terminology, compliance needs |
| 2 | **What channel?** | Messaging (web chat) / Voice / Case (no real-time) | Determines context variables, action patterns, UI rendering |
| 3 | **What's the core use case?** | [Open — let them describe it] | The "what does the customer need help with?" |
| 4 | **What's the customer persona?** | Name, loyalty/account tier, key attribute | Makes the demo relatable |

### Round 2: Complexity & Capabilities

| # | Question | Options | Default |
|---|----------|---------|---------|
| 5 | **How many actions in the chain?** | 3 (simple) / 4-5 (standard) / 6+ (complex) | 4-5 |
| 6 | **CLT cards?** | Yes — visual cards for key moments / No — text-only | Yes |
| 7 | **Knowledge articles?** | Yes — policy/procedure grounding / No | Yes |
| 8 | **Human-in-the-Loop gates?** | Every action confirms / Key moments only / Minimal (mostly silent) | Key moments only |
| 9 | **Topic switch moment?** | Yes — customer asks something off-topic mid-flow / No | Yes |
| 10 | **Closing flourish?** | Yes — extra value-add at end (weather, status, fun fact) / No | Yes |

### Round 3: Demo Beats (What Story Are You Telling?)

| # | Question | Purpose |
|---|----------|---------|
| 11 | **What's the "Know the Customer" moment?** | What profile data impresses? (loyalty tier, purchase history, preferences, open cases) |
| 12 | **What's the "wow" transaction?** | The key action the audience will remember (booking, approval, escalation, resolution) |
| 13 | **What's the loyalty/personalization play?** | How does the agent personalize? (tier-based perk, custom greeting, proactive offer) |
| 14 | **Any compliance/gating moment?** | Where should the plan pause for rep acknowledgment? (HIPAA, PCI, regulatory) |
| 15 | **What audience are you presenting to?** | Exec (keep it tight, 3 min) / Technical (show the config) / Mixed (balance both) |

---

## Validation Rules

Before generating the spec, validate against BEST-PRACTICES.md:

| Rule | Check | If Violated |
|------|-------|-------------|
| Topic naming | Is the name specific and singular? | Suggest: "[Persona Action]" not "General Support" |
| Action count | If 6+, does complexity justify it? | Warn: "6+ actions risks planner non-determinism. Consider splitting into 2 topics." |
| CLT without messaging | CLTs selected but channel is Voice? | Block: "CLT cards don't render on voice channel. Switch to messaging or remove CLTs." |
| Knowledge without articles | Knowledge selected but no article topics described? | Ask: "What policies/procedures should the agent know about?" |
| All-confirm pattern | Every action set to confirm? | Warn: "All-confirm slows the demo. Silent lookups (confirm off) make it feel intelligent. Suggest: first lookup silent, transaction confirms." |
| No topic switch | Demo has 6+ actions but no topic switch? | Suggest: "Long demos benefit from a topic switch to show conversation intelligence." |

---

## Output: Generated Spec

After all questions are answered, generate a filled `SUBAGENT-TEMPLATE.md` with:

1. **Subagent Identity** — name, developer name, description, scope (from answers)
2. **Demo Persona** — customer name, attributes, scenario (from industry + persona answers)
3. **Action Chain** — numbered action table with types, confirmation settings, CLT flags
4. **Data Flow Map** — output→input handoffs based on action chain logic
5. **Instructions** — sort-ordered instruction table following best practices
6. **Context Variables** — currentRecordId + any channel-specific vars
7. **Knowledge Articles** — article titles + coverage areas (if knowledge selected)
8. **Demo Script Outline** — phase/action/beat mapping for the presenter
9. **Quick Verification Checklist** — test prompts per action

### File Location

Save the generated spec to:
```
~/[demo-name]/skill/REBUILD-AGENT.md
```

If the repo doesn't exist yet, note that the SE should create it:
```bash
sf project generate --name [demo-name] --output-dir ~
cd ~/[demo-name] && git init
mkdir -p skill
```

---

## Industry Templates

Pre-loaded patterns for common industries. Use as starting points — the questionnaire refines them.

### Financial Services
- **Personas:** High-net-worth client, small business owner, fraud victim
- **Use cases:** Fraud alert triage, wire transfer approval, account limit increase, dispute resolution
- **Compliance gates:** PCI acknowledgment, identity verification pause
- **Knowledge:** Fraud procedures, wire limits by tier, dispute SLA policies
- **CLT cards:** Transaction timeline, risk score card, account summary

### Healthcare
- **Personas:** Patient, caregiver, provider office staff
- **Use cases:** Appointment rescheduling, prescription refill, referral status, billing dispute
- **Compliance gates:** HIPAA acknowledgment, identity verification, consent confirmation
- **Knowledge:** Scheduling policies, formulary lists, referral procedures
- **CLT cards:** Appointment calendar, medication card, coverage summary

### Retail / E-Commerce
- **Personas:** Loyalty member, first-time buyer, repeat returner
- **Use cases:** Order tracking, return/exchange, product recommendation, price match
- **Compliance gates:** None typical (low-regulation)
- **Knowledge:** Return policies, shipping SLAs, loyalty tier benefits
- **CLT cards:** Order status card, product comparison, loyalty summary

### Travel & Hospitality
- **Personas:** Frequent flyer, vacation planner, disrupted traveler
- **Use cases:** Rebooking, upgrade request, pet travel, lounge access, compensation
- **Compliance gates:** Safety acknowledgment (pets, special needs)
- **Knowledge:** Route policies, pet carrier specs, loyalty program rules
- **CLT cards:** Seat map, boarding pass, itinerary card, weather card

### Telco
- **Personas:** Consumer subscriber, enterprise admin, store associate
- **Use cases:** Plan upgrade, device troubleshooting, bill dispute, service outage
- **Compliance gates:** Plan change authorization, early termination disclosure
- **Knowledge:** Plan comparison, troubleshooting trees, coverage maps
- **CLT cards:** Usage dashboard, plan comparison card, device status

### Public Sector
- **Personas:** Citizen, caseworker, benefits applicant
- **Use cases:** Permit application status, benefits eligibility check, complaint filing
- **Compliance gates:** Data sharing consent, identity verification, privacy notice
- **Knowledge:** Eligibility criteria, process timelines, required documents
- **CLT cards:** Application status card, eligibility checklist, timeline card

---

## Example Interaction

```
SE: "I need a demo for a healthcare customer"

Planner: "Great — healthcare. A few questions to shape this:

1. What's the use case? (appointment scheduling, prescription refill, 
   referral tracking, billing, or something else?)
2. Messaging channel work, or do you need voice?
3. Who's the patient persona — any special attributes? (chronic condition, 
   VIP/concierge tier, pediatric, etc.)"

SE: "Appointment rescheduling. Messaging. Patient is a concierge-tier member 
named Margaret Chen — she has a recurring cardiology appointment."

Planner: "Got it. A few more:

4. How complex? I'd suggest 4-5 actions: Get Patient Profile → Check Provider 
   Availability → Reschedule Appointment → Send Confirmation + Reminder Setup.
5. CLT cards? I'd recommend a provider availability calendar card and a 
   confirmation card.
6. Knowledge articles? Could ground in scheduling policies (24-hr cancellation, 
   specialist wait times).
7. Any compliance gate? HIPAA acknowledgment before discussing medical details?
8. Topic switch? Maybe Margaret asks about her prescription refill mid-conversation?"

SE: "Yes to all of that. 5 actions, add a loyalty perk — concierge members get 
priority scheduling + free parking validation."

Planner: [Generates filled SUBAGENT-TEMPLATE.md with all sections complete]
```

---

## Handoff to Builder

After generating the spec, tell the SE:

```
✅ Demo spec generated: ~/[demo-name]/skill/REBUILD-AGENT.md

Next steps:
1. Review the spec — adjust any action names, persona details, or demo beats
2. When ready, invoke the build skill:
   "Build this demo using the spec at ~/[demo-name]/skill/REBUILD-AGENT.md"
   
The builder will:
- Create the SFDX project structure
- Generate Apex classes for each action
- Create the demo data script
- Deploy metadata to your SDO
- Produce the Agent Builder setup checklist
```

---

## Rules

- **Never skip the questionnaire.** Even if the SE says "just build me something" — ask at minimum: industry, channel, use case, persona. You need these to generate a coherent demo.
- **Validate against BEST-PRACTICES.md.** Don't generate specs that violate known patterns.
- **Keep action count realistic.** 4-5 is the sweet spot. 3 feels thin. 6+ risks planner non-determinism.
- **Always include a topic switch.** It's the single best "conversation intelligence" demo beat.
- **Default to messaging channel.** Voice demos require different CLT handling and are harder to debug.
- **Name the persona.** Named customers make demos memorable. Never use "John Doe" or "Jane Smith."
- **Include the closing flourish.** It's the "delight" moment that closes the demo strong.
- **Generate the full template.** Don't leave sections blank — fill every section of SUBAGENT-TEMPLATE.md with concrete values based on the SE's answers.
