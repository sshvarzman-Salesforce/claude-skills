---
name: sf-service-surveys
description: Salesforce Feedback Management / Surveys design and API integration. Use when embedding CSAT, NPS, or post-case survey capture into Service Cloud flows for authenticated or unauthenticated participants.
disable-model-invocation: true
---
# Service Cloud Surveys (Feedback Management)

## Use This Skill When

- Wiring post-case, post-chat, or post-call surveys triggered from Service Cloud journeys.
- Distinguishing authenticated (community/portal user) versus unauthenticated (email/link, guest) invitation paths.
- Persisting survey answers back onto Case, Contact, or Account for reporting and closed-loop follow-up.
- Deciding between UI-driven Survey Builder configuration and API-driven invitation generation for automation.

## Core Workflow

1. **Pick the participant model**
   - Authenticated participants: use community/portal identity — invitations tied to a User.
   - Unauthenticated participants: use email/link — invitations tied to a Contact or Lead only.
2. **Design the survey shell in Setup**
   - Survey Builder authors pages, questions, branching, and thank-you.
   - Publish before wiring APIs — unpublished surveys cannot be invited.
3. **Generate invitations via API**
   - POST `SurveyInvitation` records with correct participant, survey version, and invitation type.
   - Store invitation URLs for downstream email/SMS/chat delivery.
4. **Capture responses**
   - `SurveyResponse` + `SurveyQuestionResponse` records land as invitees complete pages.
   - Poll or subscribe for response completion when reporting depends on it.
5. **Close the loop**
   - Map responses to Case/Contact fields via Flow or Apex trigger on `SurveyResponse`.
   - Route low-score responses to a review queue or reopen case flow.

## Deliverables

- Participant-model decision (auth vs unauth) with rationale.
- Invitation generation runbook (API payloads, delivery channel).
- Response-to-record mapping (which fields update on Case/Contact/Account).
- Reporting model — dashboards for CSAT, NPS, response rate by channel.

## References

- See `references/api-cli.md` for exact REST endpoints and object mappings.
