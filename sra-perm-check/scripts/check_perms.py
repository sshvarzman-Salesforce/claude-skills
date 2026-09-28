#!/usr/bin/env python3
"""
sra-perm-check — validate an org's Service Rep Assistant / Service Assistant permissions
against the official Salesforce Help permission requirements.

Read-only. Never modifies the org.

Usage:
    python3 check_perms.py --org <alias> [--channel case|messaging|voice|all]
                           [--rep-user <005...>] [--json]

Requires: sf CLI authenticated against the target org, Python 3.9+.
"""
import argparse
import json
import subprocess
import sys

# ---- permission definitions (anchored to Salesforce Help docs) ----------------

# Permission SETS matched by developer Name.
PS_SERVICE_PLANNER_USER = "ServicePlannerUser"
PS_SERVICE_PLANNER_AGENT = "ServicePlannerAgentUser"
PS_SERVICE_PLANNER_BUILDER = "ServicePlannerBuilder"
PS_ACCESS_DEFAULT_AGENT = "CopilotSalesforceUser"  # "Access Agentforce Default Agent"

# App (user) permission fields on PermissionSet, confirmed via describe:
APP_ACCESS_CE = "PermissionsCanAccessCE"       # Access Conversation Entries
APP_VIEW_ALL_CALLS = "PermissionsViewAllCalls" # View All Voice And Video Calls
APP_RUN_FLOW = "PermissionsRunFlow"            # Run Flows

GREEN, RED, WARN = "✅", "❌", "⚠️"


