"""Preserve historical note approvals and the current approved publication baseline.

The presentation fixture permits one exact note revision. Historical scientific
fixtures remain unchanged; later approved site and identity fixes are retained.
"""
import copy
import hashlib
import json
import subprocess
import types
import unittest
from xml.etree import ElementTree
from sync_common import ROOT
import limited_evidence as notes
import author_account_release_contract as author_release

REVIEW=json.loads((ROOT/'scripts/fixtures/limited_evidence_release_20261027.json').read_text(encoding='utf-8'))
PRESENTATION=json.loads((ROOT/'scripts/fixtures/limited_evidence_presentation_20261104.json').read_text(encoding='utf-8'))
BASE=PRESENTATION['base_sha']
def old(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).replace(b'\r\n',b'\n')
def now(path):return (ROOT/path).read_bytes().replace(b'\r\n',b'\n')


class LimitedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public=json.loads(now('publications.json'))
        cls.records=notes.load(cls.public)
        cls.bydoi={p['doi']:p for p in cls.public if p.get('doi')}
        cls.baseline_records=json.loads(old('data/limited_evidence.json'))['papers']
        cls.baseline_renderer=types.ModuleType('historical_limited_evidence')
        exec(compile(old('scripts/limited_evidence.py'), 'historical_limited_evidence.py', 'exec'),
             cls.baseline_renderer.__dict__)

    def test_reviewed_notes_are_exact_and_never_upgrade_status(self):
        self.assertEqual(self.public,author_release.with_upgrades(json.loads(old('publications.json'))))
        self.assertEqual(len(self.public),REVIEW['public_works'])
        additions=len(author_release.RELEASE['papers'])
        self.assertEqual(sum(p['paper_geo_status']=='v2' for p in self.public),REVIEW['baseline_v2']+additions)
        self.assertEqual(len(self.records),REVIEW['limited_evidence_pages']-additions)
        self.assertEqual(hashlib.sha256(author_release.old('data/limited_evidence.json')).hexdigest(),REVIEW['data_sha256'])
        expected=author_release.reviewed_note_rows(REVIEW['papers'])
        inherited=PRESENTATION['inherited_note_revisions']
        self.assertEqual(set(inherited),{'10.3980/j.issn.1672-5123.2020.12.13'})
        for doi,revision in inherited.items():
            self.assertEqual(expected[doi]['content_sha256'],revision['historical_content_sha256'])
            self.assertEqual(author_release.canonical_hash(self.baseline_records[doi]),revision['approved_baseline_content_sha256'])
            self.assertEqual(self.records[doi],self.baseline_records[doi])
            expected[doi]=dict(expected[doi],content_sha256=revision['approved_baseline_content_sha256'])
        updates=PRESENTATION['note_updates']
        self.assertEqual(set(updates),{'10.1371/journal.pone.0346326'})
        for doi,update in updates.items():
            baseline=self.baseline_records[doi]
            self.assertEqual(expected[doi]['slug'],update['slug'])
            self.assertEqual(expected[doi]['content_sha256'],update['previous_content_sha256'])
            self.assertEqual(author_release.canonical_hash(baseline),update['previous_content_sha256'])
            self.assertEqual(update['allowed_changed_fields'],['scope','sections[0].text'])
            restored=copy.deepcopy(self.records[doi])
            restored['scope']=baseline['scope']
            restored['sections'][0]['text']=baseline['sections'][0]['text']
            self.assertEqual(restored,baseline)
            expected[doi]=dict(expected[doi],content_sha256=update['content_sha256'])
        self.assertEqual(set(self.records),set(expected))
        for doi,r in self.records.items():
            encoded=json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
            self.assertEqual(hashlib.sha256(encoded).hexdigest(),expected[doi]['content_sha256'])
            self.assertEqual(self.bydoi[doi]['paper_geo_status'],'none')
            self.assertNotIn('key_findings',r)
            self.assertNotIn('qa',r)
        self.assertEqual(notes.validate_generated(self.public),{'limited_evidence_pages':REVIEW['limited_evidence_pages']-additions,'full_v2_status_changed':False})

    def test_note_removal_restores_every_target_page_and_schema_exactly(self):
        for doi,r in self.records.items():
            slug=r['slug']
            for ext,render,baseline_render in [
                    ('html',notes.render_html,self.baseline_renderer.render_html),
                    ('md',notes.render_markdown,self.baseline_renderer.render_markdown)]:
                path='papers/'+slug+'.'+ext
                before=old(path).decode();after=now(path).decode();block=render(r)+('' if ext=='html' else '\n')
                baseline_block=baseline_render(self.baseline_records[doi])+('' if ext=='html' else '\n')
                self.assertEqual(before.count(baseline_block),1,path+' baseline note')
                before=before.replace(baseline_block,'',1)
                self.assertEqual(after.count(block),1,path)
                restored=after.replace(block,'',1)
                self.assertEqual(restored,before,path)
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
        allowed=set(PRESENTATION['allowed_production_paths'])
        self.assertEqual(allowed,{
            'data/limited_evidence.json',
            'papers/doi-10-1371-journal-pone-0346326.html',
            'papers/doi-10-1371-journal-pone-0346326.md',
            'research/questions.html','research/questions.json','sitemap.xml',
        })
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','data/deep_geo','citations','assets','index.html','data/publications_master.json','data/featured_papers.json','data/deep_geo_papers.json','data/profile_config.json','data/homepage_author_roles.json','data/patent_evidence.json','paper_index.json','publication_inventory.csv','publications.html','research','robots.txt','CNAME','.github','scripts/sync_common.py'],cwd=ROOT,text=True).splitlines()
        paths += ['scripts/fixtures/limited_evidence_release_20261027.json',
                  'scripts/fixtures/author_account_release_20261027.json',
                  'scripts/author_account_release_contract.py']
        for path in paths:
            if path not in allowed:
                self.assertEqual(now(path),old(path),path)
        target_slugs={r['slug'] for r in self.records.values()}
        for p in self.public:
            if p['slug'] not in target_slugs:
                for ext in ['html','md']:
                    path='papers/'+p['slug']+'.'+ext
                    before=old(path);after=now(path)
                    self.assertEqual(after,before,path)
        def sitemap(raw):
            rows=[(e.find('{*}loc').text,e.find('{*}lastmod').text) for e in ElementTree.fromstring(raw)]
            self.assertEqual(len(rows),84)
            self.assertEqual(len(dict(rows)),len(rows))
            return dict(rows)
        before=sitemap(old('sitemap.xml'));after=sitemap(now('sitemap.xml'))
        self.assertEqual(set(before),set(after))
        targets=PRESENTATION['allowed_sitemap_lastmod']
        self.assertEqual(targets,{'https://drgezhang.com/papers/doi-10-1371-journal-pone-0346326.html':'2026-11-04'})
        for url in before:
            if url in targets:self.assertEqual(after[url],targets[url],url)
            else:self.assertEqual(before[url],after[url],url)

    def test_invalid_or_unsourced_notes_fail_closed(self):
        doi,r=next(iter(self.records.items()));publication=self.bydoi[doi]
        for mutate in [lambda c:c.update(evidence_status='v2'),lambda c:c['sections'][0].pop('source_locator'),lambda c:c['sections'][0].update(source_url='javascript:alert(1)'),lambda c:c.update(slug='different-identity'),lambda c:c.update(limitations=[])]:
            bad=copy.deepcopy(r);mutate(bad)
            with self.assertRaises(ValueError):notes.validate_record(doi,bad,publication)
        with self.assertRaises(ValueError):notes.validate_record(doi,r,dict(publication,paper_geo_status='v2'))
        with self.assertRaises(ValueError):notes.validate_record(doi,r,dict(publication,type='Patent'))


if __name__=='__main__':unittest.main()
