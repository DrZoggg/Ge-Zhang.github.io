# Complete public ORCID reconciliation

Snapshot: `2026-10-12T07:07:58.055141+00:00`. Official public API: <https://pub.orcid.org/v3.0/0000-0002-3116-3246/works>; HTTP 200, no account credentials used.
Baseline: `75040ff3b04c0a5151889b1793bc69a03a590037`. `audit_orcid.py` reproduces this audit offline from the raw response and baseline Git objects; `--refresh` performs a new public GET.

| Measure | Before | Current workspace |
| --- | ---: | ---: |
| ORCID public work groups | 77 | 77 |
| ORCID work summaries (sources/put-codes, not publication count) | 107 | 107 |
| Website master records | 76 | 78 |
| Public paper index records | 75 | 77 |
| ORCID DOI records represented in master | 75 | 77 |
| ORCID DOI records represented in public index | 74 | 76 |
| ORCID DOI records missing from master | 2 | 0 |

The two baseline omissions are `10.1126/science.aek9583` and `10.1016/j.medd.2026.100004`. `10.1111/jdi.70462` already exists. There are 0 groups with ambiguous DOI identity. Article-type and full-text verification are separate checks; these counts do not claim that Science has a formal V2.

The baseline master includes one withdrawn preprint (`10.21203/rs.3.rs-3395716/v1`), which is in ORCID but deliberately excluded from the public index. One existing no-DOI Patent is absent from this public ORCID snapshot and must be preserved. Thus the baseline contains 76 master records (75 with DOI and one Patent), 75 public index records, and 75 ORCID DOI matches in master (74 in the public index).

`ORCID_SITE_RECONCILIATION.csv` has one row per public group plus the SITE_ONLY preservation case and preserves all source names and put-codes. The timestamped snapshot named in `orcid-works-public.request.json` is the complete unmodified response and retains all 107 summaries, group external identifiers and source identities. Its original byte hash is checked before use. `audit_orcid.py --expanded` can regenerate detailed working files locally; redundant copies and old execution logs are archived outside the repository, with original Git LF hashes and historical commit linkage in `ARCHIVE_MANIFEST.json`.

Targeted official `/work` responses additionally verify the three requested identities. Science's publisher-supplied AAAS record identifies Ge Zhang as first author with ORCID `0000-0002-3116-3246`. The Medicine Discovery self-entered record lists 16 authors with Ge Zhang last; the publisher corrected proof independently confirms the complete authors, Correspondence subtype (p. 5) and corresponding-author footnote (p. 6). JDI's record lists eight authors with Ge Zhang fourth; its existing master identity is unchanged.

## Final evidence and dependency status

- Science: complete local publisher print pages 38-39 were visually reviewed again, excluding adjacent Letters. The five arguments, five Q&A items, citation-use boundaries and evidence matrix are activated without scientific changes at `data/deep_geo/doi-10-1126-science-aek9583.json`, with exact paragraph locators. Formal V2 completed: **True**. PR #14's existing Letter renderer is reused; the public page has ScholarlyArticle schema and complete citations. No n=1 dataset or treatment effect was manufactured.
- Medicine Discovery: verified Correspondence; identity page only, with no automatic Selected/Deep GEO membership. Corrected-proof pagination is not used as a journal page range; volume and issue remain unassigned.
- Truly missing before: 2; added: 2; missing after: 0; identity/type records awaiting verification: 0.
- Selected Research: 29; Deep GEO: 29. Science is first independently in both; all old entries and summaries are preserved.
- `ORCID_SITE_RECONCILIATION.csv` contains all 77 public groups plus the preserved SITE_ONLY patent; `ORCID_SITE_PENDING.csv` contains only unresolved rows.
- Citation capability dependencies are resolved: PR #14 is merged and the shared renderer now supports Correspondence. Both new works have BibTeX, RIS, CSL-JSON and full Markdown authors; genre is preserved. Pending citation-capability records: 0. See the focused publication-release regression and final release acceptance; no duplicate renderer was implemented.
- Public source PDFs/page images stay outside this repository. Gold Standard records retain version descriptions, source hashes, explicit reference context and locators.

## Why daily Crossref discovery omitted these works

The original live Crossref ORCID-filter query returned eight works and included JDI, but did not include either new DOI. Both DOI-specific Crossref deposits existed and listed authors, without an author ORCID field for this researcher. An ORCID public work group can be author-added or publisher-supplied independently of Crossref author-ORCID registration. The observed discovery gap is established for that captured audit; an API indexing delay is not established. Historical raw query/request files are preserved in the local archive and original PR #15 commit, and DOI-specific deposits remain in the compact evidence record.

A separate follow-up could periodically reconcile public ORCID self-DOIs into a reviewable branch, protecting existing types, identity fields and selection controllers. It should have a read-only audit mode, idempotent DOI normalization and regression cases for same-name authors, withdrawn records and generic journal-article types. No stable synchronization or automation code was changed in this publication PR.
