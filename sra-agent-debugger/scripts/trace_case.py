#!/usr/bin/env python3
"""
SRA Agent Debugger — Case-level trace script.

Pulls GenOpPlan, RecActorActionFeed, and Data Cloud session trace for a Case ID.
Outputs a structured .txt file for AI analysis.

Usage:
    python3 trace_case.py --case 500gz000001mVlhAAE --org MetaRLUAT
"""

import argparse
import html
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def sf_query(soql: str, org: str) -> list:
    """Run a SOQL query via sf CLI and return records."""
    result = subprocess.run(
        ["sf", "data", "query", "-q", soql, "-o", org, "--json"],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        return []
    data = json.loads(result.stdout)
    return data.get("result", {}).get("records", [])


def sf_api_get(path: str, org: str) -> dict:
    """Run a REST API GET via sf CLI."""
    result = subprocess.run(
        ["sf", "api", "request", "rest", path, "-o", org],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def sf_api_post(path: str, body: dict, org: str) -> dict:
    """Run a REST API POST via sf CLI."""
    result = subprocess.run(
        ["sf", "api", "request", "rest", "--method", "POST",
         "--body", json.dumps(body), path, "-o", org],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def dc_query(sql: str, org: str) -> list:
    """Query Data Cloud SSOT and return data rows."""
    resp = sf_api_post("/services/data/v62.0/ssot/query", {"sql": sql}, org)
    return resp.get("data", [])


def resolve_case_number(case_id: str, org: str) -> str:
    """Resolve Case Number from Case ID."""
    records = sf_query(f"SELECT CaseNumber FROM Case WHERE Id = '{case_id}' LIMIT 1", org)
    if records:
        return records[0].get("CaseNumber", "")
    return ""


def fetch_gen_op_plans(case_id: str, org: str) -> list:
    """Fetch GenOpPlan records for a Case."""
    soql = (
        "SELECT Id, Intent, Type, PlanHeader, PlanSummary, "
        "TopicName, TopicDescription, CreatedDate "
        f"FROM GenOpPlan WHERE ParentId = '{case_id}' "
        "ORDER BY CreatedDate DESC LIMIT 20"
    )
    return sf_query(soql, org)


def fetch_rec_actor_feeds(case_id: str, org: str) -> list:
    """Fetch RecActorActionFeed via REST API (v67 then v66)."""
    soql = (
        "SELECT Id, Content, CreatedDate FROM RecActorActionFeed "
        f"WHERE RelatedRecordId = '{case_id}' "
        "ORDER BY CreatedDate DESC LIMIT 50"
    )
    from urllib.parse import quote
    encoded = quote(soql)

    for ver in ["v67.0", "v66.0"]:
        resp = sf_api_get(f"/services/data/{ver}/query?q={encoded}", org)
        if resp and "records" in resp:
            return resp["records"]
        if resp.get("errorCode") == "NOT_FOUND":
            continue
        if resp:
            return resp.get("records", [])
    return []


def resolve_session_ids(case_number: str, org: str) -> list:
    """Find session UUIDs from DC messages matching case number patterns."""
    patterns = [
        f'%"caseNumber":{case_number}%',
        f'%"Case Number","value":"{case_number}"%',
        f'%Case ID: {case_number}:%',
        f'%Case Number&quot;,&quot;value&quot;:&quot;{case_number}&quot;%',
    ]

    seen = set()
    ids = []

    for pattern in patterns:
        escaped_pattern = pattern.replace("'", "\\'")
        sql = (
            "SELECT ssot__AiAgentSessionId__c, ssot__MessageSentTimestamp__c "
            "FROM ssot__AiAgentInteractionMessage__dlm "
            f"WHERE ssot__ContentText__c LIKE '{escaped_pattern}' "
            "ORDER BY ssot__MessageSentTimestamp__c DESC LIMIT 20"
        )
        rows = dc_query(sql, org)
        for row in rows:
            sid = row.get("ssot__AiAgentSessionId__c")
            if sid and sid not in seen:
                seen.add(sid)
                ids.append(sid)
        if ids:
            return ids
    return ids


def trace_session(sid: str, org: str) -> dict:
    """Fetch full trace for one session."""
    trace = {"sessionId": sid}

    # Session metadata
    rows = dc_query(
        "SELECT ssot__Id__c, ssot__AiAgentChannelType__c, "
        "ssot__StartTimestamp__c, ssot__EndTimestamp__c, "
        "ssot__AiAgentSessionEndType__c "
        f"FROM ssot__AIAgentSession__dlm WHERE ssot__Id__c = '{sid}' LIMIT 1", org
    )
    if rows:
        s = rows[0]
        trace["channelType"] = s.get("ssot__AiAgentChannelType__c")
        trace["startTime"] = s.get("ssot__StartTimestamp__c")
        trace["endTime"] = s.get("ssot__EndTimestamp__c")
        trace["endType"] = s.get("ssot__AiAgentSessionEndType__c")

    # Agent identity
    rows = dc_query(
        "SELECT ssot__AiAgentApiName__c, ssot__AiAgentVersionApiName__c "
        "FROM ssot__AiAgentSessionParticipant__dlm "
        f"WHERE ssot__AiAgentSessionId__c = '{sid}' "
        "AND ssot__AiAgentSessionParticipantRole__c = 'AGENT' LIMIT 1", org
    )
    if rows:
        trace["agentApiName"] = rows[0].get("ssot__AiAgentApiName__c")
        trace["agentVersionApi"] = rows[0].get("ssot__AiAgentVersionApiName__c")

    # Interactions
    interactions = dc_query(
        "SELECT ssot__Id__c, ssot__AiAgentInteractionType__c, "
        "ssot__TopicApiName__c, ssot__StartTimestamp__c, ssot__EndTimestamp__c "
        "FROM ssot__AIAgentInteraction__dlm "
        f"WHERE ssot__AiAgentSessionId__c = '{sid}' "
        "ORDER BY ssot__StartTimestamp__c", org
    )
    trace["interactions"] = interactions
    ix_ids = [ix.get("ssot__Id__c") for ix in interactions if ix.get("ssot__Id__c")]

    # Messages
    messages = dc_query(
        "SELECT ssot__Id__c, ssot__AiAgentInteractionMessageType__c, "
        "ssot__ContentText__c, ssot__MessageSentTimestamp__c "
        "FROM ssot__AiAgentInteractionMessage__dlm "
        f"WHERE ssot__AiAgentSessionId__c = '{sid}' "
        "ORDER BY ssot__MessageSentTimestamp__c LIMIT 100", org
    )
    trace["messages"] = messages

    # Steps
    trace["steps"] = []
    if ix_ids:
        in_clause = ",".join(f"'{i}'" for i in ix_ids)
        steps = dc_query(
            "SELECT ssot__Id__c, ssot__AiAgentInteractionId__c, "
            "ssot__AiAgentInteractionStepType__c, ssot__Name__c, "
            "ssot__InputValueText__c, ssot__OutputValueText__c, "
            "ssot__ErrorMessageText__c, ssot__StartTimestamp__c, ssot__EndTimestamp__c "
            "FROM ssot__AIAgentInteractionStep__dlm "
            f"WHERE ssot__AiAgentInteractionId__c IN ({in_clause}) "
            "ORDER BY ssot__StartTimestamp__c", org
        )
        trace["steps"] = steps

    # Gateway requests
    gw_requests = dc_query(
        "SELECT gatewayRequestId__c, feature__c, model__c, "
        "promptTemplateDevName__c, promptTokens__c, completionTokens__c, "
        "totalTokens__c, timestamp__c "
        "FROM GenAIGatewayRequest__dlm "
        f"WHERE sessionId__c LIKE '%{sid}%' "
        "ORDER BY timestamp__c", org
    )
    trace["gatewayRequests"] = gw_requests
    gw_ids = [gw.get("gatewayRequestId__c") for gw in gw_requests if gw.get("gatewayRequestId__c")]

    # Gateway responses + action metadata + grounded records
    trace["gatewayResponses"] = []
    trace["actionMetadata"] = []
    trace["groundedRecords"] = []

    if gw_ids:
        in_clause = ",".join(f"'{i}'" for i in gw_ids)

        trace["gatewayResponses"] = dc_query(
            "SELECT generationResponseId__c, generationRequestId__c, timestamp__c "
            "FROM GenAIGatewayResponse__dlm "
            f"WHERE generationRequestId__c IN ({in_clause}) "
            "ORDER BY timestamp__c", org
        )

        trace["actionMetadata"] = dc_query(
            "SELECT id__c, parent__c, metadata__c, feature__c, timestamp__c "
            "FROM GenAIGtwyRequestMetadata__dlm "
            f"WHERE parent__c IN ({in_clause}) AND metadataType__c = 'ToolCall' "
            "ORDER BY timestamp__c", org
        )

        trace["groundedRecords"] = dc_query(
            "SELECT id__c, recordId__c, type__c, name__c, value__c, timestamp__c "
            "FROM GenAIGtwyObjRecord__dlm "
            f"WHERE parent__c IN ({in_clause}) "
            "ORDER BY timestamp__c", org
        )

    return trace


def unescape(text: str) -> str:
    """Unescape HTML entities."""
    if not text:
        return text or ""
    return html.unescape(text)


def format_output(case_id: str, case_number: str, org: str,
                  gen_op_plans: list, feeds: list, sessions: list) -> str:
    """Format all data into a structured text file."""
    lines = []
    lines.append("SRA Agent Debugger — Session Trace Extract")
    lines.append(f"Case: {case_number} ({case_id})")
    lines.append(f"Org: {org}")
    lines.append(f"Extracted: {datetime.utcnow().isoformat()}Z")
    lines.append("=" * 80)

    # GenOpPlan
    if gen_op_plans:
        lines.append("")
        lines.append("## Summary Plan (GenOpPlan)")
        lines.append("-" * 40)
        for i, p in enumerate(gen_op_plans, 1):
            lines.append(f"[{i}] Created: {p.get('CreatedDate', '')} | Type: {p.get('Type', '')}")
            lines.append(f"  Topic: {p.get('TopicName', '')}")
            lines.append(f"  Intent: {p.get('Intent', '')}")
            lines.append(f"  Header: {p.get('PlanHeader', '')}")
            lines.append(f"  Summary: {p.get('PlanSummary', '')}")
            if p.get("TopicDescription"):
                lines.append(f"  Topic Description: {p['TopicDescription']}")
            lines.append("")

    # RecActorActionFeed
    if feeds:
        lines.append("")
        lines.append("## RecActorActionFeed")
        lines.append("-" * 40)
        for i, f in enumerate(feeds, 1):
            lines.append(f"[{i}] Created: {f.get('CreatedDate', '')}")
            lines.append(unescape(f.get("Content", "(empty)")))
            lines.append("")

    # Sessions
    if sessions:
        for si, s in enumerate(sessions, 1):
            lines.append("")
            lines.append("=" * 80)
            lines.append(f"## Session {si}: {s['sessionId']}")
            lines.append(f"Agent: {s.get('agentApiName', 'unknown')} ({s.get('agentVersionApi', '')})")
            lines.append(f"Channel: {s.get('channelType', '')} | End: {s.get('endType', '')}")
            lines.append(f"Time: {s.get('startTime', '')} -> {s.get('endTime', '')}")

            gw_count = len(s.get("gatewayRequests", []))
            resp_count = len(s.get("gatewayResponses", []))
            lines.append(f"Gateway Requests: {gw_count} | Responses: {resp_count} | Audit OK: {gw_count == resp_count}")
            lines.append("-" * 40)

            # Build topic map
            topic_map = {}
            for ix in s.get("interactions", []):
                ix_id = ix.get("ssot__Id__c")
                topic = ix.get("ssot__TopicApiName__c", "(unknown)")
                if ix_id:
                    topic_map[ix_id] = topic

            # Dynamic Plan Steps
            steps = s.get("steps", [])
            plan_steps = [st for st in steps if st.get("ssot__AiAgentInteractionStepType__c") in
                         ("LLM_STEP", "ACTION_STEP", "TOPIC_STEP")]
            if plan_steps:
                lines.append("")
                lines.append("### Dynamic Plan Steps")
                for seq, ps in enumerate(plan_steps):
                    step_type = ps.get("ssot__AiAgentInteractionStepType__c", "")
                    name = ps.get("ssot__Name__c", "(unnamed)")
                    ix_id = ps.get("ssot__AiAgentInteractionId__c", "")
                    topic = topic_map.get(ix_id, "")
                    start = ps.get("ssot__StartTimestamp__c", "")
                    end = ps.get("ssot__EndTimestamp__c", "")
                    error = ps.get("ssot__ErrorMessageText__c")

                    lines.append(f"  [{seq}] {step_type} - {name}")
                    lines.append(f"      Topic: {topic}")
                    lines.append(f"      Time: {start} -> {end}")

                    if error and error != "NOT_SET":
                        lines.append(f"      ERROR: {unescape(error)}")

                    input_text = ps.get("ssot__InputValueText__c")
                    if input_text:
                        lines.append(f"      Input: {unescape(input_text)[:2000]}")

                    output_text = ps.get("ssot__OutputValueText__c")
                    if output_text:
                        lines.append(f"      Output: {unescape(output_text)[:2000]}")
                    lines.append("")

            # Transcript
            messages = s.get("messages", [])
            if messages:
                lines.append("")
                lines.append("### Transcript")
                for m in messages:
                    msg_type = m.get("ssot__AiAgentInteractionMessageType__c", "")
                    ts = m.get("ssot__MessageSentTimestamp__c", "")
                    content = unescape(m.get("ssot__ContentText__c", "(empty)"))
                    lines.append(f"  [{msg_type}] {ts}")
                    lines.append(f"  {content[:2000]}")
                    lines.append("")

            # Gateway Calls
            gw_reqs = s.get("gatewayRequests", [])
            if gw_reqs:
                lines.append("")
                lines.append("### Gateway Calls")
                for gw in gw_reqs:
                    lines.append(
                        f"  {gw.get('timestamp__c', '')} | {gw.get('feature__c', '')} | "
                        f"{gw.get('model__c', '')} | Template: {gw.get('promptTemplateDevName__c', '')}"
                    )
                    lines.append(
                        f"    Tokens - Prompt: {gw.get('promptTokens__c', 0)}, "
                        f"Completion: {gw.get('completionTokens__c', 0)}, "
                        f"Total: {gw.get('totalTokens__c', 0)}"
                    )

            # Action Metadata
            actions = s.get("actionMetadata", [])
            if actions:
                lines.append("")
                lines.append("### Action Metadata (ToolCalls)")
                for am in actions:
                    lines.append(f"  [{am.get('feature__c', '')}] {am.get('timestamp__c', '')}")
                    metadata = unescape(am.get("metadata__c", ""))
                    lines.append(f"  {metadata[:2000]}")
                    lines.append("")

            # Grounded Records
            grounds = s.get("groundedRecords", [])
            if grounds:
                lines.append("")
                lines.append("### Grounded Records")
                for gr in grounds:
                    lines.append(
                        f"  {gr.get('type__c', '')} | {gr.get('name__c', '')} | "
                        f"RecordId: {gr.get('recordId__c', '')} | {gr.get('timestamp__c', '')}"
                    )
                    val = gr.get("value__c")
                    if val:
                        lines.append(f"    Value: {val[:500]}")

    if not sessions:
        lines.append("")
        lines.append("## No Agentforce sessions found in Data Cloud for this Case.")
        lines.append("(Data Cloud may not have materialized yet, or the case number pattern is not recognized.)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="SRA Agent Debugger - Case Trace")
    parser.add_argument("--case", required=True, help="18-char Case record ID")
    parser.add_argument("--org", required=True, help="sf CLI org alias")
    parser.add_argument("--max-sessions", type=int, default=3, help="Max sessions to trace")
    parser.add_argument("--output", help="Override output directory")
    args = parser.parse_args()

    case_id = args.case.strip()
    org = args.org.strip()

    print(f"[1/6] Resolving Case Number for {case_id}...")
    case_number = resolve_case_number(case_id, org)
    if not case_number:
        print(f"ERROR: Case not found: {case_id}")
        sys.exit(1)
    print(f"  Case Number: {case_number}")

    print(f"[2/6] Fetching GenOpPlan...")
    gen_op_plans = fetch_gen_op_plans(case_id, org)
    print(f"  Found {len(gen_op_plans)} plan(s)")

    print(f"[3/6] Fetching RecActorActionFeed...")
    feeds = fetch_rec_actor_feeds(case_id, org)
    print(f"  Found {len(feeds)} feed record(s)")

    print(f"[4/6] Resolving session IDs from Data Cloud...")
    session_ids = resolve_session_ids(case_number, org)
    print(f"  Found {len(session_ids)} session(s)")

    print(f"[5/6] Tracing sessions (max {args.max_sessions})...")
    sessions = []
    for i, sid in enumerate(session_ids[:args.max_sessions]):
        print(f"  Tracing session {i+1}/{min(len(session_ids), args.max_sessions)}: {sid[:12]}...")
        sessions.append(trace_session(sid, org))

    print(f"[6/6] Writing output...")
    output_text = format_output(case_id, case_number, org, gen_op_plans, feeds, sessions)

    # Determine output path
    if args.output:
        out_dir = Path(args.output)
    else:
        out_dir = Path.home() / ".claude" / "data" / "sra-agent-debugger" / org / case_number
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"trace_{timestamp}.txt"
    out_file.write_text(output_text, encoding="utf-8")

    print(f"\nDone! Output: {out_file}")
    print(f"  GenOpPlans: {len(gen_op_plans)}")
    print(f"  RecActorFeeds: {len(feeds)}")
    print(f"  Sessions traced: {len(sessions)}")

    # Also print the output for immediate Claude analysis
    print("\n" + "=" * 80)
    print(output_text)


if __name__ == "__main__":
    main()
