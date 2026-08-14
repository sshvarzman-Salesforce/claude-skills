# Claude Code Skills

A collection of **155 Claude Code skills** for Salesforce development — Agentforce, Service Cloud, OmniStudio, Data Cloud, LWC, metadata, B2B Commerce, and more. Each skill is a self-contained folder with a `SKILL.md` (and optional `references/` and `assets/`) that Claude Code loads on demand.

## What is a skill?

A skill packages instructions, reference docs, and assets for a specific kind of task. When your request matches a skill's description, Claude Code loads it and follows its workflow. See the [Claude Code skills docs](https://docs.claude.com/en/docs/claude-code/skills) for details.

## Install

Skills live in `~/.claude/skills` (user scope, available in every project) or `.claude/skills` inside a project (project scope).

### Install all skills (user scope)

**macOS / Linux:**
```bash
git clone https://github.com/sshvarzman-Salesforce/claude-skills.git /tmp/claude-skills
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/*/ ~/.claude/skills/
```

**Windows (Git Bash):**
```bash
git clone https://github.com/sshvarzman-Salesforce/claude-skills.git /c/tmp/claude-skills
mkdir -p ~/.claude/skills
cp -r /c/tmp/claude-skills/*/ ~/.claude/skills/
```

### Install a single skill

Copy just the folder you want into your skills directory:
```bash
cp -r /tmp/claude-skills/developing-agentforce ~/.claude/skills/
```

### Project scope instead of user scope

Drop the folders into `<your-project>/.claude/skills/` instead of `~/.claude/skills/` if you want the skills scoped to one repo (and checked in for your team).

## Verify

Restart Claude Code (or start a new session) and the skills appear in the available-skills list. You can invoke one explicitly with `/<skill-name>`.

## Skills included

149 skills, listed alphabetically:

- `activating-datacloud`
- `agentforce-skills-research`
- `agentforce-testing-center`
- `agentforce-voice-expert`
- `ai-landing-page`
- `analyzing-omnistudio-dependencies`
- `applying-cms-brand`
- `applying-slds`
- `assigning-sra-via-flow`
- `authoring-serviceplanner-sra-topics`
- `build-agentforce-service-demo`
- `building-contact-center-kpis-agentwork`
- `building-entitlements-slas`
- `building-mobile-apps`
- `building-nba-conversation-intelligence`
- `building-omnistudio-callable-apex`
- `building-omnistudio-datamapper`
- `building-omnistudio-flexcard`
- `building-omnistudio-integration-procedure`
- `building-omnistudio-omniscript`
- `building-sf-integrations`
- `building-system-context-agent-data-flows`
- `building-ui-bundle-app`
- `building-ui-bundle-frontend`
- `building-voice-asa-agent`
- `calling-prompt-templates-in-flows`
- `case-management-setup`
- `caturday`
- `community-share`
- `configuring-connected-apps`
- `connecting-agent-data-library`
- `connecting-channels-to-asa`
- `connecting-datacloud`
- `creating-b2b-commerce-store`
- `customer-advocate`
- `cvs-sra-tracking`
- `debugging-apex-logs`
- `deploying-metadata`
- `deploying-omnistudio-datapacks`
- `deploying-person-account-fields-via-contact`
- `deploying-ui-bundle`
- `developing-agentforce`
- `developing-datacloud-code-extension`
- `fetching-salesforce-docs`
- `generating-apex`
- `generating-apex-test`
- `generating-custom-application`
- `generating-custom-field`
- `generating-custom-lightning-type`
- `generating-custom-object`
- `generating-custom-tab`
- `generating-flexipage`
- `generating-flow`
- `generating-lightning-app`
- `generating-list-view`
- `generating-lwc-components`
- `generating-mermaid-diagrams`
- `generating-permission-set`
- `generating-ui-bundle-custom-app`
- `generating-ui-bundle-features`
- `generating-ui-bundle-metadata`
- `generating-ui-bundle-site`
- `generating-validation-rule`
- `generating-visual-diagrams`
- `getting-datacloud-schema`
- `go-to-bed`
- `good-morning`
- `handling-locked-standard-objects`
- `handling-sf-data`
- `harmonizing-datacloud`
- `impeccable`
- `implementing-ui-bundle-agentforce-conversation-client`
- `implementing-ui-bundle-file-upload`
- `integrating-b2b-commerce-open-code-components`
- `investigating-agentforce-architecture`
- `investigating-agentforce-d360`
- `linking-individuals-by-phone-in-flows`
- `managing-managed-event-subscription`
- `modeling-omnistudio-epc-catalog`
- `observing-agentforce`
- `orchestrating-datacloud`
- `pm-pretotype`
- `pm-pretotype-shared`
- `preparing-datacloud`
- `querying-soql`
- `replicating-omnichannel-routing-flows`
- `retrieving-datacloud`
- `reviewing-lwc-mobile-offline`
- `routing-inbound-messaging-to-agentforce-agent`
- `running-apex-tests`
- `running-code-analyzer`
- `sc-pdlc-audit`
- `scoping-agent-user-permissions`
- `searching-media`
- `segmenting-datacloud`
- `service-helpagent-coordinate`
- `sf-agent-api-citations`
- `sf-agent-api-integration-patterns`
- `sf-agent-api-messaging`
- `sf-agent-api-review`
- `sf-agent-api-session-lifecycle`
- `sf-agent-api-setup`
- `sf-agent-api-troubleshooting`
- `sf-agent-api-variables`
- `sf-clt-builder`
- `sf-hld-reviewer`
- `sf-instance-lookup`
- `sf-pbd-writer`
- `sf-prd-writer`
- `sf-prototype`
- `sf-service-ai-intake`
- `sf-service-case-management`
- `sf-service-console-productivity`
- `sf-service-csi`
- `sf-service-email-to-case`
- `sf-service-entitlements`
- `sf-service-field-service-handoff`
- `sf-service-incident-management`
- `sf-service-itsm-processes`
- `sf-service-knowledge`
- `sf-service-messaging-conversation-toolkit`
- `sf-service-miaw-client`
- `sf-service-models-api`
- `sf-service-omnichannel-routing`
- `sf-service-review`
- `sf-service-surveys`
- `sf-service-tooling-cicd`
- `sf-service-voice-digital`
- `sf-service-voice-runtime`
- `sf-service-voice-toolkit`
- `sra-action-setup`
- `sra-agent-debugger`
- `sra-analytics`
- `sra-config-analysis`
- `sra-config-analysis-shared`
- `sra-customer-interview`
- `sra-edge-cases`
- `sra-engineer`
- `sra-expert-shared`
- `sra-latency-research`
- `sra-nga-migration`
- `sra-pm-triage`
- `sra-recall`
- `sra-remember`
- `sra-review-learnings`
- `sra-setup-debug`
- `sra-subagent-generator`
- `switching-org`
- `testing-agentforce`
- `update-my-boss`
- `uplifting-components-to-slds2`
- `using-mobile-native-capabilities`
- `using-ui-bundle-salesforce-data`
- `ux-research-insights`
- `validating-slds`

