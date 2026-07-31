---
name: case-management-setup
description: "Salesforce Case Management setup and troubleshooting. Helps admins and consultants configure cases, assignment rules, queues, Omni-Channel, Email-to-Case, escalations, entitlements, SLAs, Service Console, and sharing models. Diagnoses common setup issues."
tools: [Read, Bash, Skill]
---

# Case Management Setup & Troubleshooting

> Expert guidance for Salesforce Case Management setup, configuration, and troubleshooting. Covers everything from basic case object setup to complex Omni-Channel routing, entitlements, and SLAs.

**Invocation:** `/case-management-setup [request]`

---

## What This Skill Does

Helps with:
- **Setup guidance** — Configure cases, assignment rules, queues, Email-to-Case, escalations, entitlements
- **Troubleshooting** — Diagnose why assignments aren't working, emails aren't routing, escalations aren't firing
- **Best practices** — Recommend configurations based on org requirements
- **Org diagnostics** — Query setup via `sf` CLI to identify issues

**Example questions:**
- "How do I set up Email-to-Case?"
- "Why aren't my assignment rules working?"
- "Set up Omni-Channel routing for cases"
- "Configure entitlements and SLA milestones"
- "Debug case sharing issues"

---

## When the User Needs Help

If the user hasn't provided enough context, ask:

> What are you trying to set up or troubleshoot?
>
> Examples:
> - "Set up assignment rules to route cases to queues by product"
> - "Email-to-Case isn't creating cases — how do I debug it?"
> - "Configure entitlements with First Response and Resolution milestones"
> - "Why can't users see cases assigned to their queue?"
>
> If you want me to diagnose your org, provide the `sf` CLI alias.

---

## Core Case Management Areas

### 1. Core Case Object Setup

**Setup Path:** Setup > Object Manager > Case

**Record Types:**
- Control page layouts and picklist values per case type
- Link to Support Processes (controls Status picklist)
- Common patterns: B2B/B2C, Tier 1/2/3, Channel-specific (Web/Email/Phone/Chat)

**Page Layouts:**
- Essential sections: Case Information, Account/Contact, Web Information, System Information
- Related lists: Case Comments, Emails, Files, Activities, Case History
- Console layouts: Highlights Panel fields, subtab components, Case Feed vs Email Publisher

**Standard Fields:**
- **Status** — Controlled by Support Process (New, Working, Escalated, Closed)
- **Priority** — Low, Medium, High, Critical
- **Case Origin** — Web, Email, Phone, Chat
- **Type/Reason** — Categorization
- **Case Owner** — User or Queue
- **Parent Case** — For hierarchies

**Custom Fields (common):**
- Product/Service Affected (Lookup or Picklist)
- SLA Violation Flag (Checkbox/Formula)
- Resolution Details (Long Text)
- First Response Date (DateTime)
- Customer Satisfaction Score

---

### 2. Case Assignment Automation

**Setup Path:** Setup > Feature Settings > Service > Case Assignment Rules

**How Assignment Rules Work:**
- Only ONE rule can be active
- Evaluates entries in order (first match wins)
- Assigns to Users or Queues
- Can trigger email alerts + auto-response rules
- Evaluates on case creation OR manual "Assign using active assignment rules" checkbox

**Entry Order Logic:**
```
Priority 1: VIP customers → VIP Queue
Priority 2: Product = "Enterprise Software" → Enterprise Team Queue
Priority 3: Case Origin = "Web" → Web Support Queue
Priority 4: Default → General Support Queue
```

**Common Issues:**
- Entry order wrong (broad criteria before specific)
- "Do not reassign owner" checkbox preventing assignment
- Assignment rule not marked as active
- Queue members not configured
- User's default case owner overriding rule

**Diagnostic Queries:**
```bash
# Check active assignment rule
sf data query --query "SELECT Id, Name, IsActive FROM AssignmentRule WHERE SobjectType = 'Case'" --target-org <alias>

# Check queue membership
sf data query --query "SELECT QueueId, Queue.Name, UserOrGroupId FROM QueueSobject WHERE Queue.Type = 'Queue' AND SobjectType = 'Case'" --target-org <alias>

# Check user's default case owner
sf data query --query "SELECT Id, Name, DefaultCaseOwnerId FROM User WHERE Id = '<userId>'" --target-org <alias>
```

