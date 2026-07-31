#!/usr/bin/env python3
"""
SRA Agent Debugger — Session Trace (Case or MessagingSession).

Pulls GenOpPlan, RecActorActionFeed (with knowledge grounding analysis),
and Data Cloud session trace for a Case ID or MessagingSession ID.
Outputs a structured .txt file for AI analysis.

Usage:
    python3 trace_session.py --id 500gz000001mVlhAAE --org MetaRLUAT
    python3 trace_session.py --id 0MwHo000000vnLUKAY --org mySDO
"""

import argparse
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


# ═══════════════════════════════════════════════════════════════════════════════
# SF CLI Helpers
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# Record Resolution
# ═══════════════════════════════════════════════════════════════════════════════

def detect_record_type(record_id: str) -> str:
    """Detect record type from ID prefix."""
    prefix = record_id[:3]
    if prefix == "500":
        return "Case"
    elif prefix == "0Mw":
        return "MessagingSession"
    elif prefix == "0LQ":
        return "VoiceCall"
    else:
        return "Unknown"


def resolve_case(case_id: str, org: str) -> dict:
    """Resolve Case metadata."""
    records = sf_query(
        f"SELECT Id, CaseNumber, Subject, Status, ContactId, Contact.Name "
        f"FROM Case WHERE Id = '{case_id}' LIMIT 1", org
    )
    if records:
        return records[0]
    return {}


def resolve_messaging_session(session_id: str, org: str) -> dict:
    """Resolve MessagingSession metadata and related Case."""
    records = sf_query(
        f"SELECT Id, Name, Status, EndUserContactId, "
        f"CaseId, Case.CaseNumber, Case.Subject, "
        f"StartTime, EndTime, Channel "
        f"FROM MessagingSession WHERE Id = '{session_id}' LIMIT 1", org
    )
    if records:
        return records[0]
    return {}


def resolve_voice_call(voice_call_id: str, org: str) -> dict:
    """Resolve VoiceCall metadata and related Case."""
    records = sf_query(
        f"SELECT Id, CallType, CallStartDateTime, CallEndDateTime, "
        f"CallDurationInSeconds, CallDisposition, "
        f"RelatedRecordId, "
        f"FromPhoneNumber, ToPhoneNumber "
        f"FROM VoiceCall WHERE Id = '{voice_call_id}' LIMIT 1", org
    )
    if not records:
        return {}
    vc = records[0]
    # Try to resolve related Case
    related_id = vc.get("RelatedRecordId", "")
    if related_id and related_id[:3] == "500":
        cases = sf_query(
            f"SELECT Id, CaseNumber, Subject, Status FROM Case WHERE Id = '{related_id}' LIMIT 1", org
        )
        if cases:
            vc["Case"] = cases[0]
            vc["CaseId"] = cases[0].get("Id")
    return vc


# ═══════════════════════════════════════════════════════════════════════════════
# Core SOQL Queries (GenOpPlan, RecActorActionFeed)
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_gen_op_plans(parent_id: str, org: str) -> list:
    """Fetch GenOpPlan records for a parent record (Case or MessagingSession)."""
    soql = (
        "SELECT Id, Intent, Type, PlanHeader, PlanSummary, "
        "TopicName, TopicDescription, CreatedDate "
        f"FROM GenOpPlan WHERE ParentId = '{parent_id}' "
        "ORDER BY CreatedDate DESC LIMIT 20"
    )
    return sf_query(soql, org)


def fetch_rec_actor_feeds(related_record_id: str, org: str) -> list:
    """Fetch RecActorActionFeed via REST API (v67 then v66).

    RelatedRecordId works for BOTH Case IDs and MessagingSession IDs.
    """
    soql = (
        "SELECT Id, Content, CreatedDate FROM RecActorActionFeed "
        f"WHERE RelatedRecordId = '{related_record_id}' "
        "ORDER BY CreatedDate DESC LIMIT 50"
    )
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


# ═══════════════════════════════════════════════════════════════════════════════
# Knowledge Grounding Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_knowledge_grounding(feeds: list) -> dict:
    """Analyze RecActorActionFeed for knowledge grounding status.

    Returns a dict with:
    - grounded_count: number of feed entries with citedReferences
    - empty_count: number of entries where citedReferences is empty []
    - missing_count: entries with no citedReferences field at all
    - articles_cited: list of unique article titles/IDs cited
    - grounding_failures: list of entries where knowledge retrieval failed
    """
    analysis = {
        "grounded_count": 0,
        "empty_count": 0,
        "missing_count": 0,
        "articles_cited": [],
        "grounding_failures": [],
        "total_feeds": len(feeds),
    }

    seen_articles = set()

    for feed in feeds:
        content = feed.get("Content", "")
        if not content:
            analysis["missing_count"] += 1
            continue

        # Try to parse content as JSON or find citedReferences within it
        cited_refs = extract_cited_references(content)

        if cited_refs is None:
            # No citedReferences field found in this entry
            analysis["missing_count"] += 1
        elif len(cited_refs) == 0:
            # citedReferences exists but is empty — knowledge retrieval FAILED
            analysis["empty_count"] += 1
            analysis["grounding_failures"].append({
                "date": feed.get("CreatedDate", ""),
                "content_preview": content[:200],
            })
        else:
            # Knowledge was successfully grounded
            analysis["grounded_count"] += 1
            for ref in cited_refs:
                title = ref.get("title") or ref.get("name") or ref.get("id", "unknown")
                if title not in seen_articles:
                    seen_articles.add(title)
                    analysis["articles_cited"].append(ref)

    return analysis


def extract_cited_references(content: str) -> list:
    """Extract citedReferences from feed Content.

    Content may be JSON or HTML-escaped JSON. Returns:
    - list of refs if found (may be empty [])
    - None if citedReferences field not present
    """
    # Unescape HTML entities first
    text = html.unescape(content)

    # Try direct JSON parse
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if "citedReferences" in data:
                return data["citedReferences"]
            # Check nested structures
            for key, val in data.items():
                if isinstance(val, dict) and "citedReferences" in val:
                    return val["citedReferences"]
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and "citedReferences" in item:
                            return item["citedReferences"]
    except (json.JSONDecodeError, TypeError):
        pass

    # Try regex for citedReferences in partially-structured content
    match = re.search(r'"citedReferences"\s*:\s*(\[.*?\])', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Data Cloud Session Resolution
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_session_ids_by_case(case_number: str, org: str) -> list:
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
            "SELECT aiAgentSessionId__c, messageSentTimestamp__c "
            "FROM AiAgentInteractionMessage__dll "
            f"WHERE contentText__c LIKE '{escaped_pattern}' "
            "ORDER BY messageSentTimestamp__c DESC LIMIT 20"
        )
        rows = dc_query(sql, org)
        for row in rows:
            sid = row.get("aiAgentSessionId__c")
            if sid and sid not in seen:
                seen.add(sid)
                ids.append(sid)
        if ids:
            return ids
    return ids


