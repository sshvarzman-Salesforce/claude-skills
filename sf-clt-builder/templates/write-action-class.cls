/**
 * Write-action template — NO CLT, NO show_command.
 *
 * Reserve Lightning Types for reads. A write action reports a result in plain
 * scalars (including a `confirmation` string the user can read aloud). Cards
 * trigger these with `acc:execute` utterances (SRA) or conversational follow-up.
 *
 * Replace:
 *   {{ActionClassName}}   → e.g., StartEquipmentReplacementAction
 *   {{ActionLabel}}       → e.g., Start Equipment Replacement
 *   {{ActionDescription}} → when to call it; include "Use this only after the
 *                           user has confirmed..." for destructive writes
 *   {{InputFields}}       → additional @InvocableVariable inputs
 *   {{WriteLogic}}        → DML + field mapping
 *
 * Sharing is surface-specific — see guides/surfaces.md. Default below is SRA.
 * isConfirmationRequired on the GenAiFunction should be true for record-creating
 * actions. NEVER throw — return success=false + errorMessage + a confirmation
 * the agent can speak.
 */
global without sharing class {{ActionClassName}} {

    global class Input {
        @InvocableVariable(label='Record ID'
            description='The Salesforce record this write targets'
            required=false)
        global String recordId;

        // {{InputFields}}
    }

    global class Response {
        @InvocableVariable
        global Boolean success;

        @InvocableVariable(label='Confirmation'
            description='Plain-language confirmation the user can read aloud')
        global String confirmation;

        // Lift 2–3 scalars the planner needs after the write (ids, names, dates).
        // These are isDisplayable:false / isUsedByPlanner:true on the GenAi schema.
        // {{PassthroughFields}}

        @InvocableVariable
        global String errorMessage;
    }

    @InvocableMethod(label='{{ActionLabel}}'
        description='{{ActionDescription}} Use this only after the user has confirmed they want to proceed. Do not call this action to display a card.')
    global static List<Response> execute(List<Input> inputs) {
        List<Response> results = new List<Response>();

        for (Input inp : inputs) {
            Response res = new Response();
            try {
                // {{WriteLogic}}
                // Example:
                // if (String.isBlank(inp.recordId)) {
                //     res.success = false;
                //     res.errorMessage = 'Could not identify the record to update.';
                //     res.confirmation = 'I could not identify which record to update. Please confirm the id.';
                //     results.add(res);
                //     continue;
                // }
                // update new SomeObject(Id = inp.recordId, Status = 'In Progress');
                // res.success = true;
                // res.confirmation = 'The update is in progress.';

                res.success = true;
                res.confirmation = 'Done.';
            } catch (Exception e) {
                res.success = false;
                res.errorMessage = e.getMessage();
                res.confirmation = 'I could not complete that update: ' + e.getMessage();
            }
            results.add(res);
        }
        return results;
    }
}
