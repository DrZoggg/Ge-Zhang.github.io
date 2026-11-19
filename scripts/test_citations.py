"""Focused citation metadata, export, and Circadian Review regression checks."""

import copy
import hashlib
import json
import re
import tempfile
from pathlib import Path

from citation_common import (
    CITATIONS_DIR,
    citation_files,
    citation_record,
    citation_skip_reason,
    load_citation_metadata,
    render_csl_json,
    render_bibtex,
    render_ris,
)
from site_common import PAPERS_DIR, load_site_config
from sync_common import is_withdrawn, load_master, norm_doi, publication_authors
from official_abstracts import abstract_text, load_official_abstracts
from validate_site import json_ld_object, meta_contents, validate_citations


CIRCADIAN_DOI = "10.1002/mdr2.70052"
VERIFIED_RIS_LOCATORS = {
    "10.1136/jitc-2024-010787": "e010787",
    "10.1371/journal.pone.0346326": "e0346326",
    "10.1016/j.intimp.2024.112574": "112574",
    "10.1016/j.canlet.2024.217079": "217079",
    "10.1038/s41598-025-98859-3": "15916",
    "10.1038/s41467-024-50415-9": "6756",
    "10.1038/s41598-024-65236-5": "14155",
    "10.1155/humu/5591097": "5591097",
    "10.1186/s12931-024-02978-w": "365",
    "10.1186/s12915-025-02400-x": "280",
    "10.1186/s12967-022-03795-9": "568",
}
PRIORITY_FIELDS = {
    "10.1371/journal.pone.0346326": {
        "publication_date": "2026-04-03", "journal_abbrev": "PLoS One",
        "volume": "21", "issue": "4", "article_number": "e0346326",
        "pmid": "41931483", "pmcid": "PMC13048407",
    },
    "10.1038/s41598-025-98859-3": {
        "publication_date": "2025-05-07", "journal_abbrev": "Sci Rep",
        "volume": "15", "issue": "1", "article_number": "15916",
        "pmid": "40335605", "pmcid": "PMC12059082",
    },
    "10.1186/s12931-024-02978-w": {
        "volume": "25", "issue": "1", "article_number": "365",
    },
    "10.1155/humu/5591097": {
        "volume": "2026", "article_number": "5591097",
    },
    "10.1016/j.canlet.2024.217079": {
        "publication_date": "2024-08-28", "online_publication_date": "2024-06-25",
        "journal_abbrev": "Cancer Lett", "volume": "598", "article_number": "217079",
    },
    "10.2147/jir.s495784": {
        "publication_date": "2025-02-22", "journal_abbrev": "J Inflamm Res",
        "volume": "18", "first_page": "2629", "last_page": "2646",
    },
    "10.1136/jitc-2024-010787": {
        "volume": "13", "issue": "2", "article_number": "e010787",
    },
    "10.1016/j.intimp.2024.112574": {
        "volume": "138", "article_number": "112574",
    },
    "10.14283/jpad.2024.161": {
        "volume": "11", "issue": "6", "first_page": "1721", "last_page": "1733",
    },
    "10.3980/j.issn.1672-5123.2020.12.13": {
        "journal_abbrev": "Int Eye Sci", "issn": "1672-5123",
        "volume": "20", "issue": "12", "first_page": "2079", "last_page": "2082",
    },
    "10.1126/science.aek9583": {
        "publication_date": "2026-10-01", "volume": "394", "issue": "6819",
        "first_page": "38", "last_page": "39", "pmid": "42821669",
    },
    "10.1002/mdr2.70073": {
        "online_publication_date": "2026-06-03", "volume": "2", "issue": "3",
        "first_page": "460", "last_page": "472",
    },
    "10.1016/j.medd.2026.100004": {
        "publication_date": "2026-09-22", "article_number": "100004",
        "issn": "3117-9282", "publisher": "Elsevier BV",
    },
    "10.1016/j.colsurfb.2026.116261": {
        "online_publication_date": "2026-10-15", "volume": "270",
        "article_number": "116261", "publisher": "Elsevier BV", "pmid": "42896257",
    },
    "10.1016/j.gendis.2026.102480": {
        "online_publication_date": "2026-09-18", "article_number": "102480",
    },
    "10.1177/00368504261499186": {
        "online_publication_date": "2026-10-18", "publication_date": "2026-10-18",
        "volume": "109", "issue": "4", "article_number": "00368504261499186",
        "publisher": "SAGE Publications", "pmid": "42893432",
    },
    "10.1056/nejmc2518964": {
        "publication_date": "2026-03-05", "journal_abbrev": "N Engl J Med",
        "volume": "394", "issue": "10", "first_page": "1035", "last_page": "1036",
        "issn": "0028-4793", "eissn": "1533-4406",
        "publisher": "Massachusetts Medical Society", "pmid": "41780015",
    },
    '10.1016/j.curpro.2025.100054': {'volume': '22', 'issue': '5', 'article_number': '100054'},
    '10.1002/ggn2.202500053': {'publication_date': '2026-03-16', 'volume': '7', 'issue': '1', 'article_number': 'e00053', 'eissn': '2641-6573', 'pmid': '42016906', 'pmcid': 'PMC13093795'},
    '10.18632/aging.205564': {'publication_date': '2024-02-16', 'volume': '16', 'issue': '4', 'first_page': '3856', 'last_page': '3879', 'eissn': '1945-4589', 'pmid': '38372705', 'pmcid': 'PMC10929837'},
    '10.1016/j.ejphar.2023.175569': {'publication_date': '2023-02-03', 'volume': '943', 'article_number': '175569', 'pmid': '36740037'},
    '10.1007/s11426-026-3629-x': {'publication_date': '2026-09-15'},
    '10.3389/fcvm.2025.1724572': {'publication_date': '2026-01-05', 'volume': '12', 'article_number': '1724572', 'pmid': '41561117', 'pmcid': 'PMC12813168'},
    '10.3389/fpubh.2025.1521372': {'publication_date': '2025-03-26', 'volume': '13', 'article_number': '1521372', 'pmid': '40206179', 'pmcid': 'PMC11979105'},
    '10.3389/fonc.2021.659217': {'publication_date': '2021-05-03', 'volume': '11', 'article_number': '659217', 'pmid': '34012920', 'pmcid': 'PMC8126718'},

    "10.1038/s41598-024-65236-5": {"publication_date":"2024-06-19","volume":"14","issue":"1","article_number":"14155","eissn":"2045-2322","pmid":"38898215","pmcid":"PMC11187219"},
    "10.1016/j.joim.2025.06.003": {"publication_date":"2025-06-14","volume":"23","issue":"4","first_page":"445","last_page":"456","pmid":"40581550"},
    "10.1002/mdr2.70004": {"publication_date":"2025-04-29","volume":"1","issue":"1","first_page":"10","last_page":"31","issn":"2998-4963","eissn":"2998-4971","publisher":"Wiley"},
    "10.1111/jcmm.17789": {"publication_date":"2023-05-27","volume":"27","issue":"14","first_page":"1988","last_page":"2003","issn":"1582-1838","eissn":"1582-4934","publisher":"Wiley","pmid":"37243441","pmcid":"PMC10339102"},
    "10.1111/jcmm.70258": {"publication_date":"2024-12-24","volume":"28","issue":"24","article_number":"e70258","issn":"1582-1838","eissn":"1582-4934","publisher":"Wiley","pmid":"39719688","pmcid":"PMC11668728"},
    "10.1111/jcmm.70725": {"publication_date":"2025-08-06","volume":"29","issue":"15","article_number":"e70725","issn":"1582-1838","eissn":"1582-4934","publisher":"Wiley","pmid":"40770945","pmcid":"PMC12328994"},
    "10.2147/ijn.s522157": {"publication_date":"2025-07-28","volume":"20","first_page":"9407","last_page":"9425","eissn":"1178-2013","publisher":"Dove Medical Press","pmid":"40755464","pmcid":"PMC12315914"},
    "10.1200/po.24.00089": {"publication_date":"2024-10-21","volume":"8","article_number":"e2400089","eissn":"2473-4284","pmid":"39432882","publisher":"American Society of Clinical Oncology"},
    "10.1186/s12915-025-02400-x": {"publication_date":"2025-09-26","volume":"23","issue":"1","article_number":"280","eissn":"1741-7007","pmid":"41013440","pmcid":"PMC12465141","publisher":"BioMed Central"},
    "10.1136/jitc-2024-010127": {"publication_date":"2025-01-07","volume":"13","issue":"1","article_number":"e010127","eissn":"2051-1426","pmid":"39773567","pmcid":"PMC11749606","publisher":"BMJ"},
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


def test_locator_and_unicode_edges():
    # Test-only metadata: independent pagination/e-location, never fake pages.
    base = dict(id='synthetic-edge', type='Article', title='Synthetic UTF-8 α test',
                authors=['Élodie Müller', '张格'] + [f'Author {i}' for i in range(30)],
                journal='Synthetic Journal', year=2026, publication_date='2026-01-02',
                doi='10.9999/synthetic-edge', doi_url='https://doi.org/10.9999/synthetic-edge',
                volume='7', issue='2')
    for pages, number in [(False, True), (True, False), (True, True), (False, False)]:
        record = dict(base)
        if pages: record.update(first_page='1', last_page='9')
        if number: record['article_number'] = 'e42'
        bib, ris = render_bibtex(record), render_ris(record)
        csl = json.loads(render_csl_json(record))
        assert ('pages = {1--9}' in bib) == pages
        assert ('eid = {e42}' in bib) == number
        assert ('SP  - 1' in ris and 'EP  - 9' in ris) == pages
        assert ('C7  - e42' in ris) == number
        assert csl.get('page') == ('1-9' if pages else None)
        assert csl.get('number') == ('e42' if number else None)
        assert csl['issue'] == '2' and csl['issued']['date-parts'] == [[2026, 1, 2]]
        assert csl['DOI'] == record['doi'] and csl['title'] == record['title']
        assert [a['literal'] for a in csl['author']] == record['authors']
        assert [line[6:] for line in ris.splitlines() if line.startswith('AU  - ')] == record['authors']
        assert ' and '.join(record['authors']) in bib
        for text in (bib, ris, render_csl_json(record)): assert text.encode('utf-8').decode('utf-8') == text


def test_bibtex_hyphenated_names():
    # Citation.js imported ungrouped Ya-chen Hou as particle=chen/family=Ya-Hou.
    # Preserve the verified name tokens instead of guessing new given/family data.
    record = dict(id='synthetic-name-encoding', type='Article', title='Name encoding fixture',
                  authors=['Ya-chen Hou', 'Anne Smith-Jones', 'Ge Zhang',
                           'Élodie Müller', '张格', r'A-B C&D_%#{Q}\R'],
                  journal='Synthetic Journal', year=2026,
                  doi='10.9999/name-encoding', doi_url='https://doi.org/10.9999/name-encoding')
    original = copy.deepcopy(record)
    bib = render_bibtex(record)
    assert ('author = {{Ya-chen} Hou and Anne {Smith-Jones} and Ge Zhang and '
            'Élodie Müller and 张格 and {A-B} C\\&D\\_\\%\\#\\{Q\\}\\textbackslash{}R}') in bib
    assert r'\{Ya-chen\}' not in bib  # Grouping must not be escaped as literal braces.
    assert record == original
    assert json.loads(render_csl_json(record))['author'] == [
        {'literal': name} for name in record['authors']
    ]
    assert [line[6:] for line in render_ris(record).splitlines()
            if line.startswith('AU  - ')] == record['authors']


def run_tests():
    test_locator_and_unicode_edges()
    test_bibtex_hyphenated_names()
    master = load_master()
    public = [item for item in master if not is_withdrawn(item)]
    withdrawn = [item for item in master if is_withdrawn(item)]
    config = load_site_config()
    enhancements = load_citation_metadata(public)
    test_verified_source_handoffs(public, enhancements, config)
    official_abstracts = load_official_abstracts(public)
    test_existing_abstract_source_exports(public, enhancements, config, official_abstracts)
    # These two source handoffs have their own abstract/PDF contract below.
    assert set(enhancements) == set(PRIORITY_FIELDS) | {"10.1097/re9.0000000000000037", "10.1002/ctm2.70900"}
    by_doi = {norm_doi(item.get("doi")): item for item in public if item.get("doi")}
    for doi, expected in PRIORITY_FIELDS.items():
        enrichment = enhancements[doi]
        assert {key: value for key, value in enrichment.items()
                if key not in {"verified_sources", "ris_authors", "ris_article_locator", "official_abstract"}} == expected
        assert enrichment["verified_sources"]
        publication = by_doi[doi]
        priority = citation_record(publication, enhancements, config["site_url"], official_abstracts.get(doi))
        assert priority["title"] == publication["title"]
        assert priority["authors"] == publication_authors(publication)
        assert priority["doi"] == doi
        slug = publication["slug"]
        markup = (PAPERS_DIR / f"{slug}.html").read_text(encoding="utf-8")
        assert meta_contents(markup, "citation_publication_date") == [
            expected.get("publication_date", str(publication["year"])).replace("-", "/")
        ]
        for key, tag in (
            ("volume", "citation_volume"), ("issue", "citation_issue"),
            ("article_number", "citation_article_number"),
            ("first_page", "citation_firstpage"), ("last_page", "citation_lastpage"),
            ("issn", "citation_issn"), ("eissn", "citation_eIssn"),
            ("pmid", "citation_pmid"), ("publisher", "citation_publisher"),
        ):
            value = expected.get(key) or (expected.get('eissn') if key == 'issn' else None)
            assert meta_contents(markup, tag) == ([value] if value else [])
        export = citation_files(priority)
        bib_text = (CITATIONS_DIR / export["bib"]).read_text(encoding="utf-8")
        ris_text = (CITATIONS_DIR / export["ris"]).read_text(encoding="utf-8")
        csl_data = json.loads((CITATIONS_DIR / export["csl"]).read_text(encoding="utf-8"))
        assert f"doi = {{{doi}}}" in bib_text and f"DO  - {doi}" in ris_text
        ris_names = [line[6:] for line in ris_text.splitlines() if line.startswith("AU  - ")]
        if "ris_authors" in enrichment:
            parts = enrichment["ris_authors"]
            assert [f"{name['given']} {name['family']}" for name in parts] == priority["authors"]
            assert csl_data["author"] == parts
            assert ris_names == [f"{name['family']}, {name['given']}" for name in parts]
            unstructured = {k: v for k, v in priority.items() if k != "ris_authors"}
            other_lines = [line for line in ris_text.splitlines() if not line.startswith("AU  - ")]
            original_lines = [line for line in render_ris(unstructured).splitlines()
                              if not line.startswith("AU  - ")]
            assert other_lines == original_lines
        else:
            assert ris_names == priority["authors"]
            assert csl_data["author"] == [{"literal": name} for name in priority["authors"]]
        assert csl_data["DOI"] == doi and csl_data["title"] == priority["title"]
        if "article_number" in expected:
            number = expected["article_number"]
            assert f"eid = {{{number}}}" in bib_text
            assert f"C7  - {number}" in ris_text
            assert csl_data["number"] == number
            assert isinstance(csl_data["number"], str)
            assert "page" not in csl_data
            locator = VERIFIED_RIS_LOCATORS.get(doi)
            assert enrichment.get("ris_article_locator") == locator
            start_pages = [line[6:] for line in ris_text.splitlines() if line.startswith("SP  - ")]
            assert start_pages == ([locator] if locator else [])
            assert "EP  - " not in ris_text
        else:
            assert "number" not in csl_data
        assert "article-number" not in csl_data
        assert csl_data.get("issue") == expected.get("issue")
        if "first_page" in expected:
            pages = f"{expected['first_page']}--{expected['last_page']}"
            assert f"pages = {{{pages}}}" in bib_text
            assert f"SP  - {expected['first_page']}" in ris_text
            assert f"EP  - {expected['last_page']}" in ris_text
            assert csl_data["page"] == pages.replace("--", "-")
    for publication in public:
        current = citation_record(publication, enhancements, config["site_url"],
                                  official_abstracts.get(norm_doi(publication.get("doi"))))
        if current is None:
            continue
        data = json.loads(render_csl_json(current))
        assert isinstance(data, dict) and "article-number" not in data
        assert data.get("issue") == current.get("issue")
        if current.get("article_number"):
            assert data["number"] == current["article_number"]
            without_number = copy.deepcopy(current)
            without_number.pop("article_number")
            assert {key: value for key, value in data.items() if key != "number"} == (
                json.loads(render_csl_json(without_number))
            )
        else:
            assert "number" not in data
    eligible = sum(not citation_skip_reason(item) for item in public)
    assert validate_citations(public, config) == {
        "eligible": eligible, "skipped": len(public) - eligible,
        "bib": eligible, "ris": eligible, "csl": eligible,
    }
    circadian = next(item for item in public if norm_doi(item.get("doi")) == CIRCADIAN_DOI)
    record = citation_record(circadian, enhancements, config["site_url"], official_abstracts.get(CIRCADIAN_DOI))
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
    author_line = next(line.strip() for line in bib.splitlines()
                       if line.strip().startswith("author = {"))
    author_value = author_line.removeprefix("author = {").removesuffix("},")
    assert re.sub(r"\{([^{}]*)\}", r"\1", author_value) == " and ".join(record["authors"])
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
        {"publication_date": "2026-02-30"}, {"publication_date": "2026-13"},
        {"publication_date": "2025-11"}, {"issn": "invalid"},
        {"pmid": "none"}, {"pmcid": "PMC0"},
        {"first_page": "279", "last_page": "236"},
        {"volume": "pending"}, {"issue": " "},
    ):
        changed = copy.deepcopy(valid)
        changed.update(bad)
        reject_metadata(public, {CIRCADIAN_DOI: changed})
    reject_metadata(public, {"10.9999/non-public": valid})
    reject_metadata(public, {CIRCADIAN_DOI.upper(): valid})
    doi = "10.1038/s41467-024-50415-9"
    with_ris_names = enhancements[doi]
    names = with_ris_names["ris_authors"]
    assert names[0] == {"family": "Zhang", "given": "Ge"}
    for invalid in (list(reversed(names)), names[:-1],
                    [{"family": "Zhang", "given": "Ge,"}, *names[1:]]):
        reject_metadata(public, {doi: {**with_ris_names, "ris_authors": invalid}})
    reject_metadata(public, {doi: {**with_ris_names, "verified_sources": []}})
    for invalid in ({"ris_article_locator": "6757"}, {"first_page": "1"}, {"last_page": "2"}):
        reject_metadata(public, {doi: {**with_ris_names, **invalid}})
    print(f"CITATION TESTS PASS: {eligible} eligible, {len(public) - eligible} skipped, "
          f"{len(enhancements)} verified enrichments")


