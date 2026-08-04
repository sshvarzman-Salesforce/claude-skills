# Voice Toolkit — API + CLI Reference

Agent-side, in-console Voice Toolkit API. For customer/CTI-side Service Connector API (`Sfdc.interaction.voice.*`), see `sf-service-voice-runtime`.

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Voice Toolkit LWC API | LWC API | `lightning/voiceToolkitApi` (events: `pluginCallStarted`, `transcript`, `agentAssistUpdate`, `pluginCallEnded`) | n/a (client-only) |
| Voice Call (record) | REST | `VoiceCall`, `VoiceCallRecording` (data) | `sf data query -q "..."` |
| Call Transcript | REST | `ConversationEntry` (for messaging + voice), `VoiceCall.CallTranscript` | `sf data query -q "..."` |
| Contact Center / Call Center | Metadata | `ContactCenter` (SCV), `CallCenter` (legacy CTI) | `sf project deploy start --metadata ContactCenter` |
| SCV Recording Config | Metadata | `ContactCenterChannel`, `ContactCenter` sub-elements | included in `ContactCenter` |

## Docs

- Voice Toolkit API: https://developer.salesforce.com/docs/atlas.en-us.voice_developer_guide.meta/voice_developer_guide/voice_dev_toolkit_api.htm
- VoiceCall: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_voicecall.htm
- ConversationEntry: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_conversationentry.htm

## Notes

- Voice Toolkit **only fires while the record page hosting the LWC is open** — offscreen consumers must fall back to `ConversationEntry` polling.
- `ConversationEntry` polling has a floor of a few seconds — do not use it as a real-time source; use it as durable replay.
- Transcript fragments arrive out-of-order under network jitter; always sequence by timestamp or `ConversationIdentifier` before AI extraction.
