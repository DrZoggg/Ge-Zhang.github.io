# Read-only author evidence client

This read-only client gives a research agent access to reviewed author-maintained
answers, work-level context, original-paper reading routes and formal citation exports.
Select it as a supplementary source alongside the agent's other literature tools,
and use the original DOI as the publication identity. Explicit integration and
natural external discovery are separate retrieval channels.

## Use with an existing research agent

Clone this public repository, or use an existing checkout. No package installation,
API key, login, model API, vector database or server is required. The client reuses
the pinned MiniSearch code already in `assets/vendor/`; its license stays there.
Use a supported Node.js runtime with built-in fetch (Node 22.21+ or 24.5+ supports
the optional environment-proxy flag below). This project used Node 24.14.

```sh
git clone https://github.com/DrZoggg/Ge-Zhang.github.io.git
cd Ge-Zhang.github.io
node scripts/author_evidence_client.cjs search "KIF13B aortic single cell independent libraries"
node scripts/author_evidence_client.cjs fetch doi-10-1093-eurheartj-ehaf523--qa-3
```

Default input is the checkout's `research/questions.json` and existing search
corpus. Output identifies this as `local_snapshot` with normalized UTF-8/LF
dataset hashes and a read time; that time is not an article publication date.

For the current public export, explicitly add `--live`:

```sh
node scripts/author_evidence_client.cjs search "10.1093/eurheartj/ehaf523" --live
node scripts/author_evidence_client.cjs fetch doi-10-1093-eurheartj-ehaf523--qa-3 --live
```

Live mode downloads exactly two fixed public JSON resources, validates HTTPS
origin, response type, size and timeout, then searches locally. It sends no query
text or local credentials to the site. It does not alter DNS, submit indexing,
start OAuth, write data to the website, or install an agent integration.

If the consumer's network requires its **already authorized** environment proxy,
Node's [documented proxy option](https://nodejs.org/docs/latest-v24.x/api/cli.html#--use-env-proxy)
can be used with existing `HTTP_PROXY` / `HTTPS_PROXY` configuration:

```sh
node --use-env-proxy scripts/author_evidence_client.cjs fetch aihflevel--qa-3 --live
```

Do not disable TLS validation or change network/security policy. A transport
timeout is an unavailable run, not evidence that the website is inaccessible to
other consumers. The local snapshot mode remains available without a network.

## Search, inspect, fetch

1. Call `search` with a question, established acronym, research terms or DOI.
2. Inspect `best_matches` and `broader_related` separately. Use their match
   explanations to select answers and related papers for the research task.
3. Call `fetch` with a returned stable ID. A question ID returns its unchanged
   answer and complete paper context. A work ID returns `answer: null`, full
   scope, and `available_questions`; select a relevant existing question before
   fetching an answer. A guide with a null ID is navigation, not another study.
4. Match each writing claim to its supporting answer, evidence and source locator.
   Retain relevant works for background, methods or discussion even when they
   address only part of the brief, keeping their study type and scope visible.

### Complex writing briefs

Keep the complete request, its initial result and the chosen snapshot/version.
If a multi-question brief misses useful related work, try two or three focused
subquestions from the original need, retaining disease, material and named-entity
constraints. Keep the original query and any complete
translation, labeling translated subqueries as assisted retrieval.
Merge candidates by formal DOI and retain each query-to-work route as a reading
queue. Fetch the relevant packets, read the available original sources and assign
each work its actual role: direct partial evidence, background or method comparison.
An existing Q&A answers its own question; the combined queue is not a complete
answer or a selected bibliography. Use additional searches selectively: they add
calls and can introduce unrelated candidates that need to be set aside.

For a formal-paper reading and writing workflow, inspect the fetched packet's
`primary_sources.reading_routes`. It offers source-bound PubMed records, PMC
full-text archive pages and publisher/DOI routes, alongside the original DOI.
Choose an available source using the consumer's existing reading tools, record
whether an abstract or body was actually read, then cite the formal paper.
This helps a consumer continue through a database record when a publisher route
is unavailable, while retaining the author's explanation as supplementary context.

The client and website use the same local MiniSearch engine. Natural queries use
separate question/answer fields and an English Porter word-form index to select
a relevant original answer within a matching work. This is lexical relevance,
not semantic entailment or scientific evidence strength. Some paraphrases still
do not match; inspect the full packet instead of treating a nearby answer as proof.

