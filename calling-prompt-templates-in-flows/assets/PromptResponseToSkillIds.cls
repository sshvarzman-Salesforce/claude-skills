/**
 * Tiny invocable that turns a prompt-template response into a text collection.
 *
 * Design: the routing flow calls the OUT-OF-THE-BOX prompt template action
 * ("Lead to Skill Matching"), which returns its answer as a single string
 * (promptResponse) — the matched Omni-Channel Skill Ids, comma-separated.
 * That string is not loopable in Flow, so this class does exactly one job:
 * split it into a List<String> the flow can loop over to build the
 * SkillRequirement collection.
 *
 * It is deliberately defensive: it splits on commas / whitespace / newlines
 * and keeps only tokens shaped like a Salesforce Id (15 or 18 alphanumeric
 * chars), so any stray model text (labels, prose, code fences) can never leak
 * into the loop and blow up the downstream Get_Skill lookup.
 */
public with sharing class PromptResponseToSkillIds {

    public class Request {
        @InvocableVariable(required=true label='Prompt Response Text'
            description='The raw text returned by the Lead to Skill Matching prompt template (comma-separated Skill Ids).')
        public String promptResponse;
    }

    public class Result {
        @InvocableVariable(label='Skill Ids')
        public List<String> skillIds;
    }

    @InvocableMethod(label='Prompt Response to Skill Ids'
        description='Converts the comma-separated Skill Id text from the prompt template into a text collection to loop on.')
    public static List<Result> convert(List<Request> requests) {
        List<Result> results = new List<Result>();
        for (Request req : requests) {
            Result res = new Result();
            res.skillIds = parseIds(req == null ? null : req.promptResponse);
            results.add(res);
        }
        return results;
    }

    /**
     * Split the model output into clean Skill Ids. Tolerant of commas, spaces
     * and newlines; keeps only tokens shaped like a Salesforce Id (15/18 alnum).
     */
    @TestVisible
    private static List<String> parseIds(String text) {
        List<String> ids = new List<String>();
        if (String.isBlank(text)) {
            return ids;
        }
        for (String part : text.split('[,\\s]+')) {
            String v = (part == null) ? '' : part.trim();
            if (String.isNotBlank(v)
                    && (v.length() == 15 || v.length() == 18)
                    && v.isAlphanumeric()) {
                ids.add(v);
            }
        }
        return ids;
    }
}
