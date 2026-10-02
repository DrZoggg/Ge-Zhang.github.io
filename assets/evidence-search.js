/* Progressive MiniSearch UI. Never transmit, persist or URL-encode query text. */
(function (root) {
  'use strict';
  const normalize = (value) => String(value).normalize('NFKC').replace(/\s+/gu, ' ').trim().toLowerCase();
  const doiOf = (value) => normalize(value).replace(/^(?:https?:\/\/(?:dx\.)?doi\.org\/|doi:\s*)/u, '');
  const fallbackAliases = {hf:['hf','heart','failure'], dcm:['dcm','dilated','cardiomyopathy'], aaa:['aaa','abdominal','aortic','aneurysm'], vsmc:['vsmc','vascular','smooth','muscle'], ev:['ev','extracellular','vesicle','vesicles'], mirna:['mirna','microrna','micro','rna'], ici:['ici','immune','checkpoint','inhibitor'], crc:['crc','colorectal','cancer'], hcc:['hcc','hepatocellular','carcinoma']};
  const fallbackStop = new Set(['a','an','and','are','as','at','be','by','can','do','does','for','from','how','in','is','of','on','or','the','their','these','this','to','what','which','with','within','that','those','were','was','using','use','used','study','studies','evidence','analysis','associated','association','research','based']);
  const fallbackGeneric = new Set(['disease','model','models','patient','patients','clinical','biomarker','biomarkers','inflammation','inflammatory','cell','cells','human','molecular','risk','outcomes','prediction','prognosis','mechanism','mechanisms','data']);
  const fallbackGroups = (query) => String(query).toLowerCase().replace(/[\-/–—_]+/gu,' ').match(/[a-z0-9]+/gu)?.filter(t => !fallbackStop.has(t)).map(t => ({raw:t, terms:new Set(fallbackAliases[t] || [t])})) || [];
  const fallbackWeights = {Title:8, 'Research question':6, 'Research & review context':5, Concepts:4, 'Key finding':3.2, 'Evidence summary':3, 'Citation use case':2.5, 'Evidence scope — supports':1, Limitations:0.4, 'Limitations — does not establish':0.4};
  function createEngine(MiniSearch, data) {
    const index = new MiniSearch({fields: ['text'], storeFields: ['title', 'doi', 'url', 'category', 'text', 'limitation', 'result_kind'],
      processTerm: normalize, searchOptions: {fuzzy: false, prefix: false, combineWith: 'AND'}});
    index.addAll(data.documents);
    const papers = new Map();
    data.documents.filter(d => d.result_kind === 'paper' && d.doi).forEach(d => {
      const paper = papers.get(d.doi) || {doi:d.doi, title:d.title, url:d.url, fields:{}, sections:[]};
      paper.fields[d.category] = (paper.fields[d.category] || '') + ' ' + d.text;
      paper.sections.push(d);
      papers.set(d.doi, paper);
    });
    const dedupe = hits => { const seen = new Set(); return hits.filter(h => { const key = h.doi || h.title; if (seen.has(key)) return false; seen.add(key); return true; }); };
    const fallback = query => {
      const groups = fallbackGroups(query), rows = [];
      papers.forEach(paper => {
        let matched = 0, informative = 0, score = 0, fields = [];
        groups.forEach(group => { const hits = Object.keys(paper.fields).filter(cat => group.terms.has(cat.toLowerCase()) || [...group.terms].some(t => normalize(paper.fields[cat]).split(/[^a-z0-9]+/u).includes(t))); if (!hits.length) return; matched += 1; if (!fallbackGeneric.has(group.raw)) informative += 1; const best = hits.sort((a,b) => (fallbackWeights[b] || 1) - (fallbackWeights[a] || 1))[0]; score += (fallbackWeights[best] || 1) * (fallbackGeneric.has(group.raw) ? .18 : 1); fields.push(best); });
        const infoCoverage = informative / Math.max(1, groups.filter(g => !fallbackGeneric.has(g.raw)).length);
        if (infoCoverage < .65 || score < 12 || !fields.length || fields.every(f => f.toLowerCase().includes('limitation') || f.toLowerCase().includes('scope'))) return;
        const section = paper.sections.find(s => s.category === fields[0]) || paper.sections[0];
        rows.push({...section, doi:paper.doi, title:paper.title, url:paper.url, score, matchGroup:'broader', limitation:Boolean(section.limitation)});
      });
      return rows.sort((a,b) => b.score - a.score).slice(0,3);
    };
    const envelope = (bestMatches, broaderRelated) => {
      const response = [...bestMatches, ...broaderRelated];
      response.bestMatches = bestMatches;
      response.broaderRelated = broaderRelated;
      return response;
    };
    return (query) => {
      const value = normalize(query); if (!value) return envelope([], []);
      const doi = doiOf(value);
      if (/^10\.\d{4,9}\//u.test(doi)) { const exact = data.documents.find(d => normalize(d.doi) === doi); return envelope(exact ? [{...exact, category:'Exact DOI', score:1, matchGroup:'best'}] : [], []); }
      const stageA = dedupe(index.search(value));
      const strongA = stageA.length > 0;
      if (strongA) return envelope(stageA.map(h => ({...h, matchGroup:'best'})), []);
      return envelope([], fallback(value));
    };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {createEngine, normalize, doiOf};
  if (!root.document) return;
  const box = document.getElementById('pubSearch');
  if (!box) return;
  const results = document.getElementById('evidenceResults');
  const status = document.getElementById('evidenceSearchStatus');
  let loading;
  function load() {
    if (!loading) loading = Promise.all([
      new Promise((resolve, reject) => {
        if (root.MiniSearch) return resolve(root.MiniSearch);
        const script = document.createElement('script');
        script.src = 'assets/vendor/minisearch-7.2.0/minisearch.js';
        script.onload = () => root.MiniSearch ? resolve(root.MiniSearch) : reject(Error('Missing MiniSearch'));
        script.onerror = reject;
        document.head.append(script);
      }),
      fetch('assets/evidence-search.json').then(r => { if (!r.ok) throw Error('Corpus unavailable'); return r.json(); })
    ]).then(([MiniSearch, corpus]) => createEngine(MiniSearch, corpus)).catch(error => { loading = null; throw error; });
    return loading;
  }
  function node(tag, text) { const n = document.createElement(tag); n.textContent = text; return n; }
  let sequence = 0;
  async function search() {
    const current = ++sequence;
    const query = box.value;
    results.replaceChildren();
    if (!normalize(query)) { status.textContent = 'Browse the complete publication list below, or search visible evidence text.'; return; }
    status.textContent = 'Loading local text search…';
    try {
      const engine = await load();
      if (current !== sequence) return;
      const response = engine(query);
      const groups = [['Best matches', response.bestMatches], ['Broader related evidence', response.broaderRelated]];
      const total = response.bestMatches.length + response.broaderRelated.length;
      status.textContent = total ? `${total} results — text relevance, not evidence strength.` : 'No matching results. No answer is generated. The complete list remains below.';
      groups.forEach(([label, papers]) => { if (!papers.length) return; results.append(node('h2', label)); papers.forEach(hit => {
        const card = node('article', ''); card.className = 'evidence-search-result';
        const heading = node('h3', ''); const link = node('a', hit.title); link.href = hit.url; heading.append(link); card.append(heading);
        card.append(node('p', hit.result_kind === 'guide' ? 'Guide — selected evidence comparison; not a research article.' : 'Paper'));
        card.append(node('p', (hit.limitation ? 'LIMITATION / DOES NOT ESTABLISH — not an affirmative conclusion. ' : '') + 'Matched section: ' + hit.category));
        // Preserve full matched field; do not turn a truncated denial into a positive snippet.
        const excerpt = node('p', hit.text); excerpt.className = 'evidence-search-excerpt'; card.append(excerpt);
        if (hit.doi) { const doi = node('a', hit.doi); doi.href = 'https://doi.org/' + hit.doi; card.append(doi); }
        results.append(card);
      }); });
    } catch (_) {
      if (current === sequence) status.textContent = 'Search unavailable. All publications and links remain available below; please try again.';
    }
  }
  box.addEventListener('input', search);
})(typeof window === 'undefined' ? globalThis : window);

