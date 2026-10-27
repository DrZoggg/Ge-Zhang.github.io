"""Freeze the 55-V2 release while adding only approved non-V2 source notes."""
import copy
import hashlib
import json
import subprocess
import unittest
from xml.etree import ElementTree
from sync_common import ROOT
import limited_evidence as notes

REVIEW=json.loads((ROOT/'scripts/fixtures/limited_evidence_release_20261027.json').read_text(encoding='utf-8'))
BASE=REVIEW['base_sha']
def old(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).replace(b'\r\n',b'\n')
def now(path):return (ROOT/path).read_bytes().replace(b'\r\n',b'\n')


class LimitedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public=json.loads(now('publications.json'))
        cls.records=notes.load(cls.public)
        cls.bydoi={p['doi']:p for p in cls.public if p.get('doi')}

    def test_reviewed_notes_are_exact_and_never_upgrade_status(self):
        self.assertEqual(self.public,json.loads(old('publications.json')))
        self.assertEqual(len(self.public),REVIEW['public_works'])
        self.assertEqual(sum(p['paper_geo_status']=='v2' for p in self.public),REVIEW['baseline_v2'])
        self.assertEqual(len(self.records),REVIEW['limited_evidence_pages'])
        self.assertEqual(hashlib.sha256(now('data/limited_evidence.json')).hexdigest(),REVIEW['data_sha256'])
        self.assertEqual(set(self.records),set(REVIEW['papers']))
        for doi,r in self.records.items():
            encoded=json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
            self.assertEqual(hashlib.sha256(encoded).hexdigest(),REVIEW['papers'][doi]['content_sha256'])
            self.assertEqual(self.bydoi[doi]['paper_geo_status'],'none')
            self.assertNotIn('key_findings',r)
            self.assertNotIn('qa',r)
        self.assertEqual(notes.validate_generated(self.public),{'limited_evidence_pages':21,'full_v2_status_changed':False})

    def test_note_removal_restores_every_target_page_and_schema_exactly(self):
        for doi,r in self.records.items():
            slug=r['slug']
            for ext,render in [('html',notes.render_html),('md',notes.render_markdown)]:
                path='papers/'+slug+'.'+ext
                before=old(path).decode();after=now(path).decode();block=render(r)+('' if ext=='html' else '\n')
                self.assertEqual(after.count(block),1,path)
                self.assertEqual(after.replace(block,'',1),before,path)
                if ext=='html':
                    self.assertNotIn('Paper GEO V2</span>',after)
                    for row in r['sections']:
                        self.assertIn(row['source_url'].replace('&','&amp;'),after)
        cia=self.records['10.2147/cia.s493841']
        self.assertIn('1.43–6.72',cia['sections'][1]['text'])
        self.assertIn('sample size remains unspecified',cia['sections'][1]['text'])
        rpe=self.records['10.3980/j.issn.1672-5123.2020.12.13']
        self.assertIn('张格',rpe['sections'][-1]['text']);self.assertIn('张戈',rpe['sections'][-1]['text'])

    def test_all_existing_science_identity_citations_and_visuals_are_frozen(self):
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','data/deep_geo','citations','assets','index.html','data/publications_master.json','data/featured_papers.json','data/deep_geo_papers.json','data/profile_config.json','data/homepage_author_roles.json','data/patent_evidence.json','paper_index.json','publication_inventory.csv','publications.html','research','robots.txt','CNAME','.github','scripts/sync_common.py'],cwd=ROOT,text=True).splitlines()
        for path in paths:self.assertEqual(now(path),old(path),path)
        target_slugs={r['slug'] for r in self.records.values()}
        for p in self.public:
            if p['slug'] not in target_slugs:
                for ext in ['html','md']:
                    path='papers/'+p['slug']+'.'+ext
                    self.assertEqual(now(path),old(path),path)
        def sitemap(raw):
            return {e.find('{*}loc').text:e.find('{*}lastmod').text for e in ElementTree.fromstring(raw)}
        before=sitemap(old('sitemap.xml'));after=sitemap(now('sitemap.xml'))
        self.assertEqual(set(before),set(after))
        targets={self.bydoi[doi]['paper_url'] for doi in self.records}
        for url in before:
            if url not in targets:self.assertEqual(before[url],after[url],url)

    def test_invalid_or_unsourced_notes_fail_closed(self):
        doi,r=next(iter(self.records.items()));publication=self.bydoi[doi]
        for mutate in [lambda c:c.update(evidence_status='v2'),lambda c:c['sections'][0].pop('source_locator'),lambda c:c['sections'][0].update(source_url='javascript:alert(1)'),lambda c:c.update(slug='different-identity'),lambda c:c.update(limitations=[])]:
            bad=copy.deepcopy(r);mutate(bad)
            with self.assertRaises(ValueError):notes.validate_record(doi,bad,publication)
        with self.assertRaises(ValueError):notes.validate_record(doi,r,dict(publication,paper_geo_status='v2'))
        with self.assertRaises(ValueError):notes.validate_record(doi,r,dict(publication,type='Patent'))


if __name__=='__main__':unittest.main()
