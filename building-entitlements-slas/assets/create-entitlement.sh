#!/usr/bin/env bash
# Create the Entitlement record that links an Account to a deployed SLA process.
# Run AFTER the EntitlementProcess is deployed + Active. Resolves all Ids per-org
# (entitlement metadata is portable, but the Entitlement *record* needs live Ids).
#
# Usage: edit the three vars, then run per org.
set -euo pipefail

ALIAS="${1:-CommericalDemos}"        # target org alias
PROCESS_NAME="Gold Banking customer" # SlaProcess.Name (deployed EntitlementProcess name)
ACCOUNT_NAME="Lauren Bailey"         # account to entitle
ENTITLEMENT_NAME="Gold banking customer entitlement"
START_DATE="2026-07-28"              # coverage start (YYYY-MM-DD)

SF() { "/c/Program Files/sf/client/bin/node.exe" --no-deprecation "/c/Program Files/sf/client/bin/run.js" "$@"; }

pick() { node -e "let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>{const j=JSON.parse(s);const r=(j.result.records||[])[0];process.stdout.write(r?r.$1:'');})"; }

# a) runtime process Id  -- query SlaProcess (NOT EntitlementProcess); no VersionNumber column
SLA_ID=$(SF data query -q "SELECT Id, Name, IsActive FROM SlaProcess WHERE Name='$PROCESS_NAME'" --target-org "$ALIAS" --json | pick Id)
# b) default business hours
BH_ID=$(SF data query -q "SELECT Id FROM BusinessHours WHERE IsDefault=true AND IsActive=true LIMIT 1" --target-org "$ALIAS" --json | pick Id)
# c) account
ACCT_ID=$(SF data query -q "SELECT Id FROM Account WHERE Name='$ACCOUNT_NAME' LIMIT 1" --target-org "$ALIAS" --json | pick Id)

echo "ALIAS=$ALIAS  SlaProcess=$SLA_ID  BusinessHours=$BH_ID  Account=$ACCT_ID"
[ -z "$SLA_ID" ] && { echo "ERROR: SlaProcess '$PROCESS_NAME' not found/active in $ALIAS"; exit 1; }

SF data create record --sobject Entitlement \
  --values "Name='$ENTITLEMENT_NAME' AccountId=$ACCT_ID SlaProcessId=$SLA_ID BusinessHoursId=$BH_ID StartDate=$START_DATE" \
  --target-org "$ALIAS" --json

# verify
SF data query -q "SELECT Id, Name, Account.Name, SlaProcess.Name, BusinessHours.Name, StartDate FROM Entitlement WHERE Name='$ENTITLEMENT_NAME'" --target-org "$ALIAS" --json
