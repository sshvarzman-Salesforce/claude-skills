---
name: handling-locked-standard-objects
description: Detect and work around standard industry/FSC objects (e.g. Claim, KeyPrefix 0Zk) that ACCEPT CustomField metadata deploys and Tooling API creates with success:true, report EntityDefinition.IsCustomizable=true, but NEVER materialize the physical column at runtime — the field is invisible to SOQL, REST describe, and Apex getGlobalDescribe. Confirm the trap with getGlobalDescribe, then use a standard long-text field with structured delimited lines as the workaround.
---

# Handling Locked Standard Objects (custom fields that never materialize)

## The trap

Some standard **industry / Financial Services Cloud** objects — confirmed on the standard **`Claim`** object (KeyPrefix `0Zk`) in the CommericalDemos org — are **structurally locked**: you can create custom fields on them through every normal channel and get **success every time**, but the column never physically exists.

- A `CustomField` metadata deploy returns `success: true`.
- A Tooling API `POST` to `/sobjects/CustomField` returns `created: true`.
- `EntityDefinition.IsCustomizable` reports `true`.
- …and yet the field is **invisible to SOQL** (`No such column`), to REST describe, and to Apex `Schema.getGlobalDescribe().get('Claim').getDescribe().fields.getMap()` — a field "created" seconds earlier returns `false` from `.containsKey(...)`.

This is **structural** (a locked managed/standard object), **not** a propagation delay or cache staleness. Waiting does not fix it. The "created" field records are orphaned metadata no-ops — harmless, but never queryable.

## Detect it before you design around it

Don't trust the deploy's `success:true`. **Prove the column exists at runtime with Apex `getGlobalDescribe`** — this is the authoritative check:

```apex
// run via: sf apex run --file check.apex --target-org <org>
Map<String, Schema.SObjectField> f =
    Schema.getGlobalDescribe().get('Claim').getDescribe().fields.getMap();
System.debug('HAS FIELD: ' + f.containsKey('provider_name__c'));  // false on a locked object
```
If this prints `false` for a field you just deployed successfully, the object is locked. A SOQL smoke test on the field (`SELECT Provider_Name__c FROM Claim LIMIT 1`) failing with `No such column` corroborates it.

## The workaround: structured lines in a standard long-text field

Since you can't add columns, **pack the structured data into an existing standard long-text field** (`Claim.Summary`, 32,000 chars) as delimited `Key: Value` lines, and parse them back out in the prompt template / flow:

```
Provider: Bright Smile Dental
Service Date: 2026-07-12
Referral Required: No
Referral On File: No
Details: Dental claim for a crown replacement. Currently under review.
```

- **Write side** (system-context create flow): build the block with a formula using `BR()` between lines (see `building-system-context-agent-data-flows`), assign to `Summary`.
- **Read side** (flex prompt template): instruct the model to parse `Provider:` / `Service Date:` / `Referral Required:` / `Referral On File:` / `Details:` out of the `Summary` text into whatever sections the customer sees. The template does the parsing — no custom fields required.
- Use only **standard createable/queryable fields** otherwise: on `Claim` those are `Name`, `AccountId`, `ClaimType`, `Status`, `ClaimReason`, `EstimatedAmount`, `Summary`, `PolicyNumberId` (all confirmed queryable at runtime).

## When you hit a new object
1. Deploy/create the field as normal.
2. **Immediately run the `getGlobalDescribe` Apex check.** If `true`, you're fine — use the field. If `false`, the object is locked.
3. If locked: leave the orphaned field record (harmless), switch to the long-text-with-structured-lines design, and note it so nobody re-litigates it.

## Gotchas
- **`success:true` is a lie here.** Deploy/Tooling success does not mean the column exists. Always confirm with `getGlobalDescribe`.
- **`IsCustomizable=true` is also misleading** on these objects — it does not guarantee runtime materialization.
- **Not fixable by retry/wait/cache-clear** — it's structural. Don't burn time re-deploying.
- **Relationships to these objects still work** — e.g. `ClaimParticipant` (a separate object) links Contact→Claim normally; only *custom fields on the locked object itself* fail. Model the extra data as a long-text block or on a related object you *can* customize.