def sfq(org, soql):
    """Run a SOQL query via sf CLI, return list of records (dicts)."""
    out = subprocess.run(
        ["sf", "data", "query", "--target-org", org, "--query", soql, "--json"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        # surface the error but don't crash the whole run
        msg = (out.stdout or "") + (out.stderr or "")
        try:
            j = json.loads(out.stdout)
            msg = j.get("message", msg)
        except Exception:
            pass
        raise RuntimeError(msg.strip())
    return json.loads(out.stdout)["result"]["records"]


def assignees_of(org, ps_name):
    recs = sfq(org, f"SELECT AssigneeId, Assignee.Name, Assignee.Username "
                    f"FROM PermissionSetAssignment WHERE PermissionSet.Name = '{ps_name}'")
    return [(r["AssigneeId"], r["Assignee"]["Name"], r["Assignee"]["Username"]) for r in recs]


def user_permsets(org, uid):
    """All perm sets assigned to a user: list of (name, label)."""
    recs = sfq(org, f"SELECT PermissionSet.Name, PermissionSet.Label "
                    f"FROM PermissionSetAssignment WHERE AssigneeId = '{uid}'")
    return [(r["PermissionSet"]["Name"], r["PermissionSet"]["Label"]) for r in recs]


def has_permset(permsets, name=None, name_prefix=None, label=None):
    for n, l in permsets:
        if name and n == name:
            return (n, l)
        if name_prefix and n and n.startswith(name_prefix):
            return (n, l)
        if label and l == label:
            return (n, l)
    return None


def app_perm_source(org, uid, field):
    """Return the perm set name granting a boolean app perm, or None."""
    recs = sfq(org, f"SELECT Name FROM PermissionSet "
                    f"WHERE Id IN (SELECT PermissionSetId FROM PermissionSetAssignment "
                    f"WHERE AssigneeId = '{uid}') AND {field} = true")
    return recs[0]["Name"] if recs else None


def object_perm(org, uid, sobject):
    recs = sfq(org, f"SELECT Parent.Label, PermissionsRead, PermissionsViewAllRecords, "
                    f"PermissionsViewAllFields FROM ObjectPermissions "
                    f"WHERE ParentId IN (SELECT PermissionSetId FROM PermissionSetAssignment "
                    f"WHERE AssigneeId = '{uid}') AND SobjectType = '{sobject}'")
    read = any(r.get("PermissionsRead") for r in recs)
    vaf = any(r.get("PermissionsViewAllFields") for r in recs)
    src = recs[0]["Parent"]["Label"] if recs else None
    return read, vaf, src


def find_eligibility_flow(org, channel):
    """Return (ApiName, DurableId/FlowDefinitionId) of the channel's eligibility flow, or (None, None)."""
    try:
        recs = sfq(org, "SELECT DurableId, ApiName, Label, IsActive FROM FlowDefinitionView WHERE IsActive = true")
    except RuntimeError:
        return (None, None)
    for r in recs:
        blob = (r.get("ApiName", "") + " " + r.get("Label", "")).lower()
        chan_hit = ("voice" in blob) if channel == "voice" else ("messag" in blob)
        if "eligib" in blob and chan_hit:
            return (r["ApiName"], r.get("DurableId"))
    return (None, None)


def flow_access_source(org, uid, flow_def_id):
    """Return the perm set label granting DIRECT access to a flow (SetupEntityType='FlowDefinition'),
    for a perm set assigned to the user. This is the eligibility-flow access the doc requires;
    the Run Flows app permission does NOT satisfy it."""
    if not flow_def_id:
        return None
    recs = sfq(org, f"SELECT Parent.Label FROM SetupEntityAccess "
                    f"WHERE SetupEntityType='FlowDefinition' AND SetupEntityId='{flow_def_id}' "
                    f"AND ParentId IN (SELECT PermissionSetId FROM PermissionSetAssignment "
                    f"WHERE AssigneeId='{uid}')")
    return recs[0]["Parent"]["Label"] if recs else None


def line(persona, label, status, note=""):
    dots = "." * max(3, 42 - len(label))
    n = f"  ({note})" if note else ""
    return f"  {persona:<7}{label} {dots} {status}{n}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", required=True)
    ap.add_argument("--channel", default="all", choices=["case", "messaging", "voice", "all"])
    ap.add_argument("--rep-user", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    org = args.org

    # --- resolve users ---
    agent_users = assignees_of(org, PS_SERVICE_PLANNER_AGENT)
    rep_users = assignees_of(org, PS_SERVICE_PLANNER_USER)
    if args.rep_user:
        rep_users = [r for r in rep_users if r[0].startswith(args.rep_user[:15])]

    if not agent_users:
        print(f"{RED} No agent runtime user found (no ServicePlannerAgentUser assignee). "
              f"Is SRA set up in this org?")
        sys.exit(1)

    agent_uid, agent_name, agent_un = agent_users[0]
    agent_ps = user_permsets(org, agent_uid)

    channels = ["case", "messaging", "voice"] if args.channel == "all" else [args.channel]
    report = {"org": org, "agent_user": {"id": agent_uid, "name": agent_name},
              "rep_users": [{"id": r[0], "name": r[1]} for r in rep_users], "channels": {}}

    print(f"\n\U0001f510 SRA Permission Check — {org}   (channel: {args.channel})")
    reps_str = ", ".join(f"{r[1]}" for r in rep_users) or "(none found)"
    print(f"Rep user(s): {reps_str}   |   Agent runtime user: {agent_name} ({agent_uid[:8]}…)\n")

    # --- BASE: Mandatory ---
    print("BASE — Mandatory")
    base = {}
    # rep-side (check the first rep, or all)
    for uid, name, _ in (rep_users or []):
        rps = user_permsets(org, uid)
        spu = has_permset(rps, name=PS_SERVICE_PLANNER_USER)
        ada = has_permset(rps, name=PS_ACCESS_DEFAULT_AGENT)
        print(line("Rep", f"Service Planner User [{name}]", GREEN if spu else RED))
        print(line("Rep", f"Access Agentforce Default Agent [{name}]", GREEN if ada else RED))
        base[name] = {"ServicePlannerUser": bool(spu), "AccessAgentforceDefaultAgent": bool(ada)}
    if not rep_users:
        print(line("Rep", "Service Planner User", WARN, "no ServicePlannerUser assignees found"))

    spa = has_permset(agent_ps, name=PS_SERVICE_PLANNER_AGENT)
    afsa = has_permset(agent_ps, name_prefix="Agentforce_Service_Assistant")
    dcu = has_permset(agent_ps, label="Data Cloud User")
    print(line("Agent", "Service Planner Agent User", GREEN if spa else RED))
    print(line("Agent", "Agentforce_Service_Assistant Perms", GREEN if afsa else RED,
               afsa[0] if afsa else ""))
    print(line("Agent", "Data Cloud User (manual-assign)", GREEN if dcu else RED))
    report["base"] = {"agent": {"ServicePlannerAgentUser": bool(spa),
                                "AgentforceServiceAssistant": bool(afsa),
                                "DataCloudUser": bool(dcu)}, "rep": base}

    # --- per channel ---
    for ch in channels:
        print(f"\n{ch.upper()}")
        cr = {}
        if ch == "case":
            print("  (Base Mandatory is sufficient; ContactId context var auto-populated. "
                  "Add Knowledge/Action perms only if those features are used.)")
        if ch in ("voice", "messaging"):
            ce_src = app_perm_source(org, agent_uid, APP_ACCESS_CE)
            print(line("Agent", "Access Conversation Entries", GREEN if ce_src else RED, ce_src or ""))
            cr["AccessConversationEntries"] = bool(ce_src)
        if ch == "voice":
            vac_src = app_perm_source(org, agent_uid, APP_VIEW_ALL_CALLS)
            print(line("Agent", "View ALL Voice and Video Calls", GREEN if vac_src else RED, vac_src or ""))
            cr["ViewAllVoiceAndVideoCalls"] = bool(vac_src)
        if ch == "messaging":
            read, vaf, src = object_perm(org, agent_uid, "MessagingSession")
            st = GREEN if (read and vaf) else (WARN if read else RED)
            note = src or ""
            if read and not vaf:
                note = f"{src}: Read ok, View All Fields MISSING"
            print(line("Agent", "MessagingSession Read + View All Fields", st, note))
            cr["MessagingSessionAccess"] = {"read": read, "viewAllFields": vaf}
        if ch in ("voice", "messaging"):
            flow_api, flow_id = find_eligibility_flow(org, ch)
            if not flow_id:
                print(line("Rep", "Eligibility flow DIRECT access", WARN,
                           "eligibility flow not auto-located — verify manually"))
                cr["EligibilityFlowDirectAccess"] = "MANUAL"
            else:
                cr["EligibilityFlowDirectAccess"] = {}
                for uid, name, _ in (rep_users or []):
                    src = flow_access_source(org, uid, flow_id)
                    st = GREEN if src else RED
                    note = src if src else "NO direct grant — Run Flows does NOT count"
                    print(line("Rep", f"Eligibility flow access [{name}]", st, note))
                    cr["EligibilityFlowDirectAccess"][name] = bool(src)
                print(f"           Flow: {flow_api} ({flow_id})")
        report["channels"][ch] = cr

    # --- verdict ---
    hard_fail = (not spa or not afsa or not dcu)
    for uid, name, _ in (rep_users or []):
        b = report["base"]["rep"].get(name, {})
        if not b.get("ServicePlannerUser") or not b.get("AccessAgentforceDefaultAgent"):
            hard_fail = True
    def has_false(v):
        if v is False:
            return True
        if isinstance(v, dict):
            return any(has_false(x) for x in v.values())
        return False
    for ch, cr in report["channels"].items():
        for k, v in cr.items():
            if has_false(v):
                hard_fail = True

    print("\nVERDICT:")
    if hard_fail:
        print(f"  {RED} Documented permission gap(s) found above — fix the ❌ rows first.")
    else:
        print(f"  {GREEN} All documented permissions are present on the correct users.")
        print("  If the panel still errors, this is NOT a documented")
        print("  permission gap → check enablement (Agent Chat / Adaptive add-on, EinsteinSRAgentforce)")
        print("  and capture the failed request's network response body for the precise error.")

    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
