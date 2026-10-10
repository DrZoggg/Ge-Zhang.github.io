"""Specific-letter identity and citation compatibility; no site build or writes."""

import copy
import json

from build_publications import render_paper_html, render_paper_markdown, schema_type
from citation_common import (
    citation_record, citation_skip_reason, load_citation_metadata,
    render_bibtex, render_csl_json, render_ris,
)
from site_common import load_site_config
from sync_common import load_master, merge_items
from validate_site import meta_contents, paper_json_ld_object


DOI = "10.1056/nejmc2518964"
AUTHORS = ["Mengyao Li", "Ge Zhang", "Xiaozhu Liu"]


def run_tests():
    master = load_master()
    target = next(item for item in master if item.get("doi") == DOI)
    config = load_site_config()
    enhancement = load_citation_metadata(master)
    assert target["title"] == "Aspirin after PCI in Acute Coronary Syndromes"
    assert target["slug"] == "doi-10-1056-nejmc2518964"
    assert target["url"] == f"https://doi.org/{DOI}"
    assert target["journal"] == "New England Journal of Medicine"
    assert target["type"] == "Letter" and target["authors"] == AUTHORS
    assert not citation_skip_reason(target)
    assert schema_type(target) == "ScholarlyArticle"
    record = citation_record(target, enhancement, config["site_url"])
    assert record["publication_date"] == "2026-03-05"
    assert (record["volume"], record["issue"], record["first_page"], record["last_page"]) == (
        "394", "10", "1035", "1036"
    )
    # The publisher's parent DOI spans 1035-1037; the specific PubMed letter ends at 1036.
    assert record["pmid"] == "41780015" and record["authors"] == AUTHORS
    markup = render_paper_html(target, config=config, citation_data=record)
    markdown = render_paper_markdown(target, config=config)
    assert meta_contents(markup, "citation_author") == AUTHORS
    assert meta_contents(markup, "citation_journal_title") == [target["journal"]]
    for tag, value in (
        ("citation_doi", DOI), ("citation_date", "2026/03/05"),
        ("citation_volume", "394"), ("citation_issue", "10"),
        ("citation_firstpage", "1035"), ("citation_lastpage", "1036"),
        ("citation_pmid", "41780015"),
    ):
        assert meta_contents(markup, tag) == [value]
    schema = paper_json_ld_object(markup, "NEJM specific letter")
    assert schema["@type"] == "ScholarlyArticle"
    assert schema["isPartOf"]["name"] == target["journal"]
    assert [person["name"] for person in schema["author"]] == AUTHORS
    assert schema["author"][1]["@id"] == config["person_id"]
    assert schema["identifier"]["value"] == DOI
    assert schema["url"] == record["canonical_url"]
    assert 'Letter · 2026' in markup and 'Type: Letter' in markdown
    assert all(author in markdown for author in AUTHORS)
    bib, ris, csl = render_bibtex(record), render_ris(record), json.loads(render_csl_json(record))
    assert bib.startswith("@article{") and "pages = {1035--1036}" in bib
    assert " and ".join(AUTHORS) in bib
    assert ris.startswith("TY  - JOUR")
    assert [line[6:] for line in ris.splitlines() if line.startswith("AU  - ")] == AUTHORS
    assert "EP  - 1036" in ris and "EP  - 1037" not in ris
    assert csl["type"] == "article-journal" and csl["page"] == "1035-1036"
    assert [author["literal"] for author in csl["author"]] == AUTHORS
    assert csl["issued"]["date-parts"] == [[2026, 3, 5]]
    # Incomplete letters remain ineligible and preprints retain their existing format.
    incomplete = copy.deepcopy(target)
    incomplete.pop("authors")
    assert citation_record(incomplete, enhancement, config["site_url"]) is None
    preprint = copy.deepcopy(record)
    preprint["type"] = "Preprint"
    assert render_bibtex(preprint).startswith("@misc{")
    assert render_ris(preprint).startswith("TY  - GEN")
    assert json.loads(render_csl_json(preprint))["type"] == "manuscript"
    # Automatic upstream enrichment must not replace verified letter identity with parent metadata.
    parent = {"doi": DOI, "title": target["title"], "year": 2026, "type": "Article",
              "journal": "The New-England Medical Review and Journal",
              "authors": ["Parent page author"]}
    merged, *_ = merge_items([target], [parent], "Crossref:test")
    assert merged[0]["authors"] == AUTHORS and merged[0]["type"] == "Letter"
    assert merged[0]["journal"] == target["journal"] and merged[0]["slug"] == target["slug"]
    print("NEJM CORRESPONDENCE TESTS PASS")


if __name__ == "__main__":
    run_tests()