---

### 3. Queues and Omni-Channel

**Setup Path:** Setup > Queues

**Queue Types:**
1. **Basic Queue** — Static assignment, users manually accept cases from queue list view
2. **Omni-Channel Queue** — Skills-based and capacity-based routing

**Basic Queue Setup:**
1. Create queue: Setup > Queues > New
2. Add Supported Objects: Case
3. Add Queue Members: Users, Roles, Public Groups
4. Assign cases via Assignment Rules or manual owner change

**Omni-Channel Setup:**
**Setup Path:** Setup > Feature Settings > Service > Omni-Channel Settings

**Required Steps:**
1. Enable Omni-Channel (Setup > Omni-Channel Settings)
2. Create Service Channels (Setup > Service Channels)
   - Define capacity model (absolute or percentage)
   - Set default capacity per agent
3. Create Routing Configurations (Setup > Routing Configurations)
   - Priority-based: route by priority value
   - Skills-based: match agent skills to case requirements
   - Least active: route to agent with fewest active cases
4. Assign Users to Skills (if skills-based routing)
5. Add Omni-Channel widget to Lightning App (Service Console)

**Skills-Based Routing:**
- Create Skills (Setup > Skills)
- Assign Skills to Users (User record > Skills related list)
- Create Skill Requirements on Routing Configuration
- Cases routed to agents matching required skills

**Capacity Models:**
- **Absolute:** Each work item = fixed capacity units (e.g., Case = 5 units, Chat = 3 units)
- **Percentage:** Each work item = percentage of total capacity (Case = 50%, Chat = 25%)

**Common Issues:**
- Omni-Channel widget not added to Service Console app
- Service Channel not configured for Cases
- Routing Configuration not linked to Queue
- Agent presence status not "Available"
- Capacity maxed out (no available units)

---

### 4. Email-to-Case and Web-to-Case

#### Email-to-Case

**Setup Path:** Setup > Feature Settings > Service > Email-to-Case

**Two Deployment Models:**

**On-Demand Email-to-Case:**
- Email processed by Salesforce servers
- No firewall configuration required
- 2,500 emails/day/org limit
- Setup: Enable On-Demand, configure routing addresses

**Email-to-Case Agent:**
- Installed on your network
- No daily limits
- Processes emails locally, syncs to Salesforce
- Requires: Java, firewall rules, scheduled job

**Configuration Steps:**
1. Enable Email-to-Case
2. Create Routing Addresses (Setup > Email-to-Case > Routing Addresses)
   - Email address to monitor (e.g., support@company.com)
   - Route to Queue or User
   - Save attachments (checkbox)
   - Create case from email body (checkbox)
3. Configure Email-to-Case settings:
   - Automated case user (owner when sender not a contact)
   - Notify case owner on new emails
   - Email threading (match emails to cases by subject/thread ID)

**Email Threading:**
- **Thread ID Method:** Salesforce includes `ref:` token in email subject
- **Email Subject Method:** Match emails with same subject line
- Thread ID more reliable (works even if subject changes)

**Common Issues:**
- Email not creating cases → Check routing address configuration, daily limit
- Case created but no contact → Sender email not in system, automated case user assigned
- Attachments not saving → "Save email attachments as files" unchecked
- Email threading broken → Subject line modified, thread ID removed

**Diagnostic Queries:**
```bash
# Check routing addresses
sf data query --query "SELECT Id, EmailAddress, IsActive, RoutingName FROM EmailRoutingAddress" --target-org <alias>

# Check Email-to-Case settings
sf data query --query "SELECT IsCaseTrackingEnabled, IsOnDemandEmailToCase FROM Organization" --target-org <alias>
```

#### Web-to-Case

**Setup Path:** Setup > Feature Settings > Service > Web-to-Case

