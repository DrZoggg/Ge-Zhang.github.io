# Read-only author evidence client

This is an **explicitly selected supplementary source**, not a general literature
database, MCP service or proof that external AI search engines naturally prefer
this website. It returns existing author-maintained evidence explanations, not a
new independent study. Keep the original DOI as the formal publication identity.

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
2. Inspect `best_matches` and `broader_related` separately. Both indicate text
   relevance; neither proves that the query's clinical or causal premise holds.
3. Call `fetch` with a returned stable ID. A question ID returns its unchanged
   answer and complete paper context. A work ID returns `answer: null`, full
   scope, and `available_questions`; select a relevant existing question before
   fetching an answer. A guide with a null ID is navigation, not another study.
4. Preserve the full scope and provenance while writing. If no suitable answer
   exists, report that gap; do not turn the nearest text match into an answer.

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
- Source pointers, provenance, dataset hashes, available HTTP version metadata,
  Gold hash reported by the export and a locally verified exact-answer hash.
- An evidence-unit identity shared by representations of the same DOI, so the
  author page and publisher record are not counted as two independent studies.

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
