# Messaging + Conversation Toolkit — API + CLI Reference

This skill covers the **agent-side** Conversation Toolkit API (LWC in the service console). For the customer-side `/iamessage/api/v2` protocol, see `sf-service-miaw-client`.

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Messaging Channel | Metadata | `MessagingChannel` (`ChannelType`: MessagingInApp, WhatsApp, SMS, FBMessenger, Apple, Google) | `sf project deploy start --metadata MessagingChannel` |
| Embedded Service Config | Metadata | `EmbeddedServiceConfig` (deployment container) | `sf project deploy start --metadata EmbeddedServiceConfig` |
| Embedded Service Menu | Metadata | `EmbeddedServiceMenuSettings` | `sf project deploy start --metadata EmbeddedServiceMenuSettings` |
| Conversation Toolkit API | LWC API | `lightning/conversationToolkitApi` (`sendMessage`, `getConversationLog`, `endConversation`, `transferToAgent`, `getMessages`) | n/a (client-only) |
| Messaging Session | REST | `MessagingSession`, `MessagingEndUser`, `ConversationEntry` (data-only) | `sf data query -q "..."` |
| Messaging Template | Metadata | `MessagingChannel` sub-element | included in `MessagingChannel` deploy |

## Docs

- MessagingChannel: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_messagingchannel.htm
- Conversation Toolkit: https://developer.salesforce.com/docs/atlas.en-us.service_developer_center.meta/service_developer_center/conversation_toolkit_api.htm
- EmbeddedServiceConfig: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_embeddedserviceconfig.htm

## Notes

- Conversation Toolkit is **LWC-only** — no Aura, no Apex. If a component needs conversation data from Apex, hydrate via `ConversationEntry` SOQL from within the LWC and pass down.
- `MessagingChannel` activation is a stateful action — deploy the metadata, then activate via UI or Metadata `Deploy` with `Active=true`.
- Session ↔ Case linkage is via `MessagingSession.CaseId`; if absent, the case was not auto-created.
