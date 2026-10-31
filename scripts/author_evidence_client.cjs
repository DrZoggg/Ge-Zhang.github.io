#!/usr/bin/env node
/* Opt-in, read-only consumer of the public author-maintained evidence export.
 * This is not a search provider, MCP server, medical answer generator or proof
 * of natural discovery. Query text stays local; --live downloads two fixed URLs.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const MiniSearch = require('../assets/vendor/minisearch-7.2.0/minisearch.js');
const {createEngine} = require('../assets/evidence-search.js');

const ROOT = path.resolve(__dirname, '..');
const ORIGIN = 'https://drgezhang.com';
const PATHS = {questions:'research/questions.json', search:'assets/evidence-search.json'};
const MAX_BYTES = 2 * 1024 * 1024;
const TIMEOUT_MS = 15000;
const SOURCE_KIND = 'author_maintained_supplemental_evidence';
const clone = value => JSON.parse(JSON.stringify(value));
const digest = text => crypto.createHash('sha256').update(text.replace(/\r\n/g, '\n'), 'utf8').digest('hex');

function parseDataset(text, label) {
  const value = JSON.parse(text);
  if (!value || typeof value !== 'object') throw Error('Invalid dataset: ' + label);
  return value;
}

function loadLocal(root = ROOT) {
  const data = {}, datasets = {};
  for (const [key, relative] of Object.entries(PATHS)) {
    const bytes = fs.readFileSync(path.join(root, relative));
    if (bytes.length > MAX_BYTES) throw Error('Local dataset exceeds 2 MiB: ' + relative);
    const text = new TextDecoder('utf-8', {fatal:true}).decode(bytes);
    data[key] = parseDataset(text, relative);
    datasets[key] = {source:relative, sha256_lf:digest(text), mode:'local_snapshot'};
  }
  return {...data, retrieval:{mode:'local_snapshot', retrieved_at:new Date().toISOString(), datasets}};
}

async function fetchDataset(relative, fetchImpl = globalThis.fetch) {
  if (!Object.values(PATHS).includes(relative)) throw Error('Only fixed public export paths are allowed');
  const url = ORIGIN + '/' + relative;
  const response = await fetchImpl(url, {redirect:'error', signal:AbortSignal.timeout(TIMEOUT_MS),
    headers:{Accept:'application/json'}});
  if (!response.ok) throw Error('Public export returned HTTP ' + response.status + ': ' + relative);
  // No arbitrary redirects, alternate hosts, credentials or query parameters.
  if (response.url !== url || new URL(response.url).origin !== ORIGIN) throw Error('Unexpected public export URL');
  if (!/^application\/json(?:;|$)/i.test(response.headers.get('content-type') || '')) throw Error('Public export is not JSON');
  const declared = Number(response.headers.get('content-length'));
  if (Number.isFinite(declared) && declared > MAX_BYTES) throw Error('Public export exceeds 2 MiB');
  if (!response.body) throw Error('Public export has no body');
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    for (;;) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BYTES) { await reader.cancel(); throw Error('Public export exceeds 2 MiB'); }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const text = new TextDecoder('utf-8', {fatal:true}).decode(Buffer.concat(chunks));
  return {value:parseDataset(text, relative), metadata:{source:url, sha256_lf:digest(text), mode:'public_https',
    etag:response.headers.get('etag'), last_modified:response.headers.get('last-modified'), http_status:response.status}};
}

async function loadLive(fetchImpl = globalThis.fetch) {
  const entries = await Promise.all(Object.entries(PATHS).map(async ([key, relative]) => [key, await fetchDataset(relative, fetchImpl)]));
  const data = {}, datasets = {};
  for (const [key, loaded] of entries) { data[key] = loaded.value; datasets[key] = loaded.metadata; }
  return {...data, retrieval:{mode:'public_https', retrieved_at:new Date().toISOString(), datasets}};
}

function createClient(questions, searchCorpus, retrieval = {}) {
  if (questions.version !== 1 || questions.discovery_version !== 2 || !Array.isArray(questions.works)
      || !Array.isArray(questions.all_questions) || searchCorpus.version !== 1 || !Array.isArray(searchCorpus.documents)) {
    throw Error('Unsupported public discovery contract');
  }
  const works = new Map(), qas = new Map(), workByUrl = new Map(), qaByUrl = new Map();
  for (const work of questions.works) {
    if (!work.id || works.has(work.id) || typeof work.title !== 'string' || !Array.isArray(work.limitations)
        || !Array.isArray(work.key_findings)) throw Error('Invalid or duplicate work identity');
    if (work.evidence_status === 'reviewed_v2' && (!work.evidence_scope || !Array.isArray(work.evidence_scope.does_not_establish))) {
      throw Error('Reviewed work lacks complete evidence scope');
    }
    if (work.evidence_status === 'reviewed_v2' && (!work.study_profile
        || work.study_profile.profile_type !== work.profile_type
        || work.study_profile_source !== work.gold_source + '#/study_profile'
        || (work.model_profile && work.model_profile_source !== work.gold_source + '#/model_profile')
        || work.key_findings.some(ref => typeof ref.claim !== 'string'
          || typeof ref.context !== 'string' || !Array.isArray(ref.evidence)))) {
      throw Error('Reviewed work lacks complete source-bound profile or findings; refresh the public export');
    }
    if (!work.paper_url || workByUrl.has(work.paper_url)) throw Error('Invalid or duplicate canonical work URL');
    works.set(work.id, work); workByUrl.set(work.paper_url, work);
  }
  for (const qa of questions.all_questions) {
    const work = works.get(qa.work_id);
    if (!qa.id || qas.has(qa.id) || !work || work.evidence_status !== 'reviewed_v2'
        || typeof qa.question !== 'string' || typeof qa.answer !== 'string' || !Array.isArray(qa.evidence_refs)) {
      throw Error('Invalid question-to-work relationship');
    }
    const expectedUrl = work.paper_url + '#qa-' + qa.qa_index;
    const refs = new Set(work.key_findings.map(ref => ref.id));
    if (qa.answer_url !== expectedUrl || qaByUrl.has(qa.answer_url)
        || qa.evidence_refs.some(ref => !refs.has(ref))
        || qa.evidence_refs_status !== (qa.evidence_refs.length ? 'resolved' : 'not_encoded')
        || crypto.createHash('sha256').update(qa.answer, 'utf8').digest('hex') !== qa.answer_sha256) {
      throw Error('Invalid question evidence, anchor or answer hash');
    }
    qas.set(qa.id, qa); qaByUrl.set(qa.answer_url, qa);
  }
  // Independent static files may be cached at different deployment versions.
  // Refuse a mixed snapshot rather than joining a stale search hit to an answer.
  const seenQaDocuments = new Set();
  for (const document of searchCorpus.documents) {
    if (document.result_kind !== 'paper' || document.category !== 'Q&A') continue;
    const qa = qaByUrl.get(document.url);
    const work = qa && works.get(qa.work_id);
    if (!qa || seenQaDocuments.has(document.url)
        || document.text !== qa.question + '\n' + qa.answer
        || document.doi !== work.doi || document.title !== work.title) {
      throw Error('Search corpus and reviewed Q&A export do not match: stale, duplicate or unknown answer route');
    }
    seenQaDocuments.add(document.url);
  }
  if (seenQaDocuments.size !== qas.size || [...qaByUrl.keys()].some(url => !seenQaDocuments.has(url))) {
    throw Error('Search corpus and reviewed Q&A export do not match: missing reviewed answer route');
  }
  // Compare the shared scientific context as well as answers. Profiles are
  // carried only by the single questions snapshot; they are not joined from
  // search excerpts. No source or denominator is inferred from nearest text.
  for (const work of works.values()) {
    if (work.evidence_status !== 'reviewed_v2') continue;
    const shared = [
      ...work.key_findings.map(ref => ({url:ref.evidence_url,
        categories:['Key finding','Key argument'],
        text:[ref.claim,ref.context,...ref.evidence.flatMap(row => [row.label,row.value]),ref.source_locator].filter(Boolean).join('\n')})),
      {url:work.paper_url + '#ev-scope',categories:['Evidence scope — supports'],text:work.evidence_scope.supports.join('\n')},
      {url:work.paper_url + '#ev-scope',categories:['Limitations — does not establish'],text:work.evidence_scope.does_not_establish.join('\n')},
      {url:work.paper_url + '#ev-scope',categories:['Limitations'],text:work.limitations.join('\n')}
    ];
    for (const expected of shared) {
      const matches = searchCorpus.documents.filter(doc => doc.result_kind === 'paper'
        && doc.url === expected.url && expected.categories.includes(doc.category));
      if (matches.length !== 1 || matches[0].text !== expected.text
          || matches[0].doi !== work.doi || matches[0].title !== work.title) {
        throw Error('Search corpus and reviewed work context do not match: stale or missing finding/scope');
      }
    }
  }
  const engine = createEngine(MiniSearch, searchCorpus);
  function evidenceUnit(work) {
    return {id:work.doi ? 'doi:' + work.doi : 'site_record:' + work.id,
      doi:work.doi || null, multiple_representations_are_not_independent_studies:true};
  }
  function fetchRecord(id) {
    const qa = qas.get(id) || null;
    const work = qa ? works.get(qa.work_id) : works.get(id);
    if (!work) throw Error('Unknown stable evidence ID: ' + id);
    const supporting = qa ? work.key_findings.filter(ref => qa.evidence_refs.includes(ref.id)) : [];
    return clone({
      id, work_id:work.id, source_kind:SOURCE_KIND,
      source_description:'Author-maintained explanation of an existing work; cite the original article DOI for the formal research publication.',
      evidence_unit:evidenceUnit(work),
      question:qa ? qa.question : null, answer:qa ? qa.answer : null,
      available_questions:qa ? [] : questions.all_questions.filter(row => row.work_id === work.id)
        .map(row => ({id:row.id, question:row.question, answer_url:row.answer_url,
          evidence_refs_status:row.evidence_refs_status})),
      publication:{title:work.title, doi:work.doi || null, type:work.type, year:work.year, journal:work.journal,
        authors:work.authors, paper_geo_status:work.paper_geo_status, evidence_status:work.evidence_status},
      study_type:{publication_type:work.type, profile_type:work.profile_type || null,
        narrative_genre:work.narrative_genre || null, scientific_role:work.scientific_role || null,
        evidence_position:work.evidence_position || null},
      study_profile:work.study_profile || null,
      model_profile:work.model_profile || null,
      evidence_scope:work.evidence_scope, available_scope:work.scope || null,
      limitations:work.limitations,
      evidence_refs:qa ? qa.evidence_refs : [], evidence_refs_status:qa ? qa.evidence_refs_status : 'not_applicable',
      supporting_evidence:supporting,
      work_key_findings:qa ? [] : work.key_findings,
      links:{canonical_paper_url:work.paper_url, answer_url:qa ? qa.answer_url : null,
        markdown_url:work.markdown_url, original_doi_url:work.doi_url || null,
        publisher_url:work.publisher_url || null, citation_bibtex_url:work.citation_bibtex_url || null,
        citation_ris_url:work.citation_ris_url || null, citation_csl_json_url:work.citation_csl_json_url || null,
        gold_source_url:work.gold_source_url || null},
      provenance:work.provenance || null,
      source_pointers:{gold_source:work.gold_source || null, scope_source:work.scope_source || null,
        study_profile_source:work.study_profile_source || null,
        model_profile_source:work.model_profile_source || null,
        question_source:qa ? qa.question_source : null, answer_source:qa ? qa.answer_source : null},
      content_version:{...retrieval, gold_content_sha256_from_export:work.gold_content_sha256 || null,
        answer_sha256:qa ? qa.answer_sha256 : null, answer_sha256_verified:Boolean(qa)},
      interpretation:'Text and context are returned unchanged. Retrieval relevance does not validate a query premise or establish treatment benefit.'
    });
  }
  function searchRecords(query, limit = 5) {
    if (typeof query !== 'string' || !query.trim()) throw Error('A non-empty query is required');
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw Error('Invalid display limit');
    const result = engine(query);
    const format = hit => {
      const work = workByUrl.get(hit.url.split('#')[0]);
      const qa = qaByUrl.get(hit.url);
      return {id:qa ? qa.id : work ? work.id : null, record_kind:qa ? 'reviewed_question' : work ? 'work' : 'guide',
        title:hit.title, doi:hit.doi || null, publication_type:work ? work.type : null,
        evidence_status:work ? work.evidence_status : null, evidence_unit:work ? evidenceUnit(work) : null,
        url:hit.url, matched_section:hit.category, matched_text:hit.text,
        limitation:Boolean(hit.limitation), match_group:hit.matchGroup,
        fetch_context_available:Boolean(work),
        ...(hit.queryCoverage ? {query_coverage:{...clone(hit.queryCoverage),
          interpretation:'Partial lexical matching only. Unmatched terms may include a different entity or intervention; verify them before using this record. Matched terms do not validate the query premise. This is not entity recognition, semantic coverage or proof that absent terms are scientifically false.'}} : {})};
    };
    return clone({source_kind:SOURCE_KIND, channel:'explicitly_connected_readonly_client', query,
      query_transmitted_to_source:false, natural_discovery_proven:false,
      ranking:'MiniSearch question/answer lexical relevance with English word-form normalization; not evidence strength or a generated scientific answer',
      best_matches:result.bestMatches.slice(0,limit).map(format),
      broader_related:result.broaderRelated.slice(0,limit).map(format),
      total_best_matches:result.bestMatches.length, total_broader_related:result.broaderRelated.length,
      content_version:retrieval,
      context_requirement:'Use fetch with a returned stable ID to retain the full paper identity, scope, limitations and encoded locators. A guide with null ID is navigation, not another research study.'});
  }
  return {search:searchRecords, fetch:fetchRecord};
}

async function main(argv = process.argv.slice(2)) {
  const live = argv.includes('--live');
  const args = argv.filter(arg => arg !== '--live');
  if (!args.length || args[0] === '--help' || args[0] === '-h') {
    console.log('Read-only author evidence client (explicit opt-in; not natural AI adoption)\n'
      + '  node scripts/author_evidence_client.cjs search "question, concept or DOI" [--live]\n'
      + '  node scripts/author_evidence_client.cjs fetch <stable-question-or-work-id> [--live]\n'
      + 'Default: current repository JSON snapshot. --live: two fixed public HTTPS JSON exports, no query upload.');
    return;
  }
  if (!['search','fetch'].includes(args[0]) || args.length !== 2 || args.some(arg => arg.startsWith('--'))) {
    throw Error('Expected search <query> or fetch <stable-id>, with optional --live');
  }
  const loaded = live ? await loadLive() : loadLocal();
  const client = createClient(loaded.questions, loaded.search, loaded.retrieval);
  console.log(JSON.stringify(args[0] === 'search' ? client.search(args[1]) : client.fetch(args[1]), null, 2));
}

module.exports = {createClient, loadLocal, loadLive, fetchDataset, digest, MAX_BYTES, main};
if (require.main === module) main().catch(error => {
  console.error(JSON.stringify({error:error.message, source_kind:SOURCE_KIND, no_answer_generated:true}));
  process.exitCode = 1;
});
