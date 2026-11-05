'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createClient,loadLocal,loadLive,fetchDataset,digest,MAX_BYTES} = require('./author_evidence_client.cjs');

async function run() {
  const networkCalls=[];
  const originalFetch=globalThis.fetch;
  globalThis.fetch=(...args)=>{networkCalls.push(args);throw Error('Unexpected network request in local client');};
  const loaded = loadLocal(), catalog = loaded.questions;
  const client = createClient(catalog, loaded.search, loaded.retrieval);
  const works = new Map(catalog.works.map(work => [work.id,work]));
  function assertXmlRoute(packet) {
    const primary=packet.primary_sources, routes=primary.reading_routes;
    const api=routes.filter(route=>route.kind==='full_text_xml_api');
    if (!primary.identifiers.pmcid) {assert.deepEqual(api,[]);return;}
    assert.equal(api.length,1);assert.equal(routes.at(-1),api[0]);
    const archive=routes.find(route=>route.kind==='full_text_archive');
    assert(archive);assert.deepEqual(api[0].source_fields,archive.source_fields);
    assert.equal(api[0].provider,'PMC');assert.equal(api[0].availability,'not_checked');
    const url=new URL(api[0].url);
    assert.equal(url.origin,'https://eutils.ncbi.nlm.nih.gov');
    assert.equal(url.pathname,'/entrez/eutils/efetch.fcgi');
    assert.equal(url.username,'');assert.equal(url.password,'');assert.equal(url.hash,'');
    assert.deepEqual([...url.searchParams.keys()].sort(),['db','id','retmode']);
    assert.equal(url.searchParams.get('db'),'pmc');assert.equal(url.searchParams.get('retmode'),'xml');
    assert.equal('PMC'+url.searchParams.get('id'),primary.identifiers.pmcid);
    assert.equal(new URL(archive.url).pathname,`/articles/${primary.identifiers.pmcid}/`);
  }
  assert.equal(catalog.works.length, new Set(catalog.works.map(work=>work.id)).size);
  let nonEncoded = 0;
  for (const question of catalog.all_questions) {
    const packet = client.fetch(question.id), work = works.get(question.work_id);
    assertXmlRoute(packet);
    assert.equal(packet.question,question.question);assert.equal(packet.answer,question.answer);
    assert.deepEqual(packet.available_questions,[]);
    assert.equal(packet.publication.title,work.title);assert.equal(packet.publication.doi,work.doi);
    assert.equal(packet.publication.type,work.type);
    assert.equal(packet.study_type.profile_type,work.profile_type);
    assert.deepEqual(packet.evidence_scope,work.evidence_scope);
    assert.deepEqual(packet.limitations,work.limitations);
    assert.deepEqual(packet.provenance,work.provenance);
    assert.deepEqual(packet.study_profile,work.study_profile);
    assert.deepEqual(packet.model_profile,work.model_profile);
    assert.equal(packet.source_pointers.study_profile_source,work.study_profile_source);
    assert.equal(packet.source_pointers.model_profile_source,work.model_profile_source);
    assert.equal(packet.links.answer_url,question.answer_url);
    assert.equal(packet.links.original_doi_url,work.doi_url);
    assert.equal(packet.content_version.answer_sha256,question.answer_sha256);
    assert(packet.content_version.answer_sha256_verified);
    assert.deepEqual(packet.supporting_evidence.map(ref=>ref.id),question.evidence_refs);
    assert(packet.supporting_evidence.every(ref=>typeof ref.source_locator==='string'&&ref.source_locator));
    assert.deepEqual(packet.supporting_evidence,work.key_findings.filter(ref=>question.evidence_refs.includes(ref.id)));
    const order=Object.keys(packet);
    assert(order.indexOf('publication')<order.indexOf('question'));
    assert(order.indexOf('answer')<order.indexOf('supporting_evidence'));
    assert(order.indexOf('supporting_evidence')<order.indexOf('study_profile'));
    assert(order.indexOf('provenance')<order.indexOf('evidence_scope'));
    assert(order.indexOf('source_pointers')<order.indexOf('limitations'));
    if (question.evidence_refs_status==='not_encoded') {
      nonEncoded++;assert.equal(packet.evidence_refs_status,'not_encoded');assert.deepEqual(packet.supporting_evidence,[]);
    }
  }
  assert.equal(nonEncoded,catalog.all_questions.filter(q=>q.evidence_refs_status==='not_encoded').length);
  for (const work of catalog.works) {
    const packet = client.fetch(work.id);
    assertXmlRoute(packet);
    assert.equal(packet.answer,null);assert.equal(packet.question,null);
    assert.deepEqual(packet.available_questions,catalog.all_questions.filter(q=>q.work_id===work.id)
      .map(q=>({id:q.id,question:q.question,answer_url:q.answer_url,evidence_refs_status:q.evidence_refs_status})));
    assert.deepEqual(packet.evidence_scope,work.evidence_scope);
    assert.deepEqual(packet.limitations,work.limitations);
    if (work.evidence_status!=='reviewed_v2') {
      assert.equal(packet.study_profile,null);assert.equal(packet.model_profile,null);
      assert.equal(packet.available_scope,work.scope || null);
      assert.deepEqual(packet.supporting_evidence,[]);
      assert.deepEqual(packet.available_questions,[]);
    }
    if (work.type==='Patent') {
      assert.equal(packet.publication.doi,null);assert.equal(packet.links.original_doi_url,null);
      assert.equal(packet.links.citation_bibtex_url,null);
      assert(packet.evidence_unit.id.startsWith('site_record:'));
    }
  }
  const limitedSource=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/limited_evidence.json'),'utf8')).papers;
  const limitedWorks=catalog.works.filter(work=>work.evidence_status==='limited');
  assert.equal(limitedWorks.length,Object.keys(limitedSource).length);
  assert.equal(limitedWorks.reduce((count,work)=>count+work.author_evidence_note.sections.length,0),
    Object.values(limitedSource).reduce((count,record)=>count+record.sections.length,0));
  for (const work of catalog.works) {
    const packet=client.fetch(work.id);
    if (work.evidence_status!=='limited') {
      assert(!Object.hasOwn(work,'author_evidence_note'));assert(!Object.hasOwn(packet,'author_evidence_note'));
      continue;
    }
    const note=packet.author_evidence_note, source=limitedSource[work.doi];
    assert.deepEqual(note.sections,source.sections);assert.equal(note.reviewed_on,source.reviewed_on);
    assert.deepEqual(note,work.author_evidence_note);assert.equal(packet.answer,null);
    assert.deepEqual(packet.available_questions,[]);assert.deepEqual(packet.work_key_findings,[]);
    assert.equal(packet.publication.type,work.type);assert.equal(packet.publication.evidence_status,'limited');
    assert.deepEqual(packet.limitations,source.limitations);
    assert(Object.keys(packet).indexOf('author_evidence_note')<Object.keys(packet).indexOf('available_scope'));
    const [relative,pointer]=note.source_record.split('#');assert.equal(relative,'data/limited_evidence.json');
    let record={papers:limitedSource};
    for (const token of pointer.slice(1).split('/')) record=record[token.replace(/~1/g,'/').replace(/~0/g,'~')];
    assert.deepEqual(record,source);
    note.sections[0].text='Local packet mutation';
    assert.equal(client.fetch(work.id).author_evidence_note.sections[0].text,source.sections[0].text);
  }
  // An older snapshot's omission is not an empty note or an evidence upgrade.
  const oldSnapshot=structuredClone(catalog);
  for (const work of oldSnapshot.works) delete work.author_evidence_note;
  const oldClient=createClient(oldSnapshot,loaded.search,loaded.retrieval);
  for (const id of ['doi-10-1371-journal-pone-0346326','doi-10-2139-ssrn-4857099']) {
    const packet=client.fetch(id),oldPacket=oldClient.fetch(id);
    assert(packet.author_evidence_note);assert(!Object.hasOwn(oldPacket,'author_evidence_note'));
    delete packet.author_evidence_note;assert.deepEqual(packet,oldPacket);
  }
  const noteCases=[
    note=>{note.source_record='data/limited_evidence.json#/papers/10.0000~1other';},
    note=>{note.reviewed_on='2026-02-30';},
    note=>{note.sections=[];},
    note=>{delete note.sections[0].source_locator;},
    note=>{note.sections[0].source_url='http://example.org/paper';},
    note=>{note.sections[0].source_url='javascript:alert(1)';},
    note=>{note.sections[0].source_url='https://user:password@example.org/paper';},
    note=>{note.sections[0].text='<p>Unapproved markup</p>';},
    note=>{note.extra='Not part of the source record';},
  ];
  for (const mutate of noteCases) {
    const fixture=structuredClone(catalog),work=fixture.works.find(work=>work.id==='doi-10-1371-journal-pone-0346326');
    mutate(work.author_evidence_note);
    assert.throws(()=>createClient(fixture,loaded.search),/source-bound author evidence note/);
  }
  for (const role of ['reviewed_v2','patent_record']) {
    const fixture=structuredClone(catalog),work=fixture.works.find(work=>work.evidence_status===role);
    work.author_evidence_note=structuredClone(limitedWorks[0].author_evidence_note);
    assert.throws(()=>createClient(fixture,loaded.search),/source-bound author evidence note/);
  }
  const exact = catalog.all_questions.find(q=>q.work_id==='aihflevel');
  const found=client.search(exact.question);
  assert(found.best_matches.some(hit=>hit.id===exact.id));
  assert.equal(found.query_transmitted_to_source,false);assert.equal(found.natural_discovery_proven,false);
  const paraphrase=client.search('What happened after knocking down SYNE1 in CRC cells?');
  assert(paraphrase.broader_related.some(hit=>hit.id==='doi-10-1038-s41698-026-01699-1--qa-6'));
  const partial=client.search('KIF13B KCTD10 KLF4 vascular smooth muscle coveragefixtureunseen');
  assert(partial.broader_related.length > 0);
  assert(partial.broader_related.every(hit=>hit.query_coverage.unmatched_query_terms.includes('coveragefixtureunseen')));
  assert(partial.broader_related.every(hit=>hit.query_coverage.interpretation.includes('do not validate the query premise')));
  assert(found.best_matches.every(hit=>hit.query_coverage===undefined));
  const unrelated=client.search('James Webb exoplanet transit atmosphere methane detection');
  assert.equal(unrelated.best_matches.length,0);assert.equal(unrelated.broader_related.length,0);
  assert.throws(()=>client.fetch('not-a-known-id'),/Unknown stable/);
  assert.throws(()=>client.search(''),/non-empty/);
  const copy=client.fetch(exact.id);copy.limitations.push('Mutation must not persist');
  assert(!client.fetch(exact.id).limitations.includes('Mutation must not persist'));
  const malformed=structuredClone(catalog);malformed.all_questions[0].work_id='missing';
  assert.throws(()=>createClient(malformed,loaded.search),/relationship/);
  const tampered=structuredClone(catalog);tampered.all_questions[0].answer='A tampered answer.';
  assert.throws(()=>createClient(tampered,loaded.search),/hash/);
  const badRef=structuredClone(catalog);badRef.all_questions[0].evidence_refs=['MISSING'];
  assert.throws(()=>createClient(badRef,loaded.search),/evidence/);
  const qaDocIndex=loaded.search.documents.findIndex(doc=>doc.result_kind==='paper'&&doc.category==='Q&A');
  assert(qaDocIndex>=0);
  const mixedText=structuredClone(loaded.search);
  mixedText.documents[qaDocIndex].text+=' A stale export must not be joined.';
  assert.throws(()=>createClient(catalog,mixedText),/do not match/);
  const missingRoute=structuredClone(loaded.search);missingRoute.documents.splice(qaDocIndex,1);
  assert.throws(()=>createClient(catalog,missingRoute),/missing reviewed answer route/);
  const duplicateRoute=structuredClone(loaded.search);duplicateRoute.documents.push(structuredClone(duplicateRoute.documents[qaDocIndex]));
  assert.throws(()=>createClient(catalog,duplicateRoute),/duplicate/);
  const mixedIdentity=structuredClone(loaded.search);mixedIdentity.documents[qaDocIndex].doi='10.0000/wrong';
  assert.throws(()=>createClient(catalog,mixedIdentity),/do not match/);
  const missingProfile=structuredClone(catalog);delete missingProfile.works.find(w=>w.evidence_status==='reviewed_v2').study_profile;
  assert.throws(()=>createClient(missingProfile,loaded.search),/source-bound profile/);
  const staleFinding=structuredClone(catalog);
  staleFinding.works.find(w=>w.id==='aihflevel').key_findings[0].evidence[0].value='0.999';
  assert.throws(()=>createClient(staleFinding,loaded.search),/work context do not match/);
  const staleScope=structuredClone(catalog);
  staleScope.works.find(w=>w.id==='aihflevel').evidence_scope.does_not_establish[0]='A stale limitation';
  assert.throws(()=>createClient(staleScope,loaded.search),/work context do not match/);
  // Denominators and study design are source context, not counts to add up.
  const hf=client.fetch('aihflevel--qa-1');
  assert.equal(hf.study_profile.unique_total_n,1736);
  assert.equal(hf.study_profile.cohorts.find(c=>c.name==='CRCCD Discovery').subset_of,'CRCCD Meta');
  assert.equal(hf.model_profile.final_predictor_count,12);
  assert.equal(hf.model_profile.final_predictors.length,12);
  const plaque=client.fetch('apvs--qa-7');
  assert(plaque.study_profile.counting_note.includes('not combined'));
  assert(plaque.study_profile.scale_metrics.some(row=>row.value.includes('43,964 cells')));
  const sameStudy=client.fetch('aihflevel--qa-3');
  assert.equal(hf.evidence_unit.id,sameStudy.evidence_unit.id);
  const absentRef=client.fetch('aihflevel--qa-6');
  assert.equal(absentRef.evidence_refs_status,'not_encoded');assert.deepEqual(absentRef.supporting_evidence,[]);
  assert.deepEqual(absentRef.model_profile,hf.model_profile);
  // Real identifiers and alternatives come from this same exported work. A
  // route is an available source pointer, not a successful network/body read.
  for (const work of catalog.works) {
    const packet = client.fetch(work.id), primary = packet.primary_sources;
    assert.deepEqual(primary,client.fetch(catalog.all_questions.find(q=>q.work_id===work.id)?.id || work.id).primary_sources);
    for (const route of primary.reading_routes) {
      const url = new URL(route.url);
      assert.equal(url.protocol,'https:');assert.equal(url.username,'');assert.equal(url.password,'');
      assert.equal(route.availability,'not_checked');assert(route.source_fields.length);
    }
    if (primary.identifiers.pmid) assert.equal(packet.links.pubmed_url,`https://pubmed.ncbi.nlm.nih.gov/${primary.identifiers.pmid}/`);
    if (primary.identifiers.pmcid) assert.equal(packet.links.pmc_url,`https://pmc.ncbi.nlm.nih.gov/articles/${primary.identifiers.pmcid}/`);
  }
  const b4=client.fetch('b4galt2');
  assert.equal(b4.links.publisher_url,'https://jitc.bmj.com/content/13/2/e010787');
  assert.deepEqual(b4.primary_sources.identifiers,{pmid:'40010763',pmcid:'PMC11865799'});
  assert.equal(b4.provenance.correction_doi_url,'https://doi.org/10.1136/jitc-2024-010787corr1');
  assert.equal(b4.provenance.correction_pmc_url,'https://pmc.ncbi.nlm.nih.gov/articles/PMC12164647/');
  assert(!b4.primary_sources.reading_routes.some(route=>route.url.includes('PMC12164647')));
  assert.equal(client.fetch('time-cart').links.publisher_url,'https://link.springer.com/article/10.1186/s12943-024-02047-2');
  assert.equal(hf.links.pubmed_url,'https://pubmed.ncbi.nlm.nih.gov/39117613/');
  assert.equal(hf.links.pmc_url,'https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/');
  let sourceRouteCases=0;
  function routeFixture(overrides) {
    const fixture=structuredClone(catalog),work=fixture.works.find(w=>w.id==='aihflevel');
    Object.assign(work,{pmid:null,pmcid:null,publisher_url:null,provenance:null},overrides);
    const packet=createClient(fixture,loaded.search).fetch('aihflevel--qa-3');sourceRouteCases++;
    assert.equal(packet.publication.doi,hf.publication.doi);
    assert.equal(packet.answer,client.fetch('aihflevel--qa-3').answer);
    assert.deepEqual(packet.evidence_scope,hf.evidence_scope);assert.deepEqual(packet.limitations,hf.limitations);
    assertXmlRoute(packet);
    return packet;
  }
  const noIdentifiers=routeFixture({provenance:[{url:'https://example.org/a-supplement',label:'Source'}]});
  assert.deepEqual(noIdentifiers.primary_sources.identifiers,{pmid:null,pmcid:null});
  assert.deepEqual(noIdentifiers.primary_sources.reading_routes,[]);
  const listed=routeFixture({provenance:[null,'not a record',{pmid:'39117613',pmcid:'pmc11310499',publisher_url:'https://www.nature.com/articles/s41467-024-50415-9'}]});
  assert.equal(listed.links.pubmed_url,hf.links.pubmed_url);assert.equal(listed.links.pmc_url,hf.links.pmc_url);
  assert(listed.primary_sources.reading_routes.every(route=>route.source_fields.some(field=>field.startsWith('work.provenance[2]'))));
  const conflict=routeFixture({pmid:'39117613',pmcid:'PMC11310499',provenance:{pmid:'40010763'}});
  assert.equal(conflict.primary_sources.identifiers.pmid,null);assert.equal(conflict.links.pubmed_url,null);
  assert.equal(conflict.links.pmc_url,hf.links.pmc_url);
  assert(conflict.primary_sources.metadata_issues.some(issue=>issue.reason==='conflicting_identifiers'));
  const conflictingUrl=routeFixture({pmid:'39117613',pmcid:'PMC11310499',provenance:{pubmed_url:'https://pubmed.ncbi.nlm.nih.gov/40010763/'}});
  assert.equal(conflictingUrl.links.pubmed_url,null);assert.equal(conflictingUrl.links.pmc_url,hf.links.pmc_url);
  const invalid=routeFixture({pmid:'bad/id',pmcid:false,publisher_url:'https://user:secret@example.org/paper',provenance:{pubmed_url:'http://pubmed.ncbi.nlm.nih.gov/39117613/',pmc_url:'https://evil.invalid/articles/PMC11310499/'}});
  assert.deepEqual(invalid.primary_sources.reading_routes,[]);assert.equal(invalid.primary_sources.metadata_issues.length,5);
  assert(!JSON.stringify(invalid.primary_sources.metadata_issues).includes('secret'));
  const invalidTop=routeFixture({pmid:'bad/id',publisher_url:'http://example.org/paper',provenance:{pubmed_url:'https://pubmed.ncbi.nlm.nih.gov/39117613/',publisher_url:'https://www.nature.com/articles/s41467-024-50415-9'}});
  assert.equal(invalidTop.links.pubmed_url,hf.links.pubmed_url);
  assert.equal(invalidTop.links.publisher_url,'https://www.nature.com/articles/s41467-024-50415-9');
  assert.equal(invalidTop.primary_sources.metadata_issues.length,2);
  const fallbackConflict=routeFixture({pmid:'39117613',provenance:[{publisher_url:'https://example.org/one'},{publisher_url:'https://example.org/two'}]});
  assert.equal(fallbackConflict.links.publisher_url,null);assert.equal(fallbackConflict.links.pubmed_url,hf.links.pubmed_url);
  assert(fallbackConflict.primary_sources.metadata_issues.some(issue=>issue.reason==='conflicting_fallback_urls'));
  const preferred=routeFixture({publisher_url:'https://www.nature.com/articles/s41467-024-50415-9',provenance:{publisher_url:'https://doi.org/10.1038/s41467-024-50415-9'}});
  assert.equal(preferred.links.publisher_url,'https://www.nature.com/articles/s41467-024-50415-9');
  const wrongDoi=routeFixture({publisher_url:'https://doi.org/10.0000/wrong'});
  assert.equal(wrongDoi.links.publisher_url,null);assert.equal(wrongDoi.primary_sources.metadata_issues[0].reason,'conflicting_doi_url');
  const badDoi=routeFixture({publisher_url:'https://doi.org/%'});
  assert.equal(badDoi.links.publisher_url,null);assert.equal(badDoi.primary_sources.metadata_issues[0].reason,'invalid_doi_url');
  const resolver=routeFixture({publisher_url:'https://doi.org/10.1038/s41467-024-50415-9'});
  assert.equal(resolver.primary_sources.reading_routes[0].kind,'doi_resolver');
  const misplaced=routeFixture({pmid:39117613,publisher_url:'https://pubmed.ncbi.nlm.nih.gov/39117613/'});
  assert.equal(misplaced.links.pubmed_url,hf.links.pubmed_url);assert.equal(misplaced.links.publisher_url,null);
  assert.equal(misplaced.primary_sources.metadata_issues[0].reason,'database_url_in_publisher_field');
  const pmcConflict=routeFixture({pmcid:'PMC11310499',provenance:{pmcid:'PMC11865799'}});
  assert.equal(pmcConflict.primary_sources.identifiers.pmcid,null);
  assert(pmcConflict.primary_sources.metadata_issues.some(issue=>issue.field==='pmcid'&&issue.reason==='conflicting_identifiers'));
  const pmcUrlConflict=routeFixture({pmcid:'PMC11310499',provenance:{pmc_url:'https://pmc.ncbi.nlm.nih.gov/articles/PMC11865799/'}});
  assert.equal(pmcUrlConflict.primary_sources.identifiers.pmcid,null);
  const pmcUrlOnly=routeFixture({provenance:{pmc_url:'https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/'}});
  assert.equal(pmcUrlOnly.primary_sources.identifiers.pmcid,'PMC11310499');
  const validFallback=routeFixture({pmcid:'invalid',provenance:{pmcid:'pmc11310499'}});
  assert.equal(validFallback.primary_sources.identifiers.pmcid,'PMC11310499');
  for (const pmcid of ['PMC0','PMC001','PMC-7','11310499','PMC12345678901','PMC11310499?id=other']) {
    const malformed=routeFixture({pmcid});
    assert.equal(malformed.primary_sources.identifiers.pmcid,null);
    assert(malformed.primary_sources.metadata_issues.some(issue=>issue.reason==='invalid_identifier'));
  }
  const unrelatedPmc=routeFixture({references:[{pmcid:'PMC11865799'}],provenance:{correction_pmc_url:'https://pmc.ncbi.nlm.nih.gov/articles/PMC12164647/',url:'https://pmc.ncbi.nlm.nih.gov/articles/PMC11865799/'}});
  assert.equal(unrelatedPmc.primary_sources.identifiers.pmcid,null);
  assert.equal(sourceRouteCases,23);
  // An explicit same-work repository PDF is a reading route; an arbitrary
  // provenance link (even one labelled "full text") remains just provenance.
  const repositorySource={url:'https://repository.example.org/paper.pdf',label:'Institutional full text',
    reading_route:{kind:'institutional_repository_pdf',doi:hf.publication.doi,version:'journal_pre_proof'}};
  const repository=routeFixture({provenance:[repositorySource]});
  assert.deepEqual(repository.primary_sources.reading_routes,[{
    provider:'Institutional repository',kind:'institutional_repository_pdf',url:repositorySource.url,
    doi:hf.publication.doi,version:'journal_pre_proof',
    source_fields:['work.provenance[0].url','work.provenance[0].reading_route'],availability:'not_checked'}]);
  assert.equal(repository.links.publisher_url,null);
  const repositoryAndPmc=routeFixture({pmcid:'PMC11310499',provenance:[repositorySource]});
  assert.equal(repositoryAndPmc.primary_sources.reading_routes.at(-1).kind,'full_text_xml_api');
  assert.equal(repositoryAndPmc.primary_sources.reading_routes.filter(route=>route.kind==='institutional_repository_pdf').length,1);
  const untyped=routeFixture({provenance:[{url:repositorySource.url,label:'Publisher full text'}]});
  assert.deepEqual(untyped.primary_sources.reading_routes,[]);
  for (const changed of [
    {reading_route:{...repositorySource.reading_route,doi:'10.0000/another-work'}},
    {reading_route:{...repositorySource.reading_route,doi:''}},
    {reading_route:{...repositorySource.reading_route,version:'latest'}},
    {reading_route:{...repositorySource.reading_route,kind:'metadata'}},
    {reading_route:null},
    {url:'https://api.crossref.org/works/' + hf.publication.doi},
    {url:'file:///private/author-copy.pdf'},
    {url:'http://repository.example.org/paper.pdf'},
    {url:'https://user:secret@repository.example.org/paper.pdf'},
    {url:'https://repository.example.org/paper.pdf?token=secret'},
  ]) {
    const invalidRepository=routeFixture({provenance:[{...repositorySource,...changed}]});
    assert.deepEqual(invalidRepository.primary_sources.reading_routes,[]);
    assert.equal(invalidRepository.primary_sources.metadata_issues[0].reason,'invalid_same_work_repository_route');
    assert(!JSON.stringify(invalidRepository.primary_sources.metadata_issues).includes('secret'));
  }
  const genes=client.fetch('doi-10-1016-j-gendis-2026-102480');
  const geneRoutes=genes.primary_sources.reading_routes;
  assert.equal(geneRoutes.length,1);
  assert.equal(geneRoutes[0].url,genes.provenance[0].url);
  assert.equal(geneRoutes[0].doi,genes.publication.doi);
  assert.equal(geneRoutes[0].version,'journal_pre_proof');
  assert.equal(genes.answer,null);assert.deepEqual(genes.available_questions,[]);
  assert.equal(genes.publication.evidence_status,'limited');
  assert.equal(genes.links.publisher_url,null);
  assert(!client.fetch('doi-10-1016-j-colsurfb-2026-116261').primary_sources.reading_routes
    .some(route=>route.kind==='institutional_repository_pdf'));
  assert.equal(digest('{\r\n}'),digest('{\n}'));
  const calls=[];
  const fake=async(url,options)=>{
    calls.push({url,options});
    const data=url.endsWith('research/questions.json')?catalog:loaded.search;
    const response=new Response(JSON.stringify(data),{headers:{'content-type':'application/json; charset=utf-8',etag:'"fixture"'}});
    Object.defineProperty(response,'url',{value:url});return response;
  };
  const live=await loadLive(fake);assert.equal(calls.length,2);
  assert(calls.every(call=>call.url.startsWith('https://drgezhang.com/')&&!new URL(call.url).search));
  assert(calls.every(call=>call.options.redirect==='error'&&call.options.signal));
  assert.equal(live.retrieval.mode,'public_https');
  assert.equal(createClient(live.questions,live.search,live.retrieval).fetch(exact.id).answer,exact.answer);
  await assert.rejects(()=>fetchDataset('../secret',fake),/fixed public/);
  await assert.rejects(()=>fetchDataset('research/questions.json',async()=>({ok:false,status:429})),/HTTP 429/);
  const wrongOrigin=async()=>{const response=new Response('{}',{headers:{'content-type':'application/json'}});Object.defineProperty(response,'url',{value:'https://other.invalid/questions.json'});return response;};
  await assert.rejects(()=>fetchDataset('research/questions.json',wrongOrigin),/Unexpected/);
  const badType=async(url)=>{const response=new Response('{}',{headers:{'content-type':'text/html'}});Object.defineProperty(response,'url',{value:url});return response;};
  await assert.rejects(()=>fetchDataset('research/questions.json',badType),/not JSON/);
  const tooLarge=async(url)=>{const response=new Response(new Uint8Array(MAX_BYTES+1),{headers:{'content-type':'application/json'}});Object.defineProperty(response,'url',{value:url});return response;};
  await assert.rejects(()=>fetchDataset('research/questions.json',tooLarge),/exceeds/);
  const recoveryCases=[];
  async function recoveryCase(name, check) { await check(); recoveryCases.push(name); }
  function responseAt(url, body='{}', status=200, headers={}) {
    const response=new Response(body,{status,headers:{'content-type':'application/json',...headers}});
    Object.defineProperty(response,'url',{value:url});return response;
  }
  function sequence(steps) {
    const calls=[];
    return {calls,fetch:async(url,options)=>{
      calls.push({url,options});
      assert(calls.length<=steps.length,'Recovery requested an unplanned extra response');
      return steps[calls.length-1](url,options);
    }};
  }
  const unavailable=(url,headers={})=>responseAt(url,'{"error":"temporarily unavailable"}',503,{'retry-after':'0',...headers});
  await recoveryCase('503-then200 retains exact evidence and records only recovered dataset',async()=>{
    const byPath=new Map(),calls=[];
    const fetch=async(url,options)=>{
      const attempt=(byPath.get(url)||0)+1;byPath.set(url,attempt);calls.push({url,options});
      if(url.endsWith('assets/evidence-search.json')&&attempt===1)return unavailable(url);
      return responseAt(url,JSON.stringify(url.endsWith('research/questions.json')?catalog:loaded.search));
    };
    const recovered=await loadLive(fetch),packet=createClient(recovered.questions,recovered.search,recovered.retrieval).fetch(exact.id);
    const baseline=client.fetch(exact.id);delete baseline.content_version;delete packet.content_version;
    assert.deepEqual(packet,baseline);assert.equal(calls.length,3);
    const retried=calls.filter(row=>row.url.endsWith('assets/evidence-search.json'));
    assert.strictEqual(retried[0].options.signal,retried[1].options.signal);
    assert.strictEqual(retried[0].options,retried[1].options);
    assert.deepEqual(retried[0].options.headers,{Accept:'application/json'});
    assert.equal(retried[0].options.redirect,'error');
    assert(!Object.hasOwn(recovered.retrieval.datasets.questions,'recovery'));
    assert.deepEqual(recovered.retrieval.datasets.search.recovery,
      {attempts:2,initial_http_status:503,delay_ms:0,retry_after:'0'});
  });
  await recoveryCase('first successful response keeps old metadata shape and one request',async()=>{
    const fixture=sequence([url=>responseAt(url,'{"same":true}')]);
    const result=await fetchDataset('research/questions.json',fixture.fetch);
    assert.equal(fixture.calls.length,1);assert.deepEqual(result.value,{same:true});
    assert.deepEqual(Object.keys(result.metadata).sort(),
      ['source','sha256_lf','mode','etag','last_modified','http_status'].sort());
    assert.equal(result.metadata.sha256_lf,digest('{"same":true}'));
  });
  await recoveryCase('missing Retry-After uses fixed small delay and releases first body',async()=>{
    let first;const fixture=sequence([url=>(first=responseAt(url,'Temporary service outage',503,{'content-type':'text/plain'})),url=>responseAt(url,'{"ready":true}')]);
    const started=performance.now(),result=await fetchDataset('research/questions.json',fixture.fetch);
    assert(performance.now()-started>=200);assert(first.bodyUsed);
    assert.equal(result.metadata.recovery.delay_ms,250);assert.equal(result.metadata.recovery.retry_after,null);
  });
  await recoveryCase('small complete ordinary maintenance HTML can recover',async()=>{
    const fixture=sequence([url=>responseAt(url,'<h1>503 Service Unavailable</h1>',503,{'content-type':'text/html','retry-after':'0'}),url=>responseAt(url)]);
    const result=await fetchDataset('research/questions.json',fixture.fetch);
    assert.equal(fixture.calls.length,2);assert.equal(result.metadata.recovery.initial_http_status,503);
  });
  await recoveryCase('integer Retry-After is not shortened',async()=>{
    const fixture=sequence([url=>unavailable(url,{'retry-after':'1'}),url=>responseAt(url)]);
    const started=performance.now(),result=await fetchDataset('research/questions.json',fixture.fetch);
    assert(performance.now()-started>=900);assert.equal(result.metadata.recovery.delay_ms,1000);
  });
  await recoveryCase('future HTTP-date is respected',async()=>{
    const header=new Date(Date.now()+1800).toUTCString();let secondAt=0;
    const fixture=sequence([url=>unavailable(url,{'retry-after':header}),url=>{secondAt=Date.now();return responseAt(url);}]);
    const result=await fetchDataset('research/questions.json',fixture.fetch);
    assert(secondAt>=Date.parse(header));assert.equal(result.metadata.recovery.retry_after,header);
  });
  await recoveryCase('obsolete valid HTTP-date forms remain accepted',async()=>{
    for(const header of ['Sunday, 06-Nov-94 08:49:37 GMT','Sun Nov  6 08:49:37 1994']) {
      const fixture=sequence([url=>unavailable(url,{'retry-after':header}),url=>responseAt(url)]);
      const result=await fetchDataset('research/questions.json',fixture.fetch);
      assert.equal(fixture.calls.length,2);assert.equal(result.metadata.recovery.delay_ms,0);
    }
  });
  await recoveryCase('persistent503 has at most two requests and releases both bodies',async()=>{
    const bodies=[];const fixture=sequence([url=>{const r=unavailable(url);bodies.push(r);return r;},url=>{const r=unavailable(url);bodies.push(r);return r;}]);
    await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),/HTTP 503.*after one bounded retry/);
    assert.equal(fixture.calls.length,2);assert(bodies.every(response=>response.bodyUsed));
  });
  await recoveryCase('403429 and other HTTP failures are never retried',async()=>{
    for(const status of [403,429,500,502,504]) {
      const fixture=sequence([url=>responseAt(url,'{}',status,{'retry-after':'0'})]);
      await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),new RegExp('HTTP '+status));
      assert.equal(fixture.calls.length,1);
    }
  });
  await recoveryCase('network failure gets no speculative retry',async()=>{
    const fixture=sequence([()=>{throw Error('Fixture connection failure');}]);
    await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),/Fixture connection failure/);
    assert.equal(fixture.calls.length,1);
  });
  await recoveryCase('long Retry-After does not wait or grant a new timeout',async()=>{
    const fixture=sequence([url=>unavailable(url,{'retry-after':'60'})]),started=performance.now();
    await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),/exceeds remaining.*deadline/);
    assert.equal(fixture.calls.length,1);assert(performance.now()-started<1000);
  });
  await recoveryCase('invalid explicit Retry-After is not replaced by the short default',async()=>{
    for(const header of ['', '-1', '1.5', 'tomorrow', '999999999999999999999999', 'Sat, 31 Feb 2024 00:00:00 GMT',
                         'SundayX, 06-Nov-94 08:49:37 GMT', 'Sun, 06-Nov-94 08:49:37 GMT']) {
      const fixture=sequence([url=>unavailable(url,{'retry-after':header})]);
      await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),/Invalid Retry-After/);
      assert.equal(fixture.calls.length,1);
    }
  });
  await recoveryCase('time already spent on first response reduces remaining deadline',async()=>{
    const descriptor=Object.getOwnPropertyDescriptor(performance,'now');let clock=0;
    Object.defineProperty(performance,'now',{configurable:true,value:()=>clock});
    try {
      const fixture=sequence([url=>{clock=14950;return unavailable(url,{'retry-after':'1'});}]);
      await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),/exceeds remaining.*deadline/);
      assert.equal(fixture.calls.length,1);
    } finally {if(descriptor)Object.defineProperty(performance,'now',descriptor);else delete performance.now;}
  });
  await recoveryCase('error-body time also stays inside the same deadline',async()=>{
    const descriptor=Object.getOwnPropertyDescriptor(performance,'now');let clock=0;
    Object.defineProperty(performance,'now',{configurable:true,value:()=>clock});
    try {
      const fixture=sequence([url=>responseAt(url,new ReadableStream({pull(controller){
        clock=15001;controller.enqueue(new TextEncoder().encode('Temporary outage'));controller.close();
      }}),503,{'retry-after':'0','content-type':'text/plain'})]);
      await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),/exceeds remaining.*deadline/);
      assert.equal(fixture.calls.length,1);
    } finally {if(descriptor)Object.defineProperty(performance,'now',descriptor);else delete performance.now;}
  });
  await recoveryCase('explicit security headers and interstitial bodies get no retry',async()=>{
    const headers=[{'cf-mitigated':'challenge'},{'www-authenticate':'Basic realm="fixture"'},{'x-amzn-waf-action':'captcha'}];
    const bodies=['{"challenge":"required"}','<html><script>verify()</script></html>','Verify that you are human','x'.repeat(8193),new Uint8Array([0xff]),'opaque','<html>One more step</html>'];
    const fixtures=[...headers.map(header=>url=>unavailable(url,header)),...bodies.map((body,index)=>url=>responseAt(url,body,503,{'retry-after':'0','content-type':index===5?'application/octet-stream':'text/html'}))];
    for(const response of fixtures) {
      const fixture=sequence([response]);
      await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),/safety state is unclear/);
      assert.equal(fixture.calls.length,1);
    }
  });
  await recoveryCase('wrong503 URL cannot gain a second request',async()=>{
    const fixture=sequence([()=>unavailable('https://other.invalid/research/questions.json')]);
    await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch),/Unexpected public export URL/);
    assert.equal(fixture.calls.length,1);
  });
  await recoveryCase('recovery never bypasses success URL type JSON UTF8 or size guards',async()=>{
    const invalid=[()=>responseAt('https://other.invalid/research/questions.json'),
      url=>responseAt(url,'{}',200,{'content-type':'text/html'}),url=>responseAt(url,'{bad json'),
      url=>responseAt(url,new Uint8Array([0xff])),
      url=>responseAt(url,'{}',200,{'content-length':String(MAX_BYTES+1)}),
      url=>responseAt(url,new Uint8Array(MAX_BYTES+1))];
    for(const response of invalid) {
      const fixture=sequence([url=>unavailable(url),response]);
      await assert.rejects(()=>fetchDataset('research/questions.json',fixture.fetch));
      assert.equal(fixture.calls.length,2);
    }
  });
  await recoveryCase('mixed-version scientific content still fails after transport recovery',async()=>{
    const calls=new Map();let total=0;
    const recovered=await loadLive(async(url)=>{
      const n=(calls.get(url)||0)+1;calls.set(url,n);total++;
      if(url.endsWith('assets/evidence-search.json')&&n===1)return unavailable(url);
      return responseAt(url,JSON.stringify(url.endsWith('research/questions.json')?catalog:mixedText));
    });
    assert.throws(()=>createClient(recovered.questions,recovered.search,recovered.retrieval),/do not match/);
    assert.equal(total,3);
  });
  assert.deepEqual(networkCalls,[]);globalThis.fetch=originalFetch;
  console.log('OFFLINE BOUNDED503 CHECKS: '+JSON.stringify({cases:recoveryCases.length,passed:recoveryCases,network_calls:networkCalls.length}));
  console.log(`EVIDENCE CLIENT PASS: ${catalog.all_questions.length} source-exact question packets, ${catalog.works.length} work identities, ${nonEncoded} not_encoded preserved, scope/refs/citations joined; ${sourceRouteCases} source-route fixtures, ${limitedWorks.length} source-exact limited notes, ${noteCases.length+2} invalid-note cases and fixed-host bounded transport failures tested offline`);
}
run().catch(error=>{console.error(error);process.exitCode=1;});
