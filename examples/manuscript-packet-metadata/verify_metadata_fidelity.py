"""Offline synthetic checks for the pinned manuscript-packet adaptation.

Usage: python verify_metadata_fidelity.py /path/to/patched/manuscript_packet.py
No article download, model, patient data, or extra package is required.
"""
from __future__ import annotations

import json
from pathlib import Path
import runpy
import sys
import tempfile


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    helper = Path(sys.argv[1]).resolve()
    module = runpy.run_path(str(helper))
    cases = [
        ("letter-topic", {"publication_type": "Letter"},
         "This Letter proposes linked public records, rather than presenting a new clinical trial.",
         ("Letter", "unknown", "unknown")),
        ("real-rct", {},
         "We conducted a randomized controlled trial of the intervention. No significant benefit was found.",
         ("randomized controlled trial", "randomized controlled trial", "unknown")),
        ("empirical-letter", {"publication_type": "Letter", "study_design": "cohort study"},
         "We analyzed original follow-up data.", ("Letter", "cohort study", "unknown")),
        ("future-trial", {"publication_type": "Letter"},
         "We will conduct a randomized controlled trial.", ("Letter", "unknown", "unknown")),
        ("negative-design", {}, "Our study is not a clinical trial.",
         ("primary/other", "unknown", "unknown")),
        ("quoted-trial", {"publication_type": "Commentary"},
         'This commentary quotes another team: "We conducted a clinical trial."',
         ("Commentary", "unknown", "unknown")),
        ("protocol", {"publication_type": "Protocol", "study_design": "randomized controlled trial"},
         "We will recruit participants after approval.",
         ("Protocol", "randomized controlled trial", "unknown")),
        ("synthesis", {"publication_type": "Journal Article", "study_design": "systematic review"},
         "We synthesize published studies.",
         ("Journal Article", "systematic review", "unknown")),
        ("metadata-array", {"publication_type": ["Journal Article", "Letter", "Randomized Controlled Trial"]},
         "We report original trial results.", ("Letter", "Randomized Controlled Trial", "unknown")),
        ("unknown", {"publication_type": "unknown", "study_design": "unknown"},
         "No design information was supplied.", ("unknown", "unknown", "unknown")),
        ("conflict", {"publication_type": "clinical trial", "study_design": "cohort study"},
         "Original results.", ("clinical trial", "unknown", "unknown")),
        ("caller-quality", {"publication_type": "Letter", "evidence_quality": "moderate",
                            "quality_rationale": "Synthetic caller assessment with a stated basis."},
         "This Letter addresses reporting practice.", ("Letter", "unknown", "moderate")),
        ("bare-quality", {"publication_type": "Letter", "evidence_quality": "high"},
         "This Letter addresses reporting practice.", ("Letter", "unknown", "high")),
        ("retracted", {"study_design": "clinical trial", "evidence_quality": "high",
                       "quality_rationale": "Synthetic caller assessment."},
         "Retracted trial report.", ("primary/other", "clinical trial", "exclude")),
    ]
    cases.extend([
        ("review-alias", {"publication_type": "review-article"},
         "This review discusses prior clinical studies.", ("review-article", "unknown", "unknown")),
        ("retrospective-cohort", {"publication_type": "research-article"},
         "The investigators developed a score in retrospective longitudinal cohorts.",
         ("research-article", "retrospective cohort study", "unknown")),
    ])
    cases.append(("secondary-dataset", {},
                  "This study analyzes a dataset from a clinical trial.",
                  ("primary/other", "unknown", "unknown")))
    inputs = []
    checks = 0
    for index, (label, metadata, excerpt, expected) in enumerate(cases, 1):
        source = {"title": "Synthetic metadata control " + label,
                  "url": "https://example.org/synthetic-" + label,
                  "doi": "10.5555/synthetic-" + label, "publish_date": "2025",
                  "excerpts": [excerpt], "extracted": False, **metadata}
        normalized = module["normalize_reference"](source, index)
        actual = tuple(normalized[key] for key in ("publication_type", "study_design", "evidence_quality"))
        assert actual == expected, (label, actual, expected)
        assert normalized["doi"] == source["doi"], label
        assert normalized["supporting_excerpts"] == source["excerpts"], label
        assert {"introduction", "discussion"} <= set(normalized["manuscript_sections"]), label
        checks += 4
        inputs.append(source)
    summary_source = {"title": "Synthetic summary fallback", "summary": "We conducted a cohort study."}
    assert module["normalize_reference"](summary_source, 1)["study_design"] == "cohort study"
    summary_source.update({"extracted": True, "extraction_excerpts": []})
    assert module["source_excerpts"](summary_source) == []
    checks += 2
    def packet_for(sources):
        return module["build_manuscript_packet"](
            query="Synthetic packet-path control", sources=sources,
            search_ledger=[], target_references=len(sources))

    summary = {"title": "Synthetic summary-only packet", "url": "https://example.org/summary-packet",
               "doi": "10.5555/synthetic-summary-packet",
               "summary": "We conducted a retrospective cohort study of follow-up records."}
    ref = packet_for([summary])["references"][0]
    assert ref["supporting_excerpts"] == [summary["summary"]]
    assert ref["study_design"] == "retrospective cohort study"
    assert ref["verification_status"] == "search-only"
    checks += 3
    empty = {**summary, "extracted": True, "extraction_excerpts": []}
    ref = packet_for([empty])["references"][0]
    assert ref["supporting_excerpts"] == []
    assert ref["verification_status"] == "search-only"
    checks += 2
    first = {"title": "Synthetic duplicate packet", "url": "https://example.org/duplicate-packet",
             "doi": "10.5555/synthetic-duplicate", "excerpts": ["Reporting practices are proposed."]}
    typed = {**first, "url": "https://example.org/typed-duplicate", "publication_type": "Letter",
             "study_design": "narrative argument", "evidence_quality": "contextual",
             "quality_rationale": "Synthetic caller appraisal."}
    duplicate_packet = None
    for representations in ([first, typed], [typed, first]):
        duplicate_packet = packet_for(representations)
        refs = duplicate_packet["references"]
        assert len(refs) == 1
        ref = refs[0]
        assert (ref["publication_type"], ref["study_design"], ref["evidence_quality"]) == (
            "Letter", "narrative argument", "contextual")
        assert ref["doi"] == first["doi"] and "Synthetic caller appraisal." in ref["quality_rationale"]
        assert ref["metadata_assertions"][0]["url"] == typed["url"]
        checks += 4
    conflicting = {**first, "publication_type": "Review", "study_design": "cohort study",
                   "evidence_quality": "low", "quality_rationale": "First assertion only."}
    ref = packet_for([conflicting, typed])["references"][0]
    assert (ref["publication_type"], ref["study_design"], ref["evidence_quality"]) == (
        "unknown", "unknown", "unknown")
    assert set(ref["metadata_conflicts"]) == {"publication_type", "study_design", "evidence_quality"}
    assert len(ref["metadata_assertions"]) == 2
    checks += 3
    for representations in ([first, typed], [typed, first], [conflicting, typed], [empty]):
        expected = packet_for(representations)["references"]
        joined_sources = representations
        for _ in range(3):
            joined_sources = module["deduplicate_sources"](joined_sources)
            assert packet_for(joined_sources)["references"] == expected
            checks += 1
    searched = module["deduplicate_sources"]([first, typed])
    extracted = {**typed, "extracted": True,
                 "extraction_excerpts": ["This Letter proposes linked public reporting practices."]}
    joined = module["deduplicate_sources"]([*searched, extracted])
    ref = packet_for(joined)["references"][0]
    assert (ref["publication_type"], ref["study_design"], ref["evidence_quality"]) == (
        "Letter", "narrative argument", "contextual")
    assert ref["verification_status"] == "extracted" and ref["supporting_excerpts"] == extracted["extraction_excerpts"]
    checks += 2
    sources = inputs[:3]
    packet = module["build_manuscript_packet"](
        query="Synthetic reporting and research-design comparison",
        sources=sources, search_ledger=[], target_references=len(sources))
    assert {item["doi"] for item in packet["references"]} == {item["doi"] for item in sources}
    checks += 1
    with tempfile.TemporaryDirectory(prefix="packet-metadata-check-") as destination:
        artifacts = module["save_packet"](packet, destination)
        assert all(Path(path).is_file() for path in artifacts.values())
        saved = json.loads(Path(artifacts["packet_json"]).read_text(encoding="utf-8"))
        assert saved["references"] == packet["references"]
        citations = Path(artifacts["references_bib"]).read_text(encoding="utf-8")
        assert all(source["doi"] in citations for source in sources)
        joined_artifacts = module["save_packet"](duplicate_packet, Path(destination) / "joined")
        joined = json.loads(Path(joined_artifacts["packet_json"]).read_text(encoding="utf-8"))
        assert joined["references"][0]["metadata_assertions"] == duplicate_packet["references"][0]["metadata_assertions"]
        checks += 4
    print(json.dumps({"status": "PASS", "synthetic_cases": len(cases),
                      "checks": checks, "scope": "offline function and saved-packet verification"}))


if __name__ == "__main__":
    main()
