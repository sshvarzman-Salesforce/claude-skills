---
name: sra-recall
description: Search and retrieve learnings from the SRA memory system. Use when looking up past decisions, customer preferences, or domain knowledge about Service Rep Assistant. Supports filtered search by category, tag, or keyword, plus recent and full dump modes.
tools: [Read]
---

# SRA Recall

Query memory: $ARGUMENTS

## Usage

```
/sra-recall [query]              — Search all memory files
/sra-recall decisions [query]    — Search only decisions
/sra-recall preferences [query]  — Search only preferences
/sra-recall domain [query]       — Search only domain-knowledge
/sra-recall recent               — Show last 10 learnings (sorted by date)
/sra-recall all                  — Full memory dump grouped by category
```

## Process

1. **Parse** — Extract category filter and search terms
2. **Search** — Read from `memory/decisions.md`, `memory/preferences.md`, `memory/domain-knowledge.md`
3. **Match** — Search titles, tags (with/without #), content, source fields
4. **Format Results**

```
## Learnings matching "[query]" ([count] found)

**[category]** [Title]
Tags: #tag1 #tag2 | Learned: YYYY-MM-DD
> [First sentence or two]
---
```

## Special Queries

- **`/sra-recall recent`** — Sort all entries by date, show last 10
- **`/sra-recall all`** — All learnings grouped by category
- **`/sra-recall meta`** — Everything tagged #meta
- **`/sra-recall voice`** — Everything tagged #voice
- **`/sra-recall show-summary`** — Everything about the Show/Hide toggle feature
- **`/sra-recall routing`** — Multi-agent routing decisions and domain knowledge

## No Results

```
No learnings found matching "[query]"
Try: broader terms, /sra-recall all, or /sra-recall recent
```
