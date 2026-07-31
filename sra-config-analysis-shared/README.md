# sra-config-analysis-shared

Analyzes any Agentforce Service Assistant topic configuration for variance and non-deterministic behavior.

## Install

Copy `SKILL.md` into `~/.claude/skills/sra-config-analysis-shared/`

That's it. One file. No other skills needed — all domain knowledge from `sra-expert`, `sra-edge-cases`, `sra-agent-debugger`, `sra-test-case-writer`, `sra-setup-debug`, and `sra-recall` is baked in.

## What it does

Paste (or connect to an org) a topic's instructions + action configs + sample artifacts and it produces:

- Ranked variance sources (CRITICAL / HIGH / MEDIUM / LOW)
- Edge cases across 7 categories
- Test cases mapped to 9 quality goals
- Trace predictions (what sra-agent-debugger would show)
- Setup issue checklist
- Prioritized fix recommendations (P0 / P1 / P2)
- Slack-ready summary for team distribution

## Input modes

| Mode | How | When to use |
|------|-----|-------------|
| **Paste** | Copy/paste topic instructions, action configs, KB articles, case data | Default — works anywhere |
| **Org-connected** | MCP Adaptor pulls configs directly from the customer org | When you have API access to the org |

You can mix modes — e.g., pull topic config from the org but paste a transcript manually.

## What to provide

| Required | What |
|----------|------|
| Yes | Topic instructions (full text) |
| Yes | Classification description + scope |
| Yes | Actions list + configs (inputs, outputs, HiL settings) |
| Recommended | Knowledge Articles (full text) |
| Recommended | Sample case email or message transcript |
| Recommended | Case record field values |

The skill will ask for missing artifacts — the analysis is significantly better with real customer data vs. theoretical-only.

## Example

```
/sra-config-analysis-shared Hardware Product Support

[paste topic instructions here]
[paste action configs here]
[paste KB article here]
```

Or with org connection:

```
/sra-config-analysis-shared Hardware Product Support — connected to org
```

## Repo

https://git.soma.salesforce.com/chad-goldsmith/claude-skills
