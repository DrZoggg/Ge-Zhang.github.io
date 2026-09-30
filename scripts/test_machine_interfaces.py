"""Offline fail-closed contracts for public citation/identity interfaces."""
import json
import unittest
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from sync_common import ROOT
from citation_common import citation_skip_reason, load_citation_metadata
from scholarly_discovery import load_identifiers

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__(); self.links=[]; self.ids=[]; self.meta={};self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('link','a'):self.links.append(a)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='meta':self.meta.setdefault(a.get('name',''),[]).append(a.get('content',''))

def local(url):
    parsed=urlparse(url)
    if parsed.netloc!='drgezhang.com':raise ValueError('Noncanonical URL')
    p=ROOT/parsed.path.lstrip('/')
    if not p.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Unsafe path')
    return p

def validate_interfaces(root=ROOT):
    items=json.loads((root/'publications.json').read_text(encoding='utf-8'))
    index=json.loads((root/'paper_index.json').read_text(encoding='utf-8'))
    assert index['version']==2
    by_url={p['paper_url']:p for p in index['papers']}
    identifiers=load_identifiers(items,load_citation_metadata(items),root)
    publication=Document((root/'publications.html').read_text(encoding='utf-8'))
    for item in items:
        text=(root/'papers'/f'{item["slug"]}.html').read_text(encoding='utf-8');p=Document(text)
        assert len(p.ids)==len(set(p.ids)),item['slug']+' duplicate anchor'
        eligible=not citation_skip_reason(item);row=by_url[item['paper_url']]
        csl=[l for l in p.links if l.get('type')=='application/vnd.citationstyles.csl+json']
        cite=[l for l in p.links if l.get('rel')=='cite-as']
        assert bool(csl)==bool(cite)==eligible
        for field,suffix in [('citation_csl_json_url','.csl.json'),('citation_bibtex_url','.bib'),('citation_ris_url','.ris')]:
            expected='https://drgezhang.com/citations/'+item['slug']+suffix if eligible else None
            assert row[field]==expected
            if eligible:assert local(expected).is_file()
        if eligible:
            assert cite==[{'rel':'cite-as','href':'https://doi.org/'+item['doi']}]
            assert any(l.get('href')==f'papers/{item["slug"]}.html#cite-this-paper' for l in publication.links)
        for l in p.links:
            if l.get('rel')=='alternate':assert local(urljoin(item['paper_url'],l['href'])).is_file()
        assert row['official_abstract_available']==('official-abstract' in p.ids)
        assert type(row['question_count']) is int and type(row['concept_count']) is int
        if row['evidence_csv_url']:assert local(row['evidence_csv_url']).is_file()
        for key in ['pmid','pmcid','openalex_id','semantic_scholar_id','publisher_url']:
            if key in identifiers.get(item.get('doi'),{}):assert row[key]==identifiers[item['doi']][key]
    return {'public':len(items),'eligible':sum(not citation_skip_reason(p) for p in items)}

class MachineTests(unittest.TestCase):
    def test_interfaces(self):validate_interfaces()
    def test_unsafe_target(self):
        for url in ['https://other.example/papers/a.html','https://drgezhang.com/../../private']:
            with self.assertRaises(ValueError):local(url)
if __name__=='__main__':unittest.main()
