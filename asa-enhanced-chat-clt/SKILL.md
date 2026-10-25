---
name: asa-enhanced-chat-clt
description: Build and wire Custom Lightning Type (CLT) cards for a CUSTOMER-FACING Agentforce Service Agent (ASA, Agent Script .agent) on the Enhanced Chat v2 channel. TRIGGER when the user builds, fixes or reviews cards for an ASA / customer chat / Enhanced Chat / "ASA for Chat" agent, asks which CLT channel to use, or edits a CLT's UI Configuration channel. Covers: the CLT channel is Enhanced Chat v2 (enhancedWebChat/ folder), NOT the messaging channel; the exact bundle layout; how the Agent Script YAML binds a CLT output; display flags; variable bindings; verification. DO NOT TRIGGER for rep-facing Service Rep Assistant (ServicePlanner) cards, use sf-clt-builder and its Card Kit for those.
---

# CLT cards for a customer-facing ASA on Enhanced Chat v2

Learned 2026-10-25 on org `BWAMIDOOctober2026`, agent `Demo_ASA_With_CLT_for_Messaging` (Coastline Bank), after the user corrected the earlier guidance in `sf-clt-builder`.

## The rule that was wrong before

**The CLT channel for a customer-facing ASA is "Enhanced Chat v2". It is not the messaging channel.**

- The *session* may arrive over Messaging (MessagingSession, `@MessagingSession.*` linked variables), but the *CLT UI Configuration channel* is a separate setting and must be **Enhanced Chat v2**.
- In Setup: **Setup > Lightning Types > the type > UI Configuration tab > Channel dropdown = "Enhanced Chat v2"**, then the **Editor** and **Renderer** sub-tabs (Override Option "Editor Override", Input Component "Standard" is the default editor).
- In metadata that channel is the folder **`enhancedWebChat/`**. The platform's own deploy error lists every allowed artifact in a Lightning Type bundle (captured by dry-run, 2026-10-25):

```
editor.json
renderer.json
lightningDesktopGenAi/editor.json    lightningDesktopGenAi/renderer.json     (Lightning Experience / Service Console panel, SRA)
lightningMobileGenAi/editor.json     lightningMobileGenAi/renderer.json      (mobile)
enhancedWebChat/editor.json          enhancedWebChat/renderer.json           (Enhanced Chat v2, customer-facing)
experienceBuilder/editor.json                                                  (Experience Builder, editor only)
```

Any other folder name (`enhancedChatV2/`, `experience/`) fails with "The artifact renderer.json isn't allowed in this bundle". Use `sf project deploy start --dry-run` to test a layout without changing the org.

An ASA type that has only `lightningDesktopGenAi/` silently falls back from Enhanced Chat v2 to the desktop config. Do not rely on that for an ASA: configure the Enhanced Chat v2 channel explicitly.

## CLT bundle for an ASA type

```
lightningTypes/<typeName>/
  <typeName>.lightningType-meta.xml        # real XML, masterLabel required
  schema.json                              # title, description (<=255 chars, with show_command sentence), "lightning:type": "@apexClassType/c__<DtoClass>"
  enhancedWebChat/renderer.json            # {"renderer":{"componentOverrides":{"$":{"definition":"c/<lwc>"}}}}
```

- Keep ASA (customer) types separate from SRA (rep) types. Customer cards must not carry rep-only fields. Example in this org: ASA `coastlineCardOutput` (LWC `coastlineCard`) vs SRA `coastlineSra*Output` types (LWC `csraCard`, `lightningDesktopGenAi/`).
- If one type must serve both, keep both folders and strip internal fields from the payload.
- The DTO is one `@AuraEnabled global String cardJSON` field (the Setup preview shows "Input Object > cardJSON"). The Apex action returns the DTO inside its Response.
- LWC target is `lightning__AgentforceOutput`; in Enhanced Chat v2 the write-back API is `this.configuration?.util.sendTextMessage(...)` (see `sf-clt-builder` guides/surfaces.md). Do not use `copytochat`/`acc:execute` (SRA only).

**Verify the channel actually saved.** A change made in the Setup UI only exists once saved; retrieve the bundle and look for `enhancedWebChat/renderer.json`:

```bash
sf project retrieve start -m LightningTypeBundle:<typeName> -o <org>     # sourceApiVersion 66.0 or 68.0 both return channel folders
```

