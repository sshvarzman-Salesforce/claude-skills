/**
 * Messaging-Channel CLT LWC Template — write-back to the CUSTOMER composer
 *
 * Standard action = Edit (paste into the messaging composer to review/edit).
 * Post (send now) is provided but should be GATED behind explicit config.
 * See guides/messaging-composer-writeback.md for the full contract.
 *
 * Replace:
 *   {{ComponentClassName}} → e.g., PetReplySuggestionCard (PascalCase)
 *   {{dtoJsonField}}       → e.g., replyJSON (matches DTO's @AuraEnabled field)
 *   {{replyField}}         → the JSON key holding the draft text (e.g., suggestedReply)
 *
 * Rules (why this template is shaped this way):
 *   - The send TARGET is resolved CLIENT-SIDE from the focused console tab via
 *     c/replyRouting — NEVER from a messagingSessionId serialized in the DTO. A
 *     server-side "latest Active session" can point at a DIFFERENT customer, and a
 *     send has no undo. Server-side session resolution is reads-only.
 *   - Success is "did not reject" (!== false), never === true: sendTextMessage
 *     resolves undefined while genuinely delivering.
 *   - Once messaging is in play, do NOT fall back to the agent panel — that
 *     duplicates a message the customer already received.
 *   - Runs as the REP (with sharing on the controller is fine), unlike the CLT
 *     action class which must be `without sharing`.
 */
import { LightningElement, api, track } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { resolveMessagingSessionId, replyToCustomer } from 'c/replyRouting';

// Flip to true only when the customer accepts one-click auto-send to the customer.
const ENABLE_POST = false;

export default class {{ComponentClassName}} extends LightningElement {

    @api value;              // Platform passes the CLT DTO here
    @track data = {};
    @track errorMessage = '';
    busy = false;

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
    get showPost() {
        return ENABLE_POST;
    }

    // ---- Customer-conversation write-back -------------------------------

    /** STANDARD: paste the draft into the composer for the rep to edit, then send. */
    async handleEdit() {
        await this.deliver(/* immediate */ false,
            'Loaded into composer', 'Edit the reply, then send it yourself.', 'info');
    }

    /** GATED: send the draft immediately to the customer (no review step). */
    async handlePost() {
        await this.deliver(/* immediate */ true,
            'Reply sent', 'Your reply was posted to the customer.', 'success');
    }

    // ---- Shared delivery path -------------------------------------------

    async deliver(immediate, okTitle, okMsg, okVariant) {
        this.busy = true;
        try {
            const sessionId = await resolveMessagingSessionId();
            if (!sessionId) {
                this.toast('No live chat', 'Open the Messaging Session tab in the console first.', 'warning');
                return;
            }
            const ok = await replyToCustomer(sessionId, this.data.{{replyField}}, immediate);
            // Do NOT fall back to copytochat on failure here — that risks a duplicate send.
            this.toast(ok ? okTitle : 'Delivery failed',
                       ok ? okMsg : 'The composer did not accept the text. Try again from the composer.',
                       ok ? okVariant : 'error');
        } finally {
            this.busy = false;
        }
    }

    toast(title, message, variant) {
        this.dispatchEvent(new ShowToastEvent({ title, message, variant }));
    }
}
