/**
 * Minimal test for 75% Apex coverage. CLT data classes are simple wrappers,
 * so a single instantiation + assertion is enough for deploy validation.
 */
@isTest
private class __TYPE_NAME_PASCAL__DataTest {
    @isTest
    static void roundTrip() {
        __TYPE_NAME_PASCAL__Data d = new __TYPE_NAME_PASCAL__Data();
        d.__TYPE_NAME__JSON = '{"title":"test"}';
        System.assertEquals('{"title":"test"}', d.__TYPE_NAME__JSON);
    }
}
