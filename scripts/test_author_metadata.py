import copy
import html
import json
import re
import tempfile
from pathlib import Path

import sync_common
import limited_evidence
from build_publications import paper_schema, render_paper_html, render_paper_markdown
from citation_common import citation_files, citation_plain_text, citation_record, load_citation_metadata
from site_common import PAPERS_DIR, load_site_config
from sync_common import load_master, merge_items, normalize_authors, publication_authors, save_master
from sync_crossref import crossref_author_names
from validate_site import element_texts, paper_json_ld_object


# Publisher-verified author positions supplied in the identity-closure contract.
VERIFIED_IDENTITIES = {
    '10.1016/j.curpro.2025.100054': {'authors': ['Ge Zhang', 'Jiashen Xu', 'Zenglei Zhang', 'Chaoyang Yu', 'Kaisaierjiang Kadier', 'Di Lu', 'Mingxuan Duan', 'Ge Zhang'], 'positions': [1], 'year': 2025, 'slug': 'doi-10-1016-j-curpro-2025-100054', 'date_parts': [2025], 'volume': '22', 'issue': '5', 'number': '100054'},
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


def bibtex_author_names(bib):
    # G11 protects hyphenated name tokens with BibTeX groups, not CSL literals.
    value = re.search(r'^  author = \{(.*)\},$', bib, re.M).group(1)
    return re.sub(r'\{([^{}]*)\}', r'\1', value).split(' and ')


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
        assert bibtex_author_names(bib) == expected['authors']
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


def run_luad_affiliation_marker_test():
    """Only the verified name token is corrected; the author-version dispute stays open."""
    doi = "10.71321/fy14v342"
    expected = [
        "Ruhao Wu", "Kaisaierjiang Kadier", "Shuai Xu", "Peiyu Yuan",
        "Yu Yang", "Pengyuan Xu", "Xufeng Huang", "Shujing Zhou",
        "Song-Bin Guo", "Haonan Zhang", "Shiqian Zhang", "Chaoyang Yu",
        "Teng Li", "Ge Zhang",
    ]
    target = next(item for item in load_master() if item.get("doi") == doi)
    assert target["authors"] == publication_authors(target) == expected
    assert "researcher_author_positions" not in target
    # A stale incoming marker must not overwrite the existing verified author list.
    incoming = copy.deepcopy(target)
    incoming["authors"][1] = "Kaisaierjiang Kadier3"
    for source in ("ORCID:isolated-fixture", "Crossref:isolated-fixture"):
        merged, added, _, duplicates = merge_items([copy.deepcopy(target)], [incoming], source)
        assert added == duplicates == 0 and merged[0]["authors"] == expected
        assert "researcher_author_positions" not in merged[0]
    # This fix must not become a generic trailing-digit stripping rule.
    assert normalize_authors(["Kaisaierjiang Kadier3"]) == ["Kaisaierjiang Kadier3"]
    slug = target["slug"]
    page = (PAPERS_DIR / f"{slug}.html").read_text(encoding="utf-8")
    assert [html.unescape(v) for v in re.findall(r'<meta name="citation_author" content="([^"]*)">', page)] == expected
    config = load_site_config()
    assert_identity_schema(paper_json_ld_object(page, slug)["author"], {"authors": expected, "positions": [14]}, config)
    citation_dir = PAPERS_DIR.parent / "citations"
    bib = (citation_dir / f"{slug}.bib").read_text(encoding="utf-8")
    ris = (citation_dir / f"{slug}.ris").read_text(encoding="utf-8")
    csl = json.loads((citation_dir / f"{slug}.csl.json").read_text(encoding="utf-8"))
    assert bibtex_author_names(bib) == expected
    assert [line[6:] for line in ris.splitlines() if line.startswith("AU  - ")] == expected
    assert [author["literal"] for author in csl["author"]] == expected
    assert csl["DOI"] == doi
    print("LUAD NAME FIXTURE PASS: 14 positions preserved; site Person remains at 14; stale incoming marker rejected without external sync")


def run_retinal_publisher_identity_test():
    """Keep both publisher-named Ge Zhang authors without inferring a site identity."""
    doi = '10.3980/j.issn.1672-5123.2020.12.13'
    expected = {
        'authors': ['Ge Zhang', 'Han Zhu', 'Jing-Wen Zhang', 'Yu-Di Xu', 'Ming-Xuan Duan', 'Ge Zhang'],
        'positions': [], 'year': 2020,
    }
    target = next(item for item in load_master() if item.get('doi') == doi)
    assert_identity_record(target, expected)
    assert target['journal'] == 'International Eye Science'
    # Ordinary incoming author deduplication and the old journal cannot displace
    # this complete byline or its unresolved owner mapping, including after save/load.
    incoming = {key: target[key] for key in ('doi', 'title', 'type', 'year')}
    incoming.update(authors=normalize_authors(expected['authors']), journal='International Journal of Ophthalmology')
    assert len(incoming['authors']) == 5
    for source in ('ORCID:isolated-fixture', 'Crossref:isolated-fixture'):
        stale = {**incoming, 'authors': expected['authors'], 'researcher_author_positions': [1]}
        for candidate in (incoming, stale):
            merged, added, _, duplicates = merge_items([copy.deepcopy(target)], [copy.deepcopy(candidate)], source)
            assert added == duplicates == 0 and len(merged) == 1
            assert_identity_record(merged[0], expected)
            assert merged[0]['journal'] == target['journal']
            with tempfile.TemporaryDirectory() as temporary:
                original_master = sync_common.MASTER
                try:
                    sync_common.MASTER = Path(temporary) / 'master.json'
                    save_master(merged)
                    assert_identity_record(load_master()[0], expected)
                    assert load_master()[0]['journal'] == target['journal']
                finally:
                    sync_common.MASTER = original_master
    slug = target['slug']
    page = (PAPERS_DIR / f'{slug}.html').read_text(encoding='utf-8')
    assert [html.unescape(v) for v in re.findall(r'<meta name="citation_author" content="([^"]*)">', page)] == expected['authors']
    schema_authors = paper_json_ld_object(page, slug)['author']
    config = load_site_config()
    assert_identity_schema(schema_authors, expected, config)
    assert all(set(person) == {'@type', 'name'} for person in schema_authors)
    markdown = (PAPERS_DIR / f'{slug}.md').read_text(encoding='utf-8')
    assert f"Site maintainer: {config['researcher_name']}\n" in markdown
    assert f"Site maintainer ORCID: https://orcid.org/{config['orcid']}\n" in markdown
    assert f"Canonical site maintainer: {config['person_id']}\n" in markdown
    assert '## ORCID work-record provenance\n' in markdown
    assert 'the identity mapping between individual authors and the site maintainer remains unverified.' in markdown
    assert 'ORCID identity anchor:' not in markdown and 'Canonical researcher:' not in markdown
    assert 'Site maintainer: Ge Zhang' in page and 'site maintainer ORCID' in page
    assert 'not replace the publisher version or assert a complete author list' not in page
    # Only [] changes these role labels; omitted and verified positions retain the old text.
    for positions in (None, [1]):
        fixture = copy.deepcopy(target)
        if positions is None:
            fixture.pop('researcher_author_positions')
        else:
            fixture['researcher_author_positions'] = positions
        legacy = render_paper_markdown(fixture, config=config)
        assert f"Researcher: {config['researcher_name']}\n" in legacy
        assert 'ORCID identity anchor:' in legacy and 'Canonical researcher:' in legacy
        assert '## About this record\n' in legacy and 'via ORCID;' in legacy
        assert 'Site maintainer:' not in legacy
        assert 'Author-controlled academic record for Ge Zhang' in render_paper_html(fixture, config=config)
    citations = PAPERS_DIR.parent / 'citations'
    bib = (citations / f'{slug}.bib').read_text(encoding='utf-8')
    ris = (citations / f'{slug}.ris').read_text(encoding='utf-8')
    csl = json.loads((citations / f'{slug}.csl.json').read_text(encoding='utf-8'))
    assert bibtex_author_names(bib) == expected['authors']
    assert [line[6:] for line in ris.splitlines() if line.startswith('AU  - ')] == expected['authors']
    assert [author['literal'] for author in csl['author']] == expected['authors']
    assert csl['container-title'] == target['journal'] and csl['DOI'] == doi
    assert csl['issued'] == {'date-parts': [[2020]]}
    assert (csl['volume'], csl['issue'], csl['page']) == ('20', '12', '2079-2082')
    assert 'number' not in csl and 'article-number' not in csl
    assert 'pages = {2079--2082}' in bib and 'journal = {International Eye Science}' in bib
    assert 'SP  - 2079' in ris and 'EP  - 2082' in ris and 'DA  - ' not in ris
    metadata = json.loads((PAPERS_DIR.parent / 'data/citation_metadata.json').read_text(encoding='utf-8'))['papers'][doi]
    assert metadata['journal_abbrev'] == 'Int Eye Sci' and metadata['issn'] == '1672-5123'
    assert 'publication_date' not in metadata
    bad = copy.deepcopy(target); bad['authors'].pop()
    reject_identity_fixture(lambda: assert_identity_record(bad, expected))
    for position in (0, 5):
        bad_authors = copy.deepcopy(schema_authors)
        bad_authors[position].update({'@id': config['person_id'], 'sameAs': f"https://orcid.org/{config['orcid']}"})
        reject_identity_fixture(lambda: assert_identity_schema(bad_authors, expected, config))
        bad = copy.deepcopy(target); bad['researcher_author_positions'] = [position + 1]
        reject_identity_fixture(lambda: assert_identity_record(bad, expected))
    print('RETINAL IDENTITY TEST PASS: six ordered authors; no verified site Person; ORCID/Crossref preservation; year-only paginated citation; 5 negative fixtures')


def run_explicit_researcher_positions_contract_tests():
    """An explicit empty list keeps the complete byline without a guessed owner."""
    fixture = {
        'title': 'Explicit identity fixture', 'doi': '10.1/identity-fixture',
        'authors': ['Ge Zhang', 'Other Author', 'Ge Zhang'],
        'researcher_author_positions': [],
    }
    config = load_site_config()
    for positions in ([], [1], [3], [1, 3]):
        item = {**fixture, 'researcher_author_positions': positions}
        assert publication_authors(item) == fixture['authors']
        assert sync_common.normalize_item(item)['researcher_author_positions'] == positions
        schema = paper_schema(item, 'https://drgezhang.com/papers/identity-fixture.html', config)['author']
        assert_identity_schema(schema, {'authors': fixture['authors'], 'positions': positions}, config)
        old = {**item, 'sync_fixture_note': ''}
        incoming = {**item, 'researcher_author_positions': [3], 'sync_fixture_note': 'filled'}
        merged, added, _, duplicates = merge_items([old], [incoming], 'Crossref:isolated-fixture')
        assert added == duplicates == 0 and merged[0]['researcher_author_positions'] == positions
        assert merged[0]['sync_fixture_note'] == 'filled'  # Other empty-field backfill is unchanged.
    invalid = ('1', '', 1, True, False, {}, (), [0], [-1], [4], [1, 1], [True], [1.0], ['1'], [None])
    for positions in invalid:
        reject_identity_fixture(lambda: publication_authors({**fixture, 'researcher_author_positions': positions}))
    reject_identity_fixture(lambda: sync_common.normalize_item({'researcher_author_positions': []}))
    for authors in ([], None, ''):
        reject_identity_fixture(lambda: publication_authors({**fixture, 'authors': authors}))
    print(f'EXPLICIT POSITIONS CONTRACT PASS: empty and 3 nonempty lists; {len(invalid) + 4} invalid type/range/duplicate/missing-author fixtures rejected')


def run_limited_markdown_citation_tests():
    """Limited scientific notes keep their body while exposing existing citations."""
    config = load_site_config()
    public = json.loads((PAPERS_DIR.parent / 'publications.json').read_text(encoding='utf-8'))
    metadata = load_citation_metadata(public)
    notes = limited_evidence.load(public)
    by_doi = {p.get('doi'): p for p in public}
    checked = 0
    for doi, note in notes.items():
        publication = by_doi[doi]
        citation = citation_record(publication, metadata, config['site_url'])
        markdown = (PAPERS_DIR / f"{publication['slug']}.md").read_text(encoding='utf-8')
        assert markdown.count(limited_evidence.render_markdown(note)) == 1
        if citation is None:
            assert '## Cite this paper\n' not in markdown
            continue
        authors = markdown.split('## Full Authors\n\n', 1)[1].split('\n\n## ', 1)[0]
        assert authors.splitlines() == [f'{i}. {name}' for i, name in enumerate(publication_authors(publication), 1)]
        assert markdown.count('## Cite this paper\n') == 1
        assert citation_plain_text(citation) in markdown
        for name in citation_files(citation).values():
            assert f"{config['site_url']}/citations/{name}" in markdown
        checked += 1
    # Missing metadata must still suppress citations; no guessed author list.
    target = by_doi['10.3980/j.issn.1672-5123.2020.12.13']
    missing = copy.deepcopy(target)
    missing.pop('authors'); missing.pop('researcher_author_positions')
    assert citation_record(missing, metadata, config['site_url']) is None
    markdown = render_paper_markdown(missing, config=config, limited_note=notes[target['doi']])
    assert '## Full Authors\n' not in markdown and '## Cite this paper\n' not in markdown
    target_note = notes[target['doi']]
    assert 'remains unresolved' not in target_note['scope']
    assert not any('corrections remain on hold' in limit for limit in target_note['limitations'])
    assert 'no unique ORCID or individual-identifier mapping' in target_note['sections'][-1]['text']
    assert 'both remain name-only authors' in target_note['sections'][-1]['text']
    print(f'LIMITED MARKDOWN CITATION TESTS PASS: {checked} ordered author lists and citation links; scientific note blocks preserved; missing-author fail closed')


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
    run_luad_affiliation_marker_test()
    run_retinal_publisher_identity_test()
    run_explicit_researcher_positions_contract_tests()
    run_limited_markdown_citation_tests()
    print("AUTHOR METADATA TESTS PASS")


if __name__ == "__main__":
    run_tests()
