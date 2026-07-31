---
name: sc-pdlc-audit
description: Service Cloud FY27 PDLC Release Audit Tool — audits Chad's skills, PRDs, and outputs against the org-wide Service Cloud PM PDLC resources site. Identifies duplicates, gaps, contribution opportunities, and alignment with org templates/tools. Use when checking what already exists org-wide before building something new, or when contributing back to the shared resource.
tools: [mcp__plugin_browser_browser__browser_navigate, mcp__plugin_browser_browser__browser_screenshot, mcp__plugin_browser_browser__browser_a11y_tree, mcp__plugin_browser_browser__browser_click, mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_google_google__docs_search, Read, Write]
---

# Service Cloud FY27 PDLC Release Audit Tool

> Audits Chad's AI toolkit against the org-wide Service Cloud PM PDLC resources.
> Identifies duplicates, gaps, contribution opportunities, and template alignment.

**Invocation:** `/sc-pdlc-audit` or "audit against PDLC site" or "what should I contribute to the PDLC site"

---

## The Org-Wide Resource

**Site:** https://git.soma.salesforce.com/pages/service-cloud/pm-fy27pdlc-releases/00-get-started/index.html

**Repo:** https://git.soma.salesforce.com/service-cloud/pm-fy27pdlc-releases

This is the Service Cloud PM team's shared resource site for FY27 PDLC releases. It contains:
- Templates (PRD, PBD, one-pager, etc.)
- Process guides (APDLC phases, inspection prep, etc.)
- Tools and automation references
- Shared skills and patterns
- Release planning resources

---

## What This Skill Does

### 1. Duplicate Check
Before building a new skill or tool, check the PDLC site:
- Does a shared template already exist for what I'm building?
- Is there an org-wide tool that does what my skill does?
- Has another PM already contributed something similar?

### 2. Contribution Audit
What from my toolkit should be contributed back:
- Skills that other PMs could use (generalized versions)
- Templates I've built that aren't in the shared site
- Process improvements I've documented
- Tools/automation patterns worth sharing

### 3. Alignment Check
Are my artifacts aligned with org standards:
- Do my PRDs match the org template structure?
- Am I following the correct APDLC phase gates?
- Are my naming conventions consistent with the shared site?

### 4. Gap Analysis
What does the org site have that I'm not using:
- Templates I should adopt
- Processes I'm not following
- Tools available that I haven't integrated

---

## Audit Workflow

1. **Navigate** the PDLC site via Browser MCP (requires auth)
2. **Catalog** what exists: templates, tools, guides, processes
3. **Cross-reference** against my skills (`~/.claude/skills/`), PRDs (`~/sra-prds/`), and outputs
4. **Report** findings in 4 categories:
   - Duplicates (I built something that exists org-wide)
   - Contributions (I have something the org should have)
   - Gaps (org has something I should adopt)
   - Alignment issues (my stuff deviates from org standards)

---

## Contribution Candidates (My Toolkit → Org)

Skills/tools from my toolkit that could generalize for all Service Cloud PMs:

| My Tool | Generalized Version | Value to Org |
|---------|-------------------|--------------|
| sf-prd-writer | Generic PRD writer with Slack research | Any PM could use for their product area |
| pbd-auditor | Generic PBD audit checklist | Catch completeness gaps before inspection |
| sra-test-case-writer | Generic test case generator | Test cases from PRD requirements for any feature |
| pm-pretotype | Already generic | Concept validation for any PM |
| sra-expert pattern | Template: build-your-own-expert | Each PM builds their own domain knowledge base |

---

## When to Run This Audit

- Before building a new skill → "Does this already exist org-wide?"
- After building something useful → "Should I contribute this back?"
- Before PDLC phase gates → "Am I using the right templates?"
- Quarterly → "What's new on the org site that I should adopt?"

---

## Related

- **sf-prd-writer** — references this skill for template alignment checks
- **APDLC Tools & Docs page** — https://git.soma.salesforce.com/pages/chad-goldsmith/APDLC-Tools-and-Docs/
- **Claude Skills repo** — https://git.soma.salesforce.com/chad-goldsmith/claude-skills
