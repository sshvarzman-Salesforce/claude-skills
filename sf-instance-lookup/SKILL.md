# Salesforce Instance Lookup

Look up which Salesforce instance/pod an org is running on, given an org ID (15 or 18-char).

**Invocation:** `/sf-instance-lookup <orgId or alias>`

---

## Resolution Methods (in priority order)

### Method 1: GUS Account_Org__c (most reliable for any org)

Query the `Account_Org__c` object in GUS (org62) — it maps org IDs to instances:

```bash
sf data query --query "SELECT Name, Org_Status__c, Production_Instance__r.Name FROM Account_Org__c WHERE Name = '<orgId>'" --target-org gus --json
```

If direct match fails, use the **prefix-based lookup** — characters 3-4 of the org ID encode the instance pod:

```bash
sf data query --query "SELECT Name, Org_Status__c, Production_Instance__r.Name FROM Account_Org__c WHERE Name LIKE '00D<prefix>%' LIMIT 5" --target-org gus --json
```

The prefix is characters at position 3-4 (0-indexed) of the 15-char org ID, right after `00D`.

### Method 2: Salesforce Trust Status API (public, no auth — but only indexes production/active orgs)

```bash
curl -s "https://api.status.salesforce.com/v1/search/<orgId>"
```

Returns JSON array with `instanceKey` if the org is indexed:
```json
[{"alias": "00DHr000002gCSN", "instanceKey": "NA235", "aliasType": "orgId"}]
```

**Limitation:** Returns empty `[]` for SDOs, trials, sandboxes, scratch orgs, and demo orgs.

### Important: SDO/Demo/Trial Orgs

SDO orgs are **NOT in GUS** (`Account_Org__c` only tracks production and managed orgs). For SDO/demo/trial orgs:
- GUS exact match → will fail
- GUS LIKE prefix → returns production orgs on that prefix, which MAY share the same instance but is NOT guaranteed (especially for ambiguous prefixes)
- Status API → returns empty
- **Only reliable method:** Black Tab (`blacktab.sfdc.net`) or logging into the org and checking Setup → Company Information → Instance

### Method 3: sf CLI (authenticated orgs only)

```bash
sf org display --target-org <alias> --json
```

Returns `result.instanceUrl` (My Domain) and `result.id` (org ID). Then query the org itself:

```bash
sf data query --query "SELECT InstanceName FROM Organization" --target-org <alias>
```

---

## Prefix → Instance Decoding

The 2-character code at positions 3-4 of the 15-char org ID identifies the pod/instance pool. Orgs with the same prefix are on the same instance.

### Known Prefix Mappings

⚠️ **PREFIX LOOKUP IS A STARTING POINT, NOT A FINAL ANSWER.** Prefix-based inference is unreliable for SDO/demo/trial orgs — they frequently land on different instances than production orgs with the same prefix. **Always verify via Black Tab** for SDO/demo/trial orgs.

#### Verified Mappings (hand-confirmed via Black Tab)

| Prefix | Verified Instance | Org Type | Notes |
|--------|-------------------|----------|-------|
| `aj` | USA838 | SDO | ✓ confirmed |
| `DJ` | CS243 | Demo | ✓ confirmed |
| `fj` | USA1044 | SDO | ✓ confirmed |
| `gK` | CAN96 | SDO | ✓ confirmed |
| `Hn` | NA231 | Trial | ✓ confirmed |
| `Hr` | NA235 | Trial | ✓ confirmed |
| `Kc` | NA246 | Trial | ✓ confirmed |
| `70` | USA348 | Production | ✓ confirmed |

#### Ambiguous / Unreliable Prefixes (multiple instances observed)

| Prefix | Observed Instances | Notes |
|--------|-------------------|-------|
| `Hu` | NA238 (×2 verified), NA233 (verified) | Same prefix → different instances depending on org. ALWAYS verify. |
| `Hp` | NA233 (verified), USA1154S (GUS prod) | SDO instance ≠ production instance |
| `Ws` | USA794 (verified), GBR116 (GUS prod) | SDO instance ≠ production instance |
| `bm` | USA876 (verified), AUS18S (GUS prod) | SDO instance ≠ production instance |
| `J6` | EU50 (verified), GBR54, DEU38, SWE100 | EMEA pool — always verify |
| `Wt` | USA796 (×2 verified), GBR116, GBR118 (GUS prod) | SDO instance ≠ production instance |

#### Other Known Prefixes (from GUS prod orgs — use as hint only, verify for SDOs)

| Prefix | GUS Instance | Region/Type |
|--------|----------|-------------|
| `ak` | USA840 | NA |
| `g7` | USA1140 | NA |
| `gL` | CAN98 | Canada |
| `Ho` | NA232 | NA - Hyperforce |
| `NS` | IND56 | APAC - India |

### Verification Required

