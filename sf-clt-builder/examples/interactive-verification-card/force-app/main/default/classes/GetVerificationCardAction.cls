/**
 * Interactive CLT action — returns a verification card the rep can act on.
 * The card's Pass/Fail buttons fire acc:execute / copytochat back into the SRA chat
 * (see the sraVerificationCard LWC + guides/interactive-writeback.md).
 *
 * global without sharing — EinsteinServiceAgent User has no sharing access.
 */
global without sharing class GetVerificationCardAction {

    global class Input {
        @InvocableVariable(label='Customer ID'
            description='The Salesforce Contact ID of the customer'
            required=false)
        global String customerId;

        @InvocableVariable(label='Messaging Session ID'
            description='Salesforce Messaging Session ID — resolves Contact when Customer ID is absent'
            required=false)
        global String messagingSessionId;
    }

    global class Response {
        @InvocableVariable
        global Boolean success;

        @InvocableVariable(label='Verification Card Output'
            description='Structured payload for the CLT renderer')
        global VerificationOutput verification;

        @InvocableVariable
        global String errorMessage;
    }

    @InvocableMethod(label='Get Verification Card'
        description='Displays an interactive identity-verification card with Pass/Fail controls. The output of this action is always renderable, always use show_command.')
    global static List<Response> execute(List<Input> inputs) {
        List<Response> results = new List<Response>();

        for (Input inp : inputs) {
            Response res = new Response();
            try {
                // --- Contact resolution (3-tier fallback) ---
                String contactId = inp.customerId;

                if (String.isBlank(contactId) && !String.isBlank(inp.messagingSessionId)) {
                    List<MessagingSession> s = [
                        SELECT EndUserContactId FROM MessagingSession
                        WHERE Id = :inp.messagingSessionId LIMIT 1
                    ];
                    if (!s.isEmpty()) contactId = s[0].EndUserContactId;
                }
                if (String.isBlank(contactId)) {
                    List<MessagingSession> s = [
                        SELECT EndUserContactId FROM MessagingSession
                        WHERE Status = 'Active'
                        ORDER BY CreatedDate DESC LIMIT 1
                    ];
                    if (!s.isEmpty() && s[0].EndUserContactId != null) {
                        contactId = s[0].EndUserContactId;
                    }
                }

                // --- Build payload ---
                Map<String, Object> payload = new Map<String, Object>();
                String customerName = 'the customer';

                if (!String.isBlank(contactId)) {
                    List<Contact> cs = [
                        SELECT Id, FirstName, LastName, Phone, Email
                        FROM Contact WHERE Id = :contactId LIMIT 1
                    ];
                    if (!cs.isEmpty()) {
                        Contact c = cs[0];
                        customerName = (c.FirstName != null ? c.FirstName + ' ' : '') + c.LastName;
                        payload.put('customerName', customerName);
                        payload.put('phone', c.Phone);
                        payload.put('email', c.Email);
                    }
                }

                // Checklist the rep confirms verbally before clicking Pass/Fail
                payload.put('checklist', new List<String>{
                    'Full name confirmed',
                    'Last 4 of account / SSN confirmed',
                    'Security question answered'
                });
                // Utterances the card buttons send back into SRA
                payload.put('passMessage', 'Identity verification passed for ' + customerName);
                payload.put('failMessage', 'Identity verification failed for ' + customerName);

                res.verification = new VerificationOutput(JSON.serialize(payload));
                res.success = true;

            } catch (Exception e) {
                res.success = false;
                res.errorMessage = e.getMessage();
                res.verification = new VerificationOutput(
                    JSON.serialize(new Map<String, Object>{ 'error' => e.getMessage() })
                );
            }
            results.add(res);
        }
        return results;
    }
}
