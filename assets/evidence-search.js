/* Progressive MiniSearch UI. Never transmit, persist or URL-encode query text. */
(function (root) {
  'use strict';
  const normalize = (value) => String(value).normalize('NFKC').replace(/\s+/gu, ' ').trim().toLowerCase();
  const doiOf = (value) => normalize(value).replace(/^(?:https?:\/\/(?:dx\.)?doi\.org\/|doi:\s*)/u, '');
  function createEngine(MiniSearch, data) {
    const index = new MiniSearch({fields: ['text'], storeFields: ['title', 'doi', 'url', 'category', 'text', 'limitation', 'result_kind'],
      processTerm: normalize, searchOptions: {fuzzy: false, prefix: false, combineWith: 'AND'}});
    index.addAll(data.documents);
    return (query) => {
      const value = normalize(query);
      if (!value) return [];
      const doi = doiOf(value);
      if (/^10\.\d{4,9}\//u.test(doi)) {
        const exact = data.documents.find(d => normalize(d.doi) === doi);
        return exact ? [{...exact, category: 'Exact DOI', score: 1}] : [];
      }
      return index.search(value);
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
      const hits = engine(query);
      // Keep the most relevant matched section for each paper/guide; static records stay visible.
      const seen = new Set();
      const papers = hits.filter(hit => { if (seen.has(hit.doi || hit.title)) return false; seen.add(hit.doi || hit.title); return true; });
      status.textContent = papers.length ? `${papers.length} results — text relevance, not evidence strength.` : 'No matching results. No answer is generated. The complete list remains below.';
      papers.forEach(hit => {
        const card = node('article', ''); card.className = 'evidence-search-result';
        const heading = node('h3', ''); const link = node('a', hit.title); link.href = hit.url; heading.append(link); card.append(heading);
        card.append(node('p', hit.result_kind === 'guide' ? 'Guide — selected evidence comparison; not a research article.' : 'Paper'));
        card.append(node('p', (hit.limitation ? 'LIMITATION / DOES NOT ESTABLISH — not an affirmative conclusion. ' : '') + 'Matched section: ' + hit.category));
        // Preserve full matched field; do not turn a truncated denial into a positive snippet.
        const excerpt = node('p', hit.text); excerpt.className = 'evidence-search-excerpt'; card.append(excerpt);
        if (hit.doi) { const doi = node('a', hit.doi); doi.href = 'https://doi.org/' + hit.doi; card.append(doi); }
        results.append(card);
      });
    } catch (_) {
      if (current === sequence) status.textContent = 'Search unavailable. All publications and links remain available below; please try again.';
    }
  }
  box.addEventListener('input', search);
})(typeof window === 'undefined' ? globalThis : window);
