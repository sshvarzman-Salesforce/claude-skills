---
name: good-morning
description: Start-of-day routine that reads last night's wrap-up summary, surfaces carry-forward items, and asks what you'd like to focus on today. Run when Chad says "good morning", "start the day", "what did I miss", or "catch me up".
tools: [Read, Bash]
---

# Good Morning — Start-of-Day Orientation

> Gets you oriented fast. Reads last night's wrap-up summary, shows what's
> pending, and asks what you want to work on today.

## When to trigger

- User says "good morning", "morning", "start the day", "what's on deck"
- User asks "what did I do yesterday?", "catch me up", "where did I leave off?"

## Pipeline

### Phase 0: Refresh Skills Context

Read both skills libraries to understand what's available and what each skill does:

1. **Main skills repo** (`~/prd-writer-skill/` → `git@git.soma.salesforce.com:chad-goldsmith/claude-skills.git`):
   ```bash
   ls ~/prd-writer-skill/ | grep -v '\.git\|\.cursor\|LICENSE\|README'
   ```
   Read the SKILL.md (or skill.md) from each directory — at minimum the frontmatter (name, description, tools) and first section. Know what each skill does so you can invoke the right one when asked.

2. **Demo skills repo** (`~/sf-demo-skills/` → `git@git.soma.salesforce.com:chad-goldsmith/sf-demo-skills.git`):
   ```bash
   ls ~/sf-demo-skills/
   ```
   Read SKILL.md and any key files (BEST-PRACTICES.md, CLT-GUIDE.md, etc.)

3. **Check for recent changes** in both repos:
   ```bash
   cd ~/prd-writer-skill && git log --oneline -5 && cd ~/sf-demo-skills && git log --oneline -5
   ```
   If new skills were added since last session, read those fully.

This ensures you know the full toolkit — capabilities, invocation patterns, tools available to each skill — so you can compose them correctly throughout the day.

### Phase 0.5: Scan Key Slack Channels for Overnight Learnings

Check eng team and FDE channels for anything new since last session (last ~18 hours). Use `slack_read_channel` on each:

| Channel | ID | Why |
|---------|-----|-----|
| SOUP Engineering | `C041YHQ8LQ0` | SOUP team updates |
| SOBA Engineering | `C05UAR03WHY` | Testing framework, quality metrics |
| SPA SF Engineering | `C02P450NJ84` | UI components, LWC, service plan rendering |
| NGS Engineering | `C06NDLHQJD7` | Chad's team — planner service, plan generation pipeline, **Dynamic Plans knowledge retrieval** |
| Sox Engineering | `C02CLRPJT1R` | Chad's team — service orchestration, **Guidance Plans knowledge retrieval** |
| Service Assistant Engineering | `C06TPK97CCE` | Engineering-wide, architecture decisions |
| FDE Pioneer | `C0B2ABV0S30` | FDE implementation learnings, field gaps |
| Retriever | `C08ALF5TMS9` | Knowledge grounding & RAG platform infrastructure — upstream of what Sox/NGS integrate into SRA. Watch for changes to hybrid_search, vector indexing, chunking, ranking. Note: SRA does NOT use prompt retrievers (ADL construct); this channel covers the Data Cloud retrieval layer that SRA's Search Knowledge action calls into. |
| EK for Service Cloud Enablement | `C0A05CP17K8` | Enterprise Knowledge + Service Cloud integration — HUDMO/UDMO setup, search index/retriever config, connector status, provisioning blockers |
| Agentforce Big Impact | `C07RDL9CLDR` | High-impact initiatives, strategic decisions affecting SRA |

**What to look for:**
- Architecture decisions or changes
- New bugs / regressions reported
- Feature launches or rollbacks
- Planner behavior changes (NGS especially)
- Customer escalation patterns (FDE Pioneer)
- Anything that contradicts or extends current skill knowledge

**Output:** A short list of "overnight signals" — only surface things that are actionable or that update your understanding. Skip routine standup noise, emoji reactions, and social chatter.

### Phase 1: Find the Most Recent Wrap-Up

1. Look for the most recent `wrap-up-summary.md` in `~/.aisuite/notebook/`:
   ```bash
   ls -d ~/.aisuite/notebook/2026-*/ | sort -r | head -5
   ```
2. Read `wrap-up-summary.md` from the most recent day folder that has one.
3. If no wrap-up exists, say so and skip to Phase 3.

### Phase 2: Surface the Summary

Present a concise orientation:

```
☀️ Good morning. Here's where you left off:

📅 Last session: [date]

## What happened
[2-3 bullet summary from wrap-up]

## Still pending
[Open threads / carry-forward items from wrap-up]

## Docs updated last
[List from wrap-up — so you know what's fresh]
```

Keep it scannable. Don't regurgitate the entire wrap-up — pull the most actionable pieces.

### Phase 3: Ask What's Next

After surfacing the summary, ask:

> What would you like to focus on today? Or should I pick up one of the carry-forward items?

If the user already stated what they want to do (e.g., "good morning, let's work on X"), skip the question and go straight into it.

## Rules

- **Don't be chatty** — this is a briefing, not a conversation. Get to the point fast.
- **Don't re-read files the user already knows about** — just reference paths.
- **Don't start working on carry-forward items without asking** — surface them, let the user choose.
- **If the wrap-up is stale (>3 days old)**, mention it: "Last wrap-up is from [date] — things may have moved since then."
- **If multiple day folders exist without wrap-ups**, check the most recent 3 for any notes files and mention them briefly.

## Output Format

Keep the full output under 20 lines. This is a dashboard, not a document.
