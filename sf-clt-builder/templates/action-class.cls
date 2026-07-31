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
 *   - global without sharing (EinsteinServiceAgent User has no sharing access)
 *   - @InvocableMethod description MUST include show_command language
 *   - All Input fields: required=false (Agent Builder resolves them)
 *   - Always include messagingSessionId as fallback Contact resolution
 *   - Error case: return valid DTO with {"error": "..."} — never null
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

        @InvocableVariable(label='{{ActionLabel}} Output'
            description='Structured payload for the CLT renderer')
        global {{DtoClassName}} {{dtoFieldName}};

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
                    if (!sessions.isEmpty()) {
                        resolvedContactId = sessions[0].EndUserContactId;
                    }
                }

                // Tier 3: Most recent active session fallback
                if (String.isBlank(resolvedContactId)) {
                    List<MessagingSession> sessions = [
                        SELECT EndUserContactId FROM MessagingSession
                        WHERE Status = 'Active'
                        ORDER BY CreatedDate DESC LIMIT 1
                    ];
                    if (!sessions.isEmpty() && sessions[0].EndUserContactId != null) {
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

                res.{{dtoFieldName}} = new {{DtoClassName}}(JSON.serialize(payload));
                res.success = true;

            } catch (Exception e) {
                res.success = false;
                res.errorMessage = e.getMessage();
                res.{{dtoFieldName}} = new {{DtoClassName}}(
                    '{"error":"' + e.getMessage().replace('"', '\\"') + '"}');
            }
            results.add(res);
        }
        return results;
    }
}
