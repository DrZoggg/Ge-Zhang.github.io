"""Focused optional Citation Layer schema, anchor and parity checks."""

import copy
import json

from build_publications import validate_citation_layer
from site_common import PAPERS_DIR
from sync_common import ROOT


TARGETS = {
    "aihflevel": ("aihflevel.json", 4, 5, 5),
    "doi-10-1038-s41698-026-01699-1": (
        "doi-10-1038-s41698-026-01699-1.json", 5, 6, 6
    ),
    "apvs": ("apvs.json", 5, 7, 7),
    "doi-10-1093-eurheartj-ehaf523": ("doi-10-1093-eurheartj-ehaf523.json", 5, 7, 7),
    "doi-10-1172-jci194175": ("doi-10-1172-jci194175.json", 5, 7, 7),
    "olink-dcm": ("olink-dcm.json", 5, 6, 6),
    "smc-fate": ("smc-fate.json", 6, 6, 6),
}


def main():
    tested = []
    for slug, (filename, case_count, row_count, finding_count) in TARGETS.items():
        content = json.loads((ROOT / "data" / "deep_geo" / filename).read_text(encoding="utf-8"))
        layer = content.get("citation_layer")
        if layer is None:
            continue
        validate_citation_layer(layer, content["key_findings"], slug)
        assert len(layer["citation_use_cases"]) == case_count
        assert len(layer["evidence_matrix"]) == row_count
        assert len(content["key_findings"]) == finding_count
        page = (PAPERS_DIR / f"{slug}.html").read_text(encoding="utf-8")
        markdown = (PAPERS_DIR / f"{slug}.md").read_text(encoding="utf-8")
        for anchor in ["citation-use-cases", "citation-boundaries", "evidence-matrix"]:
            assert page.count(f'id="{anchor}"') == 1
            assert markdown.count(f'<a id="{anchor}"></a>') == 1
        for finding in content["key_findings"]:
            anchor = finding["id"].lower()
            assert page.count(f'id="{anchor}"') == 1
            assert markdown.count(f'<a id="{anchor}"></a>') == 1
        for row in layer["evidence_matrix"]:
            assert page.count(f'id="{row["id"]}"') == 1
            assert markdown.count(f'<a id="{row["id"]}"></a>') == 1
            ref = row["evidence_refs"][0]
            assert row["source_locator"] == next(
                finding["source_locator"] for finding in content["key_findings"]
                if finding["id"] == ref
            )
        bad = copy.deepcopy(layer)
        bad["evidence_matrix"][0]["evidence_refs"] = ["KF999"]
        try:
            validate_citation_layer(bad, content["key_findings"], slug)
        except ValueError:
            pass
        else:
            raise AssertionError("Unknown KF ref accepted")
        tested.append(slug)
    assert "aihflevel" in tested
    print("CITATION LAYER TESTS PASS: " + ", ".join(tested))


if __name__ == "__main__":
    main()
