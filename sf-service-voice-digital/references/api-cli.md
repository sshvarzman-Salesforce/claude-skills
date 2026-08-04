# Voice + Digital Engagement — API + CLI Reference

Blended channel reference. For deep-dives, see `sf-service-voice-toolkit` (agent LWC), `sf-service-voice-runtime` (Service Connector API), `sf-service-messaging-conversation-toolkit` (agent messaging LWC), `sf-service-miaw-client` (customer-side MIAW REST).

| Channel | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Voice / SCV | Metadata, REST | `CallCenter`, `ContactCenter` (partial); `VoiceCall`, `VoiceCallList`, `ContactCenterChannel` (records) | `sf project deploy start --metadata CallCenter` |
| Messaging (MIAW, WhatsApp, SMS, FBM, Apple, Google) | Metadata | `MessagingChannel` | `sf project deploy start --metadata MessagingChannel` |
| Embedded Service (web/mobile snap-in) | Metadata | `EmbeddedServiceConfig`, `EmbeddedServiceMenuSettings`, `EmbeddedServiceBranding` | `sf project deploy start --metadata EmbeddedServiceConfig` |
| Chat (legacy Live Agent) | Metadata | `LiveChatButton`, `LiveChatDeployment`, `LiveAgentSettings` | `sf project deploy start --metadata LiveChatButton` |
| Conversation Records | REST | `ConversationEntry`, `MessagingSession`, `VoiceCall.CallTranscript` | `sf data query -q "..."` |

## Docs

- CallCenter: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_callcenter.htm
- ContactCenter: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_contactcenter.htm
- MessagingChannel: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_messagingchannel.htm

## Notes

- **Service Cloud Voice** uses `ContactCenter` (partial metadata support today) + `CallCenter` (legacy CTI adapter). New voice deploys use `ContactCenter`.
- Cross-channel handoff shares state via `Case` — carry `MessagingSession.CaseId` or `VoiceCall.CallCaseId` across channels rather than re-creating the conversation.
- Voice transcripts are surfaced via `CallTranscript` (record) + Toolkit events (live) — never poll `CallTranscript` for real-time UX (latency + governor limits).
