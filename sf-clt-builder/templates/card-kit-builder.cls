/**
 * Card Kit builder — pairs with templates/lwc-card-kit/ (one renderer for every card).
 * Verified on the SRA panel (Global Payments Frame 9 demo, 13 cards, Oct 2026).
 *
 * Builds the JSON payload the renderer lays out. Every card has one shape: a Lightning
 * header (object icon, label, title, subtitle, "As of" stamp), an optional verdict banner,
 * a summary line, typed blocks, a recommended next step, a talk track and buttons.
 * Formatting happens HERE so the LWC stays a pure renderer.
 *
 * Block types: stats, fields, list, compare, checklist, progress, timeline, summary,
 *              and for layout 'record': path, stages, text, details.
 * States (colour only ever carries state): ok, warn, fault, info.
 * Shape and examples: guides/card-design-system.md. Buttons: guides/next-action-buttons.md.
 *
 * Replace:
 *   {{CardBuilder}} → e.g., AcmeCard
 *   TZ              → the customer's time zone if it differs from the running user's
 *
 * Apex traps already hit with this class:
 *   - List.add(0, x) throws on an EMPTY list (see primaryAction).
 *   - 'hint' is a reserved word: do not use it as a parameter name (stat uses 'caption').
 *   - Names are case-insensitive: a local 'card' and a constant 'CARD' collide.
 */
