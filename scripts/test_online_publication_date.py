"""Optional first-online dates must not change formal citation chronology."""

import json
from pathlib import Path
import subprocess
import tempfile
import types
import unittest

import build_publications as builder
import citation_common as citations
from sync_common import ROOT
import validate_site as validator


BASE = "ec52365181e8665004be43f9dd9e73858d39033d"
DOI = "10.1234/date-fixture"
SOURCES = ["https://example.org/verified-first-publication"]


def base_bytes(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def base_module(name, path):
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / path)
    exec(compile(base_bytes(path), module.__file__, "exec"), module.__dict__)
    return module


class OnlinePublicationDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = builder.load_site_config()
        cls.old_builder = base_module("baseline_build_publications", "scripts/build_publications.py")
        cls.old_citations = base_module("baseline_citation_common", "scripts/citation_common.py")
        cls.old_public = json.loads(base_bytes("publications.json"))
        cls.old_metadata = json.loads(base_bytes("data/citation_metadata.json"))["papers"]

    def publication(self, year=2027):
        return {
            "title": "Controlled cross-year publication date fixture",
            "journal": "Example Journal", "year": year, "type": "Article",
            "doi": DOI, "authors": ["Test Author"], "slug": "date-fixture",
            "paper_url": self.config["site_url"] + "/papers/date-fixture.html",
            "markdown_url": self.config["site_url"] + "/papers/date-fixture.md",
            "paper_geo_status": "none", "deep_geo": False, "featured": False,
        }

    def metadata(self, publication, fields):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            path.write_text(json.dumps({"version": 1, "papers": {DOI: fields}}), encoding="utf-8")
            return citations.load_citation_metadata([publication], path)

    def test_cross_year_and_same_year_dates_reach_both_schema_callers(self):
        for year, online in [(2027, "2026-10-15"), (2026, "2026-10-18")]:
            with self.subTest(year=year, online=online):
                publication = self.publication(year)
                metadata = self.metadata(publication, {
                    "online_publication_date": online, "verified_sources": SOURCES,
                })
                record = citations.citation_record(publication, metadata, self.config["site_url"])
                page = builder.render_paper_html(publication, config=self.config, citation_data=record)
                schema = validator.json_ld_object(page, "ScholarlyArticle", "date fixture")
                self.assertEqual(schema["datePublished"], online)
                validator.validate_schema_publication_date(schema, publication, record, "fixture")
                self.assertIn(f'<meta name="citation_publication_date" content="{year}">', page)
                self.assertNotIn('<meta name="citation_date"', page)
                catalog = builder.render_publications_page(
                    [publication] + self.old_public, self.config,
                    citation_metadata={**self.old_metadata, **metadata})
                profile = validator.json_ld_object(catalog, "ProfilePage", "catalog fixture")
                self.assertEqual(profile["hasPart"][0]["datePublished"], online)
                self.assertIn(f'"online_publication_date": "{online}"', json.dumps(metadata))

    def test_online_date_does_not_rewrite_formal_citation_exports(self):
        publication = self.publication()
        metadata = self.metadata(publication, {
            "online_publication_date": "2026-10-15", "verified_sources": SOURCES,
        })
        record = citations.citation_record(publication, metadata, self.config["site_url"])
        without_online = {key: value for key, value in record.items()
                          if key != "online_publication_date"}
        for render in (citations.render_bibtex, citations.render_ris, citations.render_csl_json):
            self.assertEqual(render(record).encode("utf-8"), render(without_online).encode("utf-8"))
        self.assertIn("year = {2027}", citations.render_bibtex(record))
        self.assertIn("PY  - 2027", citations.render_ris(record))
        self.assertNotIn("DA  -", citations.render_ris(record))
        self.assertEqual(json.loads(citations.render_csl_json(record))["issued"]["date-parts"], [[2027]])

    def test_invalid_online_dates_are_rejected(self):
        for value in (None, False, 20261015, "", " 2026-10-15", "2026-10",
                      "20261015", "2026/10/15", "2026-02-30", "2026-10-15T00:00:00Z"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.metadata(self.publication(), {
                    "online_publication_date": value, "verified_sources": SOURCES,
                })

    def test_online_date_requires_verified_https_sources(self):
        for sources in (None, [], ["http://example.org/source"]):
            fields = {"online_publication_date": "2026-10-15"}
            if sources is not None:
                fields["verified_sources"] = sources
            with self.subTest(sources=sources), self.assertRaises(ValueError):
                self.metadata(self.publication(), fields)

    def test_original_publication_date_same_year_contract_is_retained(self):
        fields = {"online_publication_date": "2026-10-15", "verified_sources": SOURCES}
        with self.assertRaisesRegex(ValueError, "publication_date disagrees with master year"):
            self.metadata(self.publication(), dict(fields, publication_date="2026-10-15"))
        # A synthetic exact issue date is valid; the real month-only record must omit it.
        accepted = self.metadata(self.publication(), dict(fields, publication_date="2027-02-03"))
        record = citations.citation_record(self.publication(), accepted, self.config["site_url"])
        schema = builder.paper_schema(self.publication(), self.publication()["paper_url"],
                                      self.config, citation_data=record)
        self.assertEqual(schema["datePublished"], "2026-10-15")
        self.assertIn("DA  - 2027/02/03", citations.render_ris(record))
        self.assertEqual(json.loads(citations.render_csl_json(record))["issued"]["date-parts"],
                         [[2027, 2, 3]])

    def test_validator_rejects_issue_year_in_place_of_explicit_first_date(self):
        publication = self.publication()
        fields = {"online_publication_date": "2026-10-15"}
        with self.assertRaises(validator.ValidationError):
            validator.validate_schema_publication_date(
                {"datePublished": "2027"}, publication, fields, "mutated fixture")
        validator.validate_schema_publication_date({"datePublished": "2027"}, publication, {}, "legacy")

    def test_legacy_schema_catalog_and_formal_exports_are_byte_identical(self):
        self.assertEqual(len(self.old_public), 77)
        for publication in self.old_public:
            with self.subTest(doi=publication.get("doi"), layer="schema"):
                expected = self.old_builder.paper_schema(publication, publication["paper_url"], self.config)
                record = citations.citation_record(publication, self.old_metadata, self.config["site_url"])
                actual = builder.paper_schema(publication, publication["paper_url"], self.config,
                                               citation_data=record)
                self.assertEqual(json.dumps(actual, ensure_ascii=False).encode("utf-8"),
                                 json.dumps(expected, ensure_ascii=False).encode("utf-8"))
                old_record = self.old_citations.citation_record(
                    publication, self.old_metadata, self.config["site_url"])
                self.assertEqual(record, old_record)
                if record:
                    self.assertNotIn("online_publication_date", record)
                    for name in ("render_bibtex", "render_ris", "render_csl_json"):
                        self.assertEqual(getattr(citations, name)(record).encode("utf-8"),
                                         getattr(self.old_citations, name)(old_record).encode("utf-8"))
        expected_catalog = self.old_builder.render_publications_page(self.old_public, self.config)
        actual_catalog = builder.render_publications_page(
            self.old_public, self.config, citation_metadata=self.old_metadata)
        self.assertEqual(actual_catalog.encode("utf-8"), expected_catalog.encode("utf-8"))
        # Default callers still use the original three positional arguments.
        self.assertEqual(builder.paper_schema(self.publication(), self.publication()["paper_url"], self.config),
                         self.old_builder.paper_schema(self.publication(), self.publication()["paper_url"],
                                                       self.config))


if __name__ == "__main__":
    unittest.main()
