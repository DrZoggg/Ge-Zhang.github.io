import copy
import html
import json
import re
import tempfile
from pathlib import Path

import sync_common
from build_publications import paper_schema, render_paper_html
from site_common import PAPERS_DIR, load_site_config
from sync_common import load_master, merge_items, normalize_authors, publication_authors, save_master
from sync_crossref import crossref_author_names
from validate_site import element_texts, paper_json_ld_object


# Publisher-verified author positions supplied in the identity-closure contract.
VERIFIED_IDENTITIES = {
    '10.1002/ggn2.202500053': {'authors': ['Haonan Zhang', 'Ge Zhang', 'Chaoyang Yu', 'Ruhao Wu', 'Shiqian Zhang', 'Xufeng Huang', 'Yingxue Yuan', 'Yaxin Chen', 'Shaotong Pei', 'Ge Zhang'], 'positions': [10], 'year': 2026, 'slug': 'doi-10-1002-ggn2-202500053', 'date_parts': [2026, 3, 16], 'volume': '7', 'issue': '1', 'number': 'e00053'},
}


def assert_identity_record(publication, expected):
    assert publication['authors'] == expected['authors']
    assert publication_authors(publication) == expected['authors']
    assert publication['researcher_author_positions'] == expected['positions']
    assert publication['year'] == expected['year']


def assert_identity_schema(authors, expected, config):
    assert [a['name'] for a in authors] == expected['authors']
    for position, author in enumerate(authors, 1):
        if position in expected['positions']:
            assert author['@id'] == config['person_id']
            assert author['sameAs'] == f"https://orcid.org/{config['orcid']}"
        else:
            assert author == {'@type': 'Person', 'name': expected['authors'][position - 1]}


def assert_identity_csl(csl, expected):
    assert [a['literal'] for a in csl['author']] == expected['authors']
    assert csl['issued'] == {'date-parts': [expected['date_parts']]}
    assert (csl.get('volume'), csl.get('issue'), csl.get('number')) == (expected['volume'], expected['issue'], expected['number'])
    assert 'article-number' not in csl and 'page' not in csl


def reject_identity_fixture(callback):
    try:
        callback()
    except (AssertionError, ValueError):
        return
    raise AssertionError('Invalid publication identity fixture was accepted')


def run_verified_identity_tests():
    config = load_site_config()
    by_doi = {p.get('doi'): p for p in load_master()}
    negatives = 0
    for doi, expected in VERIFIED_IDENTITIES.items():
        publication = by_doi[doi]
        assert_identity_record(publication, expected)
        normalized = sync_common.normalize_item(publication)
        assert_identity_record(normalized, expected)
        # Exercise both ORCID- and Crossref-style collapsed incoming identities.
        incoming = {key: publication[key] for key in ('doi', 'title', 'journal', 'type', 'year')}
        incoming['authors'] = normalize_authors(expected['authors'])
        assert len(incoming['authors']) == len(expected['authors']) - 1
        assert 'researcher_author_positions' not in incoming
        incoming['year'] = 2026  # An incoming year cannot displace the verified citation year.
        for source in ('ORCID:isolated-fixture', 'Crossref:isolated-fixture'):
            merged, added, _, duplicates = merge_items([copy.deepcopy(publication)], [copy.deepcopy(incoming)], source)
            assert len(merged) == 1 and added == duplicates == 0
            assert_identity_record(merged[0], expected)
            with tempfile.TemporaryDirectory() as temporary:
                original_master = sync_common.MASTER
                try:
                    sync_common.MASTER = Path(temporary) / 'master.json'
                    save_master(merged)
                    assert_identity_record(load_master()[0], expected)
                finally:
                    sync_common.MASTER = original_master
        slug = expected['slug']
        page = (PAPERS_DIR / (slug + '.html')).read_text(encoding='utf-8')
        rendered_authors = [html.unescape(v) for v in re.findall(r'<meta name="citation_author" content="([^"]*)">', page)]
        assert rendered_authors == expected['authors']
        schema_authors = paper_json_ld_object(page, slug)['author']
        assert_identity_schema(schema_authors, expected, config)
        assert_identity_schema(paper_schema(publication, config['site_url'] + '/papers/' + slug + '.html', config)['author'], expected, config)
        citations = PAPERS_DIR.parent / 'citations'
        bib = (citations / (slug + '.bib')).read_text(encoding='utf-8')
        ris = (citations / (slug + '.ris')).read_text(encoding='utf-8')
        csl = json.loads((citations / (slug + '.csl.json')).read_text(encoding='utf-8'))
        assert re.search(r'^  author = \{(.*)\},$', bib, re.M).group(1).split(' and ') == expected['authors']
        assert [line[6:] for line in ris.splitlines() if line.startswith('AU  - ')] == expected['authors']
        assert f"year = {{{expected['year']}}}" in bib and f"PY  - {expected['year']}" in ris
        assert f"number = {{{expected['issue']}}}" in bib and f"eid = {{{expected['number']}}}" in bib
        assert f"IS  - {expected['issue']}" in ris and f"C7  - {expected['number']}" in ris
        assert_identity_csl(csl, expected)
        if doi == '10.1016/j.curpro.2025.100054':
            metadata = json.loads((PAPERS_DIR.parent / 'data/citation_metadata.json').read_text(encoding='utf-8'))['papers'][doi]
            assert 'publication_date' not in metadata and 'DA  - ' not in ris
            assert '<meta name="citation_publication_date" content="2025">' in page
            bad = copy.deepcopy(publication); bad['year'] = 2026
            reject_identity_fixture(lambda: assert_identity_record(bad, expected))
            bad_csl = copy.deepcopy(csl); bad_csl['issued'] = {'date-parts': [[2026]]}
            reject_identity_fixture(lambda: assert_identity_csl(bad_csl, expected))
            negatives += 2
        bad = copy.deepcopy(publication); bad['authors'].pop()
        reject_identity_fixture(lambda: assert_identity_record(bad, expected))
        bad_authors = copy.deepcopy(schema_authors)
        other = next(i for i, name in enumerate(expected['authors'], 1) if name == 'Ge Zhang' and i not in expected['positions'])
        bad_authors[other - 1].update({'@id': config['person_id'], 'sameAs': f"https://orcid.org/{config['orcid']}"})
        reject_identity_fixture(lambda: assert_identity_schema(bad_authors, expected, config))
        bad = copy.deepcopy(publication); bad['researcher_author_positions'] = [1] if expected['positions'] == [10] else [10]
        reject_identity_fixture(lambda: assert_identity_record(bad, expected))
        bad_csl = copy.deepcopy(csl); bad_csl['issue'] = expected['number']
        reject_identity_fixture(lambda: assert_identity_csl(bad_csl, expected))
        bad_csl = copy.deepcopy(csl); bad_csl['page'] = bad_csl.pop('number')
        reject_identity_fixture(lambda: assert_identity_csl(bad_csl, expected))
        negatives += 5
    print(f'VERIFIED IDENTITY TESTS PASS: {len(VERIFIED_IDENTITIES)} records; isolated ORCID/Crossref preservation; {negatives} negative fixtures')


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

    run_verified_identity_tests()
    print("AUTHOR METADATA TESTS PASS")


if __name__ == "__main__":
    run_tests()
