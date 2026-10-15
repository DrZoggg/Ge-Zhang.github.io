"""Source-frozen first ordinary-work V2 batch and curated identity protection."""
import copy
import hashlib
import json
import subprocess
import unittest
from xml.etree import ElementTree

from build_publications import validate_deep_v2_content, v2_snapshot_items
from sync_common import ROOT, load_master
from validate_site import meta_contents, paper_json_ld_object

FIXTURE = ROOT / 'scripts/fixtures/ordinary_v2_batch_20261015.json'


class OrdinaryBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads(FIXTURE.read_text(encoding='utf-8'))
        cls.papers = json.loads((ROOT / 'paper_index.json').read_text(encoding='utf-8'))['papers']
        cls.master = {p.get('doi'): p for p in load_master()}

    def test_original_science_master_and_curated_order_are_unchanged(self):
        for path, digest in self.frozen['protected_hashes'].items():
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes().replace(b'\r\n', b'\n')
                self.assertIn(digest, {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b'\n', b'\r\n')).hexdigest()})
                original = subprocess.check_output(['git', 'show', self.frozen['base_sha'] + ':' + path], cwd=ROOT)
                self.assertEqual(raw, original.replace(b'\r\n', b'\n'))
        for before in self.frozen['baseline_identity']:
            now = next(p for p in self.papers if p['paper_url'] == before['paper_url'])
            self.assertEqual({key: now.get(key) for key in before}, before)
        self.assertEqual(sum(p['deep_geo'] for p in self.papers), 29)
        self.assertEqual(sum(p['featured'] for p in self.papers), 29)

    def test_six_reviewed_sources_render_as_nonselected_v2(self):
        self.assertEqual(len(self.frozen['papers']), 6)
        self.assertEqual(sum(p['paper_geo_status'] == 'v2' for p in self.papers), 35)
        for doi, reviewed in self.frozen['papers'].items():
            with self.subTest(doi=doi):
                slug = reviewed['slug']
                source = ROOT / f'data/deep_geo/{slug}.json'
                raw = source.read_bytes().replace(b'\r\n', b'\n')
                self.assertIn(reviewed['content_sha256'], {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b'\n', b'\r\n')).hexdigest()})
                content = json.loads(source.read_text(encoding='utf-8'))
                validate_deep_v2_content(content, self.master[doi])
                item = next(p for p in self.papers if p.get('doi') == doi)
                self.assertEqual(item['paper_geo_status'], 'v2')
                self.assertFalse(item['deep_geo'])
                self.assertFalse(item['featured'])
                page = (ROOT / f'papers/{slug}.html').read_text(encoding='utf-8')
                markdown = (ROOT / f'papers/{slug}.md').read_text(encoding='utf-8')
                self.assertEqual(meta_contents(page, 'citation_doi'), [doi])
                identity = paper_json_ld_object(page, slug)['sameAs']
                self.assertEqual(identity[0] if isinstance(identity, list) else identity, 'https://doi.org/' + doi)
                self.assertIn('Paper GEO V2</span>', page)
                self.assertNotIn('<span class="badge">Deep GEO</span>', page)
                self.assertEqual(page.count('id="ev-summary"'), 1)
                self.assertIn(content['research_question'], markdown)
                self.assertIn(content['author_summary'], markdown)
                self.assertIn('id="evidence-matrix"', page)
                self.assertIn('data-discovery-layer="1"', page)

    def test_observational_multicohort_preserves_separate_denominators(self):
        doi = '10.15212/bioi-2026-0017'
        source = json.loads((ROOT / 'data/deep_geo/doi-10-15212-bioi-2026-0017.json').read_text(encoding='utf-8'))
        self.assertEqual(source['study_profile']['profile_type'], 'multicohort_observational')
        self.assertNotIn('unique_total_n', source['study_profile'])
        self.assertEqual(len(v2_snapshot_items(source)), 3)
        for key, value in [('unique_total_n', 262193), ('cohorts', [])]:
            mutated = copy.deepcopy(source)
            mutated['study_profile'][key] = value
            with self.assertRaisesRegex(ValueError, 'not a synthetic cohort total'):
                validate_deep_v2_content(mutated, self.master[doi])

    def test_canonical_inventory_and_citation_exports_are_unchanged(self):
        before = subprocess.check_output(['git', 'show', self.frozen['base_sha'] + ':sitemap.xml'], cwd=ROOT)
        def urls(raw):
            return {node.text for node in ElementTree.fromstring(raw).iter() if node.tag.endswith('}loc')}
        self.assertEqual(urls(before), urls((ROOT / 'sitemap.xml').read_bytes()))
        self.assertEqual(len(urls(before)), 81)
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', self.frozen['base_sha'], '--', 'citations'], cwd=ROOT).decode().splitlines()
        for path in paths:
            original = subprocess.check_output(['git', 'show', self.frozen['base_sha'] + ':' + path], cwd=ROOT)
            self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'), original.replace(b'\r\n', b'\n'), path)


if __name__ == '__main__':
    unittest.main()
