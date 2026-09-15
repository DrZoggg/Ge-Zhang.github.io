import json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "publications_master.json"

def load_master():
    return json.loads(MASTER.read_text(encoding="utf-8")) if MASTER.exists() else []

def save_master(items):
    items = sorted(items, key=lambda x: (-int(x.get("year") or 0), (x.get("title") or "").lower()))
    MASTER.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

def norm_doi(v):
    if not v:
        return ""
    v = str(v).strip()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v, flags=re.I)
    v = re.sub(r"^doi:\s*", "", v, flags=re.I)
    return v.strip().lower()

def norm_title(v):
    if not v:
        return ""
    s = unicodedata.normalize("NFKD", str(v)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def merge_items(master, incoming, source):
    by_doi, by_title = {}, {}
    for i, item in enumerate(master):
        d, t = norm_doi(item.get("doi")), norm_title(item.get("title"))
        if d:
            by_doi[d] = i
        if t:
            by_title[t] = i

    added = enriched = 0
    for new in incoming:
        d, t = norm_doi(new.get("doi")), norm_title(new.get("title"))
        idx = by_doi.get(d) if d else None
        if idx is None and t:
            idx = by_title.get(t)

        if idx is None:
            rec = {
                "title": new.get("title") or "Untitled work",
                "year": int(new.get("year") or 0),
                "journal": new.get("journal") or "Unknown source",
                "type": new.get("type") or "Work",
                "source": source,
            }
            if d:
                rec["doi"] = d
            if new.get("url"):
                rec["url"] = new["url"]
            master.append(rec)
            idx = len(master) - 1
            if d:
                by_doi[d] = idx
            if t:
                by_title[t] = idx
            added += 1
        else:
            old = master[idx]
            changed = False
            for key in ("doi", "journal", "year", "url", "type"):
                val = new.get(key)
                if val and (not old.get(key) or old.get(key) in ("Unknown source", "Work", 0)):
                    old[key] = norm_doi(val) if key == "doi" else val
                    changed = True
            sources = old.get("sources") or ([old["source"]] if old.get("source") else [])
            if source not in sources:
                sources.append(source)
                old["sources"] = sources
                changed = True
            if changed:
                enriched += 1
    return master, added, enriched