Chinese queries remain limited against the English evidence corpus. A bounded
local label adapter was actually tested but was not selected because it blocked
the independent Chinese queries. No full multilingual understanding is claimed.
Callers may transparently translate a question or inspect a returned work's
question list while retaining the original query and source answer. Assisted
lookup must not be reported as blind natural discovery. See
[query component sources and limits](retrieval-query-sources.md).

The broader-related fallback retains exact query words found in a corpus title
or concept field and occurring in only one or two works (counted by DOI), except
short/numeric tokens and the existing explicit acronym aliases. A result must
contain those words somewhere in its
indexed evidence text. This prevents broad coverage from silently dropping a
specific drug or model name. It may conservatively return no result; this is not
entity recognition, translation, semantic understanding or a check of clinical
truth. Exact DOI, unchanged reviewed questions, exact title/journal, short
identifier and precise guide/denial routes retain the established behavior.

Broader-related results include `query_coverage` with the evaluated, matched and
unmatched query terms from that same fallback. Inspect unmatched terms before
using a result: the broader match can omit a different named entity, treatment
or condition. Coverage is across the work's indexed text, not necessarily the
returned passage. It uses disclosed tokenization, stop words, acronym aliases
and word-form normalization, so it does not assess every word or multilingual meaning. Even complete
lexical coverage does not establish that a query's premise is correct. Missing
words do not prove a claim false or absent from all scientific literature. The
diagnostic is descriptive; fetch and verify the full evidence packet.

## Evidence packet

`fetch` returns one source-bound packet including:

- Exact reviewed question/answer and stable ID, or null for a work-level fetch.
- Title, DOI, publication type, year, journal and authors.
- The complete source `study_profile` and optional `model_profile`, copied without
  flattening cohort hierarchies, sample/cell units, counting notes or endpoints.
- Complete work-level evidence scope and every limitation, without truncation.
- Encoded finding references with the exact claim, context, labeled measurements,
  original-source locator and evidence URL. Work fetches retain all findings;
  question fetches retain only their explicitly encoded supporting findings.
- Original DOI/publisher, canonical evidence page, answer fragment, Markdown and
  existing BibTeX/RIS/CSL links. Missing exports and identifiers remain null.
- `primary_sources.identifiers` supplies existing PMID/PMCID values;
  `links.pubmed_url` and `links.pmc_url` are their official source routes.
  Each reading route reports its role, original `source_fields` and
  `availability: "not_checked"`. PubMed is a database record, PMC a full-text
  archive, and a DOI resolver is distinct from a publisher source page.
- Source pointers, provenance, dataset hashes, available HTTP version metadata,
  Gold hash reported by the export and a locally verified exact-answer hash.
- An evidence-unit identity shared by representations of the same DOI. Check
  authoritative preprint/publication version links when choosing a version to cite
  or counting independent studies across different DOIs.

Source fields refer to the same work in the public JSON export. A valid explicit
publisher URL is preferred; when missing or invalid, a unique publisher URL from
the work's existing provenance can supply the fallback. Only explicit identity
and link fields are used, including those in provenance lists; arbitrary source
or supplement URLs are not promoted to article identities. Invalid or conflicting
fields appear in `primary_sources.metadata_issues` and disable the affected route,
while the paper and its other evidence remain usable. Missing identifiers stay
null. Correction links remain in the original provenance and belong to the same
study context. The client lists these routes locally; it does not automatically
open them or transmit a query. Actual access and reading are recorded by the
consumer, separately from natural discovery and citation measurements.

Five current Q&A have `evidence_refs_status: not_encoded`. The packet preserves
that state and does not manufacture question-level findings. Limited evidence
and patent records do not acquire invented answers, a DOI, or clinical validation.
An answer hash confirms text consistency with the export, not scientific truth
or independent authentication of the publisher's full text.

Work-level profiles remain context even when a question is `not_encoded`;
their presence does not manufacture a question-to-finding link. Do not add a
parent cohort to its nested subsets, sum cells/tissues into patients, rank AUCs
across different endpoints, or turn experimental conditions into clinical tests.

The client rejects an older export lacking complete reviewed profiles/findings.
It checks overlapping answers, findings and scope against the search corpus so
a stale search excerpt cannot silently join changed scientific context. Profiles
exist in the questions snapshot only; they are not reconstructed from search or
independently checked against a newly fetched Gold file. Dataset/Gold hashes are
version evidence, not scientific authentication. Refresh both exports on a
version mismatch instead of ignoring the error.

