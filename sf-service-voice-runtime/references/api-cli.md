# Service Connector API — Voice Runtime Reference

Service Connector API is a **client-side JS API** loaded into the Service Cloud Voice interaction pane. No REST/Metadata/CLI equivalent — call these from LWC or Aura on the agent softphone.

## Agent — Call Control

| Feature | JS API |
|---|---|
| Accept Incoming Call | `Sfdc.interaction.voice.acceptCall()` |
| End / Hang Up Call | `Sfdc.interaction.voice.endCall()` |
| Hold | `Sfdc.interaction.voice.hold()` |
| Resume | `Sfdc.interaction.voice.resume()` |
| Mute | `Sfdc.interaction.voice.mute()` |
| Unmute | `Sfdc.interaction.voice.unmute()` |
| Send Digits (DTMF) | `Sfdc.interaction.voice.sendDigits()` |

## Agent — Transfers & Conference

| Feature | JS API |
|---|---|
| Blind Transfer | `Sfdc.interaction.voice.blindTransfer()` |
| Warm Transfer | `Sfdc.interaction.voice.warmTransfer()` |
| Conference Call | `Sfdc.interaction.voice.conference()` |

## Agent — Presence & Session

| Feature | JS API |
|---|---|
| Login | `Sfdc.interaction.voice.login()` |
| Logout | `Sfdc.interaction.voice.logout()` |
| Set Presence / Availability | `Sfdc.interaction.voice.setAgentStatus()` |

## Supervisor Controls

| Feature | JS API |
|---|---|
| Barge-In | `Sfdc.interaction.voice.barge()` |
| Monitor (Silent) | `Sfdc.interaction.voice.monitor()` |
| Whisper | `Sfdc.interaction.voice.whisper()` |

Docs: https://developer.salesforce.com/docs/atlas.en-us.service_connector_api_developer_guide.meta/service_connector_api_developer_guide/service_connector_api_overview.htm

## Notes

- These APIs are only available inside the Service Cloud Voice interaction pane iframe/context — they fail silently or throw outside it.
- Return promises; always await and handle rejection (e.g., no active call, permission denied for supervisor action).
- Supervisor barge/monitor/whisper require the supervisor perm-set + queue permissions. Gate the UI accordingly.
- Correlate calls to `VoiceCall` records for post-call logic — see `sf-service-voice-toolkit` (transcript subscribe) and REST `VoiceCall` CRUD in `sf-service-voice-digital`.
