import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from site_common import load_profile_config
from sync_common import (
    ROOT,
    clean_text,
    load_master,
    merge_items,
    norm_doi,
    normalize_authors,
    save_master,
)

ORCID = load_profile_config()["orcid"]
CROSSREF_WORKS_URL = "https://api.crossref.org/works"
CROSSREF_HEADERS = {
    "User-Agent": "GeZhangAcademicHub/1.0 (non-commercial academic website)",
    "Accept": "application/json",
}

typemap = {
    "journal-article": "Article", "posted-content": "Preprint",
    "proceedings-article": "Conference paper", "book-chapter": "Book chapter",
    "book": "Book", "dataset": "Dataset"
}


def request_crossref(url, attempts=3):
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers=CROSSREF_HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if not retryable or attempt + 1 == attempts:
                raise
            retry_after = exc.headers.get("Retry-After", "")
            delay = int(retry_after) if retry_after.isdigit() else 2 ** attempt
            time.sleep(min(delay, 10))
        except urllib.error.URLError:
            if attempt + 1 == attempts:
                raise
            time.sleep(2 ** attempt)
    return None


def crossref_author_names(author_items):
    names = []
    if not isinstance(author_items, list):
        return names
    for author in author_items:
        if not isinstance(author, dict):
            continue
        given = clean_text(author.get("given"))
        family = clean_text(author.get("family"))
        name = clean_text(" ".join(part for part in (given, family) if part))
        if not name:
            name = clean_text(author.get("name"))
        if name:
            names.append(name)
    return normalize_authors(names)


def crossref_record(item):
    parts = (item.get("published") or item.get("issued") or {}).get("date-parts") or []
    record = {
        "title": (item.get("title") or [""])[0],
        "journal": (item.get("container-title") or [""])[0],
        "year": parts[0][0] if parts and parts[0] else 0,
        "doi": norm_doi(item.get("DOI")),
        "url": item.get("URL"),
        "type": typemap.get(item.get("type"), item.get("type") or "Work"),
    }
    authors = crossref_author_names(item.get("author"))
    if authors:
        record["authors"] = authors
    return record


def discover_orcid_records():
    params = {
        "filter": f"orcid:{ORCID}",
        "rows": "1000",
        "select": "DOI,title,container-title,published,issued,type,URL,author",
    }
    payload = request_crossref(CROSSREF_WORKS_URL + "?" + urllib.parse.urlencode(params))
    return [
        crossref_record(item)
        for item in (payload or {}).get("message", {}).get("items", [])
    ]


def fetch_doi_work(doi):
    url = CROSSREF_WORKS_URL + "/" + urllib.parse.quote(doi, safe="")
    payload = request_crossref(url)
    message = (payload or {}).get("message")
    if message is None:
        return doi, None
    returned_doi = norm_doi(message.get("DOI"))
    if returned_doi != doi:
        raise RuntimeError(f"Crossref DOI mismatch: requested {doi}, received {returned_doi}")
    return doi, message


def backfill_missing_authors(master):
    candidates = [
        norm_doi(item.get("doi"))
        for item in master
        if norm_doi(item.get("doi")) and not normalize_authors(item.get("authors"))
    ]
    if not candidates:
        return 0, 0, 0

    # Crossref's public single-record pool advertises a concurrency limit of 1.
    # Keep DOI enrichment sequential so the scheduled sync respects that limit.
    responses = [fetch_doi_work(doi) for doi in candidates]

    master_by_doi = {
        norm_doi(item.get("doi")): item
        for item in master
        if norm_doi(item.get("doi"))
    }
    enriched = unavailable = 0
    for doi, work in responses:
        authors = crossref_author_names((work or {}).get("author"))
        if not authors:
            unavailable += 1
            continue
        target = master_by_doi[doi]
        if not normalize_authors(target.get("authors")):
            target["authors"] = authors
            enriched += 1
    return len(candidates), enriched, unavailable


def main():
    incoming = discover_orcid_records()
    master = load_master()
    master, added, enriched, duplicates_merged = merge_items(
        master, incoming, "Crossref:ORCID"
    )
    backfill_candidates, authors_backfilled, authors_unavailable = (
        backfill_missing_authors(master)
    )
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
        "records_enriched": enriched + authors_backfilled,
        "duplicate_records_merged": duplicates_merged,
        "author_backfill_candidates": backfill_candidates,
        "authors_backfilled": authors_backfilled,
        "authors_unavailable": authors_unavailable,
        "orcid": ORCID,
    }
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(
        f"Crossref sync: {len(incoming)} returned; {added} added; "
        f"{enriched + authors_backfilled} enriched; "
        f"{duplicates_merged} duplicates merged; "
        f"{authors_unavailable} DOI records without reliable Crossref authors."
    )


if __name__ == "__main__":
    main()
