# Claude Code Skills

A collection of **149 Claude Code skills** for Salesforce development — Agentforce, Service Cloud, OmniStudio, Data Cloud, LWC, metadata, B2B Commerce, and more. Each skill is a self-contained folder with a `SKILL.md` (and optional `references/` and `assets/`) that Claude Code loads on demand.

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
- `build-agentforce-service-demo`
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
- `connecting-datacloud`
- `creating-b2b-commerce-store`
- `customer-advocate`
- `cvs-sra-tracking`
- `debugging-apex-logs`
- `deploying-metadata`
- `deploying-omnistudio-datapacks`
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

**Inbound messaging → Agentforce routing** — the INBOUND counterpart to `replicating-omnichannel-routing-flows`: stand up an In-App/Web chat that lands on an ASA agent end to end — the RoutingFlow (resolves Contact from a pre-chat phone, links it to the `MessagingEndUser` parent, `routeWork` routingType=Copilot → BotDefinition), the EmbeddedMessaging `MessagingChannel` with a custom pre-chat phone parameter, and the `EmbeddedServiceConfig` deployment (with the Setup-provisioned ChatterNetworkPicasso site caveat). Ships verified, deployable template XML for all three artifacts.

- `routing-inbound-messaging-to-agentforce-agent`

**Agentforce Service Agent (ASA) build suite** — hard-won patterns from an end-to-end voice ASA build (system-context data flows, agent-user permissions, data-library wiring, locked-object workarounds, and the end-to-end playbook):

- `building-system-context-agent-data-flows`
- `scoping-agent-user-permissions`
- `connecting-agent-data-library`
- `handling-locked-standard-objects`
- `building-voice-asa-agent`

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
