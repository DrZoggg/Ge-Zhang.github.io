"""Required V2 coverage and unchanged prior science; read-only regression."""
import copy
import json
import subprocess
import unittest

from paper_discovery import scientific_content
from sync_common import ROOT
from v2_coverage import coverage_rows, validate_v2_coverage, check_qa_refs

BASE = "1830f8d1f86ed72c0784752408ff325796b3226d"
LUAD = "10.71321/fy14v342"
SCIENCE = "10.1126/science.aek9583"


def old(path):
    return subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)


class V2CoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
        cls.contents = {p["doi"]: json.loads((ROOT / f'data/deep_geo/{p["slug"]}.json').read_text(encoding="utf-8")) for p in cls.public if p.get("paper_geo_status") == "v2"}

    def test_complete_modules_and_explicit_alternatives(self):
        counts = validate_v2_coverage(self.public, self.contents, ROOT)
        self.assertEqual(counts, {"v2_pages": 29, "covered_pages": 29, "field_source_qa_exceptions": 5, "citation_pilot_alternatives": 1})

    def test_prior_28_science_identity_and_selection_unchanged(self):
        before = json.loads(old("publications.json"))
        v2 = [p for p in before if p["paper_geo_status"] == "v2"]
        self.assertEqual(len(v2), 28)
        for p in v2:
            path = f'data/deep_geo/{p["slug"]}.json'
            current_bytes = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
            if p["doi"] == SCIENCE:
                self.assertEqual(scientific_content(json.loads(current_bytes)), json.loads(old(path)))
            else:
                self.assertEqual(current_bytes, old(path).replace(b"\r\n", b"\n"), path)
                for suffix in ("html", "md"):
                    page = f'papers/{p["slug"]}.{suffix}'
                    self.assertEqual((ROOT / page).read_bytes().replace(b"\r\n", b"\n"), old(page).replace(b"\r\n", b"\n"), page)
            self.assertEqual((ROOT / f'assets/evidence/{p["slug"]}.csv').read_bytes().replace(b"\r\n", b"\n"), old(f'assets/evidence/{p["slug"]}.csv').replace(b"\r\n", b"\n"))
        for path in ("data/publications_master.json", "data/featured_papers.json", "data/deep_geo_papers.json"):
            self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"), old(path).replace(b"\r\n", b"\n"), path)
        self.assertEqual(len(self.public), 77)
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
