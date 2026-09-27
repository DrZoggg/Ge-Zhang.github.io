"""Optional narrative genre is a display distinction, not publication identity."""
import copy
import json
import unittest

from build_publications import (
    render_citation_layer_html, render_citation_layer_markdown,
    validate_deep_v2_content, v2_article_label, v2_study_heading,
)
from sync_common import ROOT


class NarrativeLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contents = [json.loads(p.read_text(encoding="utf-8"))
                    for p in (ROOT / "data/deep_geo").glob("*.json")]
        cls.review = next(c for c in contents if c.get("study_profile", {}).get("profile_type") == "narrative_review"
                          and "narrative_genre" not in c["study_profile"])
        cls.clinical = next(c for c in contents if c.get("study_profile", {}).get("profile_type") == "clinical_cohort")
        cls.layer = next(c["citation_layer"] for c in contents if c.get("citation_layer"))

    def test_optional_default_and_labels(self):
        labels = {
            "Key Findings": "Key Arguments", "Review profile": "Article profile",
            "What This Review Adds": "What This Article Adds",
            "Review Design & Evidence Synthesis": "Article Scope & Approach",
            "When This Study Is Useful to Cite": "When This Article Is Useful to Cite",
            "What This Study Should Not Be Cited to Claim": "What This Article Should Not Be Cited to Claim",
        }
        for old, new in labels.items():
            self.assertEqual(v2_article_label(None, old), old)
            self.assertEqual(v2_article_label(self.review, old), old)
            for genre in ("perspective", "correspondence"):
                content = copy.deepcopy(self.review)
                content["study_profile"]["narrative_genre"] = genre
                validate_deep_v2_content(content)
                self.assertEqual(v2_article_label(content, old), new)
                self.assertEqual(v2_study_heading(content), "Article Scope & Approach")
        self.assertEqual(render_citation_layer_html(self.layer), render_citation_layer_html(self.layer, self.review))
        self.assertEqual(render_citation_layer_markdown(self.layer), render_citation_layer_markdown(self.layer, self.review))

    def test_invalid_genres(self):
        for value in ("", None, "review", [], {}):
            content = copy.deepcopy(self.review)
            content["study_profile"]["narrative_genre"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_deep_v2_content(content)
        content = copy.deepcopy(self.clinical)
        content["study_profile"]["narrative_genre"] = "perspective"
        with self.assertRaises(ValueError):
            validate_deep_v2_content(content)


if __name__ == "__main__":
    unittest.main()
