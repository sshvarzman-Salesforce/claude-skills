#!/usr/bin/env python3
"""
sra-perm-setup — PROVISION Service Rep Assistant / Service Assistant permissions
on the correct users, per channel, following the official Salesforce Help docs.

This is the WRITE counterpart to check_perms.py. It:
  1. Assigns the standard SRA perm sets to the correct identities
       - human/admin user(s): ServicePlannerUser + CopilotSalesforceUser
                              ("Access Agentforce Default Agent")
       - planner (agent runtime) user: ServicePlannerAgentUser + Data Cloud User
  2. Creates + assigns the additive CUSTOM access perm sets per channel
       - Voice:     <prefix>Agent_Voice_Access   (planner)  -> Access Conversation
                    Entries + View All Voice and Video Calls
                    <prefix>Voice_Eligibility_Flow_Access (human) -> direct flow access
       - Messaging: <prefix>Agent_Messaging_Access (planner) -> Access Conversation
                    Entries + MessagingSession Read + View All Fields
                    <prefix>Messaging_Eligibility_Flow_Access (human) -> direct flow access
       - Case:      base only (no additive perm block)
  3. Verifies with check_perms.py.

SAFETY
  - DRY-RUN by default. Nothing is written. Custom perm sets are still *validated*
    against the org via a `--dry-run` (check-only) metadata deploy, so you get real
    confidence before committing.
  - Pass --apply to actually deploy the perm sets and create the assignments.
  - Idempotent: existing assignments are detected and skipped; never deletes anything.

Usage:
    # preview + validate (writes nothing):
    python3 setup_perms.py --org KatsSDO --admin-user mrbatt13_wgnxvyjg@gmail.com \\
        --planner-user agentforce_service_assistant@...ext --channels voice

    # actually provision:
    python3 setup_perms.py --org KatsSDO --admin-user <id|username|Name> \\
        --channels voice,messaging --apply

Requires: sf CLI authenticated against the target org, Python 3.9+.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GREEN, RED, WARN, ARROW = "✅", "❌", "⚠️", "→"

# ---- standard perm sets (already exist in the org; we only ASSIGN them) --------
PS_SERVICE_PLANNER_USER = "ServicePlannerUser"       # human
PS_ACCESS_DEFAULT_AGENT = "CopilotSalesforceUser"    # human — "Access Agentforce Default Agent"
PS_SERVICE_PLANNER_AGENT = "ServicePlannerAgentUser" # planner
DATA_CLOUD_USER_LABEL = "Data Cloud User"            # planner — matched by LABEL, manual-assign

# app (user) permission METADATA names (field name minus the "Permissions" prefix)
UP_ACCESS_CE = "CanAccessCE"     # PermissionsCanAccessCE  — Access Conversation Entries
UP_VIEW_ALL_CALLS = "ViewAllCalls"  # PermissionsViewAllCalls — View All Voice and Video Calls

API_VERSION = "62.0"


# ------------------------------------------------------------------ sf helpers --
def sf(args):
    """Run an sf command (list of args), return parsed JSON dict (or raise)."""
    out = subprocess.run(["sf"] + args + ["--json"], capture_output=True, text=True)
    try:
        j = json.loads(out.stdout or "{}")
    except Exception:
        j = {}
    if out.returncode != 0 and not j:
        raise RuntimeError((out.stderr or out.stdout or "sf command failed").strip())
    return j


def sfq(org, soql):
    j = sf(["data", "query", "--target-org", org, "--query", soql])
    if "result" not in j:
        raise RuntimeError(j.get("message", "query failed"))
    return j["result"]["records"]


def resolve_users(org, idents):
    """Resolve a comma-separated list of Id/username/Name into [(id, name, username)]."""
    resolved = []
    for raw in idents:
        ident = raw.strip()
        if not ident:
            continue
        if ident.startswith("005") and len(ident) in (15, 18):
            where = f"Id = '{ident}'"
        elif "@" in ident:
            where = f"Username = '{ident}'"
        else:
            where = f"Name = '{ident}'"
        recs = sfq(org, f"SELECT Id, Name, Username FROM User WHERE {where} AND IsActive = true")
        if not recs:
            print(f"  {RED} Could not resolve active user: {ident}")
            continue
        for r in recs:
            resolved.append((r["Id"], r["Name"], r["Username"]))
    return resolved


def auto_planner(org):
    recs = sfq(org, "SELECT AssigneeId, Assignee.Name, Assignee.Username FROM "
                    "PermissionSetAssignment WHERE PermissionSet.Name = "
                    f"'{PS_SERVICE_PLANNER_AGENT}'")
    return [(r["AssigneeId"], r["Assignee"]["Name"], r["Assignee"]["Username"]) for r in recs]


def permset_id_by_name(org, name):
    recs = sfq(org, f"SELECT Id, Label FROM PermissionSet WHERE Name = '{name}'")
    return (recs[0]["Id"], recs[0]["Label"]) if recs else (None, None)


def permset_id_by_label(org, label):
    recs = sfq(org, f"SELECT Id, Name FROM PermissionSet WHERE Label = '{label}'")
    return (recs[0]["Id"], recs[0]["Name"]) if recs else (None, None)


def is_assigned(org, uid, ps_id):
    recs = sfq(org, "SELECT Id FROM PermissionSetAssignment WHERE "
                    f"AssigneeId = '{uid}' AND PermissionSetId = '{ps_id}'")
    return bool(recs)


def find_eligibility_flow(org, channel):
    """Return the channel's active eligibility flow ApiName, or None."""
    try:
        recs = sfq(org, "SELECT ApiName, Label, IsActive FROM FlowDefinitionView WHERE IsActive = true")
    except RuntimeError:
        return None
    for r in recs:
        blob = ((r.get("ApiName") or "") + " " + (r.get("Label") or "")).lower()
        chan_hit = ("voice" in blob) if channel == "voice" else ("messag" in blob)
        if "eligib" in blob and chan_hit:
            return r["ApiName"]
    return None