def test_existing_abstract_source_exports(public, enhancements, config, sources):
    """Only the existing verified source texts enter file-import abstract fields."""
    by_doi = {norm_doi(item.get("doi")): item for item in public}
    snapshot = copy.deepcopy(sources)
    for doi, source in sources.items():
        record = citation_record(by_doi[doi], enhancements, config["site_url"], source)
        legacy = citation_record(by_doi[doi], enhancements, config["site_url"])
        text = abstract_text(source)
        folded = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
        ris = (CITATIONS_DIR / f"{record['id']}.ris").read_text(encoding="utf-8")
        csl = json.loads((CITATIONS_DIR / f"{record['id']}.csl.json").read_text(encoding="utf-8"))
        assert [line[6:] for line in ris.splitlines() if line.startswith("AB  - ")] == [folded]
        assert csl.pop("abstract") == text
        assert csl == json.loads(render_csl_json(legacy))
        assert "\n".join(line for line in ris.split("\n") if not line.startswith("AB  - ")) == render_ris(legacy)
        assert record["authors"] == publication_authors(by_doi[doi])
    assert sources == snapshot
    for publication in public:
        doi = norm_doi(publication.get("doi"))
        if doi in sources or enhancements.get(doi, {}).get("official_abstract"):
            continue
        record = citation_record(publication, enhancements, config["site_url"])
        if record is None:
            continue
        record.update(description="Author explanation", summary="Author explanation")
        assert "AB  - " not in render_ris(record) and "abstract" not in json.loads(render_csl_json(record))
    # RIS line folding must retain labels, Unicode and numbers without creating fields.
    doi = next(iter(sources))
    edge = copy.deepcopy(sources[doi])
    edge["abstract"] = {"type": "structured", "sections": [
        {"label": "Background", "text": '<tag> "quoted" & 张格'},
        {"label": "Results", "text": "value 2.5\nDO  - 10.9999/fixture"},
    ]}
    record = citation_record(by_doi[doi], enhancements, config["site_url"], edge)
    ris = render_ris(record)
    assert [line[6:] for line in ris.splitlines() if line.startswith("DO  - ")] == [doi]
    assert json.loads(render_csl_json(record))["abstract"] == abstract_text(edge)
    assert 'Background: <tag> "quoted" & 张格 Results: value 2.5 DO  - 10.9999/fixture' in ris


