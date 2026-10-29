const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const MiniSearch = require(path.join(root, 'assets/vendor/minisearch-7.2.0/minisearch.js'));
const {createEngine} = require(path.join(root, 'assets/evidence-search.js'));
const corpus = JSON.parse(fs.readFileSync(path.join(root, 'assets/evidence-search.json'), 'utf8'));
const search = createEngine(MiniSearch, corpus);
assert(search('GPX4').some(x => x.doi === '10.1016/j.ejphar.2023.175569'));
assert(search('MCC950').some(x => x.doi === '10.1136/jitc-2024-010127'));
assert.equal(search(' HTTPS://DOI.ORG/10.1002/MDR2.70052 ')[0].doi, '10.1002/mdr2.70052');
assert.equal(search('10.1002/mdr2.999999').length, 0);
assert(search('ＣＬＯＣＫ').length > 0);
assert(search(corpus.documents.find(x => x.category === 'Title').text).some(x => x.category === 'Title'));
assert(search('Nature Communications').some(x => x.category === 'Journal'));
assert.equal(search('gpx5zz').length, 0); // fuzzy disabled
assert.equal(search('<script>alert("injection")</script>xxxx').length, 0);
assert(search('prospectively validated early diagnostic').some(x => x.limitation && x.category.includes('Limitations')));
const publications = JSON.parse(fs.readFileSync(path.join(root, 'publications.json'), 'utf8'));
assert.equal(new Set(corpus.documents.filter(x => x.result_kind === 'paper').map(x => x.url.split('#')[0])).size, publications.length);
const qas = corpus.documents.filter(x => x.category === 'Q&A' && x.result_kind === 'paper');
assert(qas.length > 0 && qas.every(x => /#qa-\d+$/u.test(x.url)));
// An exact reviewed question lands on that same answer, not the paper top.
for (const qa of qas) {
  const hits = search(qa.text.split('\n')[0]);
  assert(hits.some(hit => hit.url === qa.url), qa.url);
}
assert(search('DCM-HF circulating biomarkers').some(x => x.result_kind === 'guide' && x.doi === ''));
assert(search('10.1021/acs.jproteome.4c00522').every(x => x.result_kind === 'paper'));
assert(search('complete discovery participant count').some(x => x.result_kind === 'guide' && x.limitation));
// Paraphrase regression: aggregate paper relevance must not select the first
// Q&A (human tissue) when the matching passage concerns pooled aortic libraries.
assert(search('How many independent aortic single cell libraries came from five Kif13b mice?')
  .some(x => x.url === 'https://drgezhang.com/papers/doi-10-1093-eurheartj-ehaf523.html#qa-3'));
assert(!corpus.documents.some(x => x.category === 'Official Abstract'));
console.log(`SEARCH PASS: official MiniSearch, DOI, Unicode, limitations, direct reviewed answer anchors; ${publications.length} public records`);
