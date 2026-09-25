import html
import re
import tempfile
from pathlib import Path

import sync_common
from build_publications import paper_schema, render_paper_html
from site_common import PAPERS_DIR, load_site_config
from sync_common import load_master, merge_items, normalize_authors, publication_authors, save_master
from sync_crossref import crossref_author_names
from validate_site import element_texts, paper_json_ld_object


def run_tests():
    parsed = crossref_author_names(
        [
            {"given": " First ", "family": " Author "},
            {"name": "Study Group"},
            {"given": "First", "family": "Author"},
            {"given": "", "family": ""},
        ]
    )
    assert parsed == ["First Author", "Study Group"]

    existing = [{"title": "A", "doi": "10.1/test", "authors": ["Trusted Author"]}]
    incoming = [{"title": "A", "doi": "10.1/test", "authors": ["Weaker Author"]}]
    merged, _, _, _ = merge_items(existing, incoming, "Crossref:test")
    assert merged[0]["authors"] == ["Trusted Author"]

    config = load_site_config()
    publication = {
        "title": "Escaping test",
        "journal": "Test Journal",
        "year": 2026,
        "type": "Article",
        "doi": "10.1/test",
        "slug": "escaping-test",
        "authors": ["A & B", "Ge Zhang", "G. Zhang", 'Quoted "Name"'],
    }
    markup = render_paper_html(publication, config=config)
    citation_authors = [
        html.unescape(value)
        for value in re.findall(r'<meta name="citation_author" content="([^"]*)">', markup)
    ]
    assert citation_authors == publication["authors"]

    authors = paper_schema(publication, "https://drgezhang.com/papers/test.html", config)[
        "author"
    ]
    assert [author["name"] for author in authors] == publication["authors"]
    assert authors[1]["@id"] == config["person_id"]
    assert authors[1]["sameAs"] == f"https://orcid.org/{config['orcid']}"
    assert authors[0] == {"@type": "Person", "name": "A & B"}
    assert authors[2] == {"@type": "Person", "name": "G. Zhang"}
    assert authors[3] == {"@type": "Person", "name": 'Quoted "Name"'}

    without_authors = dict(publication)
    without_authors.pop("authors")
    markup = render_paper_html(without_authors, config=config)
    assert 'name="citation_author"' not in markup
    fallback = paper_schema(
        without_authors, "https://drgezhang.com/papers/test.html", config
    )["author"]
    assert fallback["@id"] == config["person_id"]

    target = next(item for item in load_master() if item.get("doi") == "10.1002/mdr2.70052")
    expected = [
        "Tian Zhang", "Ge Zhang", "Tian-Ding Liu", "Tianshu Gu", "Fengyi Yu",
        "Pengyuan Xu", "Wunan Mi", "Xuanjiang Zhao", "Qian Guo", "Honglin Zheng",
        "Taiqi Zhao", "Qiang Li", "Di Lu", "Mingxuan Duan", "Chaoyang Yu",
        "Ruhao Wu", "Shiqian Zhang", "Haonan Zhang", "Zeyu Wang",
        "Youyang Zheng", "Yan Xiao", "Zenglei Zhang", "Ge Zhang",
    ]
    assert target["authors"] == expected
    assert target["researcher_author_positions"] == [23]
    assert publication_authors(target) == expected
    assert normalize_authors(["Ge Zhang", "Ge Zhang"]) == ["Ge Zhang"]
    with tempfile.TemporaryDirectory() as temporary:
        original_master = sync_common.MASTER
        try:
            sync_common.MASTER = Path(temporary) / "master.json"
            save_master([target])
            assert load_master()[0]["authors"] == expected
            assert load_master()[0]["researcher_author_positions"] == [23]
        finally:
            sync_common.MASTER = original_master
    weaker = {"title": target["title"], "doi": target["doi"],
              "authors": ["Tian Zhang", "Ge Zhang"]}
    merged, _, _, _ = merge_items([target], [weaker], "Crossref:test")
    assert merged[0]["authors"] == expected
    assert merged[0]["researcher_author_positions"] == [23]

    page = (PAPERS_DIR / "doi-10-1002-mdr2-70052.html").read_text(encoding="utf-8")
    markdown = (PAPERS_DIR / "doi-10-1002-mdr2-70052.md").read_text(encoding="utf-8")
    assert element_texts(page, "li", {"class": "paper-geo-v2__author"}) == expected
    author_section = markdown.split("## Full Authors\n\n", 1)[1].split("\n\n## ", 1)[0]
    assert author_section.splitlines() == [
        f"{position}. {name}" for position, name in enumerate(expected, start=1)
    ]
    citation = [html.unescape(value) for value in re.findall(
        r'<meta name="citation_author" content="([^"]*)">', page
    )]
    assert citation == expected
    assert citation[1] == citation[22] == "Ge Zhang"
    schema_authors = paper_json_ld_object(page, "circadian review")["author"]
    assert [person["name"] for person in schema_authors] == expected
    assert schema_authors[1] == {"@type": "Person", "name": "Ge Zhang"}
    assert schema_authors[22]["@id"] == config["person_id"]
    assert schema_authors[22]["sameAs"] == f"https://orcid.org/{config['orcid']}"
    assert sum(person.get("@id") == config["person_id"] for person in schema_authors) == 1

    print("AUTHOR METADATA TESTS PASS")


if __name__ == "__main__":
    run_tests()
