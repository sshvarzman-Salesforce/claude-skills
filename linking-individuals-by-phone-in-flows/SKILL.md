---
name: linking-individuals-by-phone-in-flows
description: "Auto-link the individual behind an inbound (or outbound) conversation to the conversation record, by phone number, inside a Flow — using the OOB findMatchingIndividuals action. Given a phone/ANI on a VoiceCall, MessagingSession, or Case, search Contact / Person Account / Lead, size the match collection, and on exactly one match stamp the host record's lookup (e.g. Contact__c) and RelatedRecordId; on zero or multiple, write an info message + latch a filterable checkbox so a screen/LWC component can react. Covers the findMatchingIndividuals inputs (searchTerm/searchFields/searchObject) and its contactIds text-collection output, the AssignCount operator to size the collection (and the EqualsCount UI-label vs AssignCount metadata-enum gotcha), the 0 / 1 / >1 decision pattern, the single-match Get Records (Id In collection) + lookup/RelatedRecordId linking, and the Long-Text-Area cannot-be-referenced-in-a-formula gotcha that forces a flow-set checkbox. Also covers the screen-flow variant that shows ALL matches in a flowruntime:datatable for the rep to pick one (with the SINGLE_SELECT enum + numeric maxRowSelection=1 selection-mode gotcha and the T→Contact dataTypeMappings requirement). Use whenever a flow must resolve and link a caller/chatter/emailer to a record by their phone number. Trigger on: \"match caller to contact\", \"link individual by phone in a flow\", \"findMatchingIndividuals\", \"screen-pop the caller's contact\", \"populate VoiceCall Contact from phone\", \"count a flow collection size / EqualsCount\", \"which is the metadata operator for Equals Count\", \"datatable single row selection in a screen flow\", \"pick a contact from a datatable to link\"."
compatibility: "Salesforce CLI (sf) v2+; Flow (record-triggered/autolaunched or screen); findMatchingIndividuals invocable action available in the org; VoiceCall/MessagingSession/Case host objects; Contact/Person Account/Lead search objects"
metadata:
  version: "1.2"
  last_updated: "2026-09-22"
---

# Linking Individuals by Phone in Flows

## What this skill is for

When a conversation record is created — a **VoiceCall** (inbound/outbound call), a **MessagingSession** (web/in-app chat), or a **Case** (email/phone) — you usually know the other party's **phone number** but not *who* they are in the CRM. This skill is the reusable Flow pattern that resolves that phone to a **Contact, Person Account, or Lead** and links the individual to the conversation record automatically, so the rep gets a screen-pop with full context instead of an anonymous record.

```
Conversation record created  (VoiceCall / MessagingSession / Case)
  → pick the right phone field  (inbound vs outbound; ANI; SuppliedPhone)
    → findMatchingIndividuals(searchTerm=phone, searchFields="Phone", searchObject="Contact")
      → AssignCount the returned contactIds collection into a Number
        → Decision on the count:
             == 1  → Get the matched record → set host lookup (Contact__c) + RelatedRecordId → Update
             == 0  → write "No matching contact…" info text + latch a checkbox → Update
             >  1  → write "Multiple matches…" info text + latch a checkbox → Update
```

The zero/multiple branches don't guess — they surface an info message and flip a **filterable checkbox** so a downstream LWC or screen component can show the right UI (a manual-search prompt, a disambiguation list, etc.).

The build is done — this skill is the **verified, deployed** pattern from `VoiceCall_Match_Caller` (org `Dreamforce2026OrgSDO`, Active). The complete flow ships as `assets/VoiceCall_Match_Caller.flow-meta.xml`.

---

## THE headline gotcha: `AssignCount`, not `EqualsCount`

You do **not** need a Loop to count matches. Flow has a native assignment operator that sizes a collection into a Number variable in one step. In **Flow Builder the UI label is "Equals Count"** — but the **metadata XML enum is `AssignCount`**. Writing `EqualsCount` in the `.flow-meta.xml` fails deploy:

