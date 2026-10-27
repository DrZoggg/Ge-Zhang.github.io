"""Bounded source upgrades with the complete live 50-V2 baseline frozen."""
import copy
import hashlib
import html
import json
import subprocess
import unittest
from pathlib import Path
from sync_common import ROOT
import patent_evidence
import author_account_release_contract as author_release

REVIEW=json.loads((ROOT/'scripts/fixtures/researchgate_release_20261026.json').read_text(encoding='utf-8'))
BASE=REVIEW['base_sha']
def old(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).replace(b'\r\n',b'\n')
def now(path):return (ROOT/path).read_bytes().replace(b'\r\n',b'\n')

class ResearchGateReleaseTests(unittest.TestCase):
    def test_live_50_sources_and_formal_identity_are_frozen(self):
        before=json.loads(old('publications.json'))
        current=json.loads(now('publications.json'))
        previous=[p for p in before if p['paper_geo_status']=='v2']
        self.assertEqual(len(previous),50)
        expected=copy.deepcopy(before)
        for p in expected:
            if p.get('doi') in REVIEW['papers']:p['paper_geo_status']='v2'
        expected=author_release.with_upgrades(expected)
        self.assertEqual(current,expected)
        self.assertEqual(sum(p['paper_geo_status']=='v2' for p in current),55+len(author_release.RELEASE['papers']))
        for p in previous:
            for path in ['data/deep_geo/'+p['slug']+'.json','papers/'+p['slug']+'.md','assets/evidence/'+p['slug']+'.csv']:
                self.assertEqual(now(path),old(path),path)
        for path in ['data/publications_master.json','data/featured_papers.json','data/deep_geo_papers.json','data/homepage_author_roles.json','data/profile_config.json','index.html']:
            self.assertEqual(now(path),old(path),path)
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','citations','assets/visual5'],cwd=ROOT,text=True).splitlines()
        for path in paths:self.assertEqual(now(path),old(path),path)

    def test_exact_reviewed_additions_and_all_citation_locations(self):
        for doi,row in REVIEW['papers'].items():
            raw=now('data/deep_geo/'+row['slug']+'.json')
            self.assertEqual(hashlib.sha256(raw).hexdigest(),row['content_sha256'])
            c=json.loads(raw)
            self.assertEqual(c['doi'],doi)
            self.assertTrue(all(q.get('evidence_refs') for q in c['qa']))
            self.assertTrue(all(k.get('source_locator') for k in c['key_findings']))
            page=now('papers/'+row['slug']+'.html').decode()
            md=now('papers/'+row['slug']+'.md').decode()
            for finding in c['key_findings']:
                self.assertIn(html.escape(finding['claim']),page)
                self.assertIn(finding['claim'],md)
                self.assertIn(html.escape(finding['source_locator']),page)
                self.assertIn(finding['source_locator'],md)
        nejm=json.loads(now('data/deep_geo/doi-10-1056-nejmc2518964.json'))
        self.assertIn('PMID 41780015',json.dumps(nejm))
        self.assertIn('not an 83%',json.dumps(nejm))
        tox=json.loads(now('data/deep_geo/doi-10-1002-tox-24284.json'))
        self.assertFalse(tox['study_profile']['external_validation'])
        self.assertIn('0.67, 0.73, 0.75',json.dumps(tox))
        for doi in ['10.1200/po-24-00875','10.1111/odi.70054','10.1056/nejmc2518964']:
            c=json.loads(now('data/deep_geo/'+REVIEW['papers'][doi]['slug']+'.json'))
            self.assertEqual(c['study_profile']['narrative_genre'],'correspondence')

    def test_patent_module_is_bounded_non_v2_and_exactly_shared(self):
        items=json.loads(now('publications.json'))
        p=next(p for p in items if p['slug']==patent_evidence.SLUG)
        self.assertEqual(p['paper_geo_status'],'none')
        self.assertFalse(p.get('doi'))
        c=patent_evidence.load(p)
        self.assertEqual([n for x in c['claim_scope'] for n in x['claim_numbers']],list(range(1,8)))
        path='data/patent_evidence.json'
        self.assertEqual(hashlib.sha256(now(path)).hexdigest(),REVIEW['non_v2_notes'][p['slug']]['content_sha256'])
        page=now('papers/'+p['slug']+'.html').decode();md=now('papers/'+p['slug']+'.md').decode()
        self.assertEqual(page.count(patent_evidence.render_html(c)),1)
        self.assertEqual(md.count(patent_evidence.render_markdown(c)),1)
        self.assertIn('status are unknown',page)
        for _,text,_ in patent_evidence.blocks(c):
            self.assertIn(html.escape(text),page);self.assertIn(text,md)
        with self.assertRaises(ValueError):patent_evidence.load(dict(p,doi='10.1/invented'))
        self.assertIsNone(patent_evidence.load({'slug':'unrelated'}))

if __name__=='__main__':unittest.main()
