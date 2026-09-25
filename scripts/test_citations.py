"""Focused citation metadata, export, and Circadian Review regression checks."""

import copy
import json
import tempfile
from pathlib import Path

from citation_common import (
    CITATIONS_DIR,
    citation_files,
    citation_record,
    citation_skip_reason,
    load_citation_metadata,
)
from site_common import PAPERS_DIR, load_site_config
from sync_common import is_withdrawn, load_master, norm_doi, publication_authors
from validate_site import meta_contents, validate_citations


CIRCADIAN_DOI = "10.1002/mdr2.70052"


def reject_metadata(public, papers):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "citation_metadata.json"
        path.write_text(json.dumps({"version": 1, "papers": papers}), encoding="utf-8")
        try:
            load_citation_metadata(public, path)
        except ValueError:
            return
    raise AssertionError(f"Invalid citation metadata was accepted: {papers}")


def run_tests():
    master = load_master()
    public = [item for item in master if not is_withdrawn(item)]
    withdrawn = [item for item in master if is_withdrawn(item)]
    config = load_site_config()
    enhancements = load_citation_metadata(public)
    assert list(enhancements) == [CIRCADIAN_DOI]
    eligible = sum(not citation_skip_reason(item) for item in public)
    assert validate_citations(public, config) == {
        "eligible": eligible, "skipped": len(public) - eligible,
        "bib": eligible, "ris": eligible, "csl": eligible,
    }
    circadian = next(item for item in public if norm_doi(item.get("doi")) == CIRCADIAN_DOI)
    record = citation_record(circadian, enhancements, config["site_url"])
    assert len(record["authors"]) == 23
    assert record["authors"] == publication_authors(circadian)
    assert record["title"] == circadian["title"]
    assert record["journal"] == circadian["journal"]
    assert record["canonical_url"] == f"{config['site_url']}/papers/{circadian['slug']}.html"
    assert record["doi_url"] == "https://doi.org/10.1002/mdr2.70052"
    assert (record["publication_date"], record["volume"], record["issue"],
            record["first_page"], record["last_page"], record["issn"],
            record["eissn"], record["publisher"]) == (
        "2026-01-05", "2", "2", "236", "279", "2998-4963", "2998-4971", "Wiley"
    )
    page = (PAPERS_DIR / f"{circadian['slug']}.html").read_text(encoding="utf-8")
    assert meta_contents(page, "citation_date") == ["2026/01/05"]
    for tag, value in (
        ("citation_volume", "2"), ("citation_issue", "2"),
        ("citation_firstpage", "236"), ("citation_lastpage", "279"),
        ("citation_issn", "2998-4963"), ("citation_eIssn", "2998-4971"),
        ("citation_publisher", "Wiley"),
    ):
        assert meta_contents(page, tag) == [value]
    files = citation_files(record)
    bib = (CITATIONS_DIR / files["bib"]).read_text(encoding="utf-8")
    ris = (CITATIONS_DIR / files["ris"]).read_text(encoding="utf-8")
    csl = json.loads((CITATIONS_DIR / files["csl"]).read_text(encoding="utf-8"))
    assert f"doi = {{{CIRCADIAN_DOI}}}" in bib
    assert f"DO  - {CIRCADIAN_DOI}" in ris
    assert csl["DOI"] == CIRCADIAN_DOI
    assert csl["title"] == record["title"]
    assert [author["literal"] for author in csl["author"]] == record["authors"]
    assert " and ".join(record["authors"]) in bib
    assert [line.removeprefix("AU  - ") for line in ris.splitlines()
            if line.startswith("AU  - ")] == record["authors"]
    for publication in public:
        if publication.get("type") != "Preprint":
            continue
        preprint = citation_record(publication, enhancements, config["site_url"])
        if preprint is None:
            continue
        preprint_files = citation_files(preprint)
        assert (CITATIONS_DIR / preprint_files["bib"]).read_text(encoding="utf-8").startswith("@misc{")
        assert (CITATIONS_DIR / preprint_files["ris"]).read_text(encoding="utf-8").startswith("TY  - GEN")
        assert json.loads((CITATIONS_DIR / preprint_files["csl"]).read_text(encoding="utf-8"))["type"] == "manuscript"
    for item in withdrawn:
        if item.get("slug"):
            assert all(not (CITATIONS_DIR / name).exists()
                       for name in (f"{item['slug']}.bib", f"{item['slug']}.ris",
                                    f"{item['slug']}.csl.json"))
    valid = enhancements[CIRCADIAN_DOI]
    for bad in (
        {"title": "overridden"}, {"publication_date": "2025-01-05"},
        {"publication_date": "2026-02-30"}, {"issn": "invalid"},
        {"pmid": "none"}, {"pmcid": "PMC0"},
        {"first_page": "279", "last_page": "236"},
        {"volume": "pending"}, {"issue": " "},
    ):
        changed = copy.deepcopy(valid)
        changed.update(bad)
        reject_metadata(public, {CIRCADIAN_DOI: changed})
    reject_metadata(public, {"10.9999/non-public": valid})
    reject_metadata(public, {CIRCADIAN_DOI.upper(): valid})
    print(f"CITATION TESTS PASS: {eligible} eligible, {len(public) - eligible} skipped, "
          "1 verified enrichment")


if __name__ == "__main__":
    run_tests()
