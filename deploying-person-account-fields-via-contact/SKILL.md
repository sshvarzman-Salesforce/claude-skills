---
name: deploying-person-account-fields-via-contact
description: "Add custom fields to Person Accounts correctly by creating them on the CONTACT object — Salesforce auto-materializes each one on the Account object with a __pc-suffixed API name (e.g. Member_Status__c on Contact → Account.Member_Status__pc), queryable via SOQL and the REST/Bulk API and referenceable in Flow. Explains why you must NOT create the field on Account directly for Person Accounts, how to read the mirrored field via SOQL/API, how roll-up summary fields are the one exception that must live on Account, and how — in a Flow starting from a Person Account's Contact record — to traverse Contact→Account (Contact.AccountId self-lookup) to read the __pc / Account-side fields. Covers FLS, page-layout placement on BOTH Contact and Account layouts, and the deploy/verify recipe. Use whenever you must add, deploy, query, or reference a custom field on a Person Account. Trigger on: \"custom field on Person Account\", \"__pc field\", \"field on Contact shows on Account\", \"Person Account SOQL field\", \"read Person Account field in a flow\", \"Contact to Account person account lookup\", \"where do I create a Person Account custom field\"."
compatibility: "Salesforce CLI (sf) v2+; org with Person Accounts enabled; CustomField metadata; Flow; SOQL/REST/Bulk API"
metadata:
  version: "1.0"
  last_updated: "2026-08-12"
---

# Deploying Person Account Fields via Contact

## What this skill is for

Person Accounts are a single logical record stored as **two rows**: an `Account` row and a matched `Contact` (`PersonContactId`) row. This split is the source of the #1 Person Account custom-field mistake: creating a member/person attribute directly on `Account` when it belongs on the *person*.

**The rule:** for a person-level custom field, **create it on `Contact`**. Salesforce automatically mirrors it onto the `Account` object for Person Accounts under a **`__pc`-suffixed API name**. You never author the Account-side field — the platform materializes it, and it's immediately available via SOQL, REST/Bulk API, and Flow.

```
Create custom field on Contact:            Member_Status__c
        │  (Person Accounts enabled)
        ▼  platform auto-mirrors
Account (Person Account) gains:            Member_Status__pc      ← queryable, API-accessible, Flow-referenceable
                                                                    (you did NOT create this — it's automatic)
```

Verified end-to-end on the OMERS pension demo (org `CommericalDemos`): 8 member fields authored on `Contact` all surfaced as `__pc` on `Account`, queried via SOQL and read in system-mode Flows — see the worked example at the bottom.

---

## Why not create the field on Account directly?

- For a **Person Account**, the person attribute logically lives on the Contact side. If you create `Member_Status__c` on `Account`, it exists only as a *business-account* field and does **not** populate for Person Accounts through the Contact/person layer — you end up with two unrelated fields and confusion about which one holds the value.
- Creating it on **Contact** is the single source of truth: business Contacts get `Member_Status__c`, and every Person Account automatically exposes the same value as `Account.Member_Status__pc`. One field authored, both objects served.
- **Exception — roll-up summary fields.** A roll-up summary must live on the **master** object of the master-detail. If child records (e.g. `Pension_Contribution__c`) are detail to `Account`, the roll-up (e.g. `Total_Contributions_To_Date__c`) **must be created on `Account`**, not Contact — Contact can't be the master and can't hold the roll-up. These are the one category that correctly lives on Account.

---

## 1. Create the field on Contact (metadata)

Author it as a normal Contact `CustomField`. Nothing Person-Account-specific in the field XML itself — the mirroring is automatic because Person Accounts are enabled.

`force-app/main/default/objects/Contact/fields/Member_Status__c.field-meta.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Member_Status__c</fullName>
    <label>Member Status</label>
    <type>Picklist</type>
    <valueSet>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value><fullName>Active</fullName><default>false</default><label>Active</label></value>
            <value><fullName>Retired</fullName><default>false</default><label>Retired</label></value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

Deploy:
```bash
sf project deploy start --metadata CustomField:Contact.Member_Status__c --target-org <ORG> --json
```

There is **no** `Account.Member_Status__pc.field-meta.xml` to author or deploy — it appears automatically. Do not try to create it; a hand-authored `__pc` field will conflict/fail.

---

## 2. FLS — grant on the Contact field

Field-Level Security is set on the **Contact** field (the source). The `__pc` mirror inherits accessibility from the Contact field, so you permission `Contact.Member_Status__c` in profiles/permission sets and the Account-side `__pc` follows.

Permission-set entry (`fieldPermissions`) — reference the **Contact** field:
```xml
<fieldPermissions>
    <field>Contact.Member_Status__c</field>
    <editable>true</editable>
    <readable>true</readable>
</fieldPermissions>
```

> Do not add a separate `Account.Member_Status__pc` fieldPermissions entry — it's driven by the Contact field. (Attempting to permission the `__pc` mirror independently is unnecessary and can error.)

---

## 3. Page layouts — place on BOTH Contact and Account layouts

A Person Account is edited from the **Account** UI, but business Contacts use the Contact UI. To have the field visible everywhere:

- Add `Member_Status__c` to the **Contact** page layout(s).
- Add `Member_Status__pc` to the **Account** page layout(s) — this is how it shows on the Person Account record page.

Both are real layout edits. If you only add it to Contact, the value is invisible on the Person Account record page (which renders the Account layout).

---

## 4. Read the mirrored field — SOQL & API

Once deployed, query it two equivalent ways depending on which row you start from:

```sql
-- From the Account (Person Account) row — use the __pc mirror:
SELECT Id, Name, Member_Status__pc, PersonContactId
FROM Account
WHERE Id = '001gL00001b88vRQAQ' AND IsPersonAccount = true