```
'EqualsCount' is not a valid value for the enum 'FlowAssignmentOperator'
```

Correct assignment (this is the whole "counting" step — no loop, no increment):

```xml
<assignments>
    <name>Count_Matches</name>
    <label>Count Matches</label>
    <assignmentItems>
        <assignToReference>varCount</assignToReference>
        <operator>AssignCount</operator>
        <value>
            <elementReference>Find_Matching_Contacts.contactIds</elementReference>
        </value>
    </assignmentItems>
    <connector><targetReference>Evaluate_Count</targetReference></connector>
</assignments>
```

`varCount` must be `dataType=Number`, `scale=0`. `AssignCount` also works to size any SObject/text/record collection — not just `findMatchingIndividuals` output.

---

## The OOB action: `findMatchingIndividuals`

An out-of-the-box invocable Flow action (the same one the standard MIAW/SCV omni-flows use as "Load Contact by Phone Number"). It runs a SOSL-style match and returns the matched Ids as a **text collection**.

| Parameter | Value | Notes |
|---|---|---|
| `searchTerm` | the phone string (`{!varSearchPhone}`) | what to search for |
| `searchFields` | `"Phone"` | the field(s) on the search object to match against |
| `searchObject` | `"Contact"` (or `"Lead"`, or `"Account"` for Person Accounts) | the object to search |
| `storeOutputAutomatically` | `true` | required to read the output below |

**Output:** `{!Find_Matching_Contacts.contactIds}` — a **Text collection of matched record Ids**. The output property is literally named `contactIds` regardless of `searchObject` (it holds Contact Ids for Contact/Person-Account searches; for a Lead search it returns Lead Ids — verify in your org with a debug run).

```xml
<actionCalls>
    <name>Find_Matching_Contacts</name>
    <label>Find Matching Contacts</label>
    <actionName>findMatchingIndividuals</actionName>
    <actionType>findMatchingIndividuals</actionType>
    <flowTransactionModel>CurrentTransaction</flowTransactionModel>
    <inputParameters>
        <name>searchTerm</name>
        <!-- MUST be a merge-field string template, NOT <elementReference>. See the searchTerm gotcha below. -->
        <value><stringValue>{!varSearchPhone}</stringValue></value>
    </inputParameters>
    <inputParameters>
        <name>searchFields</name>
        <value><stringValue>Phone</stringValue></value>
    </inputParameters>
    <inputParameters>
        <name>searchObject</name>
        <value><stringValue>Contact</stringValue></value>
    </inputParameters>
    <nameSegment>findMatchingIndividuals</nameSegment>
    <storeOutputAutomatically>true</storeOutputAutomatically>
    <connector><targetReference>Count_Matches</targetReference></connector>
</actionCalls>
```

### THE `searchTerm` gotcha: pass it as `{!var}`, not `<elementReference>`

`searchTerm` is a **string** input, and this action only receives the variable's value when you pass it as a **merge-field string template** — `<stringValue>{!varSearchPhone}</stringValue>`. If you author it as a bare `<elementReference>varSearchPhone</elementReference>` (the shape that works for most other actions), the flow **deploys and activates cleanly but silently searches on an empty term** — it finds nothing, `AssignCount` is 0, and every call falls into the zero-match branch. No error, no fault, just "no matches" for every record. This was ground-truthed twice: the record-triggered and screen versions both had to be switched to `{!varSearchPhone}` before `findMatchingIndividuals` returned results.

```xml
<!-- WRONG — deploys fine, matches nothing, always 0 -->
<inputParameters>
    <name>searchTerm</name>
    <value><elementReference>varSearchPhone</elementReference></value>
</inputParameters>

<!-- RIGHT — the value actually reaches the action -->
<inputParameters>
    <name>searchTerm</name>
    <value><stringValue>{!varSearchPhone}</stringValue></value>
</inputParameters>
```

