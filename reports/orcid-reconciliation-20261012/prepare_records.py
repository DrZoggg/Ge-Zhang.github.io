"""Apply only the two verified additions; preserve every baseline master record.

No sync, workflow, deployment or credential operation is performed. Source PDFs
and page images stay outside Git; this report stores identity facts and hashes.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent / "orcid-reconciliation-20261012-evidence"
SCIENCE = "10.1126/science.aek9583"
MEDICINE = "10.1016/j.medd.2026.100004"
BASE = "75040ff3b04c0a5151889b1793bc69a03a590037"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source(path, locator, version):
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size, "locator": locator, "version": version,
            "redistributed": False}


def main():
    original = json.loads(subprocess.check_output(
        ["git", "show", f"{BASE}:data/publications_master.json"], cwd=ROOT))
    master_path = ROOT / "data/publications_master.json"
    master = read(master_path)
    medicine = read(EVIDENCE / "medicine/verified-metadata.json")
    medicine.update(
        article_type="Correspondence", article_type_status="verified_publisher_corrected_proof",
        corresponding_author=True, full_text_status="local_publisher_corrected_proof_verified",
        equal_contribution={"authors": ["Yahui Han", "Qiang Li"], "ge_zhang": False},
        warnings=["Volume and issue remain unassigned in the corrected proof and absent from Crossref.",
                  "Internal PDF pages 1-6 are proof pagination, not a journal page range.",
                  "No new dataset or predictive performance result is reported by this Correspondence."],
    )
    assert len(medicine["authors"]) == 16 and medicine["authors"][-1] == "Ge Zhang"
    new_record = {key: medicine[key] for key in ("title", "journal", "year", "doi", "authors")}
    new_record.update(url=medicine["doi_url"], type="Correspondence",
                      sources=["ORCID", "Crossref:DOI", "Publisher"],
                      slug="doi-10-1016-j-medd-2026-100004")
    existing = [p for p in master if p.get("doi") == MEDICINE]
    if existing:
        assert existing == [new_record], "Refuse to overwrite an existing Medicine record"
    else:
        master.append(new_record)
    for old in original:
        assert [r for r in master if r.get("slug") == old.get("slug")] == [old]
    master.sort(key=lambda r: (-int(r.get("year") or 0), " ".join(r["title"].split()).casefold()))
    write(master_path, master)

    citation_path = ROOT / "data/citation_metadata.json"
    citation = read(citation_path)
    citation["papers"][MEDICINE] = {
        "publication_date": "2026-09-22", "article_number": "100004",
        "issn": "3117-9282", "publisher": "Elsevier BV",
        "verified_sources": medicine["sources"] + [medicine["official_url"]],
    }
    write(citation_path, citation)
    ids_path = ROOT / "data/scholarly_identifiers.json"
    ids = read(ids_path)
    ids["papers"][MEDICINE] = {
        "publisher_url": medicine["official_url"], "verified_sources": medicine["sources"],
        "verified_at": "2026-10-12",
    }
    write(ids_path, ids)
    featured_path = ROOT / "data/featured_papers.json"
    featured = read(featured_path)
    assert featured["papers"][0]["doi"] == SCIENCE
    featured["papers"][0]["summary"] = (
        "Science Letter proposing current, linked public records of human protocols and major "
        "outcomes in individualized genetic therapy research; reporting proposals, not a new clinical trial."
    )
    write(featured_path, featured)

    medicine_pdf = Path("C:/Users/zg381/Downloads/1-s2.0-S3117928226000044-main (1).pdf")
    medicine["source_checks"] = {
        "article_subtype": "Publisher corrected proof p. 5, Acknowledgements explicitly identifies Correspondence.",
        "authors_and_roles": "Publisher corrected proof p. 6, complete author list and * Corresponding authors footnote.",
        "data_scope": "Publisher corrected proof p. 5, Data availability states no data used.",
        "doi_and_version": "Publisher corrected proof p. 1 DOI; embedded PDF Subject identifies Corrected Proof, 100004.",
        "online_date": "KeAi official most-downloaded article entry, Available online 22 September 2026.",
    }
    medicine["source_manifest"] = [source(medicine_pdf, "PDF pp. 1, 5, 6", "Elsevier publisher corrected proof")]
    write(OUT / "medicine/MEDICINE_GOLD_STANDARD.json", medicine)
    science_path = OUT / "science/SCIENCE_GOLD_STANDARD.json"
    gold = read(science_path)
    v2 = read(OUT / "science/SCIENCE_V2_READY.json")
    gold.update(paper_geo_v2_status="full_text_content_ready_pending_pr14", formal_v2_completed=False,
                full_text_review_completed=True,
                publication_blocker="Current main emits CreativeWork for Letter, failing the V2 ScholarlyArticle requirement. Reuse the existing fix from unmerged PR #14.")
    gold["identity"]["publisher_url"] = v2["provenance"]["publisher_url"]
    gold["verified_content_scope"]["permitted_public_summary"] = v2["summary"]
    gold["verified_content_scope"]["summary_basis"] = "Complete published Letter, print pp. 38-39, reviewed column by column."
    gold["verified_content_scope"]["verified_full_text_claims"] = [
        {"id": f["id"], "claim": f["claim"], "context": f["context"], "locator": f["source_locator"]}
        for f in v2["key_findings"]
    ]
    gold["verified_content_scope"]["full_text_argument_locators"] = [f["source_locator"] for f in v2["key_findings"]]
    gold["verified_content_scope"]["interpretation_boundary"] = (
        "Narrative reporting and governance argument, not a newly conducted n=1 clinical trial. "
        "No sample size, treatment effect, clinical performance estimate, blame or causal determination "
        "is assigned. The case and preclinical evidence are attributed to prior sources; adjacent Letters are excluded."
    )
    gold["full_text_access"] = {
        "status": "obtained_complete_local_publisher_print_pages",
        "public_web_access": "Publisher landing page is bibliographically readable; direct full-text access returned 403.",
        "review_basis": v2["provenance"]["review_basis"],
        "source_version": v2["provenance"]["source_version"],
        "page_image_scope": "Science print p. 38 right column from this Letter's heading; p. 39 left column through its DOI and reference list.",
        "entire_letter_reviewed": True,
        "source_protection": "Local full-page copies remain outside the public repository; only original paraphrases, identity facts, hashes and locators are delivered.",
    }
    gold["source_manifest"] = [
        source(EVIDENCE / f"provided-fulltext/science-page-{page}.png", locator, "Publisher print-page image")
        for page, locator in [(1, "Print p. 38, right column"), (2, "Print p. 39, left column")]
    ]
    gold["reference_context_review"] = [
        {"number": 1, "source": "ClinicalTrials.gov NCT06860672", "context": "Opening reporting-gap example; no assertion that the registry still has the same status today.", "locator": "p. 38 paragraph 1; p. 39 reference 1", "url": "https://clinicaltrials.gov/study/NCT06860672"},
        {"number": 2, "source": "K. Yang et al., Nature 651, 785 (2026)", "context": "Preclinical-publication context cited in the opening paragraph; no results or experiments imported into this Letter's evidence profile.", "locator": "p. 38 paragraph 1; p. 39 reference 2"},
        {"number": 3, "source": "WHO Trial Registration Data Set, version 1.3.1", "context": "Context for separating serious-event occurrence from causal assessment. WHO item 23 defines adverse events as events that may or may not be caused by the intervention.", "locator": "p. 39 paragraph 4; reference 3; WHO item 23", "url": "https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set"},
    ]
    gold["engineering_disposition"]["create_full_text_based_v2_json"] = False
    gold["engineering_disposition"]["full_text_v2_candidate_created"] = True
    gold["engineering_disposition"]["candidate_location"] = "SCIENCE_V2_READY.json"
    gold["engineering_disposition"]["citation_support_dependency"] = (
        "Science BibTeX/RIS/CSL and enhanced Highwire/JSON-LD remain pending the unmerged PR #14; "
        "V2 activation is also deferred because main's Letter schema type fails the V2 validator. "
        "A full-text-reviewed candidate is retained as SCIENCE_V2_READY.json. No renderer code is copied."
    )
    write(science_path, gold)
    print("Two DOI records prepared; all 76 baseline records unchanged; Science full-text V2 candidate retained pending PR #14.")


if __name__ == "__main__":
    main()
