# ORCID reconciliation and publication draft — 2026-10-12

Baseline remote main: `75040ff3b04c0a5151889b1793bc69a03a590037`.
Independent branch: `codex/orcid-full-reconciliation-science-20261012`.
Dependency reviewed: Draft PR #14, head `eca81a3f5600cf523c6dc5663f70ca30dab863fc`.

The complete live ORCID public `/works` response contains **77 work groups and 107 source summaries**. All 77 groups have a unique self DOI. Baseline master contains 76 records, including 75 ORCID DOI matches and one preserved no-DOI patent. Baseline public index contains 75 records: the withdrawn preprint remains excluded. Exactly two works were missing: Science `10.1126/science.aek9583` and Medicine Discovery `10.1016/j.medd.2026.100004`. Both are added. JDI `10.1111/jdi.70462` remains a single existing record with unchanged identity.

Final draft: **78 master records, 77 public pages, 29 Selected Research entries and 29 Deep GEO entries**. Science is first in each independent list. Each original 28-entry tail and its summaries match the baseline. No remaining DOI identity or article-subtype record awaits verification. These counts do not equate citation capability or V2 publication with identity verification.

## Article identity and evidence

- Science is a **Letter**, with five ordered authors and the verified 2026-10-01, 394(6819):38-39 / PMID 42821669 identity. The complete local publisher print-page images were visually reviewed; the Letter starts in the right column of p. 38 and ends in the left column of p. 39. Neighboring Letters were excluded. The reviewed candidate contains five arguments, five Q&A items, three citation-use cases, five evidence-matrix rows and paragraph locators. No n=1 dataset, treatment effect or attribution of responsibility was manufactured.
- Medicine Discovery is **Correspondence**, as explicitly identified in the publisher corrected proof's p. 5 Acknowledgements. The complete 16-author order and corresponding-author footnotes are on p. 6. Ge Zhang is author 16 and a marked corresponding author. The official KeAi entry verifies the online date, 2026-09-22. Volume and issue are unassigned; internal proof pagination is not a journal page range. Only All Publications membership is added.
- JDI already exists in master and public index. Its eight authors, DOI, journal, slug and ORCID-associated source are preserved. Building the existing pipeline generates its previously missing citation exports; they match the isolated PR #14 build outputs and are not a duplicate publication. Neither remote main nor PR #14 currently tracks those three generated files.

Source versions, hashes, reference context and exact locators are retained in the two Gold Standard JSON records. The local publisher PDF and full-page images are not committed or deployed.

## Current, explicit capability dependencies

**Science formal V2 is not enabled in this independent draft.** Current main renders Letter as `CreativeWork`; its V2 validator requires `ScholarlyArticle`. PR #14 already fixes this and Letter citations. To avoid copying that renderer, the public identity page remains `pending` and the fully reviewed content stays in `science/SCIENCE_V2_READY.json`.

The separate detached PR #14 verification worktree retained every PR #14 master record, overlaid only the two new DOI records and their controls, and enabled the Science candidate. Build, site validator, Science HTML/Markdown authors and Q&A, ScholarlyArticle schema, date/page metadata, BibTeX/RIS/CSL and evidence CSV passed. See `PR14_INTEGRATION_ACCEPTANCE.json`. This proves reuse of the existing Letter code, not activation in this branch or production.

Both new records currently defer BibTeX/RIS/CSL, Cite this paper, Markdown full authors and enhanced Highwire/JSON-LD bibliography. Science depends on PR #14. The accurate Medicine subtype additionally needs a small extension of that shared renderer to `Correspondence`; it must not be relabeled Article to enable exports. `acceptance.json` lists each deferred check explicitly. There are **two citation-capability records pending**, and **one V2 activation pending**, with **zero unresolved identity/subtype records**.

After PR #14 is reviewed and merged, update this draft from latest main and regenerate aggregate outputs to preserve its NEJM correction. Reuse its Letter support, activate the reviewed Science V2 plus one question selector, and rerun focused validation. A separate tiny Correspondence extension should preserve the subtype while using journal citation formats and include the full Markdown author list. Do not merge or deploy this draft ahead of that dependency review. This task does not modify PR #14, production code, sync workflows, OAuth, IndexNow or account settings.

## Validation

| Check | Result |
| --- | --- |
| Full public ORCID grouped DOI comparison, both directions | PASS: 77 groups, two additions, no unresolved DOI or duplicates |
| Master and public-index DOI deduplication; JDI once only | PASS |
| Original 76 master records and 459 existing files | Preserved |
| Two independent first-position controls, original 28-entry tails and summaries | PASS |
| Build / `validate_site.py` | PASS: 78 master / 77 public / 26 current V2 pages |
| Existing citation regressions on their original locked fixture | PASS: 72 eligible, five skipped; new unsupported genres tested separately as deferred |
| Science candidate content schema and source locators | PASS; activation deferred |
| PR #14 isolated Science V2 integration | PASS; no renderer copied into this branch |
| HTML/Markdown identity and HTML Highwire/JSON-LD author sequence | PASS; deferred fields listed separately |
| Self canonicals, sitemap uniqueness, llms inventories, publication and search indexes | PASS |
| Six 390/1440 px local browser views | PASS: one H1, no horizontal overflow or script errors; visually reviewed |
| Second build | PASS: 536 source/generated files byte-identical |
| Git diff whitespace | PASS |

The historical `scripts/test_citations.py` locks the metadata-key set to its original fixture. Running it directly with the two new metadata records fails that corpus-size assertion. `verify_existing_citations.py` runs those existing regression cases with the original fixture and validates the unsupported new genres separately in `verify_delivery.py`; it does not alter or weaken the shared production renderer. All new-field capability gaps remain explicit, not counted as passed.

## Audit deliverables

- `ORCID_SITE_RECONCILIATION.csv`: all 77 ORCID work groups and the preserved SITE_ONLY patent, with before/after categories, master/index matches, sources, put-codes, years, URLs, decisions and actions.
- `ORCID_SITE_PENDING.csv`: header only; no unresolved DOI identity rows.
- `ORCID_SITE_SUMMARY.md` and `orcid-reconciliation-summary.json`: exact before/after counts and the distinctions between records, public pages and capabilities.
- `snapshots/orcid-works-20261012T070800Z.raw.json` and request manifest: timestamped unmodified public response and SHA-256; no credentials used.
- `science/SCIENCE_GOLD_STANDARD.json` and `medicine/MEDICINE_GOLD_STANDARD.json`: identity/type evidence, source versions, hashes and evidence boundaries.
- `science/SCIENCE_V2_READY.json`: reviewed, validated content candidate for activation after PR #14.
- `acceptance.json`, `PR14_INTEGRATION_ACCEPTANCE.json`, `IDEMPOTENCE.json`, `VISUAL_ACCEPTANCE.json` and logs: concrete validation and deferred acceptance.

The live Crossref author-ORCID filter returned eight records, including JDI but neither omission. Both new DOI deposits exist without author ORCID fields. This establishes the discovery gap; no API indexing-delay explanation is asserted. Raw responses and an optional, separate read-only ORCID reconciliation patch proposal are in the summary. Stable sync code was not changed.

The requested canonical routes are `/papers/doi-10-1126-science-aek9583.html` and `/papers/doi-10-1016-j-medd-2026-100004.html`. They are generated in this draft and are not represented as deployed public URLs. No merge, Pages deployment, IndexNow submission or downstream indexing action is performed.
