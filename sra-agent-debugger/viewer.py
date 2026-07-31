#!/usr/bin/env python3
"""
SRA Tracer — HTML Viewer

Runs the trace and serves a local HTML page with a tabbed interface
for viewing the session trace data outside the org.

Usage:
    python3 viewer.py --id 0MwHo000000vnLUKAY --org mySDO
    python3 viewer.py --file ~/.claude/data/sra-agent-debugger/mySDO/MS-00000029/trace_20260622.txt
    python3 viewer.py --port 8765 --id 500gz000001mVlhAAE --org MetaRLUAT
"""

import argparse
import html
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# Import trace_session functions
sys.path.insert(0, str(Path(__file__).parent))
from trace_session import (
    detect_record_type, resolve_case, resolve_messaging_session,
    resolve_voice_call, fetch_gen_op_plans, fetch_rec_actor_feeds,
    analyze_knowledge_grounding, resolve_session_ids_by_case,
    resolve_session_ids_by_messaging, resolve_session_ids_by_voice,
    resolve_session_ids_from_feeds,
    trace_session, run_diagnostics, build_source_attribution, sf_query
)


def collect_trace_data(record_id: str, org: str, max_sessions: int = 3) -> dict:
    """Run the full trace pipeline and return structured data (not text)."""
    record_type = detect_record_type(record_id)
    if record_type == "Unknown":
        record_type = "Case"

    print(f"[1/7] Detected: {record_type} ({record_id})")

    # Resolve metadata
    print(f"[2/7] Resolving metadata...")
    record_meta = {}
    record_label = record_id[:12]

    if record_type == "Case":
        record_meta = resolve_case(record_id, org)
        record_label = record_meta.get("CaseNumber", record_id)
    elif record_type == "MessagingSession":
        record_meta = resolve_messaging_session(record_id, org)
        if not record_meta:
            record_meta = {"Id": record_id}
        record_label = record_meta.get("Name", record_id)
    elif record_type == "VoiceCall":
        record_meta = resolve_voice_call(record_id, org)
        if not record_meta:
            record_meta = {"Id": record_id}
        record_label = f"Voice_{record_id[:8]}"

    # GenOpPlan
    print(f"[3/7] Fetching GenOpPlan...")
    gen_op_plans = []
    if record_type in ("MessagingSession", "VoiceCall"):
        gen_op_plans = fetch_gen_op_plans(record_id, org)
        if not gen_op_plans and record_meta.get("CaseId"):
            gen_op_plans = fetch_gen_op_plans(record_meta["CaseId"], org)
    else:
        gen_op_plans = fetch_gen_op_plans(record_id, org)
    print(f"  Found {len(gen_op_plans)} plan(s)")

    # RecActorActionFeed
    print(f"[4/7] Fetching RecActorActionFeed...")
    feeds = fetch_rec_actor_feeds(record_id, org)
    if not feeds and record_type in ("MessagingSession", "VoiceCall") and record_meta.get("CaseId"):
        feeds = fetch_rec_actor_feeds(record_meta["CaseId"], org)
    print(f"  Found {len(feeds)} feed record(s)")

    # Knowledge grounding
    print(f"[5/7] Analyzing knowledge grounding...")
    kg_analysis = analyze_knowledge_grounding(feeds)

    # DC sessions
    print(f"[6/7] Resolving Data Cloud sessions...")
    session_ids = []
    dc_error = None
    try:
        if record_type == "Case":
            case_number = record_meta.get("CaseNumber", "")
            if case_number:
                session_ids = resolve_session_ids_by_case(case_number, org)
        elif record_type == "MessagingSession":
            session_ids = resolve_session_ids_by_messaging(record_id, org)
            if not session_ids and record_meta.get("Case", {}).get("CaseNumber"):
                session_ids = resolve_session_ids_by_case(
                    record_meta["Case"]["CaseNumber"], org)
        elif record_type == "VoiceCall":
            session_ids = resolve_session_ids_by_messaging(record_id, org)
            if not session_ids:
                session_ids = resolve_session_ids_by_voice(record_id, org)
            if not session_ids and record_meta.get("Case", {}).get("CaseNumber"):
                session_ids = resolve_session_ids_by_case(
                    record_meta["Case"]["CaseNumber"], org)
    except Exception as e:
        dc_error = str(e)

    # Fallback: extract session UUIDs from feed content
    if not session_ids and feeds:
        from trace_session import resolve_session_ids_from_feeds
        session_ids = resolve_session_ids_from_feeds(feeds)

    print(f"  Found {len(session_ids)} session(s)")

    # Trace sessions
    print(f"[7/7] Tracing sessions...")
    sessions = []
    for i, sid in enumerate(session_ids[:max_sessions]):
        print(f"  Tracing {i+1}/{min(len(session_ids), max_sessions)}: {sid[:12]}...")
        sessions.append(trace_session(sid, org))

    diagnostics = run_diagnostics(feeds, kg_analysis, sessions)
    attribution = build_source_attribution(feeds, sessions, gen_op_plans)

    return {
        "recordId": record_id,
        "recordType": record_type,
        "recordMeta": record_meta,
        "recordLabel": record_label,
        "org": org,
        "genOpPlans": gen_op_plans,
        "feeds": feeds,
        "kgAnalysis": kg_analysis,
        "sessions": sessions,
        "sessionIds": session_ids,
        "diagnostics": diagnostics,
        "attribution": attribution,
        "dcError": dc_error,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def parse_trace_file(filepath: str) -> dict:
    """Parse an existing trace .txt file into structured sections."""
    text = Path(filepath).read_text(encoding="utf-8")
    sections = {}
    current_section = "header"
    current_lines = []

    for line in text.split("\n"):
        if line.startswith("## ") or line.startswith("═"):
            if current_lines:
                sections[current_section] = "\n".join(current_lines)
            current_section = line.strip("═ #").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_section] = "\n".join(current_lines)

    return {"raw_text": text, "sections": sections}


def _parse_feed_content(feed: dict) -> dict:
    """Parse a single RecActorActionFeed entry into structured data."""
    content_raw = feed.get("Content", "")
    try:
        obj = json.loads(content_raw) if content_raw.startswith("{") else {}
    except (json.JSONDecodeError, TypeError):
        obj = {}

    feed_type = obj.get("type", obj.get("messageType", "unknown"))
    inner = obj.get("content", {})

    # Parse nested JSON strings
    if isinstance(inner, str):
        try:
            inner = json.loads(inner)
        except (json.JSONDecodeError, TypeError):
            pass

    result = {"type": feed_type, "raw": obj}

    # Extract messages from response feeds
    if isinstance(inner, dict):
        msgs = inner.get("messages", [])
        if msgs:
            result["messages"] = []
            for m in msgs:
                msg_entry = {
                    "msgType": m.get("type", ""),
                    "text": m.get("message", ""),
                    "citedReferences": m.get("citedReferences"),
                    "confirm": m.get("confirm"),
                }
                result["messages"].append(msg_entry)
        else:
            # User request
            result["userMessage"] = inner.get("message", inner.get("reply", ""))
            result["requestType"] = inner.get("type", inner.get("messageType", ""))

    # FollowupActionRequest — extract action inputs
    if feed_type == "FollowupActionRequest":
        action_inputs = []
        # Content might be a list of action inputs or nested in reply
        if isinstance(inner, dict):
            reply = inner.get("reply", [])
            if isinstance(reply, list):
                action_inputs = reply
        elif isinstance(inner, list):
            action_inputs = inner
        # Also check top-level content if it's a list
        top_content = obj.get("content", {})
        if isinstance(top_content, str):
            try:
                top_content = json.loads(top_content)
            except:
                pass
        if isinstance(top_content, dict):
            reply = top_content.get("reply", [])
            if isinstance(reply, list) and reply:
                action_inputs = reply
        result["actionInputs"] = action_inputs

    return result


