/**
 * CLT LWC Template — copy + replace placeholders.
 *
 * Placeholders to replace before deploy:
 *   __TYPE_NAME__              the LWC bundle name, lowercase camelCase (e.g. orderConfirmation)
 *   __APEX_FIELD_NAME__        the Apex class field (convention: <typeName>JSON, e.g. orderConfirmationJSON)
 *   __NESTED_CONTAINER_NAME__  the GenAiFunction output property name (e.g. OrderConfirmationDetails)
 *   BUILDER_FALLBACK_JSON      a realistic sample payload for Setup preview
 *
 * The four invariants this file encodes (DO NOT REMOVE):
 *   1. @api on getter/setter, not plain property — lets us substitute a fallback when value=null.
 *   2. Three-shape envelope unwrap — raw apex / { value: ... } / { <NestedContainer>: ... }.
 *   3. BUILDER_FALLBACK_JSON renders in Setup preview where value is null.
 *   4. connectedCallback re-runs on setter so post-paint value updates re-hydrate the view.
 */
import { LightningElement, api } from 'lwc';

const __APEX_ENVELOPE_FIELD = "__APEX_FIELD_NAME__";
const __NESTED_ENVELOPE_CONTAINER = "__NESTED_CONTAINER_NAME__";

function __buildDefaultViewModel() {
  // Return the shape every binding in the .html template expects.
  // Match this to your real view model. Defaults must be safe for the template
  // (empty strings, [], false) so the component never throws on missing fields.
  return {
    title: '',
    items: []
  };
}

function __readAny(source, keys) {
  if (!source || typeof source !== 'object') return undefined;
  for (let i = 0; i < keys.length; i += 1) {
    if (keys[i] in source) return source[keys[i]];
  }
  return undefined;
}

function __toString(value, fallback) {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  return fallback;
}

function __toObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
}

function __normalizeViewModel(payload) {
  // Coerce every field with a safe default. Customize this function to match
  // your view model — the rest of the file is reusable.
  const safe = __toObject(payload);
  if (!safe) return null;
  const normalized = __buildDefaultViewModel();
  normalized.title = __toString(__readAny(safe, ['title', 'Title']), normalized.title);
  const items = __readAny(safe, ['items', 'Items']);
  normalized.items = Array.isArray(items) ? items : normalized.items;
  return normalized;
}

function __peelValueWrapper(parsed) {
  if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
    const keys = Object.keys(parsed);
    if (keys.length === 1 && keys[0] === 'value' && parsed.value && typeof parsed.value === 'object') {
      return parsed.value;
    }
  }
  return parsed;
}

function __parseEnvelopeField(fieldValue) {
  if (typeof fieldValue !== 'string' || !fieldValue.trim()) return null;
  try { return __normalizeViewModel(__peelValueWrapper(JSON.parse(fieldValue))); }
  catch { return null; }
}

function __unwrapApexEnvelope(raw) {
  if (raw == null) return raw;
  if (typeof raw === 'string') {
    try { return __normalizeViewModel(JSON.parse(raw)); }
    catch { return null; }
  }
  if (typeof raw !== 'object') return null;

  const peeled = __peelValueWrapper(raw);
  const peeledObject = __toObject(peeled);
  if (!peeledObject) return __normalizeViewModel(peeled);

  // Shape A: peeled object IS the Apex envelope ({ <field>JSON: "..." })
  if (__APEX_ENVELOPE_FIELD in peeledObject) {
    return __parseEnvelopeField(peeledObject[__APEX_ENVELOPE_FIELD]);
  }

  // Shape B: peeled object wraps the Apex envelope under the GenAiFunction output name
  const nested = __toObject(peeledObject[__NESTED_ENVELOPE_CONTAINER]);
  if (nested && __APEX_ENVELOPE_FIELD in nested) {
    return __parseEnvelopeField(nested[__APEX_ENVELOPE_FIELD]);
  }

  // Shape C: already a normalized payload
  return __normalizeViewModel(peeledObject);
}

// --- Setup preview fallback ----------------------------------------------------------------
// When the Lightning Type Builder previews this component, value is null.
// Substitute a realistic sample payload so the preview renders correctly.
const BUILDER_FALLBACK_JSON = "{\"title\":\"Sample Title\",\"items\":[{\"id\":\"1\",\"label\":\"Sample item\"}]}";
let __builderFallbackParsed;
function __getBuilderFallback() {
  if (__builderFallbackParsed !== undefined) return __builderFallbackParsed;
  if (BUILDER_FALLBACK_JSON && BUILDER_FALLBACK_JSON !== '__BUILDER_FALLBACK_PAYLOAD__') {
    try { __builderFallbackParsed = __normalizeViewModel(JSON.parse(BUILDER_FALLBACK_JSON)); }
    catch { __builderFallbackParsed = null; }
  } else {
    __builderFallbackParsed = null;
  }
  return __builderFallbackParsed;
}

export default class extends LightningElement {
  _value;

  @api
  get value() { return this._value != null ? this._value : __getBuilderFallback(); }
  set value(v) {
    this._value = __unwrapApexEnvelope(v);
    // Re-run connectedCallback so any @track state hydrated from this.value picks up
    // edits the parent makes after the initial paint. Guard on isConnected so the first
    // synchronous assignment during element setup is a no-op.
    if (this.isConnected && typeof this.connectedCallback === 'function') {
      try { this.connectedCallback(); } catch (err) { console.error('connectedCallback re-hydrate failed', err); }
    }
  }
}
