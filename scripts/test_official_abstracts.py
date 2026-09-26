"""Focused Official Abstract source and rendered-parity regression checks."""

import copy
import json
import tempfile
from pathlib import Path

import official_abstracts
from site_common import PAPERS_DIR
from sync_common import is_withdrawn, load_master, norm_doi
from validate_site import meta_contents, paper_json_ld_object


def main():
    public = [item for item in load_master() if not is_withdrawn(item)]
    records = official_abstracts.load_official_abstracts(public)
    assert len(records) == 4
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
                assert [s["label"] for s in records[doi]["abstract"]["sections"]] == [
                    "Background", "Methods", "Results", "Conclusions"
                ]
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
                lambda payload: payload["papers"].update({"10.1002/mdr2.70052": next(iter(records.values()))}),
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
    print("OFFICIAL ABSTRACT TESTS PASS: four verified records; optional and invalid-source cases")


if __name__ == "__main__":
    main()
