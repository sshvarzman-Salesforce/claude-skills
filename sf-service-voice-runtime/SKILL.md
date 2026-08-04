---
name: sf-service-voice-runtime
description: Service Connector API — voice interaction runtime for Service Cloud Voice agents and supervisors. Use when scripting or embedding call control (accept, transfer, hold, conference, DTMF) and supervisor barge/monitor/whisper in an LWC or CTI overlay.
disable-model-invocation: true
---
# Service Cloud Voice — Runtime Interaction (Service Connector API)

## Use This Skill When

- Building or extending a Service Cloud Voice softphone / interaction pane.
- Driving call control (accept, end, hold/resume, mute/unmute, DTMF, transfer, conference) from an LWC or Aura component.
- Adding supervisor tooling — barge-in, silent monitor, whisper — in real time.
- Wiring agent presence and login/logout state changes into the same client.

## Core Workflow

1. **Confirm the CTI surface**
   - Service Cloud Voice + Amazon Connect (or partner CCaaS) is provisioned with the Service Connector API loaded on the interaction pane.
2. **Model call state**
   - Track call lifecycle: `Ringing → Connected → OnHold → Transferring → Ended`.
   - Bind UI buttons to `Sfdc.interaction.voice.*` calls; guard with the current state.
3. **Agent-side controls**
   - Accept / End: `acceptCall()`, `endCall()`.
   - Hold / Resume, Mute / Unmute.
   - Transfer patterns: blind vs warm; conference for three-way.
   - DTMF: `sendDigits()` for IVR navigation from an assist tool.
4. **Presence + login**
   - `login()`, `logout()`, `setAgentStatus()` — synchronize with Omni presence where used.
5. **Supervisor controls**
   - `barge()`, `monitor()` (silent), `whisper()` — gate behind supervisor role check on the client.
6. **Correlate to records**
   - Bind interaction events to `VoiceCall`, `MessagingSession`, or `Case` — see `sf-service-voice-toolkit` for transcript subscribe/teardown and `sf-service-voice-digital` for channel patterns.

## Deliverables

- Call-state model with allowed transitions.
- Button-to-API map for the agent pane (with role guards on supervisor actions).
- Failure/edge-case handling — dropped connections, transfer failures, DTMF timing.
- Test plan — one call per control, end-to-end with a soft phone in preview.

## References

- See `references/api-cli.md` for the full Service Connector API surface used in this skill.
