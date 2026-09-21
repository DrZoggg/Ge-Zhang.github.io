import html
import re

from build_publications import paper_schema, render_paper_html
from site_common import load_site_config
from sync_common import merge_items
from sync_crossref import crossref_author_names


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

    print("AUTHOR METADATA TESTS PASS")


if __name__ == "__main__":
    run_tests()
