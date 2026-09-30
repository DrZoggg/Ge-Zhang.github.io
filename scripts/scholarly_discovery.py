"""Static discovery interfaces derived only from approved publication sources."""
import html
import json
import re
from datetime import date
from urllib.parse import urlparse
from sync_common import ROOT

QUESTION_PATH = 'research/questions.html'
QUESTION_JSON_PATH = 'research/questions.json'
MIME_SUFFIXES = {
    'application/vnd.citationstyles.csl+json': '.csl.json',
    'application/x-bibtex': '.bib',
    'application/x-research-info-systems': '.ris',
}


def load_identifiers(items, metadata, root=ROOT):
    payload = json.loads((root / 'data/scholarly_identifiers.json').read_text(encoding='utf-8'))
    if payload.get('version') != 1 or set(payload) != {'version', 'papers'}:
        raise ValueError('Unsupported scholarly identifier contract')
    allowed = {p['doi'] for p in items if p.get('deep_geo')}
    patterns = {'pmid': r'[1-9]\d*', 'pmcid': r'PMC[1-9]\d*',
                'openalex_id': r'https://openalex.org/W[1-9]\d*',
                'semantic_scholar_id': r'[0-9a-f]{40}'}
    for doi, row in payload['papers'].items():
        if doi not in allowed or set(row) - (set(patterns) | {'publisher_url','verified_sources','verified_at'}):
            raise ValueError('Unrecognized or non-priority scholarly identity')
        for key, pattern in patterns.items():
            if key in row and not re.fullmatch(pattern, row[key]):
                raise ValueError('Invalid scholarly identifier: ' + key)
            if key in ('pmid','pmcid') and row.get(key) and metadata.get(doi,{}).get(key) not in (None,row[key]):
                raise ValueError('Scholarly identity conflicts with verified citation metadata')
        if not row.get('verified_sources') or date.fromisoformat(row['verified_at']).isoformat() != row['verified_at']:
            raise ValueError('Missing identifier provenance')
        for url in row['verified_sources'] + ([row['publisher_url']] if row.get('publisher_url') else []):
            if urlparse(url).scheme != 'https' or not urlparse(url).netloc:
                raise ValueError('Unsafe scholarly source URL')
    return payload['papers']


def identity_links(row):
    links = []
    if row.get('publisher_url'): links.append(('Publisher record', row['publisher_url']))
    if row.get('pmid'): links.append(('PubMed ' + row['pmid'], 'https://pubmed.ncbi.nlm.nih.gov/' + row['pmid'] + '/'))
    if row.get('pmcid'): links.append(('PMC ' + row['pmcid'], 'https://pmc.ncbi.nlm.nih.gov/articles/' + row['pmcid'] + '/'))
    return links


def identifier_html(row):
    if not row: return ''
    links = identity_links(row)
    if row.get('openalex_id'): links.append(('OpenAlex record', row['openalex_id']))
    if row.get('semantic_scholar_id'): links.append(('Semantic Scholar record', 'https://www.semanticscholar.org/paper/' + row['semantic_scholar_id']))
    return ('<section id="scholarly-records"><h2>Verify publication identity</h2>'
            '<p>These records identify the same original work; database inclusion is not evidence of scientific validity or clinical benefit.</p>'
            '<div class="links">' + ' '.join('<a href="' + html.escape(url,quote=True) + '">' + html.escape(label) + '</a>' for label,url in links) + '</div></section>')


def citation_head(record):
    if not record:
        return ''
    links = [f'<link rel="cite-as" href="{html.escape(record["doi_url"], quote=True)}">']
    for mime, suffix in MIME_SUFFIXES.items():
        links.append(f'<link rel="alternate" type="{mime}" href="../citations/{record["id"]}{suffix}">')
    return '\n'.join(links)


def index_fields(item, record, content, abstract, site_url, identifiers=None):
    """Absent identifiers/exports are null; observed counts are integers, not guesses."""
    v2 = content if content and content.get('version') == 2 else None
    base = f'{site_url}/citations/{item["slug"]}'
    identifiers = identifiers or {}
    return {
        'doi_url': record['doi_url'] if record else (f'https://doi.org/{item["doi"]}' if item.get('doi') else None),
        'publisher_url': identifiers.get('publisher_url'),
        'citation_bibtex_url': base + '.bib' if record else None,
        'citation_ris_url': base + '.ris' if record else None,
        'citation_csl_json_url': base + '.csl.json' if record else None,
        'pmid': identifiers.get('pmid') or (record or {}).get('pmid'),
        'pmcid': identifiers.get('pmcid') or (record or {}).get('pmcid'),
        'openalex_id': identifiers.get('openalex_id'),
        'semantic_scholar_id': identifiers.get('semantic_scholar_id'),
        'official_abstract_available': bool(abstract),
        'evidence_csv_url': f'{site_url}/assets/evidence/{item["slug"]}.csv' if v2 else None,
        'question_count': len(v2['qa']) if v2 else 0,
        'concept_count': sum(len(values) for values in v2['concepts'].values()) if v2 else 0,
    }


