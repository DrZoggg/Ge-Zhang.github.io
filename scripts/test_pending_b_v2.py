"""B-only V2 regression from the independently reviewed publisher/supplement source.
No builds, network requests, external approval dependencies, or writes.
A remains Pending with its existing identity; this is an engineering contract.
"""
import hashlib
import html
import json
import re
import subprocess
from build_publications import validate_deep_v2_content
from citation_common import citation_record, load_citation_metadata, render_bibtex, render_ris, render_csl_json
from site_common import load_site_config
from sync_common import ROOT
from validate_site import meta_contents, paper_json_ld_object, validate_v2_rendered_page

BASE = "1a3e000969d98f873eee3f6fd7043dffa92c1366"
A, B = "10.71321/fy14v342", "10.1007/s11426-026-3629-x"
SLUG = "doi-10-1007-s11426-026-3629-x"
# Fill only from the independent, final source review; never derive from mutated fixtures.
# Frozen UTF-8/LF bytes. The 41,554-byte candidate has 604 CRLF pairs:
# raw SHA fb44ac27...; LF normalization yields 40,950 bytes / abe0f48d....
B_SOURCE_SHA256 = "abe0f48da5a6326be441e0735da9c0c510bbf1bccc6a1cbda5146b0dfd75ae69"
B_FINDINGS_SHA256 = "3efa7252e4bf12b2e8a9489625edba2699772f49a7fae4515306b0a2036b03c9"
B_LOCATORS = {
    "KF1": "Main PDF pp. 2-3, Results 3.1, Fig. 1a-d; official supplement PDF pp. 2-3, Spectroscopic Measurements and DFT Calculations; pp. 5-6, Figs. S1-S4.",
    "KF2": "Main PDF p. 3, Results 3.2, Fig. 2b-g; official supplement PDF p. 2, Dynamic Light Scattering.",
    "KF3": "Main PDF pp. 3-4, Results 3.3, Fig. 3b-g; official supplement PDF p. 2, Spectroscopic Measurements; p. 7, Figs. S5-S6.",
    "KF4": "Main PDF p. 4, Results 3.3, Fig. 3h-j; official supplement PDF p. 2, Spectroscopic Measurements.",
    "KF5": "Main PDF pp. 5-6, Results 3.4, Fig. 4a-c; official supplement PDF p. 3, Animal Model and In Vivo Imaging; p. 8, Fig. S7.",
    "KF6": "Main PDF pp. 6-7, Results 3.5-3.6, Figs. 5a-d and 6a-b; official supplement PDF p. 3, animal grouping.",
    "KF7": "Main PDF pp. 7-8, Results 3.6; official supplement PDF p. 8, Figs. S8-S9.",
}
B_CRITICAL_EVIDENCE = {
    "KF3": {"Signal metric": "PA intensity at 740 nm; no validated two-wavelength ratio is defined for these displayed calibrations", "Superoxide absorption titration": "0-125 micromolar", "Superoxide PA calibration shown": "0, 12.5, 25, 50 and 80 micromolar; R-squared = 0.977", "GSH PA calibration shown": "0, 50, 100, 200 and 300 micromolar; R-squared = 0.982"},
    "KF5": {"Main group size": "n=3 per group, reported in the supplementary methods", "Main acquisition": "Pre-/post-probe PA imaging on days 2 and 8; 740 nm; aortic-region ROI", "Additional longitudinal sequence": "Fig. S7 displays days 0, 1 and 4; its separate sample count and cohort relationship are not reported"},
}

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def old_bytes(path):
    return subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)

def old(path):
    return json.loads(old_bytes(path))

def unchanged(path):
    assert (ROOT / path).read_bytes().replace(b"\r\n", b"\n") == old_bytes(path).replace(b"\r\n", b"\n"), path

def cards(page):
    section = re.search(r'<section id="featured">(.*?)</section>', page, re.S)[1]
    return re.findall(r'<article\b[^>]*class="card paper"[^>]*>.*?</article>', section, re.S)