⚠️ **For SDO/demo/trial orgs, prefix lookup is unreliable.** Even "known" prefixes like `Hu` land on different instances depending on when/where the org was provisioned.

**Always do this:**
1. Try Status API first: `curl -s "https://api.status.salesforce.com/v1/search/<orgId>"` (works for production orgs only)
2. If empty (SDO/demo/trial orgs won't be there), **tell the user to verify via Black Tab**
3. Do NOT rely on GUS for SDO/demo/trial orgs — they aren't in `Account_Org__c`
4. Present the prefix-based result as a **best guess** with a clear "⚠️ verify" flag
5. NEVER present an unverified SDO lookup as confirmed

### How to Discover New Prefixes

If you encounter an unknown prefix, query GUS:

```bash
sf data query --query "SELECT Name, Production_Instance__r.Name, Org_Status__c FROM Account_Org__c WHERE Name LIKE '00D<XX>%' LIMIT 5" --target-org gus
```

If the query returns **multiple distinct instances** for the same prefix, add it to the Ambiguous Prefixes table above.

---

## Instance Naming Conventions

| Pattern | Meaning | Example |
|---------|---------|---------|
| `NAxx` | North America (classic) | NA135, NA232, NA235 |
| `USAxxx` | US Hyperforce | USA348, USA838, USA1044 |
| `USAxxxxS` | US Hyperforce Sandbox | USA1154S, USA1200S |
| `CSxx` | Classic Sandbox | CS42, CS243 |
| `CANxx` | Canada | CAN96, CAN98 |
| `GBRxxx` | UK/Great Britain | GBR116 |
| `AUSxxS` | Australia Sandbox | AUS18S |
| `INDxx` | India | IND56 |
| `EUxx` | Europe | EU46, EU62 |
| `APxx` | Asia Pacific | AP28, AP44 |

The `S` suffix = sandbox instance.

---

## Steps (When Given a List of Org IDs)

1. **Extract the prefix** (chars 3-4 after `00D`) from each org ID
2. **Check known mappings** (table above)
3. **Check ambiguous prefix list** — if the prefix is ambiguous, DO NOT return a single instance. Flag it.
4. **For unknowns**, query GUS with LIKE pattern. If results show multiple instances for the same prefix, add to the ambiguous table.
5. **Verify with status API** for production orgs: `curl -s "https://api.status.salesforce.com/v1/search/<orgId>"`
6. **Group by instance** — orgs on the same instance share maintenance windows

### ⚠️ When to Tell the User to Manually Confirm

Flag for manual verification in these cases:

| Scenario | What to tell the user |
|----------|----------------------|
| **Prefix is in the ambiguous table** | "Prefix `XX` maps to multiple instances (list them). Check Black Tab or org login to confirm." |
| **GUS LIKE returns multiple distinct instances** | "This prefix is shared across instances: [list]. I can't determine which one without a direct match." |
| **SDO/demo/trial org** | "SDO orgs aren't in GUS or Status API. Check Black Tab or Setup → Company Information → Instance." |
| **Status API returns empty AND prefix is unambiguous** | Prefix-based result is likely correct — but note it's inferred, not confirmed. |
| **Unknown prefix entirely** | "Unknown prefix `XX` — not in my mapping table. Check Black Tab." |

**Black Tab** = Salesforce internal tool at `blacktab.sfdc.net` — search by org ID to see the authoritative instance, status, and version.

---

## Output Format

```
Org ID               Instance     Version   Type                 
══════════════════════════════════════════════════════════════════
00Daj00000txyrk      USA838       264.0     SDO pool             
00DDJ000000Qtbt      CS243        264.0     Demo                 
00D70000000JcM2      USA348       262.0     Production           
```

Include:
- **Org ID**: As provided
- **Instance**: The pod name
- **Version**: The Salesforce release version (e.g. 262.0, 264.0)
- **Type**: Production, Trial, Demo, SDO, Sandbox (from `Org_Status__c`)
- **Status URL**: `https://status.salesforce.com/instances/<INSTANCE>`

### Getting the Version

| Method | Works for | How |
|--------|-----------|-----|
| **Status API** | Production orgs | `curl -s "https://api.status.salesforce.com/v1/instances/<INSTANCE>/status"` → `releaseVersion` |
| **Black Tab** | All orgs | Shows "Version Number" column |
| **Org login** | Authenticated orgs | Setup → Company Information → "Current Salesforce Version" |
| **sf CLI** | Authenticated orgs | `sf org display --target-org <alias> --json` → `result.apiVersion` (approximate — maps to release) |

If version can't be determined programmatically, note "unknown" and tell the user to check Black Tab.

---

## Example

```
/sf-instance-lookup 00DHu00000ytg7D
```

→ Prefix `Hu` → Instance **USA1200S** (NA SDO/Demo sandbox pool)
→ Status: https://status.salesforce.com/instances/USA1200S