### Recently added

**Person Account custom fields — create on Contact, read the `__pc` mirror** — the reusable mechanics for adding a custom field to a Person Account without the classic split-field mistake. Author the person attribute on **Contact**; Salesforce auto-materializes it on **Account** as a `__pc`-suffixed field (e.g. `Member_Status__c` → `Account.Member_Status__pc`), immediately queryable via SOQL and REST/Bulk API and referenceable in Flow — you never author the Account-side field. Covers why creating it on Account directly is wrong, the one exception (roll-up summaries must live on the master Account), FLS on the Contact source field, placing it on BOTH Contact and Account page layouts, and — from a Person Account's Contact record in a Flow — traversing `Contact.AccountId → Account` (the person self-lookup) to read `__pc`/roll-up/Account-only fields in system mode. Includes the deploy/verify recipe and a worked OMERS-pension example.

- `deploying-person-account-fields-via-contact`

**Link an individual to a conversation by phone (in a Flow)** — the reusable pattern for resolving *who* a caller/chatter/emailer is and stamping them onto the conversation record. In a Flow, take the phone/ANI off a `VoiceCall` (`FromPhoneNumber`/`ToPhoneNumber` keyed on `CallType`), `MessagingSession`, or `Case`, run the OOB `findMatchingIndividuals` action (`searchTerm`/`searchFields="Phone"`/`searchObject`) against Contact / Person Account / Lead, size the returned `contactIds` collection with the `AssignCount` operator (the metadata enum for the UI's "Equals Count" — `EqualsCount` fails deploy), branch 0 / 1 / >1, and on exactly one match set the host lookup (`Contact__c`) + `RelatedRecordId`. Zero/multiple write an info Long-Text message and latch a filterable Checkbox (formulas can't reference Long Text Area, so the checkbox is flow-set). Ships the verified, deployed `VoiceCall_Match_Caller` flow as a template.

- `linking-individuals-by-phone-in-flows`

**Inbound messaging → Agentforce routing** — the INBOUND counterpart to `replicating-omnichannel-routing-flows`: stand up an In-App/Web chat that lands on an ASA agent end to end — the RoutingFlow (resolves Contact from a pre-chat phone, links it to the `MessagingEndUser` parent, `routeWork` routingType=Copilot → BotDefinition), the EmbeddedMessaging `MessagingChannel` with a custom pre-chat phone parameter, and the `EmbeddedServiceConfig` deployment (with the Setup-provisioned ChatterNetworkPicasso site caveat). Ships verified, deployable template XML for all three artifacts.