**Configuration Steps:**
1. Enable Web-to-Case
2. Generate HTML form (Setup > Web-to-Case > Generate HTML)
3. Customize form fields (pick which Case fields to include)
4. Copy HTML and embed in website
5. Configure Return URL (where to redirect after submission)

**Form Field Options:**
- Standard fields: Company, Contact, Email, Name, Phone, Subject, Description
- Custom fields: Available for selection
- Hidden fields: Pre-populate values (e.g., Case Origin = "Web")

**Security Considerations:**
- Form submissions from external websites
- reCAPTCHA recommended to prevent spam
- Daily limit: 5,000 submissions/org
- Use HTTPS for production websites

**Common Issues:**
- Form not submitting → Check Return URL, CORS settings
- Cases created but missing data → Field mapping incorrect
- Spam cases → Add reCAPTCHA, honeypot fields
- Daily limit reached → Upgrade to Email-to-Case Agent or reduce spam

---

### 5. Escalation Rules and Auto-Response Rules

#### Escalation Rules

**Setup Path:** Setup > Feature Settings > Service > Escalation Rules

**How Escalation Rules Work:**
- Time-based: Escalate if criteria not met within timeframe
- One active rule at a time
- Entries evaluate in order
- Can escalate to user, queue, or manager
- Can trigger workflow actions (email alerts, field updates)

**Configuration:**
1. Create Escalation Rule
2. Add Rule Entries:
   - Criteria (e.g., Priority = "High")
   - Age Over (e.g., 2 hours)
   - Business Hours (optional — only count business hours)
   - Escalation Actions (reassign, notify)

**Common Escalation Actions:**
- Reassign case to escalation queue
- Send email alert to manager
- Update Priority field
- Create task for VP of Support

**Business Hours:**
- Define business hours (Setup > Business Hours)
- Link to escalation rule entries
- Only counts time during business hours (e.g., escalate after 4 business hours, not 4 calendar hours)

**Common Issues:**
- Escalation not firing → Check if rule is active, criteria matches, business hours configured
- Escalating too early → Business hours not set (counts 24/7)
- Email alerts not sending → Email template not accessible, recipient email invalid
- Case already escalated → "Do not reassign owner" or manual escalation already occurred

#### Auto-Response Rules

**Setup Path:** Setup > Feature Settings > Service > Auto-Response Rules

**How Auto-Response Rules Work:**
- Send automatic email when case created
- One active rule at a time
- Entries evaluate in order (first match wins)
- Uses Email Templates

**Configuration:**
1. Create Email Templates (Setup > Email Templates)
2. Create Auto-Response Rule
3. Add Rule Entries:
   - Criteria (e.g., Case Origin = "Web")
   - Email template to send
   - Sender email address

**Common Issues:**
- Auto-response not sending → Check rule is active, criteria matches, email template exists
- Wrong template sent → Entry order incorrect
- Email deliverability → Sender email not verified, recipient email bounced

---

### 6. Case Teams and Case Sharing

#### Case Teams

**Setup Path:** Setup > Feature Settings > Service > Case Teams

**What Are Case Teams:**
- Pre-defined roles on cases (Engineer, Manager, Billing Specialist)
- Each role has access level (Read, Read/Write)
- Can add users to case team from Case detail page

**Configuration:**
1. Define Case Team Roles (Setup > Case Teams > Case Team Roles)
   - Role name (e.g., "Technical Engineer")
   - Access level (Read or Read/Write)
2. Create Predefined Case Teams (Setup > Case Teams > Predefined Case Teams)
   - Add multiple roles
   - Assign default users to each role
3. Add Case Team related list to page layout

**Use Cases:**
- Cross-functional support (sales, engineering, billing all on one case)
- Escalation paths (add manager role when escalated)
- Customer-facing roles (account manager stays on all cases for account)

#### Case Sharing

**Sharing Models:**
1. **Organization-Wide Default (OWD):** Private, Public Read Only, Public Read/Write
2. **Role Hierarchy:** Users can see records owned by users below them
3. **Sharing Rules:** Criteria-based or Owner-based
4. **Manual Sharing:** Case owner can share case with user/group
5. **Apex Managed Sharing:** Programmatic sharing via Apex

