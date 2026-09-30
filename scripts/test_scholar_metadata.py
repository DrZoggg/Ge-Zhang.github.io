"""Verified Highwire identity, not a claim of Google Scholar inclusion."""
import copy
import html
import json
import unittest
from citation_common import citation_record, load_citation_metadata
from sync_common import ROOT, load_master, is_withdrawn, publication_authors
from site_common import load_site_config
from validate_site import meta_contents, json_ld_objects


def validate_metadata(page, item, record):
    def require(ok, label):
        if not ok: raise ValueError(label)
    for key, expected in [('citation_title',[item['title']]),
                          ('citation_journal_title',[item['journal']]),
                          ('citation_author',publication_authors(item)),
                          ('citation_doi',[item['doi']] if item.get('doi') else [])]:
        require(meta_contents(page,key)==expected, key+' mismatch')
    require('<h1 ' in page and html.escape(item['title']) in page,'visible title')
    require(not meta_contents(page,'citation_pdf_url'),'unverified hosted PDF')
    if record:
        expected_date=record.get('publication_date',str(item['year'])).replace('-','/')
        require(meta_contents(page,'citation_publication_date')==[expected_date], 'publication date')
        for source,tag in [('volume','citation_volume'),('issue','citation_issue'),
                           ('first_page','citation_firstpage'),('last_page','citation_lastpage'),
                           ('article_number','citation_article_number'),('pmid','citation_pmid'),
                           ('publisher','citation_publisher'),('eissn','citation_eIssn')]:
            require(meta_contents(page,tag)==([record[source]] if record.get(source) else []),tag+' mismatch')
        issn=record.get('issn') or record.get('eissn')
        require(meta_contents(page,'citation_issn')==([issn] if issn else []),'citation_issn mismatch')
        for author in record['authors']:
            require(html.escape(author) in page.split('</head>',1)[1],'author not visible')
    schemas=json_ld_objects(page)
    require(not any(s.get('@type') in ('FAQPage','QAPage') for s in schemas),'unfounded Q&A schema')
    article=[s for s in schemas if s.get('@type')=='ScholarlyArticle']
    if article:
        require(len(article)==1,'multiple scholarly works')
        s=article[0]
        require(s['name']==s['headline']==item['title'],'schema title')
        require(s['url']==s['mainEntityOfPage']==item['paper_url'],'schema canonical')


class ScholarMetadataTests(unittest.TestCase):
    def test_all_public(self):
        items=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        metadata=load_citation_metadata(items)
        for item in items:
            with self.subTest(slug=item['slug']):
                validate_metadata((ROOT/'papers'/f'{item["slug"]}.html').read_text(encoding='utf-8'),
                                  item,citation_record(item,metadata,load_site_config()['site_url']))
    def test_reject_drift(self):
        items=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        item=next(p for p in items if p['slug']=='aihflevel')
        record=citation_record(item,load_citation_metadata(items),load_site_config()['site_url'])
        page=(ROOT/'papers/aihflevel.html').read_text(encoding='utf-8')
        mutations=[page.replace('name="citation_doi"','name="lost_doi"',1),
                   page.replace('content="6756"','content="999"',1),
                   page.replace('</head>','<meta name="citation_firstpage" content="6756"></head>',1),
                   page.replace('</head>','<meta name="citation_doi" content="10.9999/wrong"></head>',1)]
        authors=meta_contents(page,'citation_author')
        a,b=[f'<meta name="citation_author" content="{html.escape(x,quote=True)}">' for x in authors[:2]]
        mutations += [page.replace(a,'',1),page.replace(a,'SWAP',1).replace(b,a,1).replace('SWAP',b,1)]
        for changed in mutations:
            with self.assertRaises(ValueError):validate_metadata(changed,item,record)
if __name__=='__main__':unittest.main()
