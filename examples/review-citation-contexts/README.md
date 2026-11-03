# Optional review-to-original citation contexts

This source-neutral adaptation extends the existing K-Dense JATS reader. It keeps
source-relative citation groups and bibliography identities available before
flattening, so a caller can select and read relevant originals. It does not
retrieve articles, change search ranking or insert a preferred paper into a draft.

## Apply to the pinned reader

Use an isolated copy of `K-Dense-AI/scientific-agent-skills` at
`5f2bc0341354fd5590aef76a533ada1e1e5b4e62` (paper-lookup v2.4), preserving its
existing `_common.py` and other helper files. The original target is
`skills/paper-lookup/scripts/jats_to_text.py`, SHA-256
`2185a4994dc41216e160ab173183cda42b5d3e5be82547f470df6dcd6fe3a53d`.
The complete patch below applies to that original, not to an already patched file.

```sh
git -c core.autocrlf=false apply --check /path/to/kdense-jats-reference-sidecar.patch
git -c core.autocrlf=false apply /path/to/kdense-jats-reference-sidecar.patch
python -X utf8 /path/to/verify_reference_sidecar.py skills/paper-lookup/scripts/jats_to_text.py
python -X utf8 skills/paper-lookup/scripts/jats_to_text.py article.xml --include-cited-references
```

Patch SHA-256: `6ba78d271fd7b5babf4edde12f8cda5e1446fa0df2c5d6908c82d0efe64ef21a`.
Applied reader SHA-256: `654e7a6050d44bd8857473fd095dc15444b7293d3e501a7647811b0fc0144a88`.
Python 3.10+ and its standard library suffice. The verifier accepts the existing
helper path and sends small synthetic structural XML through stdin; it makes no
HTTP requests and contains no copyrighted article fixture or private audit data.
No Skill installation, account, service, dependency or global setting is added.
The per-command Git setting preserves patch bytes without changing global config.

## Output and compatibility

Without `--include-cited-references`, the existing JSON schema stays unchanged.
The default text extraction now includes direct body paragraphs interleaved with
sections, in source order; this intentionally corrects previously omitted prose
and can change section/word counts for that layout. Previously retained section
text is preserved. Normal section-based and paragraph-only regression fixtures
retain their prior default output. Foreign sub-articles/responses are excluded
from the owning article's metadata and reading text.

With the flag, JSON adds `citation_contexts` and `bibliography_references`.
Existing context fields (`section_id`, `section_title`, `paragraph_index`, `text`,
`reference_ids`, `references`, `unresolved_reference_ids`, `attribution`) remain.
Additive fields provide exact element locators, the source article's own
identifiers/JATS article type, explicit range evidence and parser-unobserved
read/use status. Source identity is distinct from every cited work's identity.
The source article type is metadata, not an independent appraisal of study design.

The bibliography list retains explicit reference IDs, labels, available titles,
publication types, DOI/PMID/PMCID, locators and identifier encoding/issue records.
It supports reference lists nested in the owning body or back matter and explicit
`pub-id` or identity-labelled `ext-link` attributes. DOI-resolver URLs are accepted
only in explicitly DOI-labelled fields. Titles, arbitrary URLs and Google Scholar
links are never mined for DOI identity. The first explicit identifier spelling is
retained, and DOI conflicts are compared case-insensitively. Ambiguous identifiers
or links remain unresolved while the readable article and other unambiguous
references stay available.

A conflicting identifier field is omitted from that record's `identifiers`;
`identifier_conflicts[field]` instead records status `unresolved` and every valid
explicit candidate value, encoding and locator. Other unambiguous fields remain.
No conflicting value is chosen. Invalid explicit fields retain their existing
issue records. The article's source identity and readable scientific body do not
become unavailable because a cited reference contains a conflict.