def resolve_session_ids_by_messaging(messaging_session_id: str, org: str) -> list:
    """Find DC session UUIDs for a MessagingSession ID.

    Tries multiple patterns:
    1. Direct match on messaging session ID in message content
    2. Match on the MessagingSession Name field
    3. Match on related Case number (if a Case is linked)
    """
    seen = set()
    ids = []

    # Pattern 1: MessagingSession ID in content
    patterns = [
        f'%{messaging_session_id}%',
        f'%"messagingSessionId":"{messaging_session_id}"%',
    ]

    for pattern in patterns:
        escaped_pattern = pattern.replace("'", "\\'")
        sql = (
            "SELECT aiAgentSessionId__c, messageSentTimestamp__c "
            "FROM AiAgentInteractionMessage__dll "
            f"WHERE contentText__c LIKE '{escaped_pattern}' "
            "ORDER BY messageSentTimestamp__c DESC LIMIT 20"
        )
        rows = dc_query(sql, org)
        for row in rows:
            sid = row.get("aiAgentSessionId__c")
            if sid and sid not in seen:
                seen.add(sid)
                ids.append(sid)
        if ids:
            return ids

    # Pattern 2: Try the session channel type = messaging
    # Use time-based heuristic: query recent sessions and match by channel
    sql = (
        "SELECT id__c "
        "FROM AiAgentSession__dll "
        "WHERE aiAgentChannelTypeId__c = 'MESSAGING' "
        "ORDER BY startTimestamp__c DESC LIMIT 10"
    )
    rows = dc_query(sql, org)
    for row in rows:
        sid = row.get("id__c")
        if sid and sid not in seen:
            seen.add(sid)
            ids.append(sid)

    return ids


def resolve_session_ids_by_voice(voice_call_id: str, org: str) -> list:
    """Find session UUIDs for a VoiceCall via DC channel type = VOICE."""
    seen = set()
    ids = []

    # Pattern 1: VoiceCall ID in message content
    patterns = [
        f'%{voice_call_id}%',
        f'%"voiceCallId":"{voice_call_id}"%',
    ]
    for pattern in patterns:
        escaped_pattern = pattern.replace("'", "\\'")
        sql = (
            "SELECT aiAgentSessionId__c, messageSentTimestamp__c "
            "FROM AiAgentInteractionMessage__dll "
            f"WHERE contentText__c LIKE '{escaped_pattern}' "
            "ORDER BY messageSentTimestamp__c DESC LIMIT 20"
        )
        rows = dc_query(sql, org)
        for row in rows:
            sid = row.get("aiAgentSessionId__c")
            if sid and sid not in seen:
                seen.add(sid)
                ids.append(sid)
        if ids:
            return ids

    # Pattern 2: Recent VOICE channel sessions
    sql = (
        "SELECT id__c "
        "FROM AiAgentSession__dll "
        "WHERE aiAgentChannelTypeId__c = 'VOICE' "
        "ORDER BY startTimestamp__c DESC LIMIT 10"
    )
    rows = dc_query(sql, org)
    for row in rows:
        sid = row.get("id__c")
        if sid and sid not in seen:
            seen.add(sid)
            ids.append(sid)

    return ids


