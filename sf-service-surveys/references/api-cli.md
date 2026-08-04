# Surveys — Feedback Management API + CLI Reference

Salesforce Surveys / Feedback Management is **data-only** — no Metadata API deploy for invitations or responses. Survey definitions themselves are configured through Survey Builder UI (backed by `Survey`, `SurveyPage`, `SurveyQuestion` records).

## Authenticated Participants

Community/portal users with a Salesforce identity.

| Feature | API | Object | CLI |
|---|---|---|---|
| Survey Invitation Generation | REST | `SurveyInvitation` | `sf data create record --sobject SurveyInvitation --values ...` |
| Survey Response Submission | REST | `SurveyResponse` | `sf data create record --sobject SurveyResponse --values ...` |
| Survey Question Response | REST | `SurveyQuestionResponse` | `sf data create record --sobject SurveyQuestionResponse --values ...` |

Docs: https://developer.salesforce.com/docs/atlas.en-us.salesforce_feedback_management_dev_guide.meta/salesforce_feedback_management_dev_guide/salesforce_surveys_for_authenticated_participants.htm

## Unauthenticated Participants

Guest users invited by email link — no Salesforce identity.

| Feature | API | Object | CLI |
|---|---|---|---|
| Survey Invitation Generation | REST | `SurveyInvitation` (with `InvitationType='Public'`) | `sf data create record --sobject SurveyInvitation --values ...` |
| Survey Response Submission | REST | `SurveyResponse` | `sf data create record --sobject SurveyResponse --values ...` |
| Survey Question Response | REST | `SurveyQuestionResponse` | `sf data create record --sobject SurveyQuestionResponse --values ...` |

Docs: https://developer.salesforce.com/docs/atlas.en-us.salesforce_feedback_management_dev_guide.meta/salesforce_feedback_management_dev_guide/salesforce_surveys_for_unauthenticated_participants.htm

## Notes

- Survey definitions are UI-configured; only invitations + responses flow through the REST/data API layer.
- Public (unauth) invitations return a shareable URL; that URL is the only carrier of participant context, so protect it.
- For bulk seeding of invitations, prefer `sf data import bulk` with an external ID on `SurveyInvitation`.
- `SurveyResponse` records fire after page completion, not after each question — trigger closed-loop logic on `SurveyResponse.CompletionStatus = 'Complete'`.
