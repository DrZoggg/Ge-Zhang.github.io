"""Check faithful implementation of the frozen ledger, not original research validity."""

import copy
import json
import subprocess
import unittest

from build_publications import validate_deep_v2_content
from site_common import PAPERS_DIR, load_site_config
from sync_common import ROOT, is_withdrawn, load_master, norm_doi
from validate_site import paper_json_ld_object, validate_v2_rendered_page


BASELINE = "7459864465947c7dee96adde876d37735d3aa081"
TARGETS = {
    "circadian-ihd": (6, 6, 4, 6),
    "doi-10-1016-j-joim-2025-06-003": (6, 6, 4, 6),
    "doi-10-1002-mdr2-70004": (7, 7, 5, 7),
}
# Explicit source, units, uses, locators and boundaries supplied in the task ledger.
FROZEN = {
    "circadian-ihd": {
        "doi": "10.1038/s41598-024-65236-5",
        "display_title": "Molecular subtypes of ischemic heart disease based on circadian rhythm",
        "counting_note": "GSE184073 cells are not independent patients. GSE59867 contains repeated follow-up of 111 STEMI patients and 46 stable CAD controls; its 436 expression samples are not 436 independent patients. Follow-up represents post-infarction recovery time points, not 24-hour circadian monitoring of the same individual. External dataset counts are article-reported samples and are not summed into a deduplicated participant total. External validation means retrospective expression-template evaluation, not prospective clinical utility. GSE70049 is a Danio rerio setb morphant expression experiment, not a verified mouse circadian perturbation.",
        "evidence": [
            [
                {
                    "label": "Post-QC cells",
                    "value": "2,237"
                },
                {
                    "label": "Analyzed samples",
                    "value": "2"
                },
                {
                    "label": "Non-grey modules",
                    "value": "8"
                }
            ],
            [
                {
                    "label": "Formula",
                    "value": "CRDscore = Srandom - SCADCRgenes"
                },
                {
                    "label": "Random features",
                    "value": "1,000"
                },
                {
                    "label": "Single-cell cutoff",
                    "value": "75th percentile"
                },
                {
                    "label": "Bulk cutoff",
                    "value": "Median"
                }
            ],
            [
                {
                    "label": "GSE70049 organism",
                    "value": "Danio rerio"
                },
                {
                    "label": "GSE70049 experiment",
                    "value": "setb morphant expression experiment"
                }
            ],
            [
                {
                    "label": "Type1 samples",
                    "value": "124"
                },
                {
                    "label": "Type2 samples",
                    "value": "93"
                },
                {
                    "label": "Type3 samples",
                    "value": "87"
                },
                {
                    "label": "Type4 samples",
                    "value": "132"
                },
                {
                    "label": "Total expression samples",
                    "value": "436"
                }
            ],
            [
                {
                    "label": "Datasets",
                    "value": "GSE20680; GSE20681; GSE43292; GSE62646"
                }
            ],
            [
                {
                    "label": "Contractile markers",
                    "value": "Lower expression"
                },
                {
                    "label": "Immune and collagen pathways",
                    "value": "Associated enrichment differences"
                }
            ]
        ],
        "claims": [
            "The analysis of GSE184073 constructed a single-cell co-expression foundation related to coronary disease.",
            "CRDscore was constructed as a research score from target-gene expression and a random background.",
            "The article reports external reference-data evaluation, but the use of GSE70049 requires qualification.",
            "Expression-based subtyping of GSE59867 yielded four groups.",
            "NTP was used to evaluate subtype assignment in four external expression datasets.",
            "Type2 showed higher CRDscore and immune-inflammatory expression characteristics."
        ],
        "locators": [
            "Results: Construction of WGCNA network in scRNA-seq dataset; Fig. 1",
            "Methods: Calculation of CRDscore based on circadian-related genes",
            "Methods: Data processing; NCBI GEO GSE70049 record",
            "Methods: Construction and validation of the CRD-related subtypes of CAD; Results: subtype identification; Fig. 4",
            "Methods: Construction and validation of the CRD-related subtypes of CAD; Fig. 4",
            "Results: functional and immune microenvironment analyses; Figs. 5-6"
        ],
        "scopes": [
            "Cells are not independent patients; two analyzed samples do not establish population-level robustness.",
            "The score does not directly measure an individual's circadian phase, amplitude or period. The two data-layer cutoffs are not one clinical threshold.",
            "The evidence does not establish that all four reference experiments are verified mouse circadian interventions. No intended replacement accession is inferred.",
            "These are expression-sample groups, not 436 independent patients. The grouping does not resolve independence of repeated follow-up samples or outcome analyses.",
            "External expression-template reproducibility is not prospective risk prediction or demonstrated clinical utility.",
            "Computational estimates and expression associations do not establish causal plaque transitions or benefit from immunotherapy or chronotherapy."
        ],
        "source_version": ""
    },
    "doi-10-1016-j-joim-2025-06-003": {
        "doi": "10.1016/j.joim.2025.06.003",
        "display_title": "Integrated-omics analysis defines subtypes of hepatocellular carcinoma based on circadian rhythm",
        "counting_note": "Cell counts, candidate genes, HCC cohort samples and separate circadian reference experiments are different units. No complete unique-participant total is inferred. The five external datasets have different analytical uses: the four Fig. 5A and four Fig. 5B sets overlap but are not identical and must not be added as eight independent cohorts. External validation means retrospective cross-dataset expression/classification evaluation, not prospective clinical utility or direct physiological rhythm measurement in HCC patients.",
        "evidence": [
            [
                {
                    "label": "Analyzed cells",
                    "value": "11,383"
                },
                {
                    "label": "Genes from modules M2/M4/M5",
                    "value": "562"
                }
            ],
            [
                {
                    "label": "Reference datasets",
                    "value": "GSE10045; GSE150381; GSE39445"
                }
            ],
            [
                {
                    "label": "TCGA-LIHC n",
                    "value": "369"
                },
                {
                    "label": "Subtypes",
                    "value": "CS-H; CS-L; CS-M"
                }
            ],
            [
                {
                    "label": "Fig. 5A datasets",
                    "value": "ICGC_LIRI; GSE14520; GSE54236; GSE104580"
                },
                {
                    "label": "Fig. 5B datasets",
                    "value": "ICGC_LIRI; GSE14520; GSE54236; GSE27150"
                }
            ],
            [
                {
                    "label": "Analyses",
                    "value": "Expression enrichment; CIBERSORT; IPS"
                }
            ],
            [
                {
                    "label": "Evidence",
                    "value": "Expression correlation and network prioritization"
                }
            ]
        ],
        "claims": [
            "Single-cell modules supplied the HCCcrds gene set.",
            "The score was evaluated in separate clock, feeding and sleep-reference data.",
            "TCGA-LIHC analysis identified CS-H, CS-L and CS-M, with poorer outcomes associated with CS-H.",
            "External subtype and survival analyses used overlapping but different cohort sets.",
            "Subtypes differed in proliferation/metabolic programs and inferred immune characteristics.",
            "NNMT and MARCKSL1 were among subtype-associated candidate genes."
        ],
        "locators": [
            "Author-deposited full text: Results 3.1; Fig. 2",
            "Author-deposited full text: Results 3.2; Fig. 3",
            "Author-deposited full text: Results 3.3-3.4; Fig. 4",
            "Author-deposited full text: Results 3.5; Fig. 5 legend",
            "Author-deposited full text: Results 3.6-3.7; Fig. 6",
            "Author-deposited full text: Results 3.8; Table 2; final PubMed abstract"
        ],
        "scopes": [
            "Cells and candidate genes are not patient counts or demonstrated causal regulators.",
            "Reference-experiment evaluation does not mean HCC patients underwent longitudinal physiological circadian measurements.",
            "Association does not establish that circadian disruption causes liver cancer or constitute a validated clinical decision rule.",
            "Do not claim that all five cohorts validated survival, or add the two four-cohort analyses as eight independent cohorts.",
            "IPS and immune deconvolution are not an observed immunotherapy-response trial.",
            "This evidence synthesis does not claim independent causal intervention or therapeutic validation of these genes."
        ],
        "source_version": "Bibliographic identity was checked against the final PubMed/publisher record. Detailed evidence locators refer to the author-deposited full text; final typeset figure-level equivalence was not independently re-established."
    },
    "doi-10-1002-mdr2-70004": {
        "doi": "10.1002/mdr2.70004",
        "display_title": "Optimized Dynamic Network Biomarker Deciphers a High-Resolution Heterogeneity Within Thyroid Cancer Molecular Subtypes",
        "counting_note": "TCGA counts of 544 in Methods and 484 in GRN analysis describe different reported analytical stages; no reason for excluding the numerical difference is inferred. Methods reports 17,709 cells and Results 17,518, without a reconstructed QC-exclusion process. One reported donor is not a large participant cohort; 48 tumor and 48 adjacent specimens do not mean 96 independent patients. Cohorts, cells, paired specimens and cultured-cell experiments are not added into a unique-participant total. External validation means retrospective expression-template/classifier evaluation, not prospective clinical utility.",
        "evidence": [
            [
                {
                    "label": "DNB genes",
                    "value": "36"
                }
            ],
            [
                {
                    "label": "Expression bins",
                    "value": "100"
                },
                {
                    "label": "Background samplings",
                    "value": "1,000"
                },
                {
                    "label": "Reported survival cutoff",
                    "value": "0.4"
                }
            ],
            [
                {
                    "label": "Candidate combinations",
                    "value": "20"
                },
                {
                    "label": "Selected combination",
                    "value": "CV-PAM"
                },
                {
                    "label": "Reported external NTP datasets",
                    "value": "6"
                }
            ],
            [
                {
                    "label": "Candidate genes",
                    "value": "296"
                },
                {
                    "label": "Final genes",
                    "value": "12"
                },
                {
                    "label": "Final classifier",
                    "value": "Neural network"
                },
                {
                    "label": "External classifier cohorts",
                    "value": "5"
                }
            ],
            [
                {
                    "label": "Reported donors",
                    "value": "1"
                },
                {
                    "label": "Cells in Methods",
                    "value": "17,709"
                },
                {
                    "label": "Cells in Results",
                    "value": "17,518"
                },
                {
                    "label": "Annotated populations",
                    "value": "7"
                }
            ],
            [
                {
                    "label": "Tumor specimens",
                    "value": "48"
                },
                {
                    "label": "Adjacent specimens",
                    "value": "48"
                },
                {
                    "label": "TPC-1 silencing",
                    "value": "Reduced proliferation and migration"
                }
            ],
            [
                {
                    "label": "Evidence",
                    "value": "Computational scoring and signature matching"
                }
            ]
        ],
        "claims": [
            "Stage II had the highest reported network instability signal.",
            "TCPSLevel was associated with clinical and outcome differences.",
            "The ensemble analysis yielded three molecular subtypes.",
            "miniPC classified the consensus subtype labels using a compact gene set.",
            "Single-cell analysis localized expression patterns across cellular compartments.",
            "ASPH was evaluated in human tissues and through TPC-1 silencing.",
            "IPS and CMap supplied candidate immune/drug-response hypotheses."
        ],
        "locators": [
            "Methods 2.2; Results 3.1; Fig. 1",
            "Methods 2.4; Results 3.2; Fig. 2",
            "Methods 2.6-2.7; Results 3.3; Fig. 3",
            "Methods 2.8; Results 3.4; Fig. 4",
            "Methods 2.1.1 and 2.3; Results 3.7; Fig. 5K-N",
            "Methods: tissue and cell experiments; Results 3.6 and 3.8; Fig. 6",
            "Methods 2.10 and 2.20; Results 3.5; Discussion"
        ],
        "scopes": [
            "Cross-sectional stage comparisons do not establish longitudinal prediction of each patient's future deterioration time.",
            "The reported cutoff is not a cross-cohort locked clinical threshold. Grouping rules used in other analyses are not automatically equivalent.",
            "Methods 2.6 prints GSE333630 whereas other locations use GSE33630. These are not silently rewritten as a fully verified accession inventory.",
            "This is subtype classification, not prospective individual survival-benefit validation. Unverified figure-only accuracy or AUC values are not reconstructed.",
            "A single donor and a large cell count do not establish large-population replication. No explanation for the count difference is invented.",
            "Paired tissues are not 96 independent patients. ASCL2-ASPH network inference is not direct binding validation, and cell effects do not establish human targeted-treatment efficacy.",
            "Predicted compounds are not proven effective treatments. IPS is not an observed outcome in patients receiving immunotherapy."
        ],
        "source_version": ""
    }
}


