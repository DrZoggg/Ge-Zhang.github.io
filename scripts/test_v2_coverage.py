"""Required V2 coverage with exactly approved central-review source changes."""
import copy
import hashlib
import json
import subprocess
import unittest

from scholarly_discovery import backlink_html, reviewed_backlinks, validate_backlink_html
from site_common import deep_content_path
from sync_common import ROOT
from v2_coverage import coverage_rows, validate_v2_coverage, check_qa_refs
from central_release_contract import (BASE, RELEASE, old, newline_hashes,
                                      reviewed_source, restore_reviewed_text,
                                      validate_new_source)

LUAD = "10.71321/fy14v342"


def with_reviewed_backlinks(before, old_rows, new_rows):
    validate_backlink_html(before, old_rows)
    old_block, new_block = backlink_html(old_rows), backlink_html(new_rows)
    if old_block:
        return before.replace(old_block, new_block, 1)
    footer = '\n<section><div class="links"><a class="btn" href="../publications.html">'
    if before.count(footer) != 1:
        raise ValueError('Missing unique relationship-panel insertion boundary')
    return before.replace(footer, new_block + footer, 1)


class V2CoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviewed = RELEASE
        cls.public = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
        cls.contents = {p["doi"]: json.loads(deep_content_path(p).read_text(encoding="utf-8")) for p in cls.public if p.get("paper_geo_status") == "v2"}
        cls.before = json.loads(old("publications.json"))
        cls.prior_v2 = [p for p in cls.before if p["paper_geo_status"] == "v2"]
        cls.prior_contents = {p["doi"]: json.loads(old(f'data/deep_geo/{p["slug"]}.json')) for p in cls.prior_v2}

    def test_complete_modules_and_explicit_alternatives(self):
        counts = validate_v2_coverage(self.public, self.contents, ROOT)
        self.assertEqual(len(self.prior_v2), 41)
        self.assertEqual(sum(len(p['changes']) for p in RELEASE['patches'].values()), 13)
        self.assertIn(set(RELEASE['papers']), [
            {'10.1016/j.csbj.2024.04.044'},
            {'10.1016/j.csbj.2024.04.044', '10.1016/j.medd.2026.100004'}])
        expected = len(self.prior_v2) + len(self.reviewed["papers"])
        self.assertEqual(counts, {"v2_pages": expected, "covered_pages": expected, "field_source_qa_exceptions": 5, "citation_pilot_alternatives": 1})

    def test_reviewed_upgrade_set_is_exact_and_not_curated(self):
        prior_dois = {p["doi"] for p in self.prior_v2}
        additions = set(self.reviewed["papers"])
        self.assertFalse(prior_dois & additions)
        self.assertEqual(set(self.contents), prior_dois | additions)
        before_by_doi = {p["doi"]: p for p in self.before if p.get("doi")}
        public_by_doi = {p["doi"]: p for p in self.public if p.get("doi")}
        for doi, reviewed in self.reviewed["papers"].items():
            with self.subTest(doi=doi):
                publication = public_by_doi[doi]
                content = self.contents[doi]
                self.assertNotEqual(before_by_doi[doi]["paper_geo_status"], "v2")
                self.assertEqual(publication["paper_geo_status"], "v2")
                self.assertFalse(publication["deep_geo"])
                self.assertFalse(publication["featured"])
                self.assertEqual(publication["slug"], reviewed["slug"])
                self.assertEqual(content["doi"], doi)
                self.assertEqual(content["version"], 2)
                self.assertEqual(content["study_profile"]["profile_type"], reviewed["profile_type"])
                self.assertIn(reviewed["content_sha256"], newline_hashes(deep_content_path(publication).read_bytes()))
                validate_new_source(doi, content)
                self.assertEqual(check_qa_refs(content), [])

    def test_prior_41_sources_identity_and_selection_unchanged_except_13_fields(self):
        self.assertEqual(len(self.before), 77)
        expected = copy.deepcopy(self.before)
        for p in expected:
            if p.get('doi') in RELEASE['papers']:
                p['paper_geo_status'] = 'v2'
        self.assertEqual(self.public, expected)
        for p in self.prior_v2:
            slug = p['slug']
            baseline = self.prior_contents[p['doi']]
            self.assertEqual(self.contents[p['doi']], reviewed_source(slug, baseline), slug)
            if slug not in RELEASE['patches']:
                self.assertEqual(deep_content_path(p).read_bytes().replace(b'\r\n', b'\n'),
                                 old('data/deep_geo/' + slug + '.json').replace(b'\r\n', b'\n'), slug)
        for path in ('data/featured_papers.json', 'data/deep_geo_papers.json',
                     'data/homepage_author_roles.json', 'data/publications_master.json'):
            self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'),
                             old(path).replace(b'\r\n', b'\n'), path)

    def test_historical_35_plus_6_sources_remain_protected(self):
        batch = json.loads((ROOT / 'scripts/fixtures/ordinary_v2_batch2_20261016.json').read_text(encoding='utf-8'))
        baseline = batch['base_sha']
        historic = json.loads(subprocess.check_output(['git', 'show', baseline + ':publications.json'], cwd=ROOT))
        prior = {p['doi']: p for p in historic if p['paper_geo_status'] == 'v2'}
        self.assertEqual(len(prior), 35)
        self.assertEqual(len(batch['papers']), 6)
        self.assertEqual(set(self.prior_contents), set(prior) | set(batch['papers']))
        for doi, p in prior.items():
            raw = subprocess.check_output(['git', 'show', baseline + ':data/deep_geo/' + p['slug'] + '.json'], cwd=ROOT)
            self.assertEqual(self.prior_contents[doi], json.loads(raw), doi)
        for doi, row in batch['papers'].items():
            self.assertIn(row['content_sha256'], newline_hashes(old('data/deep_geo/' + row['slug'] + '.json')), doi)

    def test_prior_41_pages_allow_only_reviewed_fields_and_relationships(self):
        prior_backlinks = reviewed_backlinks(self.before, self.prior_contents)
        current_backlinks = reviewed_backlinks(self.public, self.contents)
        from evidence_reuse import render_csv
        for p in self.prior_v2:
            slug = p['slug']
            page = f'papers/{slug}.html'
            before = old(page).decode('utf-8').replace('\r\n', '\n')
            after = (ROOT / page).read_text(encoding='utf-8')
            old_rows, new_rows = prior_backlinks.get(p['doi']), current_backlinks.get(p['doi'])
            validate_backlink_html(after, new_rows)
            expected = with_reviewed_backlinks(before, old_rows, new_rows)
            self.assertEqual(restore_reviewed_text(slug, before, after), expected, page)
            path = f'papers/{slug}.md'
            before_md = old(path).decode('utf-8').replace('\r\n', '\n')
            self.assertEqual(restore_reviewed_text(slug, before_md, (ROOT / path).read_text(encoding='utf-8')), before_md, path)
            csv_path = f'assets/evidence/{slug}.csv'
            expected_source = reviewed_source(slug, self.prior_contents[p['doi']])
            self.assertEqual((ROOT / csv_path).read_text(encoding='utf-8'), render_csv(p, expected_source, p['paper_url']))
            if slug not in RELEASE['patches']:
                self.assertEqual((ROOT / csv_path).read_bytes().replace(b'\r\n', b'\n'), old(csv_path).replace(b'\r\n', b'\n'))

    def test_existing_formal_citation_exports_are_unchanged(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--', 'citations'], cwd=ROOT).decode().splitlines()
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'), old(path).replace(b'\r\n', b'\n'), path)

    def target_row(self, mutate):
        p = next(p for p in self.public if p["doi"] == LUAD)
        source = copy.deepcopy(self.contents[LUAD])
        mutate(source)
        return coverage_rows([p], {LUAD: source}, ROOT)[0]

    def test_missing_context_is_publish_blocker(self):
        row = self.target_row(lambda c: c.pop("discovery_layer"))
        self.assertEqual(row["status"], "FAIL")
        self.assertNotEqual(row["discovery_context"], "PASS")

    def test_missing_citation_context_is_publish_blocker(self):
        row = self.target_row(lambda c: c.pop("citation_layer"))
        self.assertEqual(row["status"], "FAIL")
        self.assertNotEqual(row["citation_contexts"], "PASS")

    def test_new_unreferenced_qa_is_not_legacy_exception(self):
        source = copy.deepcopy(self.contents[LUAD])
        source["qa"][0].pop("evidence_refs", None)
        with self.assertRaisesRegex(ValueError, "requires evidence_refs"):
            check_qa_refs(source)

    def test_legacy_field_change_requires_review(self):
        source = copy.deepcopy(self.contents["10.1038/s41467-024-50415-9"])
        source["study_profile"]["unique_total_n"] += 1
        with self.assertRaisesRegex(ValueError, "editorial re-review"):
            check_qa_refs(source)


if __name__ == "__main__":
    unittest.main()
