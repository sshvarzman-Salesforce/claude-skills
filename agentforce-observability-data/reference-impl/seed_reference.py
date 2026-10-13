#!/usr/bin/env python3
"""
Reference synthetic-observability seeder (Path 5 / Ingestion API). Runnable, but
meant to be READ and adapted: it shows the row graph + every KPI-driving signal in
one place. Edit AGENT_API_NAME + ARCHETYPES for your demo.

What it produces per session (and which dashboard tile each part feeds):
  * Session + AGENT/USER participants   -> Unique Sessions; agent appears in dropdowns
  * TURN interaction with an ACTION_STEP -> Engagement Rate (engaged = has ACTION_STEP)
  * ACTION_STEP with/without an error    -> Success Rate (engaged AND no step error)
  * SESSION_END step Name=CLOSED_*       -> Escalation Rate (CLOSED_TRANSFERRED=escalated)
  * Moment + Quality_Score/Intent tags   -> Quality by Subagent/Intent; Sessions & Intents
  * std_Deflection/Abandonment score assoc -> Deflection Rate / Abandon Rate / Outcome
See ../references/non-sdo-ingestion-api-playbook.md §11 for the exact formulas.

Subcommands:
  setup   create the 11 IngestApi sources/schemas/streams/DLO->DMO mappings (idempotent)
  push    generate N sessions (today-relative) and ingest them (UPSERT — re-run daily)
  verify  DMO row counts + escalation/engagement signal counts
  teardown remove the sources (mappings->streams->connections)

Prereqs: DC_* env vars (see dc_client.py); the agent named AGENT_API_NAME deployed +
published + activated (for the ssot__Bot__dlm join that gates the Optimization tab) and
Agentforce Optimization ON (so the std_ score tag-defs are auto-provisioned).
"""
import argparse, csv, datetime as _dt, io, json, os, subprocess, sys, uuid as _uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stdm_schema as S              # noqa: E402
from dc_client import DC             # noqa: E402

# ─── EDIT THESE FOR YOUR DEMO ────────────────────────────────────────────────
AGENT_API_NAME = "MediCare_Health_Agent"
AGENT_VERSION = "v1"
CHANNEL = "SCRT2 - EmbeddedMessaging"
DATA_SOURCE_PREFIX = S.PREFIX        # DataSourceId stamped on every row (filter/delete key)
DAYS_SPREAD = 10                     # sessions spread over the last N days (never day 0)

# (topic/subagent, intent label, quality 1-5, outcome, action api name, action_fails, weight)
# Story: billing resolves well; prescription refills fail (abandon + escalate).
ARCHETYPES = [
    ("billing_support",           "Pay Bill",                5, "deflected",  "process_payment",   False, 25),
    ("billing_support",           "Dispute Charge",          4, "deflected",  "open_dispute",      False, 12),
    ("appointment_scheduling",    "Schedule Appointment",    5, "deflected",  "book_appointment",  False, 15),
    ("insurance_verification",    "Coverage Check",          4, "deflected",  "verify_coverage",   False, 10),
    ("prescription_management",   "Refill Status",           3, "deflected",  "get_refill_status", False, 8),
    ("prescription_management",   "Prescription Refill",     1, "abandoned",  "submit_refill",     True,  20),
    ("prescription_management",   "Prescription Refill",     2, "escalated",  "submit_refill",     True,  10),
]
CLOSE_NAME = {"deflected": "CLOSED_ACTION", "abandoned": "CLOSED_USER_REQUEST",
              "escalated": "CLOSED_TRANSFERRED"}
END_TYPE = {"deflected": "resolved", "abandoned": "resolved", "escalated": "escalated"}
INTENT_DEF = "AIE_Request_Category_" + AGENT_API_NAME
_NS = _uuid.uuid5(_uuid.NAMESPACE_URL, "obs-reference/" + AGENT_API_NAME)


