"""Freeze supplied evidence and rendering boundaries, not scientific conclusions.

No original-data reanalysis, accession correction or source reinterpretation is
performed here. Negative fixtures test the engineering transcription contract.
"""

import copy
import hashlib
import html
import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from build_publications import validate_deep_v2_content
from paper_discovery import scientific_content
from official_abstracts import EXCLUDED, load_official_abstracts
from site_common import PAPERS_DIR, index_master, load_site_config
from sync_common import ROOT, is_withdrawn, load_master, norm_doi, publication_authors
from validate_site import meta_contents, paper_json_ld_object, validate_v2_rendered_page


BASELINE = "30b242077142eb9ff13ca1089f8849644bd3e9dd"
UC = "doi-10-18632-aging-205564"
IDE = "idebenone-ferroptosis"
REP = "doi-10-1007-s11426-026-3629-x"
TARGETS = {
    UC: ("10.18632/aging.205564", "multicohort_omics", True, "evidence-uc"),
    IDE: ("10.1016/j.ejphar.2023.175569", "preclinical_multimodal", False, "evidence-idebenone"),
}
# Frozen canonical-JSON digests of the instruction-ledger transcription.
# They are constants, never derived from mutated fixtures or current files.
FROZEN = {
    UC: "a208c6c87989bef8e11e8de9d6679f932a4fb7b908578c795bc606b1770e7687",
    IDE: "702ca57262710f01ebf5a429741c5cb0b3f550e403d09559189ab46fb3cb1e27",
}
BOUNDARIES = {
    UC: ["not 606 independently deduplicated participants", "14 variables", "12-gene panel", "not prediction of future disease onset", "source provenance unresolved", "not as a verified download location", "Clinical drug efficacy was not established"],
    IDE: ["24 h and 2 h before surgery", "not relative percentage improvements", "21.82%", "33.76%", "not exclusively ferroptosis", "not complete gene-specific validation", "not human clinical efficacy evidence"],
}
COMPONENTS = {
    UC: ["Human data design", "Gene panel and classifier", "External discrimination", "Interpretability score", "Drug-signature hypotheses", "Single-cell provenance qualification"],
    IDE: ["Oxidative cellular injury", "Ferroptosis-focused cellular evidence", "Autophagy/pathway probes", "Animal timing and comparison", "Cardiac function and histology", "Myocardial molecular readouts"],
}


def digest(content):
    return hashlib.sha256(json.dumps(scientific_content(content), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def baseline(path):
    return subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT).decode("utf-8")


def validate_content(slug, content):
    doi, profile, external, prefix = TARGETS[slug]
    validate_deep_v2_content(content, slug)
    assert content["version"] == 2 and content["doi"] == doi
    study = content["study_profile"]
    assert study["profile_type"] == profile and study["external_validation"] is external
    assert "unique_total_n" not in study and "cohorts" not in study
    assert study["scale_metrics"] and study["counting_note"]
    findings = content["key_findings"]; layer = content["citation_layer"]
    assert (len(findings), len(content["qa"]), len(layer["citation_use_cases"]), len(layer["evidence_matrix"])) == (6, 6, 4, 6)
    assert layer["not_appropriate_as_evidence_for"] == content["evidence_scope"]["does_not_establish"]
    ids = {f"KF{i}" for i in range(1, 7)}
    assert {f["id"] for f in findings} == ids
    for i, (kf, qa, row) in enumerate(zip(findings, content["qa"], layer["evidence_matrix"]), 1):
        assert kf["id"] == f"KF{i}"
        assert qa["evidence_refs"] == row["evidence_refs"] == [kf["id"]]
        assert row["id"] == f"{prefix}-{i}" and row["component"] == COMPONENTS[slug][i - 1]
        assert row["source_locator"] == kf["source_locator"]
        assert row["scope"] != row["context"]
    for use in layer["citation_use_cases"]:
        assert use["evidence_refs"] and set(use["evidence_refs"]) <= ids
    values = [{v["label"]: v["value"] for v in kf["evidence"]} for kf in findings]
    if slug == UC:
        assert values[0]["article reported expression samples"] == "606"
        assert values[0]["datasets"] == "10"
        assert values[0]["UC expression samples"] == "87" and values[0]["control expression samples"] == "21"
        assert values[1]["named final UCRG panel"] == "12 genes" and "14 variables" in values[1]["Fig 3E legend"]
        assert list(values[2].items()) == [("GSE47908 AUC", "0.930"), ("GSE59071 AUC", "0.942"), ("GSE75214 AUC", "0.934"), ("GSE92415 AUC", "0.988"), ("GSE14580 AUC", "1.000")]
        assert values[4]["candidate compounds"] == "5"
        assert values[5]["cited accession"] == "GSE182272" and "unresolved" in values[5]["verification status"]
        assert "not as a verified download location" in content["provenance"]["data_source_note"]
    else:
        assert values[3]["preoperative dosing"] == "24 h and 2 h before surgery"
        assert values[4]["MI EF"] == "21.82%" and values[4]["MI plus idebenone EF"] == "33.76%"
        assert values[4]["Fig 8 reported n"] == "5"
        assert all(kf["source_locator"].startswith("Author-deposited full text:") for kf in findings)
    assert digest(content) == FROZEN[slug], "Frozen evidence or interpretation boundary changed"


class Ids(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])


class SixthBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = {slug: json.loads((ROOT / "data/deep_geo" / (slug + ".json")).read_text(encoding="utf-8")) for slug in TARGETS}

    def test_ledger_and_rendered_parity(self):
        master = load_master(); index_master(master)
        public = [p for p in master if not is_withdrawn(p)]
        by_doi = {norm_doi(p.get("doi")): p for p in public}
        config = load_site_config()
        for slug, content in self.contents.items():
            with self.subTest(slug=slug):
                validate_content(slug, content)
                item = by_doi[content["doi"]]
                assert item["slug"] == slug and item["title"] == content["display_title"]
                page = (PAPERS_DIR / (slug + ".html")).read_text(encoding="utf-8")
                markdown = (PAPERS_DIR / (slug + ".md")).read_text(encoding="utf-8")
                schema = paper_json_ld_object(page, slug)
                validate_v2_rendered_page(content, item, page, markdown, schema, by_doi, config)
                assert meta_contents(page, "citation_author") == publication_authors(item)
                assert page.count(f'<link rel="canonical" href="{config["site_url"]}/papers/{slug}.html"') == 1
                parser = Ids(); parser.feed(page)
                assert len(parser.ids) == len(set(parser.ids))
                anchors = [f"kf{i}" for i in range(1, 7)] + ["citation-use-cases", "citation-boundaries", "evidence-matrix"]
                anchors += [row["id"] for row in content["citation_layer"]["evidence_matrix"]]
                for anchor in anchors:
                    assert parser.ids.count(anchor) == 1
                    assert f'id="{anchor}"' in markdown or f"#{anchor}" in markdown
                for text in BOUNDARIES[slug]:
                    assert text in html.unescape(page) and text in markdown, text

    def test_metadata_abstracts_and_citation_identity(self):
        metadata = json.loads((ROOT / "data/citation_metadata.json").read_text(encoding="utf-8"))["papers"]
        abstracts = load_official_abstracts(load_master())
        uc_doi = TARGETS[UC][0]; ide_doi = TARGETS[IDE][0]; rep_doi = "10.1007/s11426-026-3629-x"
        assert {k: v for k, v in metadata[uc_doi].items() if k != "verified_sources"} == {"publication_date": "2024-02-16", "volume": "16", "issue": "4", "first_page": "3856", "last_page": "3879", "eissn": "1945-4589", "pmid": "38372705", "pmcid": "PMC10929837"}
        assert {k: v for k, v in metadata[ide_doi].items() if k != "verified_sources"} == {"publication_date": "2023-02-03", "volume": "943", "article_number": "175569", "pmid": "36740037"}
        assert metadata[rep_doi] == {"publication_date": "2026-09-15", "verified_sources": ["https://link.springer.com/article/10.1007/s11426-026-3629-x"]}
        assert abstracts[uc_doi]["source_type"] == "version_of_record" and abstracts[uc_doi]["verbatim"] is True
        assert abstracts[uc_doi]["source_url"] == "https://www.aging-us.com/article/205564/text"
        assert abstracts[uc_doi]["license"] == "CC-BY-4.0"
        assert len(abstracts[uc_doi]["abstract"]["text"].split("\n\n")) == 4
        for doi, slug in [(ide_doi, IDE), (rep_doi, REP)]:
            assert doi not in abstracts and doi not in EXCLUDED
            assert 'id="official-abstract"' not in (PAPERS_DIR / (slug + ".html")).read_text(encoding="utf-8")
        for slug in (UC, IDE, REP):
            path = f"citations/{slug}.csl.json"
            old = json.loads(baseline(path)); new = json.loads((ROOT / path).read_text(encoding="utf-8"))
            for key in ("DOI", "title", "author", "URL", "id", "type"):
                assert old.get(key) == new.get(key), (slug, key)
            assert "article-number" not in new
        uc = json.loads((ROOT / f"citations/{UC}.csl.json").read_text(encoding="utf-8"))
        assert uc["page"] == "3856-3879" and "number" not in uc
        assert "pages = {3856--3879}" in (ROOT / f"citations/{UC}.bib").read_text(encoding="utf-8")
        assert "SP  - 3856\nEP  - 3879" in (ROOT / f"citations/{UC}.ris").read_text(encoding="utf-8")
        ide = json.loads((ROOT / f"citations/{IDE}.csl.json").read_text(encoding="utf-8"))
        assert ide["number"] == "175569" and "page" not in ide
        assert "eid = {175569}" in (ROOT / f"citations/{IDE}.bib").read_text(encoding="utf-8")
        assert "C7  - 175569" in (ROOT / f"citations/{IDE}.ris").read_text(encoding="utf-8")

    def test_rep_date_only_and_pending_inventory(self):
        path = f"papers/{REP}.html"
        old = baseline(path); new = (ROOT / path).read_text(encoding="utf-8")
        expected = old.replace('<meta name="citation_publication_date" content="2026">', '<meta name="citation_publication_date" content="2026/09/15">\n<meta name="citation_date" content="2026/09/15">')
        assert new == expected
        path = f"citations/{REP}.csl.json"
        old = json.loads(baseline(path)); new = json.loads((ROOT / path).read_text(encoding="utf-8"))
        old["issued"] = {"date-parts": [[2026, 9, 15]]}; assert new == old
        path = f"citations/{REP}.ris"
        assert (ROOT / path).read_text(encoding="utf-8") == baseline(path).replace("PY  - 2026\n", "PY  - 2026\nDA  - 2026/09/15\n")
        assert not (ROOT / f"data/deep_geo/{REP}.json").exists()
        old = json.loads(baseline("paper_index.json")); new = json.loads((ROOT / "paper_index.json").read_text(encoding="utf-8"))
        assert old["researcher"] == new["researcher"] and old["version"] == new["version"]
        old_papers = old["papers"]; new_papers = new["papers"]
        assert len(old_papers) == len(new_papers) == 74
        for before, after in zip(old_papers, new_papers):
            if after["doi"] in {TARGETS[UC][0], TARGETS[IDE][0]}:
                before["paper_geo_status"] = "v2"
            assert before == after
        pending = {p["doi"] for p in new_papers if p["paper_geo_status"] == "pending"}
        assert pending == {"10.1007/s11426-026-3629-x", "10.1002/ggn2.202500053", "10.1016/j.curpro.2025.100054", "10.71321/fy14v342"}

    def test_protected_baseline_sources_pages_and_sitemap(self):
        names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE], cwd=ROOT).decode().splitlines()
        v2 = [p for p in names if p.startswith("data/deep_geo/") and p.endswith(".json") and json.loads(baseline(p)).get("version") == 2]
        assert len(v2) == 22
        allowed_sources = {"data/citation_metadata.json", "data/official_abstracts.json", f"data/deep_geo/{UC}.json", f"data/deep_geo/{IDE}.json", "scripts/official_abstracts.py", "scripts/test_citations.py", "scripts/test_official_abstracts.py", "scripts/test_paper_geo_v2.py", "scripts/test_citation_layer.py"}
        allowed_pages = {f"papers/{s}.html" for s in (UC, IDE, REP)} | {f"papers/{s}.md" for s in (UC, IDE)}
        allowed_citations = {f"citations/{s}.{ext}" for s in (UC, IDE, REP) for ext in ("bib", "ris", "csl.json")}
        protected = [p for p in names if (p.startswith(("data/", "scripts/", ".github/", "assets/", "papers/", "citations/")) or p in {"AGENTS.md", "robots.txt", "llms.txt", "llms-full.txt"}) and p not in allowed_sources | allowed_pages | allowed_citations]
        changes = subprocess.check_output(["git", "diff", "--name-only", BASELINE, "--", *protected], cwd=ROOT).decode()
        assert not changes, changes
        # ReP scientific Markdown and all three excluded works remain protected above.
        for name, delta in (("citation_metadata", 3), ("official_abstracts", 1)):
            path = f"data/{name}.json"; old = json.loads(baseline(path)); new = json.loads((ROOT / path).read_text(encoding="utf-8"))
            assert old["version"] == new["version"] and len(new["papers"]) == len(old["papers"]) + delta
            assert all(new["papers"][doi] == value for doi, value in old["papers"].items())
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        def inventory(text):
            return {u.find("s:loc", ns).text: u.find("s:lastmod", ns).text for u in ET.fromstring(text).findall("s:url", ns)}
        old = inventory(baseline("sitemap.xml")); new = inventory((ROOT / "sitemap.xml").read_text(encoding="utf-8"))
        assert set(old) == set(new) and len(new) == 76
        allowed = {f"https://drgezhang.com/papers/{s}.html" for s in (UC, IDE, REP)} | {"https://drgezhang.com/", "https://drgezhang.com/publications.html"}
        assert {url for url in old if old[url] != new[url]} <= allowed

    def reject(self, slug, mutation):
        content = copy.deepcopy(self.contents[slug]); mutation(content)
        with self.assertRaises((AssertionError, ValueError, KeyError)):
            validate_content(slug, content)

    def test_reject_samples_as_unique_patients(self):
        self.reject(UC, lambda c: c["key_findings"][0]["evidence"][0].update(value="606 unique patients"))

    def test_reject_resolved_single_cell_source(self):
        self.reject(UC, lambda c: c["key_findings"][5].update(claim="GSE182272 is a verified UC single-cell source."))

    def test_reject_cmap_as_effective_treatment(self):
        self.reject(UC, lambda c: c["key_findings"][4].update(claim="The five CMap candidates are proven effective UC treatments."))

    def test_reject_exclusively_post_infarction_initiation(self):
        self.reject(IDE, lambda c: c["key_findings"][3].update(claim="Idebenone was effective with exclusively post-infarction initiation."))

    def test_reject_ef_as_relative_survival_improvement(self):
        self.reject(IDE, lambda c: c["key_findings"][4].update(claim="Idebenone produced a 33.76% relative survival improvement."))

    def test_reject_nonexistent_matrix_locator(self):
        self.reject(IDE, lambda c: c["citation_layer"]["evidence_matrix"][0].update(source_locator="Fig. 99"))


if __name__ == "__main__":
    unittest.main()
