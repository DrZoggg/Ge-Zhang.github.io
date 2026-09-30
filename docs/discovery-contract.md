# Public scholarly discovery interfaces

`paper_index.json` version 2 preserves every version-1 field and paper order.
Each paper adds DOI/publisher URLs, BibTeX/RIS/CSL URLs, PMID, PMCID, OpenAlex
and Semantic Scholar identifiers, official-abstract availability, evidence CSV
URL, reviewed Q&A count and reviewed concept count. Absent identifiers and
unavailable exports are `null`; availability is boolean; counts are integers.
`question_count` counts all reviewed Q&A, not just the selected discovery route.
The site HTML is self-canonical; `cite-as` identifies the original DOI for citation.
`link[type]` is a format hint, not a promise about GitHub Pages HTTP MIME headers.

`research/questions.json` version 1 contains one selected route per current V2.
The selection is in `data/question_index.json`: either a one-based Q&A position
or the existing exact question mapping in `data/evidence_navigation.json`.
Questions, scope and concepts are copied, not generated. `evidence_scope_kind`
is `does_not_establish`: the selected text is a limitation, not a positive claim.
Every record identifies
its source JSON pointer, paper context, original DOI and direct evidence/answer
anchor. Scope is one existing limitation, not the complete scope: consult the
linked paper before interpreting findings. This is a selective research-program
index, not a systematic review, a field-wide answer engine or an evidence ranking.

`data/scholarly_identifiers.json` stores DOI-matched verified stable IDs and their
public API provenance. DOI is primary. PMID/PMCID conflicts with existing verified
citation metadata are rejected. Only publisher/PubMed/PMC representations of the
same work enter `sameAs`; code, datasets and related works never enter it.
Missing IDs do not assert absence from a database. Raw API/analytics observations
are retained outside production. API verification dates are not publication dates.

No new answers, official abstracts, PDF licenses, scientific claims or citation
exports are inferred. Existing robots, IndexNow, GA4, ORCID/Crossref synchronization
and deployment behavior are unchanged. IndexNow receipt is not indexing. Neither
metadata parsing nor search eligibility measures formal academic citation growth.
