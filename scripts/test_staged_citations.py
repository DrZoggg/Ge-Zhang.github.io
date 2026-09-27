"""Negative delivery fixtures using the current generated citation inventory."""

import shutil
import tempfile
import unittest
from pathlib import Path

from sync_common import ROOT
from validate_staged_citations import staged_target, validate_staged


class StagedCitationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name).resolve()
        for name in ("papers", "citations"):
            shutil.copytree(ROOT / name, self.stage / name)

    def test_complete_matching(self):
        result = validate_staged(self.stage)
        self.assertEqual(result["files"], result["eligible"] * 3)

    def test_omitted_directory(self):
        shutil.rmtree(self.stage / "citations")
        with self.assertRaisesRegex(ValueError, "Missing/unexpected"):
            validate_staged(self.stage)

    def test_missing_file(self):
        next((self.stage / "citations").glob("*.bib")).unlink()
        with self.assertRaisesRegex(ValueError, "Missing/unexpected"):
            validate_staged(self.stage)

    def test_altered_file(self):
        next((self.stage / "citations").glob("*.ris")).write_bytes(b"altered")
        with self.assertRaisesRegex(ValueError, "differs from generated"):
            validate_staged(self.stage)

    def test_unsafe_links(self):
        page = "https://drgezhang.com/papers/example.html"
        for href in ("https://other.example/citations/x.bib", "../../x.bib",
                     "../citations/%2e%2e/x.bib", "../citations/x.bib?other=1"):
            with self.subTest(href=href), self.assertRaises(ValueError):
                staged_target(self.stage, page, href)


if __name__ == "__main__":
    unittest.main()
