"""Read-only DOI reconciliation of a complete public ORCID /works snapshot.

Run from any directory: python reports/orcid-reconciliation-20261012/audit_orcid.py
Use --refresh only to obtain another public GET snapshot. This script never imports
sync_orcid, requests OAuth credentials, writes master/index, or invokes workflows.
ORCID work groups are the counting unit; multiple sources/put-codes are retained.
"""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sync_common import clean_text, is_withdrawn, norm_doi  # noqa: E402

ORCID = "0000-0002-3116-3246"
URL = f"https://pub.orcid.org/v3.0/{ORCID}/works"
BASELINE = "75040ff3b04c0a5151889b1793bc69a03a590037"


def save_json(name, body):
    (OUT / name).write_text(
        json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def save_csv(name, rows, fields):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def get_baseline(path, ref):
    raw = subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def doi_map(records):
    result = defaultdict(list)
    for record in records:
        doi = norm_doi(record.get("doi"))
        if doi:
            result[doi].append(record)
    return result


def external_ids(node):
    return (node.get("external-ids") or {}).get("external-id") or []


def group_dois(group):
    # Only self identifiers identify this work. Part-of IDs do not identify it.
    return sorted({
        norm_doi(ext.get("external-id-value"))
        for node in [group] + (group.get("work-summary") or [])
        for ext in external_ids(node)
        if ext.get("external-id-type", "").lower() == "doi"
        and ext.get("external-id-relationship") in (None, "self")
        and norm_doi(ext.get("external-id-value"))
    })


def present_count(dois, mapping):
    return sum(len(mapping.get(doi, [])) for doi in dois)


def refresh():
    meta = {
        "url": URL,
        "requested_at_utc": datetime.now(timezone.utc).isoformat(),
        "accept": "application/vnd.orcid+json",
        "authenticated": False,
    }
    request = urllib.request.Request(URL, headers={
        "Accept": meta["accept"],
        "User-Agent": "GeZhangAcademicHub/1.0 (non-commercial academic website)",
    })
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read()
        payload = json.loads(raw)
        if not isinstance(payload.get("group"), list):
            raise ValueError("Public ORCID response has no work-group array")
        meta.update(status=response.status, final_url=response.url,
                    content_type=response.headers.get("Content-Type"))
    (OUT / "orcid-works-public.raw.json").write_bytes(raw)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot = OUT / "snapshots" / f"orcid-works-{timestamp}.raw.json"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes(raw)
    meta["immutable_snapshot"] = snapshot.relative_to(OUT).as_posix()
    meta["sha256"] = hashlib.sha256(raw).hexdigest()
    save_json("orcid-works-public.request.json", meta)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--expanded", action="store_true", help="Also regenerate redundant detailed audit working files.")
    parser.add_argument("--baseline", default=BASELINE)
    args = parser.parse_args()
    args.baseline = subprocess.check_output(
        ["git", "rev-parse", args.baseline], cwd=ROOT).decode().strip()
    if args.refresh:
        refresh()
    request = json.loads((OUT / "orcid-works-public.request.json").read_text("utf-8"))
    raw = (OUT / request.get("immutable_snapshot", "orcid-works-public.raw.json")).read_bytes()
    if request.get("sha256") and hashlib.sha256(raw).hexdigest() != request["sha256"]:
        raise ValueError("ORCID source response bytes do not match the request manifest; restore the original LF source blob.")
    payload = json.loads(raw)
    before_master, master_sha = get_baseline("data/publications_master.json", args.baseline)
    before_index, index_sha = get_baseline("paper_index.json", args.baseline)
    before_index = before_index["papers"]
    after_master = json.loads((ROOT / "data/publications_master.json").read_text("utf-8"))
    after_index = json.loads((ROOT / "paper_index.json").read_text("utf-8"))["papers"]
    bm, bi, am, ai = map(doi_map, [before_master, before_index, after_master, after_index])
    groups = payload["group"]
    rows, details = [], []
    group_numbers_by_doi = defaultdict(list)
    ambiguous_groups = []
    for number, group in enumerate(groups, 1):
        dois = group_dois(group)
        for doi in dois:
            group_numbers_by_doi[doi].append(number)
        summaries = group.get("work-summary") or []
        titles = list(dict.fromkeys(clean_text((s.get("title") or {}).get("title", {}).get("value")) for s in summaries))
        source_names = list(dict.fromkeys((s.get("source") or {}).get("source-name", {}).get("value", "") for s in summaries))
        put_codes = [s.get("put-code") for s in summaries]
        withdrawn = any(is_withdrawn({"title": title}) for title in titles)
        withdrawn = withdrawn or any(is_withdrawn(r) for doi in dois for r in bm.get(doi, []))
        reasons = []
        if not dois:
            reasons.append("no-self-doi")
        if len(dois) > 1:
            reasons.append("multiple-distinct-self-dois")
        if any(s.get("visibility") != "public" for s in summaries):
            reasons.append("non-public-visibility-unexpected")
        if reasons:
            ambiguous_groups.append({"group_number": number, "dois": dois, "reasons": reasons})
        bm_count, bi_count, am_count, ai_count = [present_count(dois, d) for d in [bm, bi, am, ai]]
        before_status = "withdrawn-retained-master-excluded-index" if withdrawn else (
            "missing-master-and-index" if not bm_count and not bi_count else
            "present-master-and-index" if bm_count and bi_count else "master-index-mismatch")
        after_status = "withdrawn-retained-master-excluded-index" if withdrawn else (
            "missing-master-and-index" if not am_count and not ai_count else
            "present-master-and-index" if am_count and ai_count else "master-index-mismatch")
        row = {
            "group_number": number, "doi": " | ".join(dois),
            "orcid_titles": " | ".join(titles),
            "work_summary_count": len(summaries),
            "put_codes": " | ".join(map(str, put_codes)),
            "source_names": " | ".join(source_names),
            "orcid_types": " | ".join(sorted({s.get("type", "") for s in summaries})),
            "orcid_years": " | ".join(sorted({str(((s.get("publication-date") or {}).get("year") or {}).get("value") or "") for s in summaries})),
            "orcid_urls": " | ".join(sorted({((s.get("url") or {}).get("value") or "") for s in summaries})),
            "withdrawn": withdrawn,
            "baseline_master_matches": bm_count, "baseline_index_matches": bi_count,
            "baseline_status": before_status,
            "current_master_matches": am_count, "current_index_matches": ai_count,
            "current_status": after_status,
            "ambiguity": " | ".join(reasons),
        }
        rows.append(row)
        details.append({**row, "external_ids": external_ids(group), "summaries": summaries})
    orcid_dois = set(group_numbers_by_doi)
    missing_before = sorted(orcid_dois - set(bm))
    missing_after = sorted(orcid_dois - set(am))
    website_only = [r for r in before_master if norm_doi(r.get("doi")) not in orcid_dois]
    duplicate_report = {
        "baseline_master_duplicate_dois": {d: len(v) for d, v in bm.items() if len(v) > 1},
        "baseline_index_duplicate_dois": {d: len(v) for d, v in bi.items() if len(v) > 1},
        "current_master_duplicate_dois": {d: len(v) for d, v in am.items() if len(v) > 1},
        "current_index_duplicate_dois": {d: len(v) for d, v in ai.items() if len(v) > 1},
        "orcid_dois_in_multiple_groups": {d: v for d, v in group_numbers_by_doi.items() if len(v) > 1},
        "multiple_summaries_same_group_are_not_duplicate_publications": [
            {"group_number": r["group_number"], "doi": r["doi"],
             "summary_count": r["work_summary_count"], "put_codes": r["put_codes"]}
            for r in rows if r["work_summary_count"] > 1
        ],
    }
    withdrawn_rows = [{
        "doi": norm_doi(r.get("doi")), "title": r.get("title"),
        "in_orcid": norm_doi(r.get("doi")) in orcid_dois,
        "baseline_master_count": len(bm.get(norm_doi(r.get("doi")), [])),
        "baseline_index_count": len(bi.get(norm_doi(r.get("doi")), [])),
        "current_master_count": len(am.get(norm_doi(r.get("doi")), [])),
        "current_index_count": len(ai.get(norm_doi(r.get("doi")), [])),
        "action": "Preserve withdrawn record; continue excluding it from public paper index.",
    } for r in before_master if is_withdrawn(r)]
    summary = {
        "orcid": ORCID, "baseline_commit": args.baseline,
        "retrieved_at_utc": request["requested_at_utc"],
        "endpoint": URL, "http_status": request["status"],
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "baseline_master_sha256": master_sha, "baseline_paper_index_sha256": index_sha,
        "public_work_groups": len(groups),
        "public_work_summaries": sum(len(g.get("work-summary") or []) for g in groups),
        "unique_orcid_self_dois": len(orcid_dois),
        "baseline_master_records": len(before_master),
        "baseline_master_records_with_doi": sum(bool(norm_doi(r.get("doi"))) for r in before_master),
        "baseline_master_records_without_doi": sum(not norm_doi(r.get("doi")) for r in before_master),
        "baseline_paper_index_records": len(before_index),
        "orcid_dois_in_baseline_master": len(orcid_dois & set(bm)),
        "orcid_dois_in_baseline_paper_index": len(orcid_dois & set(bi)),
        "truly_missing_before_count": len(missing_before), "truly_missing_before_dois": missing_before,
        "website_only_before_count": len(website_only),
        "withdrawn_in_master_count": len(withdrawn_rows),
        "doi_identity_ambiguous_group_count": len(ambiguous_groups),
        "doi_identity_ambiguous_groups": ambiguous_groups,
        "current_master_records": len(after_master), "current_paper_index_records": len(after_index),
        "orcid_dois_in_current_master": len(orcid_dois & set(am)),
        "orcid_dois_in_current_paper_index": len(orcid_dois & set(ai)),
        "added_missing_dois_count": len(set(missing_before) & set(am)),
        "added_missing_dois": sorted(set(missing_before) & set(am)),
        "missing_after_count": len(missing_after), "missing_after_dois": missing_after,
        "scope_note": "DOI identity reconciliation only. Publisher article type, authorship, and formal full-text/V2 verification are separate editorial checks. ORCID journal-article does not establish Article versus Letter.",
    }
    if args.expanded:
        save_csv("orcid-doi-reconciliation.csv", rows, list(rows[0]))
        save_json("orcid-group-reconciliation.json", details)
        save_json("orcid-duplicates.json", duplicate_report)
        save_json("orcid-website-only.json", website_only)
        save_csv("orcid-website-only.csv", [{
            "doi": r.get("doi", ""), "title": r.get("title", ""),
            "type": r.get("type", ""), "slug": r.get("slug", ""),
            "action": "Preserve; absent from current public ORCID snapshot.",
        } for r in website_only], ["doi", "title", "type", "slug", "action"])
        save_csv("orcid-withdrawn.csv", withdrawn_rows, ["doi", "title", "in_orcid", "baseline_master_count", "baseline_index_count", "current_master_count", "current_index_count", "action"])
    category = {
        "present-master-and-index": "PRESENT_BOTH",
        "missing-master-and-index": "ORCID_ONLY_MISSING_ON_SITE",
        "master-index-mismatch": "AMBIGUOUS_OR_DUPLICATE",
        "withdrawn-retained-master-excluded-index": "WITHDRAWN_OR_NOT_PUBLIC",
    }
    all_rows = []
    for row in rows:
        doi = row["doi"]
        added = doi in summary["added_missing_dois"]
        item = {**row,
                "baseline_category": "AMBIGUOUS_OR_DUPLICATE" if row["ambiguity"] else category[row["baseline_status"]],
                "current_category": "AMBIGUOUS_OR_DUPLICATE" if row["ambiguity"] else category[row["current_status"]],
                "decision_basis": "Exact normalized self DOI in complete live public ORCID group, baseline/current master and paper index.",
                "identity_verification": "VERIFIED_PUBLISHER_PUBMED_CROSSREF_FULL_TEXT" if doi == "10.1126/science.aek9583" else "VERIFIED_PUBLISHER_CORRECTED_PROOF_CROSSREF" if doi == "10.1016/j.medd.2026.100004" else "EXISTING_RECORD_PRESERVED",
                "action": "ADD_VERIFIED_OMISSION" if added else "CORRECT_IDENTITY_VIA_PR14" if doi == "10.1056/nejmc2518964" else "PRESERVE_WITHDRAWN_EXCLUSION" if row["withdrawn"] else "PRESERVE_EXISTING",
                "verification_sources": "science/SCIENCE_GOLD_STANDARD.json" if doi == "10.1126/science.aek9583" else "medicine/MEDICINE_GOLD_STANDARD.json" if doi == "10.1016/j.medd.2026.100004" else f"https://doi.org/{doi}"}
        all_rows.append(item)
    for record in website_only:
        item = dict.fromkeys(all_rows[0], "")
        item.update(doi=record.get("doi", ""), orcid_titles=record["title"],
                    baseline_master_matches=1, baseline_index_matches=1,
                    current_master_matches=1, current_index_matches=1,
                    baseline_category="SITE_ONLY", current_category="SITE_ONLY",
                    decision_basis="Existing no-DOI patent is absent from this public ORCID response; absence is not a deletion instruction.",
                    identity_verification="EXISTING_RECORD_PRESERVED", action="PRESERVE_SITE_ONLY")
        all_rows.append(item)
    save_csv("ORCID_SITE_RECONCILIATION.csv", all_rows, list(all_rows[0]))
    save_csv("ORCID_SITE_PENDING.csv", [r for r in all_rows if r["current_category"] in {"AMBIGUOUS_OR_DUPLICATE", "ORCID_ONLY_MISSING_ON_SITE"}], list(all_rows[0]))
    summary.update(pending_identity_or_type_verification_count=len(ambiguous_groups) + len(missing_after),
                   science_formal_v2_completed=json.loads((OUT / "science/SCIENCE_GOLD_STANDARD.json").read_text("utf-8"))["formal_v2_completed"],
                   selected_count=len(json.loads((ROOT / "data/featured_papers.json").read_text("utf-8"))["papers"]),
                   deep_geo_count=len(json.loads((ROOT / "data/deep_geo_papers.json").read_text("utf-8"))["papers"]))
    from citation_common import citation_skip_reason
    summary["pending_citation_capability_record_count"] = sum(bool(citation_skip_reason(r)) for r in after_master if r.get("doi") in {"10.1126/science.aek9583", "10.1016/j.medd.2026.100004"})
    summary["doi_duplicates"] = {key: value for key, value in duplicate_report.items() if key != "multiple_summaries_same_group_are_not_duplicate_publications"}
    save_json("orcid-reconciliation-summary.json", summary)
    note = f"""# Complete public ORCID reconciliation

Snapshot: `{summary['retrieved_at_utc']}`. Official public API: <{URL}>; HTTP {summary['http_status']}, no account credentials used.
Baseline: `{args.baseline}`. `audit_orcid.py` reproduces this audit offline from the raw response and baseline Git objects; `--refresh` performs a new public GET.

| Measure | Before | Current workspace |
| --- | ---: | ---: |
| ORCID public work groups | {len(groups)} | {len(groups)} |
| ORCID work summaries (sources/put-codes, not publication count) | {summary['public_work_summaries']} | {summary['public_work_summaries']} |
| Website master records | {len(before_master)} | {len(after_master)} |
| Public paper index records | {len(before_index)} | {len(after_index)} |
| ORCID DOI records represented in master | {summary['orcid_dois_in_baseline_master']} | {summary['orcid_dois_in_current_master']} |
| ORCID DOI records represented in public index | {summary['orcid_dois_in_baseline_paper_index']} | {summary['orcid_dois_in_current_paper_index']} |
| ORCID DOI records missing from master | {len(missing_before)} | {len(missing_after)} |

The two baseline omissions are `10.1126/science.aek9583` and `10.1016/j.medd.2026.100004`. `10.1111/jdi.70462` already exists. There are {len(ambiguous_groups)} groups with ambiguous DOI identity. Article-type and full-text verification are separate checks; these counts do not claim that Science has a formal V2.

The baseline master includes one withdrawn preprint (`10.21203/rs.3.rs-3395716/v1`), which is in ORCID but deliberately excluded from the public index. One existing no-DOI Patent is absent from this public ORCID snapshot and must be preserved. Thus the baseline contains 76 master records (75 with DOI and one Patent), 75 public index records, and 75 ORCID DOI matches in master (74 in the public index).

`ORCID_SITE_RECONCILIATION.csv` has one row per public group plus the SITE_ONLY preservation case and preserves all source names and put-codes. The timestamped snapshot named in `orcid-works-public.request.json` is the complete unmodified response and retains all 107 summaries, group external identifiers and source identities. Its original byte hash is checked before use. `audit_orcid.py --expanded` can regenerate detailed working files locally; redundant copies and old execution logs are archived outside the repository, with original Git LF hashes and historical commit linkage in `ARCHIVE_MANIFEST.json`.

Targeted official `/work` responses additionally verify the three requested identities. Science's publisher-supplied AAAS record identifies Ge Zhang as first author with ORCID `0000-0002-3116-3246`. The Medicine Discovery self-entered record lists 16 authors with Ge Zhang last; the publisher corrected proof independently confirms the complete authors, Correspondence subtype (p. 5) and corresponding-author footnote (p. 6). JDI's record lists eight authors with Ge Zhang fourth; its existing master identity is unchanged.

## Final evidence and dependency status

- Science: complete local publisher print pages 38-39 were visually reviewed again, excluding adjacent Letters. The five arguments, five Q&A items, citation-use boundaries and evidence matrix are activated without scientific changes at `data/deep_geo/doi-10-1126-science-aek9583.json`, with exact paragraph locators. Formal V2 completed: **{summary['science_formal_v2_completed']}**. PR #14's existing Letter renderer is reused; the public page has ScholarlyArticle schema and complete citations. No n=1 dataset or treatment effect was manufactured.
- Medicine Discovery: verified Correspondence; identity page only, with no automatic Selected/Deep GEO membership. Corrected-proof pagination is not used as a journal page range; volume and issue remain unassigned.
- Truly missing before: {len(missing_before)}; added: {summary['added_missing_dois_count']}; missing after: {len(missing_after)}; identity/type records awaiting verification: {summary['pending_identity_or_type_verification_count']}.
- Selected Research: {summary['selected_count']}; Deep GEO: {summary['deep_geo_count']}. Science is first independently in both; all old entries and summaries are preserved.
- `ORCID_SITE_RECONCILIATION.csv` contains all {len(groups)} public groups plus the preserved SITE_ONLY patent; `ORCID_SITE_PENDING.csv` contains only unresolved rows.
- Citation capability dependencies are resolved: PR #14 is merged and the shared renderer now supports Correspondence. Both new works have BibTeX, RIS, CSL-JSON and full Markdown authors; genre is preserved. Pending citation-capability records: {summary['pending_citation_capability_record_count']}. See the focused publication-release regression and final release acceptance; no duplicate renderer was implemented.
- Public source PDFs/page images stay outside this repository. Gold Standard records retain version descriptions, source hashes, explicit reference context and locators.

## Why daily Crossref discovery omitted these works

The original live Crossref ORCID-filter query returned eight works and included JDI, but did not include either new DOI. Both DOI-specific Crossref deposits existed and listed authors, without an author ORCID field for this researcher. An ORCID public work group can be author-added or publisher-supplied independently of Crossref author-ORCID registration. The observed discovery gap is established for that captured audit; an API indexing delay is not established. Historical raw query/request files are preserved in the local archive and original PR #15 commit, and DOI-specific deposits remain in the compact evidence record.

A separate follow-up could periodically reconcile public ORCID self-DOIs into a reviewable branch, protecting existing types, identity fields and selection controllers. It should have a read-only audit mode, idempotent DOI normalization and regression cases for same-name authors, withdrawn records and generic journal-article types. No stable synchronization or automation code was changed in this publication PR.
"""
    if args.expanded:
        (OUT / "orcid-reconciliation.md").write_text(note, encoding="utf-8")
    (OUT / "ORCID_SITE_SUMMARY.md").write_text(note, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