(On 2026-10-25 the retrieved `coastlineCardOutput` still had only `lightningDesktopGenAi/`; the user's Enhanced Chat v2 selection had not been saved yet.)

## Agent Script (`.agent`) wiring for a card action

Retrieve the live agent with API 66 (`AiAuthoringBundle` type):

```bash
sf project retrieve start -m AiAuthoringBundle:<AgentDevName> -o <org>     # sourceApiVersion 66.0
```

File sections, in order: `system` (instructions, welcome/error messages), `config` (agent_label, agent_template `SvcCopilotTmpl__AgentforceServiceAgent`, developer_name), `access.default_agent_user`, `variables`, `language`, `knowledge`, `start_agent <router>`, then one `subagent <name>:` per topic with `reasoning.instructions: ->`, `reasoning.actions`, and an `actions:` definition block.

**Variables.** `linked string` variables are bound to records the platform supplies: `@MessagingSession.Id` (RoutableId), `@MessagingSession.EndUserAccountId`, `@MessagingEndUser.ContactId`, `@MessagingSession.ChannelType`, and for voice `@VoiceCall.Id`, `@VoiceCall.Contact__c`, `@VoiceCall.RelatedRecordId`. `mutable string` variables are the agent's own state. Give the router one place that normalises both channels into `Final*` variables, then pass only those to every action:

```yaml
start_agent agent_router:
    reasoning:
        instructions: ->
            if @variables.VoiceCallId is not None:
                set @variables.FinalSessionID = @variables.VoiceCallId
                set @variables.FinalChannel = "voice"
                set @variables.FinalAccountID = @variables.RelatedRecordId
            if @variables.RoutableId is not None:
                set @variables.FinalSessionID = @variables.RoutableId
                set @variables.FinalChannel = "messaging"
                set @variables.FinalAccountID = @variables.EndUserAccountId
```

Rules from the project memory still apply: no nested `if`; test linked vars with `is not None`, not `!= ""`.

**Action definition for a card (Apex).**

```yaml
actions:
    get_recent_transactions:
        description: "... The output of this action is always renderable, always use show_command."
        label: "Get Recent Transactions"
        target: "apex://CoastlineGetRecentTransactionsAction"
        inputs:
            sessionId: string
                is_required: True
                is_user_input: False            # bound from FinalSessionID, never asked
            lastFour: string
                is_required: True
                is_user_input: True             # the only thing the customer supplies
        outputs:
            card: object
                complex_data_type_name: "c__coastlineCardOutput"   # c__ + the Lightning Type FOLDER name
                is_displayable: True
                filter_from_agent: True          # planner must not narrate the card JSON
            success: boolean
                is_displayable: False
                filter_from_agent: False
            status: string                       # ok / Not verified / Not found ...
                filter_from_agent: False
            plannerSummary: string               # one line of real numbers the planner may read
                filter_from_agent: False
            shownCount: object
                complex_data_type_name: "lightning__integerType"   # integers must be declared as object + lightning__integerType
```

And in the subagent's `reasoning.actions`, bind the inputs: `with sessionId = @variables.FinalSessionID`, `with accountId = @variables.FinalAccountID`, `with lastFour = ...` (the `...` means the model fills it from the conversation), and `available when @variables.isVerified == True` to gate by state. Capture output into state with `set @variables.recentActivity = @outputs.plannerSummary`.

Other targets seen in the same agent: `flow://<FlowApiName>` (OTP, lock/unlock, order), `generatePromptResponse://<Template>` (inputs are `Input:<name>`).

**Three places carry the show-the-card language** (a missing one lowers the render rate): the action `description` ("always use show_command"), the output `description` ("Do NOT convert to text"), and the LT `schema.json` description. Add the subagent instruction "when an action returns a card it is shown as it is; never rewrite its rows as text".

**Keep one planner-visible output** (`status`, `plannerSummary`, `success` with `filter_from_agent: False`) or the planner apologises even when the card rendered.

## Go-live checklist

1. LT bundle has `enhancedWebChat/renderer.json` (retrieve to confirm it saved). Smoke-test the Apex action itself first (anonymous Apex), then the card in the live chat; first render can need a second try.
2. The LWC is deployed, `isExposed=true`, target `lightning__AgentforceOutput`.
3. The agent user's **profile** has Apex class access for the action classes (a permission set alone was not enough in ECv2 field tests); see `sf-clt-builder` "ECv2 go-live gate".
4. The Embedded Service Deployment is hosted on the Experience Cloud site and **republished after any agent or CLT change**.
5. Customer-safe payload: no rep-only fields on an ASA type.

## Related

`sf-clt-builder` (generator, Card Kit for SRA), `agentforce-lightning-types` (ECv2 runtime/debug), `calling-prompt-templates-in-flows`. Project memory: Coastline demo notes (agent actions as system-mode flows/Apex, Agent Script gotchas).
