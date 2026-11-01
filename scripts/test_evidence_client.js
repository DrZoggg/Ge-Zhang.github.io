'use strict';
const assert = require('node:assert/strict');
const {createClient,loadLocal,loadLive,fetchDataset,digest,MAX_BYTES} = require('./author_evidence_client.cjs');

async function run() {
  const loaded = loadLocal(), catalog = loaded.questions;
  const client = createClient(catalog, loaded.search, loaded.retrieval);
  const works = new Map(catalog.works.map(work => [work.id,work]));
  assert.equal(catalog.works.length, new Set(catalog.works.map(work=>work.id)).size);
  let nonEncoded = 0;
  for (const question of catalog.all_questions) {
    const packet = client.fetch(question.id), work = works.get(question.work_id);
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
  assert.equal(sourceRouteCases,12);
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
  console.log(`EVIDENCE CLIENT PASS: ${catalog.all_questions.length} source-exact question packets, ${catalog.works.length} work identities, ${nonEncoded} not_encoded preserved, scope/refs/citations joined; ${sourceRouteCases} source-route fixtures and fixed-host bounded transport failures tested offline`);
}
run().catch(error=>{console.error(error);process.exitCode=1;});