def _build_conversation_timeline(feeds: list) -> list:
    """Build a chronological conversation timeline from feeds (newest first in feeds, so reverse)."""
    timeline = []
    for feed in reversed(feeds):  # feeds come newest-first from SOQL
        parsed = _parse_feed_content(feed)
        feed_type = parsed["type"]
        created = feed.get("CreatedDate", "")

        if feed_type == "ResponseToUserRequest":
            for msg in parsed.get("messages", []):
                if msg["text"]:
                    timeline.append({
                        "role": "agent",
                        "type": msg["msgType"],
                        "text": msg["text"],
                        "cited": msg["citedReferences"],
                        "confirm": msg["confirm"],
                        "time": created,
                    })
                elif msg["confirm"]:
                    # Confirmation card
                    for c in msg["confirm"]:
                        action_type = c.get("type", "").split("/")[-1]
                        timeline.append({
                            "role": "agent",
                            "type": "Confirm",
                            "text": f"[Action: {action_type}]",
                            "actionData": c.get("value", {}),
                            "cited": msg["citedReferences"],
                            "time": created,
                        })
        elif feed_type == "ResponseToRecordChange":
            for msg in parsed.get("messages", []):
                if msg["text"]:
                    timeline.append({
                        "role": "agent",
                        "type": "RecordChange",
                        "text": msg["text"],
                        "cited": msg["citedReferences"],
                        "time": created,
                    })
        elif feed_type == "UserRequest":
            timeline.append({
                "role": "user",
                "type": parsed.get("requestType", "Text"),
                "text": parsed.get("userMessage", "(user input)"),
                "time": created,
            })
        elif feed_type == "FollowupActionRequest":
            for ai in parsed.get("actionInputs", []):
                action_type = ai.get("type", "").split("/")[-1]
                inputs = ai.get("value", {})
                timeline.append({
                    "role": "action",
                    "type": action_type,
                    "inputs": inputs,
                    "time": created,
                })
        elif feed_type == "StartDynamicPlan":
            timeline.append({"role": "system", "type": "PlanStarted", "text": "Dynamic plan generation started", "time": created})
        elif feed_type == "ShowSummaryPlan":
            timeline.append({"role": "system", "type": "PlanShown", "text": "Summary plan displayed to user", "time": created})

    return timeline


def generate_ai_summary(data: dict) -> str:
    """Generate a structured AI-written summary from all trace data layers."""
    record_type = data.get("recordType", "")
    record_meta = data.get("recordMeta", {})
    gen_op_plans = data.get("genOpPlans", [])
    feeds = data.get("feeds", [])
    kg_analysis = data.get("kgAnalysis", {})
    sessions = data.get("sessions", [])
    diagnostics = data.get("diagnostics", [])
    attribution = data.get("attribution", {})

    lines = []

    # ── What happened ──
    lines.append("## What Happened")
    if record_type == "MessagingSession":
        status = record_meta.get("Status", "unknown")
        case_obj = record_meta.get("Case", {})
        case_subj = case_obj.get("Subject", "") if case_obj else ""
        contact = record_meta.get("EndUserContactId", "unknown")
        lines.append(f"A messaging session (status: **{status}**) was initiated by contact `{contact}`.")
        if case_subj:
            lines.append(f"Related case topic: *{case_subj}*")
    elif record_type == "Case":
        subj = record_meta.get("Subject", "")
        status = record_meta.get("Status", "")
        lines.append(f"Case **{record_meta.get('CaseNumber','')}** — \"{subj}\" (Status: {status})")

    # ── Conversation Flow (from feeds) ──
    timeline = _build_conversation_timeline(feeds)
    if timeline:
        lines.append("")
        lines.append("## Conversation Flow")

        # Count actions
        actions_taken = [e for e in timeline if e["role"] == "action"]
        user_msgs = [e for e in timeline if e["role"] == "user"]
        agent_msgs = [e for e in timeline if e["role"] == "agent"]

        lines.append(f"**{len(user_msgs)} user messages** → **{len(agent_msgs)} agent responses** → **{len(actions_taken)} actions executed**")
        lines.append("")

        # Render the timeline as a readable narrative
        for entry in timeline:
            if entry["role"] == "user":
                text = entry.get("text", "(input)")
                if text and text != "(user input)":
                    lines.append(f"👤 **User:** {text[:200]}")
                else:
                    lines.append(f"👤 **User:** (sent message)")
            elif entry["role"] == "agent":
                msg_type = entry.get("type", "")
                text = entry.get("text", "")
                cited = entry.get("cited")
                action_data = entry.get("actionData")

                if msg_type == "Confirm" and action_data:
                    action_name = text.replace("[Action: ", "").replace("]", "")
                    # Summarize key inputs
                    key_inputs = []
                    for k, v in list(action_data.items())[:3]:
                        if k in ("userInput", "supportiveTextualData"):
                            key_inputs.append(f"{k}: {str(v)[:80]}...")
                        elif isinstance(v, dict) and "subject" in v:
                            key_inputs.append(f"email subject: {v['subject']}")
                        elif isinstance(v, str) and len(v) < 80:
                            key_inputs.append(f"{k}: {v}")
                    input_str = " | ".join(key_inputs) if key_inputs else ""
                    lines.append(f"🤖 **Agent confirms action:** `{action_name}`")
                    if input_str:
                        lines.append(f"   {input_str}")
                elif msg_type == "RecordChange":
                    grounding = "📚" if cited else "⚠️ LLM" if cited == [] else ""
                    lines.append(f"🤖 **Agent (record change):** {text[:180]} {grounding}")
                else:
                    grounding = "📚" if cited else "⚠️ LLM" if cited == [] else ""
                    lines.append(f"🤖 **Agent:** {text[:180]} {grounding}")
            elif entry["role"] == "action":
                action_type = entry.get("type", "unknown")
                inputs = entry.get("inputs", {})
                # Summarize action
                input_keys = list(inputs.keys())[:4]
                lines.append(f"⚡ **Action executed:** `{action_type}`")
                if "userInput" in inputs:
                    lines.append(f"   Intent: {str(inputs['userInput'])[:150]}")
                elif "messagingSessionId" in inputs:
                    lines.append(f"   SessionId: {inputs['messagingSessionId']}")
                if "latestEmailDraft" in inputs:
                    draft = inputs["latestEmailDraft"]
                    if isinstance(draft, dict):
                        lines.append(f"   Email: \"{draft.get('subject', '')}\" → {draft.get('toField', '')}")
            elif entry["role"] == "system":
                lines.append(f"📋 *{entry.get('text', '')}*")

    # ── What the agent planned ──
    if gen_op_plans:
        lines.append("")
        lines.append("## Agent Plan")
        plan = gen_op_plans[0]
        intent = plan.get("Intent__c", plan.get("Intent", ""))
        topic_name = plan.get("TopicName", plan.get("Topic__c", ""))
        topic_desc = plan.get("TopicDescription", "")
        plan_header = plan.get("PlanHeader__c", plan.get("PlanHeader", ""))
        plan_summary = plan.get("PlanSummary__c", plan.get("PlanSummary", ""))
        if intent:
            lines.append(f"**Instruction (dev name):** `{intent}`")
        if topic_name:
            lines.append(f"**Topic:** {topic_name}")
        if topic_desc:
            lines.append(f"**Topic description:** *{topic_desc[:200]}*")
        if plan_header:
            lines.append(f"**Plan:** {plan_header}")
        if plan_summary:
            # Handle both newline-separated and JSON array formats
            try:
                steps = json.loads(plan_summary) if plan_summary.startswith("[") else []
            except:
                steps = []
            if not steps:
                steps = [s.strip() for s in plan_summary.split("\n") if s.strip()]
            if steps:
                lines.append("**Steps:**")
                for si, s in enumerate(steps[:8], 1):
                    lines.append(f"  {si}. {s}")

    # ── Actions summary — extract dev names from feed content ──
    lines.append("")
    lines.append("## Actions & Execution")

    # Extract action dev names from copilotActionOutput/Input types in feeds
    action_dev_names = set()
    action_results = []
    for feed in feeds:
        content_raw = feed.get("Content", "")
        # Find all copilotAction references
        for match in re.findall(r'copilotAction(?:Output|Input)/([^"\\]+)', content_raw):
            # Strip the org-specific ID suffix (e.g. _179Ho0000004Owt)
            clean_name = re.sub(r'_[A-Za-z0-9]{15,18}$', '', match)
            action_dev_names.add(clean_name)
        # Extract action result values
        try:
            obj = json.loads(content_raw) if content_raw.startswith("{") else {}
            inner_str = obj.get("content", "")
            if isinstance(inner_str, str) and inner_str.startswith("{"):
                inner = json.loads(inner_str)
                for msg in inner.get("messages", []):
                    for result in msg.get("result", []):
                        rtype = result.get("type", "")
                        rval = result.get("value", {})
                        action_name = re.sub(r'copilotActionOutput/', '', rtype)
                        action_name = re.sub(r'_[A-Za-z0-9]{15,18}$', '', action_name)
                        if rval:
                            action_results.append({"action": action_name, "output": rval})
        except:
            pass

    dev_names = attribution.get("dev_names", {})
    topics = dev_names.get("topics", [])

    if topics:
        lines.append(f"**Topics activated:** {', '.join(str(t) for t in topics)}")

    if action_dev_names:
        lines.append(f"**Actions (dev names):** {', '.join(f'`{a}`' for a in sorted(action_dev_names))}")
    elif dev_names.get("actions"):
        lines.append(f"**Actions invoked:** {', '.join(str(a) for a in dev_names['actions'])}")
    else:
        lines.append("No actions were invoked in this session.")

    # Show action results summary
    if action_results:
        lines.append("")
        lines.append("**Action outputs:**")
        for ar in action_results:
            action = ar["action"]
            output = ar["output"]
            # Summarize the output
            if isinstance(output, dict):
                # Look for key data fields
                summary_parts = []
                for k, v in output.items():
                    if isinstance(v, str) and len(v) < 100:
                        summary_parts.append(f"{k}: {v}")
                    elif isinstance(v, dict):
                        # Try to parse JSON strings inside
                        for ik, iv in v.items():
                            if isinstance(iv, str) and iv.startswith("{"):
                                try:
                                    parsed = json.loads(iv)
                                    summary_parts.append(f"{ik}: {json.dumps(parsed)[:120]}")
                                except:
                                    summary_parts.append(f"{ik}: {iv[:80]}")
                            elif isinstance(iv, str):
                                summary_parts.append(f"{ik}: {iv[:80]}")
                if summary_parts:
                    lines.append(f"  `{action}` → {' | '.join(summary_parts[:3])}")

    feed_count = len(feeds)
    lines.append(f"**Feed entries:** {feed_count}")

    # Session-level detail from DC
    if sessions:
        for si, sess in enumerate(sessions):
            steps = sess.get("steps", [])
            if steps:
                step_types = {}
                for st in steps:
                    t = st.get("aiAgentInteractionStepTypeId__c", "OTHER")
                    step_types[t] = step_types.get(t, 0) + 1
                lines.append(f"**Session {si+1} steps:** " + ", ".join(f"{v}x {k}" for k, v in sorted(step_types.items())))

                errors = [st for st in steps if st.get("errorMessageText__c") and st["errorMessageText__c"] != "NOT_SET"]
                if errors:
                    lines.append(f"  ⚠️ {len(errors)} step(s) threw errors")

    # ── Knowledge grounding ──
    lines.append("")
    lines.append("## Knowledge Grounding")
    grounded = kg_analysis.get("grounded_count", 0)
    failed = kg_analysis.get("empty_count", 0)
    total = kg_analysis.get("total_feeds", 0)

    if total == 0:
        lines.append("No knowledge grounding data available (no feed entries).")
    elif failed == 0 and grounded > 0:
        lines.append(f"✅ **All {grounded} responses were knowledge-grounded.** The agent sourced answers from your Knowledge Articles.")
        articles = kg_analysis.get("articles_cited", [])
        if articles:
            lines.append("Articles used: " + ", ".join(a.get("title", a.get("name", "?"))[:50] for a in articles[:5]))
    elif failed > 0 and grounded == 0:
        lines.append(f"🔴 **All {failed} responses had EMPTY citedReferences.** The agent couldn't find relevant Knowledge Articles and improvised from LLM training data.")
        lines.append("**Fix:** Check that your KA articles have populated Summary fields with customer-voice keywords matching the query.")
    elif failed > 0:
        lines.append(f"🟡 **Mixed results:** {grounded} grounded, {failed} failed. Some responses came from Knowledge Articles, others were LLM-improvised.")
        lines.append("Review the LLM-only responses in Source Attribution to see which answers lacked backing.")
    else:
        lines.append(f"Feeds present ({total}) but no explicit grounding signals detected.")

    # Show which specific responses lacked grounding
    if failed > 0 and timeline:
        lines.append("")
        lines.append("**Ungrounded responses:**")
        count = 0
        for entry in timeline:
            if entry["role"] == "agent" and entry.get("cited") == []:
                text = entry.get("text", "")[:120]
                if text:
                    lines.append(f"  ⚠️ \"{text}...\"")
                    count += 1
                    if count >= 5:
                        remaining = failed - count
                        if remaining > 0:
                            lines.append(f"  ... and {remaining} more")
                        break

    # ── Gateway / Model usage ──
    if sessions:
        total_prompt = 0
        total_completion = 0
        models_used = set()
        for sess in sessions:
            for gw in sess.get("gatewayRequests", []):
                total_prompt += int(gw.get("promptTokens__c", 0) or 0)
                total_completion += int(gw.get("completionTokens__c", 0) or 0)
                model = gw.get("model__c", "")
                if model:
                    models_used.add(model)
        if total_prompt or total_completion:
            lines.append("")
            lines.append("## LLM Usage")
            lines.append(f"**Models:** {', '.join(models_used) if models_used else 'unknown'}")
            lines.append(f"**Tokens:** {total_prompt:,} prompt + {total_completion:,} completion = {total_prompt+total_completion:,} total")
            zero_completion = sum(1 for sess in sessions for gw in sess.get("gatewayRequests", []) if gw.get("completionTokens__c") == 0)
            if zero_completion:
                lines.append(f"⚠️ {zero_completion} call(s) returned 0 completion tokens (possible refusal/safety filter)")

    # ── Issues & Recommendations ──
    lines.append("")
    lines.append("## Issues & Recommendations")
    has_issues = False

    for d in diagnostics:
        if "NO ISSUES" in d:
            continue
        has_issues = True
        if "KNOWLEDGE GROUNDING FAILURE" in d:
            lines.append("🔴 **Knowledge Retrieval Failed**")
            lines.append("   → Articles not found by Data Library. Check: Summary field populated? Title has customer-voice keywords? Article published?")
        elif "CLT RENDER FAILURE" in d:
            lines.append("🟡 **Card Not Rendered (CLT)**")
            lines.append("   → Action returned data but agent narrated as text. Add `show_command` directive to instructions.")
        elif "ACTION ERROR" in d:
            lines.append(f"🔴 **Action Error:** {d.split('—')[-1].strip()[:150]}")
            lines.append("   → Check Apex logs. Common causes: `with sharing`, missing FLS, null context variable.")
        elif "GATEWAY ANOMALY" in d:
            lines.append("🟡 **Gateway Anomaly** — 0 completion tokens on some calls.")
            lines.append("   → Model may have refused. Check prompt content or safety settings.")
        elif "GROUNDED" in d:
            pass  # positive signal, skip
        else:
            lines.append(f"• {d}")

    if not has_issues:
        lines.append("✅ **No issues detected.** Session appears healthy.")

    # ── Data availability note ──
    dc_error = data.get("dcError")
    if dc_error or not sessions:
        lines.append("")
        lines.append("## Data Availability")
        lines.append("⚠️ Data Cloud session trace was not available. Analysis above is based on Core SOQL data (GenOpPlan, RecActorActionFeed).")
        lines.append("Dynamic Plan steps, Transcript, Gateway Calls, and Action metadata require Data Cloud STDM tables to be mapped.")

    return "\n".join(lines)