# ─── helpers ─────────────────────────────────────────────────────────────────
def _uid(*p): return str(_uuid.uuid5(_NS, "|".join(str(x) for x in p)))
def _iso(dt): return dt.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (dt.microsecond // 1000)
def _hex(n, seed): return "".join("0123456789abcdef"[(seed * 7 + i * 13) % 16] for i in range(n))
def _json(d): return json.dumps(d, separators=(",", ":"))


def sf_json(org, soql=None, org_display=False):
    cmd = (["sf", "org", "display", "--json", "-o", org] if org_display
           else ["sf", "data", "query", "--json", "-o", org, "-q", soql])
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("sf failed: " + (out.stderr or out.stdout))
    return json.loads(out.stdout[out.stdout.index("{"):])


def resolve_identities(org):
    org_id = sf_json(org, org_display=True)["result"]["id"]
    pl = sf_json(org, "SELECT Id FROM GenAiPlannerDefinition WHERE DeveloperName LIKE '%s%%' "
                 "ORDER BY CreatedDate DESC LIMIT 1" % AGENT_API_NAME)["result"]["records"]
    if not pl:
        raise RuntimeError("no GenAiPlannerDefinition for " + AGENT_API_NAME + " — deploy the agent first")
    planner = pl[0]["Id"][:15]
    users = sf_json(org, "SELECT Id FROM MessagingEndUser LIMIT 5")["result"]["records"]
    obj = "MessagingEndUser"
    if not users:
        users = sf_json(org, "SELECT Id FROM User WHERE IsActive=true LIMIT 5")["result"]["records"]
        obj = "User"
    return org_id, planner, [u["Id"] for u in users], obj


def _edge_rows(dc, sql):
    _, r = dc.query(sql)
    return (r.get("data") if isinstance(r, dict) else None) or []


def resolve_std_scorers(dc):
    """Resolve the PLATFORM-provisioned std_Deflection/Abandonment tag graph so we can
    push score ASSOCIATIONS that reference them. Returns None if not provisioned yet
    (agent not deployed / Optimization off) — then Deflection/Abandon read 0."""
    def defid(kind):
        rows = _edge_rows(dc, "SELECT ssot__Id__c FROM ssot__AiAgentTagDefinition__dlm WHERE "
                          "ssot__DeveloperName__c='std_%s_Score_%s_V1'" % (kind, AGENT_API_NAME))
        return rows[0][0] if rows else None
    d, a = defid("Deflection"), defid("Abandonment")
    if not d or not a:
        return None
    def vals(defid_):
        m = {}
        for v, tid in _edge_rows(dc, "SELECT ssot__Value__c, ssot__Id__c FROM ssot__AiAgentTag__dlm "
                                 "WHERE ssot__AiAgentTagDefinitionId__c='%s'" % defid_):
            m.setdefault(v, tid)
        return m
    def assoc(defid_):
        rows = _edge_rows(dc, "SELECT ssot__Id__c FROM ssot__AiAgentTagDefinitionAssociation__dlm WHERE "
                          "ssot__AiAgentTagDefinitionId__c='%s' AND ssot__AiAgentApiName__c='%s'"
                          % (defid_, AGENT_API_NAME))
        return rows[0][0] if rows else ""
    return {"defl_val": vals(d), "defl_assoc": assoc(d), "aband_val": vals(a), "aband_assoc": assoc(a)}


# ─── row-graph generator ─────────────────────────────────────────────────────
def build(org_id, planner, user_ids, std, now, n):
    rows = {o["object"]: [] for o in S.OBJECTS}
    ES = org_id
    created = _iso(now - _dt.timedelta(hours=8))

    # weighted archetype pick, deterministic by index
    bag = []
    for arc in ARCHETYPES:
        bag += [arc] * arc[6]

    # ---- tag defs we own: Intent (Generated) + Quality_Score (Predefined) ----
    for did, dev, name, dtype, stype in [
            (_uid("def", "intent"), INTENT_DEF, "Optimization Request Category", "Text", "Generated"),
            (_uid("def", "quality"), "Quality_Score", "Relevance Score", "Number", "Predefined")]:
        rows["AiAgentTagDefinition"].append({
            "Id": did, "Name": name, "DeveloperName": dev, "DataType": dtype, "SourceType": stype,
            "Status": "Active", "Description": name, "CreatedDate": created,
            "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
        rows["AiAgentTagDefinitionAssociation"].append({
            "Id": _uid("defassoc", dev), "AiAgentApiName": AGENT_API_NAME, "AiAgentTagDefinitionId": did,
            "IsActive": "true", "CreatedDate": created, "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
    intent_def, quality_def = _uid("def", "intent"), _uid("def", "quality")
    intent_assoc, quality_assoc = _uid("defassoc", INTENT_DEF), _uid("defassoc", "Quality_Score")
    q_tag = {}
    for s in range(1, 6):
        q_tag[s] = _uid("tag", "q", s)
        rows["AiAgentTag"].append({"Id": q_tag[s], "AiAgentTagDefinitionId": quality_def, "Value": str(s),
                                   "Description": str(s), "IsActive": "true", "CreatedDate": created,
                                   "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
    intent_tag = {}
    for arc in ARCHETYPES:
        iv = arc[1]
        if iv not in intent_tag:
            intent_tag[iv] = _uid("tag", "intent", iv)
            rows["AiAgentTag"].append({"Id": intent_tag[iv], "AiAgentTagDefinitionId": intent_def, "Value": iv,
                                       "Description": iv, "IsActive": "true", "CreatedDate": created,
                                       "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})

    # ---- sessions ----
    for i in range(n):
        topic, intent, quality, outcome, action, fails, _w = bag[i * 2654435761 % len(bag)]
        sid = _uid("sess", i)
        uid = user_ids[i % len(user_ids)] if user_ids else "005000000000000AAA"
        uobj = "MessagingEndUser" if str(uid).startswith("0PA") else "User"
        agent_pid, user_pid = _uid("part", i, "a"), _uid("part", i, "u")
        # spread over the last DAYS_SPREAD days (never day 0), a few minutes long
        start = now - _dt.timedelta(days=1 + (i % DAYS_SPREAD), minutes=(i * 7) % 600)
        t0 = start
        int_id = _uid("int", i)
        trace = _hex(32, i)

        # steps: VU -> TOPIC -> router(LLM) -> subagent(LLM) -> ACTION (+error) -> guard
        specs = [("VARIABLE_UPDATE_STEP", "__state_update_action__", "", ""),
                 ("TOPIC_STEP", topic, "", ""),
                 ("LLM_STEP", "agent_router", _json({"gen_ai.request.model": "llmgateway__GPT41"}),
                  _json({"gen_ai.response.finish_reasons": "tool_calls",
                         "gen_ai.output.tool_names": "go_to_" + topic, "mgr.output.payload_type": "llm_event"})),
                 ("LLM_STEP", topic, "", _json({"gen_ai.response.finish_reasons": "tool_calls",
                                                 "gen_ai.output.tool_names": action, "mgr.output.payload_type": "llm_event"})),
                 ("ACTION_STEP", action, _json({"mgr.tool.argument_keys": "id"}),
                  _json({"mgr.output.payload_type": "tool_event",
                         "mgr.tool.status": "error" if fails else "success"})),
                 ("TRUST_GUARDRAILS_STEP", "InstructionAdherence", "", "")]
        walk = t0
        prev = ""
        for si, (stype, name, iv, ov) in enumerate(specs):
            ss = walk
            dur = 0 if stype in ("VARIABLE_UPDATE_STEP", "TOPIC_STEP") else (16 if fails and stype == "ACTION_STEP" else 1)
            se = ss + _dt.timedelta(seconds=dur)
            err = ("Action %s failed: the downstream service did not return a result." % action) \
                if (fails and stype == "ACTION_STEP") else ""
            step_id = _uid("step", i, si)
            rows["AiAgentInteractionStep"].append({
                "id": step_id, "aiAgentInteractionId": int_id, "AiAgentInteractionStepType": stype,
                "name": name, "inputValueText": iv, "outputValueText": ov,
                "startTimestamp": _iso(ss), "endTimestamp": _iso(se), "prevStepId": prev,
                "errorMessageText": err, "attributeText": "", "DataSourceId": DATA_SOURCE_PREFIX,
                "ExternalSourceId": ES})
            prev = step_id
            walk = se + _dt.timedelta(seconds=1)
        turn_end = walk

        rows["AiAgentInteraction"].append({
            "Id": int_id, "AiAgentSessionId": sid, "TopicApiName": topic, "AiAgentInteractionType": "TURN",
            "SessionOwnerId": uid, "SessionOwnerObject": uobj, "StartTimestamp": _iso(t0),
            "EndTimestamp": _iso(turn_end), "TraceId": trace, "SpandId": _hex(16, i),
            "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
        for role, pid, mtype, text, ts in [
                (user_pid, user_pid, "Input", "I need help with %s." % intent.lower(), t0),
                (agent_pid, agent_pid, "Output",
                 ("I've taken care of that for you." if not fails
                  else "I'm sorry — I wasn't able to complete that request."), turn_end)]:
            rows["AiAgentInteractionMessage"].append({
                "Id": _uid("msg", i, mtype), "AiAgentSessionId": sid, "AiAgentInteractionId": int_id,
                "AiAgentSessionParticipantId": pid, "AiAgentInteractionMessageType": mtype,
                "AiAgentInteractionMsgContentType": "text/plain", "ContentText": text,
                "MessageSentTimestamp": _iso(ts), "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})

        # SESSION_END interaction + closure step (the escalation signal)
        end_id = _uid("int", i, "end")
        rows["AiAgentInteraction"].append({
            "Id": end_id, "AiAgentSessionId": sid, "TopicApiName": "NOT_SET",
            "AiAgentInteractionType": "SESSION_END", "SessionOwnerId": uid, "SessionOwnerObject": uobj,
            "StartTimestamp": _iso(turn_end), "EndTimestamp": _iso(turn_end), "TraceId": _hex(32, i + 99),
            "SpandId": _hex(16, i + 99), "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
        rows["AiAgentInteractionStep"].append({
            "id": _uid("step", i, "end"), "aiAgentInteractionId": end_id,
            "AiAgentInteractionStepType": "SESSION_END", "name": CLOSE_NAME[outcome],
            "inputValueText": "", "outputValueText": "", "startTimestamp": _iso(turn_end),
            "endTimestamp": _iso(turn_end), "prevStepId": "", "errorMessageText": "", "attributeText": "",
            "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})

        # moment + junction + intent/quality tag associations
        mid = _uid("moment", i)
        rows["AiAgentMoment"].append({
            "Id": mid, "AiAgentSessionId": sid, "AiAgentApiName": AGENT_API_NAME,
            "AiAgentVersionApiName": AGENT_VERSION, "RequestSummaryText": "User asked about %s." % intent,
            "ResponseSummaryText": ("Resolved." if not fails else "Could not complete the request."),
            "StartTimestamp": _iso(t0), "EndTimestamp": _iso(turn_end),
            "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
        rows["AiAgentMomentInteraction"].append({
            "Id": _uid("momint", i), "AiAgentMomentId": mid, "AiAgentInteractionId": int_id,
            "StartTimestamp": _iso(t0), "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
        for tag_id, assoc, val, reason in [
                (intent_tag[intent], intent_assoc, intent, "Categorized as " + intent),
                (q_tag[quality], quality_assoc, str(quality), "Quality score %d" % quality)]:
            rows["AiAgentTagAssociation"].append({
                "Id": _uid("ta", i, val), "AiAgentSessionId": sid, "AiAgentMomentId": mid, "AiAgentTagId": tag_id,
                "AiAgentTagDefinitionAssociationId": assoc, "AssociationReasonText": reason,
                "ValueText": val, "SourceType": "PROMPT_TEMPLATE", "AiAgentSessionStartTimestamp": _iso(start),
                "CreatedDate": _iso(turn_end), "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})

        # session-level Deflection/Abandonment score assocs (skip escalated: no score,
        # else a 4-5 deflection would reclassify it Deflected). Reference the PLATFORM
        # std_ tag rows + def-assocs resolved earlier.
        if std and outcome != "escalated":
            dv = "5" if outcome == "deflected" else ("1" if quality <= 1 else "2")
            av_row = "FALSE" if outcome == "deflected" else "TRUE"   # tag ROW value (uppercase)
            av_txt = av_row.lower()                                   # written ValueText (lowercase)
            if dv in std["defl_val"]:
                rows["AiAgentTagAssociation"].append({
                    "Id": _uid("score", i, "defl"), "AiAgentSessionId": sid, "AiAgentMomentId": "",
                    "AiAgentTagId": std["defl_val"][dv], "AiAgentTagDefinitionAssociationId": std["defl_assoc"],
                    "AssociationReasonText": "Deflection score " + dv, "ValueText": dv, "SourceType": "PROMPT_TEMPLATE",
                    "AiAgentSessionStartTimestamp": _iso(start), "CreatedDate": _iso(turn_end),
                    "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
            if av_row in std["aband_val"]:
                rows["AiAgentTagAssociation"].append({
                    "Id": _uid("score", i, "aband"), "AiAgentSessionId": sid, "AiAgentMomentId": "",
                    "AiAgentTagId": std["aband_val"][av_row], "AiAgentTagDefinitionAssociationId": std["aband_assoc"],
                    "AssociationReasonText": "Abandonment=" + av_txt, "ValueText": av_txt, "SourceType": "PROMPT_TEMPLATE",
                    "AiAgentSessionStartTimestamp": _iso(start), "CreatedDate": _iso(turn_end),
                    "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})

        for pid, role, obj_, part in [(agent_pid, "AGENT", "GenAiPlannerDefinition", planner),
                                      (user_pid, "USER", uobj, uid)]:
            rows["AiAgentSessionParticipant"].append({
                "Id": pid, "AiAgentSessionId": sid, "AiAgentApiName": AGENT_API_NAME,
                "AiAgentVersionApiName": AGENT_VERSION, "AiAgentTemplateApiName": "",
                "AiAgentType": "EinsteinServiceAgent", "AiAgentSessionParticipantRole": role,
                "ParticipantId": part, "ParticipantObject": obj_, "ParticipantAttributes": "{}",
                "StartTimestamp": _iso(start), "EndTimestamp": _iso(turn_end),
                "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
        rows["AiAgentSession"].append({
            "Id": sid, "AiAgentChannelType": CHANNEL, "AiAgentSessionEndType": END_TYPE[outcome],
            "StartTimestamp": _iso(start), "EndTimestamp": _iso(turn_end), "IndividualId": "NOT_SET",
            "PreviousSessionId": "NOT_SET", "SessionOwnerObject": "NOT_SET", "VariableText": "NOT_SET",
            "DataSourceId": DATA_SOURCE_PREFIX, "ExternalSourceId": ES})
    return rows


# ─── CSV + CLI ───────────────────────────────────────────────────────────────
def to_csv(o, rws):
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(o["cols"])
    for r in rws:
        w.writerow(["" if r.get(c) is None else r.get(c) for c in o["cols"]])
    return buf.getvalue().encode()


def cmd_setup(dc, org):
    for o in S.OBJECTS:
        obj = o["object"]; cname = S.STREAM_BASE[obj]   # short name == sourceName here
        ex = dc.find_ingest_connection(cname)
        if ex:
            cid, returned = ex.get("id"), ex.get("name", cname)
        else:
            _, returned, cid = dc.create_ingest_connection(cname, cname)
        dc.put_schema(cid, obj, S.schema_fields(o))
        base = S.STREAM_BASE[obj]
        stream, dlo = dc.find_stream_dlo(base)
        if not dlo:
            dc.create_stream(base, returned, obj, o["pk"], category=S.CATEGORY[obj],
                             event_time_field=S.EVENT_TIME.get(obj))
            import time
            for _ in range(6):
                time.sleep(4); stream, dlo = dc.find_stream_dlo(base)
                if dlo: break
        if dlo:
            dlo_dev = dlo if dlo.endswith("__dll") else dlo + "__dll"
            code, resp = dc.create_mapping(dlo_dev, o["dmo"], [(a + "__c", b) for a, b in o["map"]])
            ok = code in (200, 201) or "DUPLICATE" in json.dumps(resp)
            print("  %-34s map=%s" % (obj, "ok" if ok else ("FAIL %s %s" % (code, str(resp)[:160]))))
        else:
            print("  %-34s DLO not materialised yet — re-run setup" % obj)


def cmd_push(dc, org, n):
    org_id, planner, users, _ = resolve_identities(org)
    std = resolve_std_scorers(dc)
    if not std:
        print("  WARN: std_Deflection/Abandonment tag-defs not found for %s — Deflection/Abandon "
              "will read 0. Deploy the agent + enable Agentforce Optimization, then re-run." % AGENT_API_NAME)
    now = _dt.datetime.now(_dt.timezone.utc)
    rows = build(org_id, planner, users, std, now, n)
    for o in S.OBJECTS:
        rws = rows.get(o["object"], [])
        if rws:
            job = dc.ingest_csv(o["object"], S.STREAM_BASE[o["object"]], to_csv(o, rws))
            print("  pushed %-34s rows=%-4d job=%s" % (o["object"], len(rws), job))
    print("push: submitted (rows land in the DMOs within ~1-4 min).")


def cmd_verify(dc, org):
    p = DATA_SOURCE_PREFIX
    for dmo in ["ssot__AiAgentSession__dlm", "ssot__AiAgentInteraction__dlm",
                "ssot__AiAgentInteractionStep__dlm", "ssot__AiAgentMoment__dlm", "ssot__AiAgentTagAssociation__dlm"]:
        _, r = dc.query("SELECT COUNT(*) FROM %s WHERE ssot__DataSourceId__c LIKE '%s%%'" % (dmo, p))
        n = (r.get("data") or [[None]])[0][0] if isinstance(r, dict) else r
        print("  %-42s %s" % (dmo, n))
    for label, sql in [
        ("engaged sessions (ACTION_STEP)",
         "SELECT COUNT(DISTINCT i.ssot__AiAgentSessionId__c) FROM ssot__AiAgentInteractionStep__dlm st "
         "JOIN ssot__AiAgentInteraction__dlm i ON i.ssot__Id__c=st.ssot__AiAgentInteractionId__c "
         "WHERE st.ssot__AiAgentInteractionStepType__c='ACTION_STEP' AND st.ssot__DataSourceId__c LIKE '%s%%'" % p),
        ("escalated sessions (CLOSED_TRANSFERRED)",
         "SELECT COUNT(DISTINCT i.ssot__AiAgentSessionId__c) FROM ssot__AiAgentInteractionStep__dlm st "
         "JOIN ssot__AiAgentInteraction__dlm i ON i.ssot__Id__c=st.ssot__AiAgentInteractionId__c "
         "WHERE st.ssot__AiAgentInteractionStepType__c='SESSION_END' AND st.ssot__Name__c='CLOSED_TRANSFERRED' "
         "AND st.ssot__DataSourceId__c LIKE '%s%%'" % p)]:
        _, r = dc.query(sql)
        print("  %-42s %s" % (label, (r.get("data") or [[None]])[0][0] if isinstance(r, dict) else r))


def cmd_teardown(dc, org):
    import time
    st_names = []
    for o in reversed(S.OBJECTS):
        stream, _ = dc.find_stream_dlo(S.STREAM_BASE[o["object"]])
        if stream:
            dc.delete_stream(stream); st_names.append(o["object"]); print("  stream del %s" % o["object"])
    time.sleep(20)
    for o in reversed(S.OBJECTS):
        c = dc.find_ingest_connection(S.STREAM_BASE[o["object"]])
        if c and c.get("id"):
            dc.delete_connection(c["id"]); print("  conn del %s" % o["object"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["setup", "push", "verify", "teardown"])
    ap.add_argument("--target-org", default="")
    ap.add_argument("-n", "--count", type=int, default=200)
    a = ap.parse_args()
    dc = DC()
    print("[dc] core=%s cdp=%s" % (dc.core_url, dc.cdp_url))
    {"setup": lambda: cmd_setup(dc, a.target_org),
     "push": lambda: cmd_push(dc, a.target_org, a.count),
     "verify": lambda: cmd_verify(dc, a.target_org),
     "teardown": lambda: cmd_teardown(dc, a.target_org)}[a.command]()


if __name__ == "__main__":
    main()