public without sharing class {{CardBuilder}} {

    public static final String TZ = UserInfo.getTimeZone().getID();

    private Map<String, Object> root = new Map<String, Object>();
    private List<Object> blocks = new List<Object>();
    private List<Object> actions = new List<Object>();

    /** theme is a legacy hint (it only picks a fallback icon); call icon() on every card. */
    public {{CardBuilder}}(String theme, String eyebrow, String title, String subtitle) {
        root.put('theme', theme);
        root.put('eyebrow', eyebrow);
        root.put('title', title);
        root.put('subtitle', subtitle);
        root.put('stamp', 'As of ' + Datetime.now().format('h:mm a', TZ));
    }

    /**
     * SLDS icon in the white card header, e.g. standard:account. Check the name exists in the
     * org's sprite first (guides/card-design-system.md); a wrong name renders an empty square.
     */
    public {{CardBuilder}} icon(String name) {
        root.put('icon', name);
        return this;
    }

    /**
     * Salesforce record layout: the header also shows the record name (opens the record), a
     * status pill and a highlights strip. Use it when the card IS one record (a case, an order).
     */
    public {{CardBuilder}} record(String icon, String objectLabel, String name, Id recordId, String status,
                                  String statusState, List<Object> highlights) {
        root.put('layout', 'record');
        root.put('record', new Map<String, Object>{
            'icon' => icon, 'objectLabel' => objectLabel, 'name' => name,
            'recordId' => recordId,
            'objectApiName' => recordId == null ? null : String.valueOf(recordId.getSobjectType()),
            'url' => recordId == null ? null : '/lightning/r/' + recordId.getSobjectType() + '/' + recordId + '/view',
            'status' => status, 'statusState' => statusState,
            'highlights' => highlights == null ? new List<Object>() : highlights
        });
        return this;
    }

    /** The one-sentence answer at the top of the card, coloured by state. */
    public {{CardBuilder}} verdict(String text, String state) {
        root.put('verdict', new Map<String, Object>{ 'text' => text, 'state' => state });
        return this;
    }

    public {{CardBuilder}} summary(String text) {
        root.put('summary', text);
        return this;
    }

    public {{CardBuilder}} block(String type, String title, List<Object> items) {
        return block(type, title, items, null);
    }

    /** A block with a one-line note under it (e.g. the path block's "In Working for 3 days"). Empty blocks are skipped. */
    public {{CardBuilder}} block(String type, String title, List<Object> items, String note) {
        if (items == null || items.isEmpty()) return this;
        blocks.add(new Map<String, Object>{ 'type' => type, 'title' => title, 'items' => items, 'note' => note });
        return this;
    }

    public {{CardBuilder}} reco(String text) {
        root.put('reco', text);
        return this;
    }

    /** What the rep can say, in the customer's terms. Rendered under "Say to the customer". */
    public {{CardBuilder}} talkTrack(String text) {
        root.put('talkTrack', text);
        return this;
    }

    /** kind = 'execute' sends message to the assistant (runs the next action); 'copy' drops the talk track in the rep's chat box. */
    public {{CardBuilder}} action(String label, String message, String kind) {
        actions.add(new Map<String, Object>{ 'label' => label, 'message' => message, 'kind' => kind });
        return this;
    }

    /**
     * The card's main button, full width above the others. If message contains {tier}, the LWC
     * fills in the value of the tile the rep selected on a compare block (disabled until one is).
     */
    public {{CardBuilder}} primaryAction(String label, String message) {
        Map<String, Object> a = new Map<String, Object>{ 'label' => label, 'message' => message, 'kind' => 'execute', 'primary' => true };
        // Apex List.add(0, x) throws on an empty list.
        if (actions.isEmpty()) actions.add(a);
        else actions.add(0, a);
        return this;
    }

    public String toJson() {
        root.put('blocks', blocks);
        root.put('actions', actions);
        return JSON.serialize(root);
    }

    public static String errorJson(String message) {
        return JSON.serialize(new Map<String, Object>{ 'error' => message });
    }

    /**
     * A button message that makes the planner run exactly one action (guides/next-action-buttons.md).
     * actionLabel = the @InvocableMethod label; what = the record and its Id, e.g.
     * 'the single order 00012 with record Id 801…'.
     */
    public static String runFor(String actionLabel, String what) {
        return 'Run the ' + actionLabel + ' action for ' + what + '. Show only that card; do not list other cards or search knowledge.';
    }

    // ---------- item helpers ----------

    /** A stat tile: label, big value, caption under it. */
    public static Map<String, Object> stat(String label, String value, String caption, String state) {
        return new Map<String, Object>{ 'label' => label, 'value' => value, 'hint' => caption, 'state' => state };
    }

    /** A label / value line. */
    public static Map<String, Object> field(String label, String value, String state) {
        return new Map<String, Object>{ 'label' => label, 'value' => value, 'state' => state };
    }

    public static Map<String, Object> row(String primary, String secondary, String amount, String badge, String state) {
        return new Map<String, Object>{ 'primary' => primary, 'secondary' => secondary, 'amount' => amount,
                                        'badge' => badge, 'state' => state };
    }

    /** A list row with its own button: the button sends message to the assistant (acc:execute). */
    public static Map<String, Object> row(String primary, String secondary, String amount, String badge, String state,
                                          String buttonLabel, String message) {
        Map<String, Object> r = row(primary, secondary, amount, badge, state);
        if (String.isNotBlank(message)) {
            r.put('action', new Map<String, Object>{ 'label' => buttonLabel, 'message' => message });
        }
        return r;
    }

    public static Map<String, Object> check(String label, String note, String state) {
        return new Map<String, Object>{ 'label' => label, 'note' => note, 'state' => state };
    }

    public static Map<String, Object> progress(String label, String value, Integer bar, String state) {
        return new Map<String, Object>{ 'label' => label, 'value' => value,
                                        'bar' => Math.max(0, Math.min(100, bar)), 'state' => state };
    }

    /** A timeline beat. who = 'Assistant' or 'System' styles it as the bot. */
    public static Map<String, Object> event(String timeLabel, String who, String text) {
        return new Map<String, Object>{ 'time' => timeLabel, 'who' => who, 'text' => text };
    }

    /** A Path step: state is complete, current or incomplete. */
    public static Map<String, Object> step(String label, String state) {
        return new Map<String, Object>{ 'label' => label, 'state' => state };
    }

    /** A row on the time-in-status timeline: the status, when it ran, and for how long. */
    public static Map<String, Object> stage(String label, String range, String duration, Boolean current) {
        return new Map<String, Object>{ 'label' => label, 'range' => range, 'duration' => duration, 'current' => current };
    }

    /** A long text field (Description): label above, the text below. */
    public static Map<String, Object> text(String label, String value) {
        return new Map<String, Object>{ 'label' => label, 'value' => value };
    }

    /** A 'summary' block section: a label, then a sentence and/or a bullet list. */
    public static Map<String, Object> note(String label, String value, List<Object> bullets) {
        return new Map<String, Object>{ 'label' => label, 'value' => value, 'bullets' => bullets };
    }

    /** A 'summary' block link that opens a record (a console tab in the Service Console). */
    public static Map<String, Object> recordLink(String label, String linkText, Id recordId, String objectApiName) {
        return new Map<String, Object>{ 'label' => label, 'linkText' => linkText, 'recordId' => recordId,
                                        'objectApiName' => objectApiName,
                                        'href' => '/lightning/r/' + objectApiName + '/' + recordId + '/view' };
    }

    /** A compare tile (display only). highlight = the recommended one. */
    public static Map<String, Object> tier(String name, String price, String detail, String estimate,
                                           String note, Boolean highlight) {
        return new Map<String, Object>{ 'name' => name, 'price' => price, 'detail' => detail,
                                        'estimate' => estimate, 'note' => note, 'highlight' => highlight };
    }

    /** A selectable tile: the rep clicks it, and the card's primary button sends its value in place of {tier}. */
    public static Map<String, Object> tier(String name, String price, String detail, String estimate,
                                           String note, Boolean highlight, String value) {
        Map<String, Object> t = tier(name, price, detail, estimate, note, highlight);
        t.put('value', value);
        t.put('selectable', true);
        return t;
    }

    // ---------- formatting ----------

    public static String money(Decimal amount) {
        if (amount == null) return '$0.00';
        Decimal v = amount.setScale(2, RoundingMode.HALF_UP);
        Boolean negative = v < 0;
        String s = String.valueOf(v.abs());
        String whole = s.substringBefore('.');
        String cents = s.contains('.') ? s.substringAfter('.').rightPad(2, '0') : '00';
        String grouped = '';
        while (whole.length() > 3) {
            grouped = ',' + whole.right(3) + grouped;
            whole = whole.left(whole.length() - 3);
        }
        return (negative ? '-$' : '$') + whole + grouped + '.' + cents;
    }

    public static String day(Date d) {
        if (d == null) return '';
        return Datetime.newInstance(d, Time.newInstance(12, 0, 0, 0)).format('MMM d');
    }

    public static String stamp(Datetime dt) {
        return dt == null ? '' : dt.format('MMM d, h:mm a', TZ);
    }

    public static String clock(Datetime dt) {
        return dt == null ? '' : dt.format('h:mm a', TZ);
    }

    /** Elapsed time, rounded down: "45 min", "1 hour", "19 hours", "1 day", "12 days". */
    public static String duration(Datetime fromDt, Datetime toDt) {
        if (fromDt == null || toDt == null) return '';
        Long minutes = Math.max(0L, (toDt.getTime() - fromDt.getTime()) / 60000L);
        if (minutes < 60) return (minutes < 1 ? 1L : minutes) + ' min';
        Long hours = minutes / 60;
        if (hours < 24) return hours + (hours == 1 ? ' hour' : ' hours');
        Long days = hours / 24;
        return days + (days == 1 ? ' day' : ' days');
    }
}
