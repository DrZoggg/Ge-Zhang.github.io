import hashlib
import json
import re
from pathlib import Path

from sync_common import ROOT, is_withdrawn, norm_doi, norm_title


SITE_CONFIG_PATH = ROOT / "data" / "site_config.json"
FEATURED_PATH = ROOT / "data" / "featured_papers.json"
DEEP_GEO_PATH = ROOT / "data" / "deep_geo_papers.json"
DEEP_CONTENT_DIR = ROOT / "data" / "deep_geo"
PAPERS_DIR = ROOT / "papers"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

LEGACY_DEEP_SLUGS = (
    "aihflevel",
    "apvs",
    "smc-fate",
    "b4galt2",
    "nlrp3-ici",
    "olink-dcm",
    "time-cart",
    "circadian-ihd",
    "icd-cart",
    "idebenone-ferroptosis",
)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_site_config():
    config = read_json(SITE_CONFIG_PATH)
    required = (
        "site_url",
        "researcher_name",
        "researcher_name_zh",
        "person_id",
        "orcid",
    )
    missing = [key for key in required if not str(config.get(key) or "").strip()]
    if missing:
        raise ValueError("Missing site configuration: " + ", ".join(missing))
    config["site_url"] = str(config["site_url"]).rstrip("/")
    return config


def validate_slug(value):
    slug = str(value or "").strip()
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"Invalid paper slug: {slug!r}")
    return slug


def doi_slug(doi):
    normalized = norm_doi(doi)
    if not normalized:
        return ""
    safe = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return validate_slug("doi-" + safe)


def fallback_slug(publication):
    seed = "|".join(
        [
            norm_title(publication.get("title")),
            str(publication.get("year") or ""),
            norm_title(publication.get("journal")),
            str(publication.get("type") or "").casefold(),
        ]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"work-{digest}"


def ensure_public_slugs(master):
    used = {}
    changed = False
    for publication in master:
        if is_withdrawn(publication):
            continue
        slug = str(publication.get("slug") or "").strip()
        if slug:
            slug = validate_slug(slug)
        else:
            slug = doi_slug(publication.get("doi")) or fallback_slug(publication)
            publication["slug"] = slug
            changed = True
        if slug in used:
            raise ValueError(
                f"Duplicate paper slug {slug!r}: {used[slug]!r} and "
                f"{publication.get('title')!r}"
            )
        used[slug] = publication.get("title")
    return changed


def controller_key(raw):
    if isinstance(raw, str):
        doi = norm_doi(raw)
        if not doi:
            raise ValueError("Controller string entries must be valid DOI values.")
        return "doi", doi
    if not isinstance(raw, dict):
        raise ValueError("Controller entries must be DOI strings or JSON objects.")
    doi = norm_doi(raw.get("doi"))
    if doi:
        return "doi", doi
    slug = str(raw.get("slug") or "").strip()
    if slug:
        return "slug", validate_slug(slug)
    raise ValueError("Controller entry must contain a DOI or stable slug.")


def controller_token(raw):
    kind, value = controller_key(raw)
    return f"{kind}:{value}"


def publication_token(publication):
    doi = norm_doi(publication.get("doi"))
    if doi:
        return f"doi:{doi}"
    return f"slug:{validate_slug(publication.get('slug'))}"


def controller_reference(publication):
    doi = norm_doi(publication.get("doi"))
    return {"doi": doi} if doi else {"slug": validate_slug(publication.get("slug"))}


def load_controller(path, *, featured=False):
    payload = read_json(path)
    if payload.get("version") != 1 or not isinstance(payload.get("papers"), list):
        raise ValueError(f"{Path(path).name} must contain version 1 and a papers array.")
    entries = []
    seen = set()
    for position, raw in enumerate(payload["papers"], start=1):
        token = controller_token(raw)
        if token in seen:
            raise ValueError(f"Duplicate controller entry at position {position}: {token}")
        seen.add(token)
        if featured:
            if isinstance(raw, str):
                raw = {"doi": norm_doi(raw)}
            normalized = controller_reference_from_key(raw)
            normalized["summary"] = str(raw.get("summary") or "").strip()
            entries.append(normalized)
        else:
            entries.append(controller_reference_from_key(raw))
    return entries


def controller_reference_from_key(raw):
    kind, value = controller_key(raw)
    return {kind: value}


def load_featured():
    return load_controller(FEATURED_PATH, featured=True)


def load_deep_geo():
    return load_controller(DEEP_GEO_PATH, featured=False)


def save_featured(entries):
    write_json(FEATURED_PATH, {"version": 1, "papers": entries})


def save_deep_geo(entries):
    write_json(DEEP_GEO_PATH, {"version": 1, "papers": entries})


def index_master(master):
    by_token = {}
    for publication in master:
        if is_withdrawn(publication):
            continue
        token = publication_token(publication)
        if token in by_token:
            raise ValueError(f"Duplicate publication identity: {token}")
        by_token[token] = publication
    return by_token


def validate_controller_entries(entries, master_by_token, label):
    for entry in entries:
        token = controller_token(entry)
        if token not in master_by_token:
            raise ValueError(f"{label} paper not found or withdrawn: {token}")


def deep_content_path(publication):
    return DEEP_CONTENT_DIR / f"{validate_slug(publication.get('slug'))}.json"
