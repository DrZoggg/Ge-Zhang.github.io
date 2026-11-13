"""One reviewed, selective guide. Source drift requires explicit scientific re-review.

The frozen-text digest is a contract check, not independent scientific verification.
No network, new publication records, citation exports, or scientific inference.
"""
import hashlib
import copy
import csv
import html
import io
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from sync_common import ROOT, is_withdrawn
from paper_discovery import scientific_content
from theme_shell import with_theme_shell, without_theme_shell

SLUG = 'dcm-hf-circulating-biomarkers'
URL = 'https://drgezhang.com/research/' + SLUG + '.html'
DATA = 'data/research_guides/' + SLUG + '.json'
CONTRACT_SHA256 = '682e83660b7c8cbbb4d70c409c935d2b8c765272cdf1c6a26255e4d190551c45'
GUIDE_READING_STYLE = '<style>body{font:17px/1.65 system-ui,sans-serif;color:#172b3a;background:#fafcfd;margin:0}main{max-width:1120px;margin:auto;padding:24px;overflow-wrap:anywhere}h1{font-size:clamp(1.7rem,4vw,2.4rem);line-height:1.2}h2{margin-top:2rem}a{color:#075d93}aside{padding:4px 20px;border-left:4px solid #52738b;background:#eef3f6}.eyebrow{color:#486275}.comparison{max-width:100%;overflow-x:auto;margin:2rem 0}table{border-collapse:collapse;min-width:900px;width:100%;font-size:15px}caption{text-align:left;font-weight:bold;padding:12px}th,td{border:1px solid #bdcdd8;padding:14px;vertical-align:top;text-align:left}thead{background:#e7eff5}th[scope=row]{min-width:170px}td{min-width:150px}article{margin:2rem 0}li{margin:.4rem 0}@media(max-width:480px){main{padding:16px}}</style>'
FIELDS = [('discovery', 'Material / discovery'), ('follow_up', 'Follow-up'),
          ('candidates', 'Candidates'), ('additional', 'Additional evaluation'),
          ('use', 'Appropriate use'), ('boundary', 'Boundary')]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def load(root=ROOT):
    return json.loads((root / DATA).read_text(encoding='utf-8'))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def resolve(data, root=ROOT, master=None):
    master = master if master is not None else json.loads((root / 'data/publications_master.json').read_text(encoding='utf-8'))
    require(not any(p.get('slug') == SLUG or p.get('paper_url') == URL or p.get('title') == data['title']
                    for p in master), 'Guide must not enter publication master')
    public = {p.get('doi', '').lower(): p for p in master if not is_withdrawn(p)}
    sources = {}
    for row in data['studies']:
        doi = row['source_doi']
        require(doi in public, 'Missing public source DOI: ' + doi)
        path = root / row['source_json']
        require(path.resolve().is_relative_to((root / 'data/deep_geo').resolve()), 'Unsafe scientific source path')
        c = json.loads(path.read_text(encoding='utf-8'))
        require(c['doi'] == doi and c['version'] == 2, 'Source identity/version mismatch')
        require(fingerprint(scientific_content(c)) == row['source_fingerprint'], 'Scientific source changed: re-review guide before publishing')
        p = public[doi]
        url = 'https://drgezhang.com/papers/' + p['slug'] + '.html'
        page = (root / 'papers' / (p['slug'] + '.html')).read_text(encoding='utf-8')
        findings = {f['id']: f for f in c['key_findings']}
        for ref in row['evidence_refs']:
            require(ref in findings and findings[ref].get('source_locator'), 'Missing source KF/locator: ' + ref)
            require('id="' + ref.lower() + '"' in page, 'Missing canonical KF anchor: ' + ref)
        sources[row['id']] = {'title': p['title'], 'doi': doi, 'url': url, 'slug': p['slug'], 'findings': findings}
    for section in data['sections'] + data['qa']:
        for key, refs in section['refs'].items():
            require(key in sources, 'Unknown source reference')
            row = next(r for r in data['studies'] if r['id'] == key)
            require(set(refs) <= set(row['evidence_refs']), 'Unknown section KF reference')
    require(fingerprint(data) == CONTRACT_SHA256,
            'Frozen guide contract changed: scientific re-review required (not automatic synthesis)')
    return sources


def references(refs, sources, markdown=False):
    groups = []
    for key, ids in refs.items():
        s = sources[key]
        link = (lambda label, url: '[' + label + '](' + url + ')') if markdown else (
            lambda label, url: '<a href="' + html.escape(url, quote=True) + '">' + html.escape(label) + '</a>')
        groups.append(link(s['doi'], 'https://doi.org/' + s['doi']) + ': ' + ', '.join(
            link(ref, s['url'] + '#' + ref.lower()) for ref in ids))
    return '; '.join(groups)


