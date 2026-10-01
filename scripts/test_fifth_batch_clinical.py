"""Freeze the supplied fifth-batch evidence ledger, not revalidate its science.

These checks guard engineering transcription, boundaries and rendering. They
are not a participant-level reanalysis or independent source adjudication.
"""

import copy
import hashlib
import html
import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

from build_publications import validate_deep_v2_content
from paper_discovery import scientific_content
from official_abstracts import EXCLUDED, load_official_abstracts
from site_common import PAPERS_DIR, load_site_config
from sync_common import ROOT, is_withdrawn, load_master, norm_doi
from validate_site import paper_json_ld_object, validate_v2_rendered_page


BASELINE = "eb6ff1ff0a4f8a944846a45c66c08c5a33adb633"
AL = "doi-10-3389-fcvm-2025-1724572"
SLEEP = "doi-10-3389-fpubh-2025-1521372"
APATINIB = "doi-10-3389-fonc-2021-659217"
TARGETS = {
    AL: ("10.3389/fcvm.2025.1724572", 205504, 5, "evidence-al", "2026-01-05", "12", "1724572"),
    SLEEP: ("10.3389/fpubh.2025.1521372", 5837, 5, "evidence-sleep-hua", "2025-03-26", "13", "1521372"),
    APATINIB: ("10.3389/fonc.2021.659217", 32, 4, "evidence-apatinib", "2021-05-03", "11", "659217"),
}
# Frozen canonical-JSON digests of the reviewed instruction-ledger transcription.
# Constants do not derive from the current source or negative-fixture input.
FROZEN = {
    AL: "fad0750840db8f6c2f5e502e741af1e3f116b726b952240e777000a402fff7ae",
    SLEEP: "dbc91b659b64a8afc5a9ad9882d28c0d98ea337f9027b2a8f2ed0c20a0c82ea3",
    APATINIB: "111330a9faa08da6b6a342b502e27c43d3753304e8367ecbc1a784494f42169c",
}
ROOT_COHORTS = {
    AL: "UK Biobank analytic cohort",
    SLEEP: "NHANES linked-mortality analytic cohort",
    APATINIB: "Enrolled cohort — not the efficacy denominator",
}
BOUNDARIES = {
    AL: ["not a validated clinical prediction model", "not a proven causal pathway", "not a 115% absolute-risk increase", "not described here as a mean or median follow-up"],
    SLEEP: ["not an intervention-validated sleep prescription", "not an absolute-risk estimate", "does not prove that all sleep disorders", "Raw participant counts and survey-weighted percentages"],
    APATINIB: ["not the response-rate denominator", "42.71–78.84%", "Grade 3 hypertension", "No Grade 4 events or drug-related deaths were reported", "the body includes extrahepatic patients", "registry concordance was not independently adjudicated"],
}


