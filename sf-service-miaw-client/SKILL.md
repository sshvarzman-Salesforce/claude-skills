---
name: sf-service-miaw-client
description: MIAW customer-side conversation REST API for embedding Messaging for In-App and Web into custom web or mobile clients. Use when building a headless chat client that talks directly to /iamessage/api/v2, not the Salesforce-hosted embedded snap-in.
disable-model-invocation: true
---
# MIAW Client — Customer-Side Conversation REST

## Use This Skill When

- Embedding MIAW chat into a non-Salesforce web or mobile app without the standard snap-in.
- Building a native iOS/Android chat client that speaks MIAW REST directly.
- Debugging or replaying the wire protocol between a MIAW client and Salesforce.
- Distinguishing customer-side conversation REST from the agent-side Messaging + Conversation Toolkit API (see `sf-service-messaging-conversation-toolkit`).

## Core Workflow

1. **Provision the channel**
   - Ensure a `MessagingChannel` + `EmbeddedServiceConfig` exist and are activated (see `sf-service-contact-center-config`).
   - Get the org's `orgId`, `deploymentId`, `channelId` from Setup — the client needs them.
2. **Authorize the participant**
   - POST `/iamessage/api/v2/authorization` — issue a JWT scoped to the visitor.
   - Persist the token for reconnection; refresh before expiry.
3. **Start a conversation**
   - POST `/iamessage/api/v2/conversation` with the JWT — returns a conversation id.
4. **Send + receive**
   - Send: POST `/iamessage/api/v2/conversation/{id}/message` with participant-authored text/media.
   - Receive: GET `/iamessage/api/v2/conversation/{id}/stream` as a Server-Sent Events (SSE) stream. Reconnect on drop with `Last-Event-Id`.
5. **UX affordances**
   - Typing indicator: POST `/iamessage/api/v2/conversation/{id}/typingIndicator`.
   - Attachments: POST `/iamessage/api/v2/conversation/{id}/attachment` (multipart).
6. **End cleanly**
   - DELETE `/iamessage/api/v2/conversation/{id}` when the visitor closes chat.
   - Do not delete on navigation-away — reconnection preserves the session.

## Deliverables

- Auth + reconnection model (token TTL, refresh, replay via `Last-Event-Id`).
- Wire protocol trace (auth → conversation → message → stream → close) with sample payloads.
- Error/retry matrix — network drops, 401 refresh, 429 backoff, 5xx circuit.
- Handoff plan — what the agent-side sees when the client sends specific events.

## References

- See `references/api-cli.md` for the full endpoint list and headers.