# --------------------------------------------------------------- perm set XML --
def permset_xml(label, description, app_perms=None, obj_perms=None, flows=None):
    app_perms = app_perms or []
    obj_perms = obj_perms or []
    flows = flows or []
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">',
             f'    <label>{label}</label>',
             f'    <description>{description}</description>',
             '    <hasActivationRequired>false</hasActivationRequired>']
    for p in app_perms:
        parts.append(f'    <userPermissions><enabled>true</enabled><name>{p}</name></userPermissions>')
    for o in obj_perms:
        parts.append('    <objectPermissions>')
        parts.append(f'        <object>{o["object"]}</object>')
        parts.append(f'        <allowRead>{str(o.get("read", False)).lower()}</allowRead>')
        parts.append(f'        <allowCreate>{str(o.get("create", False)).lower()}</allowCreate>')
        parts.append(f'        <allowEdit>{str(o.get("edit", False)).lower()}</allowEdit>')
        parts.append(f'        <allowDelete>{str(o.get("delete", False)).lower()}</allowDelete>')
        parts.append(f'        <viewAllRecords>{str(o.get("viewAllRecords", False)).lower()}</viewAllRecords>')
        parts.append(f'        <modifyAllRecords>{str(o.get("modifyAll", False)).lower()}</modifyAllRecords>')
        parts.append('    </objectPermissions>')
    for f in flows:
        parts.append(f'    <flowAccesses><enabled>true</enabled><flow>{f}</flow></flowAccesses>')
    parts.append('</PermissionSet>')
    return "\n".join(parts)


