// Grant the Embedded Messaging guest user access to the Apex data class
// behind your CLT. Run as anonymous Apex (sf apex run -f grant-guest-perms.apex)
// when chat shows blank cards but the Builder preview works fine.
//
// Replace before running:
//   __APEX_CLASS_NAME__       Apex data class (e.g. OrderConfirmationData)
//   __GUEST_USER_QUERY__      query that resolves the guest user — see below
//
// Typical guest user query:
//   SELECT Id FROM User WHERE UserType = 'Guest' AND Username LIKE '%embedded-messaging%' LIMIT 1
//
// This is idempotent — re-running won't create duplicate SetupEntityAccess rows.

ApexClass cls = [SELECT Id FROM ApexClass WHERE Name = '__APEX_CLASS_NAME__' LIMIT 1];
User guest = [SELECT Id, ProfileId FROM User WHERE __GUEST_USER_QUERY__];

// Find the guest user's ProfilePermissionSet (every profile has one)
PermissionSet pps = [
    SELECT Id FROM PermissionSet
    WHERE ProfileId = :guest.ProfileId AND IsOwnedByProfile = true
    LIMIT 1
];

// Check if the SetupEntityAccess row already exists
List<SetupEntityAccess> existing = [
    SELECT Id FROM SetupEntityAccess
    WHERE ParentId = :pps.Id AND SetupEntityId = :cls.Id
    LIMIT 1
];

if (existing.isEmpty()) {
    SetupEntityAccess sea = new SetupEntityAccess(
        ParentId = pps.Id,
        SetupEntityId = cls.Id
    );
    insert sea;
    System.debug('Granted guest access to ' + cls.Name);
} else {
    System.debug('Guest already has access to ' + cls.Name);
}