**Setup Path:** Setup > Security > Sharing Settings

**Common Sharing Scenarios:**

**Scenario 1: Private OWD, Share with Account Team**
- OWD = Private
- Sharing Rule: Share cases where Account Owner = [User] with Account Owner (Read/Write)
- Result: Account owners see all cases for their accounts

**Scenario 2: Private OWD, Queue Members See All Queue Cases**
- OWD = Private
- Queue membership grants access to cases in that queue
- When case assigned to user, only that user + role hierarchy see it

**Common Issues:**
- Users can't see queue cases → Not a queue member
- Users can't see cases owned by peers → OWD = Private, no sharing rule
- Manager can't see team's cases → Role hierarchy not set up
- Case sharing too broad → OWD = Public Read/Write (change to Private)

**Diagnostic Queries:**
```bash
# Check OWD
sf data query --query "SELECT DefaultCaseAccess FROM Organization" --target-org <alias>

# Check sharing rules
sf data query --query "SELECT Id, Name, AccessLevel FROM CaseSharingRule" --target-org <alias>

# Check case team roles
sf data query --query "SELECT Id, Name, AccessLevel FROM CaseTeamRole" --target-org <alias>
```

---

### 7. Entitlements, Milestones, and SLAs

**Setup Path:** Setup > Feature Settings > Service > Entitlements

**Entitlement Process:**
- Defines SLA milestones for cases
- Links to Entitlements (per account or per asset)
- Controls milestone types (First Response, Resolution)

**Configuration Steps:**
1. Create Entitlement Process (Setup > Entitlement Processes)
   - Add Milestone Types
   - Define success criteria (e.g., First Response = Status changed from New)
   - Define violation criteria (e.g., Age > 2 hours)
   - Set business hours
2. Create Entitlements (per Account)
   - Link to Entitlement Process
   - Set start/end dates
   - Define case limits (if applicable)
3. Link Case to Entitlement (automatic or manual)

**Milestone Types:**
- **First Response:** Time until first rep response
- **Resolution:** Time until case closed
- **Custom:** Any time-based requirement

**Milestone Actions:**
- **Success Actions:** Send email, update field, create task
- **Violation Actions:** Send escalation email, update priority, create case

**Business Hours:**
- Critical for accurate SLA tracking
- Define working hours (e.g., 9 AM - 5 PM, Mon-Fri)
- Link to entitlement process
- Milestones only count during business hours

**Common SLA Configurations:**

**Priority-Based SLA:**
- High Priority: First Response 1 hour, Resolution 4 hours
- Medium Priority: First Response 4 hours, Resolution 24 hours
- Low Priority: First Response 24 hours, Resolution 72 hours

**Tier-Based SLA:**
- Enterprise Tier: First Response 30 mins, Resolution 2 hours
- Professional Tier: First Response 2 hours, Resolution 8 hours
- Standard Tier: First Response 8 hours, Resolution 48 hours

**Common Issues:**
- Milestone not starting → Case not linked to entitlement, entitlement inactive
- Milestone violation not firing → Business hours not configured, violation criteria wrong
- Milestone completed but actions not firing → Success actions not configured
- First Response not completing → Status change not meeting success criteria

**Diagnostic Queries:**
```bash
# Check entitlements
sf data query --query "SELECT Id, Name, StartDate, EndDate, Status FROM Entitlement WHERE Status = 'Active'" --target-org <alias>

# Check case milestones
sf data query --query "SELECT Id, CaseId, MilestoneType.Name, CompletionDate, IsViolated FROM CaseMilestone WHERE CaseId = '<caseId>'" --target-org <alias>
```

---

### 8. Lightning Service Console Setup

**Setup Path:** Setup > App Manager

**Service Console vs Standard App:**
- **Console:** Multi-tab interface, workspace tabs, utility bar, productivity tools
- **Standard:** Single-object focus, traditional navigation

**Console Components:**

**1. Workspace Tabs:**
- Primary tabs (Cases, Accounts, Contacts)
- Subtabs (related records open in subtabs, not new tabs)