(This applies specifically to `findMatchingIndividuals`' string inputs. `searchFields`/`searchObject` are literal strings anyway. When you build it in Flow Builder the UI does this for you — the bug only bites hand-authored XML.)

> **Fallback:** if the action isn't available or errors in a pure-screen-flow context, a **Get Records on the search object filtered by `Phone = {!varSearchPhone}`** is functionally identical — size that collection with `AssignCount` the same way. Prefer the OOB action (it handles phone normalization/matching heuristics).

---

## Which phone field to search — per host object

The action needs a single phone string. Where you get it depends on the host record and, for calls, the direction.

| Host record | Phone source | Notes |
|---|---|---|
| **VoiceCall** — inbound | `$Record.FromPhoneNumber` | label "Caller Contact Info" = the caller (the person you want to identify) |
| **VoiceCall** — outbound | `$Record.ToPhoneNumber` | label "Recipient Contact Info" = the party you dialed |
| **MessagingSession** | a pre-chat phone param, or `MessagingEndUser.MessagingPlatformKey` | web/in-app chat usually captures phone in pre-chat; see the `routing-inbound-messaging-to-agentforce-agent` skill |
| **Case** | `SuppliedPhone` (Web-to-Case) or `ContactPhone` | email-to-case has no phone; fall back to `SuppliedEmail` + `searchFields="Email"` |

**VoiceCall direction switch** — branch on `CallType` (picklist, exact values `Inbound` / `Outbound`) and assign the correct field to `varSearchPhone` before the search:

```xml
<decisions>
    <name>Which_Phone</name>
    <label>Which Phone (Inbound vs Outbound)</label>
    <defaultConnector><targetReference>Set_Outbound_Phone</targetReference></defaultConnector>
    <defaultConnectorLabel>Outbound (use Recipient / To)</defaultConnectorLabel>
    <rules>
        <name>Inbound</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>$Record.CallType</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue><stringValue>Inbound</stringValue></rightValue>
        </conditions>
        <connector><targetReference>Set_Inbound_Phone</targetReference></connector>
        <label>Inbound</label>
    </rules>
</decisions>
```

---

## The 0 / 1 / >1 decision

Size the collection, then branch. **Exactly one** is the only branch that links; the other two only inform.

```xml
<decisions>
    <name>Evaluate_Count</name>
    <label>Evaluate Match Count</label>
    <defaultConnector><targetReference>Set_No_Match_Text</targetReference></defaultConnector>
    <defaultConnectorLabel>Zero (No Match)</defaultConnectorLabel>
    <rules>
        <name>Multiple_Matches</name>
        <conditions>
            <leftValueReference>varCount</leftValueReference>
            <operator>GreaterThan</operator>
            <rightValue><numberValue>1.0</numberValue></rightValue>
        </conditions>
        <connector><targetReference>Set_Multiple_Text</targetReference></connector>
        <label>Multiple</label>
    </rules>
    <rules>
        <name>Exactly_One</name>
        <conditions>
            <leftValueReference>varCount</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue><numberValue>1.0</numberValue></rightValue>
        </conditions>
        <connector><targetReference>Get_Matched_Contact</targetReference></connector>
        <label>Exactly One</label>
    </rules>
</decisions>
```

> **Watch the default dead-end.** Every branch must connect to something. An unwired Decision outcome is a silent no-op — no fault, no error, the record just isn't updated. (See memory `flow-decision-default-connector-deadend`.) Here the *default* is deliberately the zero-match path.

---

## Single match → link the individual

On exactly one, fetch the record (Id **In** the collection, first-record-only) so you have its Name for display, then assign the host record's lookup **and** `RelatedRecordId`:

```xml
<recordLookups>
    <name>Get_Matched_Contact</name>
    <label>Get Matched Contact</label>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Id</field>
        <operator>In</operator>
        <value><elementReference>Find_Matching_Contacts.contactIds</elementReference></value>
    </filters>
    <getFirstRecordOnly>true</getFirstRecordOnly>
    <object>Contact</object>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <storeOutputAutomatically>true</storeOutputAutomatically>
    <connector><targetReference>Link_Contact</targetReference></connector>
</recordLookups>

<assignments>
    <name>Link_Contact</name>
    <label>Link Matched Contact</label>
    <assignmentItems>
        <assignToReference>$Record.Contact__c</assignToReference>   <!-- host lookup to the individual -->
        <operator>Assign</operator>
        <value><elementReference>Get_Matched_Contact.Id</elementReference></value>
    </assignmentItems>
    <assignmentItems>
        <assignToReference>$Record.RelatedRecordId</assignToReference> <!-- VoiceCall "Related To" -->
        <operator>Assign</operator>
        <value><elementReference>Get_Matched_Contact.Id</elementReference></value>
    </assignmentItems>
    <connector><targetReference>Update_VoiceCall_Contact</targetReference></connector>
</assignments>
```

**Linking field per host object:**

| Host record | Individual link field | Also set |
|---|---|---|
| VoiceCall | custom lookup, e.g. `Contact__c` | `RelatedRecordId` (the standard "Related To") |
| MessagingSession | `EndUserContactId` (Contact) | — |
| Case | `ContactId` (Contact) / `AccountId` (Person Account) | `Lead__c` custom lookup if matching a Lead |

> **Person Accounts / Leads:** search `searchObject="Account"` (Person Account) or `"Lead"`. For a Case→Lead link you need a custom `Lead__c` lookup on Case (standard Case has no Lead lookup). Contact-only stamping uses the standard `ContactId`.

For a **record-triggered flow** the update is just `<recordUpdates><inputReference>$Record</inputReference></recordUpdates>` (you already mutated `$Record`). For a **screen/autolaunched flow** on a passed-in Id, do a Get + Update Records on that Id instead of `$Record`.

---

## Screen-flow variant: let the rep pick from ALL matches (datatable)

The record-triggered flow above only auto-links on **exactly one** match. The companion pattern is a **screen flow** that takes the conversation `recordId`, runs the same `findMatchingIndividuals` search, and — when there are matches — shows **every** matched Contact in a **`flowruntime:datatable`** with single-row selection, so the rep picks the right one and clicks Next to link it. (Zero matches → a "no matches" screen instead.)

Structure: `recordId` (String input) → Get host record → `Which_Phone` decision → set `varSearchPhone` → `findMatchingIndividuals` → `AssignCount` → `Any_Matches` decision (`varCount > 0`): **has matches** → Get **all** matched Contacts (`Id In {!...contactIds}`, **`getFirstRecordOnly=false`**) → datatable screen → assign `firstSelectedRow.Id` to the host lookup + `RelatedRecordId` → Update; **no matches** → info screen.

### The datatable field — the config that actually gives single-row selection

This is the whole gotcha of the screen variant. The `flowruntime:datatable` selection parameters are **not** the strings you'd guess:

```xml
<fields>
    <name>Contact_Table</name>
    <dataTypeMappings>                 <!-- REQUIRED for the generic datatable, else deploy: "missing a type mapping 'T'" -->
        <typeName>T</typeName>
        <typeValue>Contact</typeValue>
    </dataTypeMappings>
    <extensionName>flowruntime:datatable</extensionName>
    <fieldType>ComponentInstance</fieldType>
    <inputParameters>
        <name>selectionMode</name>
        <value><stringValue>SINGLE_SELECT</stringValue></value>   <!-- the enum is SINGLE_SELECT, NOT "SingleSelect" -->
    </inputParameters>
    <inputParameters>
        <name>minRowSelection</name>
        <value><numberValue>0.0</numberValue></value>            <!-- a NUMBER, not the string "required" -->
    </inputParameters>
    <inputParameters>
        <name>maxRowSelection</name>
        <value><numberValue>1.0</numberValue></value>            <!-- THIS enforces single-row selection -->
    </inputParameters>
    <inputParameters>
        <name>tableData</name>
        <value><elementReference>Get_Matched_Contacts</elementReference></value>
    </inputParameters>
    <inputParameters>
        <name>columns</name>
        <value><stringValue>[{"apiName":"Name","label":"Name","type":"text", ... }]</stringValue></value>
    </inputParameters>
    <inputParameters>
        <name>label</name>
        <value><stringValue>Data Table</stringValue></value>
    </inputParameters>
    <inputsOnNextNavToAssocScrn>UseStoredValues</inputsOnNextNavToAssocScrn>
    <isRequired>true</isRequired>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</fields>
```

**Read the selected row** as `{!Contact_Table.firstSelectedRow.Id}` / `{!Contact_Table.firstSelectedRow.Name}` (available because `storeOutputAutomatically=true`). Assign it to the host lookup + `RelatedRecordId` exactly like the auto-link branch, then Update.

> **The selection-mode gotcha (ground-truthed in-org):** hand-authoring `selectionMode = SingleSelect` with `minRowSelection = required` (the plausible-looking string values) is **wrong** — that's not the shape the component reads. The correct, deployed values are `selectionMode = SINGLE_SELECT` (upper-snake enum), `maxRowSelection = 1.0` (**a `numberValue`** — this is what actually caps selection at one row), and `minRowSelection = 0.0` (also a number). When you configure the datatable in Flow Builder the UI writes these for you; the bug only bites hand-authored XML. Get the enum casing and the numeric `maxRowSelection` right or you get multi-select / a silently mis-bound `firstSelectedRow`.

The multi-match Get must set **`getFirstRecordOnly=false`** and query every column the datatable shows (`Name`, `Phone`, `MobilePhone`, `Email`, …) — unlike the single-match auto-link Get, which is `getFirstRecordOnly=true`.

---

## Zero / multiple → info text + a filterable checkbox

The other two branches write a human-readable message to a **Long Text Area** field on the host record and flip a **Checkbox** to `true`:

```xml
<assignments>
    <name>Set_No_Match_Text</name>
    <assignmentItems>
        <assignToReference>$Record.Callers_found_info__c</assignToReference>
        <operator>Assign</operator>
        <value><stringValue>No matching contacts found for that phone number</stringValue></value>
    </assignmentItems>
    <assignmentItems>
        <assignToReference>$Record.Callers_found_info_check__c</assignToReference>
        <operator>Assign</operator>
        <value><booleanValue>true</booleanValue></value>
    </assignmentItems>
    <connector><targetReference>Update_VoiceCall_Info</targetReference></connector>
</assignments>
```

### Why a checkbox and not a formula — the Long-Text gotcha

You cannot use the info Long-Text field itself as a component-visibility filter (Lightning App Builder doesn't allow long-text in visibility rules), and you **cannot** make a formula checkbox derived from it either:

```
You referenced an unsupported field type called 'Long Text Area' using the following field: Callers_found_info__c
```

Salesforce **formulas cannot reference a Long Text Area field at all** — not even `ISBLANK`/`LEN`. So a formula checkbox is impossible; the flow must set a **plain Checkbox** (`type=Checkbox`, `defaultValue=false`). Then an LWC / screen component can filter on that boolean.

> The checkbox **latches true** and stays true. If you want it to reset when a later run finds exactly one match, add a `Callers_found_info_check__c = false` assignment on the single-match branch too. (The reference flow leaves it latched by design.)

### FLS note for VoiceCall custom fields

VoiceCall custom-field FLS is silently ignored (`permissionable=false`) — the field is accessible to all profiles by default, so you don't need to grant FLS for a VoiceCall field (memory `voicecall-custom-fields-not-permissionable`). MessagingSession/Case custom fields **do** need normal FLS.

---

## Variables

```xml
<variables>
    <name>varSearchPhone</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
</variables>
<variables>
    <name>varCount</name>
    <dataType>Number</dataType>
    <isCollection>false</isCollection>
    <scale>0</scale>
    <value><numberValue>0.0</numberValue></value>
</variables>
```

For a screen/autolaunched flow, add a `recordId` (String, `isInput=true`) instead of relying on `$Record`.

---

## Build → deploy → verify

1. Author `flows/<YourFlow>.flow-meta.xml` (start from `assets/VoiceCall_Match_Caller.flow-meta.xml`). Set `<status>Active</status>` so it deploys Active.
2. Ensure the host object has the info Long-Text field + the Checkbox field (and, for MessagingSession/Case, FLS on them). For a custom individual-link lookup (`Contact__c`, `Lead__c`) create + FLS it first.
3. Deploy:
   ```bash
   sf project deploy start --metadata Flow:<YourFlow> --target-org <ORG> --json
   ```
4. Verify Active (this org rejects `FlowDefinitionView`/`FlowVersionView` via Tooling API — query the `Flow` Tooling object instead):
   ```bash
   sf data query --use-tooling-api --target-org <ORG> --json \
     -q "SELECT Status, VersionNumber FROM Flow WHERE Definition.DeveloperName='<YourFlow>' ORDER BY VersionNumber DESC LIMIT 1"
   ```
5. Runtime test: create a VoiceCall with a `FromPhoneNumber` that (a) matches one Contact → `Contact__c` + `RelatedRecordId` stamped; (b) matches none → info text + checkbox true; (c) matches many → "Multiple…" + checkbox true.

> `sf` on this machine: `node "/c/Program Files/sf/client/bin/run.js" <cmd> --json`; filter noise with `grep -v "punycode\|DeprecationWarning\|update available\|npm warn"`; always pass `--target-org <ORG>`.

---

## Adapting to each host / search object — quick recipe

1. **Host = VoiceCall:** branch `CallType` → `FromPhoneNumber`/`ToPhoneNumber`; link `Contact__c` + `RelatedRecordId`.
2. **Host = MessagingSession:** phone from pre-chat param or `MessagingEndUser`; link `EndUserContactId`.
3. **Host = Case:** phone from `SuppliedPhone`/`ContactPhone` (email-to-case → use `SuppliedEmail` + `searchFields="Email"`); link `ContactId`/`AccountId`, or a custom `Lead__c` for a Lead.
4. **Search = Person Account:** `searchObject="Account"`. **Search = Lead:** `searchObject="Lead"` (output holds Lead Ids).
5. Keep the middle the same everywhere: `findMatchingIndividuals` → `AssignCount` → 0/1/>1 Decision → single-match Get + link, zero/multiple info+checkbox.

---

## Common mistakes → fixes

| Mistake | Fix |
|---|---|
| `EqualsCount` in the XML | Use `AssignCount` (that's the metadata enum; "Equals Count" is only the Builder UI label) |
| `searchTerm` passed as `<elementReference>varSearchPhone</elementReference>` | Deploys fine but searches an empty term → always 0 matches. Pass it as `<stringValue>{!varSearchPhone}</stringValue>` |
| Datatable `selectionMode = SingleSelect` + `minRowSelection = required` (strings) | Wrong shape. Use `selectionMode = SINGLE_SELECT` (enum) + `maxRowSelection = 1.0` (numberValue) + `minRowSelection = 0.0` (numberValue) for single-row selection |
| Datatable missing `<dataTypeMappings>T→Contact` | Deploy fails "missing a type mapping 'T'"; the generic `flowruntime:datatable` needs the type mapping on the field |
| Multi-match Get with `getFirstRecordOnly=true` | The datatable shows only one row — set `getFirstRecordOnly=false` and query every column the datatable displays |
| Adding a Loop to count matches | Delete it — `AssignCount` sizes the collection in one assignment |
| Formula checkbox on the Long-Text info field | Impossible — formulas can't reference Long Text Area; set a plain Checkbox in the flow |
| Long-Text field used as a component-visibility filter | Not allowed — filter on the flow-set Checkbox instead |
| Unwired Decision default outcome | Wire every outcome; an unconnected default is a silent no-op (no fault) |
| Only setting `Contact__c`, not `RelatedRecordId` | Set both so the VoiceCall "Related To" also resolves |
| Granting FLS on a VoiceCall custom field and expecting it to matter | VoiceCall custom-field FLS is ignored (`permissionable=false`); accessible to all by default |
| Reading `.contactIds` after forgetting `storeOutputAutomatically=true` | The output is only available when `storeOutputAutomatically=true` |
