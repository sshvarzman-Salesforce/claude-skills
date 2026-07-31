---
name: build-agentforce-service-demo
description: >
  Universal skill for building and deploying Agentforce Service Assistant Dynamic Plans demos
  in a Salesforce SDO. Handles SFDX project setup, metadata deployment, demo data creation,
  and produces a manual setup checklist for Agentforce config. Applies to any Service Assistant
  messaging demo — not tied to a specific scenario. When creating a new subagent, use the
  SUBAGENT-TEMPLATE.md framework to generate a complete demo-specific build doc.
tools: [Bash, Read, Write, Edit]
---

# Build Agentforce Service Demo

Deploys and configures an **Agentforce Service Assistant Dynamic Plans** (Human-in-the-Loop, messaging) demo in a target Salesforce SDO.

Use this skill for any new demo. It covers the repeatable infrastructure — SFDX structure, SF CLI auth, metadata deploy, demo data, and Agentforce setup guidance.

**Demo planner:** see `DEMO-PLANNER.md` (same repo) — questionnaire-driven spec generator
**Best practices reference:** see `BEST-PRACTICES.md` (same repo)
**CLT card guide:** see `CLT-GUIDE.md` (same repo)
**Subagent template:** see `SUBAGENT-TEMPLATE.md` (same repo)
**Reference implementations:**
- [pet-travel-demo](https://git.soma.salesforce.com/chad-goldsmith/pet-travel-demo)
- [retail-return-demo](https://git.soma.salesforce.com/chad-goldsmith/retail-return-demo)
- [financial-fraud-demo](https://git.soma.salesforce.com/chad-goldsmith/financial-fraud-demo)

---

## Getting Started

**New to building SRA demos?** Start here.

### Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| `sf` CLI | Deploy metadata, run data scripts, auth to orgs | `npm install -g @salesforce/cli` |
| Claude Code | Run this skill + AI-assisted build | [claude.ai/claude-code](https://claude.ai/claude-code) |
| SDO org (262+) | Target Salesforce org with SRA enabled | Request via SDO portal |
| Git access | Clone demo repos | SSH key on git.soma |

### Quick Start (5 minutes to first demo)

```bash
# 1. Clone this repo
git clone git@git.soma.salesforce.com:chad-goldsmith/sf-demo-skills.git
cd sf-demo-skills

# 2. Copy the skill into your Claude Code skills directory
cp -r . ~/.claude/skills/build-agentforce-service-demo/

# 3. Auth to your SDO
sf org login web --alias mySDO --set-default --instance-url https://your-sdo.my.salesforce.com

# 4. Pick an existing demo to deploy (or build your own):
#    Option A: Deploy the Pet Travel demo (separate repo)
git clone git@git.soma.salesforce.com:chad-goldsmith/pet-travel-demo.git
cd pet-travel-demo && sf project deploy start --source-dir force-app --target-org mySDO

#    Option B: Use a subagent template to build from scratch
cp SUBAGENT-TEMPLATE.md my-new-demo/skill/REBUILD-AGENT.md
# Fill in the template, then follow the steps below
```

### Your First Demo (Recommended Path)

1. **Deploy an existing demo** (Pet Travel or Financial Fraud) to see it working
2. **Read BEST-PRACTICES.md** to understand design patterns
3. **Read CLT-GUIDE.md** if your demo needs visual cards
4. **Run the Demo Planner** (`DEMO-PLANNER.md`) — it asks what you need and generates a spec
5. **Build from the spec** using `SUBAGENT-TEMPLATE.md` framework

### Grounding Sources

Before generating any subagent, read these reference docs (grounding material):

| File | Purpose |
|------|---------|
| `references/alberto-best-practices.md` | 3 worked examples (Credit Card Declined, Processing Returns, Travel Documentation) + subagent guidelines |
| `references/alberto-topic-strategy.md` | Instruction-writing guidance, topic granularity, KB-grounding depth rules |
| `references/alberto-design-strategy.md` | Reasoning-anchor model (why description/scope matter), 2 examples (Payroll, Benefits Enrollment) |
| `references/alberto-generator-prompt.md` | Original prompt, output structure rules, output limits |
| `BEST-PRACTICES.md` | Comprehensive rules (includes Alberto's + your action/CLT/SFDX patterns) |

**Read all before producing subagent output** — they're the source material this skill reasons from.

### Related Skills

These skills complement the demo builder:

| Skill | Repo | Purpose |
|-------|------|---------|
| `demo-planner` | This repo (`DEMO-PLANNER.md`) | "What kind of demo?" → questionnaire → filled spec |
| `sra-setup-debug` | [claude-skills](https://git.soma.salesforce.com/chad-goldsmith/claude-skills) | Diagnose "why isn't my demo working?" |
| `sra-expert-shared` | [claude-skills](https://git.soma.salesforce.com/chad-goldsmith/claude-skills) | SRA knowledge base (architecture, patterns) |
| `sra-agent-debugger` | [claude-skills](https://git.soma.salesforce.com/chad-goldsmith/claude-skills) | Trace a session to debug action failures |
| `sf-clt-builder` | [claude-skills](https://git.soma.salesforce.com/chad-goldsmith/claude-skills) | Generate CLT card LWC + metadata |

---

## How This Skill Set Works

```
sf-demo-skills/                           ← General demo knowledge (this repo)
├── SKILL.md                              ← Universal demo build process
├── DEMO-PLANNER.md                       ← Questionnaire-driven spec generator
├── BEST-PRACTICES.md                     ← Rules and patterns (topics, actions, sequencing)
├── CLT-GUIDE.md                          ← Custom Lightning Type card guide
└── SUBAGENT-TEMPLATE.md                  ← Framework for new demo docs

pet-travel-demo/ (standalone repo)       ← Reference implementation
├── force-app/                            ← Deployable Apex, LWC, Lightning Types
└── skill/                                ← Agent Builder config docs
    ├── REBUILD-AGENT.md                  ← Full rebuild guide
    ├── BUILD-SHEET.md                    ← Step-by-step click-through
    ├── DEMO-SCRIPT.md                    ← Turn-by-turn talk track
    ├── KNOWLEDGE-ARTICLE.md              ← Knowledge articles
    ├── TOPIC-INSTRUCTIONS.md             ← Topic & instruction config
    └── setup-data.apex                   ← Demo data script
```

**Repo organization:**
- **sf-demo-skills** → shared playbook (best practices, templates, CLT guide)
- **Each demo** → its own SFDX repo (code in `force-app/`, docs in `skill/`)

**When you create a new demo:**
1. Use the universal skill (this file) for project setup, deploy, and auth
2. Copy `SUBAGENT-TEMPLATE.md` into your new demo's `skill/` folder
3. Fill in the template sections (identity, actions, data flow, instructions)
4. The filled template becomes your rebuild doc + demo-specific skill
5. Follow BEST-PRACTICES.md for all design decisions

---

## What Makes a Great Service Assistant Demo

Every demo should land three core value props:

### 1. Know the Customer
Surface everything the rep needs before they type a word. Loyalty tier, purchase history, open cases, preferences — pulled from CRM. Rep walks in informed.

### 2. Know What the Engagement Is About
Agentforce reads the conversation and builds the dynamic plan automatically. The rep doesn't decide what steps to take — the agent identifies the intent and constructs the action chain. Rep reviews and approves.

### 3. Know How to Solve It
The plan executes proactively. Silent lookups run in background. Rep clicks sidebar buttons to confirm key moments. No numbered lists in chat — clean, conversational, rep-guided.

### Conversation Intelligence Highlights to Call Out
- **Rep can ask questions in the sidebar** — agent listens and responds
- **Customer questions are handled automatically** — agent triggers knowledge search without rep involvement
- **Agent extracts data from conversation** — if rep asks "what's your order number?" and customer replies, the agent captures and uses it in subsequent actions
- **No numbered lists in chat** — all next steps appear as sidebar buttons

---

## Demo Build Process

### Step 1: Project Setup

```bash
# Create SFDX project
sf project generate --name my-demo-name --output-dir ~

# Initialize git
cd ~/my-demo-name
git init
git remote add origin git@git.soma.salesforce.com:chad-goldsmith/my-demo-name.git
```

Structure every demo repo the same way:
```
my-demo-name/
├── force-app/main/default/
│   ├── objects/         ← custom objects + fields
│   └── profiles/        ← Admin.profile-meta.xml for FLS
├── skill/
│   ├── setup-data.apex  ← idempotent demo data script
│   ├── DEMO-SCRIPT.md   ← turn-by-turn demo flow
│   └── TOPIC-INSTRUCTIONS.md ← copy-paste for Agentforce Setup UI
└── sfdx-project.json
```

### Step 2: Auth to SDO

```bash
# Standard login
sf org login web --alias mySDO --set-default --instance-url https://your-sdo.my.salesforce.com

# Verify
sf org display --target-org mySDO
```

> **URL format:** Always use `.my.salesforce.com` — Lightning URLs (`lightning.force.com`) will fail.

### Step 3: Deploy Metadata

```bash
cd ~/my-demo-name
sf project deploy start --source-dir force-app --target-org mySDO
```

Common errors:
| Error | Fix |
|---|---|
| `DUPLICATE_DEVELOPER_NAME` | Field exists — add `--ignore-conflicts` |
| `You cannot deploy to a required field` | Remove that field from profile XML (required fields auto-grant FLS) |
| `INSUFFICIENT_ACCESS` | User needs deploy perms in org |
| `INVALID_TYPE` | Update `sourceApiVersion` in `sfdx-project.json` |

### Step 4: Demo Data

Run idempotent Apex to set up demo records:

```bash
sf apex run --file ~/my-demo-name/skill/setup-data.apex --target-org mySDO
```

**Rules for demo data scripts:**
- Always check-before-insert (query first, upsert or update if exists)
- Reset fields to known values even if record exists
- Print success/failure to debug log
- Never hardcode record IDs — query by name or unique field

### Step 5: Verify

```bash
# Spot-check key records
sf data query --query "SELECT Id, Name FROM YourObject__c LIMIT 5" --target-org mySDO
```

---

## Agentforce Setup Checklist

After metadata deploys, these steps must be done in the Salesforce Setup UI.

### Topic
```
Setup → Agentforce → Topics → New

Name:                   [Specific to demo — see BEST-PRACTICES.md for naming rules]
Classification Desc:    [What case types + questions this covers]
Scope:                  [What agent will and won't do]
Instructions:           [One task per instruction — 4-5 if using knowledge grounding]
```

### Flows (Agentforce Actions)
For each action in the demo:
```
Flow Builder → New Flow → Autolaunched Flow (No Trigger)

- Add Input Variables:  Available for Input ✓
- Add Output Variables: Available for Output ✓
- Build logic
- Activate
```

> **Critical — Pass-through variables:** If a value is needed by downstream actions
> (e.g. CustomerId, FlightNumber), the first action that receives it MUST also
> mark it Available for Output — even if the flow doesn't transform it.
> Without this, downstream actions can't map to it and the agent has to guess.
>
> Example: Get Customer Profile takes CustomerId as input. Pet Booking and
> Loyalty Perk also need CustomerId. So Get Customer Profile must output
> CustomerId even though it doesn't change it. Add it to the Assignment element
> and mark the variable Available for Output.

Then register — **always use the Asset Library, not the subagent UI:**
```
Setup → Agentforce Studio → Agentforce Asset Library → Actions → New
  Type: Flow
  Confirmation: On (rep must click) or Off (runs silently)
```

> **Critical:** Do NOT use "Create New Action" inside a subagent in Agentforce Builder.
> That creates a local-only action that:
> - Does NOT appear in the Asset Library or other subagents
> - Cannot be re-added after removal (known bug W-22614303 in v262)
> - Does NOT auto-refresh when flow variables change
>
> Always create in the Asset Library first, then use "Add from Asset Library"
> inside the subagent. When a flow changes (new variables added), rebuild the
> action in the Asset Library, then remove and re-add from Asset Library in
> the subagent to pick up the new schema.

### Topic Action Chain
Add actions to topic in execution order. Typical pattern:
```
Action 1: Get Customer Profile  — Confirmation: On  (shows rep who they're talking to)
Action 2: [Silent lookup]       — Confirmation: Off (runs in background)
Action 3: [Key transaction]     — Confirmation: On  (rep confirms the important moment)
Action N: [Final deliverable]   — Confirmation: On  (boarding pass, case close, etc.)
```

### Action Variable Mapping
When adding actions to a topic, map outputs from earlier actions to inputs of
later ones. Don't leave inputs unmapped if the value came from a prior step —
the agent will try to infer it but explicit mapping is more reliable.

| Pattern | How to map |
|---|---|
| ID passed through multiple actions | Output it from action 1, map to input on actions 2-N |
| Silent lookup feeds next action | Map output directly — agent won't show it to rep |
| Boolean flag (e.g. PerkGranted → LoungePassIncluded) | Map explicitly — booleans don't infer well |

### Prompt Templates (if used)
```
Setup → Prompt Builder → New Template
  - Use Insert Resource for data pills — never type {!Variable} manually
  - Keep output short and conversational
  - Test preview before wiring to action
```

### Knowledge (if used)
```
Setup → Knowledge → New Article
  - Publish and set to public
  - Write content in alphanumeric steps (1, a, b, 2, a, b...)

Agentforce Builder → Data Library → New
  Identifying fields: Title, Summary
  Content fields:     Answer, Detail, Question (+ custom fields)

Permission sets (assign to relevant users):
  Agent Knowledge Access    → ServicePlanner User
  Service Rep Knowledge Access → Service Reps
```

---

## Connecting to a Different SDO

```bash
# Remove current auth
sf org logout --target-org mySDO

# Re-auth
sf org login web --alias mySDO --set-default --instance-url https://new-sdo.my.salesforce.com

# Redeploy (safe to run again — metadata is idempotent)
sf project deploy start --source-dir force-app --target-org mySDO --ignore-conflicts

# Re-run demo data
sf apex run --file skill/setup-data.apex --target-org mySDO
```

---

## Profile XML Rules (FLS)

Every demo needs a `profiles/Admin.profile-meta.xml`. Rules:
- Include `<fieldPermissions>` for every custom field on every custom object
- **Do NOT include required fields** — they cause deploy errors (`You cannot deploy to a required field`)
- Always include `<objectPermissions>` (CRUD + ViewAll + ModifyAll) for every custom object
- Include `<custom>false</custom>` and `<userLicense>Salesforce</userLicense>`

Template:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <fieldPermissions>
        <editable>true</editable>
        <field>MyObject__c.MyField__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>true</modifyAllRecords>
        <object>MyObject__c</object>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>
    <custom>false</custom>
    <userLicense>Salesforce</userLicense>
</Profile>
```

---

## Active Demos

| Demo | Location | Description | Status |
|---|---|---|---|
| Pet Travel Management | [chad-goldsmith/pet-travel-demo](https://git.soma.salesforce.com/chad-goldsmith/pet-travel-demo) | In-cabin pet booking with paired seating, loyalty perks, boarding pass CLT cards | Active — deployed to mySDO |
| Financial Fraud Detection | `sf-demo-skills/subagents/financial-fraud-demo/` | Fraud alert triage, transaction investigation, case escalation | Complete — template ready |

### Demo Capabilities Matrix

| Capability | Pet Travel | Financial Fraud |
|-----------|-----------|-----------------|
| Custom Objects + Fields | ✅ Pet_Manifest__c | ✅ (uses standard Case fields) |
| Apex Actions | ✅ GetCustomerProfile, CheckPetManifest, GenerateBoardingPass | ✅ (flow-based) |
| CLT Cards | ✅ Seat map, boarding pass, customer profile | ❌ |
| Knowledge Articles | ✅ 10+ (airport references, policies, carrier specs) | ✅ (fraud procedures) |
| Dynamic Plans | ✅ | ✅ |
| Messaging Channel | ✅ | ✅ |
| Voice Channel | 🔜 (in progress) | ❌ |

*Add new demos to this table as you build them.*
