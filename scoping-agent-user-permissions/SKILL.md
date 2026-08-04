---
name: scoping-agent-user-permissions
description: Build and assign the permission set an Agentforce Service Agent's Einstein Agent User needs. The Einstein Agent User license BLOCKS object Create/Edit on industry/FSC objects (Claim, ClaimParticipant, InsurancePolicy*, etc.), so the correct grant is object Read-only with ViewAll=0 / ModifyAll=0 plus full field-level FLS (readable+editable), while all record writes run in system-context flows.
---

# Scoping Agent-User Permissions (Read-only object + full FLS, no ViewAll/ModifyAll)

## What this skill is for

An Agentforce Service Agent runs its actions as the **Einstein Agent User**. That user needs a permission set granting access to the objects/fields the demo touches. Two hard constraints shape it:

1. **Standing user requirement:** the agent user **must NOT have `ViewAll` or `ModifyAll`** on any object — but it *should* have "view, edit, view and read/write access on all fields." Translation: object perms with `viewAllRecords=false` + `modifyAllRecords=false`, and **full FLS** (`readable=true` + `editable=true`) on every field.
2. **License reality (verified):** the Einstein Agent User license **rejects object Create/Edit** on Claim / ClaimParticipant / ClaimCoverage / ClaimItem / InsurancePolicy* — deploy fails with `FIELD_INTEGRITY_EXCEPTION "user license doesn't allow the permission: Create/Edit ..."`. So you cannot grant object C/E even if you wanted to.

**Resolution:** object access = **Read only** (`allowRead=true`, everything else `false`), full FLS on all fields, and **every write happens in a system-context flow** (see the `building-system-context-agent-data-flows` skill) so the agent user never needs object C/E.

A real, deployed, assigned example ships at `assets/example-agent-user-permset.permissionset-meta.xml` (ClaimSecure's `ClaimSecure_Object_Access_to_ASA`, 9 objects, ~200 FLS entries).

## The exact object-permission block

FLS is license-independent, so `editable=true` is safe on every field even though the object is read-only. Object CRUD is where the license bites — keep it Read-only:

```xml
<objectPermissions>
    <allowCreate>false</allowCreate>
    <allowDelete>false</allowDelete>
    <allowEdit>false</allowEdit>
    <allowRead>true</allowRead>
    <modifyAllRecords>false</modifyAllRecords>
    <object>Claim</object>
    <!-- viewAllRecords omitted → defaults to false. Do NOT add it. -->
</objectPermissions>
```
Repeat for every object the demo reads. In the ClaimSecure example: `Claim`, `ClaimParticipant`, `ClaimCoverage`, `ClaimItem`, `InsurancePolicy`, `InsurancePolicyCoverage`, `InsurancePolicyParticipant`, plus dependency-chain reads `Contact` and `Account`.

## The FLS block (full read+edit on all fields)

```xml
<fieldPermissions>
    <editable>true</editable>
    <field>Claim.ClaimReason</field>
    <readable>true</readable>
</fieldPermissions>
```
One entry per FLS-permissionable field, `editable=true` + `readable=true`.

**Exclude (they are not FLS-permissionable and will fail the deploy):**
- Compound **Address** parent fields and their subfields: `Street`, `City`, `State`, `PostalCode`, `Country`, `Latitude`, `Longitude`, `GeocodeAccuracy` (and `*Address` compound parents).
- System/audit fields: `Id`, `IsDeleted`, `CreatedById`, `CreatedDate`, `LastModifiedById`, `LastModifiedDate`, `SystemModstamp`, `OwnerId`, `Name` on some standard objects.
- **Required** fields and **master-detail** fields (e.g. `ClaimParticipant.Roles`, `ClaimParticipant.ClaimId`) — FLS is set structurally / not permissionable; adding them errors. In the ClaimSecure perm set `ClaimParticipant.Roles` has **no** FLS entry, which is expected.
- Formula / rollup / auto-number fields are read-only — set `editable=false` (or omit) for those; forcing `editable=true` fails.

**How to generate the field list cleanly:** query FieldDefinition and filter, rather than hand-listing:
```bash
sf data query --json -q "SELECT QualifiedApiName, IsCompound, IsCalculated FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName='Claim'"
```
Drop `IsCompound=true`, drop the address subfields, and set `editable=false` where `IsCalculated=true`.

## Deploy & assign

```bash
sf project deploy start --json --metadata PermissionSet:<PermSetName> --target-org <org>
sf org assign permset --name <PermSetName> --target-org <org> --json
```
Confirm the assignment:
```bash
sf data query --json --target-org <org> \
  -q "SELECT Id, PermissionSet.Name, AssigneeId FROM PermissionSetAssignment WHERE PermissionSet.Name='<PermSetName>' AND AssigneeId='<agentUserId>'"
```

## Verify
- Object perms: every object shows `allowRead=true`, `allowCreate/Edit/Delete=false`, `modifyAllRecords=false`, no `viewAllRecords`.
- FLS present on the fields the actions read/return; required/master-detail fields correctly omitted.
- `PermissionSetAssignment` row exists for the Einstein Agent User.
- Because writes are in `SystemModeWithoutSharing` flows, creating a record through the agent works even though the agent user has no object Create.

## Gotchas
- **Don't try to grant object Create/Edit to fix a write failure** — the license forbids it; move the write into a system-context flow instead.
- **`viewAllRecords`/`modifyAllRecords` must stay false** — this is a standing user rule, not just a default.
- **FLS on required/master-detail/compound fields fails the deploy** — omit them; the deploy is all-or-nothing, so one bad field entry blocks the whole perm set.
- **Separate concern from run mode:** the perm set covers user-context surfaces; system-context flows cover record writes. You need both. See `building-system-context-agent-data-flows`.
- **New custom fields:** standing user rule is to add every new field to all page layouts with FLS read+write for all profiles — that's a profile/layout task separate from this agent-user perm set.