**2. Utility Bar:**
- Bottom toolbar with persistent tools
- Common utilities: Omni-Channel, Notes, History, Macros

**3. Split View:**
- Show related list details without leaving case
- Configure in App Builder (Case Record Page)

**4. Keyboard Shortcuts:**
- Open new tab, close tab, switch tabs, search
- Enable in Setup > Console Settings

**5. Macros:**
- Automate repetitive tasks (update status, send email, create task)
- Record actions in macro builder
- Run with one click

**6. Quick Text:**
- Pre-defined text snippets
- Insert into emails, case comments, chat
- Support merge fields (e.g., {!Case.CaseNumber})

**Configuration Steps:**
1. Create Lightning App (Setup > App Manager > New Lightning App)
2. Choose "Console Navigation"
3. Add Standard/Custom Tabs
4. Add Utility Items (Omni-Channel, Notes, etc.)
5. Configure Navigation Items (Cases, Accounts, Contacts)
6. Assign to Profiles

**Console Best Practices:**
- Add Case Feed component to case page (App Builder)
- Enable keyboard shortcuts
- Configure workspace rules (auto-open subtabs for related records)
- Add Lightning components (Path, Knowledge, Recommendations)

---

### 9. Case Feed vs Email Publisher

**Case Feed:**
- Chatter-style feed on case
- Posts, comments, @mentions
- Better for internal collaboration
- Shows case updates chronologically

**Email Publisher:**
- Traditional email interface
- Send/receive emails directly on case
- Better for external communication
- Uses Email Templates

**Feature Comparison:**

| Feature | Case Feed | Email Publisher |
|---------|-----------|-----------------|
| **Email Sending** | Via Email action on feed | Direct email compose |
| **Email Threading** | Shows emails in feed | Traditional email list |
| **Internal Notes** | Feed posts (private or public) | Case Comments |
| **@Mentions** | Yes | No |
| **File Attachments** | Inline in feed | Separate attachment section |
| **Rich Text** | Yes | Yes |
| **Email Templates** | Yes | Yes |

**When to Use Case Feed:**
- Internal collaboration heavy
- Want timeline view of case activity
- Use @mentions for team communication

**When to Use Email Publisher:**
- Email-heavy support process
- Traditional email workflow preferred
- Reps comfortable with email interface

**Migration Considerations:**
- Can't easily switch between Feed and Publisher
- Page layouts differ (Feed vs Classic)
- Training required for reps when switching

---

### 10. Common Validation Rules and Automation Patterns

#### Validation Rules

**Pattern 1: Require Resolution Details When Closing**
```
AND(
  ISPICKVAL(Status, "Closed"),
  ISBLANK(Resolution_Details__c)
)
```
Error Message: "Resolution Details required when closing case"

**Pattern 2: Contact Required for Cases from Customers**
```
AND(
  ISPICKVAL(Case_Type__c, "Customer"),
  ISBLANK(ContactId)
)
```
Error Message: "Contact required for customer cases"

**Pattern 3: Priority Justification for High/Critical**
```
AND(
  OR(
    ISPICKVAL(Priority, "High"),
    ISPICKVAL(Priority, "Critical")
  ),
  ISBLANK(Priority_Justification__c)
)
```
Error Message: "Justification required for High/Critical priority"

#### Flow/Workflow Patterns

**Pattern 1: First Response Tracking**
- Trigger: Case Status changed from "New" to anything else
- Action: Set First_Response_Date__c = NOW()

**Pattern 2: Auto-Close Old Cases**
- Scheduled Flow: Daily at 2 AM
- Criteria: Status = "Pending Customer" AND Last Modified Date > 30 days ago
- Action: Set Status = "Closed - Auto"

**Pattern 3: Escalation Notification**
- Trigger: Priority changed to "Critical"
- Action: Send email to VP of Support, create task for case owner

---

### 11. Reports and Dashboards

#### Essential Case Reports

**1. Case Aging Report**
- Report Type: Cases
- Filters: Status != "Closed"
- Group by: Priority
- Columns: Case Number, Age (Days), Owner, Subject
- Chart: Bar chart of age by priority

