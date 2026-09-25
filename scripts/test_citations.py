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
PRIORITY_FIELDS = {
    "10.1038/s41467-024-50415-9": {
        "publication_date": "2024-08-08", "volume": "15", "issue": "1",
        "article_number": "6756", "eissn": "2041-1723",
        "pmid": "39117613", "pmcid": "PMC11310499",
    },
    "10.1038/s41698-026-01699-1": {
        "publication_date": "2026-09-16", "eissn": "2397-768X",
    },
    "10.1016/j.isci.2023.107587": {
        "publication_date": "2023-08-09", "volume": "26", "issue": "9",
        "article_number": "107587", "eissn": "2589-0042",
        "pmid": "37664595", "pmcid": "PMC10470306",
    },
    "10.1186/s12967-022-03795-9": {
        "publication_date": "2022-12-06", "volume": "20", "issue": "1",
        "article_number": "568", "eissn": "1479-5876",
        "pmid": "36474294", "pmcid": "PMC9724432",
    },
    "10.1002/ehf2.14003": {
        "publication_date": "2022-06-21", "volume": "9", "issue": "5",
        "first_page": "2937", "last_page": "2954", "eissn": "2055-5822",
        "pmid": "35727093", "pmcid": "PMC9349450", "publisher": "Wiley",
    },
    "10.1021/acs.jproteome.4c00522": {
        "publication_date": "2024-08-12", "volume": "23", "issue": "9",
        "first_page": "4139", "last_page": "4150", "issn": "1535-3893",
        "eissn": "1535-3907", "pmid": "39129220",
        "pmcid": "PMC11385702", "publisher": "American Chemical Society",
    },
    "10.1093/eurheartj/ehaf523": {
        "publication_date": "2025-07-25", "volume": "46", "issue": "45",
        "first_page": "4969", "last_page": "4984", "issn": "0195-668X",
        "eissn": "1522-9645", "pmid": "40709729",
        "publisher": "Oxford University Press",
    },
    "10.1172/jci194175": {
        "publication_date": "2026-01-29", "volume": "136", "issue": "6",
        "article_number": "e194175", "issn": "0021-9738",
        "eissn": "1558-8238", "pmid": "41609725",
        "pmcid": "PMC12987658",
        "publisher": "American Society for Clinical Investigation",
    },
    CIRCADIAN_DOI: {
        "publication_date": "2026-01-05", "volume": "2", "issue": "2",
        "first_page": "236", "last_page": "279", "issn": "2998-4963",
        "eissn": "2998-4971", "publisher": "Wiley",
    },
}


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
    assert set(enhancements) == set(PRIORITY_FIELDS)
    by_doi = {norm_doi(item.get("doi")): item for item in public if item.get("doi")}
    for doi, expected in PRIORITY_FIELDS.items():
        enrichment = enhancements[doi]
        assert {key: value for key, value in enrichment.items()
                if key != "verified_sources"} == expected
        assert enrichment["verified_sources"]
        publication = by_doi[doi]
        priority = citation_record(publication, enhancements, config["site_url"])
        assert priority["title"] == publication["title"]
        assert priority["authors"] == publication_authors(publication)
        assert priority["doi"] == doi
        slug = publication["slug"]
        markup = (PAPERS_DIR / f"{slug}.html").read_text(encoding="utf-8")
        assert meta_contents(markup, "citation_publication_date") == [
            expected["publication_date"].replace("-", "/")
        ]
        for key, tag in (
            ("volume", "citation_volume"), ("issue", "citation_issue"),
            ("article_number", "citation_article_number"),
            ("first_page", "citation_firstpage"), ("last_page", "citation_lastpage"),
            ("issn", "citation_issn"), ("eissn", "citation_eIssn"),
            ("pmid", "citation_pmid"), ("publisher", "citation_publisher"),
        ):
            assert meta_contents(markup, tag) == ([expected[key]] if key in expected else [])
        export = citation_files(priority)
        bib_text = (CITATIONS_DIR / export["bib"]).read_text(encoding="utf-8")
        ris_text = (CITATIONS_DIR / export["ris"]).read_text(encoding="utf-8")
        csl_data = json.loads((CITATIONS_DIR / export["csl"]).read_text(encoding="utf-8"))
        assert f"doi = {{{doi}}}" in bib_text and f"DO  - {doi}" in ris_text
        assert csl_data["DOI"] == doi and csl_data["title"] == priority["title"]
        assert [author["literal"] for author in csl_data["author"]] == priority["authors"]
        if "article_number" in expected:
            number = expected["article_number"]
            assert f"eid = {{{number}}}" in bib_text
            assert f"C7  - {number}" in ris_text
            assert csl_data["article-number"] == number
            assert "SP  - " not in ris_text and "EP  - " not in ris_text
        if "first_page" in expected:
            pages = f"{expected['first_page']}--{expected['last_page']}"
            assert f"pages = {{{pages}}}" in bib_text
            assert f"SP  - {expected['first_page']}" in ris_text
            assert f"EP  - {expected['last_page']}" in ris_text
            assert csl_data["page"] == pages.replace("--", "-")
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
          f"{len(enhancements)} verified enrichments")


if __name__ == "__main__":
    run_tests()
