# Re-theming the Observability QBrix for any industry — full playbook

This is the end-to-end recipe for replacing the stock DriveMax synthetic
data with your own branded sessions that **render correctly in Agentforce
Studio → Analytics and Optimization → Insights**, and that tell a
deliberate quality story (e.g. "the agent does most things well but fails
at one specific intent"). Proven end-to-end on the Skywave Airlines rebrand
(404 sessions; Quality-by-Intent bottoming out on seat-change while other
intents scored High).

It assumes you've read `sdo-qbrix.md` for the per-field render requirements
(enums, Participant__c, NOT_SET sentinel, telemetry, timestamps). This file
is the **structure + story + seeder template** on top of that.

---

## 0. Mental model — the analyzer does NOT process synthetic data

The single most important fact: the Agentforce Optimization analyzer
(AgentOpt connector) only scores **real** (AIPlatform) sessions. It will
**never** generate quality scores, intents, or moments for synthetic
(`Salesforce_Home`) data. Therefore **everything the dashboard shows must be
pre-baked into the SDO custom objects**. This is exactly what the stock
DriveMax data does, and what your seeder must do.

Corollary: don't wait for "processing." If a chart is empty, a field/tag is
missing in your seed — not a pipeline that hasn't run yet.

## 1. The object graph you must seed

Eleven `SDO_Analytics_AIAgent*_v2__c` objects. The render-critical wiring:

```
Session ──< Participant         (2: AGENT + USER, both need Participant__c)
        ──< Interaction         (N TURN rows + exactly 1 SESSION_END)
        │       ──< Message      (Input + Output per turn)
        │       ──< Step         (TOPIC_STEP / LLM_STEP / ACTION_STEP)
        ──< Moment              (1..3 per session = the "intent rows")
                ──< MomentInteraction  (junction → the moment's interactions)
                ──< TagAssociation ×2  → Tag → TagDefinition
                       (1 AIE intent tag  + 1 Quality_Score tag)
TagDefinition ──< TagDefinitionAssociation (per agent)
```

**The Moment is the unit of the dashboard.** Each moment becomes one row in
Sessions & Intents and one data point in Quality-by-Intent /
Quality-by-Subagent. A moment carries:
- a `Request_Summary_Text__c` + `Response_Summary_Text__c` (the intent/response shown),
- a MomentInteraction junction to its interactions (whose `Topic_API_Name__c` is the **subagent**),
- **exactly two tag associations**: the **AIE intent** tag and the **Quality_Score** tag.

## 1b. The `ssot__Bot__dlm` join — gate for Optimization & Sessions (easy to miss)

The Optimization **Insights** and **Sessions & Intents** views join each
session's agent to the **`ssot__Bot__dlm`** DMO on
`ssot__DeveloperName__c` = the session's agent API name. **No matching Bot
row → the session never appears in those two surfaces** (Analytics is
separate and does not need this). This is a different, independent gate from
the Participant__c / NOT_SET requirements that unlock Analytics.

Critically, `ssot__Bot__dlm` is **NOT** one of the SDO_Analytics synthetic
objects. It is fed by the **`BotDefinition_Home`** data stream from the
org's **real `BotDefinition` records** (`DataSourceObjectId = BotDefinition`).
So a Bot row exists only for agents that are actually **deployed** in the
org.

Consequences for a rebrand:
- If your synthetic sessions' agent api name matches a **real deployed
  agent** (as Skywave's `Skywave_Airlines_Agent` did — by luck of naming),
  the Bot row exists automatically and Optimization/Sessions work.
- If your demo agent is **NOT deployed** (the common future case — e.g. the
  stock `DriveMax_Suppport`, which has no agent in-org and therefore never
  appears in Optimization/Sessions), you must do ONE of:
  1. **Deploy a minimal/barebones agent** whose API name exactly equals the
     synthetic sessions' `AI_Agent_Api_Name__c`, then refresh
     `BotDefinition_Home` so its Bot row lands. (Simplest, most robust.)
  2. **Seed a `ssot__Bot__dlm` row** directly (advanced; the DLO behind it),
     `ssot__DeveloperName__c` = the agent api name, `ssot__Label__c`,
     `ssot__AgentType__c = 'EinsteinServiceAgent'`.

Verify the join key matches exactly:
```sql
-- agent name on your synthetic sessions
SELECT "ssot__AiAgentApiName__c" FROM "ssot__AiAgentSessionParticipant__dlm"
WHERE "ssot__DataSourceId__c" = 'Salesforce_Home' GROUP BY 1
-- must have a row here with the SAME DeveloperName
SELECT "ssot__DeveloperName__c" FROM "ssot__Bot__dlm"
```

> This was the long-unexplained reason DriveMax synthetic data never showed
> in Optimization/Sessions while Skywave did, and why the 2 DriveMax
> `Copilot_for_Salesforce` sessions DID show (Copilot is a real, deployed
> agent with a Bot row). A Salesforce dev hit the same wall preparing 262
> and fixed it by creating the missing `ssot__Bot__dlm` data. Note the
> behaviour can vary by **Service Agent Analytics app version**.
>
> **CONFIRMED BY EXPERIMENT:** deploying + publishing + **activating** a
> barebones agent named exactly `DriveMax_Suppport`, then refreshing
> `BotDefinition_Home`, made a `ssot__Bot__dlm` row appear — and the
> previously-invisible DriveMax synthetic sessions immediately surfaced in
> Optimization/Sessions. So option 1 (deploy a minimal agent with the
> matching api name) is verified to work. A minimal `start_agent`-only
> AgentforceServiceAgent (needs `default_agent_user`) is enough — it does
> not need topics or actions. **Activation is required** (it's what makes
> the BotDefinition/BotVersion active so the Bot row is created), and the
> `BotDefinition_Home` stream must be refreshed afterward (same
> SalesforceDotCom interactive-refresh constraint as the SDO streams).

## 2. The two tag definitions that matter (ship ONLY these)

DriveMax ships exactly two tag-definition types. Match it:

| Developer_Name | Source_Type | Data_Type | Drives |
|---|---|---|---|
| `AIE_Request_Category_<AgentApiName>` | `Generated` | `Text` | the **Intent** dimension (Quality-by-Intent, intent rankings) |
| `Quality_Score` | `Predefined` | `Integer` | **Average Quality Score**, Quality-by-Subagent, Quality-by-Intent bands |

- The `<AgentApiName>` suffix must match your agent's API name exactly.
- `Quality_Score`: create **5 reusable tag rows** valued `'1'..'5'`, associate **one per moment**. Score→band mapping in the UI: 5≈High, 4≈High, 3≈Medium, 2≈Low, 1≈Very Low (averaged per intent/subagent).
- Do NOT ship `Topic_Quality` / `User_Satisfaction` / `Resolution_Status`
  as seed tags — those are live-analyzer output for real sessions, not part
  of the synthetic seed. (They'll appear in-org from your real test chats;
  that's fine, just don't seed them.)
- Reuse tags: create each intent value once and each score 1-5 once, then
  reference them from many associations (DriveMax: ~47 tags → 3,073
  associations). Don't mint a fresh tag per association.

## 3. Designing the quality story

The story is controlled entirely by **which Quality_Score you attach to
which intent**, plus the subagent (topic) each intent rolls up under.

Decisions to make per industry:
1. **Subagents (topics)** — the `Topic_API_Name__c` values, mirroring the
   real agent's topics. The failing capability should usually NOT be its own
   topic, so the failure surfaces under Quality-by-**Intent**, not
   Quality-by-Subagent. (Skywave: 5 topics, no "seat" topic; seat failures
   live under `flight_management`.)
2. **Intents** — granular `AIE_Request_Category` values, grouped by bucket.
   The "fail" bucket gets several intents that all score low.
3. **Quality bands per intent bucket** — the heart of the story.

Skywave's archetype table (topic, bucket, score-range, weight):

```
flight_management  seat     1-2   weight 30   <- the failure, biggest slice
flight_management  booking  4-5   weight 20
mileage_account    loyalty  4-5   weight 15
case_management    support  3-4   weight 15
name_change        name     4-5   weight 10
off_topic          misc     2-3   weight 10
```

Result (verified): seat intents averaged 1.36–1.52 (Very Low, bottom of
Quality-by-Intent); booking/mileage/name 4.4–4.7 (High);
`flight_management` subagent showed Medium overall (dragged down by the seat
slice it contains) — which is the ideal "drill from subagent into intent to
find the culprit" narrative.

**Tuning levers:**
- Make the headline "Average Quality Score" lean lower → raise the failing
  bucket's `weight` or widen more buckets into the 2-3 band.
- Sharper contrast → narrow ranges (seat `1-1`, others `5-5`).
- Believability → keep a few mid-scores (the `3-4` support bucket) so it's
  not a clean bimodal split.

## 4. Message content matters for the transcript

Even though the analyzer won't score synthetic data, the
`Request_Summary_Text__c`/`Response_Summary_Text__c` (moment) and the
Input/Output messages are shown verbatim in Sessions & Intents. Write the
**failing** intent's sample pairs as genuine failures ("I was unable to
retrieve the seat map…") so the transcript matches the low score, and the
successful intents as clean successes.

## 5. Seeder skeleton (Apex)

The full working class is `Skywave_ObservabilitySeeder` in the
is_interactive_skywave repo (commit ce0dbb2). Key shape to copy:

```apex
public with sharing class <Industry>_ObservabilitySeeder {
    public static final String DEMO_TAG  = '<UNIQUE_TAG>';   // for scoped wipe
    public static final String AGENT_API_NAME = '<Your_Agent_Api_Name>';
    private static final Integer CHUNK_SIZE = 100;            // DML-limit safe
    private static final String AIE_INTENT_DEF =
        'AIE_Request_Category_' + AGENT_API_NAME;

    // 1) INTENTS: Map<bucket, List<intentValue>>  (your dashboard intents)
    // 2) SAMPLES: Map<bucket, List<[userMsg, agentMsg]>> (fail bucket = failures)
    // 3) archetypes(): List of (topic, bucket, minScore, maxScore, weight)

    public class SeedJob implements Queueable {            // chained chunks
        Integer total, done;
        public void execute(QueueableContext qc) {
            if (done == 0) seedTagDefinitions(); else loadTagMaps();
            Integer n = Math.min(CHUNK_SIZE, total - done);
            seedSessions(n, done);
            if (done + n < total && !Test.isRunningTest())
                System.enqueueJob(new SeedJob(total, done + n));
        }
    }

    // seedTagDefinitions(): insert 2 tag defs + def-associations +
    //   reusable intent tags (1 per value) + 5 Quality_Score tags ('1'..'5')
    // loadTagMaps(): re-query those into the static maps for chunks 2+
    // seedSessions(n, offset): per session ->
    //   pick 1-3 moments; per moment pick an archetype (weighted),
    //   an intent value, a Quality_Score in [min,max];
    //   build 2 interactions (TURN) + messages + steps + MomentInteraction;
    //   moment row + 2 tag associations (intent + score);
    //   then session row, 2 participants (with Participant__c), SESSION_END.
}
```

Non-negotiables baked into the working version (see sdo-qbrix.md for why):
- enums: message `Input`/`Output`, content `text/plain`, interaction `TURN`
  (+ one `SESSION_END`), step `TOPIC_STEP`/`LLM_STEP`/`ACTION_STEP`.
- participants: AGENT → `Participant_Object__c='GenAiPlannerDefinition'`,
  `Participant__c` = live planner id (query
  `GenAiPlannerDefinition WHERE DeveloperName LIKE '<Agent>_v%'`); USER →
  `'MessagingEndUser'`, `Participant__c` = a real MessagingEndUser id,
  rotated across ~25 of them.
- session optional fields = literal `'NOT_SET'` (Individual,
  Previous_Session_Id, Session_Owner_Object, Variable). NOT
  Related_Voice_Call (real VoiceCall lookup → rejects 'NOT_SET').
- timestamps: write session/participant `End_Timestamp__c` via
  `DateTime.newInstanceGmt(...)`; interaction/step/message use the
  `*_Days__c` + `*_Time__c` pairs (the `*_Timestamp__c` are read-only
  formulas). day-offset ≥ 1 (never future-date).
- every tag association sets `AI_Agent_Tag_Definition_Association_Id__c`.
- chunk inserts at `CHUNK_SIZE`≈100 sessions; a full session graph is
  ~30-40 rows, so ~400 sessions = ~15K rows total across chained chunks.

## 5b. Conversation timing — two independent intervals

Realistic timing makes the dashboard believable; getting it wrong inflates
the latency metric and makes transcripts look robotic. There are **two
separate intervals** and they must be decoupled:

1. **Agent latency = interaction `Start_Time`→`End_Time` duration.** This is
   what the dashboard reports as **Average Agent Latency** — NOT the
   user-message→agent-message delta. Keep it short and tight: **2-4s**
   (`turnEnd = turnStart.addSeconds(2 + rand(3))`). A wide window here (the
   original bug used 20-60s) drives the headline latency to ~40s. Put the
   user message at `turnStart` and the agent message at `turnEnd` so both
   sit inside this window.
2. **User think/away time = the gap BETWEEN one interaction's end and the
   next interaction's start.** Real chat users are slow and variable: they
   ask, switch to other work while the answer appears, and check back later.
   Model it right-skewed, NOT a flat few seconds:
   ```apex
   Integer userGap = (rand(100) < 70)
       ? 15 + rand(60)     // attentive reading pause: 15-75s
       : 90 + rand(210);   // stepped away: 90-300s
   cursor = turnEnd.addSeconds(userGap);
   ```
   Because this gap is between interactions, it does NOT affect the
   per-interaction latency metric. Verified shape: agent latency avg ~3s
   (2-4); user gap avg ~89s, median ~58s, spanning 15-300s.

## 6. Scoped wipe (never destroy coexisting DriveMax data)

The wipe batch MUST filter on your `Demo_Identifier__c` — an unfiltered
`DELETE FROM SDO_Analytics_*` wipes the stock DriveMax rows too:
```apex
Database.getQueryLocator(
  'SELECT Id FROM ' + obj + ' WHERE Demo_Identifier__c = :demoTag');
```

## 7. Run sequence

```
1. sf project deploy start -m ApexClass:<Industry>_ObservabilitySeeder \
                           -m ApexClass:<Industry>_ObservabilityWipe
2. Database.executeBatch(new <Industry>_ObservabilityWipe(), 2000);  // scoped
3. System.enqueueJob(new <Industry>_ObservabilitySeeder.SeedJob(400));
4. (Dev Console) <DataStreamRunner>.refreshSdoAnalyticsStreams();    // CRLF/interactive — see sdo-qbrix.md
5. Agentforce Studio → Optimization → Insights, filter Agent = <Your Agent>
```

The stream refresh is the step that pushes the SDO rows into the DMOs the
dashboard reads. Charts are empty until it completes (SalesforceDotCom
streams must be refreshed from a browser/Dev Console — CLI/API can't).

## 8. Verify the story at the source before refreshing

Don't wait on the dashboard to find mistakes — verify the seed directly.
Per-intent average Quality_Score (the story) is two tag-associations joined
on the same moment:
```
moment ─ assoc(AIE intent tag)     -> intent value
       └ assoc(Quality_Score tag)  -> 1..5
group by intent value, avg the score → seat intents should be lowest.
```
A quick Apex/script that walks TagAssociation → Tag → (def, value) and
buckets score by intent confirms the story in seconds.

## 9. Known limits / future gaps

- `Variable__c` is `string(255)` — cannot hold a real session's ~1.5K-char
  variable-state JSON. Use `NOT_SET`; don't try to clone real VariableText.
- Sessions & Intents "Processed vs Unprocessed": synthetic sessions sit as
  **Unprocessed** (the analyzer owns "Processed"). The quality story renders
  in Analytics + Optimization **Insights** regardless — those are the demo
  targets. Don't chase getting synthetic data into "Processed".
- Average Agent Latency: see the timing model in §5b — derive it from the
  interaction Start→End duration (keep it 2-4s), NOT from the message delta.
