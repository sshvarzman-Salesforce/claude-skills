/**
 * Interactive verification CLT — renders a checklist card and writes the
 * rep's verdict back into the SRA conversation.
 *
 * copytochat  → drops text into the chat input box (rep reviews/edits)
 * acc:execute → auto-sends text into chat history (agent responds)
 *
 * Requires: SRA panel + SRA in Dynamic Plan mode. See guides/interactive-writeback.md.
 */
import { LightningElement, api, track } from 'lwc';

export default class SraVerificationCard extends LightningElement {

    @api value;
    @track data = {};
    @track errorMessage = '';

    connectedCallback() {
        try {
            if (!this.value || !this.value.verificationJSON) {
                this.errorMessage = 'No data provided.';
                return;
            }
            const raw = this.value.verificationJSON;
            const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
            if (parsed.error) {
                this.errorMessage = parsed.error;
                return;
            }
            this.data = parsed;
        } catch (e) {
            console.error('sraVerificationCard parse error:', e);
            this.errorMessage = 'Error loading verification data.';
        }
    }

    get hasData() {
        return !this.errorMessage && this.data && Object.keys(this.data).length > 0;
    }
    get hasError() {
        return !!this.errorMessage;
    }
    get customerName() {
        return this.data.customerName || 'the customer';
    }
    get checklist() {
        return this.data.checklist || [];
    }

    // ---- Write-back ------------------------------------------------------

    postToChat(message) {
        this.dispatchEvent(new CustomEvent('acc:execute', {
            detail: { content: message },
            bubbles: true,
            composed: true
        }));
    }

    copyToChat(message) {
        this.dispatchEvent(new CustomEvent('copytochat', {
            detail: { content: message },
            bubbles: true,
            composed: true
        }));
    }

    handlePass() {
        this.postToChat(this.data.passMessage || 'Identity verification passed');
    }
    handleFail() {
        this.postToChat(this.data.failMessage || 'Identity verification failed');
    }
    handleDraftNote() {
        this.copyToChat('Verification pending — still need to confirm ');
    }
}
