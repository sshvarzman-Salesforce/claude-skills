/**
 * CLT LWC Template
 *
 * Replace:
 *   {{ComponentClassName}} → e.g., PetCustomerProfileCard (PascalCase)
 *   {{dtoJsonField}}       → e.g., profileJSON (matches the DTO's @AuraEnabled field name)
 *   {{dataFields}}         → Replace with actual getter methods for template binding
 *
 * Rules:
 *   - @api value receives the entire DTO object from the platform
 *   - Parse this.value.<dtoJsonField> in connectedCallback()
 *   - Always handle: missing value, missing field, parse error, data.error
 *   - Never throw — render an error state instead
 */
import { LightningElement, api, track } from 'lwc';

export default class {{ComponentClassName}} extends LightningElement {

    @api value;          // Platform passes the CLT DTO here
    @track data = {};
    @track errorMessage = '';

    connectedCallback() {
        try {
            if (!this.value || !this.value.{{dtoJsonField}}) {
                this.errorMessage = 'No data provided.';
                return;
            }

            const raw = this.value.{{dtoJsonField}};
            const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;

            if (parsed.error) {
                this.errorMessage = parsed.error;
                return;
            }

            this.data = parsed;
        } catch (e) {
            console.error('{{ComponentClassName}} parse error:', e);
            this.errorMessage = 'Error loading data.';
        }
    }

    get hasData() {
        return !this.errorMessage && this.data && Object.keys(this.data).length > 0;
    }

    get hasError() {
        return !!this.errorMessage;
    }

    // {{dataFields}} — add getters for each field the template binds to
    // Example:
    // get customerName() {
    //     return this.data.customerName || '—';
    // }
}