def generate_html(data: dict) -> str:
    """Generate a complete standalone HTML page from trace data."""
    record_label = data.get("recordLabel", data.get("recordId", "Unknown"))
    record_type = data.get("recordType", "")
    org = data.get("org", "")
    timestamp = data.get("timestamp", "")
    record_meta = data.get("recordMeta", {})
    gen_op_plans = data.get("genOpPlans", [])
    feeds = data.get("feeds", [])
    kg_analysis = data.get("kgAnalysis", {})
    sessions = data.get("sessions", [])
    diagnostics = data.get("diagnostics", [])
    attribution = data.get("attribution", {})
    dc_error = data.get("dcError")

    # Build case/session info
    case_info = ""
    if record_type == "Case":
        case_info = f"Case {record_meta.get('CaseNumber', '')} — {html.escape(record_meta.get('Subject', ''))}"
    elif record_type == "MessagingSession":
        case_obj = record_meta.get("Case", {})
        session_name = record_meta.get("Name", "")
        case_num = case_obj.get("CaseNumber", "") if case_obj else ""
        case_subj = case_obj.get("Subject", "") if case_obj else ""
        case_info = f"Session: {session_name}"
        if case_num:
            case_info += f" | Case: {case_num} — {html.escape(case_subj)}"

    # Dynamic Plan tab content
    dynamic_plan_html = ""
    if sessions:
        for si, sess in enumerate(sessions):
            steps = sess.get("steps", [])
            if steps:
                dynamic_plan_html += f'<h3>Session {si+1}: {html.escape(sess.get("sessionId","")[:16])}...</h3>'
                dynamic_plan_html += '<table class="data-table"><thead><tr>'
                dynamic_plan_html += '<th>Type</th><th>Name</th><th>Topic</th><th>Start</th><th>Duration</th><th>Input</th><th>Output</th>'
                dynamic_plan_html += '</tr></thead><tbody>'
                for step in steps:
                    step_type = step.get("aiAgentInteractionStepTypeId__c", "")
                    name = html.escape(step.get("name__c", "") or "")
                    # Find topic from interaction
                    ix_id = step.get("aiAgentInteractionId__c", "")
                    topic = ""
                    for ix in sess.get("interactions", []):
                        if ix.get("id__c") == ix_id:
                            topic = ix.get("topicApiName__c", "") or ""
                            break
                    start_ts = step.get("startTimestamp__c", "")
                    end_ts = step.get("endTimestamp__c", "")
                    duration = ""
                    if start_ts and end_ts:
                        try:
                            s = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                            e = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
                            duration = f"{(e-s).total_seconds():.1f}s"
                        except:
                            pass
                    input_val = html.escape((step.get("inputValueText__c", "") or "")[:200])
                    output_val = html.escape((step.get("outputValueText__c", "") or "")[:200])
                    error = step.get("errorMessageText__c", "")
                    row_class = ' class="error-row"' if error and error != "NOT_SET" else ""
                    type_badge = f'<span class="badge badge-{step_type.lower().replace("_","-")}">{html.escape(step_type)}</span>'
                    dynamic_plan_html += f'<tr{row_class}><td>{type_badge}</td><td>{name}</td><td>{html.escape(topic)}</td><td class="ts">{start_ts[-12:-1] if start_ts else ""}</td><td>{duration}</td>'
                    dynamic_plan_html += f'<td class="truncate" title="{input_val}">{input_val[:80]}</td>'
                    dynamic_plan_html += f'<td class="truncate" title="{output_val}">{output_val[:80]}</td></tr>'
                dynamic_plan_html += '</tbody></table>'
    if not dynamic_plan_html:
        dynamic_plan_html = '<p class="empty-state">No Data Cloud session steps available.</p>'

    # Transcript tab
    transcript_html = ""
    if sessions:
        for si, sess in enumerate(sessions):
            messages = sess.get("messages", [])
            if messages:
                transcript_html += f'<h3>Session {si+1}</h3><div class="transcript">'
                for msg in messages:
                    msg_type = msg.get("aiAgentInteractionMessageTypeId__c", "")
                    content = html.escape(msg.get("contentText__c", "") or "")
                    ts = msg.get("messageSentTimestamp__c", "")
                    ts_short = ts[-12:-1] if ts else ""
                    bubble_class = "user" if "INPUT" in msg_type.upper() or "USER" in msg_type.upper() else "agent"
                    transcript_html += f'<div class="message {bubble_class}">'
                    transcript_html += f'<div class="msg-header"><span class="msg-type">{html.escape(msg_type)}</span><span class="msg-ts">{ts_short}</span></div>'
                    transcript_html += f'<div class="msg-content">{content}</div></div>'
                transcript_html += '</div>'
    if not transcript_html:
        transcript_html = '<p class="empty-state">No Data Cloud transcript available.</p>'

    # Knowledge Grounding tab
    kg_html = '<div class="kg-summary">'
    kg_html += f'<div class="stat-grid">'
    kg_html += f'<div class="stat"><span class="stat-num">{kg_analysis.get("grounded_count", 0)}</span><span class="stat-label">KA-Grounded</span></div>'
    kg_html += f'<div class="stat warning"><span class="stat-num">{kg_analysis.get("empty_count", 0)}</span><span class="stat-label">Failed (empty)</span></div>'
    kg_html += f'<div class="stat"><span class="stat-num">{kg_analysis.get("total_feeds", 0)}</span><span class="stat-label">Total Feeds</span></div>'
    kg_html += '</div>'

    articles = kg_analysis.get("articles_cited", [])
    if articles:
        kg_html += '<h3>Articles Cited</h3><ul class="article-list">'
        for art in articles:
            title = html.escape(art.get("title", art.get("name", "Unknown")))
            kg_html += f'<li class="article-item">📄 {title}</li>'
        kg_html += '</ul>'

    kg_html += '</div>'

    # Source Attribution tab
    attr_html = '<div class="attribution">'
    dev_names = attribution.get("dev_names", {})
    if dev_names:
        # Agent
        agent_name = dev_names.get("agent", "")
        if agent_name:
            attr_html += f'<div class="attr-section"><h4>Agent</h4><code>{html.escape(str(agent_name))}</code></div>'
        # Topics
        topics = dev_names.get("topics", [])
        if topics:
            attr_html += '<div class="attr-section"><h4>Topics</h4><ul>'
            for t in topics:
                attr_html += f'<li><code>{html.escape(str(t))}</code></li>'
            attr_html += '</ul></div>'
        # Actions
        actions = dev_names.get("actions", [])
        if actions:
            attr_html += '<div class="attr-section"><h4>Actions</h4><ul>'
            for a in actions:
                attr_html += f'<li><code>{html.escape(str(a))}</code></li>'
            attr_html += '</ul></div>'
        # Prompt Templates
        templates = dev_names.get("prompt_templates", [])
        if templates:
            attr_html += '<div class="attr-section"><h4>Prompt Templates</h4><ul>'
            for t in templates:
                attr_html += f'<li><code>{html.escape(str(t))}</code></li>'
            attr_html += '</ul></div>'

    # KA sources
    ka_sources = attribution.get("knowledge_sources", [])
    if ka_sources:
        attr_html += '<div class="attr-section"><h4>Knowledge Article Sources</h4><table class="data-table"><thead><tr><th>Record ID</th><th>Title</th></tr></thead><tbody>'
        for src in ka_sources:
            attr_html += f'<tr><td><code>{html.escape(str(src.get("recordId", "")))}</code></td><td>{html.escape(str(src.get("title", src.get("name", ""))))}</td></tr>'
        attr_html += '</tbody></table></div>'

    # LLM-only
    llm_only = attribution.get("llm_only_responses", [])
    if llm_only:
        attr_html += f'<div class="attr-section warning-section"><h4>⚠️ LLM-Only Responses ({len(llm_only)})</h4>'
        attr_html += '<p>These responses had no knowledge grounding — the LLM improvised from training data.</p><ul>'
        for lr in llm_only[:10]:
            snippet = html.escape(str(lr.get("content", lr.get("snippet", "")))[:150])
            attr_html += f'<li class="llm-only-item">{snippet}...</li>'
        attr_html += '</ul></div>'

    attr_html += '</div>'

    # RecActorActionFeed tab
    feed_html = ''
    if feeds:
        feed_html += '<div class="feeds">'
        for fi, feed in enumerate(feeds):
            content_raw = feed.get("Content", "") or ""
            try:
                content_obj = json.loads(content_raw) if content_raw.startswith("{") else {}
            except:
                content_obj = {}
            feed_html += f'<div class="feed-entry">'
            feed_html += f'<div class="feed-header">Feed Entry {fi+1} — {html.escape(feed.get("CreatedDate", ""))}</div>'
            feed_html += f'<pre class="json-block">{html.escape(json.dumps(content_obj, indent=2)[:3000] if content_obj else content_raw[:3000])}</pre>'
            feed_html += '</div>'
        feed_html += '</div>'
    else:
        feed_html = '<p class="empty-state">No RecActorActionFeed entries found.</p>'

    # GenOpPlan / Summary Plan tab
    plan_html = ''
    if gen_op_plans:
        for pi, plan in enumerate(gen_op_plans):
            plan_html += f'<div class="plan-entry">'
            plan_html += f'<h3>Plan {pi+1}</h3>'
            plan_html += f'<table class="meta-table">'
            for key in ["Intent__c", "Topic__c", "PlanHeader__c", "PlanSummary__c", "CreatedDate"]:
                val = plan.get(key, "")
                if val:
                    plan_html += f'<tr><td class="meta-key">{html.escape(key.replace("__c",""))}</td><td>{html.escape(str(val)[:500])}</td></tr>'
            plan_html += '</table>'
            # PlanSummary often has steps
            summary = plan.get("PlanSummary__c", "")
            if summary and len(summary) > 100:
                plan_html += f'<h4>Plan Steps</h4><pre class="plan-steps">{html.escape(summary)}</pre>'
            plan_html += '</div>'
    else:
        plan_html = '<p class="empty-state">No GenOpPlan entries found.</p>'

    # Gateway Calls tab
    gw_html = ''
    if sessions:
        for si, sess in enumerate(sessions):
            gw_reqs = sess.get("gatewayRequests", [])
            if gw_reqs:
                gw_html += f'<h3>Session {si+1}</h3>'
                gw_html += '<table class="data-table"><thead><tr><th>Feature</th><th>Model</th><th>Template</th><th>Prompt Tokens</th><th>Completion</th><th>Total</th><th>Time</th></tr></thead><tbody>'
                for gw in gw_reqs:
                    gw_html += f'<tr><td>{html.escape(str(gw.get("feature__c","")))}</td>'
                    gw_html += f'<td><code>{html.escape(str(gw.get("model__c","")))}</code></td>'
                    gw_html += f'<td>{html.escape(str(gw.get("promptTemplateDevName__c","")))}</td>'
                    gw_html += f'<td>{gw.get("promptTokens__c","")}</td>'
                    gw_html += f'<td>{gw.get("completionTokens__c","")}</td>'
                    gw_html += f'<td>{gw.get("totalTokens__c","")}</td>'
                    ts = str(gw.get("timestamp__c", ""))
                    gw_html += f'<td class="ts">{ts[-12:-1] if len(ts)>12 else ts}</td></tr>'
                gw_html += '</tbody></table>'
    if not gw_html:
        gw_html = '<p class="empty-state">No gateway call data available.</p>'

    # Actions tab
    actions_html = ''
    if sessions:
        for si, sess in enumerate(sessions):
            action_meta = sess.get("actionMetadata", [])
            if action_meta:
                actions_html += f'<h3>Session {si+1}</h3>'
                for am in action_meta:
                    metadata = am.get("metadata__c", "")
                    try:
                        meta_obj = json.loads(metadata) if metadata else {}
                    except:
                        meta_obj = {}
                    actions_html += f'<div class="action-entry">'
                    actions_html += f'<div class="action-header">{html.escape(str(am.get("feature__c","")))}</div>'
                    actions_html += f'<pre class="json-block">{html.escape(json.dumps(meta_obj, indent=2)[:2000] if meta_obj else metadata[:2000])}</pre>'
                    actions_html += '</div>'
    if not actions_html:
        actions_html = '<p class="empty-state">No action metadata available.</p>'

    # Context & Grounding tab — shows what was passed to planner on each turn
    context_html = ''
    if sessions:
        for si, sess in enumerate(sessions):
            steps = sess.get("steps", [])
            llm_steps = [s for s in steps if s.get("aiAgentInteractionStepTypeId__c") == "LLM_STEP"]
            if llm_steps:
                context_html += f'<h3>Session {si+1}: Planner Context per Turn</h3>'

                for step_idx, step in enumerate(llm_steps):
                    input_val = step.get("inputValueText__c", "") or ""
                    if not input_val:
                        continue
                    try:
                        input_val_decoded = html.unescape(input_val) if '&' in input_val else input_val
                        step_data = json.loads(input_val_decoded)
                    except (json.JSONDecodeError, TypeError):
                        continue

                    prompt_name = step_data.get("promptName", "")
                    messages = step_data.get("messages", [])
                    tools = step_data.get("tools", [])
                    prompt_vars = step_data.get("promptVariables", {})

                    # Extract context sections from messages
                    data_section = ""
                    knowledge_section = ""
                    conversation_history = ""
                    context_entity = ""
                    seed_steps = ""
                    user_utterance = ""

                    for msg in messages:
                        if msg.get("role") != "user":
                            continue
                        content = msg.get("content", "")
                        # Extract DATA_TAG section
                        dt_start = content.find("<{{DATA_TAG}}>")
                        dt_end = content.find("</{{DATA_TAG}}>")
                        if dt_start >= 0 and dt_end >= 0:
                            data_section = content[dt_start+14:dt_end].strip()
                            # Parse sub-sections
                            ch_start = data_section.find("#### Conversation History:")
                            ss_start = data_section.find("#### Seed Steps:")
                            ce_start = data_section.find("#### Context Entity:")
                            if ch_start >= 0:
                                end_ch = ss_start if ss_start > ch_start else (ce_start if ce_start > ch_start else len(data_section))
                                conversation_history = data_section[ch_start+26:end_ch].strip()
                            if ss_start >= 0:
                                end_ss = ce_start if ce_start > ss_start else len(data_section)
                                seed_steps = data_section[ss_start+16:end_ss].strip()
                            if ce_start >= 0:
                                context_entity = data_section[ce_start+20:].strip()

                        # Extract KNOWLEDGE section
                        kt_start = content.find("<{{KNOWLEDGE_DATA_TAG}}>")
                        kt_end = content.find("</{{KNOWLEDGE_DATA_TAG}}>")
                        if kt_start >= 0 and kt_end >= 0:
                            knowledge_section = content[kt_start+24:kt_end].strip()

                        # User utterance is text before the DATA_TAG or the whole message
                        if dt_start > 0:
                            user_utterance = content[:dt_start].strip()
                        elif dt_start < 0:
                            user_utterance = content.strip()

                    # Extract tool call results from messages
                    tool_results = []
                    for msg in messages:
                        if msg.get("role") == "tool":
                            tool_results.append({
                                "id": msg.get("tool_call_id", ""),
                                "content": msg.get("content", "")
                            })

                    # Tool calls made by assistant
                    tool_calls = []
                    for msg in messages:
                        if msg.get("role") == "assistant" and msg.get("tool_calls"):
                            for tc in msg["tool_calls"]:
                                func = tc.get("function", {})
                                tool_calls.append({
                                    "name": func.get("name", ""),
                                    "arguments": func.get("arguments", "")
                                })

                    ts = step.get("startTimestamp__c", "")
                    ts_short = ts[-12:-1] if ts else ""

                    # Render this turn
                    context_html += f'<div class="context-turn">'
                    context_html += f'<div class="context-turn-header" onclick="this.parentElement.classList.toggle(\'expanded\')">'
                    context_html += f'<span class="expand-icon">▶</span> '
                    context_html += f'<strong>Turn {step_idx+1}</strong> — '
                    context_html += f'<code>{html.escape(prompt_name)}</code> '
                    context_html += f'<span class="ts">{ts_short}</span> '
                    context_html += f'<span class="badge">{len(tools)} tools</span> '
                    context_html += f'<span class="badge">{len(messages)} msgs</span>'
                    if knowledge_section:
                        context_html += f' <span class="badge badge-ok">📚 Knowledge</span>'
                    context_html += f'</div>'
                    context_html += f'<div class="context-turn-body">'

                    # User utterance
                    if user_utterance:
                        context_html += f'<div class="context-section"><h5>💬 User Utterance / Instruction</h5>'
                        context_html += f'<pre class="context-block">{html.escape(user_utterance[:2000])}</pre></div>'

                    # Context Entity
                    if context_entity:
                        context_html += f'<div class="context-section"><h5>🎯 Context Entity</h5>'
                        context_html += f'<code>{html.escape(context_entity)}</code></div>'

                    # Available Tools
                    if tools:
                        context_html += f'<div class="context-section"><h5>🔧 Available Tools ({len(tools)})</h5>'
                        context_html += '<table class="data-table compact"><thead><tr><th>Action</th><th>Description</th></tr></thead><tbody>'
                        for t in tools:
                            func = t.get("function", {})
                            context_html += f'<tr><td><code>{html.escape(func.get("name",""))}</code></td>'
                            context_html += f'<td>{html.escape((func.get("description","") or "")[:120])}</td></tr>'
                        context_html += '</tbody></table></div>'

                    # Knowledge Grounding
                    if knowledge_section:
                        context_html += f'<div class="context-section"><h5>📚 Knowledge Grounding (passed to planner)</h5>'
                        context_html += f'<pre class="context-block knowledge-block">{html.escape(knowledge_section[:5000])}</pre></div>'
                    else:
                        context_html += f'<div class="context-section"><h5>📚 Knowledge Grounding</h5>'
                        context_html += f'<span class="empty-note">None — no knowledge content injected this turn</span></div>'

                    # Conversation History (accumulated)
                    if conversation_history and conversation_history != "[]":
                        context_html += f'<div class="context-section"><h5>📜 Conversation History (accumulated context)</h5>'
                        # Try to pretty-print if JSON
                        try:
                            ch_data = json.loads(conversation_history)
                            context_html += f'<pre class="context-block">{html.escape(json.dumps(ch_data, indent=2)[:8000])}</pre>'
                        except:
                            context_html += f'<pre class="context-block">{html.escape(conversation_history[:8000])}</pre>'
                        context_html += '</div>'

                    # Seed Steps
                    if seed_steps:
                        context_html += f'<div class="context-section"><h5>🌱 Seed Steps</h5>'
                        context_html += f'<pre class="context-block">{html.escape(seed_steps[:3000])}</pre></div>'

                    # Tool Calls & Results
                    if tool_calls:
                        context_html += f'<div class="context-section"><h5>⚙️ Tool Calls in Context</h5>'
                        for tc in tool_calls:
                            context_html += f'<div class="tool-call"><code>{html.escape(tc["name"])}</code>'
                            try:
                                args_obj = json.loads(tc["arguments"]) if tc["arguments"] else {}
                                context_html += f'<pre class="context-block">{html.escape(json.dumps(args_obj, indent=2)[:1000])}</pre>'
                            except:
                                context_html += f'<pre class="context-block">{html.escape(tc["arguments"][:500])}</pre>'
                            context_html += '</div>'
                        context_html += '</div>'

                    if tool_results:
                        context_html += f'<div class="context-section"><h5>📤 Tool Results Returned</h5>'
                        for tr in tool_results:
                            context_html += f'<div class="tool-result"><code>{html.escape(tr["id"])}</code>'
                            context_html += f'<pre class="context-block">{html.escape(tr["content"][:1000])}</pre></div>'
                        context_html += '</div>'

                    # Prompt Variables
                    if prompt_vars:
                        context_html += f'<div class="context-section"><h5>📋 Prompt Variables</h5>'
                        context_html += f'<pre class="context-block">{html.escape(json.dumps(prompt_vars, indent=2)[:2000])}</pre></div>'

                    context_html += '</div></div>'  # close body and turn

            # Retriever Requests
            ret_reqs = sess.get("retrieverRequests", [])
            if ret_reqs:
                context_html += f'<h3>Session {si+1}: Knowledge Retrieval Calls</h3>'
                ret_resps = sess.get("retrieverResponses", [])
                resp_by_req = {}
                for resp in ret_resps:
                    req_id = resp.get("aIRetrieverRequestId__c", "")
                    resp_by_req.setdefault(req_id, []).append(resp)

                context_html += '<table class="data-table"><thead><tr><th>Time</th><th>Query</th><th>Retriever</th><th>Results</th><th>Top Score</th></tr></thead><tbody>'
                for req in ret_reqs:
                    req_id = req.get("id__c", "")
                    resps = resp_by_req.get(req_id, [])
                    top_score = max((r.get("scoreNumber__c", 0) or 0 for r in resps), default=0)
                    ts = req.get("requestTimestamp__c", "")
                    ts_short = ts[-12:-1] if len(ts) > 12 else ts
                    context_html += f'<tr><td class="ts">{ts_short}</td>'
                    context_html += f'<td class="truncate" title="{html.escape(req.get("queryText__c","") or "")}">{html.escape((req.get("queryText__c","") or "")[:80])}</td>'
                    context_html += f'<td><code>{html.escape((req.get("retrieverApiName__c","") or "")[:30])}</code></td>'
                    context_html += f'<td>{len(resps)}</td>'
                    context_html += f'<td>{top_score:.4f}</td></tr>'
                    # Show response details in expandable row
                    if resps:
                        context_html += f'<tr class="detail-row"><td colspan="5"><details><summary>View {len(resps)} results</summary>'
                        context_html += '<table class="data-table compact"><thead><tr><th>Score</th><th>Record ID</th><th>Content Preview</th></tr></thead><tbody>'
                        for resp in sorted(resps, key=lambda r: -(r.get("scoreNumber__c", 0) or 0)):
                            result_text = (resp.get("resultText__c", "") or "")[:150]
                            context_html += f'<tr><td>{resp.get("scoreNumber__c", 0):.4f}</td>'
                            context_html += f'<td><code>{html.escape(resp.get("sourceRecordId__c","") or "")}</code></td>'
                            context_html += f'<td class="truncate">{html.escape(result_text)}</td></tr>'
                        context_html += '</tbody></table></details></td></tr>'
                context_html += '</tbody></table>'

    if not context_html:
        context_html = '<p class="empty-state">No context data available. Data Cloud session trace required.</p>'

    # Diagnostics tab
    diag_html = '<div class="diagnostics">'
    for d in diagnostics:
        diag_class = "diag-error" if "FAILURE" in d or "ERROR" in d or "ANOMALY" in d else "diag-ok" if "NO ISSUES" in d or "GROUNDED" in d else "diag-warn"
        icon = "🔴" if "error" in diag_class else "🟢" if "ok" in diag_class else "🟡"
        diag_html += f'<div class="diag-item {diag_class}">{icon} {html.escape(d)}</div>'
    diag_html += '</div>'

    # DC error notice
    dc_notice = ""
    if dc_error or (not sessions and not data.get("sessionIds")):
        dc_notice = '''<div class="dc-notice">
            <strong>⚠️ Data Cloud Session Trace Unavailable</strong><br>
            Core SOQL data (RecActorActionFeed, GenOpPlan) is valid. Data Cloud STDM tables may not be mapped on this org.
        </div>'''

    # AI Summary
    ai_summary_md = generate_ai_summary(data)
    # Convert markdown-ish to HTML
    summary_html = '<div class="ai-summary">'
    for line in ai_summary_md.split("\n"):
        if line.startswith("## "):
            summary_html += f'<h3 class="summary-heading">{html.escape(line[3:])}</h3>'
        elif line.startswith("**") and line.endswith("**"):
            summary_html += f'<p class="summary-bold">{html.escape(line.strip("*"))}</p>'
        elif line.startswith("🔴") or line.startswith("🟡") or line.startswith("✅") or line.startswith("⚠️"):
            css_class = "issue-red" if "🔴" in line else "issue-yellow" if "🟡" in line else "issue-green" if "✅" in line else "issue-warn"
            summary_html += f'<div class="summary-issue {css_class}">{html.escape(line)}</div>'
        elif line.startswith("   →"):
            summary_html += f'<div class="summary-fix">{html.escape(line.strip())}</div>'
        elif line.startswith("  "):
            summary_html += f'<div class="summary-indent">{html.escape(line.strip())}</div>'
        elif line.startswith("•"):
            summary_html += f'<div class="summary-bullet">{html.escape(line)}</div>'
        elif line.strip():
            # Handle inline bold **text**
            escaped = html.escape(line)
            escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
            escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)
            escaped = escaped.replace('`', '<code>').replace('</code>', '</code>', 1) if '`' in escaped else escaped
            # Proper backtick handling
            parts = escaped.split('`')
            if len(parts) > 2:
                result = parts[0]
                for i in range(1, len(parts)):
                    if i % 2 == 1:
                        result += f'<code>{parts[i]}</code>'
                    else:
                        result += parts[i]
                escaped = result
            summary_html += f'<p class="summary-line">{escaped}</p>'
    summary_html += '</div>'

    # Raw JSON tab
    raw_json = json.dumps(data, indent=2, default=str)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SRA Tracer — {html.escape(record_label)}</title>
