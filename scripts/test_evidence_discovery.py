"""Focused deterministic discovery checks, without network or build side effects."""
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit
from evidence_discovery import search_corpus, visible_text, without_evidence_ui
from sync_common import ROOT, is_withdrawn, load_master
from build_publications import load_deep_content


def check():
    public = json.loads((ROOT / 'publications.json').read_text(encoding='utf-8'))
    content = {p.get('doi',''): load_deep_content(p, allow_missing=True) for p in public if p['deep_geo']}
    data = json.loads((ROOT / 'assets/evidence-search.json').read_text(encoding='utf-8'))
    assert data == search_corpus(ROOT, public, content)
    assert len({d['url'].split('#')[0] for d in data['documents'] if d['result_kind']=='paper'}) == len(public)
    guides = [d for d in data['documents'] if d['result_kind']=='guide']
    assert len({d['url'].split('#')[0] for d in guides}) == 1 and all(d['doi']=='' for d in guides)
    for d in data['documents']:
        u = urlsplit(d['url'])
        page = (ROOT / u.path.lstrip('/')).read_text(encoding='utf-8')
        assert not u.fragment or f'id="{u.fragment}"' in page
    withdrawn = [p for p in load_master() if is_withdrawn(p)]
    assert not any(d['doi'] == p.get('doi') for d in data['documents'] for p in withdrawn)
    page = (ROOT / 'publications.html').read_text(encoding='utf-8')
    assert page.count('data-paper-record="true"') == len(public)
    for item in json.loads((ROOT / 'data/evidence_navigation.json').read_text(encoding='utf-8')):
        assert html.escape(item['question']) in page
    source = json.loads((ROOT / 'assets/vendor/minisearch-7.2.0/SOURCE.json').read_text())
    for name, digest in source['files'].items():
        assert hashlib.sha256((ROOT / 'assets/vendor/minisearch-7.2.0' / name).read_bytes()).hexdigest() == digest
    a='<p>Scientific qualifier: not validated.</p>'
    b=a+'<!-- EVIDENCE_UI_START --><button>UI</button><!-- EVIDENCE_UI_END -->'
    assert without_evidence_ui(a)==without_evidence_ui(b)
    assert without_evidence_ui(a)!=without_evidence_ui(a.replace('not validated','validated'))
    print('DISCOVERY PASS: exact deterministic visible corpus, anchors, 74 static records, withdrawn exclusion, vendor hashes, content-date boundary')


if __name__ == '__main__':
    check()
