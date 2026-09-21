import copy
import json

from build_publications import (
    flatten_concepts,
    load_deep_content,
    render_paper_html,
    render_paper_markdown,
    resolve_related_papers,
    validate_deep_v2_content,
)
from site_common import (
    PAPERS_DIR,
    controller_token,
    index_master,
    load_deep_geo,
    load_site_config,
)
from sync_common import is_withdrawn, load_master, norm_doi
from validate_site import (
    AIHFLEVEL_DOI,
    paper_json_ld_object,
    validate_aihflevel_v2,
)


def expect_value_error(callback, expected):
    try:
        callback()
    except ValueError as exc:
        assert expected.casefold() in str(exc).casefold(), str(exc)
    else:
        raise AssertionError(f"Expected ValueError containing {expected!r}.")


def run_tests():
    config = load_site_config()
    master = load_master()
    public = [item for item in master if not is_withdrawn(item)]
    master_by_token = index_master(master)
    public_by_doi = {
        norm_doi(item.get("doi")): item
        for item in public
        if norm_doi(item.get("doi"))
    }

    v1_count = 0
    v2_items = []
    for entry in load_deep_geo():
        publication = master_by_token[controller_token(entry)]
        content = load_deep_content(publication)
        if content["version"] == 2:
            v2_items.append((publication, content))
            continue
        v1_count += 1
        assert content["version"] == 1
        assert render_paper_html(
            publication,
            config=config,
            deep_content=content,
            public_by_doi=public_by_doi,
        ) == (PAPERS_DIR / f"{publication['slug']}.html").read_text(encoding="utf-8")
        assert render_paper_markdown(
            publication,
            config=config,
            deep_content=content,
            public_by_doi=public_by_doi,
        ) == (PAPERS_DIR / f"{publication['slug']}.md").read_text(encoding="utf-8")

    assert v1_count == len(load_deep_geo()) - 1
    assert len(v2_items) == 1
    publication, content = v2_items[0]
    assert norm_doi(publication["doi"]) == AIHFLEVEL_DOI
    validate_deep_v2_content(content, "AIHFLevel test fixture")

    related = resolve_related_papers(content, public_by_doi, config["site_url"])
    assert [item["doi"] for item in related] == [
        "10.2147/cia.s462542",
        "10.1002/ggn2.202500053",
    ]
    assert [item["url"] for item in related] == [
        "https://drgezhang.com/papers/doi-10-2147-cia-s462542.html",
        "https://drgezhang.com/papers/doi-10-1002-ggn2-202500053.html",
    ]

    page = render_paper_html(
        publication,
        config=config,
        deep_content=content,
        public_by_doi=public_by_doi,
    )
    markdown = render_paper_markdown(
        publication,
        config=config,
        deep_content=content,
        public_by_doi=public_by_doi,
    )
    schema = paper_json_ld_object(page, "AIHFLevel test page")
    validate_aihflevel_v2(
        content,
        publication,
        page,
        markdown,
        schema,
        public_by_doi,
        config,
    )
    assert schema["description"] == content["author_summary"]
    assert schema["keywords"] == flatten_concepts(content)
    assert page == (PAPERS_DIR / "aihflevel.html").read_text(encoding="utf-8")
    assert markdown == (PAPERS_DIR / "aihflevel.md").read_text(encoding="utf-8")

    bad_ref = copy.deepcopy(content)
    bad_ref["qa"][0]["evidence_refs"] = ["KF999"]
    expect_value_error(
        lambda: validate_deep_v2_content(bad_ref, "bad Q&A"),
        "real finding IDs",
    )

    bad_hierarchy = copy.deepcopy(content)
    bad_hierarchy["study_profile"]["cohorts"][0]["n"] = 499
    expect_value_error(
        lambda: validate_deep_v2_content(bad_hierarchy, "bad hierarchy"),
        "child counts",
    )

    bad_finding = copy.deepcopy(content)
    bad_finding["key_findings"][0]["metric"] = "average C-index"
    expect_value_error(
        lambda: validate_deep_v2_content(bad_finding, "bad finding"),
        "normalized V2 fields",
    )

    bad_provenance = copy.deepcopy(content)
    bad_provenance["provenance"]["publisher_url"] = "http://example.org/paper"
    expect_value_error(
        lambda: validate_deep_v2_content(bad_provenance, "bad provenance"),
        "HTTPS URL",
    )

    bad_related = copy.deepcopy(content)
    bad_related["related_papers"][0]["doi"] = "10.9999/not-public"
    expect_value_error(
        lambda: resolve_related_papers(
            bad_related, public_by_doi, config["site_url"]
        ),
        "does not resolve",
    )

    print("PAPER GEO V2 TESTS PASS")
    print(json.dumps({"v1_pages": v1_count, "v2_pages": len(v2_items)}, indent=2))


if __name__ == "__main__":
    run_tests()
