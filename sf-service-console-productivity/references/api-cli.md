# Service Console Productivity — API + CLI Reference

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Macros | Metadata, REST | `Macro`, `MacroInstruction` | `sf project deploy start --metadata Macro` |
| Quick Text | Metadata, REST | `QuickText` | `sf project deploy start --metadata QuickText` |
| Console App | Metadata | `CustomApplication` (with `<uiType>Lightning</uiType>` + `<navType>Console</navType>`) | `sf project deploy start --metadata CustomApplication` |
| Page Layout | Metadata | `Layout` | `sf project deploy start --metadata Layout` |
| Lightning Page (record page) | Metadata | `FlexiPage` | `sf project deploy start --metadata FlexiPage` |
| Utility Bar / Custom Console Components | Metadata | `CustomApplication` (`<utilityBar>`), `LightningComponentBundle` | `sf project deploy start --metadata CustomApplication` |

## Docs

- Macro: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_macro.htm
- QuickText: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_quicktext.htm
- FlexiPage: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flexipage.htm

## Notes

- Macros with irreversible actions ("send email and close case") require **explicit user opt-in** — do not enable by default in profile assignments.
- `QuickText` supports merge fields; validate that referenced fields exist on target orgs before deploy.
- The utility bar is a `CustomApplication` sub-element, not its own metadata type. To version utility-bar content, deploy the parent app.