def test_verified_source_handoffs(public, enhancements, config):
    """Formal abstracts and reviewed PDFs retain their distinct import contracts."""
    cr_doi, ctm_doi = "10.1097/re9.0000000000000037", "10.1002/ctm2.70900"
    by_doi = {norm_doi(item.get("doi")): item for item in public}
    assert {doi for doi, value in enhancements.items() if "official_abstract" in value} == {cr_doi}
    cr = citation_record(by_doi[cr_doi], enhancements, config["site_url"])
    abstract = cr["official_abstract"]
    text = abstract["text"]
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == "ca9148e89175c2b57eda4ccdbe781a68426d35978b92ff9a733c4cd9f00625f2"
    assert abstract["source_url"] in cr["verified_sources"]
    assert abstract["source_version"] == "publisher_accepted_manuscript"
    original = copy.deepcopy(cr)
    ris = render_ris(cr)
    assert [line[6:] for line in ris.splitlines() if line.startswith("AB  - ")] == [text]
    assert [line[6:] for line in ris.splitlines() if line.startswith("L1  - ")] == [cr["fulltext_pdf"]["url"]]
    assert [line[6:] for line in ris.splitlines() if line.startswith("N1  - ")] == [
        "Full text PDF: publisher accepted manuscript (Publish Ahead of Print)."]
    assert cr["fulltext_pdf"]["version"] == "publisher_accepted_manuscript"
    cr_page = (PAPERS_DIR / f"{cr['id']}.html").read_text(encoding="utf-8")
    assert meta_contents(cr_page, "citation_pdf_url") == [cr["fulltext_pdf"]["url"]]
    assert f'href="{cr["fulltext_pdf"]["url"]}">Full text PDF · Accepted manuscript</a>' in cr_page
    cr_markdown = (PAPERS_DIR / f"{cr['id']}.md").read_text(encoding="utf-8")
    assert f'[Full text PDF · Accepted manuscript]({cr["fulltext_pdf"]["url"]})' in cr_markdown
    assert json.loads(render_csl_json(cr))["abstract"] == text
    assert meta_contents((PAPERS_DIR / f"{cr['id']}.html").read_text(encoding="utf-8"), "citation_abstract") == [text]
    assert cr == original

    ctm = citation_record(by_doi[ctm_doi], enhancements, config["site_url"])
    ris = render_ris(ctm)
    ctm_page = (PAPERS_DIR / f"{ctm['id']}.html").read_text(encoding="utf-8")
    assert meta_contents(ctm_page, "citation_publication_date") == ["2026/11"]
    assert meta_contents(ctm_page, "citation_date") == ["2026/11"]
    assert json_ld_object(ctm_page, "ScholarlyArticle", ctm["id"])["datePublished"] == "2026-11-14"
    assert [line for line in ris.splitlines() if line.startswith("DA  - ")] == ["DA  - 2026/11"]
    ctm_csl = json.loads(render_csl_json(ctm))
    assert ctm_csl["issued"]["date-parts"] == [[2026, 11]]
    assert [line[6:] for line in ris.splitlines() if line.startswith("L1  - ")] == [ctm["fulltext_pdf"]["url"]]
    assert ctm["fulltext_pdf"]["version"] == "version_of_record"
    assert not any(line.startswith("N1  - ") for line in ris.splitlines())
    assert not any(line.startswith(("AB  - ", "N2  - ")) for line in ris.splitlines())
    assert "abstract" not in ctm_csl
    assert meta_contents(ctm_page, "citation_abstract") == []
    for record in (cr, ctm):
        expected_names = record.get("ris_authors") or [{"literal": name} for name in record["authors"]]
        expected_ris = ([f"{name['family']}, {name['given']}" for name in expected_names]
                        if record.get("ris_authors") else record["authors"])
        assert [line[6:] for line in render_ris(record).splitlines() if line.startswith("AU  - ")] == expected_ris
        assert json.loads(render_csl_json(record))["author"] == expected_names
        assert meta_contents((PAPERS_DIR / f"{record['id']}.html").read_text(encoding="utf-8"), "citation_author") == record["authors"]

    from build_publications import render_paper_html
    item = next(item for item in json.loads((PAPERS_DIR.parent / "publications.json").read_text(encoding="utf-8"))
                if norm_doi(item.get("doi")) == cr_doi)
    escaped = copy.deepcopy(cr)
    edge_text = '<text> "quoted" & Unicode: 张格'
    escaped["official_abstract"]["text"] = edge_text
    markup = render_paper_html(item, config=config, citation_data=escaped)
    assert meta_contents(markup, "citation_abstract") == [edge_text]
    assert 'content="&lt;text&gt; &quot;quoted&quot; &amp; Unicode: 张格"' in markup
    for patch in ({"verbatim": False}, {"source_url": "https://example.org/unsourced"},
                  {"text": "abstract\nDO  - 10.9999/injected"}, {"text": "unknown"}):
        changed = copy.deepcopy(enhancements[cr_doi])
        changed["official_abstract"].update(patch)
        reject_metadata(public, {cr_doi: changed})
    changed = copy.deepcopy(enhancements[ctm_doi])
    changed["official_abstract"] = copy.deepcopy(abstract)
    changed["verified_sources"] += [abstract["source_url"]]
    reject_metadata(public, {ctm_doi: changed})


if __name__ == "__main__":
    run_tests()
