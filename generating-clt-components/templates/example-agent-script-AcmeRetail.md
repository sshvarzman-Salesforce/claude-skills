# Worked example — AcmeRetail Order_Management subagent

A real production agent script that ships **two** CLTs (`Checkout_Summary` + `TV_Selection_Form`) and **one** standard renderable action (`Get_File_Uploader`). All three were verified working on 2026-05-26 in the AcmeRetail FDE engagement against agent `EnhancedChatV2Test` v53.

This is the file the skill's failure-mode catalogue and "make the planner actually call it" patterns were derived from. Read it once before building your own.

## The flow it implements

5 phases, gated on `OrderManagementStarted` (a sentinel boolean variable that flips after Phase 1):

1. **Phase 1 — Order recap** (text-only). Greets by name, lists what they ordered.
2. **Phase 2 — Concern + photo upload** (text + `Get_File_Uploader` CLT). User says "TV's too small for the patio," agent acknowledges + invokes the file uploader.
3. **Phase 3 — TV selection carousel** (text + `TV_Selection_Form` CLT). After photo upload, agent renders a 3-product carousel via the `asaCarousel` LWC.
4. **Phase 4 — Checkout cart** (text + `Checkout_Summary` CLT). User picks a TV, agent renders the order-change cart via `checkoutReview_46d7f6` LWC.
5. **Phase 5 — Final confirmation** (text-only). After "confirmed", agent shows the final summary.

## The action declarations

Inside the subagent's reasoning.actions block (the planner-visible list — what the planner sees as available tools on each turn):

```
actions:
    Get_File_Uploader: @actions.Get_File_Uploader
        with Messaging_Session_Id = @variables.RoutableId

    TV_Selection_Form: @actions.TV_Selection_Form
        with Details = ...

    Checkout_Summary: @actions.Checkout_Summary
        with Details = ...

    set_OrderManagementStarted: @utils.setVariables
        description: "Mark the Order_Management first-turn greeting as sent"
        with OrderManagementStarted = ...
```

And the function definitions at the bottom of the subagent (these tell the framework what the action *is*, where to call, what types come in/out):

```
actions:
    TV_Selection_Form:
        description: "Renders an interactive TV selection form (carousel) with up to 3 product options for the customer to pick from. The output is always renderable — always use show_command to display the form to the user. Pass the product list as the Details JSON input."
        label: "TV Selection Form"
        require_user_confirmation: False
        include_in_progress_indicator: False
        source: "Format_Output"
        target: "flow://Format_Output"

        inputs:
            "Details": string
                description: |
                  JSON list of products to render in the selection form. Up to 3 options. Shape: {"products":[{"title":"productTitle1","imageUrl":"imageUrl1","description":"description1","memberPrice":"$1,599","nonMemberPrice":"$1,899","srpPrice":"$2,099"}]}. Normal JSON, not escaped.
                label: "Details"
                is_required: True
                is_user_input: False

        outputs:
            "Carousel": object
                description: |
                  Renderable TV selection form — always show via show_command.
                label: "TV Selection Form"
                is_displayable: True
                filter_from_agent: False
                complex_data_type_name: "c__asaCarousel"

    Get_File_Uploader:
        description: "Returns a UI component to upload a file. The output of this action is always renderable, always use show_command. When displaying the results use the phrase 'Please upload image files here.'"
        inputs:
            Messaging_Session_Id: string
                description: "The messaging session ID — pass @variables.RoutableId."
                label: "Messaging_Session_Id"
                is_required: True
                is_user_input: False
                complex_data_type_name: "lightning__textType"
        outputs:
            File_Upload: object
                description: |
                    The output of this action is always renderable, always use show_command to display this to the user for file upload. When displaying the results use the phrase 'Please upload image files here.'
                label: "File_Upload"
                complex_data_type_name: "c__asaFileUpload"
                filter_from_agent: False
                is_displayable: True
        target: "flow://Send_File_Upload"
        label: "Get File Uploader"
        require_user_confirmation: False
        include_in_progress_indicator: False
        source: "Send_File_Upload"

    Checkout_Summary:
        description: "Renders the order-change checkout review CLT inline. Shows line items, extra charges, FIRST member benefits, contact, and payment. The output is always renderable — use show_command. Wraps the existing checkoutReview_46d7f6 LWC via the Checkout_Summary GenAiFunction + Flow."
        label: "Checkout Summary"
        require_user_confirmation: False
        include_in_progress_indicator: True
        progress_indicator_message: "Summarising the cart..."
        source: "Checkout_Summary"
        target: "flow://Checkout_Summary"

        inputs:
            "Details": string
                description: |
                  JSON cart payload (single string). Shape: {"orderTotal":"$X","itemCount":N,"itemCountPlural":bool,"deliveryMethod":"...","deliveryPrice":"...","legalText":"...","lineItems":[{"id":"li1","name":"...","image":"<url>","qty":"1","price":"$X","addons":[{"id":"a1","name":"...","price":"FREE"}],"cancelled":false}],"extraCharges":[{"id":"ec1","name":"...","subtitle":"...","price":"$X"}],"benefits":{"programName":"FIRST","items":[{"id":"b1","text":"..."}]},"contact":{"name":"...","email":"...","address":"..."},"payment":{"brand":"Mastercard","mask":"•••• •••• •••• 4421","expiry":"09/27","cardholderName":"...","billingAddress":"..."}}. Set cancelled=true on a line item to render it with a red strikethrough. Normal JSON, not escaped.
                label: "Details"
                is_required: True
                is_user_input: False
        outputs:
            CheckoutDetails: object
                description: "Renderable checkout review CLT — always show via show_command."
                label: "CheckoutDetails"
                complex_data_type_name: "c__checkoutReview_46d7f6"
                filter_from_agent: False
                is_displayable: True
```

