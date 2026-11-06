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

Limited-evidence works can also provide an optional `author_evidence_note` in
the export and fetched packet. Its `sections` retain the existing author note's
headings, text, HTTPS source URLs and locators, alongside the original
`reviewed_on` date. This is supplementary author context, not Gold Q&A or a read
of the original paper's full text; the work's publication type, scope and limits
remain unchanged. `source_record` is a repository-relative JSON Pointer into
`data/limited_evidence.json`, not an HTTP reading URL. Use the original HTTPS
URLs within `sections` to open their sources. Older snapshots without this
optional object remain readable; omission does not mean no author note exists.

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

A reviewed institutional PDF can also appear as an `institutional_repository_pdf`
route with its bound `doi` and explicit `version` (`journal_pre_proof`,
`accepted_manuscript` or `version_of_record`). Follow that URL with the consumer's
existing PDF reader and retain the stated version in the reading log. The route
comes from an explicit `reading_route` annotation on an existing source record;
the client does not infer it from a filename, label, reference or arbitrary note
URL. `availability: "not_checked"` means the client has not fetched that PDF.
Older exports without the annotation continue to expose their original sources.

A verified author-shared ResearchGate publication page can appear as an
`author_shared_copy` route. The client uses the dedicated provenance link
only when its accompanying DOI URL matches the work's formal DOI. Use a web
reader to check what the landing page actually exposes and record the reading
level. The author-shared route supplements the publisher and PubMed links.
Use the original DOI for the formal citation.

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

For a citation in a table, follow the reference link in the published HTML. With
JATS, add `--table-id` with the exact `table-wrap` ID and match the bibliography
`xref` element's `rid` to `bibliography_references[].reference_id`. The paragraph
sidecar covers scanned body paragraphs. If you use Europe PMC's references API,
check `hitCount` for additional pages and match by DOI or PMID. Keep the article's
reference label separately because the API's `citedOrder` can differ from it.

[Origin, MIT license, stdin and output contracts](../scripts/jats-reader/ORIGIN.md)
are included with the reader. This local CLI is explicitly invoked by the consumer;
it does not change this client's search/fetch behavior or install an upstream default.

### Find papers using a dataset from the research task

When a research task or an already read paper supplies a dataset accession,
supplement topic searches with Europe PMC's [data-accession index](https://groups.google.com/a/ebi.ac.uk/g/epmc-webservices/c/7ZTIYvhJq6E).
It can expose relevant papers whose titles and abstracts do not name the dataset.
Reuse an existing HTTP tool or paper-lookup's Europe PMC search; no new service or
API key is needed. For example, replace the accession below with the one supplied
by the actual research task and save one bounded response:

```sh
curl --fail --get --max-time 45 \
  "https://www.ebi.ac.uk/europepmc/webservices/rest/search" \
  --data-urlencode "query=ACCESSION_ID:GSE57338" \
  --data-urlencode "format=json" \
  --data-urlencode "resultType=core" \
  --data-urlencode "pageSize=20" \
  --output dataset-papers.json
```

Check the JSON for `errCode`, `resultList` and the echoed `request.queryString`;
HTTP 200 alone is insufficient. Preserve the original topic-search pool, this
supplement's complete returned page and its query/time/budget, then join formal
DOIs. Screen titles, study types and available source links for the writing need.
A missing index abstract need not exclude a relevant paper with readable full text.
Read selected PMC records with the existing `/{PMCID}/fullTextXML` route and JATS
reader, or use a same-paper publisher/repository route already returned in metadata.

Locate the accession in the paper's Methods, results or data statement and record
its role: original data, discovery, validation, comparison or a cited mention.
An indexed mention is a discovery lead, not proof of direct reuse. Track shared
cohorts across papers when discussing validation; several papers using the same
dataset are distinct publications, not automatically independent populations.
Cite the selected paper's formal DOI beside the supported argument and retain the
body locator. Keep this given-dataset supplement separate from the original search
and from broad natural-discovery measurements. Consumers explicitly execute the
route; this recipe does not alter their default search or install a tool.

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

### Follow PubMed full-text links after a resolver failure

If a selected paper's DOI route fails, reuse the already read official PubMed
record's **Full Text Sources** links before treating its abstract as the only
available text. A publisher link can work even when the DOI route failed;
other LinkOut providers may require access. Keep those outcomes separate.

Save this standard-library snippet as `extract_pubmed_fulltext_routes.py`. It
reads a saved scrape JSON containing `metadata` and `markdown` (including a
Firecrawl `structuredContent` envelope or a saved `response` wrapper). Supply
the selected paper's PMID and DOI from its verified identity. It extracts only
the Full Text Sources section, not references, related articles or generic links.

