import json, urllib.parse, urllib.request
from datetime import datetime, timezone
from sync_common import load_master, save_master, merge_items, norm_doi, ROOT

ORCID = "0000-0002-3116-3246"
params = {
    "filter": f"orcid:{ORCID}",
    "rows": "1000",
    "select": "DOI,title,container-title,published,issued,type,URL,author",
}
url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={
    "User-Agent": "GeZhangAcademicHub/1.0 (non-commercial academic website)",
    "Accept": "application/json",
})
with urllib.request.urlopen(req, timeout=45) as r:
    payload = json.load(r)

typemap = {
    "journal-article": "Article", "posted-content": "Preprint",
    "proceedings-article": "Conference paper", "book-chapter": "Book chapter",
    "book": "Book", "dataset": "Dataset"
}
incoming = []
for x in payload.get("message", {}).get("items", []):
    parts = (x.get("published") or x.get("issued") or {}).get("date-parts") or []
    incoming.append({
        "title": (x.get("title") or [""])[0],
        "journal": (x.get("container-title") or [""])[0],
        "year": parts[0][0] if parts and parts[0] else 0,
        "doi": norm_doi(x.get("DOI")),
        "url": x.get("URL"),
        "type": typemap.get(x.get("type"), x.get("type") or "Work"),
    })

master = load_master()
master, added, enriched, duplicates_merged = merge_items(master, incoming, "Crossref:ORCID")
save_master(master)
status_path = ROOT / "sync_status.json"
status = {}
if status_path.exists():
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        pass
status["crossref"] = {
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "records_returned": len(incoming),
    "new_records_added": added,
    "records_enriched": enriched,
    "duplicate_records_merged": duplicates_merged,
    "orcid": ORCID,
}
status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
print(
    f"Crossref sync: {len(incoming)} returned; {added} added; "
    f"{enriched} enriched; {duplicates_merged} duplicates merged."
)
