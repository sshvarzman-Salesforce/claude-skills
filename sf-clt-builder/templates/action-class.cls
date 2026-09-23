/**
 * CLT Action Class Template
 *
 * Replace:
 *   {{ActionClassName}}   → e.g., GetCustomerProfileAction
 *   {{ActionLabel}}       → e.g., Get Customer Profile
 *   {{ActionDescription}} → e.g., Retrieves customer loyalty tier, pet name, and seat preference.
 *   {{DtoClassName}}      → e.g., CustomerProfileOutput
 *   {{dtoFieldName}}      → e.g., profile (the Response field name)
 *   {{dtoJsonField}}      → e.g., profileJSON (the DTO's @AuraEnabled String field)
 *   {{InputFields}}       → Replace with actual input @InvocableVariable declarations
 *   {{QueryLogic}}        → Replace with actual SOQL + payload building logic
 *
 * Rules:
 *   - Sharing is SURFACE-SPECIFIC (see guides/surfaces.md):
 *       SRA / EinsteinServiceAgent → global without sharing (that user has no sharing)
 *       Employee Agent / Cowork    → with sharing unless the run-as user is proven bare
 *   - @InvocableMethod description MUST include show_command language
 *   - All Input fields: required=false (Agent Builder resolves them)
 *   - On SRA / messaging demos: include messagingSessionId + the three-tier Contact ladder
 *     (READS only — never use the ladder to choose a send target)
 *   - NEVER throw. Every failure path returns a valid DTO carrying {"error": "..."}
 *     so the LWC can render an error state — a thrown exception produces no output
 *     at all, so the card cannot render and the user just sees a generic failure.
 *   - Scope every SOQL query to a demo-owned field so a shared org's unrelated
 *     records can't surface in the conversation
 *   - Format dates/defaults in Apex before serializing; keep the LWC a pure renderer
 */
global without sharing class {{ActionClassName}} {

    global class Input {
        @InvocableVariable(label='Customer ID'
            description='The Salesforce Contact ID of the customer'
            required=false)
        global String customerId;

        @InvocableVariable(label='Messaging Session ID'
            description='The Salesforce Messaging Session ID — used to resolve Contact when Customer ID is not available'
            required=false)
        global String messagingSessionId;

        // {{InputFields}} — add additional inputs here
    }

    global class Response {
        @InvocableVariable
        global Boolean success;

        // @InvocableVariable is REQUIRED here. It is what declares the DTO as an
        // action output. (Inside the DTO, the String field is @AuraEnabled only.)
        @InvocableVariable(label='{{ActionLabel}} Output'
            description='Structured payload for the CLT renderer')
        global {{DtoClassName}} {{dtoFieldName}};

        // Flat passthroughs — lift the 2-3 scalars the planner needs to chain a
        // follow-up action, so it never has to re-parse the card JSON. Leave these
        // UNfiltered in Agent Builder; keep the card output filtered. Add sparingly:
        // every unfiltered output is extra reasoning context.
        // {{PassthroughFields}}
        // e.g. @InvocableVariable global String faultyDeviceId;

        @InvocableVariable
        global String errorMessage;
    }

    @InvocableMethod(label='{{ActionLabel}}'
        description='{{ActionDescription}} The output of this action is always renderable, always use show_command.')
    global static List<Response> execute(List<Input> inputs) {
        List<Response> results = new List<Response>();

        for (Input inp : inputs) {
            Response res = new Response();
            try {
                // --- Contact Resolution (3-tier fallback) ---
                String resolvedContactId = inp.customerId;

                // Tier 2: Resolve via MessagingSession
                if (String.isBlank(resolvedContactId)
                    && !String.isBlank(inp.messagingSessionId)) {
                    List<MessagingSession> sessions = [
                        SELECT EndUserContactId FROM MessagingSession
                        WHERE Id = :inp.messagingSessionId LIMIT 1
                    ];
                    if (!sessions.isEmpty() && sessions[0].EndUserContactId != null) {
                        resolvedContactId = sessions[0].EndUserContactId;
                    }
                }

                // Tier 3: Most recent active session that actually HAS a contact.
                // Filter on EndUserContactId in the WHERE clause, not after the query:
                // if the newest active session has a null contact, filtering afterwards
                // returns nothing and the card fails, instead of falling through to the
                // newest session that does have one.
                if (String.isBlank(resolvedContactId)) {
                    List<MessagingSession> sessions = [
                        SELECT EndUserContactId FROM MessagingSession
                        WHERE Status = 'Active' AND EndUserContactId != NULL
                        ORDER BY CreatedDate DESC LIMIT 1
                    ];
                    if (!sessions.isEmpty()) {
                        resolvedContactId = sessions[0].EndUserContactId;
                    }
                }

                // --- Build Payload ---
                Map<String, Object> payload = new Map<String, Object>();

                // {{QueryLogic}} — replace with actual SOQL + field mapping
                // Example:
                // Contact c = [SELECT Id, FirstName, LastName FROM Contact
                //              WHERE Id = :resolvedContactId LIMIT 1];
                // payload.put('customerName', c.FirstName + ' ' + c.LastName);

                // Soft failures (no contact resolved, no records found) go into the
                // payload as 'error' so the card still renders an error state:
                //   if (String.isBlank(resolvedContactId)) {
                //       payload.put('error', 'No customer could be resolved for this conversation.');
                //   }

                res.{{dtoFieldName}} = new {{DtoClassName}}(JSON.serialize(payload));
                res.success = !payload.containsKey('error');

            } catch (Exception e) {
                // Serialize the error with JSON.serialize — never hand-build the JSON
                // string. A message containing a quote, backslash, or newline breaks
                // manual escaping, the LWC's JSON.parse then throws, and the error
                // state itself fails to render.
                res.success = false;
                res.errorMessage = e.getMessage();
                res.{{dtoFieldName}} = new {{DtoClassName}}(
                    JSON.serialize(new Map<String, Object>{ 'error' => e.getMessage() })
                );
            }
            results.add(res);
        }
        return results;
    }
}
