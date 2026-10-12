"""Frozen acceptance contract for the PR 14/15 publication release; no writes."""

import hashlib
import html
import json
import re
import subprocess
import unittest
from collections import Counter

from build_publications import validate_deep_v2_content
from citation_common import (
    citation_plain_text, citation_record, load_citation_metadata,
    render_bibtex, render_csl_json, render_ris,
)
from site_common import load_deep_geo, load_featured, load_site_config
from sync_common import ROOT, is_withdrawn, load_master, norm_doi
from validate_site import meta_contents, paper_json_ld_object, validate_v2_rendered_page


# Remote main after PR 14 was merged, before integrating the two new records.
BASELINE = "e6081a2f2912983bb2f0105aef6932959161019d"
SCIENCE = "10.1126/science.aek9583"
MEDICINE = "10.1016/j.medd.2026.100004"
JDI = "10.1111/jdi.70462"
AIHF = "10.1038/s41467-024-50415-9"
# Reviewed B-only promotion; A remains Pending with its existing identity.
B_V2 = "10.1007/s11426-026-3629-x"
B_CARD = "papers/doi-10-1007-s11426-026-3629-x.html"
SCIENCE_SHA256 = "ff93dc81e2c7e8a6e8ee573b4529f4ac2b96b42dbcef607d5b4e1a5b310f869e"
IDENTITIES = {
    SCIENCE: {
        "slug": "doi-10-1126-science-aek9583",
        "type": "Letter",
        "title": "Recording results from single-patient trials",
        "journal": "Science",
        "authors": ["Ge Zhang", "Honglin Zheng", "Qiang Li", "Taiqi Zhao", "Teng Li"],
        "date_parts": [2026, 10, 1],
        "position": 1,
    },
    MEDICINE: {
        "slug": "doi-10-1016-j-medd-2026-100004",
        "type": "Correspondence",
        "title": "Multimodal AI for cardiovascular care must learn when not to predict",
        "journal": "Medicine Discovery",
        "authors": [
            "Yahui Han", "Qiang Li", "Taiqi Zhao", "Shanshan Cai", "Biyun Li",
            "Kaisaierjiang Kadier", "Tianshu Gu", "Zhonghua Sun", "Pengyuan Xu",
            "Dezhi Liu", "Moyan Li", "Xufeng Huang", "Qian Guo", "Yuan Cheng",
            "Honglin Zheng", "Ge Zhang",
        ],
        "date_parts": [2026, 9, 22],
        "position": 16,
    },
}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def baseline(path):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT).decode("utf-8")


def plain(markup):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", markup)).split())


def featured_cards(markup):
    region = re.search(r'<section id="featured">(.*?)</section>', markup, re.S)
    if region is None:
        raise AssertionError("Missing rendered Selected Research section")
    cards = []
    for card in re.findall(r'<article\b[^>]*class="card paper"[^>]*>(.*?)</article>', region[1], re.S):
        heading = re.search(r'<h3><a href="([^"]+)">(.*?)</a></h3>', card, re.S)
        summary = re.search(r"<p>(.*?)</p>", card, re.S)
        if heading is None or summary is None:
            raise AssertionError("Selected Research card lost its paper link or summary")
        cards.append((heading[1], plain(heading[2]), plain(summary[1])))
    return cards


def publication_records(markup):
    return re.findall(r'<article\b[^>]*data-paper-record="true"[^>]*>(.*?)</article>', markup, re.S)


class PublicationReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = load_master()
        cls.by_doi = {norm_doi(p.get("doi")): p for p in cls.master}
        cls.config = load_site_config()
        cls.enhancement = load_citation_metadata(cls.master)
        cls.index = json.loads(read("paper_index.json"))["papers"]
        cls.old_index = json.loads(baseline("paper_index.json"))["papers"]
        cls.content = json.loads(read(f'data/deep_geo/{IDENTITIES[SCIENCE]["slug"]}.json'))

    def test_verified_science_v2_and_rendered_evidence(self):
        path = ROOT / "data/deep_geo" / (IDENTITIES[SCIENCE]["slug"] + ".json")
        # Ignore checkout newline conversion, but freeze the reviewed content bytes.
        self.assertEqual(hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(), SCIENCE_SHA256)
        content = self.content
        validate_deep_v2_content(content, IDENTITIES[SCIENCE]["slug"])
        self.assertEqual(content["doi"], SCIENCE)
        self.assertEqual(content["version"], 2)
        self.assertEqual(content["study_profile"]["narrative_genre"], "correspondence")
        self.assertEqual(content["study_profile"]["scale_metrics"][0], {"label": "Publication genre", "value": "Letter"})
        forbidden = {
            "population", "primary_endpoint", "secondary_endpoint", "unique_total_n",
            "cohorts", "cohort", "model_profile", "sample_size", "treatment_effects",
            "trial_outcomes", "external_validation", "data_modalities",
        }
        self.assertFalse(forbidden.intersection(content))
        self.assertFalse(forbidden.intersection(content["study_profile"]))
        self.assertIn("not an observed n=1 dataset", content["study_profile"]["counting_note"])
        self.assertIn("no new clinical trial", content["study_profile"]["study_design"])
        self.assertEqual([f["id"] for f in content["key_findings"]], [f"KF{i}" for i in range(1, 6)])
        self.assertEqual(len(content["qa"]), 5)
        self.assertEqual(len(content["citation_layer"]["evidence_matrix"]), 5)
        for finding, qa, row in zip(content["key_findings"], content["qa"], content["citation_layer"]["evidence_matrix"]):
            self.assertEqual(qa["evidence_refs"], [finding["id"]])
            self.assertEqual(row["evidence_refs"], [finding["id"]])
            self.assertEqual(row["finding"], finding["claim"])
            self.assertEqual(row["source_locator"], finding["source_locator"])
        slug = IDENTITIES[SCIENCE]["slug"]
        markup, markdown = read(f"papers/{slug}.html"), read(f"papers/{slug}.md")
        schema = paper_json_ld_object(markup, slug)
        validate_v2_rendered_page(content, self.by_doi[SCIENCE], markup, markdown, schema, self.by_doi, self.config)
        for label in ("Key Arguments", "Article profile", "Article Scope & Approach", "What This Article Adds"):
            self.assertIn(label, html.unescape(markup))
            self.assertIn(label, markdown)
        self.assertNotIn("Deep GEO · Pending", markup)
        self.assertNotIn("Deep GEO · Pending", markdown)
        self.assertEqual(schema["@type"], "ScholarlyArticle")

    def test_full_authors_types_citation_files_and_identity(self):
        for doi, expected in IDENTITIES.items():
            with self.subTest(doi=doi):
                item = self.by_doi[doi]
                for field in ("slug", "type", "title", "journal", "authors"):
                    self.assertEqual(item[field], expected[field])
                self.assertEqual(item["year"], 2026)
                self.assertEqual(item["url"], f"https://doi.org/{doi}")
                slug = expected["slug"]
                markup, markdown = read(f"papers/{slug}.html"), read(f"papers/{slug}.md")
                self.assertEqual(meta_contents(markup, "citation_author"), expected["authors"])
                self.assertEqual(meta_contents(markup, "citation_doi"), [doi])
                self.assertIn(f'{expected["type"]} · 2026', markup)
                self.assertIn(f'Type: {expected["type"]}\n', markdown)
                full_authors = markdown.split("## Full Authors\n", 1)[1].split("\n## ", 1)[0]
                self.assertEqual(re.findall(r"^\d+\. (.+)$", full_authors, re.M), expected["authors"])
                schema = paper_json_ld_object(markup, slug)
                self.assertEqual(schema["@type"], "ScholarlyArticle")
                self.assertEqual([a["name"] for a in schema["author"]], expected["authors"])
                identities = [i for i, a in enumerate(schema["author"], 1) if a.get("@id") == self.config["person_id"]]
                self.assertEqual(identities, [expected["position"]])
                canonical = f'{self.config["site_url"]}/papers/{slug}.html'
                self.assertEqual(schema["url"], canonical)
                self.assertIn(f'<link rel="canonical" href="{canonical}">', markup)
                self.assertIn(f"Canonical page: {canonical}", markdown)
                record = citation_record(item, self.enhancement, self.config["site_url"])
                self.assertIsNotNone(record)
                self.assertIn(html.escape(citation_plain_text(record)), markup)
                bib, ris = read(f"citations/{slug}.bib"), read(f"citations/{slug}.ris")
                csl_text = read(f"citations/{slug}.csl.json")
                self.assertEqual(bib, render_bibtex(record))
                self.assertEqual(ris, render_ris(record))
                self.assertEqual(csl_text, render_csl_json(record))
                self.assertEqual(re.search(r"^  author = \{(.*)\},$", bib, re.M)[1].split(" and "), expected["authors"])
                self.assertEqual([line[6:] for line in ris.splitlines() if line.startswith("AU  - ")], expected["authors"])
                self.assertIn(f'  note = {{{expected["type"]}}},', bib)
                self.assertIn(f'M3  - {expected["type"]}\n', ris)
                csl = json.loads(csl_text)
                self.assertEqual([a["literal"] for a in csl["author"]], expected["authors"])
                self.assertEqual(csl["genre"], expected["type"])
                self.assertEqual(csl["type"], "article-journal")
                self.assertEqual(csl["DOI"], doi)
                self.assertEqual(csl["issued"]["date-parts"], [expected["date_parts"]])
                for suffix in ("bib", "ris", "csl.json"):
                    self.assertIn(f'../citations/{slug}.{suffix}', markup)

    def test_medicine_article_number_without_fabricated_pagination(self):
        slug = IDENTITIES[MEDICINE]["slug"]
        record = citation_record(self.by_doi[MEDICINE], self.enhancement, self.config["site_url"])
        self.assertEqual(record["article_number"], "100004")
        self.assertFalse({"volume", "issue", "first_page", "last_page"}.intersection(record))
        csl = json.loads(read(f"citations/{slug}.csl.json"))
        self.assertEqual(csl["number"], "100004")
        self.assertFalse({"volume", "issue", "page", "article-number"}.intersection(csl))
        bib, ris, markup = read(f"citations/{slug}.bib"), read(f"citations/{slug}.ris"), read(f"papers/{slug}.html")
        self.assertIn("eid = {100004}", bib)
        self.assertNotRegex(bib, r"(?m)^  (volume|number|pages) =")
        self.assertIn("C7  - 100004\n", ris)
        self.assertNotRegex(ris, r"(?m)^(VL|IS|SP|EP)  - ")
        for tag in ("citation_volume", "citation_issue", "citation_firstpage", "citation_lastpage"):
            self.assertEqual(meta_contents(markup, tag), [])

    def test_independent_selection_order_and_original_summaries(self):
        for path, current in (("data/featured_papers.json", load_featured()), ("data/deep_geo_papers.json", load_deep_geo())):
            with self.subTest(controller=path):
                old = json.loads(baseline(path))["papers"]
                self.assertEqual(len(old), 28)
                self.assertEqual(len(current), 29)
                self.assertEqual(current[0]["doi"], SCIENCE)
                self.assertEqual(current[1]["doi"], AIHF)
                self.assertEqual(current[1:], old)
                self.assertNotIn(MEDICINE, [p["doi"] for p in current])
        cards = featured_cards(read("index.html"))
        self.assertEqual(cards[0][0], f'papers/{IDENTITIES[SCIENCE]["slug"]}.html')
        self.assertEqual(cards[1][0], "papers/aihflevel.html")
        # B's empty controller summary falls back to its reviewed Deep summary.
        # All other existing card links, titles and summaries remain protected.
        self.assertEqual(
            [card for card in cards[1:] if card[0] != B_CARD],
            [card for card in featured_cards(baseline("index.html")) if card[0] != B_CARD],
        )
        # B's new source is frozen independently by test_pending_b_v2.py.
        for entry in json.loads(baseline("data/deep_geo_papers.json"))["papers"]:
            if entry["doi"] == B_V2:
                continue
            slug = self.by_doi[entry["doi"]]["slug"]
            path = f"data/deep_geo/{slug}.json"
            if (ROOT / path).exists():
                self.assertEqual(json.loads(read(path)), json.loads(baseline(path)), path)

    def test_published_counts_deduplication_and_protected_urls(self):
        exports = {"master": self.master, "paper_index": self.index, "publications": json.loads(read("publications.json"))}
        for name, rows in exports.items():
            with self.subTest(export=name):
                counts = Counter(norm_doi(p.get("doi")) for p in rows if p.get("doi"))
                self.assertTrue(all(n == 1 for n in counts.values()))
                self.assertEqual(counts[JDI], 1)
                self.assertEqual(counts[SCIENCE], 1)
                self.assertEqual(counts[MEDICINE], 1)
        self.assertEqual(len(self.master), 78)
        self.assertEqual(sum(not is_withdrawn(p) for p in self.master), 77)
        self.assertEqual(len(self.index), len(self.old_index) + 2)
        self.assertEqual(len(self.index), 77)
        self.assertEqual(len(exports["publications"]), 77)
        old_v2 = {p["doi"] for p in self.old_index if p["paper_geo_status"] == "v2"}
        v2 = {p["doi"] for p in self.index if p["paper_geo_status"] == "v2"}
        self.assertEqual(v2, old_v2 | {SCIENCE, B_V2})
        self.assertEqual(len(v2), 28)
        current = {p["doi"]: p for p in self.index if p.get("doi")}
        for old in self.old_index:
            if old.get("doi"):
                for field in ("doi", "title", "type", "journal", "year", "paper_url", "markdown_url"):
                    self.assertEqual(current[old["doi"]][field], old[field], (old["doi"], field))
        old_master = json.loads(baseline("data/publications_master.json"))
        for old in old_master:
            key = norm_doi(old.get("doi"))
            if key:
                for field in ("doi", "title", "type", "journal", "year", "authors", "slug", "url"):
                    self.assertEqual(self.by_doi[key].get(field), old.get(field), (key, field))
        medicine_index = current[MEDICINE]
        self.assertFalse(medicine_index["featured"])
        self.assertFalse(medicine_index["deep_geo"])
        self.assertEqual(medicine_index["paper_geo_status"], "none")
        records = publication_records(read("publications.html"))
        self.assertEqual(len(records), 77)
        for doi in (SCIENCE, MEDICINE, JDI):
            self.assertEqual(sum(f'href="https://doi.org/{doi}"' in record for record in records), 1)

    def test_science_discovery_label_is_letter(self):
        questions = json.loads(read("research/questions.json"))
        rows = questions["questions"] if isinstance(questions, dict) else questions
        science_rows = [row for row in rows if row.get("doi") == SCIENCE]
        self.assertEqual(len(science_rows), 1)
        self.assertEqual(science_rows[0]["publication_type"], "Letter")
        markup = read("research/questions.html")
        card = re.search(r'<article class="card" id="' + IDENTITIES[SCIENCE]["slug"] + r'">(.*?)</article>', markup, re.S)
        self.assertIsNotNone(card)
        self.assertIn('<p class="meta">Letter</p>', card[1])
        self.assertNotIn('<p class="meta">narrative review</p>', card[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