- `routing-inbound-messaging-to-agentforce-agent`

**ServicePlanner (SRA) topics with real actions** — build a classic ServicePlanner Service Rep Assistant into a multi-topic guided-resolution assistant AND attach a real prompt-template/flow action to a topic. The non-obvious lesson: a ServicePlanner `GenAiPlannerBundle` DOES accept custom `generatePromptResponse`/`flow` actions, but only as per-topic `<localActions>` (with a matching per-topic `<localActionLinks>`) — a top-level `<plannerActions>` throws the opaque `ErrorId (-1341094778)`. Covers the decomposed bundle shape, the numbered `Step N:` instruction convention (HTML/bold + per-step customer scripting), per-topic knowledge actions, action-name uniqueness, `localActions/<topic>/<action>/schema.json`, and the deactivate → deploy → reactivate lifecycle.

- `authoring-serviceplanner-sra-topics`

**Assigning which SRA is shown (multi-agent assignment flow)** — the OPTIONAL *Define Your Multi-Agent Assignment Criteria* autolaunched flow that decides which ServicePlanner SRA appears on a live VoiceCall / MessagingSession / Case, keyed on that record's fields. The whole contract is two variables: an input String named exactly `recordId`, and one output String whose **value must be the SRA's agent API name** (`BotDefinition.DeveloperName`, not a label/Id). Covers the exact variable shapes, per-channel object differences, building one from scratch, and scaling an existing flow to a new brand/SRA.

- `assigning-sra-via-flow`

**Agentforce Service Agent (ASA) build suite** — hard-won patterns from an end-to-end voice ASA build (system-context data flows, agent-user permissions, data-library wiring, locked-object workarounds, channel connection, and the end-to-end playbook). The playbook now states two hard rules learned the hard way: **prompt templates are for DATA READS ONLY** (create/modify/delete must be autolaunched Flows), and **every agent action needs ≥1 input parameter** (the `Input:ContactID`-hardcoded-to-the-demo-persona pattern; a zero-input action throws the Simulator's "missing input parameters" error):

- `building-system-context-agent-data-flows`
- `scoping-agent-user-permissions`
- `connecting-agent-data-library`
- `handling-locked-standard-objects`
- `connecting-channels-to-asa`
- `building-voice-asa-agent`

**Connecting voice + messaging channels to an ASA** — the connect-the-channels map: how a live VOICE call and an in-app/web MESSAGING chat get INTO the agent (inbound omni-flow → `routeWork` routingType=Copilot → BotDefinition) and how the agent hands a conversation OUT to a human — to a QUEUE, a SKILL, or DIRECT to a specific rep — on `@utils.escalate`. Nails the two perennial mistakes: (1) messaging escalation binds in the agent `.agent` metadata but VOICE binds only in Setup (never metadata); (2) messaging must use the messaging escalation flow, never the voice one. Points at the deep-dive skills that carry the deployable XML.

- `connecting-channels-to-asa`

**Contact-center KPIs from the AgentWork object** — build accurate Speed-to-Answer (ASA), Abandoned, and Accepted-by-a-genuine-HUMAN KPIs on `VoiceCall` and `MessagingSession`, driven off `AgentWork`. Covers the custom fields (`Entered_Queue_Timestamp__c`, `Accepted_By_Human_Timestamp__c`, `Abandoned__c`, the `Speed_To_Answer_Seconds__c` formula), the record-triggered AgentWork stamping flow, and the whole reason it's hard — the **double-accept problem**: an escalated conversation produces TWO accepted AgentWork rows (first the bot/ASA/Omni leg as an Automated Process user, then the real human), so the human stamp must gate on `UserType='Standard'` AND `Profile.Name != 'Einstein Agent User'`. Includes the acceptor-User-lookup pattern and the auto-store-vs-`queriedFields` runtime-fault gotcha.

- `building-contact-center-kpis-agentwork`

**Service Cloud implementation-pattern suite:**

- `service-helpagent-coordinate`
- `sf-service-ai-intake`
- `sf-service-case-management`
- `sf-service-console-productivity`
- `sf-service-csi`
- `sf-service-email-to-case`
- `sf-service-entitlements`
- `sf-service-field-service-handoff`
- `sf-service-incident-management`
- `sf-service-itsm-processes`
- `sf-service-knowledge`
- `sf-service-messaging-conversation-toolkit`
- `sf-service-miaw-client`
- `sf-service-models-api`
- `sf-service-omnichannel-routing`
- `sf-service-review`
- `sf-service-surveys`
- `sf-service-tooling-cicd`
- `sf-service-voice-digital`
- `sf-service-voice-runtime`
- `sf-service-voice-toolkit`

## Notes

- Each skill folder is self-contained — you can install any subset.
- Skills are instructions and reference material, not executable programs; they contain no secrets or credentials.