def deploy_permsets(org, permsets, apply, api_version=API_VERSION):
    """permsets: dict {fullName: xml}. Deploy via mdapi dir. Validate-only unless apply."""
    if not permsets:
        return True
    tmp = tempfile.mkdtemp(prefix="sra_perm_setup_")
    psdir = os.path.join(tmp, "permissionsets")
    os.makedirs(psdir, exist_ok=True)
    for full, xml in permsets.items():
        with open(os.path.join(psdir, f"{full}.permissionset"), "w") as fh:
            fh.write(xml)
    members = "".join(f"<members>{m}</members>" for m in permsets)
    with open(os.path.join(tmp, "package.xml"), "w") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<Package xmlns="http://soap.sforce.com/2006/04/metadata">\n'
                 f'  <types>{members}<name>PermissionSet</name></types>\n'
                 f'  <version>{api_version}</version>\n</Package>\n')
    args = ["project", "deploy", "start", "--metadata-dir", tmp,
            "--target-org", org, "--wait", "10"]
    if not apply:
        args.append("--dry-run")  # validate only
    mode = "APPLY (deploy)" if apply else "VALIDATE (check-only)"
    print(f"\n  {ARROW} Metadata {mode} for: {', '.join(permsets)}")
    try:
        j = sf(args)
    except RuntimeError as e:
        print(f"  {RED} deploy call failed: {e}")
        return False
    res = j.get("result", {})
    ok = res.get("success", False) or (res.get("status") == "Succeeded")
    if ok:
        print(f"  {GREEN} perm set metadata {'deployed' if apply else 'validated'} OK")
        return True
    print(f"  {RED} perm set metadata {'deploy' if apply else 'validation'} FAILED:")
    failures = (res.get("details", {}) or {}).get("componentFailures", []) or []
    if isinstance(failures, dict):
        failures = [failures]
    for f in failures[:10]:
        print(f"      - {f.get('fullName','?')}: {f.get('problem','?')}")
    if not failures:
        print(f"      {json.dumps(res)[:500]}")
    return False


def set_view_all_fields(org, ps_id, sobject, apply):
    """Set PermissionsViewAllFields=true on the perm set's ObjectPermissions row.
    'View All Fields' is NOT a valid element in .permissionset metadata, so it must be
    set on the data record after the Read grant creates the ObjectPermissions row."""
    if not ps_id:
        return f"{RED} perm set not found"
    try:
        recs = sfq(org, "SELECT Id, PermissionsViewAllFields FROM ObjectPermissions WHERE "
                        f"ParentId = '{ps_id}' AND SobjectType = '{sobject}'")
    except RuntimeError as e:
        return f"{WARN} could not check: {e}"
    if recs and recs[0].get("PermissionsViewAllFields"):
        return f"{GREEN} View All Fields already set"
    if not apply:
        return f"{WARN} WOULD set View All Fields (dry-run)"
    try:
        if recs:
            sf(["data", "update", "record", "--target-org", org, "--sobject", "ObjectPermissions",
                "--record-id", recs[0]["Id"], "--values", "PermissionsViewAllFields=true"])
        else:
            sf(["data", "create", "record", "--target-org", org, "--sobject", "ObjectPermissions",
                "--values", f"ParentId={ps_id} SobjectType={sobject} "
                            f"PermissionsRead=true PermissionsViewAllFields=true"])
        return f"{GREEN} View All Fields set"
    except RuntimeError as e:
        return f"{RED} {e}"


def assign(org, uid, uname, ps_id, ps_label, apply):
    """Idempotent assignment. Returns a status string."""
    if not ps_id:
        return f"{RED} perm set not found"
    try:
        if is_assigned(org, uid, ps_id):
            return f"{GREEN} already assigned"
    except RuntimeError as e:
        return f"{WARN} could not check: {e}"
    if not apply:
        return f"{WARN} WOULD assign (dry-run)"
    try:
        j = sf(["data", "create", "record", "--target-org", org,
                "--sobject", "PermissionSetAssignment",
                "--values", f"AssigneeId={uid} PermissionSetId={ps_id}"])
        if j.get("result", {}).get("success") or j.get("status") == 0:
            return f"{GREEN} assigned"
        return f"{RED} {j.get('message','assign failed')}"
    except RuntimeError as e:
        if "DUPLICATE" in str(e).upper():
            return f"{GREEN} already assigned"
        return f"{RED} {e}"