def digest(content):
    return hashlib.sha256(json.dumps(scientific_content(content), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def baseline(path):
    return subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT)


def validate_content(slug, content):
    doi, total, count, prefix, _, _, _ = TARGETS[slug]
    validate_deep_v2_content(content, slug)
    assert content["version"] == 2 and content["doi"] == doi
    study = content["study_profile"]
    assert study["profile_type"] == "clinical_cohort"
    assert study["external_validation"] is False and "model_profile" not in content
    assert study["unique_total_n"] == total
    assert len(study["cohorts"]) == 1
    cohort = study["cohorts"][0]
    assert set(cohort) == {"name", "role", "n"}
    assert cohort["name"] == ROOT_COHORTS[slug] and cohort["n"] == total
    assert not re.search(r"training|validation|discovery|replication", cohort["role"], re.I)
    if slug == APATINIB:
        assert "Enrollment total" in cohort["role"] and "KF1" in cohort["role"]
    findings = content["key_findings"]
    layer = content["citation_layer"]
    assert (len(findings), len(content["qa"]), len(layer["citation_use_cases"]), len(layer["evidence_matrix"])) == (count, count, 4, count)
    ids = {f"KF{i}" for i in range(1, count + 1)}
    assert {f["id"] for f in findings} == ids
    for i, (kf, qa, row) in enumerate(zip(findings, content["qa"], layer["evidence_matrix"]), 1):
        assert kf["id"] == f"KF{i}"
        assert qa["evidence_refs"] == row["evidence_refs"] == [kf["id"]]
        assert row["id"] == f"{prefix}-{i}"
        assert row["source_locator"] == kf["source_locator"]
        assert row["scope"] != row["context"]
        assert len(row["component"].split()) >= 3 and "KF" not in row["component"]
    for use in layer["citation_use_cases"]:
        assert use["evidence_refs"] and set(use["evidence_refs"]) <= ids
    # Fixed quantitative ledger examples independent of the frozen digest.
    evidence = [{p["label"]: p["value"] for p in kf["evidence"]} for kf in findings]
    if slug == AL:
        assert evidence[0]["analytic participants"] == "205,504"
        assert evidence[0]["incident CVD events"] == "18,542"
        assert evidence[2]["hazard ratio"] == "2.15"
        assert evidence[4]["neutrophil count mediation estimate"] == "4.73%"
    elif slug == SLEEP:
        assert evidence[0]["analytic participants"] == "5,837" and evidence[0]["deaths"] == "906"
        assert evidence[3]["P"] == "0.651" and evidence[4]["estimated turning point"] == "7.23 h"
    else:
        assert evidence[0]["enrolled"] == "32" and evidence[0]["FAS safety population"] == "26"
        assert evidence[1]["efficacy denominator"] == "24"
        assert evidence[1]["DCR Results reported 95 percent CI"] == "42.71–78.84%"
        assert evidence[3]["Grade 3 hypertension"] == evidence[3]["Grade 3 leukopenia"] == "3 patients"
    assert digest(content) == FROZEN[slug], "Supplied ledger or interpretation boundary changed"


class FifthBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = {slug: json.loads((ROOT / "data/deep_geo" / (slug + ".json")).read_text(encoding="utf-8")) for slug in TARGETS}

    def test_ledger_and_rendered_parity(self):
        public = [p for p in load_master() if not is_withdrawn(p)]
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
                assert page.count(f'<link rel="canonical" href="{config["site_url"]}/papers/{slug}.html"') == 1
                for anchor in [f"kf{i}" for i in range(1, TARGETS[slug][2] + 1)] + ["citation-use-cases", "citation-boundaries", "evidence-matrix"]:
                    assert page.count(f'id="{anchor}"') == 1
                    assert f'id="{anchor}"' in markdown or f'#{anchor}' in markdown
                for text in BOUNDARIES[slug]:
                    assert text in html.unescape(page) and text in markdown, text
        assert by_doi[TARGETS[AL][0]]["year"] == 2026

    def test_metadata_and_abstracts(self):
        meta = json.loads((ROOT / "data/citation_metadata.json").read_text(encoding="utf-8"))["papers"]
        abstracts = load_official_abstracts(load_master())
        for slug, (doi, _, _, _, date, volume, number) in TARGETS.items():
            assert [meta[doi][k] for k in ("publication_date", "volume", "article_number")] == [date, volume, number]
            csl = json.loads((ROOT / "citations" / (slug + ".csl.json")).read_text(encoding="utf-8"))
            assert csl["DOI"] == doi and csl["number"] == number
            assert "article-number" not in csl and "page" not in csl
            page = (PAPERS_DIR / (slug + ".html")).read_text(encoding="utf-8")
            if slug == APATINIB:
                assert doi not in abstracts and doi not in EXCLUDED
                assert 'id="official-abstract"' not in page
                assert "abstract" not in paper_json_ld_object(page, slug)
            else:
                assert abstracts[doi]["verbatim"] is True
                assert abstracts[doi]["source_type"] == "version_of_record"
                assert abstracts[doi]["source_url"] == meta[doi]["verified_sources"][0]
                labels = [s["label"] for s in abstracts[doi]["abstract"]["sections"]]
                assert labels == (["Background", "Methods", "Results", "Conclusion"] if slug == AL else ["Objectives", "Materials and methods", "Results", "Conclusion"])

    def test_existing_evidence_identity_and_inventory_unchanged(self):
        names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE], cwd=ROOT).decode().splitlines()
        old_v2 = [p for p in names if p.startswith("data/deep_geo/") and p.endswith(".json") and json.loads(baseline(p)).get("version") == 2]
        assert len(old_v2) == 19
        protected = [p for p in names if p.startswith(("scripts/", ".github/", "assets/", "data/"))]
        permitted = {"data/citation_metadata.json", "data/official_abstracts.json", "scripts/official_abstracts.py", "scripts/test_citations.py", "scripts/test_official_abstracts.py", "scripts/test_paper_geo_v2.py", "scripts/test_citation_layer.py"}
        protected = [p for p in protected if p not in permitted]
        for path in old_v2:
            slug = path.rsplit("/", 1)[1][:-5]
            protected += [f"papers/{slug}.html", f"papers/{slug}.md"]
        luad = "doi-10-71321-fy14v342"
        protected += [f"papers/{luad}.{ext}" for ext in ("html", "md")]
        protected += [f"citations/{luad}.{ext}" for ext in ("bib", "ris", "csl.json")]
        changes = subprocess.check_output(["git", "diff", "--name-only", BASELINE, "--", *protected], cwd=ROOT).decode()
        assert not changes, changes
        for name, delta in (("citation_metadata", 3), ("official_abstracts", 2)):
            path = f"data/{name}.json"
            old = json.loads(baseline(path)); new = json.loads((ROOT / path).read_text(encoding="utf-8"))
            assert old["version"] == new["version"] and len(new["papers"]) == len(old["papers"]) + delta
            assert all(new["papers"][doi] == record for doi, record in old["papers"].items())
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        def inventory(data):
            return {u.find("s:loc", ns).text: u.find("s:lastmod", ns).text for u in ET.fromstring(data).findall("s:url", ns)}
        old = inventory(baseline("sitemap.xml")); new = inventory((ROOT / "sitemap.xml").read_bytes())
        assert set(old) == set(new) and len(new) == 76
        allowed_dates = {f"https://drgezhang.com/papers/{slug}.html" for slug in TARGETS} | {"https://drgezhang.com/", "https://drgezhang.com/publications.html"}
        assert {url for url in old if old[url] != new[url]} <= allowed_dates

    def reject(self, slug, mutation):
        content = copy.deepcopy(self.contents[slug]); mutation(content)
        with self.assertRaises((AssertionError, ValueError, KeyError)):
            validate_content(slug, content)

    def test_reject_all_recruited_ukb_as_analytic_sample(self):
        self.reject(AL, lambda c: c["key_findings"][0]["evidence"][0].update(value="502,366"))

    def test_reject_mediation_as_proven_intervention(self):
        self.reject(AL, lambda c: c["key_findings"][4].update(claim="Lowering neutrophils is proven to reduce CVD risk by 4.73%."))

    def test_reject_personal_sleep_prescription(self):
        self.reject(SLEEP, lambda c: c["key_findings"][4].update(claim="7.23 hours is a validated personal sleep prescription."))

    def test_reject_enrollment_as_orr_denominator(self):
        self.reject(APATINIB, lambda c: c["key_findings"][1]["evidence"][0].update(value="32"))

    def test_reject_dcr_interval_in_survival_days(self):
        self.reject(APATINIB, lambda c: c["key_findings"][1]["evidence"][-1].update(value="112.86–387.14 days"))

    def test_reject_no_grade_three_events(self):
        self.reject(APATINIB, lambda c: c["key_findings"][3].update(claim="No Grade 3 events occurred."))


if __name__ == "__main__":
    unittest.main()