def render(data, sources):
    esc = html.escape
    body = ['<nav><a href="../publications.html">Publications</a> · <a href="' + SLUG + '.md">Markdown version</a></nav>',
            '<p class="eyebrow">Selected evidence guide · not a research article</p>',
            '<h1>' + esc(data['title']) + '</h1>', '<h2>Primary question</h2><p>' + esc(data['question']) + '</p>',
            '<aside id="scope"><h2>Scope</h2><p>' + esc(data['scope']) + '</p></aside>',
            '<p>' + esc(data['answer']) + '</p>', '<div class="comparison" role="region" aria-label="Study comparison" tabindex="0">',
            '<table><caption>Three selected studies — different analytes and evaluation units</caption><thead><tr>'
            '<th scope="col">Study / source</th><th scope="col">Material / discovery</th><th scope="col">Follow-up / additional evaluation</th>'
            '<th scope="col">Appropriate use</th><th scope="col">Boundary</th></tr></thead><tbody>']
    md = ['# ' + data['title'], '**Selected evidence guide — not a research article**',
          '[Canonical guide](' + URL + ')', '## Primary question', data['question'], '## Scope', data['scope'], data['answer'], '## Three selected studies']
    for row in data['studies']:
        s = sources[row['id']]
        ref = {row['id']: row['evidence_refs']}
        body.append('<tr><th scope="row"><a href="#' + row['id'] + '">' + esc(row['label']) + '</a><p>' +
                    references(ref, sources) + '</p></th><td>' + esc(row['discovery']) + '</td><td>' +
                    ''.join('<p>' + esc(row[k]) + '</p>' for k in ('follow_up', 'candidates', 'additional') if k in row) +
                    '</td><td>' + esc(row['use']) + '</td><td>' + esc(row['boundary']) + '</td></tr>')
        md += ['### ' + row['label']] + ['**' + label + ':** ' + row[k] for k, label in FIELDS if k in row]
        md.append(references(ref, sources, True))
    body.append('</tbody></table></div>')
    for i, section in enumerate(data['sections'] + data['qa']):
        label = section.get('label')
        body.append('<section id="question-' + str(i+1) + '"><h2>' + esc(section['heading']) + '</h2>' +
                    ('<p><strong>' + esc(label) + '</strong></p>' if label else '') + '<p>' + esc(section['text']) +
                    '</p><p>' + references(section['refs'], sources) + '</p></section>')
        md += ['## ' + section['heading']] + (['**' + label + '**'] if label else []) + [section['text'], references(section['refs'], sources, True)]
    body.append('<section><h2>Read and reuse the evidence</h2>')
    md.append('## Read and reuse the evidence')
    for row in data['studies']:
        s = sources[row['id']]
        links = [('Original paper page', s['url']), ('Formal DOI', 'https://doi.org/' + s['doi']),
                 ('Study-level CSV', 'https://drgezhang.com/assets/evidence/' + s['slug'] + '.csv')]
        links += [(label, 'https://drgezhang.com/citations/' + s['slug'] + ext) for label, ext in [('BibTeX', '.bib'), ('RIS', '.ris'), ('CSL JSON', '.csl.json')]]
        body.append('<article id="' + row['id'] + '"><h3>' + esc(s['title']) + '</h3><ul>' +
                    ''.join('<li><a href="' + esc(url, quote=True) + '">' + esc(label) + '</a></li>' for label, url in links) + '</ul><h4>Source locators</h4><ul>')
        md += ['### ' + s['title']] + ['- [' + label + '](' + url + ')' for label, url in links] + ['**Source locators**']
        for ref in row['evidence_refs']:
            locator = s['findings'][ref]['source_locator']
            body.append('<li>' + references({row['id']: [ref]}, sources) + ' — ' + esc(locator) + '</li>')
            md.append('- ' + references({row['id']: [ref]}, sources, True) + ' — ' + locator)
        body.append('</ul></article>')
    body.append('</section><p>' + esc(data['closing']) + '</p>')
    md.append(data['closing'])
    schema = {'@context': 'https://schema.org', '@type': 'WebPage', 'name': data['title'], 'url': URL, 'description': data['scope']}
    page = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
    page += '<title>' + esc(data['title']) + '</title><meta name="description" content="' + esc(data['scope'], quote=True) + '">\n'
    page += '<link rel="canonical" href="' + URL + '"><link rel="alternate" type="text/markdown" href="' + URL[:-5] + '.md">\n'
    page += '<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">\n'
    for prop, value in [('og:type', 'website'), ('og:title', data['title']), ('og:description', data['scope']), ('og:url', URL)]:
        page += '<meta property="' + prop + '" content="' + esc(value, quote=True) + '">\n'
    page += '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c') + '</script>\n'
    page += GUIDE_READING_STYLE + '</head><body><main>\n'
    return with_theme_shell(page + '\n'.join(body) + '\n</main></body></html>\n', guide=True), '\n\n'.join(md) + '\n'


def validate_page(page, expected_url=URL):
    from html.parser import HTMLParser
    class Identity(HTMLParser):
        def __init__(self):
            super().__init__(); self.h1 = 0; self.canonical = []
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag == 'h1': self.h1 += 1
            require(not (tag == 'meta' and a.get('name', '').lower() == 'citation_doi'), 'Guide cannot have citation_doi')
            if tag == 'link' and a.get('rel') == 'canonical': self.canonical.append(a.get('href'))
    p = Identity(); p.feed(page)
    require(p.h1 == 1 and p.canonical == [expected_url], 'Guide identity/canonical mismatch')
    require('ScholarlyArticle' not in page and 'FAQPage' not in page, 'Guide is WebPage only')


