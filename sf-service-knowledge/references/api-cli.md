# Service Knowledge — API + CLI Reference

| Feature | API | Metadata Type / Object | CLI |
|---|---|---|---|
| Knowledge Settings (org enablement, translation) | Metadata | `KnowledgeSettings` | `sf project deploy start --metadata KnowledgeSettings` |
| Article Type / Fields | Metadata | `CustomObject:Knowledge__kav` (extend with `CustomField`) | `sf project deploy start --metadata CustomObject:Knowledge__kav` |
| Data Categories | Metadata | `DataCategoryGroup` | `sf project deploy start --metadata DataCategoryGroup` |
| Article Records | REST, Bulk | `Knowledge__kav`, `Knowledge__DataCategorySelection` | `sf data import bulk --sobject Knowledge__kav` |
| Article Feedback (Voting) | REST | `KnowledgeArticleVoteStat` (data-only) | n/a |
| Search / Suggest | REST | Salesforce Knowledge REST — `/services/data/vXX.0/support/knowledgeArticles` | `sf data query -q "FIND {..} IN ALL FIELDS RETURNING KnowledgeArticleVersion(Title)"` |

## Docs

- KnowledgeSettings: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_knowledgesettings.htm
- Knowledge__kav: https://developer.salesforce.com/docs/atlas.en-us.knowledge_dev.meta/knowledge_dev/knowledge_development_intro.htm
- Data Categories: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_datacategorygroup.htm

## Notes

- Knowledge is **Lightning Knowledge** by default — the legacy `KnowledgeArticle` object is not writable in new orgs.
- Article versions: only `Draft`/`Online`/`Archived` versions exist; publishing creates a new version rather than editing in place.
- Deploy `DataCategoryGroup` before any article that references categories — the deploy validates category paths.
