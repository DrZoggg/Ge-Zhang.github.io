"""Focused, read-only acceptance for this publication-only draft.

Run from repository root: python reports/orcid-reconciliation-20261012/verify_delivery.py
The unmerged PR #14 dependency is reported explicitly, never counted as a pass.
"""
import collections
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from citation_common import citation_skip_reason
from build_publications import validate_deep_v2_content
from sync_common import norm_doi, is_withdrawn

BASE = "75040ff3b04c0a5151889b1793bc69a03a590037"
SCIENCE = "10.1126/science.aek9583"
MEDICINE = "10.1016/j.medd.2026.100004"
JDI = "10.1111/jdi.70462"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def before(path):
    return json.loads(subprocess.check_output(
        ["git", "show", f"{BASE}:{path}"], cwd=ROOT).decode("utf-8"))


def by_doi(rows):
    return {norm_doi(row.get("doi")): row for row in rows if row.get("doi")}


def meta(page, name):
    return [html.unescape(x) for x in re.findall(
        rf'<meta name="{re.escape(name)}" content="([^"]*)">', page)]


def main():
    old, current = before("data/publications_master.json"), load("data/publications_master.json")
    old_dois, current_dois = by_doi(old), by_doi(current)
    for row in old:
        matches = [x for x in current if x.get("slug") == row.get("slug")]
        assert matches == [row], f"Protected old record changed: {row.get('slug')}"
    counts = collections.Counter(norm_doi(x.get("doi")) for x in current if x.get("doi"))
    assert all(n == 1 for n in counts.values()), "Duplicate DOI in master"
    additions = sorted(set(current_dois) - set(old_dois))
    assert additions == sorted([SCIENCE, MEDICINE]), additions
    assert current_dois[JDI] == old_dois[JDI]
    for controller in ("featured_papers", "deep_geo_papers"):
        path = f"data/{controller}.json"
        previous, updated = before(path), load(path)
        assert updated["papers"][0]["doi"] == SCIENCE
        assert updated["papers"][1:] == previous["papers"], f"Old {controller} changed"
        assert len(updated["papers"]) == len(previous["papers"]) + 1
        assert MEDICINE not in {x.get("doi") for x in updated["papers"]}
    index = load("paper_index.json")["papers"]
    public = load("publications.json")
    assert len(index) == len(public) == sum(not is_withdrawn(x) for x in current)
    for rows in (index, public):
        assert len(by_doi(rows)) == len([x for x in rows if x.get("doi")])
        assert len([x for x in rows if norm_doi(x.get("doi")) == JDI]) == 1
    for name in ("citation_metadata", "scholarly_identifiers", "question_index"):
        path = f"data/{name}.json"
        prior, updated = before(path), load(path)
        assert all(updated["papers"][d] == entry for d, entry in prior["papers"].items()), path
        expected = set() if name == "question_index" else {SCIENCE, MEDICINE}
        assert set(updated["papers"]) - set(prior["papers"]) == expected
    old_questions = by_doi(before("research/questions.json")["questions"])
    new_questions = by_doi(load("research/questions.json")["questions"])
    assert all(new_questions[d] == row for d, row in old_questions.items())
    assert new_questions == old_questions
    old_index_dois = by_doi(before("paper_index.json")["papers"])
    new_index_dois = by_doi(index)
    assert set(new_index_dois) - set(old_index_dois) == {SCIENCE, MEDICINE}
    assert all(new_index_dois[d]["paper_url"] == r["paper_url"] for d, r in old_index_dois.items())
    dependencies = []
    checks = []
    for doi in additions:
        row = current_dois[doi]
        slug = row["slug"]
        page = (ROOT / f"papers/{slug}.html").read_text(encoding="utf-8")
        md = (ROOT / f"papers/{slug}.md").read_text(encoding="utf-8")
        canonical = f"https://drgezhang.com/papers/{slug}.html"
        assert page.count(f'<link rel="canonical" href="{canonical}">') == 1
        assert len(re.findall(r"<h1(?:\s|>)", page)) == 1
        assert meta(page, "citation_title") == [row["title"]]
        assert meta(page, "citation_doi") == [doi]
        assert meta(page, "citation_journal_title") == [row["journal"]]
        assert meta(page, "citation_author") == row["authors"]
        schemas = [json.loads(s) for s in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
        schema = next(s for s in schemas if s.get("identifier", {}).get("value") == doi)
        assert schema["name"] == row["title"]
        assert [a["name"] for a in schema["author"]] == row["authors"]
        assert schema["url"] == canonical
        for value in (row["title"], row["journal"], f'Type: {row["type"]}', doi, canonical):
            assert value in md, (doi, "markdown identity", value)
        author_parity = all(f"{i}. {author}" in md for i, author in enumerate(row["authors"], 1))
        if not author_parity:
            dependencies.append({"doi": doi, "check": "Markdown full author list", "status": "PENDING_PR14" if row["type"] == "Letter" else "PENDING_SHARED_CORRESPONDENCE_SUPPORT"})
        reason = citation_skip_reason(row)
        if reason:
            assert not any((ROOT / f"citations/{slug}{ext}").exists() for ext in (".bib", ".ris", ".csl.json"))
            dependencies.append({"doi": doi, "check": "BibTeX/RIS/CSL and Cite this paper", "reason": reason, "status": "PENDING_PR14" if row["type"] == "Letter" else "PENDING_SHARED_CORRESPONDENCE_SUPPORT"})
            enhancement = load("data/citation_metadata.json")["papers"][doi]
            assert enhancement["publication_date"][:4] == str(row["year"])
            # Current main applies enhancements only to citation-eligible types.
            assert meta(page, "citation_publication_date") == [str(row["year"])]
            dependencies.append({"doi": doi, "check": "Enhanced exact date/volume/pages in Highwire and JSON-LD; ScholarlyArticle schema type", "status": "PENDING_PR14" if row["type"] == "Letter" else "PENDING_SHARED_CORRESPONDENCE_SUPPORT", "observed_schema_type": schema["@type"], "observed_highwire_date": str(row["year"])})
        else:
            for ext in (".bib", ".ris", ".csl.json"):
                text = (ROOT / f"citations/{slug}{ext}").read_text(encoding="utf-8")
                assert doi in text
            csl = load(f"citations/{slug}.csl.json")
            assert [a["literal"] for a in csl["author"]] == row["authors"]
        for path in ("sitemap.xml", "llms-full.txt", "publications.html", "assets/evidence-search.json"):
            text = (ROOT / path).read_text(encoding="utf-8")
            assert slug in text, (doi, path)
        checks.append({"doi": doi, "canonical": canonical, "highwire_and_jsonld_authors": "PASS", "markdown_identity": "PASS", "markdown_authors": "PASS" if author_parity else "PENDING_PR14" if row["type"] == "Letter" else "PENDING_SHARED_CORRESPONDENCE_SUPPORT"})
    science = by_doi(public)[SCIENCE]
    assert science["type"] == "Letter"
    assert science["paper_geo_status"] == "pending"
    assert science["featured"] is True and science["deep_geo"] is True
    assert not (ROOT / f'data/deep_geo/{science["slug"]}.json').exists()
    science_content = load("reports/orcid-reconciliation-20261012/science/SCIENCE_V2_READY.json")
    validate_deep_v2_content(science_content)
    gold = load("reports/orcid-reconciliation-20261012/science/SCIENCE_GOLD_STANDARD.json")
    assert gold["formal_v2_completed"] is False and gold["full_text_review_completed"] is True
    assert gold["full_text_access"]["entire_letter_reviewed"] is True
    assert len(gold["source_manifest"]) == 2
    assert gold["verified_content_scope"]["sample_size"] is None
    assert gold["verified_content_scope"]["trial_outcomes"] is None
    assert gold["verified_content_scope"]["treatment_effects"] is None
    assert science_content["study_profile"]["profile_type"] == "narrative_review"
    assert not any(k in science_content["study_profile"] for k in ("unique_total_n", "cohorts", "population"))
    assert [f["source_locator"] for f in science_content["key_findings"]] == gold["verified_content_scope"]["full_text_argument_locators"]
    science_page = (ROOT / f'papers/{science["slug"]}.html').read_text("utf-8")
    science_md = (ROOT / f'papers/{science["slug"]}.md').read_text("utf-8")
    assert "Deep GEO · Pending" in science_md
    assert "data-v2-section" not in science_page
    assert not (ROOT / f'assets/evidence/{science["slug"]}.csv').exists()
    dependencies.append({"doi": SCIENCE, "check": "Formal V2 activation", "status": "PENDING_PR14", "reason": "Main emits CreativeWork for Letter; V2 requires ScholarlyArticle. Full-text-reviewed candidate is retained in the report."})
    assert science["slug"] in (ROOT / "llms.txt").read_text("utf-8")
    medicine = by_doi(public)[MEDICINE]
    assert medicine["type"] == "Correspondence"
    assert medicine["featured"] is False and medicine["deep_geo"] is False
    assert medicine["paper_geo_status"] == "none"
    assert not (ROOT / f'data/deep_geo/{medicine["slug"]}.json').exists()
    sitemap = ET.fromstring((ROOT / "sitemap.xml").read_text("utf-8"))
    sitemap_urls = [e.text for e in sitemap.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert len(sitemap_urls) == len(set(sitemap_urls))
    for d in additions:
        assert sitemap_urls.count(f'https://drgezhang.com/papers/{current_dois[d]["slug"]}.html') == 1
    # Verify every old paper page, evidence source and automation stays unchanged.
    protected = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "papers", "citations", "data/deep_geo", ".github", "scripts", "robots.txt", "data/profile.json", "data/profile_control.json", "data/research_themes.json"], cwd=ROOT).decode("utf-8").splitlines()
    for path in protected:
        original = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
        current_bytes = (ROOT / path).read_bytes()
        assert current_bytes.replace(b"\r\n", b"\n") == original.replace(b"\r\n", b"\n"), path
    # Only aggregated generated outputs and allowed source data may change.
    allowed = {"data/publications_master.json", "data/featured_papers.json", "data/deep_geo_papers.json", "data/citation_metadata.json", "data/scholarly_identifiers.json", "data/question_index.json", "index.html", "publications.html", "publications.json", "publication_inventory.csv", "paper_index.json", "llms.txt", "llms-full.txt", "sitemap.xml", "assets/evidence-search.json", "research/questions.html", "research/questions.json"}
    changed = subprocess.check_output(["git", "-c", "core.quotePath=false", "diff", "--name-only", BASE], cwd=ROOT, stderr=subprocess.DEVNULL).decode("utf-8").splitlines()
    # Evidence CSV bytes differ only by Windows checkout line endings.
    for path in [p for p in changed if p.startswith("assets/evidence/")]:
        original = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
        assert (ROOT / path).read_bytes().replace(b"\r\n", b"\n") == original.replace(b"\r\n", b"\n")
    generated_new = {f"citations/{current_dois[JDI]['slug']}{ext}" for ext in (".bib", ".ris", ".csl.json")}
    assert all(p in allowed or p in generated_new or p.startswith(("reports/orcid-reconciliation-20261012/", "assets/evidence/")) or any(p == f"papers/{current_dois[d]['slug']}{ext}" for d in additions for ext in (".html", ".md")) for p in changed), changed
    result = {"base_sha": BASE, "existing_records_preserved": len(old), "protected_existing_files": len(protected), "master": len(current), "public": len(public), "added_dois": additions, "doi_duplicates": 0, "featured": len(load("data/featured_papers.json")["papers"]), "deep_geo": len(load("data/deep_geo_papers.json")["papers"]), "old_controller_entries_and_summaries": "UNCHANGED", "science_v2": "FULL_TEXT_REVIEWED_CANDIDATE_PENDING_PR14_ACTIVATION", "science_formal_v2_completed": False, "pending_identity_or_type_verification_count": 0, "pending_citation_capability_record_count": len({d["doi"] for d in dependencies}), "checks": checks, "deferred_acceptance": dependencies}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
