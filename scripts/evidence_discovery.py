"""Deterministic, visible-text-only discovery helpers; no network dependencies."""
import html
import json
import re
from html.parser import HTMLParser

UI_START = '<!-- EVIDENCE_UI_START -->'
UI_END = '<!-- EVIDENCE_UI_END -->'


def ui(markup):
    return UI_START + markup + UI_END


def without_evidence_ui(page):
    """Exclude explicitly marked navigation/controls from content-date comparison.

    Does not exclude any scientific text. IndexNow still diffs actual HTML bytes.
    The legacy publications filter is replaced by progressive discovery UI.
    """
    page = re.sub(re.escape(UI_START) + r'.*?' + re.escape(UI_END), '', page, flags=re.S)
    page = re.sub(r' id="ev-(?:summary|findings|scope)"', '', page)
    page = re.sub(r'<script>\s*const box=document.getElementById\(\'pubSearch\'\);.*?</script>', '', page, flags=re.S)
    return page


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def visible_text(page):
    parser = VisibleText()
    parser.feed(without_evidence_ui(page))
    return '\n'.join(parser.parts)


def navigation_html(root, items):
    entries = json.loads((root / 'data/evidence_navigation.json').read_text(encoding='utf-8'))
    by_doi = {p.get('doi', '').lower(): p for p in items}
    rows = []
    for entry in entries:
        p = by_doi[entry['doi']]
        url = p['paper_url']
        page = (root / 'papers' / (p['slug'] + '.html')).read_text(encoding='utf-8')
        anchor = entry.get('anchor')
        if anchor and f'id="{anchor}"' in page:
            url += '#' + anchor
        rows.append('<li><a href="' + html.escape(url, quote=True) + '">' + html.escape(entry['question'])
                    + '</a><p>' + html.escape(p['title']) + '</p></li>')
    return ui('<section id="scientific-questions"><h2>Browse by scientific question</h2>'
              '<p>Selected questions addressed by publications in this research program; '
              'not a systematic or exhaustive review of the field.</p><ol>' + ''.join(rows) + '</ol></section>')


def search_corpus(root, items, contents):
    """Each document is a visible field/section, preserving negative-field context."""
    documents = []
    for p in items:
        url = p['paper_url']
        page = (root / 'papers' / (p['slug'] + '.html')).read_text(encoding='utf-8')
        visible = visible_text(page)
        def add(category, texts, anchor='', limitation=False):
            texts = [str(t) for t in texts if t]
            # Authors may not be visibly rendered on metadata-incomplete records.
            if not texts:
                return
            for text in texts:
                if text not in visible:
                    raise ValueError(f'Search text not visibly present: {p["slug"]}/{category}: {text}')
            if anchor and f'id="{anchor}"' not in page:
                anchor = ''
            documents.append({'id': len(documents), 'doi': p.get('doi', ''), 'title': p['title'],
                              'category': category, 'text': '\n'.join(texts),
                              'url': url + ('#' + anchor if anchor else ''), 'limitation': limitation})
        add('Title', [p['title']])
        add('Journal', [p.get('journal')])
        add('DOI', [p['doi']] if p.get('doi') and p['doi'] in visible else [])
        add('Authors', [a for a in p.get('authors', []) if a in visible])
        c = contents.get(p.get('doi', '').lower())
        if not c or c.get('version') != 2:
            continue
        add('Research question', [c['research_question']])
        add('Evidence summary', [c['summary'], c['author_summary']], 'ev-summary')
        add('Concepts', [s for values in c.get('concepts', {}).values() for s in values])
        argument = c['study_profile'].get('narrative_genre') in ('perspective', 'correspondence')
        for f in c['key_findings']:
            add('Key argument' if argument else 'Key finding',
                [f['claim'], f['context'], *[x[k] for x in f['evidence'] for k in ('label','value')], f['source_locator']], f['id'].lower())
        for q in c['qa']:
            add('Q&A', [q['question'], q['answer']])
        for row in c.get('citation_layer', {}).get('citation_use_cases', []):
            add('Citation use case', [row['query'], row['supported_scope']], row['id'].lower())
        add('Evidence scope — supports', c['evidence_scope']['supports'], 'ev-scope')
        add('Limitations — does not establish', c['evidence_scope']['does_not_establish'], 'ev-scope', True)
        add('Limitations', c['limitations'], 'ev-scope', True)
    return {'version': 1, 'description': 'Visible public text for local text-relevance search; no generated answers or evidence-strength ranking.', 'documents': documents}