def validate_content(slug, content):
    validate_deep_v2_content(content)
    fixed = FROZEN[slug]
    assert content["version"] == 2 and content["doi"] == fixed["doi"]
    assert content["display_title"] == fixed["display_title"]
    study = content["study_profile"]
    assert study["profile_type"] == "multicohort_omics"
    assert study["external_validation"] is True
    assert "unique_total_n" not in study and "cohorts" not in study
    assert study["counting_note"] == fixed["counting_note"]
    findings = content["key_findings"]
    layer = content["citation_layer"]
    rows = layer["evidence_matrix"]
    assert (len(findings),len(content["qa"]),len(layer["citation_use_cases"]),len(rows)) == TARGETS[slug]
    assert [finding["id"] for finding in findings] == [f"KF{i}" for i in range(1,len(findings)+1)]
    assert [case["id"] for case in layer["citation_use_cases"]] == [f"CU{i}" for i in range(1,len(layer["citation_use_cases"])+1)]
    assert [finding["evidence"] for finding in findings] == fixed["evidence"]
    assert [finding["claim"] for finding in findings] == fixed["claims"]
    assert [finding["source_locator"] for finding in findings] == fixed["locators"]
    assert [row["scope"] for row in rows] == fixed["scopes"]
    for item in content["qa"] + layer["citation_use_cases"] + rows:
        refs = item["evidence_refs"]
        assert refs and len(refs)==len(set(refs))
        assert set(refs) <= {finding["id"] for finding in findings}
    for finding,row in zip(findings,rows):
        assert row["evidence_refs"] == [finding["id"]]
        assert row["source_locator"] == finding["source_locator"]
        assert row["component"] not in {item["id"] for item in findings}
        assert row["scope"] != row["context"]
        assert finding["claim"] in row["finding"]
    assert layer["not_appropriate_as_evidence_for"] == content["evidence_scope"]["does_not_establish"]
    if fixed["source_version"]:
        assert content["provenance"]["source_version"] == fixed["source_version"]
    if slug == "circadian-ihd":
        assert sum(int(item["value"]) for item in findings[3]["evidence"][:4]) == 436
        assert "GSE59867" in study["counting_note"] and "111 STEMI patients" in study["counting_note"]
        assert "46 stable CAD controls" in study["counting_note"]
    elif slug == "doi-10-1016-j-joim-2025-06-003":
        sets = [set(item["value"].split("; ")) for item in findings[3]["evidence"]]
        assert sets[0] - sets[1] == {"GSE104580"}
        assert sets[1] - sets[0] == {"GSE27150"}
        assert len(sets[0] | sets[1]) == 5
    else:
        assert "544" in study["counting_note"] and "484" in study["counting_note"]
        assert "17,709" in study["counting_note"] and "17,518" in study["counting_note"]
        assert "96 independent patients" in study["counting_note"]
        summary_and_concepts = json.dumps([content["summary"],content["concepts"]]).lower()
        assert "circadian" not in summary_and_concepts and "chronotherapy" not in summary_and_concepts


class FourthBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = {slug:json.loads((ROOT/"data/deep_geo"/(slug+".json")).read_text(encoding="utf-8")) for slug in TARGETS}

    def test_frozen_sources_and_rendering(self):
        public = [item for item in load_master() if not is_withdrawn(item)]
        by_doi = {norm_doi(item.get("doi")):item for item in public}
        config = load_site_config()
        for slug,content in self.contents.items():
            with self.subTest(slug=slug):
                validate_content(slug,content)
                item=by_doi[content["doi"]]
                assert item["slug"]==slug and item["title"]==content["display_title"]
                page=(PAPERS_DIR/(slug+".html")).read_text(encoding="utf-8")
                markdown=(PAPERS_DIR/(slug+".md")).read_text(encoding="utf-8")
                validate_v2_rendered_page(content,item,page,markdown,paper_json_ld_object(page,slug),by_doi,config)
                assert f'<link rel="canonical" href="{config["site_url"]}/papers/{slug}.html"' in page

    def test_protected_baseline_and_luad(self):
        protected = ["data/publications_master.json","data/featured_papers.json","data/deep_geo_papers.json",
                     "data/research_clusters.json","data/profile_config.json",".github/workflows/static.yml",
                     "scripts/build_publications.py","scripts/validate_staged_citations.py"]
        slugs = ["aihflevel","apvs","smc-fate","olink-dcm","doi-10-1038-s41698-026-01699-1",
                 "doi-10-1002-ehf2-14003","doi-10-1093-eurheartj-ehaf523","doi-10-1172-jci194175",
                 "doi-10-1002-mdr2-70052","doi-10-1200-po-24-00089","doi-10-1186-s12915-025-02400-x",
                 "nlrp3-ici","doi-10-1111-jcmm-17789","doi-10-1111-jcmm-70258",
                 "doi-10-1111-jcmm-70725","doi-10-2147-ijn-s522157","doi-10-71321-fy14v342"]
        for slug in slugs:
            protected += ["data/deep_geo/"+slug+".json","papers/"+slug+".html","papers/"+slug+".md"]
        protected += ["citations/doi-10-71321-fy14v342"+ext for ext in (".bib",".ris",".csl.json")]
        changed=subprocess.check_output(["git","diff","--name-only",BASELINE,"--",*protected],cwd=ROOT).decode()
        assert not changed, changed
        for name,delta in (("citation_metadata",3),("official_abstracts",2)):
            path="data/"+name+".json"
            old=json.loads(subprocess.check_output(["git","show",BASELINE+":"+path],cwd=ROOT))
            new=json.loads((ROOT/path).read_text(encoding="utf-8"))
            assert new["version"]==old["version"] and len(new["papers"])==len(old["papers"])+delta
            assert all(new["papers"][doi]==record for doi,record in old["papers"].items())
            assert new["papers"].get("10.71321/fy14v342")==old["papers"].get("10.71321/fy14v342")

    def reject(self,slug,mutate):
        content=copy.deepcopy(self.contents[slug])
        mutate(content)
        with self.assertRaises((AssertionError,ValueError,KeyError)):
            validate_content(slug,content)

    def test_reject_436_unique_patients(self):
        self.reject("circadian-ihd",lambda c:c["key_findings"][3]["evidence"][4].update(value="436 unique patients"))

    def test_reject_mouse_reference(self):
        self.reject("circadian-ihd",lambda c:c["key_findings"][2]["evidence"][1].update(value="confirmed mouse circadian perturbation"))

    def test_reject_identical_hcc_cohorts(self):
        self.reject("doi-10-1016-j-joim-2025-06-003",lambda c:c["key_findings"][3]["evidence"][1].update(value=c["key_findings"][3]["evidence"][0]["value"]))

    def test_reject_erased_source_version(self):
        self.reject("doi-10-1016-j-joim-2025-06-003",lambda c:c["provenance"].pop("source_version"))

    def test_reject_cells_as_patients(self):
        self.reject("doi-10-1002-mdr2-70004",lambda c:c["key_findings"][4]["evidence"][2].update(label="Patients in Results",value="17,518 patients"))

    def test_reject_minipc_survival_benefit(self):
        self.reject("doi-10-1002-mdr2-70004",lambda c:c["key_findings"][3].update(claim="miniPC is a prospectively validated survival-benefit model."))

    def test_reject_cmap_treatment_efficacy(self):
        self.reject("doi-10-1002-mdr2-70004",lambda c:c["key_findings"][6].update(claim="CMap candidates are proven effective treatment."))

    def test_reject_nonexistent_locator(self):
        self.reject("circadian-ihd",lambda c:c["citation_layer"]["evidence_matrix"][0].update(source_locator="Fig. 99"))


if __name__ == "__main__":
    unittest.main()
