---
name: sra-review-learnings
description: Review and process pending learnings in the SRA memory system. Use when processing auto-suggested learnings that are awaiting review in memory/pending.md. Supports store, edit, and delete actions.
tools: [Read, Write, Edit]
---

# SRA Review Learnings

Review pending learnings.

## Process

1. **Read** `memory/pending.md` and parse all entries
2. **If empty:** "No pending learnings. Add manually with `/sra-remember`."
3. **Display each pending item:**
   ```
   ## Pending Learnings ([count] items)

   ### 1. [category] "[Title]"
   Source: [Context] | Detected: [Date]
   > [Content]
   Tags: #tag1 #tag2
   → Store | Edit | Delete
   ```

4. **Process responses:**
   - `store all` — Move all to category files
   - `store 1, 3` — Store specific items
   - `delete 2` — Remove from pending
   - `edit 1: [modification]` — Update and keep in pending
   - Combined: `store 1, delete 2, edit 3: [mod]`

5. **Execute:**
   - Store: Remove from `memory/pending.md`, append to `memory/[category].md`
   - Delete: Remove from `memory/pending.md`
   - Edit: Update in `memory/pending.md`

6. **Confirm:**
   ```
   Processed [X] learnings:
   - Stored: [count] | Deleted: [count] | Edited: [count]
   Remaining pending: [count]
   ```
