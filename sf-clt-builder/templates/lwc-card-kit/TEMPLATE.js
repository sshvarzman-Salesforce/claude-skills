import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

const STATE_ICON = {
    ok: 'utility:success',
    warn: 'utility:warning',
    fault: 'utility:error',
    info: 'utility:info'
};

// Header icon when Apex sends none (data.icon unset). Theme is a legacy hint only; it never colours the header.
const THEME_ICON = {
    navy: 'standard:account',
    teal: 'standard:approval',
    red: 'standard:report',
    amber: 'standard:currency'
};

/**
 * Card Kit renderer: ONE LWC for every card on an Agentforce surface (verified on the SRA panel).
 * Apex builds a typed payload with the card builder (templates/card-kit-builder.cls) and
 * serializes it into value.{{dtoJsonField}}; this component only lays it out.
 * Design rules and the payload shape: guides/card-design-system.md.
 *
 * Buttons (guides/next-action-buttons.md):
 *   kind 'execute' — sends Apex's prepared instruction ("Run the <action label> action for …
 *                    with record Id …. Show only that card; …") to the assistant chat, so the
 *                    planner runs that action and shows the next card. Fires once (sentKeys).
 *   kind 'copy'    — drops the talk track into the rep's chat box (copytochat).
 *   primary        — full-width brand button; a message containing {tier} sends the value of
 *                    the selectable tile the rep picked on a 'compare' block.
 *   row buttons    — a 'list' row can carry its own button (Details, Transactions…).
 *   record links   — a 'summary' item with recordId opens the record (console tab).
 * Write-back per surface: SRA panel = acc:execute / copytochat; Enhanced Chat v2 =
 * configuration.util.sendTextMessage. Nothing here sends to the customer.
 *
 * layout = 'record' adds a Salesforce record header: record name (opens the record), status
 * pill and a highlights strip.
 *
 * Replace:
 *   {{ComponentClassName}} → e.g., AcmeCard (PascalCase of the LWC folder name)
 *   {{dtoJsonField}}       → the DTO's single @AuraEnabled String field, e.g., cardJSON
 */
export default class {{ComponentClassName}} extends NavigationMixin(LightningElement) {
    @api value;
    @api configuration;   // set on Enhanced Chat v2 only

    data;
    errorMessage = '';
    copied = false;
    sentKeys = [];
    selectedTier = null;

    connectedCallback() {
        try {
            const raw = this.value && this.value.{{dtoJsonField}};
            if (!raw) {
                this.errorMessage = 'No card data was returned.';
                return;
            }
            const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
            if (parsed.error) {
                this.errorMessage = parsed.error;
                return;
            }
            this.data = parsed;
            // Pre-select the highlighted selectable tile (the recommended option).
            (parsed.blocks || []).forEach((b) => {
                (b.items || []).forEach((it) => {
                    if (it.selectable && it.highlight && !this.selectedTier) this.selectedTier = it.value;
                });
            });
        } catch (e) {
            this.errorMessage = 'This card could not be displayed.';
        }
    }

    get hasError() {
        return !!this.errorMessage;
    }

    get hasData() {
        return !this.errorMessage && !!this.data;
    }

    get headerIcon() {
        return (this.data && (this.data.icon || THEME_ICON[this.data.theme])) || THEME_ICON.navy;
    }

    get isRecord() {
        return !!(this.data && this.data.layout === 'record' && this.data.record);
    }

    get cardClass() {
        return this.isRecord ? 'gp-card gp-card_record' : 'gp-card';
    }

    get record() {
        return (this.data && this.data.record) || {};
    }

    get statusPillClass() {
        return `gp-pill gp-pill_${this.record.statusState || 'info'}`;
    }

    get highlights() {
        return (this.record.highlights || []).map((h, i) => ({
            ...h,
            key: `h${i}`,
            valueClass: `gp-hl__value gp-value_${h.state || 'info'}`
        }));
    }

    get hasHighlights() {
        return this.highlights.length > 0;
    }

    get verdict() {
        return this.data && this.data.verdict;
    }

    get verdictClass() {
        return `gp-verdict gp-verdict_${(this.verdict && this.verdict.state) || 'info'}`;
    }

    get verdictIcon() {
        return STATE_ICON[(this.verdict && this.verdict.state) || 'info'];
    }

