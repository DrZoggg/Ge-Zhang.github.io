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
  function createBaselineEngine(MiniSearch, data) {
    const index = new MiniSearch({fields: ['text'], storeFields: ['title', 'doi', 'url', 'category', 'text', 'limitation', 'result_kind'],
      processTerm: normalize, searchOptions: {fuzzy: false, prefix: false, combineWith: 'AND'}});
    index.addAll(data.documents);
    const exactQuestions = new Map(data.documents
      .filter(d => d.result_kind === 'paper' && d.category === 'Q&A')
      .map(d => [normalize(d.text.split('\n')[0]), d]));
    const papers = new Map();
    data.documents.filter(d => d.result_kind === 'paper' && d.doi).forEach(d => {
      const paper = papers.get(d.doi) || {doi:d.doi, title:d.title, url:d.url, fields:{}, sections:[]};
      paper.fields[d.category] = (paper.fields[d.category] || '') + ' ' + d.text;
      paper.sections.push(d);
      papers.set(d.doi, paper);
    });
    // Corpus-specific words must not disappear when a whole-paper fallback
    // relaxes coverage. Count works, not repeated sections or representations.
    const tokenWorkCounts = new Map(), topicalTokens = new Set();
    papers.forEach(paper => {
      paper.tokens = new Set(normalize(Object.values(paper.fields).join(' ')).split(/[^a-z0-9]+/u));
      paper.tokens.forEach(token => tokenWorkCounts.set(token, (tokenWorkCounts.get(token) || 0) + 1));
      normalize((paper.fields.Title || '') + ' ' + (paper.fields.Concepts || ''))
        .split(/[^a-z0-9]+/u).forEach(token => topicalTokens.add(token));
    });
    const dedupe = hits => { const seen = new Set(); return hits.filter(h => { const key = h.doi || h.title; if (seen.has(key)) return false; seen.add(key); return true; }); };
    const fallback = query => {
      const groups = fallbackGroups(query), rows = [];
      const anchors = groups.map(group => group.raw).filter(token =>
        token.length >= 3 && /[a-z]/u.test(token) && !fallbackAliases[token]
        && topicalTokens.has(token) && tokenWorkCounts.get(token) <= 2);
      papers.forEach(paper => {
        if (anchors.some(token => !paper.tokens.has(token))) return;
        let matched = 0, informative = 0, score = 0, fields = [];
        const matchedQueryTerms = new Set();
        groups.forEach(group => { const hits = Object.keys(paper.fields).filter(cat => group.terms.has(cat.toLowerCase()) || [...group.terms].some(t => normalize(paper.fields[cat]).split(/[^a-z0-9]+/u).includes(t))); if (!hits.length) return; matchedQueryTerms.add(group.raw); matched += 1; if (!fallbackGeneric.has(group.raw)) informative += 1; const best = hits.sort((a,b) => (fallbackWeights[b] || 1) - (fallbackWeights[a] || 1))[0]; score += (fallbackWeights[best] || 1) * (fallbackGeneric.has(group.raw) ? .18 : 1); fields.push(best); });
        const infoCoverage = informative / Math.max(1, groups.filter(g => !fallbackGeneric.has(g.raw)).length);
        if (infoCoverage < .65 || score < 12 || !fields.length || fields.every(f => f.toLowerCase().includes('limitation') || f.toLowerCase().includes('scope'))) return;
        // A category can contain several Q&A/findings. Choose its strongest
        // lexical passage instead of always jumping to its first document.
        const passageScore = section => {
          const tokens = new Set(normalize(section.text).split(/[^a-z0-9]+/u));
          return groups.reduce((total, group) => total +
            ([...group.terms].some(term => tokens.has(term)) ? (fallbackGeneric.has(group.raw) ? .18 : 1) : 0), 0);
        };
        const candidates = paper.sections.filter(s => s.category === fields[0]);
        const section = candidates.sort((a,b) => passageScore(b) - passageScore(a))[0] || paper.sections[0];
        const evaluatedQueryTerms = [...new Set(groups.map(group => group.raw))];
        rows.push({...section, doi:paper.doi, title:paper.title, url:section.url, score, matchGroup:'broader', limitation:Boolean(section.limitation),
          queryCoverage: {
            basis:'Whole-work indexed text using the existing ASCII fallback tokens, stop words and acronym aliases; not the matched passage alone',
            evaluated_query_terms:evaluatedQueryTerms,
            matched_query_terms:evaluatedQueryTerms.filter(term => matchedQueryTerms.has(term)),
            unmatched_query_terms:evaluatedQueryTerms.filter(term => !matchedQueryTerms.has(term))
          }});
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
      // An unchanged reviewed question must resolve to its own answer before
      // paper-level deduplication can select a different matched section.
      const exactQuestion = exactQuestions.get(value);
      const stageA = dedupe([...(exactQuestion ? [{...exactQuestion, score:1}] : []), ...index.search(value)]);
      const strongA = stageA.length > 0;
      if (strongA) return envelope(stageA.map(h => ({...h, matchGroup:'best'})), []);
      return envelope([], fallback(value));
    };
  }
/* words/stemmer 2.0.1 — https://github.com/words/stemmer/tree/2.0.1
Adaptation: ESM export removed for this existing browser closure.
(The MIT License)

Copyright (c) 2014 Titus Wormer <tituswormer@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/
// Standard suffix manipulations.
/** @type {Record<string, string>} */
const step2list = {
  ational: 'ate',
  tional: 'tion',
  enci: 'ence',
  anci: 'ance',
  izer: 'ize',
  bli: 'ble',
  alli: 'al',
  entli: 'ent',
  eli: 'e',
  ousli: 'ous',
  ization: 'ize',
  ation: 'ate',
  ator: 'ate',
  alism: 'al',
  iveness: 'ive',
  fulness: 'ful',
  ousness: 'ous',
  aliti: 'al',
  iviti: 'ive',
  biliti: 'ble',
  logi: 'log'
}

/** @type {Record<string, string>} */
const step3list = {
  icate: 'ic',
  ative: '',
  alize: 'al',
  iciti: 'ic',
  ical: 'ic',
  ful: '',
  ness: ''
}

// Consonant-vowel sequences.
const consonant = '[^aeiou]'
const vowel = '[aeiouy]'
const consonants = '(' + consonant + '[^aeiouy]*)'
const vowels = '(' + vowel + '[aeiou]*)'

const gt0 = new RegExp('^' + consonants + '?' + vowels + consonants)
const eq1 = new RegExp(
  '^' + consonants + '?' + vowels + consonants + vowels + '?$'
)
const gt1 = new RegExp('^' + consonants + '?(' + vowels + consonants + '){2,}')
const vowelInStem = new RegExp('^' + consonants + '?' + vowel)
const consonantLike = new RegExp('^' + consonants + vowel + '[^aeiouwxy]$')

// Exception expressions.
const sfxLl = /ll$/
const sfxE = /^(.+?)e$/
const sfxY = /^(.+?)y$/
const sfxIon = /^(.+?(s|t))(ion)$/
const sfxEdOrIng = /^(.+?)(ed|ing)$/
const sfxAtOrBlOrIz = /(at|bl|iz)$/
const sfxEED = /^(.+?)eed$/
const sfxS = /^.+?[^s]s$/
const sfxSsesOrIes = /^.+?(ss|i)es$/
const sfxMultiConsonantLike = /([^aeiouylsz])\1$/
const step2 =
  /^(.+?)(ational|tional|enci|anci|izer|bli|alli|entli|eli|ousli|ization|ation|ator|alism|iveness|fulness|ousness|aliti|iviti|biliti|logi)$/
const step3 = /^(.+?)(icate|ative|alize|iciti|ical|ful|ness)$/
const step4 =
  /^(.+?)(al|ance|ence|er|ic|able|ible|ant|ement|ment|ent|ou|ism|ate|iti|ous|ive|ize)$/

/**
 * Get the stem from a given value.
 *
 * @param {string} value
 *   Value to stem.
 * @returns {string}
 *   Stem for `value`
 */
// eslint-disable-next-line complexity
function stemmer(value) {
  let result = String(value).toLowerCase()

  // Exit early.
  if (result.length < 3) {
    return result
  }

  /** @type {boolean} */
  let firstCharacterWasLowerCaseY = false

  // Detect initial `y`, make sure it never matches.
  if (
    result.codePointAt(0) === 121 // Lowercase Y
  ) {
    firstCharacterWasLowerCaseY = true
    result = 'Y' + result.slice(1)
  }

  // Step 1a.
  if (sfxSsesOrIes.test(result)) {
    // Remove last two characters.
    result = result.slice(0, -2)
  } else if (sfxS.test(result)) {
    // Remove last character.
    result = result.slice(0, -1)
  }

  /** @type {RegExpMatchArray|null} */
  let match

  // Step 1b.
  if ((match = sfxEED.exec(result))) {
    if (gt0.test(match[1])) {
      // Remove last character.
      result = result.slice(0, -1)
    }
  } else if ((match = sfxEdOrIng.exec(result)) && vowelInStem.test(match[1])) {
    result = match[1]

    if (sfxAtOrBlOrIz.test(result)) {
      // Append `e`.
      result += 'e'
    } else if (sfxMultiConsonantLike.test(result)) {
      // Remove last character.
      result = result.slice(0, -1)
    } else if (consonantLike.test(result)) {
      // Append `e`.
      result += 'e'
    }
  }

  // Step 1c.
  if ((match = sfxY.exec(result)) && vowelInStem.test(match[1])) {
    // Remove suffixing `y` and append `i`.
    result = match[1] + 'i'
  }

  // Step 2.
  if ((match = step2.exec(result)) && gt0.test(match[1])) {
    result = match[1] + step2list[match[2]]
  }

  // Step 3.
  if ((match = step3.exec(result)) && gt0.test(match[1])) {
    result = match[1] + step3list[match[2]]
  }

  // Step 4.
  if ((match = step4.exec(result))) {
    if (gt1.test(match[1])) {
      result = match[1]
    }
  } else if ((match = sfxIon.exec(result)) && gt1.test(match[1])) {
    result = match[1]
  }

  // Step 5.
  if (
    (match = sfxE.exec(result)) &&
    (gt1.test(match[1]) ||
      (eq1.test(match[1]) && !consonantLike.test(match[1])))
  ) {
    result = match[1]
  }

  if (sfxLl.test(result) && gt1.test(result)) {
    result = result.slice(0, -1)
  }

  // Turn initial `Y` back to `y`.
  if (firstCharacterWasLowerCaseY) {
    result = 'y' + result.slice(1)
  }

  return result
}

// Candidate only: derived lexical views. All returned text and URLs are originals.
const createBaseline=createBaselineEngine;
const porter=stemmer;
const STOP=new Set('a an and are as at be been being by can could did do does for from had has have how i in into is it its me of on or our please show tell than that the their them there these they this those to us using use used was were what when where whether which who why will with within would study studies research evidence paper papers analysis find about after before only actually called happened report reported reports results result'.split(' '));
const GENERIC=new Set('disease model patient clinical cell human molecular risk outcome data biomarker study group gene experiment'.split(' '));
const ALIASES={hf:['heart','failure'],dcm:['dilated','cardiomyopathy'],aaa:['abdominal','aortic','aneurysm'],vsmc:['vascular','smooth','muscle'],ev:['extracellular','vesicle'],mirna:['microrna'],ici:['immune','checkpoint','inhibitor'],crc:['colorectal','cancer'],hcc:['hepatocellular','carcinoma']};
function stem(t){
 t=normalize(t);if(STOP.has(t))return null;
 const irregular={mice:'mouse',men:'man',women:'woman',children:'child'};
 if(irregular[t])return irregular[t];
 if(!/^[a-z]+$/.test(t)||t.length<5)return t;
 if(t.endsWith('ies'))return t.slice(0,-3)+'y';
 if(t.endsWith('ing')&&t.length>6)return t.slice(0,-3).replace(/([b-df-hj-np-tv-z])\1$/,'$1');
 if(t.endsWith('ed')&&t.length>5)return t.slice(0,-2).replace(/([b-df-hj-np-tv-z])\1$/,'$1');
 if(t.endsWith('s')&&!t.endsWith('ss')&&!t.endsWith('sis'))return t.slice(0,-1);
 return t;
}
function tokens(value){return normalize(value).replace(/(\d),(?=\d{3}\b)/g,'$1').match(/[a-z0-9]+/g)||[];}
function canonicalTerms(value){return [...new Set(tokens(value).map(stem).filter(Boolean))];}
function createEngine(MiniSearch,data,options={}){
 const queryAdapter=options.queryAdapter || null;
 const baseline=createBaseline(MiniSearch,data);
 const guideIndex=new MiniSearch({fields:['text'],storeFields:['result_kind'],processTerm:normalize,searchOptions:{fuzzy:false,prefix:false,combineWith:'AND'}});
 guideIndex.addAll(data.documents.filter(d=>d.result_kind==='guide'));
 const scopeIndex=new MiniSearch({fields:['text'],processTerm:normalize,searchOptions:{fuzzy:false,prefix:false,combineWith:'AND'}});
 scopeIndex.addAll(data.documents.filter(d=>d.limitation));
 const mode=options.mode||'porter';
 const process=mode==='qa_weight'?t=>STOP.has(normalize(t))?null:normalize(t):mode==='porter'?t=>{t=normalize(t);return STOP.has(t)?null:/^[a-z]+$/.test(t)?porter(t):t;}:stem;
 const groups=query=>[...new Set(tokens(query))].filter(raw=>process(raw)).map(raw=>({raw,key:process(raw),terms:new Set((ALIASES[raw]||[raw]).map(process).filter(Boolean))}));
 const genericTerms=new Set([...GENERIC].map(process));
 const records=data.documents.map(d=>({...d,question:d.category==='Q&A'?d.text.split('\n')[0]:'',answer:d.category==='Q&A'?d.text.split('\n').slice(1).join('\n'):'',body:d.category==='Q&A'?'':d.text}));
 const index=new MiniSearch({fields:['question','answer','title','body'],storeFields:['title','doi','url','category','text','limitation','result_kind'],tokenize:tokens,processTerm:process,searchOptions:{combineWith:'OR',fuzzy:false,prefix:false,boost:{question:3,answer:1.4,title:.45,body:1}}});
 index.addAll(records);
 const papers=new Map();const frequency=new Map();const topicTokens=new Set();
 records.filter(d=>d.doi&&d.result_kind==='paper').forEach(d=>{
  let p=papers.get(d.doi);if(!p){p={docs:[],tokens:new Set(),fieldTokens:new Map()};papers.set(d.doi,p);}
  p.docs.push(d);const ts=tokens(d.text).map(process).filter(Boolean);ts.forEach(t=>p.tokens.add(t));
  const ct=p.fieldTokens.get(d.category)||new Set();ts.forEach(t=>ct.add(t));p.fieldTokens.set(d.category,ct);
  if(d.category==='Title'||d.category==='Concepts')ts.forEach(t=>topicTokens.add(t));
 });
 for(const p of papers.values())for(const t of p.tokens)frequency.set(t,(frequency.get(t)||0)+1);
 const exactQuestions=new Map(data.documents.filter(d=>d.category==='Q&A').map(d=>[normalize(d.text.split('\n')[0]),d]));
 const exactTitles=new Set(data.documents.filter(d=>d.category==='Title'||d.category==='Journal').map(d=>normalize(d.text)));
 const envelope=(best,broader)=>{const r=[...best,...broader];r.bestMatches=best;r.broaderRelated=broader;return r;};
 return query=>{
  const original=normalize(query);
  const adapted=queryAdapter?queryAdapter(String(query).normalize('NFKC')):null;
  const complete=response=>{
   if(adapted){response.queryAdaptation=adapted;for(const hit of response)hit.queryAdaptation=adapted;}
   return response;
  };
  if(!original)return complete(envelope([],[]));
  if(adapted?.diagnostics?.unmapped_cjk?.length){
   const response=envelope([],[]);response.retrievalDecision='needs_query_clarification';return complete(response);
  }
  if(/^10\.\d{4,9}\//u.test(doiOf(original))||exactQuestions.has(original)||exactTitles.has(original))return complete(baseline(query));
  // Preserve precise whole-query routes to an existing guide or denial passage.
  if(guideIndex.search(original).length||scopeIndex.search(original).length)return complete(baseline(query));
  const effective=typeof adapted==='string'?adapted:adapted?.query||original;
  const gs=groups(effective);
  // Small identifier/phrase searches retain the established precise behavior.
  if(gs.length<3)return complete(baseline(effective));
  const anchors=gs.filter(g=>g.raw.length>=3&&/[a-z]/.test(g.raw)&&!ALIASES[g.raw]&&topicTokens.has(g.key)&&frequency.get(g.key)<=2).map(g=>g.key);
  const queryTerms=[...new Set(gs.flatMap(g=>[...g.terms]))].join(' ');
  const hits=index.search(queryTerms);
  const ranked=[];
  for(const [doi,p] of papers){
   if(anchors.some(a=>!p.tokens.has(a)))continue;
   const matching=gs.filter(g=>[...g.terms].some(t=>p.tokens.has(t)));
   const info=gs.filter(g=>!genericTerms.has(g.key));const matchedInfo=info.filter(g=>[...g.terms].some(t=>p.tokens.has(t)));
   if(matchedInfo.length<2||matchedInfo.length/Math.max(1,info.length)<.55)continue;
   const passageHits=hits.filter(h=>h.doi===doi);
   if(!passageHits.length)continue;
   const topicalStrength=matching.reduce((sum,g)=>sum+Math.log(1+papers.size/(frequency.get(g.key)||papers.size)),0);
   // Work selection is based on original body/identity, not adding facts.
   const score=passageHits[0].score+topicalStrength*2;
   const qaHits=passageHits.filter(h=>h.category==='Q&A');
   const bestQa=qaHits[0];
   let chosen=passageHits[0];
   if(bestQa){
    const qt=new Set(tokens(bestQa.text.split('\n')[0]).map(process).filter(Boolean));
    const at=new Set(tokens(bestQa.text).map(process).filter(Boolean));
    const qaInfo=info.filter(g=>[...g.terms].some(t=>at.has(t)));
    const questionInfo=info.filter(g=>[...g.terms].some(t=>qt.has(t)));
    if(qaInfo.length>=2&&questionInfo.length>=1&&bestQa.score>=chosen.score*.55)chosen=bestQa;
   }
   const evaluated=[...new Set(gs.map(g=>g.raw))];
   ranked.push({...chosen,doi,score,matchGroup:'broader',queryCoverage:{basis:'Whole-work indexed lexical view; stop words, disclosed acronym aliases and optional word-form normalization. Not semantic entailment or evidence strength.',evaluated_query_terms:evaluated,matched_query_terms:matching.map(g=>g.raw),unmatched_query_terms:evaluated.filter(t=>!matching.some(g=>g.raw===t))},retrievalMethod:mode, ...(adapted?{queryAdaptation:adapted}: {})});
  }
  ranked.sort((a,b)=>b.score-a.score);
  return complete(envelope([],ranked.slice(0,3)));
 };
}


  if (typeof module !== 'undefined' && module.exports) module.exports = {createEngine, normalize, doiOf};
  if (!root.document) return;
  const box = document.getElementById('pubSearch');
  if (!box) return;
  const results = document.getElementById('evidenceResults');
  const status = document.getElementById('evidenceSearchStatus');
  // Resolve from this existing script so the same search works at / and /research/.
  const assetsBase = new URL('.', document.currentScript.src);
  let loading;
  function load() {
    if (!loading) loading = Promise.all([
      new Promise((resolve, reject) => {
        if (root.MiniSearch) return resolve(root.MiniSearch);
        const script = document.createElement('script');
        script.src = new URL('vendor/minisearch-7.2.0/minisearch.js', assetsBase).href;
        script.onload = () => root.MiniSearch ? resolve(root.MiniSearch) : reject(Error('Missing MiniSearch'));
        script.onerror = reject;
        document.head.append(script);
      }),
      fetch(new URL('evidence-search.json', assetsBase)).then(r => { if (!r.ok) throw Error('Corpus unavailable'); return r.json(); })
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
        card.append(node('p', hit.result_kind === 'guide' ? 'Guide — selected evidence comparison; not a research article.' : 'Research record'));
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

