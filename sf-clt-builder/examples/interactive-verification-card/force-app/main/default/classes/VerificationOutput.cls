/**
 * CLT DTO — single-JSON-field pattern.
 * Holds the serialized payload the sraVerificationCard LWC renders.
 */
@JsonAccess(serializable='always' deserializable='always')
global class VerificationOutput {

    @AuraEnabled
    global String verificationJSON;

    global VerificationOutput(String verificationJSON) {
        this.verificationJSON = verificationJSON;
    }

    global VerificationOutput() {
        this.verificationJSON = '';
    }
}