def main():
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in [B_SOURCE_SHA256, B_FINDINGS_SHA256])
    assert B_LOCATORS and B_CRITICAL_EVIDENCE, "B requires approved facts and source locators"
    master = json.loads(read("data/publications_master.json"))
    assert master == old("data/publications_master.json") and len(master) == 78
    by_doi = {p["doi"]: p for p in master if p.get("doi")}
    for control in ["featured_papers", "deep_geo_papers"]:
        unchanged("data/" + control + ".json")
        rows = json.loads(read("data/" + control + ".json"))["papers"]
        assert len(rows) == 29 and [p["doi"] for p in rows[:2]] == ["10.1126/science.aek9583", "10.1038/s41467-024-50415-9"]
    before = old("paper_index.json")["papers"]
    now = json.loads(read("paper_index.json"))["papers"]
    prior_v2 = {p["doi"] for p in before if p["paper_geo_status"] == "v2"}
    assert len(prior_v2) == 27 and len(before) == len(now) == 77
    assert {p["doi"] for p in now if p["paper_geo_status"] == "v2"} == prior_v2 | {B}
    assert {p["doi"] for p in now if p["paper_geo_status"] == "pending"} == {A}
    assert not (ROOT / "data/deep_geo/doi-10-71321-fy14v342.json").exists()
    current_by_doi = {p.get("doi") or p["paper_url"]: p for p in now}
    for p in before:
        new = current_by_doi[p.get("doi") or p["paper_url"]]
        for field in ["doi", "title", "type", "journal", "year", "paper_url", "markdown_url"]:
            assert new.get(field) == p.get(field), (p.get("doi"), field)
    assert len(json.loads(read("publications.json"))) == 77
    assert len({p["doi"] for p in now if p.get("doi")}) == sum(bool(p.get("doi")) for p in now)
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "--", "data", "citations", ".github"], cwd=ROOT).decode().splitlines()
    for path in paths:
        if path != "data/question_index.json":
            unchanged(path)
    for doi in prior_v2 | {A}:
        slug = by_doi[doi]["slug"]
        for suffix in ["html", "md"]:
            unchanged(f"papers/{slug}.{suffix}")
        if doi in prior_v2:
            unchanged(f"assets/evidence/{slug}.csv")
    old_cards, new_cards = cards(old_bytes("index.html").decode()), cards(read("index.html"))
    target_link = f'href="papers/{SLUG}.html"'
    assert len(old_cards) == len(new_cards) == 29
    assert [c for c in old_cards if target_link not in c] == [c for c in new_cards if target_link not in c], "Other 28 Selected cards changed"
    assert [re.search(r'<h3><a href="([^"]+)', c)[1] for c in old_cards] == [re.search(r'<h3><a href="([^"]+)', c)[1] for c in new_cards]
    q_before, q_now = old("data/question_index.json"), json.loads(read("data/question_index.json"))
    assert set(q_now["papers"]) == set(q_before["papers"]) | {B} and A not in q_now["papers"]
    assert q_now["papers"][B] == {"qa_index": 3}
    assert all(q_now["papers"][doi] == v for doi, v in q_before["papers"].items())
    assert {k:v for k,v in q_now.items() if k != "papers"} == {k:v for k,v in q_before.items() if k != "papers"}
    raw = (ROOT / f"data/deep_geo/{SLUG}.json").read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(raw).hexdigest() == B_SOURCE_SHA256
    content = json.loads(raw)
    findings = json.dumps(content["key_findings"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(findings).hexdigest() == B_FINDINGS_SHA256
    assert {f["id"]:f["source_locator"] for f in content["key_findings"]} == B_LOCATORS
    by_id = {f["id"]: f for f in content["key_findings"]}
    for finding_id, expected in B_CRITICAL_EVIDENCE.items():
        values = {item["label"]:item["value"] for item in by_id[finding_id]["evidence"]}
        assert all(values.get(label) == value for label, value in expected.items())
    assert content["doi"] == B and content["version"] == 2
    assert content["study_profile"]["profile_type"] == "preclinical_multimodal"
    assert content["study_profile"]["external_validation"] is False
    assert len(content["key_findings"]) == 7 and len(content["qa"]) == 8
    assert len(content["citation_layer"]["citation_use_cases"]) == 6 and len(content["citation_layer"]["evidence_matrix"]) == 7
    assert not {"unique_total_n", "cohorts"}.intersection(content["study_profile"])
    validate_deep_v2_content(content, SLUG)
    item, config = by_doi[B], load_site_config()
    assert item["type"] == "Article" and len(item["authors"]) == 10 and item["authors"][5] == "Ge Zhang"
    markup, markdown = read(f"papers/{SLUG}.html"), read(f"papers/{SLUG}.md")
    schema = paper_json_ld_object(markup, SLUG)
    validate_v2_rendered_page(content, item, markup, markdown, schema, by_doi, config)
    assert meta_contents(markup, "citation_author") == item["authors"]
    assert [p["name"] for p in schema["author"]] == item["authors"]
    author_block = markdown.split("## Full Authors\n", 1)[1].split("\n## ", 1)[0]
    assert re.findall(r"^\d+\. (.+)$", author_block, re.M) == item["authors"]
    assert f'<p>{html.escape(content["summary"])}</p>' in next(c for c in new_cards if target_link in c)
    record = citation_record(item, load_citation_metadata(master), config["site_url"])
    for suffix, render in [("bib", render_bibtex), ("ris", render_ris), ("csl.json", render_csl_json)]:
        assert read(f"citations/{SLUG}.{suffix}") == render(record)
        assert f'../citations/{SLUG}.{suffix}' in markup
    questions = json.loads(read("research/questions.json"))["questions"]
    assert [q for q in questions if q["doi"] != B] == old("research/questions.json")["questions"]
    assert len([q for q in questions if q["doi"] == B]) == 1
    question = next(q for q in questions if q["doi"] == B)
    assert question["question"] == content["qa"][2]["question"] and question["answer_url"].endswith("#qa-3")
    print("B V2 PASS: 28 V2 / A Pending; 27 prior evidence sources, identities and other 28 cards frozen")

if __name__ == "__main__":
    main()
