@isTest
private class PromptResponseToSkillIdsTest {

    @isTest
    static void convertsCommaSeparatedIds() {
        PromptResponseToSkillIds.Request req = new PromptResponseToSkillIds.Request();
        req.promptResponse = '0C5gL0000005PgwSAE,0C5gL0000005Ph4SAE,0C5gL0000005nrJSAQ';

        List<PromptResponseToSkillIds.Result> results =
            PromptResponseToSkillIds.convert(new List<PromptResponseToSkillIds.Request>{ req });

        System.assertEquals(1, results.size(), 'One result per request');
        System.assertEquals(3, results[0].skillIds.size(), 'All three Ids parsed');
        System.assertEquals('0C5gL0000005PgwSAE', results[0].skillIds[0]);
        System.assertEquals('0C5gL0000005nrJSAQ', results[0].skillIds[2]);
    }

    @isTest
    static void tolerantOfWhitespaceNewlinesAndStrayText() {
        PromptResponseToSkillIds.Request req = new PromptResponseToSkillIds.Request();
        // Stray prose, newlines, spaces and a too-short token must all be dropped.
        req.promptResponse = 'Here are the ids:\n 0C5gL0000005PgwSAE , 0C5gL0000005Ph4SAE\nabc123';

        List<PromptResponseToSkillIds.Result> results =
            PromptResponseToSkillIds.convert(new List<PromptResponseToSkillIds.Request>{ req });

        System.assertEquals(2, results[0].skillIds.size(),
            'Only the two Id-shaped tokens survive; prose and short tokens dropped');
        System.assertEquals('0C5gL0000005PgwSAE', results[0].skillIds[0]);
        System.assertEquals('0C5gL0000005Ph4SAE', results[0].skillIds[1]);
    }

    @isTest
    static void handlesBlankAndNull() {
        PromptResponseToSkillIds.Request blankReq = new PromptResponseToSkillIds.Request();
        blankReq.promptResponse = '   ';
        PromptResponseToSkillIds.Request nullReq = new PromptResponseToSkillIds.Request();
        nullReq.promptResponse = null;

        List<PromptResponseToSkillIds.Result> results =
            PromptResponseToSkillIds.convert(new List<PromptResponseToSkillIds.Request>{ blankReq, nullReq });

        System.assertEquals(2, results.size());
        System.assertEquals(0, results[0].skillIds.size(), 'Blank -> empty list');
        System.assertEquals(0, results[1].skillIds.size(), 'Null -> empty list');
    }
}