**2. SLA Compliance Report**
- Report Type: Cases with Case Milestones
- Filters: Milestone Type = "First Response", Date Range = This Month
- Group by: Milestone Violated (Yes/No)
- Summary: Count of cases, % violated
- Chart: Donut chart of compliance

**3. Case Resolution Time Report**
- Report Type: Cases
- Filters: Status = "Closed", Closed Date = This Month
- Formula Field: Resolution_Time__c = Closed Date - Created Date (in hours)
- Group by: Priority
- Summary: Average Resolution Time
- Chart: Line chart of avg resolution time over time

**4. Cases by Origin**
- Report Type: Cases
- Filters: Date Range = This Quarter
- Group by: Case Origin
- Summary: Count of cases
- Chart: Pie chart of cases by origin

#### Dashboard Components

**Manager Dashboard:**
- Open Cases by Queue (table)
- SLA Compliance (gauge)
- Cases Closed This Month (metric)
- Escalated Cases (table)
- Case Aging by Priority (bar chart)

**Agent Dashboard:**
- My Open Cases (table)
- My Cases Due Today (table)
- My SLA Compliance (gauge)
- My Avg Resolution Time (metric)

**Executive Dashboard:**
- Total Cases by Status (pie chart)
- Case Volume Trend (line chart)
- SLA Compliance by Product (table)
- Customer Satisfaction Score (gauge)

---

### 12. Troubleshooting Common Issues

#### Assignment Rules Not Working

**Symptoms:**
- Cases stay with default owner
- Cases don't route to expected queue

**Diagnostic Steps:**
1. Check if assignment rule is active:
   ```bash
   sf data query --query "SELECT Id, Name, IsActive FROM AssignmentRule WHERE SobjectType = 'Case'" --target-org <alias>
   ```
2. Check entry order — most specific first
3. Check "Do not reassign owner" checkbox on case
4. Check if user's default case owner is overriding
5. Test assignment rule with sample criteria

**Common Fixes:**
- Activate assignment rule
- Reorder entries (specific before general)
- Uncheck "Do not reassign owner"
- Clear user's default case owner

#### Email-to-Case Not Creating Cases

**Symptoms:**
- Emails sent to routing address don't create cases

**Diagnostic Steps:**
1. Check if Email-to-Case enabled
2. Check routing address active and configured
3. Check daily limit (2,500/day for On-Demand)
4. Check sender email matches contact in system
5. Check email delivery logs

**Common Fixes:**
- Enable Email-to-Case
- Activate routing address
- Wait for daily limit reset (midnight UTC)
- Add sender as contact or configure automated case user
- Check spam filters (emails may be blocked)

#### Escalation Rules Not Firing

**Symptoms:**
- Cases not escalating when expected

