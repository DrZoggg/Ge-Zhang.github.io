'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets/evidence-search.js'), 'utf8');
const corpus = JSON.parse(fs.readFileSync(path.join(root, 'assets/evidence-search.json'), 'utf8'));
const publications = JSON.parse(fs.readFileSync(path.join(root, 'publications.json'), 'utf8'));
const MiniSearch = require(path.join(root, 'assets/vendor/minisearch-7.2.0/minisearch.js'));

// A local DOM contract test runs the actual browser closure and real vendored
// engine. It does not automate a browser or make a network request.
class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.listeners = {}; this.value = ''; this._text = ''; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(c => typeof c === 'string' ? c : c.textContent).join(''); }
  append(...values) { this.children.push(...values); }
  replaceChildren(...values) { this._text = ''; this.children = values; }
  addEventListener(event, listener) { this.listeners[event] = listener; }
}
function descendants(node) {
  return [node, ...node.children.filter(c => typeof c !== 'string').flatMap(descendants)];
}
function badges(card) {
  return descendants(card).filter(n => String(n.className || '').split(' ').includes('pub-status'));
}
function install(data) {
  const box = new Element('input'), results = new Element('section'), status = new Element('p');
  const elements = {pubSearch:box, evidenceResults:results, evidenceSearchStatus:status};
  let fetches = 0;
  const document = {
    currentScript:{src:'https://drgezhang.com/assets/evidence-search.js'},
    getElementById:id => elements[id], createElement:tag => new Element(tag),
    head:{append() { throw Error('Preloaded official MiniSearch should be reused'); }},
  };
  const window = {document, MiniSearch};
  vm.runInNewContext(source, {window, document, URL, fetch:async url => {
    assert.equal(String(url), 'https://drgezhang.com/assets/evidence-search.json');
    fetches += 1;
    return {ok:true, json:async () => data};
  }}, {timeout:1000});
  return {box, results, status, fetches:() => fetches, async query(text) {
    box.value = text; await box.listeners.input();
    return results.children.filter(n => n.className === 'evidence-search-result');
  }};
}

async function main() {
  const staticPage = fs.readFileSync(path.join(root, 'publications.html'), 'utf8');
  const staticStatuses = new Map([...staticPage.matchAll(/<article class="pub"[^>]*>[\s\S]*?<a href="([^"]+)"[\s\S]*?<span class="badge pub-status">([^<]*)<\/span>/g)]
    .map(m => [new URL(m[1], 'https://drgezhang.com/publications.html').href, m[2]]));
  assert.equal(staticStatuses.size, publications.length);
  const ui = install(corpus), observed = new Map();
  for (const paper of publications) {
    const cards = await ui.query(paper.doi || paper.title);
    const card = cards.find(c => descendants(c).some(n => n.tagName === 'A' && n.href?.split('#')[0] === paper.paper_url));
    assert(card, paper.paper_url);
    assert.equal(badges(card).length, 1, paper.paper_url);
    assert.equal(badges(card)[0].textContent, staticStatuses.get(paper.paper_url), paper.paper_url);
    observed.set(paper.paper_url, badges(card)[0].textContent);
  }
  assert.equal(observed.size, publications.length);
  assert.equal(ui.fetches(), 1, 'Corpus and actual engine are reused across input events');
  const guideCards = await ui.query('DCM-HF circulating biomarkers');
  const guides = guideCards.filter(c => c.textContent.includes('Guide — selected evidence comparison; not a research article.'));
  assert(guides.length);
  assert(guides.every(c => badges(c).length === 0));
  assert.equal((await ui.query('')).length, 0);
  assert.match(ui.status.textContent, /complete publication list/);

  const first = corpus.documents.find(d => d.result_kind === 'paper' && d.category === 'Title');
  // The display consumes the canonical exported label; it must not infer Deep
  // completion from V2 content or from static publication cards on this page.
  const ordinary = install({documents:[{...first, id:0, paper_status_label:'Paper GEO V2'}]});
  assert.equal(badges((await ordinary.query(first.doi))[0])[0].textContent, 'Paper GEO V2');
  const guide = install({documents:[{...first, id:0, doi:'', result_kind:'guide', paper_status_label:'Deep GEO · Complete'}]});
  assert.equal(badges((await guide.query(first.title))[0]).length, 0);
  const legacy = {...first, id:0}; delete legacy.paper_status_label;
  const oldCache = install({documents:[legacy]});
  assert.equal(badges((await oldCache.query(first.doi))[0]).length, 0, 'Absent old metadata is not guessed');
  console.log(`SEARCH UI STATUS PASS: ${observed.size} real records match static status; guide, non-Deep V2, legacy metadata and clear-input cases passed; no network`);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
