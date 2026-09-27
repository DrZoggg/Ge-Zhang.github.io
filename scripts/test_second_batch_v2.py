"""Regression checks for the supplied second-batch scientific invariants."""

import json

from sync_common import ROOT


def load(slug):
    return json.loads((ROOT / "data/deep_geo" / f"{slug}.json").read_text(encoding="utf-8"))


def counts(content, expected):
    assert content["version"] == 2
    assert len(content["key_findings"]) == expected
    assert len(content["qa"]) == expected
    assert len(content["citation_layer"]["citation_use_cases"]) == expected
    rows = content["citation_layer"]["evidence_matrix"]
    assert len(rows) == expected
    for finding, row in zip(content["key_findings"], rows):
        assert row["evidence_refs"] == [finding["id"]]
        assert row["source_locator"] == finding["source_locator"]
    assert all(question.get("evidence_refs") for question in content["qa"])


def main():
    rap = load("doi-10-1200-po-24-00089")
    counts(rap, 6)
    study = rap["study_profile"]
    assert study["profile_type"] == "clinical_cohort"
    assert study["unique_total_n"] == 506
    assert [cohort["n"] for cohort in study["cohorts"]] == [268, 116, 384, 122]
    assert sum(cohort["n"] for cohort in study["cohorts"] if not cohort.get("subset_of")) == 506
    model = rap["model_profile"]
    assert (model["initial_variables"], model["algorithm_count"], model["modeling_schemes"]) == (53, 12, 132)
    assert model["selected_algorithms"] == ["Surv.coxboost", "Surv.aorsf"]
    assert model["final_predictors"] == ["pTNM", "ROM", "CEA", "Ns", "PostCEA", "Ts", "CA199", "HLP", "Postchem", "Minutes"]
    assert [item["value"] for item in rap["key_findings"][5]["evidence"][:3]] == ["0.587", "0.754", "0.810"]
    assert "pmcid" not in rap["provenance"]
    clarification = (
        "The Results text reports Replication low/intermediate/high counts of 68/20/19, "
        "which sum to 107 and do not reconcile with the stated Replication cohort size of 116. "
        "These subgroup counts are retained as article-reported values; the denominator "
        "discrepancy is unresolved and must not be interpreted as documented exclusions "
        "or a complete partition of all 116 patients."
    )
    kf5 = next(item for item in rap["key_findings"] if item["id"] == "KF5")
    row = next(item for item in rap["citation_layer"]["evidence_matrix"]
               if item["id"] == "evidence-rap-aiscore-5")
    cu5 = next(item for item in rap["citation_layer"]["citation_use_cases"] if item["id"] == "CU5")
    label = "Article-reported Replication low/intermediate/high counts (sum 107; cohort 116; unresolved denominator discrepancy)"
    assert kf5["evidence"][3] == {"label": label, "value": "68 / 20 / 19"}
    assert sum(int(value) for value in kf5["evidence"][3]["value"].split(" / ")) == 107
    assert kf5["context"] == row["context"] == row["scope"] == clarification
    assert clarification in rap["limitations"] and clarification in cu5["supported_scope"]
    assert label + ": 68 / 20 / 19" in row["finding"]
    assert kf5["source_locator"] == row["source_locator"] == (
        "Results: Interpretability and Clinical Stratification of RAP-AIscore; Fig. 4A-E"
    )
    for extension in ("html", "md"):
        rendered = (ROOT / "papers" / f"doi-10-1200-po-24-00089.{extension}").read_text(encoding="utf-8")
        assert clarification in rendered
        assert label in rendered and "68 / 20 / 19" in rendered
    aaa = load("doi-10-1186-s12915-025-02400-x")
    counts(aaa, 7)
    assert aaa["study_profile"]["profile_type"] == "multicohort_omics"
    assert "unique_total_n" not in aaa["study_profile"]
    assert [item["value"] for item in aaa["key_findings"][3]["evidence"]] == ["968", "437", "375", "374", "50 genes"]
    assert [item["value"] for item in aaa["key_findings"][4]["evidence"]][1:] == [
        "0.911 / 0.917 / 0.926 / 0.955", "0.982 / 0.911 / 0.893 / 0.857", "0.956 / 0.887 / 0.506 / 0.514",
    ]
    assert "5 AAA and 4 controls" in aaa["limitations"][0]
    nlrp3 = load("nlrp3-ici")
    counts(nlrp3, 7)
    assert nlrp3["study_profile"]["profile_type"] == "preclinical_multimodal"
    assert nlrp3["study_profile"]["external_validation"] is False
    assert "unique_total_n" not in nlrp3["study_profile"]
    assert "tested preclinical melanoma models" in nlrp3["research_question"]
    assert [item["value"] for item in nlrp3["key_findings"][3]["evidence"][:3]] == ["68,058", "14", "8"]
    assert nlrp3["key_findings"][5]["evidence"][0]["value"] == "n=8/group"
    assert "Mouse treatment-after-injury experiment" in nlrp3["key_findings"][6]["context"]
    print("SECOND BATCH V2 TESTS PASS: RAP-AIscore, AAA and NLRP3 supplied counts and evidence levels")


if __name__ == "__main__":
    main()
