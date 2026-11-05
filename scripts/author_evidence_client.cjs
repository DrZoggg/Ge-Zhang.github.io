#!/usr/bin/env node
/* Opt-in, read-only consumer of the public author-maintained evidence export.
 * This is not a search provider, MCP server, medical answer generator or proof
 * of natural discovery. Query text stays local; --live downloads two fixed URLs.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {setTimeout: wait} = require('node:timers/promises');
const MiniSearch = require('../assets/vendor/minisearch-7.2.0/minisearch.js');
const {createEngine} = require('../assets/evidence-search.js');

const ROOT = path.resolve(__dirname, '..');
const ORIGIN = 'https://drgezhang.com';
const PATHS = {questions:'research/questions.json', search:'assets/evidence-search.json'};
const MAX_BYTES = 2 * 1024 * 1024;
const TIMEOUT_MS = 15000;
const RETRY_DELAY_MS = 250;
const MAX_RETRY_BODY_BYTES = 8192;
const SOURCE_KIND = 'author_maintained_supplemental_evidence';
const clone = value => JSON.parse(JSON.stringify(value));
const digest = text => crypto.createHash('sha256').update(text.replace(/\r\n/g, '\n'), 'utf8').digest('hex');

function validateAuthorEvidenceNote(work) {
  if (!Object.hasOwn(work, 'author_evidence_note')) return; // Older export snapshots remain readable.
  const note = work.author_evidence_note;
  const object = value => value && typeof value === 'object' && !Array.isArray(value);
  const keys = (value, expected) => object(value)
    && Object.keys(value).sort().join(',') === expected.slice().sort().join(',');
  const plain = (value, maximum) => typeof value === 'string' && value.length > 0
    && value.length <= maximum && value === value.trim() && !/[\r\n<>]/.test(value);
  const invalid = () => { throw Error('Invalid source-bound author evidence note: ' + work.id); };
  if (work.evidence_status !== 'limited' || work.paper_geo_status === 'v2'
      || work.type === 'Patent' || typeof work.doi !== 'string' || !work.doi
      || !keys(note, ['reviewed_on', 'source_record', 'sections'])) invalid();
  const pointer = 'data/limited_evidence.json#/papers/' + work.doi.replace(/~/g, '~0').replace(/\//g, '~1');
  const day = note.reviewed_on;
  const parsedDay = typeof day === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(day)
    && !day.startsWith('0000-') ? Date.parse(day + 'T00:00:00Z') : NaN;
  if (note.source_record !== pointer || !Number.isFinite(parsedDay)
      || new Date(parsedDay).toISOString().slice(0, 10) !== day
      || !Array.isArray(note.sections) || note.sections.length < 1 || note.sections.length > 4) invalid();
  for (const section of note.sections) {
    if (!keys(section, ['heading', 'text', 'source_url', 'source_locator'])
        || !plain(section.heading, 100) || !plain(section.text, 1800)
        || !plain(section.source_locator, 600) || typeof section.source_url !== 'string') invalid();
    let url;
    try { url = new URL(section.source_url); } catch { invalid(); }
    if (url.protocol !== 'https:' || !url.hostname || url.username || url.password) invalid();
  }
}

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

function retryDelay(value) {
  if (value === null) return RETRY_DELAY_MS;
  if (/^\d+$/.test(value)) {
    const milliseconds = Number(value) * 1000;
    if (Number.isSafeInteger(milliseconds)) return milliseconds;
  }
  // Normalize the two obsolete HTTP-date forms before strict calendar checking.
  const normalized = value.replace(/^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (\d{2})-([A-Za-z]{3})-(\d{2}) (\d{2}:\d{2}:\d{2}) GMT$/,
    (_, weekday, day, month, shortYear, time) => {
      const currentYear = new Date().getUTCFullYear();
      let year = Math.floor(currentYear / 100) * 100 + Number(shortYear);
      if (year > currentYear + 50) year -= 100;
      return `${weekday.slice(0, 3)}, ${day} ${month} ${year} ${time} GMT`;
    }).replace(/^([A-Za-z]{3}) ([A-Za-z]{3}) ([ \d]\d) (\d{2}:\d{2}:\d{2}) (\d{4})$/,
      (_, weekday, month, day, time, year) => `${weekday}, ${day.trim().padStart(2, '0')} ${month} ${year} ${time} GMT`);
  const httpDate = /^[A-Za-z]{3}, \d{2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} GMT$/;
  const timestamp = httpDate.test(normalized) ? Date.parse(normalized) : NaN;
  if (Number.isFinite(timestamp) && new Date(timestamp).toUTCString() === normalized) {
    return Math.max(0, timestamp - Date.now());
  }
  throw Error('Invalid Retry-After; public export HTTP 503 was not retried');
}

async function releaseErrorBody(response) {
  if (response.body) await response.body.cancel();
}

async function ordinary503(response, signal) {
  const get = name => response.headers.get(name) || '';
  if (get('cf-mitigated') || get('www-authenticate')
      || /challenge|captcha/i.test(get('x-amzn-waf-action'))) {
    await releaseErrorBody(response);
    return false;
  }
  if (!response.body) return true;
  if (!/^(?:application\/json|text\/(?:plain|html))(?:;|$)/i.test(get('content-type'))) {
    await releaseErrorBody(response);
    return false;
  }
  // A small complete error message can be classified without executing it.
  // Truncated/binary bodies and security interstitials get no second request.
  const reader = response.body.getReader(), chunks = [];
  let size = 0;
  try {
    for (;;) {
      signal.throwIfAborted();
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_RETRY_BODY_BYTES) { await reader.cancel(); return false; }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  let message;
  try { message = new TextDecoder('utf-8', {fatal:true}).decode(Buffer.concat(chunks)); }
  catch { return false; }
  const ordinaryHtml = !/^text\/html(?:;|$)/i.test(get('content-type'))
    || /503|service (?:temporarily )?unavailable|temporarily unavailable|temporary outage/i.test(message);
  return ordinaryHtml
    && !/captcha|challenge|verify.{0,40}human|unusual traffic|access denied|automated (?:requests|traffic)|enable.{0,30}(?:javascript|cookies)|<script\b|<form\b|<iframe\b/i.test(message);
}

async function fetchDataset(relative, fetchImpl = globalThis.fetch) {
  if (!Object.values(PATHS).includes(relative)) throw Error('Only fixed public export paths are allowed');
  const url = ORIGIN + '/' + relative;
  const deadline = performance.now() + TIMEOUT_MS, signal = AbortSignal.timeout(TIMEOUT_MS);
  const options = {redirect:'error', signal, headers:{Accept:'application/json'}};
  let response, recovery;
  for (let attempt = 1; attempt <= 2; attempt++) {
    signal.throwIfAborted();
    if (performance.now() >= deadline) throw Error('Public export deadline expired: ' + relative);
    response = await fetchImpl(url, options);
    if (response.ok) break;
    if (response.status !== 503 || attempt === 2) {
      await releaseErrorBody(response);
      throw Error('Public export returned HTTP ' + response.status + ': ' + relative
        + (attempt === 2 ? ' (after one bounded retry)' : ''));
    }
    if (response.url !== url) {
      await releaseErrorBody(response);
      throw Error('Unexpected public export URL');
    }
    let delay;
    try { delay = retryDelay(response.headers.get('retry-after')); }
    catch (error) { await releaseErrorBody(response); throw error; }
    if (delay >= deadline - performance.now()) {
      await releaseErrorBody(response);
      throw Error('Retry-After exceeds remaining public export deadline: ' + relative);
    }
    if (!await ordinary503(response, signal)) throw Error('Public export HTTP 503 safety state is unclear; not retried');
    if (delay >= deadline - performance.now()) throw Error('Retry-After exceeds remaining public export deadline: ' + relative);
    await wait(delay, undefined, {signal});
    recovery = {attempts:2, initial_http_status:503, delay_ms:delay,
      retry_after:response.headers.get('retry-after')};
  }
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
    etag:response.headers.get('etag'), last_modified:response.headers.get('last-modified'), http_status:response.status,
    ...(recovery ? {recovery} : {})}};
}

async function loadLive(fetchImpl = globalThis.fetch) {
  const entries = await Promise.all(Object.entries(PATHS).map(async ([key, relative]) => [key, await fetchDataset(relative, fetchImpl)]));
  const data = {}, datasets = {};
  for (const [key, loaded] of entries) { data[key] = loaded.value; datasets[key] = loaded.metadata; }
  return {...data, retrieval:{mode:'public_https', retrieved_at:new Date().toISOString(), datasets}};
}

function primarySources(work) {
  const issues = [], routes = [];
  const present = value => value !== null && value !== undefined && value !== '';
  // Read explicit identity/link fields and reviewed same-DOI repository routes.
  // Never infer article identity from arbitrary source URLs or display labels.
  const provenance = Array.isArray(work.provenance) ? work.provenance
    .map((value,index) => ({value,path:`work.provenance[${index}]`}))
    : [{value:work.provenance,path:'work.provenance'}];
  const records = [{value:work,path:'work'}, ...provenance]
    .filter(row => row.value && typeof row.value === 'object' && !Array.isArray(row.value));
  const fields = key => records.filter(row => present(row.value[key]))
    .map(row => ({value:row.value[key],field:row.path + '.' + key}));
  const issue = (field,reason,source_fields) => issues.push({field,reason,...(source_fields ? {source_fields} : {})});
  function https(value) {
    if (typeof value !== 'string' || !value || value !== value.trim()) return null;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && !url.username && !url.password ? url : null;
    } catch { return null; }
  }
  const idFormat = {pmid:/^[1-9][0-9]{0,9}$/,pmcid:/^PMC[1-9][0-9]{0,9}$/i};
  function identifier(key,urlKey) {
    const claims = [];
    for (const row of fields(key)) {
      const value = typeof row.value === 'string' ? row.value.trim()
        : Number.isSafeInteger(row.value) && row.value > 0 ? String(row.value) : '';
      if (!idFormat[key].test(value)) issue(row.field,'invalid_identifier');
      else claims.push({value:key === 'pmcid' ? value.toUpperCase() : value,field:row.field});
    }
    for (const row of fields(urlKey)) {
      const url = https(row.value);
      const match = url && !url.search && !url.hash && (key === 'pmid'
        ? url.hostname === 'pubmed.ncbi.nlm.nih.gov' && url.pathname.match(/^\/([1-9][0-9]{0,9})\/?$/)
        : url.hostname === 'pmc.ncbi.nlm.nih.gov' && url.pathname.match(/^\/articles\/(PMC[1-9][0-9]{0,9})\/?$/i));
      if (!match) issue(row.field,'invalid_database_url');
      else claims.push({value:key === 'pmcid' ? match[1].toUpperCase() : match[1],field:row.field});
    }
    const values = [...new Set(claims.map(row => row.value))];
    if (values.length > 1) {
      issue(key,'conflicting_identifiers',claims.map(row => row.field));
      return {value:null,source_fields:[]};
    }
    return {value:values[0] || null,source_fields:claims.map(row => row.field)};
  }
  const pmid = identifier('pmid','pubmed_url'), pmcid = identifier('pmcid','pmc_url');
  const pubmed = pmid.value ? `https://pubmed.ncbi.nlm.nih.gov/${pmid.value}/` : null;
  const pmc = pmcid.value ? `https://pmc.ncbi.nlm.nih.gov/articles/${pmcid.value}/` : null;
  if (pubmed) routes.push({provider:'PubMed',kind:'database_record',url:pubmed,source_fields:pmid.source_fields,availability:'not_checked'});
  if (pmc) routes.push({provider:'PMC',kind:'full_text_archive',url:pmc,source_fields:pmcid.source_fields,availability:'not_checked'});
  const publisherFields = fields('publisher_url'), validPublishers = [];
  for (const row of publisherFields) {
    const url = https(row.value);
    if (!url) { issue(row.field,'invalid_https_url'); continue; }
    if (['pubmed.ncbi.nlm.nih.gov','pmc.ncbi.nlm.nih.gov'].includes(url.hostname)) {
      issue(row.field,'database_url_in_publisher_field'); continue;
    }
    if (['doi.org','dx.doi.org'].includes(url.hostname)) {
      let doi = null;
      try { doi = decodeURIComponent(url.pathname.slice(1)); } catch {}
      if (!doi) { issue(row.field,'invalid_doi_url'); continue; }
      if (typeof work.doi !== 'string' || doi.toLowerCase() !== work.doi.toLowerCase()) {
        issue(row.field,'conflicting_doi_url'); continue;
      }
    }
    validPublishers.push({...row,url:url.href});
  }
  // The explicit work identity field is the preferred source. Only use a
  // provenance fallback when that field is missing or invalid; do not guess
  // between different fallback locations.
  let publisher = validPublishers.find(row => row.field === 'work.publisher_url') || null;
  if (!publisher) {
    const alternatives = [...new Set(validPublishers.map(row => row.url))];
    if (alternatives.length === 1) publisher = validPublishers[0];
    else if (alternatives.length > 1) issue('publisher_url','conflicting_fallback_urls',validPublishers.map(row => row.field));
  }
  if (publisher) {
    const resolver = ['doi.org','dx.doi.org'].includes(new URL(publisher.url).hostname);
    routes.push({provider:resolver ? 'DOI' : 'Publisher',kind:resolver ? 'doi_resolver' : 'publisher_source',
      url:publisher.url,source_fields:[publisher.field],availability:'not_checked'});
  }
  for (const row of provenance) {
    if (!row.value || typeof row.value !== 'object' || !Object.hasOwn(row.value, 'reading_route')) continue;
    const route = row.value.reading_route, url = https(row.value.url);
    if (!route || typeof route !== 'object' || Array.isArray(route)
        || Object.keys(route).sort().join(',') !== 'doi,kind,version'
        || route.kind !== 'institutional_repository_pdf'
        || typeof work.doi !== 'string' || typeof route.doi !== 'string'
        || !/^10\.\d{4,9}\/\S+$/.test(route.doi) || route.doi.toLowerCase() !== work.doi.toLowerCase()
        || !['journal_pre_proof','accepted_manuscript','version_of_record'].includes(route.version)
        || !url || !url.pathname.toLowerCase().endsWith('.pdf') || url.search || url.hash) {
      issue(row.path + '.reading_route','invalid_same_work_repository_route');
      continue;
    }
    if (routes.some(existing => existing.url === url.href && existing.version === route.version)) continue;
    routes.push({provider:'Institutional repository',kind:route.kind,url:url.href,
      doi:route.doi,version:route.version,
      source_fields:[row.path + '.url',row.path + '.reading_route'],availability:'not_checked'});
  }
  const copyKey = 'researchgate_author_shared_copy_url';
  for (const row of provenance) {
    if (!present(row.value?.[copyKey])) continue;
    const field = row.path + '.' + copyKey;
    const url = https(row.value[copyKey]), doiUrl = row.value.doi_url;
    // Surface only the reviewed provenance role, bound to this work's formal DOI.
    if (typeof work.doi !== 'string' || !/^10\.\d{4,9}\/\S+$/.test(work.doi)
        || typeof doiUrl !== 'string' || doiUrl.toLowerCase() !== 'https://doi.org/' + work.doi.toLowerCase()
        || !url || url.hostname !== 'www.researchgate.net' || url.port || url.search || url.hash
        || !/^\/publication\/[1-9]\d*(?:_[A-Za-z0-9_-]+)?\/?$/.test(url.pathname)) {
      issue(field,'invalid_same_work_author_shared_route');
      continue;
    }
    if (routes.some(existing => existing.kind === 'author_shared_copy' && existing.url === url.href)) continue;
    routes.push({provider:'ResearchGate',kind:'author_shared_copy',url:url.href,doi:work.doi,
      source_fields:[field,row.path + '.doi_url'],availability:'not_checked'});
  }
  if (pmcid.value) routes.push({provider:'PMC',kind:'full_text_xml_api',
    url:`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=${pmcid.value.slice(3)}&retmode=xml`,
    source_fields:pmcid.source_fields,availability:'not_checked'});
  return {identifiers:{pmid:pmid.value,pmcid:pmcid.value},reading_routes:routes,metadata_issues:issues,
    links:{pubmed_url:pubmed,pmc_url:pmc,publisher_url:publisher ? publisher.url : null}};
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
    validateAuthorEvidenceNote(work);
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
    const primary = primarySources(work);
    return clone({
      id, work_id:work.id, source_kind:SOURCE_KIND,
      source_description:'Author-maintained explanation of an existing work; cite the original work using its stated publication type and available identifiers.',
      evidence_unit:evidenceUnit(work),
      publication:{title:work.title, doi:work.doi || null, type:work.type, year:work.year, journal:work.journal,
        authors:work.authors, paper_geo_status:work.paper_geo_status, evidence_status:work.evidence_status},
      question:qa ? qa.question : null, answer:qa ? qa.answer : null,
      evidence_refs:qa ? qa.evidence_refs : [], evidence_refs_status:qa ? qa.evidence_refs_status : 'not_applicable',
      supporting_evidence:supporting,
      work_key_findings:qa ? [] : work.key_findings,
      available_questions:qa ? [] : questions.all_questions.filter(row => row.work_id === work.id)
        .map(row => ({id:row.id, question:row.question, answer_url:row.answer_url,
          evidence_refs_status:row.evidence_refs_status})),
      study_type:{publication_type:work.type, profile_type:work.profile_type || null,
        narrative_genre:work.narrative_genre || null, scientific_role:work.scientific_role || null,
        evidence_position:work.evidence_position || null},
      study_profile:work.study_profile || null,
      model_profile:work.model_profile || null,
      primary_sources:{identifiers:primary.identifiers,reading_routes:primary.reading_routes,metadata_issues:primary.metadata_issues},
      links:{canonical_paper_url:work.paper_url, answer_url:qa ? qa.answer_url : null,
        markdown_url:work.markdown_url, original_doi_url:work.doi_url || null,
        publisher_url:primary.links.publisher_url, pubmed_url:primary.links.pubmed_url, pmc_url:primary.links.pmc_url,
        citation_bibtex_url:work.citation_bibtex_url || null,
        citation_ris_url:work.citation_ris_url || null, citation_csl_json_url:work.citation_csl_json_url || null,
        gold_source_url:work.gold_source_url || null},
      provenance:work.provenance || null,
      source_pointers:{gold_source:work.gold_source || null, scope_source:work.scope_source || null,
        study_profile_source:work.study_profile_source || null,
        model_profile_source:work.model_profile_source || null,
        question_source:qa ? qa.question_source : null, answer_source:qa ? qa.answer_source : null},
      content_version:{...retrieval, gold_content_sha256_from_export:work.gold_content_sha256 || null,
        answer_sha256:qa ? qa.answer_sha256 : null, answer_sha256_verified:Boolean(qa)},
      ...(Object.hasOwn(work, 'author_evidence_note') ? {author_evidence_note:work.author_evidence_note} : {}),
      evidence_scope:work.evidence_scope, available_scope:work.scope || null,
      limitations:work.limitations,
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
