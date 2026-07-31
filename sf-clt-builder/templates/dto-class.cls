/**
 * CLT DTO Template — Single-JSON-Field Pattern
 *
 * Replace:
 *   {{ClassName}}  → e.g., CustomerProfileOutput
 *   {{fieldName}}  → e.g., profileJSON (convention: <purpose>JSON)
 *
 * Rules:
 *   - ONE @AuraEnabled String field (NOT @InvocableVariable)
 *   - global access modifier on class and field
 *   - @JsonAccess required for platform serialization
 *   - Two constructors: parameterized + no-arg
 */
@JsonAccess(serializable='always' deserializable='always')
global class {{ClassName}} {

    @AuraEnabled
    global String {{fieldName}};

    global {{ClassName}}(String {{fieldName}}) {
        this.{{fieldName}} = {{fieldName}};
    }

    global {{ClassName}}() {
        this.{{fieldName}} = '';
    }
}
