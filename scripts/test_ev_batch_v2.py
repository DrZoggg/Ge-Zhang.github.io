"""Third EV batch: supplied scientific boundaries, references and rendered parity."""

import copy
import html
import json
import unittest

from build_publications import validate_deep_v2_content
from site_common import PAPERS_DIR, load_site_config
from sync_common import ROOT, is_withdrawn, load_master, norm_doi
from validate_site import paper_json_ld_object, validate_v2_rendered_page


TARGETS = {
    "10.1111/jcmm.17789": ("doi-10-1111-jcmm-17789", 2023),
    "10.1111/jcmm.70258": ("doi-10-1111-jcmm-70258", 2024),
    "10.1111/jcmm.70725": ("doi-10-1111-jcmm-70725", 2025),
    "10.2147/ijn.s522157": ("doi-10-2147-ijn-s522157", 2025),
}


def values(finding):
    return {item["label"]: item["value"] for item in finding["evidence"]}


def validate_content(content):
    validate_deep_v2_content(content)
    assert content["version"] == 2
    study = content["study_profile"]
    assert "unique_total_n" not in study and "cohorts" not in study
    assert study["counting_note"].strip()
    findings = content["key_findings"]
    assert [item["id"] for item in findings] == [f"KF{i}" for i in range(1, 7)]
    layer = content["citation_layer"]
    assert len(content["qa"]) == len(layer["citation_use_cases"]) == len(layer["evidence_matrix"]) == 6
    assert [case["id"] for case in layer["citation_use_cases"]] == [f"CU{i}" for i in range(1, 7)]
    for item in content["qa"] + layer["citation_use_cases"] + layer["evidence_matrix"]:
        refs = item["evidence_refs"]
        assert refs and len(refs) == len(set(refs))
        assert set(refs) <= {finding["id"] for finding in findings}
    for row, finding in zip(layer["evidence_matrix"], findings):
        assert row["evidence_refs"] == [finding["id"]]
        assert row["source_locator"] == finding["source_locator"]
        assert row["component"] not in {f"KF{i}" for i in range(1, 7)}
        assert row["scope"] != row["context"]
    assert layer["not_appropriate_as_evidence_for"] == content["evidence_scope"]["does_not_establish"]
    doi = content["doi"]
    k1, k2, k3, k4, k5, k6 = findings
    assert study["profile_type"] == ("preclinical_multimodal" if doi == "10.2147/ijn.s522157" else "multicohort_omics")
    assert study["external_validation"] is (doi != "10.2147/ijn.s522157")
    if doi == "10.1111/jcmm.17789":
        assert values(k3) == {
            "Detected miRNA features": "3,687",
            "Final threshold as stated in Results": "Absolute logFC >0.5 and P<0.05",
            "Final differential features": "92", "Upregulated / downregulated": "48 / 44",
        }
        assert int(values(k3)["Final differential features"]) == sum(map(int, values(k3)["Upregulated / downregulated"].split(" / ")))
        assert "0.05" in k3["context"] and "unresolved reporting difference" in k3["context"]
        assert values(k6) == {
            "Table 1 hsa-miR-185-5p logFC": "1.04", "Table 1 hsa-miR-185-5p P value": "0.0322",
            "External 10-miRNA panel membership": "Not included in the listed qRT-PCR panel",
        }
        assert "rather than a member" in k6["claim"]
        assert "not reliably established" in study["counting_note"]
        assert values(k5)["External sample"] == "10 DCM patients and 6 healthy controls"
        assert values(k5)["Hub miRNAs tested"] == "10"
    elif doi == "10.1111/jcmm.70258":
        assert values(k1)["Discovery participants"] == "3 DCM; 5 healthy controls"
        assert values(k1)["External participants"] == "6 DCM; 4 healthy controls"
        assert values(k1)["Methods 2.7 platform"] == "LC Human ceRNA Array V1.0 (Agilent array workflow)"
        assert "internally inconsistent" in k1["claim"] and "microarray" in k1["context"]
        assert "sequencing" in values(k1)["Reporting difference"]
        assert values(k3)["Detected circRNAs"] == "865"
        assert values(k3)["Final differential set"] == "49"
        assert values(k3)["Upregulated / downregulated"] == "27 / 22"
        assert 49 == 27 + 22
        assert "Methods lists ten candidates" in k6["context"] and "describe nine" in k6["context"]
        assert values(k6)["Panel described in Results/Fig. 5"] == "9 circRNAs"
        assert "unresolved differences" in k5["claim"]
        assert "38-node network and 25 hubs" in values(k5)["Count qualification"]
        assert "also lists degrees <=5" in values(k5)["Table qualification"]
    elif doi == "10.1111/jcmm.70725":
        assert list(values(k1).values()) == ["10 / 5", "8 / 4", "18 / 9"]
        assert values(k3)["Analyzed protein panel"] == "92 proteins"
        assert values(k3)["Reported differential set"] == "5 proteins: 3 upregulated and 2 downregulated"
        assert values(k4)["Western blot"] == "IL-4, IL-6, MCP-1 and Oncostatin-M higher; Neurturin not statistically significant"
        assert values(k4)["ELISA"] == "IL-4, IL-6 and Oncostatin-M higher; MCP-1 and Neurturin lower"
        assert list(values(k5).items())[:5] == list(zip(
            ["IL-4 AUC", "IL-6 AUC", "MCP-1 AUC", "Neurturin AUC", "Oncostatin-M AUC"],
            ["0.760", "0.840", "0.800", "0.840", "0.900"]))
        assert "0.486-1.000" in values(k5)["Precision qualification"]
        assert "not a five-protein combined model" in k5["context"]
        assert "no longitudinal prediction" in k1["context"]
    else:
        assert doi == "10.2147/ijn.s522157"
        assert values(k1)["Loaded-particle DLS diameter"] == "172.35 ± 0.8 nm"
        assert values(k1)["Encapsulation efficiency"] == "98.0 ± 1.2%"
        assert values(k1)["Size-method distinction"] == "TEM describes approximately 100 nm; DLS reports hydrodynamic size"
        assert k6["source_locator"].endswith("; Fig. 2B-C")
        assert "in vitro" in k5["context"]
        assert "not treated patients" in study["counting_note"]
        assert "Animal intervention evidence only" in k3["context"]
        serialized = json.dumps(findings)
        assert all(token not in serialized for token in ("42.6%", "27.3%", "36.5%", "300 mg/kg"))


class EVBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = {doi: json.loads((ROOT / "data/deep_geo" / (slug+".json")).read_text(encoding="utf-8"))
                        for doi, (slug, _) in TARGETS.items()}

    def test_sources_and_rendering(self):
        public = [item for item in load_master() if not is_withdrawn(item)]
        by_doi = {norm_doi(item.get("doi")): item for item in public}
        config = load_site_config()
        for doi, content in self.contents.items():
            with self.subTest(doi=doi):
                validate_content(content)
                slug, year = TARGETS[doi]
                item = by_doi[doi]
                assert item["slug"] == slug and item["year"] == year
                assert content["display_title"] == item["title"]
                page = (PAPERS_DIR / (slug+".html")).read_text(encoding="utf-8")
                markdown = (PAPERS_DIR / (slug+".md")).read_text(encoding="utf-8")
                validate_v2_rendered_page(content, item, page, markdown,
                                         paper_json_ld_object(page, slug), by_doi, config)
                assert f'<link rel="canonical" href="{config["site_url"]}/papers/{slug}.html"' in page
                for finding in content["key_findings"]:
                    assert html.escape(finding["context"]) in page and finding["context"] in markdown

    def reject(self, doi, mutate):
        changed = copy.deepcopy(self.contents[doi])
        mutate(changed)
        with self.assertRaises((AssertionError, ValueError)):
            validate_content(changed)

    def test_reject_synthetic_participants(self):
        self.reject("10.1111/jcmm.17789", lambda c: c["study_profile"].update(unique_total_n=16))

    def test_reject_mir185_external_validation_claim(self):
        self.reject("10.1111/jcmm.17789", lambda c: c["key_findings"][5]["evidence"][2].update(value="Externally validated"))

    def test_reject_confirmed_sequencing(self):
        self.reject("10.1111/jcmm.70258", lambda c: c["key_findings"][0].update(
            claim="Confirmed sequencing", context="A verified sequencing platform."))

    def test_reject_erased_panel_discrepancy(self):
        self.reject("10.1111/jcmm.70258", lambda c: c["key_findings"][5].update(context="Ten candidates were validated."))

    def test_reject_concordant_elisa(self):
        self.reject("10.1111/jcmm.70725", lambda c: c["key_findings"][3]["evidence"][2].update(value="All five proteins higher"))

    def test_reject_liposome_external_validation(self):
        self.reject("10.2147/ijn.s522157", lambda c: c["study_profile"].update(external_validation=True))

    def test_reject_nonexistent_matrix_locator(self):
        self.reject("10.2147/ijn.s522157", lambda c: c["citation_layer"]["evidence_matrix"][5].update(source_locator="Fig. 99"))


if __name__ == "__main__":
    unittest.main()
