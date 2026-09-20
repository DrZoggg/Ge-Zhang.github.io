import json, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from site_common import load_profile_config
from sync_common import load_master, save_master, merge_items, norm_doi, ROOT

ORCID = load_profile_config()["orcid"]
CLIENT_ID = os.environ.get("ORCID_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("ORCID_CLIENT_SECRET", "").strip()

if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit(
        "ORCID public API credentials are not configured. "
        "Add repository secrets ORCID_CLIENT_ID and ORCID_CLIENT_SECRET, then run again."
    )

# Obtain a /read-public token using ORCID's client-credentials OAuth flow.
token_data = urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "client_credentials",
    "scope": "/read-public",
}).encode("utf-8")
token_req = urllib.request.Request(
    "https://orcid.org/oauth/token",
    data=token_data,
    headers={"Accept": "application/json"},
    method="POST",
)
with urllib.request.urlopen(token_req, timeout=45) as r:
    token_payload = json.load(r)
token = token_payload.get("access_token")
if not token:
    raise SystemExit("ORCID token request failed: no access_token returned.")

req = urllib.request.Request(
    f"https://pub.orcid.org/v3.0/{ORCID}/works",
    headers={
        "Accept": "application/vnd.orcid+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "GeZhangAcademicHub/1.0 (non-commercial academic website)",
    },
)
with urllib.request.urlopen(req, timeout=45) as r:
    payload = json.load(r)

typemap = {
    "journal-article": "Article", "preprint": "Preprint",
    "conference-paper": "Conference paper", "book-chapter": "Book chapter",
    "book": "Book", "data-set": "Dataset", "patent": "Patent", "review": "Review",
}
incoming = []
for group in payload.get("group", []):
    summaries = group.get("work-summary", []) or []
    if not summaries:
        continue
    def score(s):
        ext = ((s.get("external-ids") or {}).get("external-id") or [])
        has_doi = any((e.get("external-id-type") or "").lower() == "doi" for e in ext)
        has_journal = bool((s.get("journal-title") or {}).get("value"))
        return (1 if has_doi else 0, 1 if has_journal else 0)
    s = sorted(summaries, key=score, reverse=True)[0]
    title = (((s.get("title") or {}).get("title") or {}).get("value")) or ""
    journal = ((s.get("journal-title") or {}).get("value")) or ""
    year = (((s.get("publication-date") or {}).get("year") or {}).get("value")) or 0
    doi, source_url = "", ""
    for e in ((s.get("external-ids") or {}).get("external-id") or []):
        if (e.get("external-id-type") or "").lower() == "doi" and not doi:
            doi = norm_doi(e.get("external-id-value"))
            source_url = ((e.get("external-id-url") or {}).get("value")) or ""
    if not source_url:
        source_url = ((s.get("url") or {}).get("value")) or ""
    if doi and not source_url:
        source_url = "https://doi.org/" + doi
    incoming.append({
        "title": title,
        "journal": journal or "Unknown source",
        "year": int(year) if str(year).isdigit() else 0,
        "doi": doi,
        "url": source_url,
        "type": typemap.get(s.get("type"), s.get("type") or "Work"),
    })

master = load_master()
master, added, enriched, duplicates_merged = merge_items(master, incoming, "ORCID")
save_master(master)

status_path = ROOT / "sync_status.json"
status = {}
if status_path.exists():
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        status = {}
status["orcid"] = {
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "public_work_groups_returned": len(incoming),
    "new_records_added": added,
    "records_enriched": enriched,
    "duplicate_records_merged": duplicates_merged,
    "orcid": ORCID,
}
status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
print(
    f"ORCID reconciliation: {len(incoming)} public works; {added} added; "
    f"{enriched} enriched; {duplicates_merged} duplicates merged."
)