def build(root=ROOT):
    data = load(root); sources = resolve(data, root)
    rendered = render(data, sources)
    validate_page(rendered[0])
    changed = False
    for extension, text in zip(('html', 'md'), rendered):
        path = root / 'research' / (SLUG + '.' + extension)
        previous = path.read_text(encoding='utf-8') if path.exists() else None
        different = previous != text
        if different:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        if extension == 'html':
            changed = previous is None or without_theme_shell(previous) != without_theme_shell(text)
    return changed


def validate(root=ROOT):
    data = load(root); sources = resolve(data, root)
    expected = render(data, sources)
    for ext, text in zip(('html', 'md'), expected):
        require((root / 'research' / (SLUG + '.' + ext)).read_text(encoding='utf-8') == text, 'Guide differs from reviewed rendering')
    validate_page(expected[0])
    return {'guides': 1, 'sources': 3, 'source_KFs': 11}


def navigation():
    data = load()
    extra = ''.join('<p><a href="' + comparison_url(d) + '">' + html.escape(d['title']) + '</a></p><p>' + html.escape(d['scope']) + '</p>' for d in load_comparisons())
    return '<section id="selected-evidence-guides"><h2>Selected evidence guides</h2><p><a href="' + URL + '">' + html.escape(data['title']) + '</a></p><p>' + html.escape(data['scope']) + '</p>' + extra + '</section>'


def search_documents(root, start):
    from evidence_discovery import visible_text
    data = load(root)
    page = (root/'research'/(SLUG+'.html')).read_text(encoding='utf-8')
    visible = visible_text(page)
    docs = []
    def add(category, text, anchor='', limitation=False):
        require(text in visible, 'Guide search field is not visibly present')
        require(not anchor or 'id="'+anchor+'"' in page, 'Guide search anchor missing')
        docs.append({'id': start+len(docs), 'result_kind':'guide', 'doi':'', 'title':data['title'],
                     'category':category, 'text':text, 'url':URL+('#'+anchor if anchor else ''), 'limitation':limitation})
    for key in ['title','question','answer','scope','closing']:
        add(key.title(), data[key], 'scope' if key=='scope' else '', key=='scope')
    for row in data['studies']:
        add('Study', row['label'])
        for key, label in FIELDS:
            if key in row: add(label, row[key], limitation=key=='boundary')
    for i, section in enumerate(data['sections']+data['qa']):
        add('Question', section['heading'], 'question-'+str(i+1))
        add('Comparison' if i<3 else 'Q&A', section['text'], 'question-'+str(i+1), i in (1,2,4,5))
    return docs


# Extractive comparisons reuse this guide pipeline. The original frozen guide
# and its contract above remain unchanged; each new selection is reviewed alone.
COMPARISONS = {
    'circadian-evidence-levels': '4dde76f203b9d4705ca90767f10538a60a1420b929d9f76770c11231cc193781',
    'cardiovascular-prediction-evidence': '250f479469ec2f666e9d9a54d3cf8a49394bd2ab98a74cb2db0260169fa93e44',
    'atherosclerosis-cell-mechanisms': 'de30a2e924a343c1348d6e9a070be634e31a304a49b28a0c416c1e00090873be',
}


def load_comparisons(root=ROOT):
    result = []
    for slug, contract in COMPARISONS.items():
        data = json.loads((root / 'data/research_guides' / (slug + '.json')).read_text(encoding='utf-8'))
        require(data['slug'] == slug and fingerprint(data) == contract,
                'Comparison selection changed: independent review required')
        result.append(data)
    return result


def comparison_url(data):
    return 'https://drgezhang.com/research/' + data['slug'] + '.html'