def resolve_session_ids_from_feeds(feeds: list) -> list:
    """Extract session UUIDs directly from RecActorActionFeed content.

    The feed entries contain URLs like:
    .../sessions/019ef228-90d0-7cbd-9a3d-186ac2cf52bb/messages
    This is the most reliable way to resolve the DC session UUID.
    """
    uuid_pattern = re.compile(
        r'/sessions/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    )
    seen = set()
    ids = []
    for feed in feeds:
        content = feed.get("Content", "") or ""
        for match in uuid_pattern.finditer(content):
            sid = match.group(1)
            if sid not in seen:
                seen.add(sid)
                ids.append(sid)
    return ids


# ═══════════════════════════════════════════════════════════════════════════════
# Full Session Trace
# ═══════════════════════════════════════════════════════════════════════════════

def trace_session(sid: str, org: str) -> dict:
    """Fetch full trace for one session."""
    trace = {"sessionId": sid}

    # Session metadata
    rows = dc_query(
        "SELECT id__c, aiAgentChannelTypeId__c, "
        "startTimestamp__c, endTimestamp__c, "
        "sessionEndType__c "
        f"FROM AiAgentSession__dll WHERE id__c = '{sid}' LIMIT 1", org
    )
    if rows:
        s = rows[0]
        trace["channelType"] = s.get("aiAgentChannelTypeId__c")
        trace["startTime"] = s.get("startTimestamp__c")
        trace["endTime"] = s.get("endTimestamp__c")
        trace["endType"] = s.get("sessionEndType__c")

    # Agent identity
    rows = dc_query(
        "SELECT aiAgentApiName__c, aiAgentVersionApiName__c "
        "FROM AiAgentSessionParticipant__dll "
        f"WHERE aiAgentSessionId__c = '{sid}' "
        "AND aiAgentSessionParticipantRole__c = 'AGENT' LIMIT 1", org
    )
    if rows:
        trace["agentApiName"] = rows[0].get("aiAgentApiName__c")
        trace["agentVersionApi"] = rows[0].get("aiAgentVersionApiName__c")

    # Interactions
    interactions = dc_query(
        "SELECT id__c, aiAgentInteractionTypeId__c, "
        "topicApiName__c, startTimestamp__c, endTimestamp__c "
        "FROM AiAgentInteraction__dll "
        f"WHERE aiAgentSessionId__c = '{sid}' "
        "ORDER BY startTimestamp__c", org
    )
    trace["interactions"] = interactions
    ix_ids = [ix.get("id__c") for ix in interactions if ix.get("id__c")]

    # Messages
    messages = dc_query(
        "SELECT id__c, aiAgentInteractionMessageTypeId__c, "
        "contentText__c, messageSentTimestamp__c "
        "FROM AiAgentInteractionMessage__dll "
        f"WHERE aiAgentSessionId__c = '{sid}' "
        "ORDER BY messageSentTimestamp__c LIMIT 100", org
    )
    trace["messages"] = messages

    # Steps
    trace["steps"] = []
    if ix_ids:
        in_clause = ",".join(f"'{i}'" for i in ix_ids)
        steps = dc_query(
            "SELECT id__c, aiAgentInteractionId__c, "
            "aiAgentInteractionStepTypeId__c, name__c, "
            "inputValueText__c, outputValueText__c, "
            "errorMessageText__c, startTimestamp__c, endTimestamp__c "
            "FROM AiAgentInteractionStep__dll "
            f"WHERE aiAgentInteractionId__c IN ({in_clause}) "
            "ORDER BY startTimestamp__c", org
        )
        trace["steps"] = steps

    # Gateway requests
    gw_requests = dc_query(
        "SELECT gatewayRequestId__c, feature__c, model__c, "
        "promptTemplateDevName__c, promptTokens__c, completionTokens__c, "
        "totalTokens__c, timestamp__c "
        "FROM GenAIGatewayRequest__dll "
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
            "FROM GenAIGatewayResponse__dll "
            f"WHERE generationRequestId__c IN ({in_clause}) "
            "ORDER BY timestamp__c", org
        )

        trace["actionMetadata"] = dc_query(
            "SELECT id__c, parent__c, metadata__c, feature__c, timestamp__c "
            "FROM GenAIGtwyRequestMetadata__dll "
            f"WHERE parent__c IN ({in_clause}) AND metadataType__c = 'ToolCall' "
            "ORDER BY timestamp__c", org
        )

        trace["groundedRecords"] = dc_query(
            "SELECT id__c, recordId__c, type__c, name__c, value__c, timestamp__c "
            "FROM GenAIGtwyObjRecord__dll "
            f"WHERE parent__c IN ({in_clause}) "
            "ORDER BY timestamp__c", org
        )

    # Retriever requests & responses (linked by session time window)
    trace["retrieverRequests"] = []
    trace["retrieverResponses"] = []
    trace["observabilitySpans"] = []

    start_ts = trace.get("startTime")
    if start_ts:
        end_ts = trace.get("endTime") or ""
        # Use a generous window if no end time
        time_filter = f"requestTimestamp__c >= '{start_ts}'"
        if end_ts:
            time_filter += f" AND requestTimestamp__c <= '{end_ts}'"

        retriever_reqs = dc_query(
            "SELECT id__c, queryText__c, retrieverApiName__c, sourceAssetApiName__c, "
            "featureText__c, traceId__c, requestTimestamp__c, requestInfoText__c "
            f"FROM AIRetrieverRequest__dll WHERE {time_filter} "
            "ORDER BY requestTimestamp__c LIMIT 50", org
        )
        trace["retrieverRequests"] = retriever_reqs

        req_ids = [r.get("id__c") for r in retriever_reqs if r.get("id__c")]
        if req_ids:
            in_clause_reqs = ",".join(f"'{i}'" for i in req_ids)
            trace["retrieverResponses"] = dc_query(
                "SELECT id__c, aIRetrieverRequestId__c, resultText__c, citations__c, "
                "scoreNumber__c, sourceRecordId__c, sortIndexNumber__c, responseTimestamp__c "
                f"FROM AIRetrieverResponse__dll "
                f"WHERE aIRetrieverRequestId__c IN ({in_clause_reqs}) "
                "ORDER BY responseTimestamp__c, sortIndexNumber__c LIMIT 200", org
            )

        # Observability spans (use same time window)
        span_filter = f"startDateTime__c >= '{start_ts}'"
        if end_ts:
            span_filter += f" AND startDateTime__c <= '{end_ts}'"

        trace["observabilitySpans"] = dc_query(
            "SELECT operationName__c, serviceName__c, traceId__c, spanId__c, "
            "parentSpanId__c, durationNanos__c, statusCode__c, startDateTime__c, "
            "endDateTime__c, attributes__c "
            f"FROM ObservabilitySpans__dll WHERE {span_filter} "
            "ORDER BY startDateTime__c LIMIT 200", org
        )

    return trace


# ═══════════════════════════════════════════════════════════════════════════════
# Diagnostic Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def run_diagnostics(feeds: list, kg_analysis: dict, sessions: list) -> list:
    """Run automated diagnostic checks and return findings."""
    findings = []

    # Check 1: Knowledge grounding failures
    if kg_analysis["empty_count"] > 0:
        findings.append(
            f"KNOWLEDGE GROUNDING FAILURE: {kg_analysis['empty_count']} feed entries have "
            f"citedReferences: [] — Data Library returned nothing. "
            f"Check: article Summary field populated? Title matches query keywords? "
            f"Article published and accessible to ServicePlanner User?"
        )

    if kg_analysis["grounded_count"] > 0:
        articles = [a.get("title", a.get("name", "unknown")) for a in kg_analysis["articles_cited"]]
        findings.append(
            f"KNOWLEDGE GROUNDED: {kg_analysis['grounded_count']} entries used knowledge. "
            f"Articles cited: {', '.join(articles[:5])}"
        )

    # Check 2: No feeds at all
    if kg_analysis["total_feeds"] == 0:
        findings.append(
            "NO RECACTORACTION FEEDS: No RecActorActionFeed entries found for this record. "
            "Either: (a) the agent hasn't run yet, (b) wrong record ID, or "
            "(c) the agent ran but didn't produce action feed entries."
        )

    # Check 3: Session trace issues
    for s in sessions:
        steps = s.get("steps", [])
        error_steps = [st for st in steps if st.get("errorMessageText__c")
                       and st["errorMessageText__c"] != "NOT_SET"]
        if error_steps:
            for es in error_steps:
                findings.append(
                    f"ACTION ERROR in session {s['sessionId'][:12]}...: "
                    f"Step '{es.get('name__c', 'unnamed')}' — "
                    f"{html.unescape(es.get('errorMessageText__c', ''))[:200]}"
                )

        # Check for CLT render failures
        for st in steps:
            output = st.get("outputValueText__c", "") or ""
            if "ACTION_SUCCESS_RESPONSE" in output and "show_command" not in output:
                findings.append(
                    f"CLT RENDER FAILURE: Step '{st.get('name__c', '')}' returned "
                    f"ACTION_SUCCESS_RESPONSE without show_command — card data was narrated "
                    f"as text instead of rendering. Add show_command instruction directive."
                )

        # Check gateway anomalies
        gw_reqs = s.get("gatewayRequests", [])
        zero_completion = [gw for gw in gw_reqs if gw.get("completionTokens__c") == 0]
        if zero_completion:
            findings.append(
                f"GATEWAY ANOMALY: {len(zero_completion)} gateway call(s) with 0 completion "
                f"tokens — model may have refused or hit a safety filter."
            )

    if not findings:
        findings.append("NO ISSUES DETECTED: All checks passed. Session appears healthy.")

    return findings


# ═══════════════════════════════════════════════════════════════════════════════
# Source Attribution Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def build_source_attribution(feeds: list, sessions: list, gen_op_plans: list) -> dict:
    """Cross-reference all data layers to build a source attribution map.

    For each agent response/action, determines:
    - Source: Knowledge Article (KA), LLM generation (no grounding), or Action output
    - Dev names: topic, action, prompt template active at that point
    - Context variables populated at invocation time
    - Grounded records used
    """
    attribution = {
        "responses": [],       # Per-response attribution
        "dev_names": {         # All dev names seen in session
            "topics": set(),
            "actions": set(),
            "prompt_templates": set(),
            "agent_api": None,
            "agent_version": None,
        },
        "context_vars": [],    # Context variables extracted from action inputs
        "knowledge_sources": [],  # KA records used as grounding
        "llm_only_responses": [],  # Responses with no grounding (LLM improvisation)
        "gateway_features": [],    # Distinct gateway features used
    }

    # ── Extract dev names from GenOpPlan ──────────────────────────
    for plan in gen_op_plans:
        topic = plan.get("TopicName", "")
        if topic:
            attribution["dev_names"]["topics"].add(topic)

    # ── Extract from RecActorActionFeed ──────────────────────────
    for feed in feeds:
        content = feed.get("Content", "")
        if not content:
            continue

        text = html.unescape(content)
        response_entry = {
            "timestamp": feed.get("CreatedDate", ""),
            "source_type": "UNKNOWN",
            "knowledge_articles": [],
            "action_dev_name": None,
            "context_vars_populated": {},
            "content_preview": text[:150],
        }

        # Parse citedReferences
        cited = extract_cited_references(text)
        if cited is not None:
            if len(cited) > 0:
                response_entry["source_type"] = "KNOWLEDGE_ARTICLE"
                for ref in cited:
                    ka_entry = {
                        "id": ref.get("id") or ref.get("recordId") or "",
                        "title": ref.get("title") or ref.get("name") or "",
                        "url": ref.get("url") or "",
                        "snippet": ref.get("snippet") or ref.get("content", "")[:100],
                    }
                    response_entry["knowledge_articles"].append(ka_entry)
                    attribution["knowledge_sources"].append(ka_entry)
            else:
                response_entry["source_type"] = "LLM_ONLY"
                attribution["llm_only_responses"].append(response_entry)

        # Extract action dev name from content
        action_match = re.search(r'"actionDevName"\s*:\s*"([^"]+)"', text)
        if action_match:
            response_entry["action_dev_name"] = action_match.group(1)
            attribution["dev_names"]["actions"].add(action_match.group(1))

        # Extract action name from invocationTarget pattern
        target_match = re.search(r'"invocationTarget"\s*:\s*"([^"]+)"', text)
        if target_match:
            attribution["dev_names"]["actions"].add(target_match.group(1))

        # Extract context variables from content (look for variable assignments)
        var_patterns = [
            (r'"(\w+)"\s*:\s*"(0[A-Za-z0-9]{14,17})"', "record_id"),  # SF IDs
            (r'"(currentRecordId|ContactId|CaseId|messagingSessionId)"\s*:\s*"([^"]+)"', "context_var"),
        ]
        for pattern, var_type in var_patterns:
            for match in re.finditer(pattern, text):
                var_name = match.group(1)
                var_value = match.group(2)
                if var_name not in ("id", "Id", "attributes"):
                    response_entry["context_vars_populated"][var_name] = var_value

        attribution["responses"].append(response_entry)

    # ── Extract from Data Cloud session traces ────────────────────
    for session in sessions:
        # Agent dev name
        if session.get("agentApiName"):
            attribution["dev_names"]["agent_api"] = session.get("agentApiName")
            attribution["dev_names"]["agent_version"] = session.get("agentVersionApi")

        # Topics from interactions
        for ix in session.get("interactions", []):
            topic = ix.get("topicApiName__c")
            if topic:
                attribution["dev_names"]["topics"].add(topic)

        # Prompt templates + features from gateway requests
        for gw in session.get("gatewayRequests", []):
            template = gw.get("promptTemplateDevName__c")
            if template:
                attribution["dev_names"]["prompt_templates"].add(template)
            feature = gw.get("feature__c")
            if feature and feature not in attribution["gateway_features"]:
                attribution["gateway_features"].append(feature)

        # Action dev names from action metadata (ToolCalls)
        for am in session.get("actionMetadata", []):
            metadata_text = html.unescape(am.get("metadata__c", "") or "")
            # Parse tool call name
            tool_match = re.search(r'"name"\s*:\s*"([^"]+)"', metadata_text)
            if tool_match:
                attribution["dev_names"]["actions"].add(tool_match.group(1))

            # Extract input variables (context vars populated at call time)
            try:
                tool_data = json.loads(metadata_text)
                if isinstance(tool_data, dict):
                    inputs = tool_data.get("arguments") or tool_data.get("inputs") or tool_data.get("parameters") or {}
                    if isinstance(inputs, dict):
                        for k, v in inputs.items():
                            if v and str(v).strip():
                                attribution["context_vars"].append({
                                    "action": tool_match.group(1) if tool_match else "unknown",
                                    "variable": k,
                                    "value": str(v)[:100],
                                    "timestamp": am.get("timestamp__c", ""),
                                })
            except (json.JSONDecodeError, TypeError):
                pass

        # Grounded records → knowledge sources
        for gr in session.get("groundedRecords", []):
            ka_entry = {
                "id": gr.get("recordId__c") or "",
                "title": gr.get("name__c") or "",
                "type": gr.get("type__c") or "",
                "value_preview": (gr.get("value__c") or "")[:100],
                "timestamp": gr.get("timestamp__c") or "",
            }
            attribution["knowledge_sources"].append(ka_entry)

    # Convert sets to lists for JSON serialization
    attribution["dev_names"]["topics"] = sorted(attribution["dev_names"]["topics"])
    attribution["dev_names"]["actions"] = sorted(attribution["dev_names"]["actions"])
    attribution["dev_names"]["prompt_templates"] = sorted(attribution["dev_names"]["prompt_templates"])

    return attribution


def format_source_attribution(attribution: dict) -> list:
    """Format source attribution into output lines."""
    lines = []
    lines.append("")
    lines.append("## Source Attribution")
    lines.append("-" * 40)

    # Dev names registry
    dn = attribution["dev_names"]
    lines.append("")
    lines.append("### Dev Names Active in Session")
    lines.append(f"  Agent: {dn['agent_api'] or '(not found)'} (version: {dn['agent_version'] or 'N/A'})")
    lines.append(f"  Topics: {', '.join(dn['topics']) if dn['topics'] else '(none detected)'}")
    lines.append(f"  Actions: {', '.join(dn['actions']) if dn['actions'] else '(none detected)'}")
    lines.append(f"  Prompt Templates: {', '.join(dn['prompt_templates']) if dn['prompt_templates'] else '(none detected)'}")
    if attribution["gateway_features"]:
        lines.append(f"  Gateway Features: {', '.join(attribution['gateway_features'])}")

    # Context variables populated
    if attribution["context_vars"]:
        lines.append("")
        lines.append("### Context Variables Populated at Action Invocation")
        seen = set()
        for cv in attribution["context_vars"]:
            key = f"{cv['action']}.{cv['variable']}"
            if key not in seen:
                seen.add(key)
                lines.append(f"  {cv['action']} → {cv['variable']} = {cv['value']}")

    # Knowledge sources (KA grounding)
    if attribution["knowledge_sources"]:
        lines.append("")
        lines.append("### Knowledge Article Sources (Grounded)")
        seen_ids = set()
        for ks in attribution["knowledge_sources"]:
            record_id = ks.get("id") or ks.get("recordId", "")
            if record_id and record_id not in seen_ids:
                seen_ids.add(record_id)
                title = ks.get("title") or ks.get("name") or "(untitled)"
                rec_type = ks.get("type", "")
                lines.append(f"  [{rec_type}] {title}")
                lines.append(f"    Record ID: {record_id}")
                preview = ks.get("value_preview") or ks.get("snippet") or ""
                if preview:
                    lines.append(f"    Preview: {preview[:120]}")

    # LLM-only responses (no knowledge grounding)
    if attribution["llm_only_responses"]:
        lines.append("")
        lines.append("### LLM-Only Responses (NO Knowledge Grounding)")
        lines.append(f"  Count: {len(attribution['llm_only_responses'])}")
        lines.append("  These responses had citedReferences: [] — the LLM generated")
        lines.append("  the answer from its training data, NOT from your knowledge base.")
        for i, resp in enumerate(attribution["llm_only_responses"][:5], 1):
            lines.append(f"  [{i}] {resp['timestamp']}: {resp['content_preview'][:100]}...")

    # Per-response source map
    ka_responses = [r for r in attribution["responses"] if r["source_type"] == "KNOWLEDGE_ARTICLE"]
    llm_responses = [r for r in attribution["responses"] if r["source_type"] == "LLM_ONLY"]
    unknown_responses = [r for r in attribution["responses"] if r["source_type"] == "UNKNOWN"]

    lines.append("")
    lines.append("### Source Summary")
    lines.append(f"  Knowledge-grounded responses: {len(ka_responses)}")
    lines.append(f"  LLM-only responses (no grounding): {len(llm_responses)}")
    lines.append(f"  Non-knowledge responses (actions/other): {len(unknown_responses)}")

    if ka_responses:
        lines.append("")
        lines.append("  Grounded response detail:")
        for r in ka_responses[:10]:
            articles = ", ".join(a["title"] or a["id"] for a in r["knowledge_articles"][:3])
            action = r.get("action_dev_name") or ""
            lines.append(f"    {r['timestamp']} | Source: {articles} | Action: {action}")

    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# Output Formatting
# ═══════════════════════════════════════════════════════════════════════════════

def unescape(text: str) -> str:
    """Unescape HTML entities."""
    if not text:
        return text or ""
    return html.unescape(text)


def format_output(record_id: str, record_type: str, record_meta: dict,
                  org: str, gen_op_plans: list, feeds: list,
                  kg_analysis: dict, sessions: list, diagnostics: list,
                  attribution: dict = None) -> str:
    """Format all data into a structured text file."""
    lines = []
    lines.append("SRA Agent Debugger — Session Trace Extract")
    lines.append(f"Record: {record_id} (type: {record_type})")
    lines.append(f"Org: {org}")
    lines.append(f"Extracted: {datetime.utcnow().isoformat()}Z")
    lines.append("=" * 80)

    # Record metadata
    lines.append("")
    lines.append("## Record Metadata")
    lines.append("-" * 40)
    if record_type == "Case":
        lines.append(f"  Case Number: {record_meta.get('CaseNumber', 'N/A')}")
        lines.append(f"  Subject: {record_meta.get('Subject', 'N/A')}")
        lines.append(f"  Status: {record_meta.get('Status', 'N/A')}")
        contact = record_meta.get("Contact", {})
        if contact:
            lines.append(f"  Contact: {contact.get('Name', 'N/A')}")
    elif record_type == "MessagingSession":
        lines.append(f"  Session Name: {record_meta.get('Name', 'N/A')}")
        lines.append(f"  Status: {record_meta.get('Status', 'N/A')}")
        lines.append(f"  Channel: {record_meta.get('Channel', 'N/A')}")
        lines.append(f"  Start: {record_meta.get('StartTime', 'N/A')}")
        lines.append(f"  End: {record_meta.get('EndTime', 'N/A')}")
        case = record_meta.get("Case", {})
        if case:
            lines.append(f"  Related Case: {case.get('CaseNumber', 'N/A')} — {case.get('Subject', 'N/A')}")
        else:
            lines.append(f"  Related Case: None")
        lines.append(f"  EndUserContactId: {record_meta.get('EndUserContactId', 'N/A')}")
    elif record_type == "VoiceCall":
        lines.append(f"  Call Type: {record_meta.get('CallType', 'N/A')}")
        lines.append(f"  Duration: {record_meta.get('CallDurationInSeconds', 0)}s")
        lines.append(f"  Disposition: {record_meta.get('CallDisposition', 'N/A')}")
        lines.append(f"  From: {record_meta.get('FromPhoneNumber', 'N/A')}")
        lines.append(f"  To: {record_meta.get('ToPhoneNumber', 'N/A')}")
        lines.append(f"  Start: {record_meta.get('CallStartDateTime', 'N/A')}")
        lines.append(f"  End: {record_meta.get('CallEndDateTime', 'N/A')}")
        case = record_meta.get("Case", {})
        if case:
            lines.append(f"  Related Case: {case.get('CaseNumber', 'N/A')} — {case.get('Subject', 'N/A')}")
        else:
            lines.append(f"  Related Case: None (VoiceCall not linked to a Case)")

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
    else:
        lines.append("")
        lines.append("## Summary Plan (GenOpPlan)")
        lines.append("  (none found)")

    # RecActorActionFeed
    lines.append("")
    lines.append("## RecActorActionFeed")
    lines.append("-" * 40)
    if feeds:
        for i, f in enumerate(feeds, 1):
            lines.append(f"[{i}] Created: {f.get('CreatedDate', '')}")
            content = unescape(f.get("Content", "(empty)"))
            lines.append(content[:3000])
            lines.append("")
    else:
        lines.append("  (none found)")

    # Knowledge Grounding Analysis
    lines.append("")
    lines.append("## Knowledge Grounding Analysis")
    lines.append("-" * 40)
    lines.append(f"  Total feed entries: {kg_analysis['total_feeds']}")
    lines.append(f"  Grounded (citedReferences populated): {kg_analysis['grounded_count']}")
    lines.append(f"  Empty (citedReferences: []): {kg_analysis['empty_count']}")
    lines.append(f"  No citedReferences field: {kg_analysis['missing_count']}")
    if kg_analysis["articles_cited"]:
        lines.append(f"  Articles cited:")
        for art in kg_analysis["articles_cited"][:10]:
            title = art.get("title") or art.get("name") or art.get("id", "unknown")
            lines.append(f"    - {title}")
    if kg_analysis["grounding_failures"]:
        lines.append(f"  Grounding failures (citedReferences: []):")
        for gf in kg_analysis["grounding_failures"][:5]:
            lines.append(f"    - {gf['date']}: {gf['content_preview'][:100]}...")

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

            # ── Quick Glance: Utterance, Topic, Sub-Agent ──────────────
            lines.append("")
            lines.append("### Quick Glance")

            # User utterance (first Input message)
            messages = s.get("messages", [])
            utterance = "(not found)"
            for m in messages:
                if m.get("aiAgentInteractionMessageTypeId__c") == "Input":
                    raw_utterance = unescape(m.get("contentText__c", ""))
                    utterance = raw_utterance[:300] if raw_utterance else "(empty)"
                    break
            lines.append(f"  Utterance: {utterance}")

            # Topic selection + sub-agent / routing
            interactions = s.get("interactions", [])
            topic_sequence = []
            for ix in interactions:
                topic = ix.get("topicApiName__c")
                ix_type = ix.get("aiAgentInteractionTypeId__c", "")
                start = ix.get("startTimestamp__c", "")
                if topic:
                    topic_sequence.append({
                        "topic": topic,
                        "type": ix_type,
                        "start": start,
                    })

            if topic_sequence:
                primary_topic = topic_sequence[0]["topic"]
                lines.append(f"  Topic Selected: {primary_topic}")
                if len(topic_sequence) > 1:
                    lines.append(f"  Topic Switches ({len(topic_sequence)} total):")
                    for ti, ts in enumerate(topic_sequence):
                        marker = "→" if ti > 0 else "●"
                        lines.append(f"    {marker} [{ti}] {ts['topic']} ({ts['type']}) at {ts['start']}")
            else:
                lines.append(f"  Topic Selected: (none — planner did not route to a topic)")

            # Sub-agent detection: look for TOPIC_STEP with different topics
            steps = s.get("steps", [])
            topic_steps = [st for st in steps
                          if st.get("aiAgentInteractionStepTypeId__c") == "TOPIC_STEP"]
            if topic_steps:
                lines.append(f"  Sub-Agent / Topic Steps: {len(topic_steps)}")
                for ts in topic_steps:
                    name = ts.get("name__c", "(unnamed)")
                    lines.append(f"    • {name}")

            # Actions invoked (quick list)
            action_steps = [st for st in steps
                          if st.get("aiAgentInteractionStepTypeId__c") == "ACTION_STEP"]
            if action_steps:
                action_names = [st.get("name__c", "(unnamed)") for st in action_steps]
                lines.append(f"  Actions Invoked: {', '.join(action_names)}")

            lines.append("")

            # Build topic map
            topic_map = {}
            for ix in s.get("interactions", []):
                ix_id = ix.get("id__c")
                topic = ix.get("topicApiName__c", "(unknown)")
                if ix_id:
                    topic_map[ix_id] = topic

            # Dynamic Plan Steps
            steps = s.get("steps", [])
            plan_steps = [st for st in steps if st.get("aiAgentInteractionStepTypeId__c") in
                         ("LLM_STEP", "ACTION_STEP", "TOPIC_STEP")]
            if plan_steps:
                lines.append("")
                lines.append("### Dynamic Plan Steps")
                for seq, ps in enumerate(plan_steps):
                    step_type = ps.get("aiAgentInteractionStepTypeId__c", "")
                    name = ps.get("name__c", "(unnamed)")
                    ix_id = ps.get("aiAgentInteractionId__c", "")
                    topic = topic_map.get(ix_id, "")
                    start = ps.get("startTimestamp__c", "")
                    end = ps.get("endTimestamp__c", "")
                    error = ps.get("errorMessageText__c")

                    lines.append(f"  [{seq}] {step_type} - {name}")
                    lines.append(f"      Topic: {topic}")
                    lines.append(f"      Time: {start} -> {end}")

                    if error and error != "NOT_SET":
                        lines.append(f"      ERROR: {unescape(error)}")

                    input_text = ps.get("inputValueText__c")
                    if input_text:
                        lines.append(f"      Input: {unescape(input_text)[:2000]}")

                    output_text = ps.get("outputValueText__c")
                    if output_text:
                        lines.append(f"      Output: {unescape(output_text)[:2000]}")
                    lines.append("")

            # Transcript
            messages = s.get("messages", [])
            if messages:
                lines.append("")
                lines.append("### Transcript")
                for m in messages:
                    msg_type = m.get("aiAgentInteractionMessageTypeId__c", "")
                    ts = m.get("messageSentTimestamp__c", "")
                    content = unescape(m.get("contentText__c", "(empty)"))
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

            # Retriever Requests & Responses (Knowledge Search)
            ret_reqs = s.get("retrieverRequests", [])
            if ret_reqs:
                lines.append("")
                lines.append("### Knowledge Retrieval (Data Library)")
                lines.append(f"  Total retriever calls: {len(ret_reqs)}")
                ret_resps = s.get("retrieverResponses", [])
                # Group responses by request
                resp_by_req = {}
                for resp in ret_resps:
                    req_id = resp.get("aIRetrieverRequestId__c", "")
                    resp_by_req.setdefault(req_id, []).append(resp)

                for req in ret_reqs:
                    req_id = req.get("id__c", "")
                    info = req.get("requestInfoText__c", "") or ""
                    lines.append(f"")
                    lines.append(f"  [{req.get('requestTimestamp__c', '')[:19]}] "
                                 f"Retriever: {req.get('retrieverApiName__c', 'unknown')}")
                    lines.append(f"    Query: {(req.get('queryText__c', '') or '')[:200]}")
                    lines.append(f"    Info: {info[:150]}")
                    # Show responses for this request
                    resps = resp_by_req.get(req_id, [])
                    if resps:
                        lines.append(f"    Results ({len(resps)}):")
                        for resp in resps[:5]:  # Top 5
                            score = resp.get("scoreNumber__c", 0) or 0
                            record_id = resp.get("sourceRecordId__c", "")
                            result_text = (resp.get("resultText__c", "") or "")[:120]
                            lines.append(f"      Score: {score:.4f} | Record: {record_id}")
                            lines.append(f"        {result_text}")
                    else:
                        lines.append(f"    Results: (none returned)")

            # Observability Spans (Execution Waterfall)
            spans = s.get("observabilitySpans", [])
            if spans:
                lines.append("")
                lines.append("### Execution Waterfall (Observability Spans)")
                lines.append(f"  Total spans: {len(spans)}")
                # Group by traceId for readability
                traces = {}
                for sp in spans:
                    tid = sp.get("traceId__c", "unknown")
                    traces.setdefault(tid, []).append(sp)
                lines.append(f"  Distinct traces: {len(traces)}")
                lines.append("")
                for tid, trace_spans in list(traces.items())[:10]:
                    # Show root spans first
                    root_spans = [sp for sp in trace_spans
                                  if sp.get("parentSpanId__c") in (None, "", "0000000000000000")]
                    child_spans = [sp for sp in trace_spans
                                   if sp.get("parentSpanId__c") not in (None, "", "0000000000000000")]
                    lines.append(f"  Trace: {tid[:24]}...")
                    for sp in root_spans:
                        dur_ms = int(sp.get("durationNanos__c", 0) or 0) / 1_000_000
                        lines.append(f"    {sp.get('operationName__c', '')} "
                                     f"({dur_ms:.0f}ms) [{sp.get('statusCode__c', '')}]")
                    for sp in child_spans:
                        dur_ms = int(sp.get("durationNanos__c", 0) or 0) / 1_000_000
                        lines.append(f"      └─ {sp.get('operationName__c', '')} "
                                     f"({dur_ms:.0f}ms) [{sp.get('statusCode__c', '')}]")
                    lines.append("")

    if not sessions:
        lines.append("")
        lines.append("## No Agentforce sessions found in Data Cloud for this record.")
        lines.append("(Data Cloud may not have materialized yet, or the session pattern is not recognized.)")
        lines.append("NOTE: Core SOQL data (GenOpPlan, RecActorActionFeed) above is still valid.")

    # Source Attribution
    if attribution:
        lines.extend(format_source_attribution(attribution))

    # Diagnostic Summary
    lines.append("")
    lines.append("=" * 80)
    lines.append("## Diagnostic Summary")
    lines.append("-" * 40)
    for d in diagnostics:
        lines.append(f"  * {d}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="SRA Agent Debugger - Session Trace")
    parser.add_argument("--id", required=True, help="18-char Case ID (500...) or MessagingSession ID (0Mw...)")
    parser.add_argument("--org", required=True, help="sf CLI org alias")
    parser.add_argument("--max-sessions", type=int, default=3, help="Max DC sessions to trace")
    parser.add_argument("--output", help="Override output directory")
    # Legacy support
    parser.add_argument("--case", help="(Legacy) Case ID — use --id instead")
    args = parser.parse_args()

    # Support legacy --case flag
    record_id = (args.id or args.case or "").strip()
    if not record_id:
        print("ERROR: --id is required (Case ID or MessagingSession ID)")
        sys.exit(1)

    org = args.org.strip()
    record_type = detect_record_type(record_id)

    if record_type == "Unknown":
        print(f"WARNING: Unrecognized ID prefix for '{record_id}'. Trying as Case ID...")
        record_type = "Case"

    print(f"[1/7] Detected record type: {record_type} ({record_id})")

    # Step 2: Resolve record metadata
    print(f"[2/7] Resolving {record_type} metadata...")
    record_meta = {}
    record_label = record_id[:12]

    if record_type == "Case":
        record_meta = resolve_case(record_id, org)
        if not record_meta:
            print(f"ERROR: Case not found: {record_id}")
            sys.exit(1)
        record_label = record_meta.get("CaseNumber", record_id)
        print(f"  Case: {record_label} — {record_meta.get('Subject', '')}")
    elif record_type == "MessagingSession":
        record_meta = resolve_messaging_session(record_id, org)
        if not record_meta:
            print(f"WARNING: MessagingSession not found via SOQL: {record_id}")
            print(f"  (Proceeding with RecActorActionFeed query which may still work)")
            record_meta = {"Id": record_id}
        else:
            record_label = record_meta.get("Name", record_id)
            case = record_meta.get("Case", {})
            if case:
                print(f"  Session: {record_label} | Related Case: {case.get('CaseNumber', 'none')}")
            else:
                print(f"  Session: {record_label} | No related Case")
    elif record_type == "VoiceCall":
        record_meta = resolve_voice_call(record_id, org)
        if not record_meta:
            print(f"WARNING: VoiceCall not found via SOQL: {record_id}")
            print(f"  (Proceeding with RecActorActionFeed query which may still work)")
            record_meta = {"Id": record_id}
        else:
            call_type = record_meta.get("CallType", "unknown")
            duration = record_meta.get("CallDurationInSeconds", 0)
            record_label = f"Voice_{record_id[:8]}"
            case = record_meta.get("Case", {})
            if case:
                record_label = case.get("CaseNumber", record_label)
                print(f"  VoiceCall: {call_type} | Duration: {duration}s | Case: {case.get('CaseNumber')}")
            else:
                print(f"  VoiceCall: {call_type} | Duration: {duration}s | No related Case")

    # Step 3: Fetch GenOpPlan
    print(f"[3/7] Fetching GenOpPlan...")
    gen_op_plans = []
    # For messaging/voice, try the record ID first, then the related Case ID
    if record_type in ("MessagingSession", "VoiceCall"):
        gen_op_plans = fetch_gen_op_plans(record_id, org)
        if not gen_op_plans and record_meta.get("CaseId"):
            gen_op_plans = fetch_gen_op_plans(record_meta["CaseId"], org)
    else:
        gen_op_plans = fetch_gen_op_plans(record_id, org)
    print(f"  Found {len(gen_op_plans)} plan(s)")

    # Step 4: Fetch RecActorActionFeed
    print(f"[4/7] Fetching RecActorActionFeed (RelatedRecordId = {record_id})...")
    feeds = fetch_rec_actor_feeds(record_id, org)
    # If messaging/voice yielded nothing, try the related Case
    if not feeds and record_type in ("MessagingSession", "VoiceCall") and record_meta.get("CaseId"):
        print(f"  No feeds for {record_type} ID, trying related Case: {record_meta['CaseId']}")
        feeds = fetch_rec_actor_feeds(record_meta["CaseId"], org)
    print(f"  Found {len(feeds)} feed record(s)")

    # Step 5: Analyze knowledge grounding
    print(f"[5/7] Analyzing knowledge grounding...")
    kg_analysis = analyze_knowledge_grounding(feeds)
    if kg_analysis["empty_count"] > 0:
        print(f"  WARNING: {kg_analysis['empty_count']} entries have citedReferences: [] (knowledge retrieval FAILED)")
    if kg_analysis["grounded_count"] > 0:
        print(f"  OK: {kg_analysis['grounded_count']} entries successfully grounded with knowledge")

    # Step 6: Resolve DC session IDs
    print(f"[6/7] Resolving Data Cloud session IDs...")
    session_ids = []
    if record_type == "Case":
        case_number = record_meta.get("CaseNumber", "")
        if case_number:
            session_ids = resolve_session_ids_by_case(case_number, org)
    elif record_type == "MessagingSession":
        session_ids = resolve_session_ids_by_messaging(record_id, org)
        # Also try via related case number
        if not session_ids and record_meta.get("Case", {}).get("CaseNumber"):
            session_ids = resolve_session_ids_by_case(
                record_meta["Case"]["CaseNumber"], org
            )
    elif record_type == "VoiceCall":
        # Voice sessions: try via VoiceCall ID in messages, then VOICE channel, then related Case
        session_ids = resolve_session_ids_by_messaging(record_id, org)
        if not session_ids:
            session_ids = resolve_session_ids_by_voice(record_id, org)
        if not session_ids and record_meta.get("Case", {}).get("CaseNumber"):
            session_ids = resolve_session_ids_by_case(
                record_meta["Case"]["CaseNumber"], org
            )
    # Fallback: extract session UUIDs directly from feed content (most reliable)
    if not session_ids and feeds:
        print(f"  Trying feed-based UUID extraction...")
        session_ids = resolve_session_ids_from_feeds(feeds)
        if session_ids:
            print(f"  Extracted {len(session_ids)} session UUID(s) from feed content")

    print(f"  Found {len(session_ids)} DC session(s)")

    # Step 7: Trace sessions
    print(f"[7/7] Tracing sessions (max {args.max_sessions})...")
    sessions = []
    for i, sid in enumerate(session_ids[:args.max_sessions]):
        print(f"  Tracing session {i+1}/{min(len(session_ids), args.max_sessions)}: {sid[:12]}...")
        sessions.append(trace_session(sid, org))

    # Run diagnostics
    diagnostics = run_diagnostics(feeds, kg_analysis, sessions)

    # Build source attribution
    print(f"  Building source attribution...")
    attribution = build_source_attribution(feeds, sessions, gen_op_plans)
    ka_count = len(attribution["knowledge_sources"])
    llm_count = len(attribution["llm_only_responses"])
    action_count = len(attribution["dev_names"]["actions"])
    print(f"  Sources: {ka_count} KA-grounded, {llm_count} LLM-only, {action_count} actions")

    # Write output
    output_text = format_output(
        record_id, record_type, record_meta, org,
        gen_op_plans, feeds, kg_analysis, sessions, diagnostics, attribution
    )

    # Determine output path
    if args.output:
        out_dir = Path(args.output)
    else:
        out_dir = Path.home() / ".claude" / "data" / "sra-agent-debugger" / org / record_label
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"trace_{timestamp}.txt"
    out_file.write_text(output_text, encoding="utf-8")

    print(f"\nDone! Output: {out_file}")
    print(f"  GenOpPlans: {len(gen_op_plans)}")
    print(f"  RecActorFeeds: {len(feeds)}")
    print(f"  Knowledge grounded: {kg_analysis['grounded_count']}, failed: {kg_analysis['empty_count']}")
    print(f"  Sessions traced: {len(sessions)}")
    print(f"  Diagnostics: {len(diagnostics)} finding(s)")

    # Also print the output for immediate Claude analysis
    print("\n" + "=" * 80)
    print(output_text)


if __name__ == "__main__":
    main()
