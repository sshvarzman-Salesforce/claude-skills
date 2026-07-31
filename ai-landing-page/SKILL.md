---
name: ai-landing-page
description: Manage Chad's AI tools landing page (APDLC-Tools-and-Docs). Add cards, update metrics, edit detail panels, and push changes live. Use when asked to "update the landing page", "add X to my page", or "update the page with today's work".
tools: [Bash, Read, Write, Edit]
---

# AI Landing Page — APDLC-Tools-and-Docs

> Manages the single-page app at https://git.soma.salesforce.com/pages/chad-goldsmith/APDLC-Tools-and-Docs/
> that showcases how Chad uses AI in product development.

## Location

- **Local repo:** `~/APDLC-Tools-and-Docs/`
- **Remote:** `git@git.soma.salesforce.com:chad-goldsmith/APDLC-Tools-and-Docs.git`
- **File:** `index.html` (everything is in this one file — styles, markup, JS)
- **Deploys:** GitHub Pages — push to `master` and it's live within ~30 seconds

## When to trigger

- User says "update the landing page", "add X to the page", "update my page"
- User asks to add a new tool/skill/capability
- User asks to update metrics (skill count, PRD count, etc.)
- Called by the `go-to-bed` skill during end-of-day wrap-up

## Page Structure

The page is a single HTML file with these sections (top to bottom):

### 1. Header
```html
<header class="header">
    <h1>How Chad Goldsmith Uses AI in Product Development</h1>
    <p>...</p>
    <span class="subtitle">APDLC Tools & Docs — SRA PM — Salesforce</span>
</header>
```

### 2. Metrics Bar (4 counters)
```html
<div class="metrics-bar">
    <div class="metric-item" onclick="showDetail('skills')">
        <div class="metric-value">14</div>
        <div class="metric-label">Active Skills</div>
    </div>
    <!-- Patent Filing, PRDs → Epics, Channels Monitored -->
</div>
```
Update these numbers when skills are added, PRDs are written, etc.

### 3. Card Grid (3-column hub)
Each card:
```html
<div class="card" data-category="demos" data-id="demos" onclick="showDetail('demos')">
    <span class="card-icon">🚀</span>
    <div class="card-title">Demo Engineering</div>
    <div class="card-desc">Short description...</div>
    <div class="card-stats">
        <span class="stat">CLT Builder</span>
        <span class="stat">Pet Travel</span>
        <span class="stat">Universal Skill</span>
    </div>
</div>
```
- `data-id` must match the detail panel ID
- `card-stats` has 3 short keyword pills
- `onclick` calls `showDetail('id')`

### 4. Connection Flows (animated pipelines)
```html
<div class="connection-flow" onclick="showDetail('flow-demo')">
    <span class="flow-node purple">PRD</span>
    <span class="flow-arrow">→</span>
    <span class="flow-node green">sf-demo-skills</span>
    ...
</div>
```
Node color classes: `blue`, `green`, `purple`, `yellow`, `pink`, `cyan`

### 5. Impact Table (Before/After)
Shows time savings and "wouldn't happen without AI" rows.

### 6. Detail Panels (hidden by default, shown on card click)
```html
<div class="detail-panel" id="detail-skills">
    <div class="detail-header">
        <h2>🛠️ Claude Code Skills</h2>
        <button class="detail-close" onclick="hideDetail()">✕</button>
    </div>
    <div class="detail-body">
        <!-- Rich content: h3, ul/li, code, .flow-diagram blocks -->
    </div>
</div>
```

### 7. Learning of the Day (single featured insight)
```html
<!-- Learning of the Day -->
<div>
    <span id="lotd-date">Jun 23, 2026</span>
    <p id="lotd-text">The learning text...</p>
    <span id="lotd-tag-1">Tag 1</span>
    <span id="lotd-tag-2">Tag 2</span>
    <span id="lotd-tag-3">Tag 3</span>
</div>
```
Updated nightly by the `go-to-bed` skill. Pick the single most interesting AI-related learning.

### 8. What's New Streaming Ticker
A JS-powered ticker that shows 5 entries at a time, auto-scrolls every 8s. Entries are in the `tickerItems` array in the script block. Add new entries at the TOP of the array (newest first).

### 9. JavaScript (bottom of file)
- `showDetail(id)` — shows `#detail-{id}`, hides others
- `hideDetail()` — hides all panels
- Particle animation for background
- Ticker logic (auto-scroll, pause, prev/next)

## How to Add a New Card

1. Add the card markup in the `.hub` grid (maintain 3-column layout)
2. Create a matching detail panel with `id="detail-{data-id}"`
3. If it connects to existing flows, update or add a connection flow
4. Update relevant metric counters

## How to Update Metrics

Find the `.metrics-bar` section and update the `metric-value` div contents:
- **Active Skills** — count of skills in `~/.claude/skills/`
- **Patent Filing** — number of patents filed
- **PRDs → Epics** — count of PRDs in `~/sra-prds/`
- **Channels Monitored** — Caturday channel count

## Style Guidelines

- Keep descriptions concise (1-2 sentences per card)
- Use emoji for card icons (consistent with existing)
- Stats pills should be 1-2 words each (3 per card)
- Detail panels can be rich (headers, lists, code blocks, flow diagrams)
- Don't change the overall color scheme (dark theme, indigo/purple accents)
- Flow diagram blocks use `.highlight` (blue), `.accent` (green), `.warn` (yellow)

## Push Workflow

```bash
cd ~/APDLC-Tools-and-Docs
git add index.html
git commit -m "descriptive message"
git push
```

Live within ~30 seconds at the pages URL.

## Rules

- ALWAYS read the current `index.html` before editing (it may have been updated outside this tool)
- NEVER remove existing cards without explicit user request
- NEVER change the page's overall structure/layout/theme
- Keep detail panel content factual — these are showcased to colleagues
- When updating metrics, verify the actual count (ls skills dir, count PRDs, etc.)
- If unsure whether something belongs on the page, ask — this is externally visible