def research_use_packet(value, studies):
    """Validate reviewed synthesis separately from the unchanged Gold answers.

    The enclosing guide digest binds the new prose and source selection. These
    guards additionally keep sentence references and formal study identities
    intact when the controller is reviewed or extended.
    """
    def fields(row, keys):
        require(isinstance(row, dict) and set(row) == set(keys), 'Research-use fields differ')
    def text(value):
        require(isinstance(value, str) and value and value == value.strip()
                and not any(ord(c) < 32 for c in value), 'Research-use text must be plain and non-empty')
    def identifier(value):
        text(value)
        require(re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', value), 'Unsafe research-use ID')
    def rows(value):
        require(isinstance(value, list) and value, 'Research-use arrays must be non-empty')
    required = ('id', 'question', 'question_zh', 'answer', 'answer_zh', 'answer_source_ids',
                'sources', 'checklist', 'study_roles', 'comparison', 'comparison_note',
                'comparison_note_source_ids', 'research_uses')
    fields(value, required + (('task_workspace',) if isinstance(value, dict) and 'task_workspace' in value else ()))
    identifier(value['id'])
    for key in ('question', 'question_zh', 'answer', 'answer_zh', 'comparison_note'):
        text(value[key])
    sources = {}
    rows(value['sources'])
    for source in value['sources']:
        fields(source, ('id', 'title', 'doi', 'url', 'locator'))
        identifier(source['id'])
        require(source['id'] not in sources, 'Duplicate research-use source ID')
        for key in ('title', 'doi', 'url', 'locator'):
            text(source[key])
        require(re.fullmatch(r'10\.\d{4,9}/[^\s<>\"]+', source['doi'], re.I), 'Invalid research-use source DOI')
        try:
            url = urlsplit(source['url'])
            valid = url.scheme == 'https' and url.hostname and not url.username and not url.password
        except ValueError:
            valid = False
        require(valid, 'Research-use sources require public HTTPS')
        if url.hostname in ('doi.org', 'dx.doi.org'):
            require(unquote(url.path.lstrip('/')).casefold() == source['doi'].casefold(),
                    'Research-use source DOI URL mismatch')
        sources[source['id']] = source
    def refs(value):
        rows(value)
        require(all(isinstance(s, str) and s in sources for s in value)
                and len(set(value)) == len(value), 'Unknown or duplicate research-use source reference')
    refs(value['answer_source_ids'])
    refs(value['comparison_note_source_ids'])
    for key, title in (('checklist', 'dimension'), ('research_uses', 'use')):
        rows(value[key])
        for row in value[key]:
            fields(row, (title, 'text', 'source_ids'))
            text(row[title]); text(row['text']); refs(row['source_ids'])
    study_by_id = {study['id']: study for study in studies}
    rows(value['study_roles'])
    require([row.get('work_id') for row in value['study_roles']] == list(study_by_id),
            'Research-use roles must retain selected study identities and order')
    for row in value['study_roles']:
        fields(row, ('work_id', 'role', 'text', 'source_ids'))
        text(row['role']); text(row['text']); refs(row['source_ids'])
        require(row['work_id'] in row['source_ids'], 'Research-use study role needs its original source')
    fields(value['comparison'], ('caption', 'rows'))
    text(value['comparison']['caption'])
    rows(value['comparison']['rows'])
    require([row.get('work_id') for row in value['comparison']['rows']] == list(study_by_id),
            'Research-use comparison must retain selected study identities and order')
    for row in value['comparison']['rows']:
        fields(row, ('work_id', 'design', 'population', 'endpoint', 'validation', 'metrics', 'doi', 'source_ids'))
        for key in ('design', 'population', 'endpoint', 'validation', 'metrics', 'doi'):
            text(row[key])
        refs(row['source_ids'])
        wid = row['work_id']
        require(wid in sources and wid in row['source_ids'] and row['doi'] == study_by_id[wid]['doi']
                and sources[wid]['doi'] == row['doi'] and sources[wid]['title'] == study_by_id[wid]['title'],
                'Research-use comparison original identity/DOI mismatch')
    if 'task_workspace' in value:
        workspace = value['task_workspace']
        fields(workspace, ('title', 'intro', 'columns', 'display_columns', 'examples', 'decisions'))
        text(workspace['title']); text(workspace['intro'])
        rows(workspace['columns'])
        require(len(workspace['columns']) <= 16, 'Task worksheet has too many columns')
        column_ids = []
        for column in workspace['columns']:
            fields(column, ('id', 'label'))
            text(column['id'])
            require(re.fullmatch(r'[a-z][a-z0-9_-]*', column['id']), 'Unsafe task worksheet column ID')
            text(column['label']); worksheet_csv_cell(column['label'])
            require(column['id'] not in column_ids, 'Duplicate task worksheet column ID')
            column_ids.append(column['id'])
        rows(workspace['display_columns'])
        require(all(isinstance(key, str) and key in column_ids for key in workspace['display_columns'])
                and len(set(workspace['display_columns'])) == len(workspace['display_columns']),
                'Unknown or duplicate displayed worksheet column')
        rows(workspace['examples'])
        require(len(workspace['examples']) <= 12, 'Task worksheet has too many examples')
        for example in workspace['examples']:
            fields(example, ('cells', 'source_ids'))
            fields(example['cells'], column_ids)
            for cell in example['cells'].values():
                text(cell); worksheet_csv_cell(cell)
            refs(example['source_ids'])
        rows(workspace['decisions'])
        for decision in workspace['decisions']:
            fields(decision, ('rule', 'text', 'source_ids'))
            text(decision['rule']); text(decision['text']); refs(decision['source_ids'])
    return {'kind': 'source_linked_methodological_synthesis', **copy.deepcopy(value)}


def worksheet_csv_cell(value):
    """Keep reviewed CSV text literal; allow a numeric negative, not a formula."""
    require(isinstance(value, str) and value and value == value.strip()
            and not any(ord(c) < 32 for c in value), 'Worksheet cell must be plain non-empty text')
    numeric_negative = re.fullmatch(r'-\d+(?:\.\d+)?(?:[eE][+-]?\d+)?', value)
    require(value[0] not in '=+@' and (value[0] != '-' or numeric_negative is not None),
            'Worksheet cell must not start a spreadsheet formula')
    return value


def task_workspace_csv(workspace, blank=False):
    """Static UTF-8 CSV, with all reviewed columns and no executable cells."""
    columns = workspace['columns']
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow([worksheet_csv_cell(column['label']) for column in columns])
    if blank:
        writer.writerow([''] * len(columns))
    else:
        for example in workspace['examples']:
            writer.writerow([worksheet_csv_cell(example['cells'][column['id']]) for column in columns])
    return stream.getvalue()


def resolve_research_use(slug, section_id, root=ROOT):
    """Resolve a navigation reference from the sole reviewed guide controller."""
    require(slug in COMPARISONS, 'Unknown research-use guide reference')
    data = json.loads((Path(root) / 'data/research_guides' / (slug + '.json')).read_text(encoding='utf-8'))
    packet = comparison_packet(data, root)
    use = packet.get('research_use')
    require(use and use['id'] == section_id, 'Unknown research-use section reference')
    return {**copy.deepcopy(use), 'guide_url': packet['canonical_url'] + '#' + use['id']}


def urls(root=ROOT):
    return [URL] + [comparison_url(d) for d in load_comparisons(root)]


def comparison_packet(data, root=ROOT):
    require(data['slug'] in COMPARISONS and fingerprint(data) == COMPARISONS[data['slug']],
            'Comparison contract changed: independent review required')
    master = json.loads((root / 'data/publications_master.json').read_text(encoding='utf-8'))
    public = {p.get('doi', '').lower(): p for p in master if not is_withdrawn(p)}
    require(not any(p.get('slug') == data['slug'] or p.get('title') == data['title'] for p in master),
            'Comparison must not enter publication master')
    studies = []
    for row in data['studies']:
        path = root / row['source_json']
        require(path.resolve().is_relative_to((root / 'data/deep_geo').resolve()), 'Unsafe comparison source path')
        c = json.loads(path.read_text(encoding='utf-8'))
        require(c['doi'] == row['source_doi'] and c['version'] == 2 and c['doi'] in public,
                'Comparison source identity/version mismatch')
        require(fingerprint(scientific_content(c)) == row['source_fingerprint'],
                'Comparison scientific source changed: re-review required')
        p = public[c['doi']]
        require(p['slug'] == row['id'], 'Comparison source slug mismatch')
        url = 'https://drgezhang.com/papers/' + p['slug'] + '.html'
        page = (root / 'papers' / (p['slug'] + '.html')).read_text(encoding='utf-8')
        findings = {f['id']: f for f in c['key_findings']}
        selected = []
        for index in row['qa_indices']:
            require(isinstance(index, int) and 1 <= index <= len(c['qa']), 'Invalid reviewed question index')
            qa = c['qa'][index - 1]
            refs = qa.get('evidence_refs', [])
            require(refs and all(ref in findings and findings[ref].get('source_locator') for ref in refs),
                    'Selected comparison answer needs encoded source locators')
            require('id="qa-' + str(index) + '"' in page, 'Missing comparison answer anchor')
            for ref in refs:
                require('id="' + ref.lower() + '"' in page, 'Missing comparison finding anchor')
            selected.append({**qa, 'answer_url': url + '#qa-' + str(index),
                             'source_pointer': row['source_json'] + '#/qa/' + str(index - 1),
                             'supporting_evidence': [findings[ref] for ref in refs]})
        studies.append({'id': row['id'], 'task': row['task'], 'doi': c['doi'], 'title': p['title'],
                        'evidence_unit': 'doi:' + c['doi'], 'paper_url': url,
                        'doi_url': 'https://doi.org/' + c['doi'],
                        'source_json': row['source_json'], 'source_fingerprint': row['source_fingerprint'],
                        'study_profile': c['study_profile'], 'selected_questions': selected,
                        'evidence_scope': c['evidence_scope'], 'limitations': c['limitations']})
        if data.get('contribution_first') is True:
            studies[-1]['publication'] = {key: p[key] for key in ('authors', 'year', 'journal', 'type') if key in p}
    require(len({s['doi'] for s in studies}) == len(studies), 'Duplicate DOI in comparison')
    packet = {'version': 1, 'kind': 'selective_author_evidence_comparison',
            **{k: data[k] for k in ('title', 'question', 'scope', 'reading_rule')},
            'canonical_url': comparison_url(data), 'studies': studies}
    require('contribution_first' not in data or type(data['contribution_first']) is bool,
            'Comparison presentation flag must be boolean')
    if data.get('contribution_first') is True:
        packet['presentation'] = 'contribution-first-v1'
    if 'research_use' in data:
        packet['research_use'] = research_use_packet(data['research_use'], studies)
    return packet


def render_task_workspace(workspace, guide_url, section_id, refs, md_refs):
    """A compact visible comparison with the full reviewed worksheet download."""
    require(isinstance(guide_url, str) and re.fullmatch(
        r'https://drgezhang\.com/research/[a-z][a-z0-9]*(?:-[a-z0-9]+)*\.html', guide_url),
        'Task worksheet requires its canonical guide URL')
    esc = html.escape
    csv_url = guide_url[:-5] + '.worksheet.csv'
    blank_url = guide_url[:-5] + '.blank.csv'
    labels = {column['id']: column['label'] for column in workspace['columns']}
    shown = workspace['display_columns']
    body = ['<section id="' + section_id + '-task-workspace" class="task-workspace"><h3>'
            + esc(workspace['title']) + '</h3><p>' + esc(workspace['intro']) + '</p>',
            '<p><a href="' + esc(csv_url, quote=True) + '" download>Download completed worksheet (CSV)</a> · '
            '<a href="' + esc(blank_url, quote=True) + '" download>Download blank worksheet (CSV)</a></p>',
            '<div class="comparison" role="region" aria-label="' + esc(workspace['title'], quote=True)
            + '" tabindex="0"><table><caption>' + esc(workspace['title']) + '</caption><thead><tr>'
            + ''.join('<th scope="col">' + esc(labels[key]) + '</th>' for key in shown)
            + '<th scope="col">Sources</th></tr></thead><tbody>']
    md = ['### ' + workspace['title'], workspace['intro'],
          '[Download completed worksheet (CSV)](' + csv_url + ') · [Download blank worksheet (CSV)](' + blank_url + ')',
          '| ' + ' | '.join(labels[key].replace('|', '\\|') for key in shown) + ' | Sources |',
          '| ' + ' | '.join('---' for _ in range(len(shown) + 1)) + ' |']
    for example in workspace['examples']:
        cells = [example['cells'][key] for key in shown]
        body.append('<tr><th scope="row">' + esc(cells[0]) + '</th>'
                    + ''.join('<td>' + esc(cell) + '</td>' for cell in cells[1:])
                    + '<td>' + refs(example['source_ids']) + '</td></tr>')
        md.append('| ' + ' | '.join(cell.replace('|', '\\|') for cell in cells)
                  + ' | ' + md_refs(example['source_ids']) + ' |')
    body.append('</tbody></table></div><h4>Decisions from the comparison</h4><ul>')
    md.append('#### Decisions from the comparison')
    for decision in workspace['decisions']:
        body.append('<li><strong>' + esc(decision['rule']) + ':</strong> ' + esc(decision['text'])
                    + ' ' + refs(decision['source_ids']) + '</li>')
        md.append('- **' + decision['rule'] + ':** ' + decision['text'] + ' ' + md_refs(decision['source_ids']))
    body.append('</ul></section>')
    return '\n'.join(body), md


def render_research_use(use, studies, guide_url=None):
    """Public, source-linked answer, metric table and research uses in HTML/MD."""
    esc = html.escape
    sid = use['id']
    source_by_id = {source['id']: source for source in use['sources']}
    study_by_id = {study['id']: study for study in studies}
    def refs(ids):
        return ' '.join('<a href="#' + sid + '-source-' + source + '">['
                        + str(list(source_by_id).index(source) + 1) + ']</a>' for source in ids)
    def md_refs(ids):
        return ' '.join('[' + str(list(source_by_id).index(source) + 1) + ']('
                        + source_by_id[source]['url'] + ')' for source in ids)
    body = ['<section id="' + sid + '" class="research-use"><h2>' + esc(use['question']) + '</h2>',
            '<p lang="zh">' + esc(use['question_zh']) + '</p>',
            '<p><strong>Source-linked methodological synthesis:</strong> ' + esc(use['answer']) + ' '
            + refs(use['answer_source_ids']) + '</p>',
            '<p lang="zh">' + esc(use['answer_zh']) + '</p><h3>Evaluation checklist</h3><ul>']
    md = ['## ' + use['question'], use['question_zh'], '**Source-linked methodological synthesis:** '
          + use['answer'] + ' ' + md_refs(use['answer_source_ids']), use['answer_zh'], '### Evaluation checklist']
    for row in use['checklist']:
        body.append('<li><strong>' + esc(row['dimension']) + ':</strong> ' + esc(row['text']) + ' ' + refs(row['source_ids']) + '</li>')
        md.append('- **' + row['dimension'] + ':** ' + row['text'] + ' ' + md_refs(row['source_ids']))
    if 'task_workspace' in use:
        workspace_html, workspace_md = render_task_workspace(
            use['task_workspace'], guide_url, sid, refs, md_refs)
        body += ['</ul>', workspace_html, '<h3>How the selected papers contribute</h3><ul>']
        md += workspace_md
    else:
        body.append('</ul><h3>How the selected papers contribute</h3><ul>')
    md.append('### How the selected papers contribute')
    for row in use['study_roles']:
        study = study_by_id[row['work_id']]
        body.append('<li><strong><a href="#' + study['id'] + '">' + esc(row['role'])
                    + '</a>:</strong> ' + esc(row['text']) + ' ' + refs(row['source_ids']) + '</li>')
        md.append('- **[' + row['role'] + '](' + study['paper_url'] + '):** ' + row['text'] + ' ' + md_refs(row['source_ids']))
    body.append('</ul><div class="comparison" role="region" aria-label="Model evaluation evidence" tabindex="0"><table><caption>'
                + esc(use['comparison']['caption']) + '</caption><thead><tr><th>Paper / design</th><th>Population</th>'
                + '<th>Endpoint / horizon</th><th>Validation</th><th>Reported evaluation</th><th>Original source</th></tr></thead><tbody>')
    md += ['### ' + use['comparison']['caption'], '| Paper / design | Population | Endpoint / horizon | Validation | Reported evaluation | Original source |',
           '| --- | --- | --- | --- | --- | --- |']
    for row in use['comparison']['rows']:
        study = study_by_id[row['work_id']]
        body.append('<tr><th scope="row"><a href="' + esc(study['paper_url'], quote=True) + '">' + esc(study['title'])
                    + '</a><br>' + esc(row['design']) + '</th>'
                    + ''.join('<td>' + esc(row[key]) + '</td>' for key in ('population', 'endpoint', 'validation', 'metrics'))
                    + '<td><a href="' + esc(study['doi_url'], quote=True) + '">' + esc(row['doi']) + '</a> '
                    + refs(row['source_ids']) + '</td></tr>')
        cells = ['[' + study['title'] + '](' + study['paper_url'] + '); ' + row['design']]
        cells += [row[key] for key in ('population', 'endpoint', 'validation', 'metrics')]
        cells += ['[' + row['doi'] + '](' + study['doi_url'] + ') ' + md_refs(row['source_ids'])]
        md.append('| ' + ' | '.join(cell.replace('|', '\\|') for cell in cells) + ' |')
    body.append('</tbody></table></div><p>' + esc(use['comparison_note']) + ' ' + refs(use['comparison_note_source_ids']) + '</p><h3>Research applications</h3><ul>')
    md += [use['comparison_note'] + ' ' + md_refs(use['comparison_note_source_ids']), '### Research applications']
    for row in use['research_uses']:
        body.append('<li><strong>' + esc(row['use']) + ':</strong> ' + esc(row['text']) + ' ' + refs(row['source_ids']) + '</li>')
        md.append('- **' + row['use'] + ':** ' + row['text'] + ' ' + md_refs(row['source_ids']))
    body.append('</ul><h3>Sources and locators</h3><ol>')
    md.append('### Sources and locators')
    for source in use['sources']:
        body.append('<li id="' + sid + '-source-' + source['id'] + '"><a href="' + esc(source['url'], quote=True) + '">'
                    + esc(source['title']) + '</a> · DOI: <a href="https://doi.org/' + esc(source['doi'], quote=True) + '">'
                    + esc(source['doi']) + '</a> — ' + esc(source['locator']) + '</li>')
        md.append('- [' + source['title'] + '](' + source['url'] + ') · DOI: [' + source['doi']
                  + '](https://doi.org/' + source['doi'] + ') — ' + source['locator'])
    body.append('</ol></section>')
    return '\n'.join(body), md


def render_comparison(packet):
    esc = html.escape
    url = packet['canonical_url']
    contribution_first = packet.get('presentation') == 'contribution-first-v1'
    label = 'Selected author evidence guide' if contribution_first else 'Selected evidence comparison · not a research article'
    scope_tag = 'div' if contribution_first else 'aside'
    scope_style = ' style="padding:4px 20px;border-left:4px solid var(--strong-line,#52738b);background:var(--soft,#eef3f6)"' if contribution_first else ''
    link = lambda label, href: '<a href="' + esc(href, quote=True) + '">' + esc(label) + '</a>'
    def value_html(value):
        if isinstance(value, dict):
            return '<dl>' + ''.join('<dt>' + esc(k.replace('_', ' ')) + '</dt><dd>' + value_html(v) + '</dd>' for k, v in value.items()) + '</dl>'
        if isinstance(value, list): return '<ul>' + ''.join('<li>' + value_html(v) + '</li>' for v in value) + '</ul>'
        return esc(json.dumps(value) if not isinstance(value, str) else value)
    def value_md(value, level=0):
        if isinstance(value, dict):
            return '\n'.join('  '*level + '- **' + k.replace('_', ' ') + ':**\n' + value_md(v, level+1) for k,v in value.items())
        if isinstance(value, list): return '\n'.join('  '*level + '- ' + value_md(v, level+1).lstrip() for v in value)
        return '  '*level + (json.dumps(value) if not isinstance(value, str) else value)
    body = ['<nav>' + link('Publications', '../publications.html') + ' · ' + link('Markdown', url[:-5]+'.md') + ' · ' + link('Source matrix JSON', url[:-5]+'.json') + '</nav>',
            '<p class="eyebrow">' + label + '</p>',
            '<h1>' + esc(packet['title']) + '</h1><h2>' + esc(packet['question']) + '</h2>',
            '<' + scope_tag + ' id="scope"' + scope_style + '><p>' + esc(packet['scope']) + '</p><p>' + esc(packet['reading_rule']) + '</p></' + scope_tag + '>',
            '<div class="comparison" role="region" aria-label="Research task comparison" tabindex="0"><table><caption>Different research tasks and evidence types</caption><thead><tr><th>Research task</th><th>Reviewed design</th><th>Reviewed evidence type</th></tr></thead><tbody>']
    md = ['# ' + packet['title'], '**Selected author evidence guide**' if contribution_first else '**Selected evidence comparison — not a research article**',
          '[Canonical comparison](' + url + ')', '## ' + packet['question'], packet['scope'], packet['reading_rule']]
    if packet.get('research_use'):
        synthesis_html, synthesis_md = render_research_use(packet['research_use'], packet['studies'], url)
        # Keep every legacy guide byte-identical when the optional section is absent.
        body.insert(-1, synthesis_html)
        md += synthesis_md
    for s in packet['studies']:
        body.append('<tr><th scope="row">' + link(s['task'], '#'+s['id']) + '</th><td>' + esc(s['study_profile']['study_design']) + '</td><td>' + esc(s['study_profile']['evidence_type']) + '</td></tr>')
    body.append('</tbody></table></div>')
    for s in packet['studies']:
        base = 'https://drgezhang.com/citations/' + s['id']
        links = [('Author evidence page',s['paper_url']), ('Formal publication DOI',s['doi_url']),
                 ('BibTeX',base+'.bib'), ('RIS',base+'.ris'), ('CSL JSON',base+'.csl.json')]
        body += ['<article id="' + s['id'] + '"><h2>' + esc(s['task']) + '</h2><h3>' + esc(s['title']) + '</h3>']
        md += ['## ' + s['task'], '### ' + s['title']]
        if contribution_first:
            publication = s['publication']
            if 'authors' in publication:
                authors = '; '.join(publication['authors'])
                body.append('<p class="guide-publication-authors"><strong>Authors:</strong> ' + esc(authors) + '</p>')
                md.append('**Authors:** ' + authors)
            details = [(label, str(publication[key])) for key, label in
                       (('year', 'Year'), ('journal', 'Journal'), ('type', 'Publication type')) if key in publication]
            if details:
                body.append('<p class="guide-publication-details">' + esc(' · '.join(label + ': ' + value for label, value in details)) + '</p>')
                md.append(' · '.join('**' + label + ':** ' + value for label, value in details))
        body.append('<p>' + ' · '.join(link(label,href) for label,href in links) + '</p>')
        md.append(' · '.join('['+label+']('+href+')' for label,href in links))
        if not contribution_first:
            body.append('<h3>Reviewed study profile</h3>' + value_html(s['study_profile']))
            md += ['### Reviewed study profile', value_md(s['study_profile'])]
        for qa in s['selected_questions']:
            body.append('<section><h3>' + link(qa['question'], qa['answer_url']) + '</h3><p>' + esc(qa['answer']) + '</p><ul>')
            md += ['### ' + qa['question'], qa['answer'], '[Unchanged reviewed answer](' + qa['answer_url'] + ')']
            for f in qa['supporting_evidence']:
                href = s['paper_url'] + '#' + f['id'].lower()
                body.append('<li>' + link(f['id'],href) + ' — ' + esc(f['source_locator']) + '</li>')
                md.append('- ['+f['id']+']('+href+') — '+f['source_locator'])
            body.append('</ul></section>')
        if contribution_first:
            body.append('<h3>Reviewed study profile</h3>' + value_html(s['study_profile']))
            md += ['### Reviewed study profile', value_md(s['study_profile'])]
        for key,label in [('evidence_scope','Complete reviewed evidence scope'),('limitations','Complete reviewed limitations')]:
            body.append('<h3>' + label + '</h3>' + value_html(s[key]))
            md += ['### ' + label, value_md(s[key])]
        body.append('</article>')
    # Reuse the existing guide's minimal reading styles, not a new UI system.
    schema = {'@context':'https://schema.org', '@type':'WebPage', 'name':packet['title'], 'url':url, 'description':packet['scope']}
    head = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    head += '<title>'+esc(packet['title'])+'</title><meta name="description" content="'+esc(packet['scope'],quote=True)+'">'
    head += '<link rel="canonical" href="'+url+'"><link rel="alternate" type="text/markdown" href="'+url[:-5]+'.md">'
    head += '<link rel="alternate" type="application/json" href="'+url[:-5]+'.json">'
    head += '<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script>'
    page = with_theme_shell(head + GUIDE_READING_STYLE + '</head><body><main>\n' + '\n'.join(body) + '\n</main></body></html>\n', guide=True)
    validate_page(page, url)
    return page, '\n\n'.join(md)+'\n', json.dumps(packet,ensure_ascii=False,indent=2)+'\n'


def build_comparisons(root=ROOT, validate_only=False):
    changed = {}
    for data in load_comparisons(root):
        packet = comparison_packet(data, root)
        rendered = render_comparison(packet)
        outputs = list(zip(('html', 'md', 'json'), rendered))
        workspace = packet.get('research_use', {}).get('task_workspace')
        if workspace is not None:
            outputs += [('worksheet.csv', task_workspace_csv(workspace)),
                        ('blank.csv', task_workspace_csv(workspace, blank=True))]
        for ext,text in outputs:
            path = root/'research'/(data['slug']+'.'+ext)
            is_csv = ext.endswith('.csv')
            previous = ((path.read_bytes().decode('utf-8') if is_csv else path.read_text(encoding='utf-8'))
                        if path.exists() else None)
            if validate_only: require(previous == text, 'Comparison differs from source-bound rendering: '+ext)
            elif previous != text:
                if is_csv: path.write_bytes(text.encode('utf-8'))
                else: path.write_text(text,encoding='utf-8')
            if ext == 'html': changed[comparison_url(data)] = previous is None or without_theme_shell(previous) != without_theme_shell(text)
    return changed


def comparison_search_documents(root, start):
    """Append guide navigation without renumbering existing paper/QA records."""
    docs = []
    research_uses = []
    for data in load_comparisons(root):
        packet = comparison_packet(data, root)
        if packet.get('research_use'):
            research_uses.append((packet, packet['research_use']))
        for s in packet['studies']:
            for qa in s['selected_questions']:
                docs.append({'id':start+len(docs), 'result_kind':'guide', 'doi':'',
                             'title':packet['title'], 'category':'Selected evidence comparison',
                             'text':qa['question']+'\n'+qa['answer'],
                             'url':packet['canonical_url']+'#'+s['id'], 'limitation':False})
    # Keep existing guide IDs stable; the new answer comes from the same
    # reviewed controller and visible section, not a second answer database.
    for packet, use in research_uses:
        docs.append({'id':start+len(docs), 'result_kind':'guide', 'doi':'',
                     'title':packet['title'], 'category':'Research-use answer',
                     'text':use['question']+'\n'+use['answer'],
                     'url':packet['canonical_url']+'#'+use['id'], 'limitation':False})
    return docs


if __name__ == "__main__":
    build()
    build_comparisons()
    print('GUIDE PASS:', validate())
