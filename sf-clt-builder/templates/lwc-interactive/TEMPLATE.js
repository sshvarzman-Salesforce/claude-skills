/**
 * Interactive CLT LWC Template — write-back is SURFACE-SPECIFIC.
 *
 *   SRA sidebar:        copytochat / acc:execute (undocumented; SRA panel + Dynamic Plan)
 *   Employee LEX:       lightning/accApi execute() — do not assume copytochat works
 *   Enhanced Chat v2:   this.configuration?.util.sendTextMessage(...)
 *   Agentforce Cowork:  no-op until a write-back is verified — NavigationMixin only
 *
 * See guides/surfaces.md and guides/interactive-writeback.md.
 *
 * Replace:
 *   {{ComponentClassName}} → e.g., PetVerificationCard (PascalCase)
 *   {{dtoJsonField}}       → e.g., verificationJSON (matches DTO's @AuraEnabled field)
 *   {{dataFields}}         → getters for template binding
 */
import { LightningElement, api, track } from 'lwc';

export default class {{ComponentClassName}} extends LightningElement {

    @api value;
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
        // Resolve host context OUTSIDE the parse try/catch so a messaging miss
        // can never blank the card. On SRA, import resolveConversationContext
        // from the reply-routing module and stash it on this.context here.
    }

    get hasData() {
        return !this.errorMessage && this.data && Object.keys(this.data).length > 0;
    }
    get hasError() {
        return !!this.errorMessage;
    }

    /**
     * Route a string to whichever write-back the host actually supports.
     * Returns true when something accepted the message, false when the surface
     * has no write-back (Cowork) or the call was refused.
     */
    async sendOnSurface(message, { autoSend = true } = {}) {
        if (!message) {
            return false;
        }

        // Enhanced Chat v2 injects configuration.util. LEX desktop does not.
        const chatUtil = this.configuration && this.configuration.util;
        if (chatUtil && typeof chatUtil.sendTextMessage === 'function') {
            try {
                await chatUtil.sendTextMessage(message);
                return true;
            } catch (e) {
                return false;
            }
        }

        // SRA panel (undocumented). No-ops on Employee LEX / ACC / Cowork.
        this.dispatchEvent(new CustomEvent(autoSend ? 'acc:execute' : 'copytochat', {
            detail: { content: message },
            bubbles: true,
            composed: true
        }));
        return true;
    }

    /** Drop text into the SRA chat input box for the rep to review/edit. */
    copyToChat(message) {
        return this.sendOnSurface(message, { autoSend: false });
    }

    /** Auto-send text into SRA chat history as if the rep typed it. */
    postToChat(message) {
        return this.sendOnSurface(message, { autoSend: true });
    }

    handleCopy(event) {
        this.copyToChat(event.currentTarget.dataset.message);
    }
    handlePost(event) {
        this.postToChat(event.currentTarget.dataset.message);
    }

    // {{dataFields}} — add getters for each field the template binds to
}
