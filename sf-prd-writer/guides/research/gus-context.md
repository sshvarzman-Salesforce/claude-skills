# GUS Context (Optional)

When research depth is **Full**, query GUS for relevant context.

1. **Search for existing epics/stories** related to the feature using `query_gus_records`:
   * Search for the feature name or related keywords in Work item subjects
   * Look for existing epics under the Service Rep Assistant product tag
   * Check for bugs or known issues that are prerequisites or blockers

2. **Pull context from GUS into the PRD:**
   * If an epic exists → add its W- number to the Administrative section and Dependencies
   * If related bugs exist → reference them in Risks & Edge Cases
   * If sprint/velocity context exists → inform the Rollout Strategy section

3. **After PRD creation (optional, user-initiated):** When the user asks to "create the GUS epic" — use the [GUS Epic guide](../reporting/gus-epic.md) to generate the epic description `.md` file. The `dxmcp-gus` tool is not available in this environment, so GUS items cannot be created directly. The workflow is: generate the content → user pastes into GUS → user shares the GUS URL → skill updates the link in the file.

**Do NOT auto-create GUS items.** GUS epic generation is user-initiated. Only run when explicitly asked.