<style>
:root {{
    --bg: #1a1a2e;
    --surface: #16213e;
    --surface2: #0f3460;
    --accent: #e94560;
    --accent2: #0ea5e9;
    --text: #eaeaea;
    --text-muted: #a0a0b0;
    --border: #2a2a4a;
    --success: #22c55e;
    --warning: #f59e0b;
    --error: #ef4444;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
}}
.header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}}
.header h1 {{
    font-size: 18px;
    font-weight: 600;
    color: var(--accent2);
}}
.header .meta {{
    font-size: 13px;
    color: var(--text-muted);
}}
.header .session-badge {{
    background: var(--accent);
    color: white;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}}
.trace-form {{
    display: flex;
    gap: 8px;
    align-items: center;
    margin-left: auto;
}}
.trace-input {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 7px 12px;
    font-size: 13px;
    color: var(--text);
    width: 320px;
    font-family: 'SF Mono', monospace;
}}
.trace-input:focus {{
    outline: none;
    border-color: var(--accent2);
    box-shadow: 0 0 0 2px rgba(14,165,233,0.2);
}}
.trace-btn {{
    background: var(--accent2);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
}}
.trace-btn:hover {{ background: #0284c7; }}
.trace-btn:disabled {{
    background: var(--border);
    cursor: wait;
}}
.loading-overlay {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(26,26,46,0.85);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 16px;
}}
.loading-overlay.active {{ display: flex; }}
.spinner {{
    width: 40px;
    height: 40px;
    border: 3px solid var(--border);
    border-top-color: var(--accent2);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
.loading-text {{ color: var(--text-muted); font-size: 14px; }}
.info-bar {{
    background: var(--surface2);
    padding: 12px 24px;
    display: flex;
    gap: 32px;
    font-size: 13px;
    border-bottom: 1px solid var(--border);
}}
.info-bar .info-item {{ display: flex; gap: 6px; }}
.info-bar .info-label {{ color: var(--text-muted); }}
.info-bar .info-value {{ color: var(--text); font-weight: 500; }}
.dc-notice {{
    background: #78350f;
    border: 1px solid var(--warning);
    border-radius: 6px;
    padding: 12px 16px;
    margin: 12px 24px;
    font-size: 13px;
    color: #fef3c7;
}}
.tabs {{
    display: flex;
    gap: 0;
    background: var(--surface);
    border-bottom: 2px solid var(--border);
    padding: 0 24px;
    overflow-x: auto;
}}
.tab {{
    padding: 12px 18px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    white-space: nowrap;
    transition: all 0.15s;
}}
.tab:hover {{ color: var(--text); background: rgba(255,255,255,0.03); }}
.tab.active {{
    color: var(--accent2);
    border-bottom-color: var(--accent2);
}}
.tab-content {{
    display: none;
    padding: 24px;
    max-width: 1400px;
    overflow-x: auto;
}}
.tab-content.active {{ display: block; }}
h3 {{ font-size: 15px; margin: 16px 0 10px; color: var(--accent2); }}
h4 {{ font-size: 13px; margin: 12px 0 8px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}
.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    margin-bottom: 20px;
}}
.data-table th {{
    background: var(--surface2);
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
}}
.data-table td {{
    padding: 7px 10px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
}}
.data-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
.data-table .error-row td {{ background: rgba(239,68,68,0.1); }}
.truncate {{ max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.ts {{ font-family: 'SF Mono', monospace; font-size: 11px; color: var(--text-muted); }}
.badge {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
}}
.badge-topic_step {{ background: #1e3a5f; color: #60a5fa; }}
.badge-action_step {{ background: #1a3f2e; color: #4ade80; }}
.badge-llm_completion_response {{ background: #3b1f4a; color: #c084fc; }}
.badge-action_success_response {{ background: #1a3f2e; color: #86efac; }}
.badge-input {{ background: #3b3010; color: #fbbf24; }}

.transcript {{ max-width: 700px; }}
.message {{
    margin: 8px 0;
    padding: 10px 14px;
    border-radius: 10px;
    max-width: 85%;
}}
.message.user {{
    background: var(--surface2);
    border: 1px solid var(--border);
    margin-left: auto;
}}
.message.agent {{
    background: #1a2744;
    border: 1px solid #2a4a7a;
}}
.msg-header {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}}
.msg-type {{ font-size: 10px; font-weight: 600; color: var(--accent2); text-transform: uppercase; }}
.msg-ts {{ font-size: 10px; color: var(--text-muted); font-family: monospace; }}
.msg-content {{ font-size: 13px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }}

.stat-grid {{ display: flex; gap: 20px; margin: 16px 0; }}
.stat {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 24px;
    text-align: center;
}}
.stat.warning {{ border-color: var(--warning); }}
.stat-num {{ display: block; font-size: 28px; font-weight: 700; color: var(--text); }}
.stat.warning .stat-num {{ color: var(--warning); }}
.stat-label {{ display: block; font-size: 11px; color: var(--text-muted); margin-top: 4px; text-transform: uppercase; }}

.article-list {{ list-style: none; }}
.article-item {{ padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 13px; }}

.attr-section {{ margin: 16px 0; padding: 12px 0; border-bottom: 1px solid var(--border); }}
.attr-section h4 {{ margin-bottom: 8px; }}
.attr-section ul {{ list-style: none; padding-left: 8px; }}
.attr-section li {{ padding: 3px 0; font-size: 13px; }}
.warning-section {{ background: rgba(245,158,11,0.05); border: 1px solid rgba(245,158,11,0.2); border-radius: 6px; padding: 12px 16px !important; }}
.llm-only-item {{ color: var(--warning); }}

.meta-table {{ border-collapse: collapse; margin: 8px 0; }}
.meta-table td {{ padding: 4px 12px 4px 0; font-size: 13px; vertical-align: top; }}
.meta-key {{ color: var(--text-muted); font-weight: 500; min-width: 120px; }}

.plan-steps {{ font-size: 12px; line-height: 1.6; white-space: pre-wrap; color: var(--text); background: var(--surface2); padding: 12px; border-radius: 6px; }}

.feed-entry, .action-entry {{
    margin: 12px 0;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
}}
.feed-header, .action-header {{
    background: var(--surface2);
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
}}
.json-block {{
    padding: 12px;
    font-size: 11px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    line-height: 1.5;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 400px;
    overflow-y: auto;
    background: var(--bg);
}}

.diagnostics {{ margin: 8px 0; }}
.diag-item {{
    padding: 10px 14px;
    margin: 6px 0;
    border-radius: 6px;
    font-size: 13px;
    line-height: 1.5;
}}
.diag-error {{ background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); }}
.diag-ok {{ background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); }}
.diag-warn {{ background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); }}

.empty-state {{ color: var(--text-muted); font-style: italic; padding: 40px; text-align: center; }}

code {{ font-family: 'SF Mono', monospace; font-size: 12px; background: var(--surface2); padding: 1px 5px; border-radius: 3px; }}

#raw-json {{
    font-size: 11px;
    font-family: 'SF Mono', monospace;
    line-height: 1.4;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 80vh;
    overflow-y: auto;
    background: var(--surface);
    padding: 16px;
    border-radius: 6px;
}}
.ai-summary {{
    max-width: 800px;
    line-height: 1.7;
}}
.ai-summary .summary-heading {{
    font-size: 16px;
    color: var(--accent2);
    margin: 24px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}}
.ai-summary .summary-heading:first-child {{ margin-top: 0; }}
.ai-summary p, .ai-summary .summary-line {{
    margin: 6px 0;
    font-size: 14px;
}}
.ai-summary .summary-bold {{
    font-weight: 600;
    font-size: 14px;
    margin: 8px 0;
}}
.ai-summary .summary-issue {{
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 5px;
    font-size: 14px;
    font-weight: 500;
}}
.ai-summary .issue-red {{ background: rgba(239,68,68,0.1); border-left: 3px solid var(--error); }}
.ai-summary .issue-yellow {{ background: rgba(245,158,11,0.1); border-left: 3px solid var(--warning); }}
.ai-summary .issue-green {{ background: rgba(34,197,94,0.1); border-left: 3px solid var(--success); }}
.ai-summary .issue-warn {{ background: rgba(245,158,11,0.08); border-left: 3px solid var(--warning); }}
.ai-summary .summary-fix {{
    margin: 2px 0 8px 20px;
    font-size: 13px;
    color: var(--text-muted);
    font-style: italic;
}}
.ai-summary .summary-indent {{
    margin: 2px 0;
    padding-left: 16px;
    font-size: 13px;
    color: var(--text-muted);
}}
.ai-summary .summary-bullet {{
    margin: 4px 0;
    padding-left: 8px;
    font-size: 13px;
}}
.ai-summary strong {{ color: var(--text); }}
.ai-summary em {{ color: var(--text-muted); font-style: italic; }}
.ai-summary code {{ font-size: 12px; }}

/* Context & Grounding tab */
.context-turn {{
    border: 1px solid var(--border);
    border-radius: 6px;
    margin: 8px 0;
    overflow: hidden;
}}
.context-turn-header {{
    padding: 10px 14px;
    background: var(--surface);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
}}
.context-turn-header:hover {{ background: #2a2d35; }}
.expand-icon {{ transition: transform 0.2s; font-size: 10px; }}
.context-turn.expanded .expand-icon {{ transform: rotate(90deg); }}
.context-turn-body {{
    display: none;
    padding: 12px 16px;
    border-top: 1px solid var(--border);
}}
.context-turn.expanded .context-turn-body {{ display: block; }}
.context-section {{
    margin: 12px 0;
}}
.context-section h5 {{
    color: var(--accent);
    margin: 0 0 6px 0;
    font-size: 13px;
}}
.context-block {{
    background: #1a1c22;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 10px;
    font-size: 12px;
    line-height: 1.5;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
}}
.knowledge-block {{
    border-left: 3px solid #4ade80;
}}
.empty-note {{
    color: var(--text-muted);
    font-style: italic;
    font-size: 12px;
}}
.tool-call, .tool-result {{
    margin: 6px 0;
    padding-left: 8px;
    border-left: 2px solid var(--border);
}}
.detail-row td {{
    padding: 4px 8px !important;
    background: #1a1c22;
}}
.data-table.compact {{
    font-size: 11px;
}}
.data-table.compact td, .data-table.compact th {{
    padding: 4px 6px;
}}
.badge-ok {{
    background: #1a3f2e;
    color: #4ade80;
}}
</style>
</head>
<body>

<div class="header">
    <h1>🔍 SRA Tracer</h1>
    <form class="trace-form" method="POST" action="/trace">
        <input type="text" name="record_id" class="trace-input" placeholder="Case or MessagingSession ID (500... / 0Mw...)" value="{html.escape(data.get('recordId',''))}" />
        <button type="submit" class="trace-btn">🔍 Trace</button>
    </form>
    <span class="session-badge">{html.escape(record_label)}</span>
</div>

<div class="info-bar">
    <div class="info-item"><span class="info-label">Org:</span><span class="info-value">{html.escape(org)}</span></div>
    <div class="info-item"><span class="info-label">Type:</span><span class="info-value">{html.escape(record_type)}</span></div>
    <div class="info-item"><span class="info-label">Status:</span><span class="info-value">{html.escape(str(record_meta.get("Status", "")))}</span></div>
    <div class="info-item"><span class="info-label">Contact:</span><span class="info-value">{html.escape(str(record_meta.get("EndUserContactId", record_meta.get("ContactId", ""))))}</span></div>
    <div class="info-item"><span class="info-label">Traced:</span><span class="info-value">{html.escape(timestamp[:19] if timestamp else "")}</span></div>
</div>

{dc_notice}

<div class="tabs">
    <div class="tab active" data-tab="summary">🤖 AI Summary</div>
    <div class="tab" data-tab="diagnostics">🩺 Diagnostics</div>
    <div class="tab" data-tab="dynamic-plan">📋 Dynamic Plan</div>
    <div class="tab" data-tab="transcript">💬 Transcript</div>
    <div class="tab" data-tab="knowledge">📚 Knowledge Grounding</div>
    <div class="tab" data-tab="attribution">🔗 Source Attribution</div>
    <div class="tab" data-tab="feeds">⚡ RecActorActionFeed</div>
    <div class="tab" data-tab="plan">📝 Summary Plan</div>
    <div class="tab" data-tab="context">🧠 Context & Grounding</div>
    <div class="tab" data-tab="gateway">🌐 Gateway Calls</div>
    <div class="tab" data-tab="actions">⚙️ Actions</div>
    <div class="tab" data-tab="raw">{{ }} Raw JSON</div>
</div>

<div class="tab-content active" id="tab-summary">{summary_html}</div>
<div class="tab-content" id="tab-diagnostics">{diag_html}</div>
<div class="tab-content" id="tab-dynamic-plan">{dynamic_plan_html}</div>
<div class="tab-content" id="tab-transcript">{transcript_html}</div>
<div class="tab-content" id="tab-knowledge">{kg_html}</div>
<div class="tab-content" id="tab-attribution">{attr_html}</div>
<div class="tab-content" id="tab-feeds">{feed_html}</div>
<div class="tab-content" id="tab-plan">{plan_html}</div>
<div class="tab-content" id="tab-context">{context_html}</div>
<div class="tab-content" id="tab-gateway">{gw_html}</div>
<div class="tab-content" id="tab-actions">{actions_html}</div>
<div class="tab-content" id="tab-raw"><pre id="raw-json">{html.escape(raw_json[:100000])}</pre></div>

<div class="loading-overlay" id="loading">
    <div class="spinner"></div>
    <div class="loading-text">Tracing session...</div>
</div>

<script>
document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    }});
}});
// Make truncated cells expandable
document.querySelectorAll('.truncate').forEach(el => {{
    el.addEventListener('click', () => {{
        el.style.maxWidth = el.style.maxWidth ? '' : 'none';
        el.style.whiteSpace = el.style.whiteSpace === 'normal' ? '' : 'normal';
    }});
}});
// Form submission with loading state
document.querySelector('.trace-form').addEventListener('submit', (e) => {{
    const input = document.querySelector('.trace-input');
    const id = input.value.trim();
    if (!id) {{ e.preventDefault(); return; }}
    document.getElementById('loading').classList.add('active');
    document.querySelector('.trace-btn').disabled = true;
}});
</script>
</body>
</html>'''


def serve_html(html_content: str, port: int = 8787, org: str = "", max_sessions: int = 3):
    """Serve the HTML on a local port and open the browser."""
    current_html = [html_content]  # mutable container for closure

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(current_html[0].encode("utf-8"))

        def do_POST(self):
            if self.path == "/trace":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                # Parse form data
                from urllib.parse import parse_qs
                params = parse_qs(body)
                record_id = params.get("record_id", [""])[0].strip()

                if record_id and org:
                    print(f"\n🔄 New trace requested: {record_id}")
                    try:
                        data = collect_trace_data(record_id, org, max_sessions)
                        current_html[0] = generate_html(data)
                        # Save JSON
                        out_dir = Path.home() / ".claude" / "data" / "sra-agent-debugger" / org / data["recordLabel"]
                        out_dir.mkdir(parents=True, exist_ok=True)
                        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                        json_file = out_dir / f"trace_{timestamp}.json"
                        json_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
                        print(f"  Saved: {json_file}")
                    except Exception as e:
                        print(f"  ERROR: {e}")

                # Redirect back to GET
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress log noise

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    print(f"\n✅ Viewer ready at: http://127.0.0.1:{port}")
    print(f"   Paste any Case/MessagingSession ID in the input to re-trace.")
    print(f"   Press Ctrl+C to stop.\n")

    # Open browser
    webbrowser.open(f"http://127.0.0.1:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()


def main():
    parser = argparse.ArgumentParser(description="SRA Tracer — HTML Viewer")
    parser.add_argument("--id", help="18-char Case ID (500...) or MessagingSession ID (0Mw...)")
    parser.add_argument("--org", help="sf CLI org alias")
    parser.add_argument("--file", help="Path to an existing trace JSON or .txt file")
    parser.add_argument("--max-sessions", type=int, default=3, help="Max DC sessions to trace")
    parser.add_argument("--port", type=int, default=8787, help="Local port (default 8787)")
    parser.add_argument("--save", help="Save HTML to file instead of serving")
    args = parser.parse_args()

    if args.file:
        # Load from file
        filepath = Path(args.file)
        if filepath.suffix == ".json":
            data = json.loads(filepath.read_text())
        else:
            # Parse .txt trace file
            data = parse_trace_file(str(filepath))
            data["recordLabel"] = filepath.stem
            data["org"] = "file"
            data["recordType"] = "File"
            data["recordMeta"] = {}
            data["genOpPlans"] = []
            data["feeds"] = []
            data["kgAnalysis"] = {"grounded_count": 0, "empty_count": 0, "total_feeds": 0, "articles_cited": []}
            data["sessions"] = []
            data["diagnostics"] = ["Loaded from file — run live trace for full diagnostics."]
            data["attribution"] = {}
            data["timestamp"] = ""
    elif args.org and not args.id:
        # Start with empty page — user will trace from the browser
        data = {
            "recordId": "",
            "recordType": "",
            "recordMeta": {},
            "recordLabel": "Ready",
            "org": args.org,
            "genOpPlans": [],
            "feeds": [],
            "kgAnalysis": {"grounded_count": 0, "empty_count": 0, "total_feeds": 0, "articles_cited": []},
            "sessions": [],
            "sessionIds": [],
            "diagnostics": ["Paste a Case or MessagingSession ID above and click Trace."],
            "attribution": {},
            "dcError": None,
            "timestamp": "",
        }
    elif args.id and args.org:
        # Run live trace
        data = collect_trace_data(args.id, args.org, args.max_sessions)

        # Also save JSON for later
        out_dir = Path.home() / ".claude" / "data" / "sra-agent-debugger" / args.org / data["recordLabel"]
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        json_file = out_dir / f"trace_{timestamp}.json"
        json_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        print(f"  Saved JSON: {json_file}")
    else:
        print("Usage: python3 viewer.py --org <alias>")
        print("       python3 viewer.py --id <record_id> --org <alias>")
        print("       python3 viewer.py --file <trace_file.json>")
        sys.exit(1)

    # Generate HTML
    html_content = generate_html(data)

    if args.save:
        Path(args.save).write_text(html_content, encoding="utf-8")
        print(f"Saved HTML: {args.save}")
    else:
        org_alias = args.org or data.get("org", "")
        serve_html(html_content, args.port, org=org_alias, max_sessions=args.max_sessions)


if __name__ == "__main__":
    main()