# ----------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser(description="Provision SRA / Service Assistant permissions.")
    ap.add_argument("--org", required=True, help="sf CLI alias (authenticated)")
    ap.add_argument("--admin-user", required=True,
                    help="human/admin user(s) that will demo — Id, username, or Name; comma-separated")
    ap.add_argument("--planner-user", default=None,
                    help="agent runtime user — Id/username/Name. Default: auto-detect ServicePlannerAgentUser assignee")
    ap.add_argument("--channels", default="all",
                    help="comma list of case|messaging|voice, or 'all' (default all)")
    ap.add_argument("--prefix", default="SRA_", help="name prefix for created custom perm sets (default SRA_)")
    ap.add_argument("--apply", action="store_true", help="actually write (default: dry-run/validate only)")
    ap.add_argument("--api-version", default=API_VERSION)
    args = ap.parse_args()
    org = args.org
    api_version = args.api_version

    channels = ["case", "messaging", "voice"] if args.channels == "all" \
        else [c.strip().lower() for c in args.channels.split(",") if c.strip()]

    mode = "APPLY — WILL WRITE TO ORG" if args.apply else "DRY-RUN — no changes (perm sets validated only)"
    print(f"\n\U0001f527 SRA Permission SETUP — {org}   (channels: {', '.join(channels)})")
    print(f"Mode: {mode}\n")

    # --- resolve identities ---
    admins = resolve_users(org, args.admin_user.split(","))
    if not admins:
        print(f"{RED} No admin/human user resolved. Aborting.")
        sys.exit(1)
    if args.planner_user:
        planners = resolve_users(org, [args.planner_user])
    else:
        planners = auto_planner(org)
    if not planners:
        print(f"{RED} No planner (agent runtime) user resolved. "
              f"Assign ServicePlannerAgentUser first, or pass --planner-user. Aborting.")
        sys.exit(1)

    print("Identities")
    for _, n, u in admins:
        print(f"  Human/admin : {n}  ({u})")
    for _, n, u in planners:
        print(f"  Planner user: {n}  ({u})")

    # --- resolve standard perm set ids ---
    spu_id, _ = permset_id_by_name(org, PS_SERVICE_PLANNER_USER)
    ada_id, _ = permset_id_by_name(org, PS_ACCESS_DEFAULT_AGENT)
    spa_id, _ = permset_id_by_name(org, PS_SERVICE_PLANNER_AGENT)
    dcu_id, _ = permset_id_by_label(org, DATA_CLOUD_USER_LABEL)

    # ============================ BASE (Mandatory) ============================
    print("\nBASE — Mandatory")
    for uid, n, u in admins:
        print(f"  Human [{n}]  Service Planner User ........... "
              f"{assign(org, uid, u, spu_id, PS_SERVICE_PLANNER_USER, args.apply)}")
        print(f"  Human [{n}]  Access Agentforce Default Agent  "
              f"{assign(org, uid, u, ada_id, PS_ACCESS_DEFAULT_AGENT, args.apply)}")
    for uid, n, u in planners:
        print(f"  Planner [{n}]  Service Planner Agent User .... "
              f"{assign(org, uid, u, spa_id, PS_SERVICE_PLANNER_AGENT, args.apply)}")
        print(f"  Planner [{n}]  Data Cloud User (manual) ...... "
              f"{assign(org, uid, u, dcu_id, DATA_CLOUD_USER_LABEL, args.apply)}")

    # ==================== additive custom perm sets per channel ================
    to_deploy = {}          # fullName -> xml
    planner_assign = []     # (fullName, label)
    human_assign = []       # (fullName, label)
    vaf_targets = []        # (fullName, sobject) needing View All Fields patched post-deploy

    if "voice" in channels:
        vname = f"{args.prefix}Agent_Voice_Access"
        to_deploy[vname] = permset_xml(
            vname.replace("_", " "),
            "SRA Voice — planner user: Conversation Entries + View All Voice/Video Calls",
            app_perms=[UP_ACCESS_CE, UP_VIEW_ALL_CALLS])
        planner_assign.append((vname, vname.replace("_", " ")))
        flow = find_eligibility_flow(org, "voice")
        if flow:
            fname = f"{args.prefix}Voice_Eligibility_Flow_Access"
            to_deploy[fname] = permset_xml(
                fname.replace("_", " "),
                "SRA Voice — human: direct access to the Voice Call eligibility flow",
                flows=[flow])
            human_assign.append((fname, fname.replace("_", " ")))
            print(f"\n  {ARROW} Voice eligibility flow detected: {flow}")
        else:
            print(f"\n  {WARN} Voice eligibility flow NOT auto-detected — create/activate it, "
                  f"then grant humans direct access (Run Flows does NOT satisfy this).")

    if "messaging" in channels:
        mname = f"{args.prefix}Agent_Messaging_Access"
        to_deploy[mname] = permset_xml(
            mname.replace("_", " "),
            "SRA Messaging — planner user: Conversation Entries + MessagingSession Read/View All Fields",
            app_perms=[UP_ACCESS_CE],
            obj_perms=[{"object": "MessagingSession", "read": True},
                       {"object": "MessagingEndUser", "read": True}])  # MessagingSession Read depends on it
        planner_assign.append((mname, mname.replace("_", " ")))
        vaf_targets.append((mname, "MessagingSession"))
        flow = find_eligibility_flow(org, "messaging")
        if flow:
            fname = f"{args.prefix}Messaging_Eligibility_Flow_Access"
            to_deploy[fname] = permset_xml(
                fname.replace("_", " "),
                "SRA Messaging — human: direct access to the Messaging eligibility flow",
                flows=[flow])
            human_assign.append((fname, fname.replace("_", " ")))
            print(f"  {ARROW} Messaging eligibility flow detected: {flow}")
        else:
            print(f"  {WARN} Messaging eligibility flow NOT auto-detected — create/activate it, "
                  f"then grant humans direct access.")

    if "case" in channels:
        print("\n  CASE: base Mandatory is sufficient — no additive perm set needed.")

    # ---- deploy (validate-only in dry-run) ----
    deploy_ok = deploy_permsets(org, to_deploy, args.apply, api_version)

    # ---- assign the custom perm sets ----
    if to_deploy:
        print("\nADDITIVE — custom access perm sets")
        if not args.apply:
            for full, label in planner_assign:
                print(f"  Planner  {label} ......... {WARN} WOULD create + assign (validated above)")
            for full, sobj in vaf_targets:
                print(f"  Planner  {sobj} View All Fields ......... {WARN} WOULD set post-deploy")
            for full, label in human_assign:
                print(f"  Human    {label} ......... {WARN} WOULD create + assign (validated above)")
        elif not deploy_ok:
            print(f"  {RED} skipping assignments — perm set deploy failed above.")
        else:
            for full, label in planner_assign:
                ps_id, _ = permset_id_by_name(org, full)
                for uid, n, u in planners:
                    print(f"  Planner [{n}]  {label} ... {assign(org, uid, u, ps_id, label, True)}")
            for full, sobj in vaf_targets:
                ps_id, _ = permset_id_by_name(org, full)
                print(f"  Planner  {sobj} View All Fields ... {set_view_all_fields(org, ps_id, sobj, True)}")
            for full, label in human_assign:
                ps_id, _ = permset_id_by_name(org, full)
                for uid, n, u in admins:
                    print(f"  Human [{n}]  {label} ... {assign(org, uid, u, ps_id, label, True)}")

    # ---- verify ----
    print("\n" + "=" * 60)
    if args.apply and deploy_ok:
        print("Provisioning complete. Verifying with check_perms.py …\n")
        chk = os.path.join(HERE, "check_perms.py")
        admin_id = admins[0][0]
        for ch in channels:
            subprocess.run([sys.executable, chk, "--org", org, "--channel", ch,
                            "--rep-user", admin_id])
    else:
        print("DRY-RUN complete. No changes were made.")
        print("Re-run with --apply to provision. Then it auto-verifies with check_perms.py.")
        print("\nNOTE: permissions are necessary but not sufficient for Voice — after this,")
        print("also confirm a DEFAULT AGENT is set on the Voice tab of Service Assistant Setup")
        print("(mandatory since 262; its absence throws \"We couldn't send your request. Try again.\").")


if __name__ == "__main__":
    main()