Duplicate reference IDs retain every bibliography entry, each marked
`reference_id_status: "ambiguous_duplicate"` with all candidate reference locators.
A context keeps that ID in `unresolved_reference_ids`, omits all ambiguous entries
from its `references`, and supplies `reference_link_issues` with candidate locators.
Other references remain linked normally. Duplicate IDs cannot supply numeric-range
resolution. These ambiguity fields appear only on affected records/contexts;
clean records receive no new annotations. Malformed XML and the metadata-only
refusal retain their original failure behavior.

A numeric citation range is expanded only for adjacent bibliography xrefs in the
same parent separated by a range dash, with numeric endpoint text, a unique and
complete bibliography-label map, matching endpoint identities and an ascending
span of at most 1,000. This uses labels, never reference-ID order. A comma list,
reversed range, duplicate/missing labels or other ambiguity is not interpolated;
unresolved range evidence stays visible. Group membership does not identify which
reference supports each clause.

`context_status` distinguishes selected/outside-selected links, unlinked entries,
missing IDs and unresolved-range ambiguity. “Uncited in scanned body paragraphs”
is limited to the paragraphs this reader scanned, not proof of global absence.
Read/use statuses are `not_observed_by_parser`; reference presence never asserts
an original abstract/body read, verified claim, draft citation or published growth.

`--sections` retains top-level case-insensitive title/sec-type substring filtering;
contexts may come from nested sections under the selected top-level block. Direct
body paragraphs participate when no section filter is supplied. This is not a
fine-grained nested-section selector. `--text-only` emits text and no JSON
sidecars. The existing metadata-only refusal/exit 2 remains, unless the caller
explicitly requests `--allow-metadata-only`.

## Same-citation alternatives

[JATS 1.4 citation-alternatives](https://jats.nlm.nih.gov/archiving/tag-library/1.4/element/citation-alternatives.html)
represents multiple formats or languages of one citation. If a reference has no
legacy direct mixed/element citation, this adaptation also accepts direct
`element-citation`, `mixed-citation` and `nlm-citation` children of its direct
`citation-alternatives` container. It emits one bibliography record per `ref`,
not one study per representation. Existing direct-citation precedence is unchanged.

Repeated identifier fields merge only when their explicit normalized values
agree; DOI comparison remains case-insensitive. Available unambiguous fields are
retained when another representation omits them. Missing identities are never
inferred from titles, unlabelled prose, arbitrary links or the container's
`object-id`. An explicit disagreement removes only that field from `identifiers`
and preserves every candidate value/encoding/locator in `identifier_conflicts`.
Other fields, references and readable article text remain available. The standard
container asserts one citation; the parser does not independently verify DOI/PMID
crosswalks. Identifier-source locators retain both representations. The first
available structured title and publication type are display metadata, not an
identity-inference rule. Duplicate `ref` IDs remain separate ambiguous entries;
alternatives never merge different `ref` elements or foreign sub-articles.

The verifier runs 28 synthetic cases, including same-citation alternatives.
Retained-source checks keep
default reading text, source identity, paragraph order, locators and existing
citation-range behavior unchanged. This is parsing/identity completeness, not a
new original read, natural candidate result, scientific validation or draft use.

## Use in a research-writing workflow

Search for the research need normally and retain relevant alternatives. Inspect
an available source's citation contexts as a separate route, select originals by
scientific contribution, then record their actual abstract/body reading and
claim-specific use. Keep the source role, paragraph/reference locator and cited
DOI together. Bibliographic visibility is not reading, and reading is not final
citation. Keep reference-assisted diagnostics separate from natural first-pass
results. An unresolved graph record does not establish an empty bibliography.

The parser has bounded layout/range handling and is not a universal JATS or
scientific-entailment engine. The synthetic verifier and private retained-source
regressions demonstrate local compatibility, not natural consumer adoption or
improved clinical evidence. Consumers apply this adaptation explicitly; it is
not an upstream default or a new installed reader.

## License and origin

The patch modifies the pinned MIT-licensed K-Dense reader, Copyright (c) 2025
K-Dense Inc. Its complete notice is retained in `LICENSE.kdense.md`. The added
verifier uses only synthetic structural data and standard Python. This work does
not modify the separate manuscript-packet metadata-fidelity adaptation.