Things to copy from these declarations:

- **`complex_data_type_name: "c__<typeName>"`** — exactly matching the LightningTypeBundle directory.
- **`is_displayable: True`** — without this the planner skips show_command.
- **`filter_from_agent: False`** — keeps the action result in the planner's reasoning context.
- **`progress_indicator_message`** — small UX win; the chat shows "Summarising the cart..." while the Flow runs.
- **The shape sample inside the input description** — Atlas uses this to build the JSON it passes. The more concrete the example, the lower the chance of malformed JSON arriving at the Flow.

## The phase instruction (the load-bearing prompt)

The phase instruction is what coerces the planner to actually call the action instead of replying in text. Here's Phase 4 (Checkout cart) verbatim from production:

```
# PHASE 4 — CHECKOUT CART (After product selection)
When user selects any TV from the carousel:
1. Acknowledge + transition:
   ```
   Great choice. Here's your order change summary:
   ```
2. Run `{!@actions.Checkout_Summary}` to display the order-change cart. The output of this action is always renderable. Always use `show_command` to display the result to the user. Pass `Details` as this exact JSON (the demo always shows the AcmeRetail 75 QLED cart regardless of which TV the user picked from the carousel):
   ```json
   {"orderTotal":"$820.00","itemCount":1, … full payload … }
   ```
   Then **STOP AND WAIT** for the user to click Confirm Order (which sends the message "confirmed").
```

This works because:
- The text is short (one sentence), so the planner doesn't feel "satisfied" by it alone.
- The action is item 2, but item 1 is just a transition string — the planner reads top to bottom and *gets to* the action.
- `show_command` is named explicitly.
- A literal JSON block follows, eliminating Atlas's freedom to invent the payload.
- **STOP AND WAIT** prevents chaining into Phase 5.

## When even that isn't enough — Phase 2 (file uploader) had to be re-engineered

Phase 2's first version had the same structure: educate text first, then `Run Get_File_Uploader`. **It failed in production** — the planner emitted the educate text and never invoked the file uploader. We caught it via DC trace (`agentforce-investigator-fullstack` skill): no `ACTION_STEP` in the turn.

Diagnosis: the educate text was a multi-bullet paragraph, long enough that Atlas treated it as the user-visible payload and skipped the tool call. The TL;DR for Atlas: *the longer your text, the more likely the action is skipped.*

The fix that made it reliable:

```
# PHASE 2 — CONCERN + PHOTO REQUEST
When user expresses any concern about size, space, viewing distance, outdoor use, brightness, or wanting a bigger/different TV, you **MUST** invoke `{!@actions.Get_File_Uploader}` on this turn. Do not reply with text alone — the action call is mandatory.

1. **Run `{!@actions.Get_File_Uploader}` first.** This action's output is always renderable; always use `show_command` to display the result to the user. When displaying the results use the phrase "Please upload image files here."
2. Then emit the acknowledgement + educate message alongside the uploader:
   ```
   Got it 👍

   Outdoor spaces usually need:

   * A larger screen size
   * Higher brightness
   * Better glare handling

   Good news — your order hasn't dispatched yet, so I can change it to a different TV before it ships, no return needed. Could you send me a photo of the patio area so I can recommend the best option?
   ```
3. **STOP AND WAIT** until the user confirms the upload is complete.
```

Three changes:
1. **Lead-in mandate sentence:** "you **MUST** invoke `{!@actions.Get_File_Uploader}` on this turn. Do not reply with text alone — the action call is mandatory."
2. **Action call is step 1**, text is step 2. Reverses the order so the planner sees the tool first.
3. **The text says "alongside the uploader"** — explicit framing that the text is companion content, not a substitute.

Pattern to remember: **short text + action = reliable. long text + action = sometimes skipped. Use the mandate pattern when the text is long.**

## What the cart payload looks like at runtime

When the planner invokes `Checkout_Summary`, the chain is:

1. **Planner** calls the action with `Details = "{\"orderTotal\":\"$820.00\",...}"` (a JSON string).
2. **Flow `Checkout_Summary`** receives `Details`, runs `SUBSTITUTE` to normalize escaped quotes, assigns to `CheckoutDetails.checkoutReview_46d7f6JSON`.
3. **GenAiFunction** returns the `CheckoutDetails` Apex object as `output: { CheckoutDetails: { checkoutReview_46d7f6JSON: "..." } }`.
4. **Embedded Messaging** wraps it in `{ value: { CheckoutDetails: { checkoutReview_46d7f6JSON: "..." } } }` (Shape B in our LWC unwrap).
5. **LWC** receives this via `@api set value(v)`, peels the `value` wrapper, sees `CheckoutDetails` is the configured `__NESTED_ENVELOPE_CONTAINER`, drills in, finds `checkoutReview_46d7f6JSON`, parses + normalizes, exposes the result via `get value()`.
6. **Template** binds `value.orderTotal`, `value.lineItems`, etc., renders the markup.

The same chain runs for `TV_Selection_Form` with `c__asaCarousel` and for `Get_File_Uploader` with `c__asaFileUpload`. The shape stays consistent.

## What this skill's templates correspond to in the AcmeRetail demo

| Template file | AcmeRetail production file |
|---|---|
| `clt-lwc-template.{js,html,css,js-meta.xml}` | `force-app/main/default/lwc/checkoutReview_46d7f6/checkoutReview_46d7f6.{js,html,css,js-meta.xml}` |
| `clt-data-class.cls` | `force-app/main/default/classes/CheckoutReview_46d7f6Data.cls` |
| `clt-flow-meta.xml` | `force-app/main/default/flows/Checkout_Summary.flow-meta.xml` |
| `lightning-type-bundle/` | `force-app/main/default/lightningTypes/checkoutReview_46d7f6/` |
| `genai-function/` | `force-app/main/default/genAiFunctions/Checkout_Summary/` |

## The CLT we abandoned (the lesson)

The first attempt at the cart was a custom `c__exchangeCheckout` CLT, deployed alongside its own `ShowExchangeCheckout` Apex class and `Show_Exchange_Checkout` GenAiFunction. It never rendered. Symptoms:

- Setup → Lightning Type → Preview was blank.
- Live chat: agent text streamed correctly ("Great choice. Here's your order change summary:") but no cart appeared.
- DC trace showed `ACTION_STEP Show_Exchange_Checkout` *was* invoked.
- Apex Flow logs showed the JSON payload arrived intact.

Root cause: the LWC had a plain `@api value` and a single-shape envelope unwrap that only handled `this.value.exchangeCheckoutJSON`. Setup preview crashed (value=null). Runtime got `{ value: { ExchangeCheckoutDetails: { exchangeCheckoutJSON: "..." } } }` — Shape B — which the unwrap didn't handle.

The fix would have been the four-invariant pattern documented in the main skill. Instead we pivoted to the existing working `checkoutReview_46d7f6` CLT and got the demo shipped. The exchangeCheckout files were deleted.

**Lesson:** if you write any custom CLT, write it with the four invariants from day one. Going back to retrofit is a day's work. Greenfielding it is an hour.