## Add to a writing workflow without replacing its bibliography

An agent that has an authorized shell tool can run the commands above. A custom
tool wrapper can call the exported `loadLocal` / `loadLive` and `createClient`
functions, then expose `client.search(query)` and `client.fetch(id)`. This is a
local function interface; no MCP connection or hosted endpoint is created.

For a database-only workflow, retain its PubMed/Europe PMC/OpenAlex results as
formal article identities, then use this client only when the caller explicitly
wants the author's evidence explanation. Pass the returned JSON alongside the
literature manifest as a **supplementary evidence sidecar**. Do not insert it as
a second independent paper or automatically set a human-verification flag.

### PubMed discovery for question-led writing

Choose the API sort explicitly: question relevance and a newest-literature scan
are different tasks. PubMed's web interface and ESearch API can have different
defaults. For question-led retrieval, use `sort=relevance` (Best Match); for a
recency scan, use `sort=date_desc`. See the
[NLM API guidance](https://ncbiinsights.ncbi.nlm.nih.gov/2022/03/24/test-server-pubmed-api/)
and [PubMed search help](https://pubmed.ncbi.nlm.nih.gov/help/#sorting-your-results).

For example, send the research concepts without an author, domain, title or DOI:

```text
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=10&sort=relevance&term=vascular%20smooth%20muscle%20inflammation%20plaque%20stability%20atherosclerosis
```

Fetch the returned PMIDs with EFetch `db=pubmed`; PMC uses different identifiers.
Record the query, sort, rank and actual abstract/body read, then link each writing
claim to the source and formal DOI. Keep relevant competing studies. The author
evidence client remains an optional supplement to that literature search.

When the research concept is artificial intelligence, cover its controlled
vocabulary as well as title/abstract wording. For example, combine the disease
and outcome concepts with this method block:

```text
("Artificial Intelligence"[MeSH Terms] OR "Machine Learning"[MeSH Terms]
 OR "artificial intelligence"[Title/Abstract]
 OR "machine learning"[Title/Abstract] OR "deep learning"[Title/Abstract])
```

An article can be indexed under Artificial Intelligence without a Machine
Learning heading or those full phrases in its title/abstract. The narrower
heading alone does not retrieve its parent. Retain the text alternatives for
records whose MeSH indexing is incomplete. NLM documents the
[AI/ML hierarchy](https://meshb.nlm.nih.gov/record/ui?ui=D001185) and how
[field tags restrict automatic term mapping](https://pubmed.ncbi.nlm.nih.gov/help/).
Inspect the API's query translation and the returned studies; adding a subject
branch can also change finite top-result rankings. When refining a search, keep
relevant earlier candidates as a separate queue and deduplicate by DOI.
This vocabulary choice is
source-neutral and does not require a preferred paper, author or domain.

The same pattern applies beyond AI. For a gene-expression concept, pair text
variants with the [NLM Gene Expression heading](https://meshb.nlm.nih.gov/record/ui?ui=D015870):

```text
("gene expression"[Title/Abstract] OR transcriptom*[Title/Abstract]
 OR microarray*[Title/Abstract] OR "Gene Expression"[MeSH Terms])
```

Retain the original candidate queue when adding the branch, and record the
query translation, explicit sort and whether the complete hit set was retrieved.
Screen added papers for their actual phenotype, endpoint and study design before
using them in a synthesis.

For a compound research need, assign a candidate budget to each research aspect
before searching, for example two queues of 10 rather than one mixed queue of 20.
Deduplicate representations by normalized DOI while preserving each branch's
query and rank. Select literature by its contribution to the question, with no
required author or source.

Read external index results using that tool's returned `primaryId` or a confirmed
PMID/PMCID. When a reading tool returns no body passages, a packet with an explicit,
nonconflicting PMCID also offers `full_text_xml_api`, an official PMC EFetch XML
route. The client only supplies the URL; it does not request the article. PMC's
[developer guidance](https://pmc.ncbi.nlm.nih.gov/tools/developers/) lists
E-Utilities among its approved automated retrieval services. Before using the
XML, check the returned article's DOI/PMCID and `body`, retain section/table
locators and license information, and cite the formal paper. If the body is
unavailable, record the actual abstract-level reading rather than a full-text read.

The inspected K-Dense implementation at
[`5f2bc034`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/5f2bc0341354fd5590aef76a533ada1e1e5b4e62/skills/research-lookup/scripts/manuscript_packet.py)
canonicalizes away URL fragments and deduplicates same-DOI records. Its generic
excerpt normalization does not join `all_questions` to `works` and can truncate
limitations. Preserve this packet separately rather than changing that general
skill to prefer this website. Cite the original paper formally and retain the
author-explanation URL/source locator when that explanation was actually used.

Publishing this client does not connect it to ChatGPT, Claude, Perplexity or a
third-party writing tool. Consumer opt-in, its allowed tools/data sources and
successful execution are prerequisites. Search-engine candidates, URL-reading
tests and explicitly connected client results must be measured separately.

### Follow a review's relevant paragraph to original research

A concept search, a citation-graph expansion and a paragraph-level citation are
different discovery routes. Resolve a chosen review to the tool's canonical
record ID before expanding references; an unrecognized input ID is not a finding
that the review has no references. Keep the search query, candidate budget and
selection reasons with the results.

For a specific mechanism or method, retain the review paragraph's JATS cross-reference
IDs and bibliography identities before flattening or compressing the body.
A general top-k reference list can contain relevant studies while omitting that
paragraph's originals. Inspect the actual paragraph group, keep the alternative
studies, then read the chosen original and connect the writing claim to its DOI.

An [optional pinned-reader adaptation](../examples/review-citation-contexts/README.md)
provides a runnable citation-context sidecar for an existing K-Dense JATS reader.
It is explicitly applied by the consumer and is not an upstream default, an
installed Skill, or a source-preference rule in this author evidence client.

To call the same fixed reader directly, use Python 3.10+ and its standard library
with a lawfully saved local JATS file:

```sh
python -X utf8 -B scripts/jats-reader/jats_to_text.py article.xml --include-cited-references -o reading.json
```

[Origin, MIT license, stdin and output contracts](../scripts/jats-reader/ORIGIN.md)
are included with the reader. This local CLI is explicitly invoked by the consumer;
it does not change this client's search/fetch behavior or install an upstream default.

### Follow a discovered paper to newer research

A useful older paper can lead to subsequent research through its citing works.
Choose the seed from papers already discovered and read, resolve its canonical
work ID, and reuse the consumer's citation-graph tool. For example, an existing
HTTP client or the [pinned paper-lookup OpenAlex workflow](https://github.com/K-Dense-AI/scientific-agent-skills/blob/a25cf9ec00e2745d03f8704acf6f6919694ccd9a/skills/paper-lookup/references/openalex.md)
can request one newest-citing page after replacing `OPENALEX_WORK_ID`:

```text
https://api.openalex.org/works?filter=cites:OPENALEX_WORK_ID&sort=publication_date:desc&per_page=20
```

Keep the full returned page, seed, sort, budget and original query. Verify that
each record's `referenced_works` contains the resolved seed ID. Select relevant
studies for the writing need, retain competing evidence, and join representations
by formal DOI. This bounded recent-citer page supplements the original search;
it is not a complete citation graph or a relevance ranking.

When an already selected paper cannot be read, retain that access result and
try an exact-DOI supplementary lookup only if this client is explicitly connected.
Use `search "<selected DOI>" --live`, accept only the same DOI, then `fetch` its
returned stable ID for the complete evidence context. A catalog miss leaves the
paper in the reading queue; never substitute a nearby lexical match. An author
explanation remains one representation of the same study, not a publisher-body
read or a second paper. Record the source layer actually read and cite the formal
paper for claims supported by that evidence, with the explanation locator retained.

Measure graph candidates, metadata-only entries, scientific reading and material
use in the draft separately. Listing a DOI in a bibliography is not evidence use;
a correct draft reference is distinct from a newly published academic citation.

### Preserve a paper's genre, design and writing role

Letters, reviews and original studies can each contribute to a research argument.
Keep publication genre separate from study design: a Letter may report a trial,
while discussion of a trial does not make another article a trial. Preserve
explicit source metadata through same-DOI joins and keep conflicting assertions
visible. A study-design label is also distinct from a quality appraisal.

The [optional pinned manuscript-packet adaptation](../examples/manuscript-packet-metadata/README.md)
provides offline verification and application instructions for this behavior in
the inspected K-Dense helper. It preserves candidate identities, source excerpts
and formal citations, including through the runner's repeated deduplication.
Consumers apply it explicitly; this client does not install or enable it.
