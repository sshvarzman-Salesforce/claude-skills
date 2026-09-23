/**
 * Reply routing helper for CLT cards — a service module (no template), so several
 * cards can share one copy. Deploy as its own LWC bundle with isExposed=false.
 *
 * A card's "Explain to customer" text is often already written in second person,
 * so it is a rep-to-customer reply. This module works out where that reply can
 * actually go, based on the record the rep has open:
 *
 *   Messaging Session (0Mw) -> send straight into the live customer conversation
 *   Case (500)              -> caller decides (email composer, panel, etc.)
 *   Voice Call (0LQ)        -> nothing; the rep reads the card aloud
 *   anything else           -> the agent panel (copytochat)
 *
 * WHY THE TARGET IS RESOLVED CLIENT-SIDE:
 * Apex actions typically resolve the customer with a ladder ending in "most recent
 * Active MessagingSession". That is fine for READING — a wrong card is visible and
 * recoverable. It is NOT safe for SENDING: an org can have several Active sessions
 * at once, so that fallback can name a different customer's conversation and the
 * reply is delivered with no undo. The send target therefore comes only from the
 * tab the rep is actually looking at.
 *
 * HOST CONTEXT: calling lightning/conversationToolkitApi from inside the Agentforce
 * panel (lightning__AgentforceOutput) is undocumented, but VERIFIED WORKING as of
 * 2026-09-02 — no bridge component needed. Every failure path still resolves false
 * rather than throwing, since undocumented behaviour can change without notice.
 *
 * SUCCESS DETECTION: "did not reject", never "=== true". The docs claim these methods
 * resolve true, but sendTextMessage resolves undefined while genuinely delivering the
 * message. A strict === true check reads a successful send as a failure, and any
 * fallback then duplicates a message the customer already received.
 *
 * Call resolveConversationContext() OUTSIDE the card's JSON-parse try/catch so a
 * messaging miss can never blank the card.
 */
import { getFocusedTabInfo, getTabInfo } from 'lightning/platformWorkspaceApi';
import { sendTextMessage, setAgentInput } from 'lightning/conversationToolkitApi';

const PREFIX = {
    MESSAGING: '0Mw',
    CASE: '500',
    VOICE: '0LQ'
};

export const CONTEXT = {
    MESSAGING: 'messaging',
    CASE: 'case',
    VOICE: 'voice',
    OTHER: 'other'
};

function recordIdOf(tab) {
    if (!tab) {
        return null;
    }
    return tab.recordId || (tab.pageReference && tab.pageReference.attributes
        ? tab.pageReference.attributes.recordId
        : null);
}

function kindOf(id) {
    if (typeof id !== 'string') {
        return null;
    }
    if (id.startsWith(PREFIX.MESSAGING)) {
        return CONTEXT.MESSAGING;
    }
    if (id.startsWith(PREFIX.CASE)) {
        return CONTEXT.CASE;
    }
    if (id.startsWith(PREFIX.VOICE)) {
        return CONTEXT.VOICE;
    }
    return null;
}

/**
 * What the rep currently has open: { kind, recordId }.
 * kind is CONTEXT.OTHER with a null recordId when we can't tell, which is a normal
 * outcome — it just means the card should fall back to the agent panel.
 */
export async function resolveConversationContext() {
    try {
        const focused = await getFocusedTabInfo();

        const focusedId = recordIdOf(focused);
        const focusedKind = kindOf(focusedId);
        if (focusedKind) {
            return { kind: focusedKind, recordId: focusedId };
        }

        // The rep may be on a subtab (Contact, Asset) nested inside the workspace
        // tab for the session or case, so check the parent before giving up.
        if (focused && focused.parentTabId) {
            const parentId = recordIdOf(await getTabInfo(focused.parentTabId));
            const parentKind = kindOf(parentId);
            if (parentKind) {
                return { kind: parentKind, recordId: parentId };
            }
        }
    } catch (e) {
        // Not a console app, or the workspace API isn't reachable from this host.
    }
    return { kind: CONTEXT.OTHER, recordId: null };
}

/** Convenience for cards that only care about the live-chat case. */
export async function resolveMessagingSessionId() {
    const ctx = await resolveConversationContext();
    return ctx.kind === CONTEXT.MESSAGING ? ctx.recordId : null;
}

/**
 * Deliver text into the live conversation as the rep.
 *
 *   immediate=true  -> sends outright
 *   immediate=false -> drops it into the composer for the rep to review and send
 *
 * Resolves false only when the platform actually refused, so callers can fall back.
 * Once a messaging session is in play, do NOT fall back to the agent panel — report
 * failure on the button label instead, or a successful send is duplicated.
 */
export async function replyToCustomer(sessionId, text, immediate = true) {
    if (kindOf(sessionId) !== CONTEXT.MESSAGING || !text) {
        return false;
    }
    try {
        if (immediate) {
            return (await sendTextMessage(sessionId, { text })) !== false;
        }
        // setAtCursor=true, otherwise this overwrites whatever the rep has typed.
        return (await setAgentInput(sessionId, { text }, true)) !== false;
    } catch (e) {
        return false;
    }
}