def question_records(items, contents, fields, root=ROOT):
    """One context-bound, exact reviewed question per V2; never synthesize answers."""
    selection = json.loads((root / 'data/question_index.json').read_text(encoding='utf-8'))['papers']
    navigation = json.loads((root / 'data/evidence_navigation.json').read_text(encoding='utf-8'))
    mapping = {r['doi']: (i, r) for i, r in enumerate(navigation)}
    eligible = {p['doi'] for p in items if contents.get(p.get('doi', '').lower(), {}).get('version') == 2}
    if set(selection) != eligible:
        raise ValueError('Question selection must cover exactly current reviewed V2 works')
    rows = []
    for item in items:
        content = contents.get(item.get('doi', '').lower())
        if not content or content.get('version') != 2:
            continue
        choice = selection[item['doi']]
        if choice == {'navigation': True}:
            i, original = mapping[item['doi']]
            question, anchor = original['question'], original['anchor']
            source = f'data/evidence_navigation.json#/{i}/question'
        elif set(choice) == {'qa_index'} and type(choice['qa_index']) is int and 1 <= choice['qa_index'] <= len(content['qa']):
            i = choice['qa_index']
            question, anchor = content['qa'][i-1]['question'], f'qa-{i}'
            source = f'data/deep_geo/{item["slug"]}.json#/qa/{i-1}/question'
        else:
            raise ValueError('Invalid reviewed question selector: ' + item['doi'])
        rows.append({
                'id': item['slug'], 'question': question,
                'title': item['title'], 'doi': item['doi'], 'paper_url': item['paper_url'],
                'answer_url': item['paper_url'] + '#' + anchor,
                'source': source,
                'profile_type': content['study_profile']['profile_type'],
                'narrative_genre': content['study_profile'].get('narrative_genre'),
                'evidence_scope': content['evidence_scope']['does_not_establish'][0],
                'evidence_scope_kind': 'does_not_establish',
                'concepts': [v for values in content['concepts'].values() for v in values],
                'citation_bibtex_url': fields[item['slug']]['citation_bibtex_url'],
                'citation_ris_url': fields[item['slug']]['citation_ris_url'],
                'citation_csl_json_url': fields[item['slug']]['citation_csl_json_url'],
        })
    return rows


def render_questions(rows, config):
    escape = html.escape
    cards = []
    for row in rows:
        citation = (f'<a href="{escape(row["paper_url"], quote=True)}#cite-this-paper">Cite</a>'
                    if row['citation_csl_json_url'] else '')
        cards.append(
            f'<article class="card" id="{escape(row["id"], quote=True)}">'
            f'<h2><a href="{escape(row["answer_url"], quote=True)}">{escape(row["question"])}</a></h2>'
            f'<p>Paper context: {escape(row["title"])}</p><p class="meta">{escape(row["profile_type"].replace("_", " "))}</p>'
            f'<p><strong>Does not establish:</strong> {escape(row["evidence_scope"])}</p>'
            f'<p class="links"><a href="https://doi.org/{escape(row["doi"], quote=True)}">Original article DOI</a>'
            f' {citation}</p></article>')
    url = config['site_url'] + '/' + QUESTION_PATH
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scientific questions | {escape(config['researcher_name'])}</title>
<meta name="description" content="Browse reviewed scientific questions, evidence limits and original article citations from this research program.">
<link rel="canonical" href="{url}"><link rel="alternate" type="application/json" href="questions.json">
<link rel="stylesheet" href="../assets/style.css"></head><body>
<header><nav><a class="brand" href="../index.html">{escape(config['researcher_name'])}</a><div class="navlinks"><a href="../publications.html">All publications</a></div></nav></header>
<main class="wrap"><section><div class="eyebrow">Research discovery</div><h1>Scientific questions</h1>
<p class="lead">Questions addressed by publications in this research program</p>
<p>This selective index is not an exhaustive or systematic review of the field. Questions are reproduced from reviewed paper Q&amp;A or existing reviewed question mappings. Read each question in its stated paper context. Follow it to the existing answer or evidence section and full evidence scope; the original article remains the formal citation source.</p>
<p><a href="questions.json">Machine-readable question index</a> · <a href="../publications.html">Browse all publications</a></p></section>
<div class="question-index">{''.join(cards)}</div></main>
<footer><div class="wrap">{escape(config['researcher_name'])} · Academic evidence hub</div></footer></body></html>
'''


def validate_generated(items, config, root=ROOT):
    """Check the additive contract during normal Pages validation, without network."""
    from citation_common import citation_record, load_citation_metadata
    from official_abstracts import load_official_abstracts
    metadata = load_citation_metadata(items)
    abstracts = load_official_abstracts(items)
    identities = load_identifiers(items, metadata, root)
    contents = {}
    fields = {}
    for item in items:
        path = root / 'data/deep_geo' / (item['slug'] + '.json')
        content = json.loads(path.read_text(encoding='utf-8')) if item.get('deep_geo') and path.exists() else None
        if content: contents[item['doi']] = content
        record = citation_record(item, metadata, config['site_url'])
        fields[item['slug']] = index_fields(item, record, content, abstracts.get(item.get('doi')), config['site_url'], identities.get(item.get('doi')))
    index = json.loads((root / 'paper_index.json').read_text(encoding='utf-8'))
    if index.get('version') != 2 or len(index['papers']) != len(items):
        raise ValueError('Machine discovery index version/inventory mismatch')
    for item, indexed in zip(items,index['papers']):
        if indexed['paper_url'] != item['paper_url'] or any(indexed.get(k) != v for k,v in fields[item['slug']].items()):
            raise ValueError('Machine discovery field drift: ' + item['slug'])
    expected = question_records(items, contents, fields, root)
    actual = json.loads((root / QUESTION_JSON_PATH).read_text(encoding='utf-8'))
    if actual != {'version':1,'questions':expected}:
        raise ValueError('Question index differs from reviewed sources')
    page = (root / QUESTION_PATH).read_text(encoding='utf-8')
    for row in expected:
        slug = row['id']; anchor = row['answer_url'].split('#')[1]
        target = (root / 'papers' / (slug + '.html')).read_text(encoding='utf-8')
        if target.count('id="'+anchor+'"') != 1 or html.escape(row['answer_url'],quote=True) not in page:
            raise ValueError('Missing or ambiguous scientific question route')
    return {'question_routes':len(expected),'identity_records':len(identities)}
