"""Frozen instruction-ledger checks for two narrative articles, not reanalysis."""
import copy
import html
import json
import subprocess
import unittest

from build_publications import validate_deep_v2_content
from official_abstracts import EXCLUDED, load_official_abstracts
from site_common import PAPERS_DIR, load_site_config
from sync_common import ROOT, load_master
from test_author_metadata import VERIFIED_IDENTITIES, assert_identity_record, assert_identity_schema, assert_identity_csl
from test_sixth_batch_evidence import Ids
from validate_site import meta_contents, paper_json_ld_object, validate_v2_rendered_page

BASELINE = "f8a700d7181cc26585cd135a1e17d63a21b5f672"
A = "doi-10-1002-ggn2-202500053"
B = "doi-10-1016-j-curpro-2025-100054"
TARGETS = {
    A: ("10.1002/ggn2.202500053", "perspective", "evidence-ai-ensemble"),
    B: ("10.1016/j.curpro.2025.100054", "correspondence", "evidence-cardiovascular-ai"),
}
# Fixed assertions refer to the supplied ledger, never to a mutated fixture.
CLAIMS = {
    A: [
        "Choose complementary learners in relation to the clinical context rather than pursuing a single algorithm as universally optimal.",
        "Evaluate and select models using aggregate evidence across independent cohorts.",
        "Interpret SHAP attributions as distribution-dependent and examine them alongside sensitivity analysis and calibration.",
        "Account for distribution shift, computational resources, standardization and clinical workflows when planning translation.",
    ],
    B: [
        "Develop multimodal AI along two directions: mechanism-oriented research and individualized digital twins.",
        "Integrate imaging and molecular information to formulate network and disease-subtyping hypotheses.",
        "Explore updateable physiological models, image-to-mesh workflows and treatment-scenario simulation.",
        "Address longitudinal data, computational resources, prospective evaluation, privacy and governance before clinical translation.",
    ],
}
LOCATORS = {A: ["Section 4.1", "Section 4.2", "Sections 4.3 and 6", "Sections 6-7"],
            B: ["Sections 1-2", "Sections 2.1-2.2", "Section 3", "Sections 4.1-4.3"]}
COMPONENTS = {A: ["Learner integration", "Multi-cohort evaluation", "Attribution robustness", "Deployment constraints"],
              B: ["Research agenda", "Cross-modal biological interpretation", "Patient-specific simulation", "Translation requirements"]}
LABELS = ["Key Arguments", "Article profile", "What This Article Adds", "Article Scope & Approach",
          "When This Article Is Useful to Cite", "What This Article Should Not Be Cited to Claim"]


def baseline(path):
    return subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT).decode("utf-8")


def validate_content(slug, content):
    validate_deep_v2_content(content, slug)
    doi, genre, prefix = TARGETS[slug]
    assert content["version"] == 2 and content["doi"] == doi
    study = content["study_profile"]
    assert study["profile_type"] == "narrative_review" and study["narrative_genre"] == genre
    forbidden = {"population", "primary_endpoint", "secondary_endpoint", "data_modalities",
                 "external_validation", "unique_total_n", "cohorts", "cohort", "model_profile"}
    assert not forbidden.intersection(study) and not forbidden.intersection(content)
    assert study["scale_metrics"] == [
        {"label": "Article format", "value": genre.title()},
        {"label": "Evidence basis", "value": "Narrative argument and discussion of cited prior research"},
        {"label": "Empirical evaluation reported in this article", "value": "No new empirical evaluation reported"},
    ]
    assert study["evidence_type"] == "Methodological proposal and narrative synthesis; no new empirical evaluation reported in this article."
    assert 80 <= len(content["author_summary"].split()) <= 120
    findings = content["key_findings"]; layer = content["citation_layer"]
    assert tuple(map(len, [findings, content["qa"], layer["citation_use_cases"], layer["evidence_matrix"]])) == (4, 4, 4, 4)
    assert layer["not_appropriate_as_evidence_for"] == content["evidence_scope"]["does_not_establish"]
    for i, (kf, qa, use, row) in enumerate(zip(findings, content["qa"], layer["citation_use_cases"], layer["evidence_matrix"])):
        assert kf["id"] == f"KF{i+1}"
        assert kf["claim"] == row["finding"] == CLAIMS[slug][i]
        assert kf["source_locator"] == row["source_locator"] == LOCATORS[slug][i]
        assert qa["evidence_refs"] == use["evidence_refs"] == row["evidence_refs"] == [kf["id"]]
        assert row["id"] == f"{prefix}-{i+1}" and row["component"] == COMPONENTS[slug][i]
        assert row["evidence_level"] == ("Methodological proposal" if slug == A else "Narrative synthesis")
        assert row["scope"] == use["supported_scope"] != row["context"]
        assert qa["question"] == use["query"] and qa["question"].endswith("?")
        assert "this study" not in qa["question"].lower()
        assert qa["answer"] == kf["claim"] + " " + kf["context"]
    assert [r["doi"] for r in content["related_papers"]] == (
        ["10.1038/s41467-024-50415-9", "10.1200/po.24.00089", "10.1016/j.isci.2023.107587"]
        if slug == A else [TARGETS[A][0]])
    if slug == B:
        assert "not a claim" in content["related_papers"][0]["relationship"]
        assert "author-deposited" in content["provenance"]["source_version"]


class NarrativeArticleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = {s: json.loads((ROOT / f"data/deep_geo/{s}.json").read_text(encoding="utf-8")) for s in TARGETS}

    def test_ledger_parity_and_identity(self):
        master = load_master(); by_doi = {p.get("doi"): p for p in master}; config = load_site_config()
        for slug, content in self.contents.items():
            with self.subTest(slug=slug):
                validate_content(slug, content)
                doi = TARGETS[slug][0]; item = by_doi[doi]; identity = VERIFIED_IDENTITIES[doi]
                assert_identity_record(item, identity)
                assert content["display_title"] == item["title"]
                page = (PAPERS_DIR / f"{slug}.html").read_text(encoding="utf-8")
                markdown = (PAPERS_DIR / f"{slug}.md").read_text(encoding="utf-8")
                schema = paper_json_ld_object(page, slug)
                validate_v2_rendered_page(content, item, page, markdown, schema, by_doi, config)
                assert_identity_schema(schema["author"], identity, config)
                assert meta_contents(page, "citation_author") == identity["authors"]
                assert_identity_csl(json.loads((ROOT / f"citations/{slug}.csl.json").read_text(encoding="utf-8")), identity)
                for label in LABELS:
                    assert label in html.unescape(page) and label in markdown
                for label in ["Key Findings", "Review profile", "What This Review Adds", "Review Design & Evidence Synthesis", "When This Study Is Useful to Cite", "What This Study Should Not Be Cited to Claim"]:
                    assert f">{label}</h" not in page and f"## {label}\n" not in markdown
                parser = Ids(); parser.feed(page)
                assert len(parser.ids) == len(set(parser.ids))
                for anchor in [f"kf{i}" for i in range(1,5)] + ["citation-use-cases", "citation-boundaries", "evidence-matrix"]:
                    assert parser.ids.count(anchor) == 1 and f'<a id="{anchor}"></a>' in markdown

    def test_protected_sources_exports_and_original_v2(self):
        names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE], cwd=ROOT).decode().splitlines()
        original = [n for n in names if n.startswith("data/deep_geo/") and n.endswith(".json") and json.loads(baseline(n)).get("version") == 2]
        assert len(original) == 24
        for path in original:
            content = json.loads((ROOT / path).read_text(encoding="utf-8"))
            assert "narrative_genre" not in content["study_profile"]
        protected = [n for n in names if n.startswith("citations/")] + ["data/publications_master.json", "data/citation_metadata.json"]
        protected += original
        protected += [f"papers/{p.rsplit('/',1)[-1][:-5]}.{ext}" for p in original for ext in ("html", "md")]
        for path in protected:
            self.assertEqual((ROOT / path).read_text(encoding="utf-8"), baseline(path), path)
        records = load_official_abstracts(load_master())
        previous = json.loads(baseline("data/official_abstracts.json"))["papers"]
        assert all(records[d] == r for d, r in previous.items())
        assert set(records) - set(previous) == {TARGETS[A][0]} and len(records) == 19
        a = records[TARGETS[A][0]]
        assert a["source_type"] == "publisher" and a["verbatim"] is True and a["license"] == "CC-BY-4.0"
        assert a["source_url"] == "https://advanced.onlinelibrary.wiley.com/doi/full/10.1002/ggn2.202500053"
        assert TARGETS[B][0] not in records and TARGETS[B][0] not in EXCLUDED
        metadata = json.loads((ROOT / "data/citation_metadata.json").read_text(encoding="utf-8"))["papers"]
        assert len(metadata) == 27 and "publication_date" not in metadata[TARGETS[B][0]]

    def test_negative_ledger_fixtures(self):
        mutations = [
            (A, "clinical genre", lambda c: c["study_profile"].update(profile_type="clinical_cohort")),
            (A, "unknown genre", lambda c: c["study_profile"].update(narrative_genre="review")),
            (A, "empty genre", lambda c: c["study_profile"].update(narrative_genre="")),
            (A, "invented cohort", lambda c: c["study_profile"].update(cohorts=[{"name":"New cohort", "n":100, "role":"validation"}])),
            (A, "completed validation", lambda c: c["key_findings"][1].update(claim="Completed clinical validation established clinical benefit.")),
            (B, "validated therapeutic twin", lambda c: c["key_findings"][2].update(claim="A validated therapeutic digital twin improves patient outcomes.")),
            (B, "incorrect locator", lambda c: c["citation_layer"]["evidence_matrix"][0].update(source_locator="Section 99")),
            (B, "empirical scale", lambda c: c["study_profile"]["scale_metrics"][2].update(value="Completed prospective clinical validation")),
            (B, "external validation", lambda c: c["study_profile"].update(external_validation=True)),
        ]
        for slug, label, mutation in mutations:
            content = copy.deepcopy(self.contents[slug]); mutation(content)
            with self.subTest(fixture=label), self.assertRaises((ValueError, AssertionError)):
                validate_content(slug, content)


if __name__ == "__main__":
    unittest.main()
