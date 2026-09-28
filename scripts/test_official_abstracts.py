"""Focused Official Abstract source and rendered-parity regression checks."""

import copy
import json
import tempfile
from pathlib import Path

import official_abstracts
from site_common import PAPERS_DIR
from sync_common import is_withdrawn, load_master, norm_doi
from validate_site import meta_contents, paper_json_ld_object
from test_abstract_additions import FIXTURE, fixtures, reviewed_record


def main():
    public = [item for item in load_master() if not is_withdrawn(item)]
    records = official_abstracts.load_official_abstracts(public)
    additions = fixtures()
    original_dois = json.loads(FIXTURE.read_text(encoding="utf-8"))["baseline_dois"]
    assert len(records) == len(original_dois) + len(additions)
    for doi in additions:
        assert records[doi] == reviewed_record(doi)
    for doi in ("10.1016/j.joim.2025.06.003", "10.71321/fy14v342", "10.1111/jcmm.70725", "10.1200/po.24.00089"):
        if doi not in additions:
            assert doi not in records
    assert not set(records) & official_abstracts.EXCLUDED
    for item in public:
        doi = norm_doi(item.get("doi"))
        page = (PAPERS_DIR / f"{item['slug']}.html").read_text(encoding="utf-8")
        markdown = (PAPERS_DIR / f"{item['slug']}.md").read_text(encoding="utf-8")
        schema = paper_json_ld_object(page, item["slug"])
        if doi in records:
            text = official_abstracts.abstract_text(records[doi])
            assert page.count('id="official-abstract"') == 1
            assert meta_contents(page, "citation_abstract") == [text]
            assert schema["abstract"] == text
            assert "## Official Abstract" in markdown
            if records[doi]["abstract"]["type"] == "structured":
                expected_labels = (
                    [s["label"] for s in reviewed_record(doi)["abstract"]["sections"]]
                    if doi in additions else
                    ["Background", "Methods", "Results", "Conclusion"]
                    if doi == "10.3389/fcvm.2025.1724572"
                    else ["Objectives", "Materials and methods", "Results", "Conclusion"]
                    if doi == "10.3389/fpubh.2025.1521372"
                    else
                    ["Purpose", "Methods", "Results", "Conclusion"]
                    if doi == "10.2147/ijn.s522157"
                    else
                    ["Aims", "Methods", "Results", "Conclusions"]
                    if doi == "10.1002/ehf2.14003"
                    else ["Background", "Results", "Conclusions"]
                    if doi == "10.1186/s12915-025-02400-x"
                    else ["Background", "Methods", "Results", "Conclusions"]
                )
                assert [s["label"] for s in records[doi]["abstract"]["sections"]] == expected_labels
        else:
            assert 'id="official-abstract"' not in page
            assert not meta_contents(page, "citation_abstract")
            assert "abstract" not in schema

    with tempfile.TemporaryDirectory() as temp:
        original_path = official_abstracts.PATH
        official_abstracts.PATH = Path(temp) / "official_abstracts.json"
        try:
            assert official_abstracts.load_official_abstracts(public) == {}
            for mutation in (
                lambda payload: payload["papers"].update({"10.1093/eurheartj/ehaf523": next(iter(records.values()))}),
                lambda payload: payload["papers"]["10.1093/eurheartj/ehaf523"].update({"license": "CC-BY-4.0", "license_url": official_abstracts.LICENSE_URLS["CC-BY-4.0"]}),
                lambda payload: payload["papers"]["10.1111/jcmm.70725"].update({"license": "OUP-AUTHOR-ABSTRACT-REUSE", "license_url": records["10.1093/eurheartj/ehaf523"]["license_url"]}),
                lambda payload: payload["papers"]["10.1093/eurheartj/ehaf523"].update({"source_url": "https://academic.oup.com/eurheartj/article/46/45/4969/8212255?unreviewed=1"}),
                lambda payload: payload["papers"]["10.1016/j.ejphar.2023.175569"].update({"source_url": "https://pubmed.ncbi.nlm.nih.gov/1/"}),
                lambda payload: payload["papers"]["10.1016/j.ejphar.2023.175569"].update({"source_type": "publisher"}),
                lambda payload: payload["papers"]["10.1111/jcmm.70725"].update({"source_type": "pubmed"}),
                lambda payload: payload["papers"]["10.1016/j.ejphar.2023.175569"].update({"license": "CC-BY-NC-4.0", "license_url": official_abstracts.LICENSE_URLS["CC-BY-NC-4.0"]}),
                lambda payload: next(iter(payload["papers"].values())).update({"verbatim": False}),
                lambda payload: next(iter(payload["papers"].values())).update({"license": "unknown"}),
                lambda payload: next(iter(payload["papers"].values()))["abstract"].update({"text": ""}),
            ):
                payload = {"version": 1, "papers": copy.deepcopy(records)}
                mutation(payload)
                official_abstracts.PATH.write_text(json.dumps(payload), encoding="utf-8")
                try:
                    official_abstracts.load_official_abstracts(public)
                except ValueError:
                    pass
                else:
                    raise AssertionError("Invalid Official Abstract source accepted")
        finally:
            official_abstracts.PATH = original_path
    print(f"OFFICIAL ABSTRACT TESTS PASS: {len(records)} records; {len(additions)} reviewed additions; exact sources, structure, parity and invalid-source cases")


if __name__ == "__main__":
    main()
