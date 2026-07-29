# Claude Code Skills

A collection of **82 Claude Code skills** for Salesforce development — Agentforce, OmniStudio, Data Cloud, LWC, metadata, B2B Commerce, and more. Each skill is a self-contained folder with a `SKILL.md` (and optional `references/` and `assets/`) that Claude Code loads on demand.

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

- `activating-datacloud`
- `analyzing-omnistudio-dependencies`
- `applying-cms-brand`
- `applying-slds`
- `building-entitlements-slas`
- `building-mobile-apps`
- `building-nba-conversation-intelligence`
- `building-omnistudio-callable-apex`
- `building-omnistudio-datamapper`
- `building-omnistudio-flexcard`
- `building-omnistudio-integration-procedure`
- `building-omnistudio-omniscript`
- `building-sf-integrations`
- `building-ui-bundle-app`
- `building-ui-bundle-frontend`
- `calling-prompt-templates-in-flows`
- `configuring-connected-apps`
- `connecting-datacloud`
- `creating-b2b-commerce-store`
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
- `preparing-datacloud`
- `querying-soql`
- `replicating-omnichannel-routing-flows`
- `retrieving-datacloud`
- `reviewing-lwc-mobile-offline`
- `running-apex-tests`
- `running-code-analyzer`
- `searching-media`
- `segmenting-datacloud`
- `sf-agent-api-citations`
- `sf-agent-api-integration-patterns`
- `sf-agent-api-messaging`
- `sf-agent-api-review`
- `sf-agent-api-session-lifecycle`
- `sf-agent-api-setup`
- `sf-agent-api-troubleshooting`
- `sf-agent-api-variables`
- `switching-org`
- `testing-agentforce`
- `uplifting-components-to-slds2`
- `using-mobile-native-capabilities`
- `using-ui-bundle-salesforce-data`
- `validating-slds`

## Notes

- Each skill folder is self-contained — you can install any subset.
- Skills are instructions and reference material, not executable programs; they contain no secrets or credentials.
