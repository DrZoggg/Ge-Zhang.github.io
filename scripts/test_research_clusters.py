"""Focused paired-paper cluster validation and rendering regression."""

import copy
import json

from build_publications import resolve_research_clusters
from site_common import PAPERS_DIR
from sync_common import ROOT


MEMBERS = {
    "10.1093/eurheartj/ehaf523": "doi-10-1093-eurheartj-ehaf523",
    "10.1172/jci194175": "doi-10-1172-jci194175",
}
ANCHOR = "research-cluster-kif13b-atherosclerosis"


def main():
    cluster = json.loads((ROOT / "data/research_clusters.json").read_text(encoding="utf-8"))
    assert cluster["version"] == 1
    assert list(cluster["clusters"]) == ["kif13b-atherosclerosis"]
    assert {member["doi"] for member in cluster["clusters"]["kif13b-atherosclerosis"]["members"]} == set(MEMBERS)
    contents = {
        slug: json.loads((ROOT / "data/deep_geo" / f"{slug}.json").read_text(encoding="utf-8"))
        for slug in MEMBERS.values()
    }
    public = {
        doi: {"doi": doi, "title": contents[slug]["display_title"],
              "paper_url": f"https://drgezhang.com/papers/{slug}.html"}
        for doi, slug in MEMBERS.items()
    }
    resolve_research_clusters(contents, public)
    for doi, slug in MEMBERS.items():
        page = (PAPERS_DIR / f"{slug}.html").read_text(encoding="utf-8")
        markdown = (PAPERS_DIR / f"{slug}.md").read_text(encoding="utf-8")
        assert page.count(f'id="{ANCHOR}"') == 1
        assert markdown.count(f'<a id="{ANCHOR}"></a>') == 1
        assert "KIF13B Atherosclerosis Evidence Network" in page and "KIF13B Atherosclerosis Evidence Network" in markdown
        for other_doi, other_slug in MEMBERS.items():
            url = f"https://drgezhang.com/papers/{other_slug}.html"
            assert url in page and url in markdown
            assert other_doi in page and other_doi in markdown
        for member in contents[slug]["_research_cluster"]["members"]:
            for ref in member["evidence_refs"]:
                member_content = contents[MEMBERS[member["doi"]]]
                assert ref in {finding["id"] for finding in member_content["key_findings"]}
    bad = copy.deepcopy(contents)
    del bad["doi-10-1172-jci194175"]
    try:
        resolve_research_clusters(bad, public)
    except ValueError:
        pass
    else:
        raise AssertionError("Missing cluster member accepted")
    print("RESEARCH CLUSTER TESTS PASS: paired canonical members, evidence refs and HTML/Markdown anchors")


if __name__ == "__main__":
    main()
