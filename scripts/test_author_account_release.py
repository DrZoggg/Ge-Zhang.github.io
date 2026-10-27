"""Source-approved V2 upgrades; original 55 pages and all identities stay exact."""
import copy
import csv
import hashlib
import io
import json
import subprocess
import unittest
from xml.etree import ElementTree

import author_account_release_contract as release
import limited_evidence
from build_publications import validate_deep_v2_content
from evidence_reuse import render_csv
from site_common import load_site_config
from sync_common import ROOT
from validate_site import paper_json_ld_object, validate_v2_rendered_page


PROTECTED = (
    'data', 'papers', 'citations', 'assets', 'research', 'index.html',
    'publications.json', 'paper_index.json', 'publication_inventory.csv',
    'publications.html', 'sitemap.xml', 'llms.txt', 'llms-full.txt',
    'robots.txt', 'CNAME', '.github', 'scripts/sync_common.py',
)


class AuthorAccountReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads(release.old('publications.json'))
        cls.public = json.loads(release.now('publications.json'))
        cls.original = {p['doi']: p for p in cls.before if p.get('doi')}
        cls.bydoi = {p['doi']: p for p in cls.public if p.get('doi')}
        cls.contents = {
            doi: json.loads(release.now('data/deep_geo/' + row['slug'] + '.json'))
            for doi, row in release.RELEASE['papers'].items()
        }

    def test_only_reviewed_status_fields_change(self):
        self.assertEqual(len(self.before), release.RELEASE['public_works'])
        self.assertEqual(sum(p['paper_geo_status'] == 'v2' for p in self.before),
                         release.RELEASE['baseline_v2'])
        for doi, row in release.RELEASE['papers'].items():
            self.assertEqual(self.original[doi]['paper_geo_status'], 'none', doi)
            self.assertEqual(self.original[doi]['slug'], row['slug'], doi)
            self.assertFalse(self.original[doi]['featured'], doi)
            self.assertFalse(self.original[doi]['deep_geo'], doi)
        self.assertEqual(self.public, release.with_upgrades(self.before))
        self.assertEqual(sum(p['paper_geo_status'] == 'v2' for p in self.public),
                         release.RELEASE['baseline_v2'] + len(release.RELEASE['papers']))
        self.assertEqual(sum(p['featured'] for p in self.public), 29)
        self.assertEqual(sum(p['deep_geo'] for p in self.public), 29)

    def test_exact_gold_hashes_and_complete_rendered_evidence(self):
        for doi, row in release.RELEASE['papers'].items():
            with self.subTest(doi=doi):
                slug = row['slug']
                content = self.contents[doi]
                raw = release.now('data/deep_geo/' + slug + '.json')
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['content_sha256'])
                self.assertEqual(release.canonical_hash(content), row['canonical_json_sha256'])
                self.assertEqual(content['doi'], doi)
                self.assertEqual(content['version'], 2)
                self.assertEqual(content['study_profile']['profile_type'], row['profile_type'])
                self.assertEqual(len(content['key_findings']), row['key_findings'])
                self.assertEqual(len(content['citation_layer']['citation_use_cases']), row['citation_use_cases'])
                self.assertEqual(len(content['citation_layer']['evidence_matrix']), row['evidence_rows'])
                validate_deep_v2_content(content, slug)
                page = release.now('papers/' + slug + '.html').decode('utf-8')
                markdown = release.now('papers/' + slug + '.md').decode('utf-8')
                self.assertNotIn('id="limited-evidence"', page)
                self.assertNotIn('<a id="limited-evidence"></a>', markdown)
                validate_v2_rendered_page(
                    content=content, publication=self.bydoi[doi], page=page, markdown=markdown,
                    schema=paper_json_ld_object(page, slug), public_by_doi=self.bydoi,
                    config=load_site_config())
                self.assertEqual(release.now('assets/evidence/' + slug + '.csv').decode('utf-8'),
                                 render_csv(self.bydoi[doi], content, self.bydoi[doi]['paper_url']))

    def test_only_icm_hmg_notes_change_and_upgraded_notes_are_removed(self):
        before = json.loads(release.old('data/limited_evidence.json'))
        current = json.loads(release.now('data/limited_evidence.json'))
        expected = copy.deepcopy(before)
        for doi in release.RELEASE['papers']:
            self.assertIn(doi, expected['papers'])
            del expected['papers'][doi]
        for doi, row in release.RELEASE['limited_evidence_updates'].items():
            record = current['papers'][doi]
            self.assertEqual(record['slug'], row['slug'])
            self.assertEqual(release.canonical_hash(record), row['content_sha256'])
            self.assertEqual(self.bydoi[doi]['paper_geo_status'], 'none')
            limited_evidence.validate_record(doi, record, self.bydoi[doi])
            expected['papers'][doi] = record
            for ext, renderer in [('html', limited_evidence.render_html),
                                  ('md', limited_evidence.render_markdown)]:
                path = 'papers/' + row['slug'] + '.' + ext
                suffix = '' if ext == 'html' else '\n'
                old_block = renderer(before['papers'][doi]) + suffix
                new_block = renderer(record) + suffix
                prior_page = release.old(path).decode('utf-8')
                current_page = release.now(path).decode('utf-8')
                self.assertEqual(prior_page.count(old_block), 1)
                self.assertEqual(current_page.count(new_block), 1)
                self.assertEqual(current_page.replace(new_block, '', 1),
                                 prior_page.replace(old_block, '', 1))
        self.assertEqual(current, expected)
        self.assertEqual(len(current['papers']), 21 - len(release.RELEASE['papers']))
        icm = json.dumps(current['papers'][release.ICM], ensure_ascii=False)
        for unresolved in ('GSE57338', 'GSE57345', '203', '0.943', '0.933'):
            self.assertIn(unresolved, icm)

    def test_all_prior_science_citations_visuals_and_other_notes_are_frozen(self):
        allowed = release.allowed_production_paths()
        self.assertFalse(release.changed_paths(*PROTECTED) - allowed)
        untracked = subprocess.check_output(
            ['git', '-c', 'core.quotepath=false', 'ls-files', '--others', '--exclude-standard', '--', *PROTECTED],
            cwd=ROOT, text=True, encoding='utf-8').splitlines()
        self.assertFalse(set(untracked) - allowed)
        previous = [p for p in self.before if p['paper_geo_status'] == 'v2']
        self.assertEqual(len(previous), 55)
        for p in previous:
            slug = p['slug']
            for path in ('data/deep_geo/' + slug + '.json', 'papers/' + slug + '.html',
                         'papers/' + slug + '.md', 'assets/evidence/' + slug + '.csv'):
                if path != 'papers/' + slug + '.html' or slug not in release.BACKLINK_ONLY:
                    self.assertNotIn(path, allowed)
                self.assertTrue((ROOT / path).is_file(), path)
        self.assertFalse(any(p.startswith('citations/') for p in allowed))
        self.assertNotIn('index.html', allowed)

    def test_four_navigation_blocks_are_exact_and_all_other_html_stays_frozen(self):
        old_items, old_rows = release.backlink_context(baseline=True)
        _, current_rows = release.backlink_context()
        changed = {slug for slug, p in old_items.items()
                   if slug not in release.changed_slugs()
                   and old_rows.get(p.get('doi')) != current_rows.get(p.get('doi'))}
        self.assertEqual(changed, release.BACKLINK_ONLY)
        for slug in release.BACKLINK_ONLY:
            path = 'papers/' + slug + '.html'
            before = release.old(path).decode('utf-8')
            after = release.now(path).decode('utf-8')
            self.assertEqual(release.backlink_core(slug, after),
                             release.backlink_core(slug, before, baseline=True), slug)
            self.assertEqual(release.now('papers/' + slug + '.md'),
                             release.old('papers/' + slug + '.md'), slug)

    def test_machine_indexes_allow_only_reviewed_status_and_evidence_fields(self):
        prior = json.loads(release.old('paper_index.json'))
        current = json.loads(release.now('paper_index.json'))
        expected = copy.deepcopy(prior)
        for row in expected['papers']:
            content = self.contents.get(row.get('doi'))
            if content:
                slug = release.RELEASE['papers'][row['doi']]['slug']
                row.update(paper_geo_status='v2', discovery_layer=content['discovery_layer'],
                           question_count=len(content['qa']),
                           concept_count=sum(len(values) for values in content['concepts'].values()),
                           evidence_csv_url='https://drgezhang.com/assets/evidence/' + slug + '.csv')
        self.assertEqual(current, expected)
        read_csv = lambda raw: list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        prior_csv = read_csv(release.old('publication_inventory.csv'))
        for row in prior_csv:
            if row.get('doi') in release.RELEASE['papers']:
                row['paper_geo_status'] = 'v2'
        self.assertEqual(read_csv(release.now('publication_inventory.csv')), prior_csv)
        prior_selection = json.loads(release.old('data/question_index.json'))
        expected_selection = copy.deepcopy(prior_selection)
        expected_selection['papers'].update({doi: {'qa_index': 1} for doi in release.RELEASE['papers']})
        self.assertEqual(json.loads(release.now('data/question_index.json')), expected_selection)

    def test_sitemap_inventory_and_only_actual_changed_content_dates(self):
        def entries(raw):
            return {e.find('{*}loc').text: e.find('{*}lastmod').text for e in ElementTree.fromstring(raw)}
        before = entries(release.old('sitemap.xml'))
        current = entries(release.now('sitemap.xml'))
        self.assertEqual(set(current), set(before))
        for url, date in before.items():
            path = url.removeprefix('https://drgezhang.com/') or 'index.html'
            changed = release.now(path) != release.old(path)
            if changed:
                self.assertIn(url, release.dated_urls())
                self.assertEqual(current[url], release.CONTENT_DATE, url)
            else:
                self.assertEqual(current[url], date, url)


if __name__ == '__main__':
    unittest.main()