-- From the Contact row — use the base __c field:
SELECT Id, Name, Member_Status__c, AccountId
FROM Contact
WHERE Id = '003gL00000zvHFWQA2'
```

Both return the same value for a Person Account. REST/Bulk API see the `__pc` field on the Account sObject exactly like any other field.

---

## 5. In a Flow: from a Person Account's Contact record, reach the Account side

When a Flow is handed a **Contact Id** for a Person Account (e.g. a caller resolved to their Contact), the Contact's **`AccountId`** is the self-lookup to the Account version of that same Person Account. Two patterns:

**A) Read the base field directly (simplest).** The person fields are on Contact already, so a `Get Records` on Contact returns `Member_Status__c` with no extra hop:
```
Get_Contact:  Contact WHERE Id = {!recordId}   →  {!Get_Contact.Member_Status__c}
```

**B) Traverse Contact → Account to read Account-side / `__pc` or roll-up fields.** Roll-up summaries and any Account-only field live only on the Account row, so you must hop:
```
Get_Contact:   Contact WHERE Id = {!recordId}        (returns AccountId)
Get_Account:   Account  WHERE Id = {!Get_Contact.AccountId}
               →  {!Get_Account.Total_Contributions_To_Date__c}   (roll-up, Account-only)
               →  {!Get_Account.Member_Status__pc}                (mirror, if you prefer the Account side)
```
`Get_Contact.AccountId` **is** the Person Account's Account Id — that's the self-lookup the user asked about. From there every Account/`__pc`/roll-up field is reachable.

> Cross-object shorthand also works in a single Get on Contact for many fields (`{!Get_Contact.Account.Total_Contributions_To_Date__c}`), but the explicit two-Get pattern is clearest and avoids surprises when the flow runs in system mode.

Run person-data reads in **system mode** (`SystemModeWithoutSharing` on the autolaunched flow) when the flow is invoked by an agent/automated user so FLS/sharing don't silently drop fields.

---

## 6. Deploy & verify recipe

```bash
# 1. Deploy the Contact field(s)
sf project deploy start --metadata CustomField:Contact.Member_Status__c --target-org <ORG> --json

# 2. Confirm the __pc mirror exists on Account (Tooling API FieldDefinition)
sf data query --use-tooling-api --target-org <ORG> --json \
  -q "SELECT QualifiedApiName FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName='Account' AND QualifiedApiName='Member_Status__pc'"

# 3. Prove it returns a value for a real Person Account
sf data query --target-org <ORG> --json \
  -q "SELECT Id, Name, Member_Status__pc FROM Account WHERE IsPersonAccount=true AND Id='001gL00001b88vRQAQ'"
```

If step 2 returns the field, the mirror materialized. If step 3 shows the value, SOQL/API access is confirmed.

---

## Worked example — OMERS pension demo (CommericalDemos)

- **8 member fields** (Member Status, membership number, DB pension attributes, SIN last-4, DOB-derived flags, etc.) were authored on **Contact**. Every one auto-appeared on **Account** as `__c` → `__pc` (e.g. `SIN_Last_4__c` → `SIN_Last_4__pc`).
- Lauren Bailey (the demo member): Account `001gL00001b88vRQAQ`, Contact/`PersonContactId` `003gL00000zvHFWQA2`. `SELECT SIN_Last_4__pc FROM Account WHERE Id='001gL00001b88vRQAQ'` and `SELECT SIN_Last_4__c FROM Contact WHERE Id='003gL00000zvHFWQA2'` return the same value.
- **All flows/lookups point at Contact** (`003gL00000zvHFWQA2`), reading the base `__c` fields; where Account-only roll-ups were needed (`Total_Contributions_To_Date__c`, `Total_Employee_Contributions__c`, `Total_Employer_Contributions__c` — master of `Pension_Contribution__c`), the flow hops `Contact.AccountId → Account` to read them.
- Layouts: the 8 `__c` fields sit in an "OMERS Pension" section on the Contact layouts; the 8 `__pc` fields + 3 roll-ups sit in the matching section on the Account layouts.

## Gotchas

| Gotcha | Fix |
|---|---|
| Created the person field on Account directly | Delete it; author on **Contact** — the `__pc` mirror is automatic |
| Tried to author/deploy the `Account.*__pc` field | Don't — it's platform-generated; hand-authoring conflicts |
| Roll-up summary "won't create on Contact" | Correct — roll-ups must live on the **master** (Account); that's the one Account-side exception |
| `__pc` field FLS "not taking" | Permission the **Contact** `__c` field; the mirror inherits |
| Field value invisible on the Person Account record page | Add the `__pc` field to the **Account** page layout (the Person Account UI renders the Account layout) |
| Flow can't see the field for an agent/automated user | Run the data-read flow in **SystemModeWithoutSharing** |
| Need an Account-only/roll-up value starting from a Contact | Hop `Contact.AccountId → Account` (the Person Account self-lookup) |
