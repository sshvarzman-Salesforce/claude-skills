# MIAW Client — /iamessage/api/v2 Reference

All endpoints are **customer-side REST**, called by the client running in the visitor's browser or mobile app. No CLI. Base path: `/iamessage/api/v2`.

| Step | Method + Path | Purpose |
|---|---|---|
| Authorization | `POST /iamessage/api/v2/authorization` | Issue JWT for the visitor; scope + TTL |
| Create Conversation | `POST /iamessage/api/v2/conversation` | Start a session; returns conversation id |
| Send Message | `POST /iamessage/api/v2/conversation/{id}/message` | Customer → agent |
| Stream (SSE) | `GET /iamessage/api/v2/conversation/{id}/stream` | Server-Sent Events — messages, typing, presence |
| Typing Indicator | `POST /iamessage/api/v2/conversation/{id}/typingIndicator` | Announce "user is typing" |
| Attachment | `POST /iamessage/api/v2/conversation/{id}/attachment` | Multipart upload of file/image |
| Close Conversation | `DELETE /iamessage/api/v2/conversation/{id}` | End the session gracefully |

Docs:
- Conversation: https://developer.salesforce.com/docs/service/messaging-web/references/conversation.html
- Message: https://developer.salesforce.com/docs/service/messaging-web/references/message.html

## Headers

- `Authorization: Bearer <JWT>` on every request after `/authorization`.
- `X-Org-Id`, `X-Deployment-Id`, `X-Channel-Id` — required for authorization; keep in a small config module.

## SSE reconnection

- Client SHOULD send `Last-Event-Id` on reconnect to backfill missed messages.
- Server closes stream on inactivity; treat as normal — reopen.

## Related

- `sf-service-messaging-conversation-toolkit` — the **agent-side** Conversation Toolkit API (LWC in agent console).
- `sf-service-contact-center-config` — provisioning `MessagingChannel` and `EmbeddedServiceConfig`.
- `sf-service-voice-digital` — channel patterns that include MIAW alongside SMS/WhatsApp.

## Notes

- The `/iamessage/api/v2` surface is the same one used by the Salesforce-hosted embedded snap-in. If you can use the snap-in, prefer it — this skill is for custom clients.
- Never expose org-level API tokens in a client. The `/authorization` step exists precisely so client apps hold a scoped, short-lived JWT and nothing else.
- Attachment size and mime-type limits follow the channel's `MessagingChannel` config.
