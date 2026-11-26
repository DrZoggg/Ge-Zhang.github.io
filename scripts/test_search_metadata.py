import json
import tempfile
import unittest
from pathlib import Path

import search_metadata


PAGE = (
    '<!doctype html><html><head><title>Formal &amp; complete title</title>'
    '<meta name="description" content="Complete evidence summary.">'
    '<meta property="og:title" content="Formal &amp; complete title">'
    '<meta name="citation_title" content="Formal &amp; complete title">'
    '</head><body><h1>Formal &amp; complete title</h1></body></html>'
)


class SearchMetadataTests(unittest.TestCase):
    def test_projection_changes_only_search_head(self):
        fields = {"title": "Research & evidence", "description": 'The comparison uses "paired" source data.'}
        page = search_metadata.project(PAGE, fields)
        self.assertEqual(search_metadata.read(page), fields)
        self.assertEqual(search_metadata.project(page, search_metadata.read(PAGE)), PAGE)
        self.assertEqual(search_metadata.project(PAGE, {}), PAGE)
        self.assertEqual(search_metadata.route("https://drgezhang.com/"), "index.html")

    def test_invalid_source_fields_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / search_metadata.SOURCE_PATH
            path.parent.mkdir()
            invalid = [
                {"../index.html": {"title": "Unsafe path"}},
                {"index.html": {"title": "T" * 70}},
                {"index.html": {"description": "This does not finish the description"}},
                {"index.html": {"title": "Incomplete…"}},
                {"index.html": {"keywords": "Other metadata"}},
            ]
            for records in invalid:
                with self.subTest(records=records):
                    path.write_text(json.dumps(records), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        search_metadata.load(root)
            path.write_text('{"index.html":{"title":"One","title":"Two"}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate search metadata key"):
                search_metadata.load(root)

    def test_validation_matches_configured_source_and_detects_unknown_route(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "index.html"
            path.write_text(PAGE, encoding="utf-8")
            routes = {"index.html"}
            with self.assertRaisesRegex(ValueError, "Unknown search metadata routes"):
                search_metadata.validate_published(root, {"missing.html": {"title": "Short title"}}, routes)
            records = {"index.html": {"title": "Short title"}}
            with self.assertRaisesRegex(ValueError, "differs from reviewed text"):
                search_metadata.validate_published(root, records, routes)
            path.write_text(search_metadata.project(PAGE, records["index.html"]), encoding="utf-8")
            search_metadata.validate_published(root, records, routes)


if __name__ == "__main__":
    unittest.main()
