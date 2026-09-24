/**
 * CLT Apex data class — copy and rename for your CLT.
 *
 * Naming conventions (load-bearing — these names match the LWC's __APEX_ENVELOPE_FIELD constant):
 *   Class:        <TypeName>Data         (PascalCase)
 *   Field:        <typeName>JSON         (lowerCamelCase + JSON suffix)
 *
 * Example for an LWC named `orderConfirmation`:
 *   Class:        OrderConfirmationData
 *   Field:        orderConfirmationJSON
 *
 * The @JsonAccess annotation lets the platform serialize/deserialize this between
 * the Flow and the LWC. The @AuraEnabled annotation is mandatory — without it,
 * the LWC's @api value receives the field as undefined.
 */
@JsonAccess(serializable='always' deserializable='always')
global with sharing class __TYPE_NAME_PASCAL__Data {
    @AuraEnabled global String __TYPE_NAME__JSON;
}
