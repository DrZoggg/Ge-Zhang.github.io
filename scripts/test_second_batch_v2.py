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
    print("SECOND BATCH V2 TESTS PASS: RAP-AIscore supplied counts, predictors and external performance")


if __name__ == "__main__":
    main()