    get blocks() {
        return ((this.data && this.data.blocks) || []).map((b, bi) => {
            const items = (b.items || []).map((it, ii) => {
                const state = it.state || 'info';
                const key = `b${bi}-i${ii}`;
                const sent = this.sentKeys.includes(key);
                const picked = it.selectable ? it.value === this.selectedTier : !!it.highlight;
                return {
                    ...it,
                    key,
                    hasAction: !!(it.action && it.action.message),
                    actionLabel: it.action ? (sent ? 'Sent ✓' : it.action.label) : null,
                    actionDisabled: sent,
                    blockIndex: bi,
                    itemIndex: ii,
                    icon: STATE_ICON[state],
                    valueClass: `gp-value gp-value_${state}`,
                    badgeClass: `gp-badge gp-badge_${state}`,
                    barClass: `gp-bar__fill gp-bar__fill_${state}`,
                    barStyle: `width: ${Math.max(0, Math.min(100, it.bar || 0))}%;`,
                    tierClass: `gp-tier${picked ? ' gp-tier_pick' : ''}${it.selectable ? ' gp-tier_selectable' : ''}`,
                    radioClass: picked ? 'gp-radio gp-radio_on' : 'gp-radio',
                    tierPressed: picked ? 'true' : 'false',
                    whoClass: it.who === 'Assistant' || it.who === 'System' ? 'gp-who gp-who_bot' : 'gp-who',
                    stepClass: `gp-step gp-step_${it.state || 'incomplete'}`,
                    ariaCurrent: it.state === 'current' ? 'step' : null,
                    stageClass: it.current ? 'gp-stage gp-stage_current' : 'gp-stage',
                    detailClass: it.state ? `gp-detail__value gp-detail__value_${it.state}` : 'gp-detail__value',
                    hasBullets: Array.isArray(it.bullets) && it.bullets.length > 0,
                    bulletItems: (Array.isArray(it.bullets) ? it.bullets : []).map((t, ti) => ({ key: `${key}-l${ti}`, text: t }))
                };
            });
            return {
                key: `b${bi}`,
                title: b.title,
                note: b.note,
                items,
                isStats: b.type === 'stats',
                isFields: b.type === 'fields',
                isList: b.type === 'list',
                isCompare: b.type === 'compare',
                isChecklist: b.type === 'checklist',
                isProgress: b.type === 'progress',
                isTimeline: b.type === 'timeline',
                isPath: b.type === 'path',
                isStages: b.type === 'stages',
                isText: b.type === 'text',
                isDetails: b.type === 'details',
                isSummary: b.type === 'summary'
            };
        });
    }

    get allActions() {
        return ((this.data && this.data.actions) || []).map((a, i) => {
            const key = `a${i}`;
            const sent = a.kind !== 'copy' && this.sentKeys.includes(key);
            const needsTier = !!(a.message && a.message.includes('{tier}'));
            let label = a.label;
            if (a.kind === 'copy' && this.copied) label = 'Copied to chat';
            else if (sent) label = `${a.label} ✓`;
            return {
                ...a,
                key,
                index: i,
                label,
                sublabel: needsTier ? (this.selectedTier ? `${this.selectedTier} selected` : 'Select an option above') : null,
                variant: i === 0 ? 'brand' : 'neutral',
                disabled: sent || (needsTier && !this.selectedTier)
            };
        });
    }

    get primaryActions() {
        return this.allActions.filter((a) => a.primary);
    }

    get actions() {
        return this.allActions.filter((a) => !a.primary);
    }

    get hasActions() {
        return this.actions.length > 0;
    }

    // Record name in the record header: open the record (a console tab in the Service Console).
    openRecord(event) {
        const { recordId, objectApiName } = this.record;
        if (!recordId) return;
        event.preventDefault();
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: { recordId, objectApiName, actionName: 'view' }
        });
    }

    // A record link inside a block (e.g. the conversation on an AI summary): open the record.
    openItemRecord(event) {
        const { id, object } = event.currentTarget.dataset;
        if (!id) return;
        event.preventDefault();
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: { recordId: id, objectApiName: object, actionName: 'view' }
        });
    }

    // Selectable tiles on a compare block (e.g. pricing tiers).
    handleTierSelect(event) {
        const value = event.currentTarget.dataset.value;
        if (value) this.selectedTier = value;
    }

    handleTierKey(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            this.handleTierSelect(event);
        }
    }

    // Card-level buttons (primary and secondary).
    handleAction(event) {
        const index = Number(event.currentTarget.dataset.index);
        const action = this.data.actions[index];
        if (!action) return;
        if (action.kind === 'copy') {
            this.copyToChat(action.message || this.data.talkTrack);
            this.copied = true;
            return;
        }
        let message = action.message;
        if (message && message.includes('{tier}')) {
            if (!this.selectedTier) return;
            message = message.split('{tier}').join(this.selectedTier);
        }
        this.runNext(message, `a${index}`);
    }

    // Row-level buttons (e.g. Details on a list row).
    handleRowAction(event) {
        const { block, item } = event.currentTarget.dataset;
        const b = this.data.blocks[Number(block)];
        const it = b && b.items ? b.items[Number(item)] : null;
        if (!it || !it.action) return;
        this.runNext(it.action.message, `b${block}-i${item}`);
    }

    // Ask the assistant to run the next action. Each button fires once.
    runNext(message, key) {
        if (!message || this.sentKeys.includes(key)) return;
        if (this.configuration && this.configuration.util && this.configuration.util.sendTextMessage) {
            this.configuration.util.sendTextMessage(message);          // Enhanced Chat v2
        } else {
            this.fire('acc:execute', message);                           // Service Assistant panel
        }
        this.sentKeys = [...this.sentKeys, key];
    }

    copyToChat(text) {
        this.fire('copytochat', text);
    }

    // bubbles + composed are both required to cross the shadow boundary and reach the
    // Service Assistant panel listener. Fire exactly one event name.
    fire(eventName, content) {
        if (!content) return;
        this.dispatchEvent(new CustomEvent(eventName, {
            detail: { content },
            bubbles: true,
            composed: true
        }));
    }
}
