import copy
import html
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "publications_master.json"

_HTML_TAG_RE = re.compile(r"<\s*/?\s*[a-z][^>]*>", re.I)
_WITHDRAWN_RE = re.compile(
    r"^\s*(?:\[\s*withdrawn\s*\]|withdrawn|withdrawal)\s*(?::|[-–—])?\s*",
    re.I,
)
_DASH_TRANSLATION = str.maketrans({
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-", "−": "-"
})
_PLACEHOLDERS = {"", "unknown source", "work", "untitled work"}


def load_master():
    return json.loads(MASTER.read_text(encoding="utf-8")) if MASTER.exists() else []


def clean_text(value):
    """Remove publisher markup and normalize whitespace without losing display text."""
    if value is None:
        return ""
    text_value = html.unescape(str(value))
    text_value = _HTML_TAG_RE.sub("", text_value)
    text_value = unicodedata.normalize("NFKC", text_value).translate(_DASH_TRANSLATION)
    text_value = re.sub(r"[\u200b-\u200d\ufeff]", "", text_value)
    return re.sub(r"\s+", " ", text_value).strip()


def title_status(value):
    title = clean_text(value)
    if _WITHDRAWN_RE.match(title):
        return "withdrawn", _WITHDRAWN_RE.sub("", title, count=1).strip()
    return "", title


def norm_doi(value):
    if not value:
        return ""
    doi = clean_text(value)
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.I)
    return doi.strip().rstrip(".,;)").lower()


def norm_title(value):
    if not value:
        return ""
    _, title = title_status(value)
    title = unicodedata.normalize("NFKD", title.casefold())
    title = "".join(ch for ch in title if not unicodedata.combining(ch))
    title = title.replace("&", " and ")
    title = re.sub(r"[\W_]+", " ", title, flags=re.UNICODE)
    return re.sub(r"\s+", " ", title).strip()


def is_withdrawn(item):
    status = clean_text(item.get("status", "")).casefold()
    detected, _ = title_status(item.get("title", ""))
    return status == "withdrawn" or detected == "withdrawn"


def _valid_year(value):
    try:
        year = int(value)
    except (TypeError, ValueError):
        return 0
    return year if 1000 <= year <= 3000 else 0


def _sources(item, default_source=""):
    values = []
    raw = item.get("sources") or []
    if isinstance(raw, str):
        raw = [raw]
    raw = list(raw) + [item.get("source"), default_source]
    for value in raw:
        value = clean_text(value)
        if value and value not in values:
            values.append(value)
    return values


def normalize_item(item, default_source=""):
    rec = copy.deepcopy(item)
    # Presentation state belongs to the dedicated controllers. External sync
    # must never persist or resurrect legacy Featured flags in master metadata.
    rec.pop("featured", None)
    detected_status, cleaned_title = title_status(rec.get("title", ""))
    rec["title"] = cleaned_title or "Untitled work"
    rec["journal"] = clean_text(rec.get("journal")) or "Unknown source"
    rec["type"] = clean_text(rec.get("type")) or "Work"
    rec["year"] = _valid_year(rec.get("year"))

    doi = norm_doi(rec.get("doi"))
    if doi:
        rec["doi"] = doi
    else:
        rec.pop("doi", None)

    url = clean_text(rec.get("url"))
    if url:
        rec["url"] = url
    else:
        rec.pop("url", None)

    if detected_status == "withdrawn" or clean_text(rec.get("status")).casefold() == "withdrawn":
        rec["status"] = "withdrawn"
    elif not clean_text(rec.get("status")):
        rec.pop("status", None)

    sources = _sources(rec, default_source)
    rec.pop("source", None)
    if sources:
        rec["sources"] = sources
    else:
        rec.pop("sources", None)
    return rec


def _is_placeholder(value):
    return clean_text(value).casefold() in _PLACEHOLDERS


def _same_work(left, right):
    left_doi, right_doi = norm_doi(left.get("doi")), norm_doi(right.get("doi"))
    if left_doi and right_doi:
        return left_doi == right_doi
    left_title, right_title = norm_title(left.get("title")), norm_title(right.get("title"))
    return bool(left_title and left_title == right_title)


def _find_match(items, new):
    doi = norm_doi(new.get("doi"))
    if doi:
        for index, old in enumerate(items):
            if norm_doi(old.get("doi")) == doi:
                return index

    title = norm_title(new.get("title"))
    if not title:
        return None
    candidates = [
        index for index, old in enumerate(items)
        if norm_title(old.get("title")) == title and _same_work(old, new)
    ]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        candidate_dois = {norm_doi(items[index].get("doi")) for index in candidates}
        candidate_dois.discard("")
        if len(candidate_dois) <= 1:
            return candidates[0]
    return None


def _merge_record(old, new):
    left, right = normalize_item(old), normalize_item(new)
    merged = copy.deepcopy(left)

    # Preserve arbitrary/manual fields and stable slugs. Featured state is
    # deliberately excluded by normalize_item().
    for key, value in right.items():
        if key not in merged or merged.get(key) in (None, "", [], 0, False):
            merged[key] = copy.deepcopy(value)

    for key in ("journal", "type"):
        if _is_placeholder(merged.get(key)) and not _is_placeholder(right.get(key)):
            merged[key] = right[key]
    if not _valid_year(merged.get("year")) and _valid_year(right.get("year")):
        merged["year"] = _valid_year(right.get("year"))
    if not norm_doi(merged.get("doi")) and norm_doi(right.get("doi")):
        merged["doi"] = norm_doi(right.get("doi"))
    if not merged.get("url") and right.get("url"):
        merged["url"] = right["url"]
    if left.get("slug") or right.get("slug"):
        merged["slug"] = left.get("slug") or right.get("slug")
    if is_withdrawn(left) or is_withdrawn(right):
        merged["status"] = "withdrawn"

    sources = _sources(left) + _sources(right)
    merged["sources"] = list(dict.fromkeys(sources))
    if not merged["sources"]:
        merged.pop("sources", None)
    return normalize_item(merged)


def deduplicate_items(items):
    unique = []
    duplicates_merged = 0
    for raw in items:
        rec = normalize_item(raw)
        index = _find_match(unique, rec)
        if index is None:
            unique.append(rec)
        else:
            unique[index] = _merge_record(unique[index], rec)
            duplicates_merged += 1
    return unique, duplicates_merged


def save_master(items):
    items, duplicates_merged = deduplicate_items(items)
    items = sorted(items, key=lambda x: (-int(x.get("year") or 0), norm_title(x.get("title"))))
    MASTER.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items, duplicates_merged


def merge_items(master, incoming, source):
    master, duplicates_merged = deduplicate_items(master)
    added = enriched = 0
    for raw in incoming:
        new = normalize_item(raw, source)
        index = _find_match(master, new)
        if index is None:
            master.append(new)
            added += 1
            continue

        merged = _merge_record(master[index], new)
        if merged != master[index]:
            master[index] = merged
            enriched += 1

    master, extra_merged = deduplicate_items(master)
    return master, added, enriched, duplicates_merged + extra_merged
