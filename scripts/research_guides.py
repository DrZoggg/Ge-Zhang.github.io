"""One reviewed, selective guide. Source drift requires explicit scientific re-review.

The frozen-text digest is a contract check, not independent scientific verification.
No network, new publication records, citation exports, or scientific inference.
"""
import hashlib
import html
import json
from pathlib import Path
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
COMPARISONS = {'circadian-evidence-levels': '4dde76f203b9d4705ca90767f10538a60a1420b929d9f76770c11231cc193781'}


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
    require(len({s['doi'] for s in studies}) == len(studies), 'Duplicate DOI in comparison')
    return {'version': 1, 'kind': 'selective_author_evidence_comparison',
            **{k: data[k] for k in ('title', 'question', 'scope', 'reading_rule')},
            'canonical_url': comparison_url(data), 'studies': studies}


def render_comparison(packet):
    esc = html.escape
    url = packet['canonical_url']
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
            '<p class="eyebrow">Selected evidence comparison · not a research article</p>',
            '<h1>' + esc(packet['title']) + '</h1><h2>' + esc(packet['question']) + '</h2>',
            '<aside id="scope"><p>' + esc(packet['scope']) + '</p><p>' + esc(packet['reading_rule']) + '</p></aside>',
            '<div class="comparison" role="region" aria-label="Research task comparison" tabindex="0"><table><caption>Different research tasks and evidence types</caption><thead><tr><th>Research task</th><th>Reviewed design</th><th>Reviewed evidence type</th></tr></thead><tbody>']
    md = ['# ' + packet['title'], '**Selected evidence comparison — not a research article**',
          '[Canonical comparison](' + url + ')', '## ' + packet['question'], packet['scope'], packet['reading_rule']]
    for s in packet['studies']:
        body.append('<tr><th scope="row">' + link(s['task'], '#'+s['id']) + '</th><td>' + esc(s['study_profile']['study_design']) + '</td><td>' + esc(s['study_profile']['evidence_type']) + '</td></tr>')
    body.append('</tbody></table></div>')
    for s in packet['studies']:
        base = 'https://drgezhang.com/citations/' + s['id']
        links = [('Author evidence page',s['paper_url']), ('Formal publication DOI',s['doi_url']),
                 ('BibTeX',base+'.bib'), ('RIS',base+'.ris'), ('CSL JSON',base+'.csl.json')]
        body += ['<article id="' + s['id'] + '"><h2>' + esc(s['task']) + '</h2><h3>' + esc(s['title']) + '</h3>',
                 '<p>' + ' · '.join(link(label,href) for label,href in links) + '</p>',
                 '<h3>Reviewed study profile</h3>' + value_html(s['study_profile'])]
        md += ['## ' + s['task'], '### ' + s['title'], ' · '.join('['+label+']('+href+')' for label,href in links),
               '### Reviewed study profile', value_md(s['study_profile'])]
        for qa in s['selected_questions']:
            body.append('<section><h3>' + link(qa['question'], qa['answer_url']) + '</h3><p>' + esc(qa['answer']) + '</p><ul>')
            md += ['### ' + qa['question'], qa['answer'], '[Unchanged reviewed answer](' + qa['answer_url'] + ')']
            for f in qa['supporting_evidence']:
                href = s['paper_url'] + '#' + f['id'].lower()
                body.append('<li>' + link(f['id'],href) + ' — ' + esc(f['source_locator']) + '</li>')
                md.append('- ['+f['id']+']('+href+') — '+f['source_locator'])
            body.append('</ul></section>')
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
        rendered = render_comparison(comparison_packet(data, root))
        for ext,text in zip(('html','md','json'),rendered):
            path = root/'research'/(data['slug']+'.'+ext)
            previous = path.read_text(encoding='utf-8') if path.exists() else None
            if validate_only: require(previous == text, 'Comparison differs from source-bound rendering: '+ext)
            elif previous != text: path.write_text(text,encoding='utf-8')
            if ext == 'html': changed[comparison_url(data)] = previous is None or without_theme_shell(previous) != without_theme_shell(text)
    return changed


def comparison_search_documents(root, start):
    """Append guide navigation without renumbering existing paper/QA records."""
    docs = []
    for data in load_comparisons(root):
        packet = comparison_packet(data, root)
        for s in packet['studies']:
            for qa in s['selected_questions']:
                docs.append({'id':start+len(docs), 'result_kind':'guide', 'doi':'',
                             'title':packet['title'], 'category':'Selected evidence comparison',
                             'text':qa['question']+'\n'+qa['answer'],
                             'url':packet['canonical_url']+'#'+s['id'], 'limitation':False})
    return docs


if __name__ == "__main__":
    build()
    build_comparisons()
    print('GUIDE PASS:', validate())
