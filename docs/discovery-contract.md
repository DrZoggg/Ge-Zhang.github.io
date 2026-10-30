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

The optional `answer_preview` field is an additive, at-most-six-entry pilot,
selected by `answer_previews` in the same `data/question_index.json` controller.
Only directly selected Gold Q&A entries qualify; navigation mappings without an
exact Q&A selector are rejected rather than assigned a guessed answer. The
complete answer is copied verbatim, alongside all `does_not_establish` limits,
resolved `evidence_refs`, original-source locators and links to the existing
paper evidence anchors. No answer, denominator or conclusion is synthesized.
The source and scope JSON pointers identify the unchanged Gold file. The Gold
content SHA-256 uses UTF-8 text with LF line endings for portability; the answer
SHA-256 hashes the exact UTF-8 answer string. Existing fields, routes and order
remain unchanged, so the JSON contract stays at version 1. The answer and scope
are ordinary crawlable HTML, not excluded UI-only text, and the Questions
page's sitemap lastmod follows the existing substantive-content change rule.

The additive Scientific Questions discovery contract has `discovery_version: 2`.
The existing `version: 1` and 59 selected `questions` retain their fields, order,
eight independent navigation mappings and six complete answer previews. They are
not replaced by the full Q&A list; homepage consumers still use that legacy list.

`works` is a normalized context record for every current public work, in publication
order. It identifies the existing paper and Markdown URLs, DOI and citation exports
(null when unavailable), source evidence status, exact reviewed fields and concepts,
complete evidence scope and limitations, and source-located findings. The additive
`study_profile` and optional `model_profile` preserve the entire reviewed object,
including cohort relationships, denominators, counting notes and endpoints, with
their source JSON pointers. Findings retain exact claim, context and labeled
measurements as well as locators. Missing model profiles are null. These fields
are work context and do not fill absent question-level evidence refs. Fields and
concepts describe paper context, not a claim that each Q&A validates every concept.
Limited notes and the patent reuse their existing scope without synthesizing Q&A.
Gold source pointers refer to the public source repository; `/data/` is not deployed
by Pages and is not advertised as a public site endpoint. Gold hashes normalize LF.

`all_questions` is generated from all existing V2 Gold `qa` entries. Each stable
`work_id--qa-N` record retains the exact question and answer, one-based position,
direct canonical-paper `#qa-N` URL, source pointers, answer hash and evidence refs.
The work record resolves each finding reference to its exact original-source locator
and existing paper anchor. An empty source `evidence_refs` is explicitly
`not_encoded`; no finding relationship is guessed, and no stronger scientific
verification is claimed. The current snapshot contains 362 Q&A: 357 with resolved
question-level refs and five without encoded refs. These are observations, not fixed
future inventory requirements.

The public HTML contains all question links in native disclosures, every work
identity, six answer previews and the original evidence limits. Complete answers
remain on existing canonical paper pages and in the derived JSON export, rather
than hundreds of new pages or a single full-answer HTML dump. No new canonical URL,
FAQ/QAPage schema, robots policy or publishing framework is introduced. The existing
MiniSearch corpus and pinned engine are reused; Q&A hits now link directly to the
corresponding answer anchor. Search is a local progressive enhancement, not a new
AI answer generator; all discovery links remain available without JavaScript.

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

## Explicit external consumers

The [optional read-only client](author-evidence-client.md) reuses these exports
and the existing MiniSearch engine. `search` returns stable question/work IDs;
`fetch` joins a question to its work and returns full identity, scope, limitations,
encoded locators, formal citation links and content-version metadata. It does not
generate scientific answers or add a new public page, API, Skill or MCP server.
Local and live-public-export reads are labeled separately. A client match is an
explicit integration result, not evidence of natural external AI adoption.

A URL fragment such as `#qa-3` is a document location, not a distinct HTTP response
or independent index page. Extractors must select that node and retain or join the
work context. A normalized `all_questions` record is deliberately not a standalone
clinical evidence packet; consuming it without its `works` record loses context.
The data relationship itself is unchanged. Missing question-level refs stay missing.

Paraphrase fallback preserves paper selection and now chooses the most relevant
passage within its selected category, rather than the first Q&A of that paper.
All exact-question routing remains covered by the existing regression. Broader
text matches, null work-level answers, no matches and unsupported language must
not be reported as correct answers to clinical or causal questions.
