"""Verified Highwire identity, not a claim of Google Scholar inclusion."""
import copy
import html
import json
import unittest
from build_publications import render_paper_html
from citation_common import citation_record, highwire_first_page, load_citation_metadata, validate_fulltext_pdf
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
    pdf = record.get('fulltext_pdf') if record else None
    require(meta_contents(page,'citation_pdf_url') == ([pdf['url']] if pdf else []),
            'unverified or mismatched hosted PDF')
    if record:
        expected_date=record.get('publication_date',str(item['year'])).replace('-','/')
        require(meta_contents(page,'citation_publication_date')==[expected_date], 'publication date')
        for source,tag in [('volume','citation_volume'),('issue','citation_issue'),
                           ('first_page','citation_firstpage'),('last_page','citation_lastpage'),
                           ('article_number','citation_article_number'),('pmid','citation_pmid'),
                           ('publisher','citation_publisher'),('eissn','citation_eIssn')]:
            value = highwire_first_page(record) if source == 'first_page' else record.get(source)
            require(meta_contents(page,tag)==([value] if value else []),tag+' mismatch')
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
    def test_verified_article_locators_are_emitted_only_for_the_reviewed_cohort(self):
        items = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
        metadata = load_citation_metadata(items)
        expected = {
            "10.1038/s41467-024-50415-9": "6756",
            "10.1038/s41598-024-65236-5": "14155",
            "10.1038/s41598-025-98859-3": "15916",
            "10.1186/s12915-025-02400-x": "280",
            "10.3389/fpubh.2025.1521372": "1521372",
            "10.3389/fcvm.2025.1724572": "1724572",
            "10.3389/fonc.2021.659217": "659217",
            "10.1371/journal.pone.0346326": "e0346326",
            "10.1016/j.isci.2023.107587": "107587",
            "10.1111/jcmm.70258": "e70258",
            "10.1111/jcmm.70725": "e70725",
            "10.1155/humu/5591097": "5591097",
            "10.1186/s12931-024-02978-w": "365",
            "10.1186/s12967-022-03795-9": "568",
            "10.15212/cvia.2024.0023": "e956",
            "10.1007/s10238-024-01439-4": "169",
            "10.1186/s12943-024-02047-2": "131",
            "10.1038/s41598-024-80885-2": "30755",
            "10.1016/j.cmpbup.2024.100164": "100164",
            "10.1111/jcmm.70475": "e70475",
            "10.1002/clc.70019": "e70019",
            "10.1172/jci194175": "e194175",
            "10.1136/jitc-2024-010127": "e010127",
            "10.1002/ggn2.202500053": "e00053",
        }
        self.assertEqual({doi: fields["highwire_article_locator"]["value"]
                          for doi, fields in metadata.items()
                          if "highwire_article_locator" in fields}, expected)
        for item in items:
            if item.get("doi") in expected:
                page = (ROOT / "papers" / f'{item["slug"]}.html').read_text(encoding="utf-8")
                self.assertEqual(meta_contents(page, "citation_firstpage"), [expected[item["doi"]]])
                self.assertEqual(meta_contents(page, "citation_lastpage"), [])
        config = load_site_config()
        item = next(item for item in items if item.get("doi") == "10.1038/s41598-025-98859-3")
        record = citation_record(item, metadata, config["site_url"])
        for pagination, expected_first in (
            ({"first_page": "12", "last_page": "19"}, ["12"]),
            ({"last_page": "19"}, []),
        ):
            page = render_paper_html(item, config=config, citation_data={**record, **pagination})
            self.assertEqual(meta_contents(page, "citation_firstpage"), expected_first)
            self.assertEqual(meta_contents(page, "citation_lastpage"), ["19"])
            self.assertEqual(meta_contents(page, "citation_article_number"), ["15916"])

    def test_hosted_pdf_requires_reviewed_bytes_and_identity_path(self):
        items=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        item=next(p for p in items if p.get('doi')=='10.1002/ctm2.70900')
        record=load_citation_metadata(items)[item['doi']]
        for key,value in [('url','https://drgezhang.com/assets/fulltext/ctm2-70900.pdf'),
                          ('sha256','0'*64), ('version','unknown'),
                          ('version','publisher_accepted_manuscript')]:
            pdf=copy.deepcopy(record['fulltext_pdf']);pdf[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_fulltext_pdf(pdf,item,record['verified_sources'])

    def test_reviewed_accepted_pdf_cannot_be_labelled_version_of_record(self):
        items=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        item=next(p for p in items if p.get('doi')=='10.1097/re9.0000000000000037')
        record=load_citation_metadata(items)[item['doi']]
        pdf=copy.deepcopy(record['fulltext_pdf'])
        pdf['version']='version_of_record'
        with self.assertRaises(ValueError):
            validate_fulltext_pdf(pdf,item,record['verified_sources'])

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
