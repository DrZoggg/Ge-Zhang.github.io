"""Selected-card branding contracts, without generating the site."""

import copy
import json
import unittest
from html.parser import HTMLParser
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from build_publications import render_featured_cards
from journal_branding import load_journal_branding, render_journal_mark
from site_common import controller_token, load_featured, publication_token
from sync_common import ROOT


class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class JournalBrandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.branding = load_journal_branding()
        cls.publications = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
        cls.by_token = {publication_token(item): item for item in cls.publications}
        cls.featured = load_featured()

    def test_every_selected_journal_has_a_verified_local_mark(self):
        targets = {"Cardiac Research", "Clinical and Translational Medicine"}
        targets.update(self.by_token[controller_token(entry)]["journal"] for entry in self.featured)
        for journal in targets:
            with self.subTest(journal=journal):
                record = self.branding[journal]
                self.assertIn(record["kind"], {"journal", "publisher"})
                self.assertEqual(urlsplit(record["source_url"]).scheme, "https")
                self.assertEqual(urlsplit(record["asset_source_url"]).scheme, "https")
                self.assertTrue((ROOT / record["asset"]).is_file())
                self.assertGreater(record["width"], 0)
                self.assertGreater(record["height"], 0)
                self.assertNotIn("--fallback", render_journal_mark(journal, self.branding))

    def test_local_svg_marks_have_no_executable_or_remote_dependencies(self):
        assets = {record["asset"] for record in self.branding.values()}
        for asset in sorted(assets):
            with self.subTest(asset=asset):
                self.assertLess((ROOT / asset).stat().st_size, 150_000)
                if not asset.endswith(".svg"):
                    continue
                svg = ET.parse(ROOT / asset).getroot()
                self.assertEqual(svg.tag.split("}")[-1], "svg")
                self.assertIn("viewBox", svg.attrib)
                for node in svg.iter():
                    self.assertNotIn(node.tag.split("}")[-1], {"script", "foreignObject", "text"})
                    for name, value in node.attrib.items():
                        self.assertFalse(name.lower().startswith("on"))
                        if name.split("}")[-1] in {"href", "src"}:
                            self.assertTrue(value.startswith("#"), value)
                source = (ROOT / asset).read_text(encoding="utf-8")
                self.assertNotRegex(source, r"@import|url\(\s*['\"]?https?://")

    def test_all_cards_remove_type_labels_and_preserve_publication_data(self):
        before = copy.deepcopy(self.by_token)
        markup = render_featured_cards(self.featured, self.by_token, {})
        tags = Tags(markup).tags
        self.assertEqual(sum(tag == "article" for tag, _ in tags), len(self.featured))
        self.assertFalse(any("paper-kind" in attrs.get("class", "").split() for _, attrs in tags))
        marks = [(tag, attrs) for tag, attrs in tags if "journal-brand" in attrs.get("class", "").split()]
        self.assertEqual(len(marks), len(self.featured))
        self.assertFalse(any(tag == "img" for tag, _ in tags))
        art = [attrs for _, attrs in tags if attrs.get("class") == "journal-brand-art"]
        self.assertEqual(len(art), len(self.featured))
        for (_, mark), logo in zip(marks, art):
            self.assertEqual(mark["aria-hidden"], "true")
            self.assertRegex(logo["style"], r"^background-image:url\(assets/journal-logos/[^)]+\)$")
        self.assertEqual(self.by_token, before)

    def test_unmapped_or_missing_asset_has_neutral_text_without_a_broken_image(self):
        unknown = render_journal_mark("Future Journal of Medicine & Science", self.branding)
        self.assertIn('data-brand-kind="neutral-abbreviation"', unknown)
        self.assertNotIn("<img", unknown)
        missing = {"Science": {**self.branding["Science"], "asset": "assets/journal-logos/missing.svg"}}
        self.assertNotIn("<img", render_journal_mark("Science", missing))
        self.assertIn("&lt;", render_journal_mark("<Journal>", {"<Journal>": {"abbreviation": "<J>"}}))


if __name__ == "__main__":
    unittest.main()
