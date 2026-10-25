/**
 * Card Kit action template — a LIST card whose rows drill into a DETAIL card.
 * Pairs with templates/card-kit-builder.cls and templates/lwc-card-kit/.
 *
 * Replace:
 *   {{ActionClassName}} → e.g., AcmeGetOrderHistoryAction
 *   {{ActionLabel}}     → e.g., Acme SRA - Get Order History   (the label IS the button contract)
 *   {{DetailLabel}}     → e.g., Acme SRA - Get Order Details   (the action the row button runs)
 *   {{CardBuilder}}     → e.g., AcmeCard
 *   {{DtoClassName}}    → e.g., AcmeOrderHistoryOutput (single @AuraEnabled String cardJSON)
 *   {{SummaryLabel}}    → e.g., Acme SRA - Get Account Summary (a card-level button's target)
 *   {{QueryLogic}}      → your SOQL, scoped to demo-owned records
 *   {{DemoScopeFilter}} → a demo-owned filter for the default record, e.g. Demo_Key__c = 'ACME-GOLDEN'
 *
 * Response contract (every card action in the kit):
 *   success        — Boolean, planner-visible (keeps the planner from apologising)
 *   <card>         — the DTO: isDisplayable true, isUsedByPlanner false
 *   passthroughs   — small facts the planner branches on (counts, flags), planner-visible
 *   plannerSummary — ONE line of real numbers, planner-visible, so the plan steps and the
 *                    rep-facing reply quote the data instead of inventing it
 *   errorMessage   — planner-visible; the card still renders with {"error": …}
 * Never throw: a thrown exception produces no output, so no card.
 *
 * Inputs: the record the card is for is resolved HERE (context, record Id, or a demo
 * default), so the action can fire with zero inputs the moment the conversation calls
 * for it. Inputs exist only for buttons that name a record (see guides/next-action-buttons.md).
 */
global without sharing class {{ActionClassName}} {

    global class Input {
        @InvocableVariable(label='Account ID'
            description='The Account record Id from the card button that asked for this card. Optional; defaults to the customer on this conversation.'
            required=false)
        global String accountId;

        @InvocableVariable(label='Record ID'
            description='The VoiceCall, Case or MessagingSession the rep is working. Optional.'
            required=false)
        global String recordId;
    }

    global class Response {
        @InvocableVariable(label='Success' description='True when the card was built.')
        global Boolean success;

        @InvocableVariable(label='Order History Card' description='Structured payload for the card renderer.')
        global {{DtoClassName}} card;

        @InvocableVariable(label='Order Count' description='Number of orders on the card.')
        global Integer orderCount;

        @InvocableVariable(label='Planner Summary' description='One-line factual summary of what the card shows.')
        global String plannerSummary;

        @InvocableVariable(label='Error Message' description='Error detail when the card could not be built.')
        global String errorMessage;
    }

    @InvocableMethod(label='{{ActionLabel}}'
        description='Shows the order history card: every order with its status and a Details button. The output of this action is always renderable, always use show_command.')
    global static List<Response> execute(List<Input> inputs) {
        List<Response> out = new List<Response>();
        for (Input i : inputs) out.add(build(i));
        return out;
    }

    private static Response build(Input i) {
        Response r = new Response();
        try {
            Id accountId = resolveAccount(i);
            Account a = [SELECT Id, Name FROM Account WHERE Id = :accountId];
            List<Order> orders = [SELECT Id, OrderNumber, Status, TotalAmount, EffectiveDate
                                  FROM Order WHERE AccountId = :accountId ORDER BY EffectiveDate DESC LIMIT 10]; // {{QueryLogic}}

            List<Object> rows = new List<Object>();
            Decimal total = 0;
            for (Order o : orders) {
                total += o.TotalAmount == null ? 0 : o.TotalAmount;
                String state = o.Status == 'Activated' ? 'ok' : 'warn';
                rows.add({{CardBuilder}}.row('Order ' + o.OrderNumber, {{CardBuilder}}.day(o.EffectiveDate),
                    {{CardBuilder}}.money(o.TotalAmount), o.Status, state,
                    'Details', {{CardBuilder}}.runFor('{{DetailLabel}}', 'the single order ' + o.OrderNumber + ' with record Id ' + o.Id)));
            }

            {{CardBuilder}} card = new {{CardBuilder}}('navy', 'Order history', a.Name, orders.size() + ' orders · ' + {{CardBuilder}}.money(total))
                .icon('standard:orders');
            card.verdict(orders.isEmpty() ? 'No orders on this account yet.' : orders.size() + ' recent orders, newest first.',
                orders.isEmpty() ? 'info' : 'ok');
            card.block('stats', null, new List<Object>{
                {{CardBuilder}}.stat('Orders', String.valueOf(orders.size()), 'last 10', 'info'),
                {{CardBuilder}}.stat('Total', {{CardBuilder}}.money(total), 'all statuses', 'info')
            });
            card.block('list', 'Recent orders', rows);
            card.reco('Open the order the customer is asking about.');
            card.talkTrack('I can see your recent orders here. Which one are you calling about?');
            card.action('Account summary', {{CardBuilder}}.runFor('{{SummaryLabel}}', a.Name + ' (account Id ' + a.Id + ')'), 'execute');
            card.action('Copy talk track', null, 'copy');

            r.card = new {{DtoClassName}}(card.toJson());
            r.orderCount = orders.size();
            r.plannerSummary = orders.size() + ' orders on ' + a.Name + ' totalling ' + {{CardBuilder}}.money(total) + '.';
            r.success = true;
        } catch (Exception e) {
            r.success = false;
            r.errorMessage = e.getMessage();
            r.card = new {{DtoClassName}}({{CardBuilder}}.errorJson('Could not load the order history: ' + e.getMessage()));
        }
        return r;
    }

    /** Button Id first, then the record the rep is on, then the demo default. */
    private static Id resolveAccount(Input i) {
        if (i != null && String.isNotBlank(i.accountId)) {
            try { return Id.valueOf(i.accountId.trim()); } catch (Exception e) { /* not an Id: fall through */ }
        }
        // Resolve from i.recordId (VoiceCall / Case / MessagingSession) here if the surface passes it.
        return [SELECT Id FROM Account WHERE {{DemoScopeFilter}} ORDER BY CreatedDate LIMIT 1].Id;
    }
}
