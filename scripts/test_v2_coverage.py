"""Required V2 coverage and unchanged prior science; read-only regression."""
import copy
import hashlib
import json
import subprocess
import unittest

from scholarly_discovery import backlink_html, reviewed_backlinks, validate_backlink_html
from site_common import deep_content_path
from sync_common import ROOT
from v2_coverage import coverage_rows, validate_v2_coverage, check_qa_refs
from theme_shell import without_theme_shell
from discovery_test_contract import REVIEWED_FEATURED_SHA256

BASE = "3452075cb5355fc17d45baab1a3989e72f8b5b39"
FIXTURE = ROOT / "scripts/fixtures/ordinary_v2_batch2_20261016.json"
LUAD = "10.71321/fy14v342"


def old(path):
    return subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)


def newline_hashes(value):
    """Allow only Git's LF/CRLF checkout conversion, never changed JSON content."""
    normalized = value.replace(b"\r\n", b"\n")
    return {hashlib.sha256(normalized).hexdigest(), hashlib.sha256(normalized.replace(b"\n", b"\r\n")).hexdigest()}


def with_reviewed_backlinks(before, old_rows, new_rows):
    """Replace exactly the validated relationship panel at its existing slot."""
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
        cls.reviewed = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.public = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
        cls.contents = {p["doi"]: json.loads(deep_content_path(p).read_text(encoding="utf-8")) for p in cls.public if p.get("paper_geo_status") == "v2"}
        cls.before = json.loads(old("publications.json"))
        cls.prior_v2 = [p for p in cls.before if p["paper_geo_status"] == "v2"]
        cls.prior_contents = {p["doi"]: json.loads(old(f'data/deep_geo/{p["slug"]}.json')) for p in cls.prior_v2}

    def test_complete_modules_and_explicit_alternatives(self):
        counts = validate_v2_coverage(self.public, self.contents, ROOT)
        self.assertEqual(len(self.prior_v2), 35)
        self.assertEqual(len(self.reviewed["papers"]), 6)
        expected = len(self.prior_v2) + len(self.reviewed["papers"])
        self.assertEqual(counts, {"v2_pages": expected, "covered_pages": expected, "field_source_qa_exceptions": 5, "citation_pilot_alternatives": 1})

    def test_reviewed_upgrade_set_is_exact_and_not_curated(self):
        self.assertEqual(self.reviewed["base_sha"], BASE)
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
                self.assertEqual(check_qa_refs(content), [])

    def test_prior_35_sources_identity_and_selection_unchanged(self):
        self.assertEqual(len(self.prior_v2), 35)
        self.assertEqual(len(self.before), 77)
        self.assertEqual(len(self.public), len(self.before))
        self.assertEqual(len(self.reviewed["baseline_identity"]), len(self.before))
        current_by_url = {p["paper_url"]: p for p in self.public}
        indexed_by_url = {p["paper_url"]: p for p in json.loads((ROOT / "paper_index.json").read_text(encoding="utf-8"))["papers"]}
        for identity in self.reviewed["baseline_identity"]:
            self.assertEqual({key: indexed_by_url[identity["paper_url"]].get(key) for key in identity}, identity)
        identity_fields = ("doi", "title", "authors", "journal", "year", "type", "slug", "paper_url", "markdown_url", "deep_geo", "featured")
        for p in self.before:
            self.assertEqual({k: current_by_url[p["paper_url"]].get(k) for k in identity_fields}, {k: p.get(k) for k in identity_fields}, p["paper_url"])
        protected_sources = {f'data/deep_geo/{p["slug"]}.json' for p in self.prior_v2}
        self.assertTrue(protected_sources <= set(self.reviewed["protected_hashes"]))
        for path, digest in self.reviewed["protected_hashes"].items():
            current_bytes = (ROOT / path).read_bytes()
            baseline_bytes = old(path)
            self.assertIn(digest, newline_hashes(baseline_bytes), path)
            if path == 'data/featured_papers.json':
                self.assertEqual(hashlib.sha256(current_bytes.replace(b"\r\n", b"\n")).hexdigest(), REVIEWED_FEATURED_SHA256, path)
            else:
                self.assertEqual(current_bytes.replace(b"\r\n", b"\n"), baseline_bytes.replace(b"\r\n", b"\n"), path)

    def test_prior_35_pages_allow_only_reviewed_relationship_navigation(self):
        prior_backlinks = reviewed_backlinks(self.before, self.prior_contents)
        current_backlinks = reviewed_backlinks(self.public, self.contents)
        for p in self.prior_v2:
            path = f'data/deep_geo/{p["slug"]}.json'
            current_bytes = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(current_bytes, old(path).replace(b"\r\n", b"\n"), path)
            page = f'papers/{p["slug"]}.html'
            before = old(page).decode("utf-8").replace("\r\n", "\n")
            after = (ROOT / page).read_text(encoding="utf-8")
            old_rows, new_rows = prior_backlinks.get(p["doi"]), current_backlinks.get(p["doi"])
            validate_backlink_html(after, new_rows)
            expected = with_reviewed_backlinks(before, old_rows, new_rows)
            # Visual 4's exact shared theme shell is already separately tested.
            # Preserve every remaining scientific byte and relationship panel.
            self.assertEqual(without_theme_shell(after), without_theme_shell(expected), page)
            markdown = f'papers/{p["slug"]}.md'
            self.assertEqual((ROOT / markdown).read_bytes().replace(b"\r\n", b"\n"), old(markdown).replace(b"\r\n", b"\n"), markdown)
            self.assertEqual((ROOT / f'assets/evidence/{p["slug"]}.csv').read_bytes().replace(b"\r\n", b"\n"), old(f'assets/evidence/{p["slug"]}.csv').replace(b"\r\n", b"\n"))

    def test_existing_formal_citation_exports_are_unchanged(self):
        paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "--", "citations"], cwd=ROOT).decode().splitlines()
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"), old(path).replace(b"\r\n", b"\n"), path)

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