```sh
python -X utf8 -B extract_pubmed_fulltext_routes.py pubmed-scrape.json --pmid 36940731 --doi 10.1016/j.freeradbiomed.2023.03.003 > reading-routes.json
```

```python
"""Extract source-bound LinkOut routes from a saved PubMed scrape; no network."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def extract(payload, pmid, doi):
    if not re.fullmatch(r"[1-9][0-9]{0,9}", pmid):
        raise ValueError("Expected a numeric PMID")
    if not re.fullmatch(r"10\.\d{4,9}/\S+", doi):
        raise ValueError("Expected a formal DOI, without a resolver prefix")
    response = payload.get("response", payload)
    if response.get("isError") or response.get("success") is False:
        raise ValueError("Saved scrape reports an error")
    data = response.get("structuredContent", response)
    meta, markdown = data.get("metadata", {}), data.get("markdown", "")
    if meta.get("statusCode") != 200 or not isinstance(markdown, str):
        raise ValueError("Expected a successful saved page with Markdown")
    if str(meta.get("citation_pmid", "")) != pmid:
        raise ValueError("Source PMID does not match the selected paper")
    if str(meta.get("citation_doi", "")).casefold() != doi.casefold():
        raise ValueError("Source DOI does not match the selected paper")
    if meta.get("uid") is not None and str(meta["uid"]) != pmid:
        raise ValueError("Conflicting source PMID")
    source_url = meta.get("sourceURL")
    for value in (source_url, meta.get("url", source_url)):
        u = urlsplit(value or "")
        if (u.scheme != "https" or u.netloc != "pubmed.ncbi.nlm.nih.gov"
                or u.path.rstrip("/") != "/" + pmid or u.query or u.fragment):
            raise ValueError("Expected the selected official PubMed record URL")
    heading = re.search(r"(?m)^\s*(?:-\s*)?#{1,6}\s+Full Text Sources\s*$", markdown)
    if not heading:
        raise ValueError("No saved Full Text Sources section; availability remains unknown")
    section = re.split(r"(?m)^\s*(?:-\s*)?#{1,6}\s+", markdown[heading.end():], maxsplit=1)[0]
    routes, seen = [], set()
    for line in section.splitlines():
        match = re.fullmatch(r"\s*-\s+\[([^\]\n]+)\]\((https://[^\s]+)\)\s*", line)
        if not match:
            continue
        provider, url = match.groups()
        try:
            u = urlsplit(url)
            port = u.port
        except ValueError:
            continue
        if (not u.hostname or "." not in u.hostname or u.username or u.password
                or port not in (None, 443) or url in seen):
            continue
        seen.add(url)
        routes.append({"kind": "pubmed_full_text_link", "provider": provider,
                       "url": url, "source_pmid": pmid, "source_doi": doi,
                       "source_url": source_url, "source_section": "Full Text Sources",
                       "availability": "not_checked", "reading_level": "not_read",
                       "destination_identity": "not_verified"})
    if not routes:
        raise ValueError("No usable saved LinkOut links; availability remains unknown")
    return {"pmid": pmid, "doi": doi, "reading_routes": routes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scrape", type=Path)
    parser.add_argument("--pmid", required=True)
    parser.add_argument("--doi", required=True)
    args = parser.parse_args()
    raw = args.scrape.read_bytes()
    result = extract(json.loads(raw), args.pmid, args.doi)
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

Pass an untried `reading_routes[].url` to the consumer's existing permitted web
reader; do not repeat a failed URL or bypass access controls. Confirm the
returned article's DOI/title and actual body sections before promoting the route
to a body read. A link, open-access label or HTTP 200 alone is insufficient.
Preserve the original abstract-only run, then record the later source, time,
reading level and any newly supported methods separately. This recipe performs
no network calls and does not install itself into other research agents; the
consumer must explicitly use it. It does not change the site's article identity
or `primary_sources` exports.

### Follow a selected paper to formal comments and corrections

For a Methods or Discussion question where interpretation, event counting, analysis populations or later corrections matter, inspect the already selected original paper's PubMed XML for `MedlineCitation/CommentsCorrectionsList`. Retain the selected paper, original research need, XML source/hash and each associated record's raw `RefType`, PMID, `RefSource` and optional note. Select the associated correspondence or correction for its substantive contribution to that question, and retain competing interpretations. Reuse the consumer's existing lawful PubMed/publisher reading route when it explicitly continues to those records.

Keep the relationship's direction. `CommentIn` identifies a comment on the current paper; a correspondence record's `CommentOn` identifies the paper being discussed. Preserve correction/retraction relationship types as returned. These typed associations are not citation counts. See NLM's [CommentsCorrections element](https://dtd.nlm.nih.gov/ncbi/pubmed/doc/out/250101/el-CommentsCorrections.html) and [comment/correction guidance](https://pubmed.ncbi.nlm.nih.gov/help/#comment-correction).

Keep each PMID record with its authors, pages, formal DOI and any publisher segment identifier before joining work representations. Several letters and a reply can share one DOI while retaining distinct PMIDs, author lists and page ranges. Preserve those records and their writing roles; they do not constitute several trials or independent replications. A missing PMID remains `null`; free-text references do not supply an invented identifier.

Save the following standard-library code as `extract_pubmed_relations.py` in your existing working directory. It reads one already saved PubMed article XML file and prints JSON. Run it once for the selected papers' XML, then for any associated-record XML the consumer has actually obtained. It preserves raw relation types and record identities; shared-DOI groups use case-insensitive keys and are diagnostic only; each raw DOI value is retained.

```sh
python -X utf8 -B extract_pubmed_relations.py selected-papers.xml
python -X utf8 -B extract_pubmed_relations.py associated-records.xml
```

```python
"""Extract typed PubMed relations from one already-saved XML file; no network."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def text(node):
    return ("".join(node.itertext()).strip() or None) if node is not None else None


def extract(raw):
    root = ET.fromstring(raw)  # ElementTree does not fetch the external PubMed DTD.
    if root.tag not in ("PubmedArticleSet", "PubmedArticle"):
        raise ValueError("Expected PubmedArticleSet or PubmedArticle XML")
    articles = [root] if root.tag == "PubmedArticle" else root.findall("./PubmedArticle")
    records = []
    for index, item in enumerate(articles, 1):
        article = item.find("./MedlineCitation/Article")
        ids = [{"type": n.get("IdType"), "value": text(n)}
               for n in item.findall("./PubmedData/ArticleIdList/ArticleId")]
        locations = [{"type": n.get("EIdType"), "valid": n.get("ValidYN"), "value": text(n)}
                     for n in article.findall("./ELocationID")] if article is not None else []
        dois = [x["value"] for x in ids if x["type"] == "doi" and x["value"]]
        dois += [x["value"] for x in locations
                 if x["type"] == "doi" and x["valid"] != "N" and x["value"]]
        records.append({
            "record_index": index,
            "pmid": text(item.find("./MedlineCitation/PMID")),
            "title": text(item.find("./MedlineCitation/Article/ArticleTitle")),
            "authors": [{tag: text(a.find(tag)) for tag in
                         ("LastName", "ForeName", "Initials", "Suffix", "CollectiveName")}
                        for a in item.findall("./MedlineCitation/Article/AuthorList/Author")],
            "journal": text(item.find("./MedlineCitation/Article/Journal/Title")),
            "volume": text(item.find("./MedlineCitation/Article/Journal/JournalIssue/Volume")),
            "issue": text(item.find("./MedlineCitation/Article/Journal/JournalIssue/Issue")),
            "pagination": {tag: text(item.find("./MedlineCitation/Article/Pagination/" + tag))
                           for tag in ("MedlinePgn", "StartPage", "EndPage")},
            "dois": list(dict.fromkeys(dois)),
            "article_ids": ids, "elocation_ids": locations,
            "publication_types": [text(n) for n in item.findall(
                "./MedlineCitation/Article/PublicationTypeList/PublicationType")],
            "comments_corrections": [
                {"RefType": n.get("RefType"), "PMID": text(n.find("PMID")),
                 "RefSource": text(n.find("RefSource")), "Note": text(n.find("Note"))}
                for n in item.findall("./MedlineCitation/CommentsCorrectionsList/CommentsCorrections")]
        })
    relations = [edge for row in records for edge in row["comments_corrections"]]
    groups = defaultdict(list)
    for row in records:
        for doi in dict.fromkeys(value.casefold() for value in row["dois"]):
            groups[doi].append({"record_index": row["record_index"], "pmid": row["pmid"]})
    return {"records": records, "summary": {
        "record_count": len(records), "relation_count": len(relations),
        "relation_types": dict(Counter(edge["RefType"] for edge in relations)),
        "missing_related_pmids": sum(edge["PMID"] is None for edge in relations),
        "shared_doi_records": {doi: rows for doi, rows in groups.items() if len(rows) > 1}
    }}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=Path)
    args = parser.parse_args()
    raw = args.xml.read_bytes()
    result = extract(raw)
    result["input"] = str(args.xml.resolve())
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

This snippet supports `PubmedArticleSet`/`PubmedArticle` XML and performs no network requests. Record metadata extraction, abstract/body reading and material use in a draft separately. Read the available communication/correction itself before relying on its substantive argument; preserve its own genre, source locator and formal citation. A metadata link alone establishes an association. The consumer must explicitly choose and execute this workflow with its allowed tools; publication of this recipe does not install it in external research agents or demonstrate natural adoption.
