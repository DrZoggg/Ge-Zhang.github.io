"""One reviewed, selective guide. Source drift requires explicit scientific re-review.

The frozen-text digest is a contract check, not independent scientific verification.
No network, new publication records, citation exports, or scientific inference.
"""
import hashlib
import html
import json
from pathlib import Path
from sync_common import ROOT, is_withdrawn

SLUG = 'dcm-hf-circulating-biomarkers'
URL = 'https://drgezhang.com/research/' + SLUG + '.html'
DATA = 'data/research_guides/' + SLUG + '.json'
CONTRACT_SHA256 = '682e83660b7c8cbbb4d70c409c935d2b8c765272cdf1c6a26255e4d190551c45'
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
        require(fingerprint(c) == row['source_fingerprint'], 'Scientific source changed: re-review guide before publishing')
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
    for prop, value in [('og:type', 'website'), ('og:title', data['title']), ('og:description', data['scope']), ('og:url', URL)]:
        page += '<meta property="' + prop + '" content="' + esc(value, quote=True) + '">\n'
    page += '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c') + '</script>\n'
    page += '<style>body{font:17px/1.65 system-ui,sans-serif;color:#172b3a;background:#fafcfd;margin:0}main{max-width:1120px;margin:auto;padding:24px;overflow-wrap:anywhere}h1{font-size:clamp(1.7rem,4vw,2.4rem);line-height:1.2}h2{margin-top:2rem}a{color:#075d93}aside{padding:4px 20px;border-left:4px solid #52738b;background:#eef3f6}.eyebrow{color:#486275}.comparison{max-width:100%;overflow-x:auto;margin:2rem 0}table{border-collapse:collapse;min-width:900px;width:100%;font-size:15px}caption{text-align:left;font-weight:bold;padding:12px}th,td{border:1px solid #bdcdd8;padding:14px;vertical-align:top;text-align:left}thead{background:#e7eff5}th[scope=row]{min-width:170px}td{min-width:150px}article{margin:2rem 0}li{margin:.4rem 0}@media(max-width:480px){main{padding:16px}}</style></head><body><main>\n'
    return page + '\n'.join(body) + '\n</main></body></html>\n', '\n\n'.join(md) + '\n'


def validate_page(page):
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
    require(p.h1 == 1 and p.canonical == [URL], 'Guide identity/canonical mismatch')
    require('ScholarlyArticle' not in page and 'FAQPage' not in page, 'Guide is WebPage only')


def build(root=ROOT):
    data = load(root); sources = resolve(data, root)
    rendered = render(data, sources)
    validate_page(rendered[0])
    changed = False
    for extension, text in zip(('html', 'md'), rendered):
        path = root / 'research' / (SLUG + '.' + extension)
        different = not path.exists() or path.read_text(encoding='utf-8') != text
        if different:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        if extension == 'html': changed = different
    return changed


def validate(root=ROOT):
    data = load(root); sources = resolve(data, root)
    expected = render(data, sources)
    for ext, text in zip(('html', 'md'), expected):
        require((root / 'research' / (SLUG + '.' + ext)).read_text(encoding='utf-8') == text, 'Guide differs from reviewed rendering')
    validate_page(expected[0])
    return {'guides': 1, 'sources': 3, 'source_KFs': 11}


if __name__ == '__main__':
    build(); print('GUIDE PASS:', validate())