**Diagnostic Steps:**
1. Check if escalation rule is active
2. Check case meets entry criteria
3. Check age calculation (business hours vs calendar hours)
4. Check if case already escalated (won't re-escalate)
5. Check escalation actions configured

**Common Fixes:**
- Activate escalation rule
- Verify criteria matches case
- Configure business hours if needed
- Check "Do not reassign owner" checkbox
- Add escalation actions (email, reassign)

#### Entitlement Milestones Not Starting

**Symptoms:**
- Case created but no milestones

**Diagnostic Steps:**
1. Check if case linked to active entitlement
2. Check entitlement has active entitlement process
3. Check milestone types configured in process
4. Check business hours configured
5. Check case meets entitlement criteria

**Common Fixes:**
- Link case to entitlement (automatic or manual)
- Activate entitlement
- Configure milestone types in process
- Define business hours
- Update case to meet entitlement criteria

#### Case Sharing Issues

**Symptoms:**
- Users can't see cases they should access

**Diagnostic Steps:**
1. Check Organization-Wide Default (OWD) for Cases
2. Check user's role hierarchy
3. Check sharing rules
4. Check queue membership (for queue cases)
5. Check case team membership

**Common Fixes:**
- Change OWD to Public Read Only (if too restrictive)
- Add user to role hierarchy
- Create sharing rule (criteria or owner-based)
- Add user to queue as member
- Add user to case team

---

## Quick Reference: Setup Paths

| Feature | Setup Path |
|---------|-----------|
| Case Object Settings | Setup > Object Manager > Case |
| Record Types | Setup > Object Manager > Case > Record Types |
| Page Layouts | Setup > Object Manager > Case > Page Layouts |
| Assignment Rules | Setup > Feature Settings > Service > Case Assignment Rules |
| Queues | Setup > Queues |
| Omni-Channel Settings | Setup > Feature Settings > Service > Omni-Channel Settings |
| Service Channels | Setup > Service Channels |
| Routing Configurations | Setup > Routing Configurations |
| Email-to-Case | Setup > Feature Settings > Service > Email-to-Case |
| Web-to-Case | Setup > Feature Settings > Service > Web-to-Case |
| Escalation Rules | Setup > Feature Settings > Service > Escalation Rules |
| Auto-Response Rules | Setup > Feature Settings > Service > Auto-Response Rules |
| Case Teams | Setup > Feature Settings > Service > Case Teams |
| Sharing Settings | Setup > Security > Sharing Settings |
| Entitlement Processes | Setup > Entitlement Processes |
| Entitlements | Entitlements object (standard object) |
| Business Hours | Setup > Business Hours |
| Service Console App | Setup > App Manager |
| Email Templates | Setup > Email Templates |
| Macros | Setup > Macros |
| Quick Text | Setup > Quick Text |

---

## Response Pattern

When the user asks for setup help:
1. **Understand the requirement** — What are they trying to achieve?
2. **Recommend approach** — Best practice configuration for their scenario
3. **Provide step-by-step setup** — Exact Setup paths and configuration
4. **Call out gotchas** — Common mistakes and how to avoid them
5. **Offer diagnostic queries** — `sf` CLI commands to validate setup

When troubleshooting:
1. **Understand the symptom** — What's not working?
2. **Run diagnostics** — Query org to see current setup (if org alias provided)
3. **Identify root cause** — Compare expected vs actual configuration
4. **Provide fix** — Clear steps to resolve
5. **Verify fix** — Query again to confirm resolution

---

## Example Interactions

**User:** "Set up assignment rules to route cases by product to different queues"

**Response:**
1. Create Queues (Setup > Queues):
   - Product A Queue
   - Product B Queue
   - General Queue (fallback)
2. Add Queue Members (users who handle each product)
3. Create Assignment Rule (Setup > Case Assignment Rules)
   - Entry 1: Product = "Product A" → Assign to Product A Queue
   - Entry 2: Product = "Product B" → Assign to Product B Queue
   - Entry 3: Default → Assign to General Queue
4. Activate the rule
5. Test with sample cases

Common gotcha: Entry order matters — specific criteria before general.

---

**User:** "Email-to-Case isn't creating cases — how do I debug?"

**Response:**
Let me check your org setup (provide sf CLI alias if you want me to run diagnostics).

Manual checks:
1. Setup > Email-to-Case > Is it enabled?
2. Setup > Email-to-Case > Routing Addresses > Is your address active?
3. Check daily limit (2,500/day for On-Demand) — Setup > System Overview
4. Test email: Send from a contact's email address (not generic email)
5. Check Setup > Email Logs for delivery failures

If I have your org alias, I'll run:
```bash
sf data query --query "SELECT Id, EmailAddress, IsActive, RoutingName FROM EmailRoutingAddress" --target-org <alias>
```

Common fixes:
- Activate routing address
- Wait for daily limit reset (midnight UTC)
- Add sender as contact or configure automated case user

---

## When to Use Other Skills

- **For SRA-specific setup** → Use `sra-setup-debug` skill (checks SRA permissions, agent user, channels, knowledge)
- **For general Salesforce CLI queries** → Use Bash tool directly
- **For custom code/Apex** → This skill provides formulas and patterns, but doesn't write custom Apex

---

## Changelog

| Date | Change |
|------|--------|
| 2026-07-20 | Initial skill creation — comprehensive case management setup and troubleshooting |
