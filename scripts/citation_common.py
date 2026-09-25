"""Deterministic, master-led citation records and static exports."""

import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from site_common import validate_slug
from sync_common import ROOT, norm_doi, publication_authors


CITATION_METADATA_PATH = ROOT / "data" / "citation_metadata.json"
CITATIONS_DIR = ROOT / "citations"
ENHANCEMENT_FIELDS = {
    "publication_date", "journal_abbrev", "issn", "eissn", "volume", "issue",
    "first_page", "last_page", "article_number", "publisher", "pmid", "pmcid",
    "verified_sources",
}
PLACEHOLDERS = {"unknown", "n/a", "pending", "0", "null", "none", "-", "not available"}
EXPORT_SUFFIXES = (".bib", ".ris", ".csl.json")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate citation metadata key: {key}")
        result[key] = value
    return result


def _verified_text(value, label):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty trimmed text.")
    if value.casefold() in PLACEHOLDERS:
        raise ValueError(f"{label} must not be a placeholder.")
    return value


def _valid_doi(doi):
    return bool(re.fullmatch(r"10\.\d{4,9}/\S+", doi)) and doi == norm_doi(doi)


def load_citation_metadata(publications, path=CITATION_METADATA_PATH):
    """Validate optional, DOI-keyed bibliographic enhancements against public master."""
    path = Path(path)
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
    if not isinstance(payload, dict) or set(payload) != {"version", "papers"}:
        raise ValueError("citation_metadata.json must contain version and papers only.")
    if type(payload["version"]) is not int or payload["version"] != 1:
        raise ValueError("citation_metadata.json version must be 1.")
    papers = payload["papers"]
    if not isinstance(papers, dict):
        raise ValueError("citation_metadata.json papers must be a DOI-keyed object.")
    public_by_doi = {
        norm_doi(item.get("doi")): item
        for item in publications if norm_doi(item.get("doi"))
    }
    normalized = set()
    for doi, fields in papers.items():
        if not _valid_doi(doi) or doi in normalized:
            raise ValueError(f"Citation metadata DOI key is invalid or duplicated: {doi!r}")
        normalized.add(doi)
        publication = public_by_doi.get(doi)
        if publication is None:
            raise ValueError(f"Citation metadata DOI does not resolve to a public work: {doi}")
        if not isinstance(fields, dict) or not fields or set(fields) - ENHANCEMENT_FIELDS:
            raise ValueError(f"Citation metadata for {doi} contains unsupported or identity fields.")
        for key, value in fields.items():
            if key == "verified_sources":
                if not isinstance(value, list) or not value:
                    raise ValueError(f"Citation metadata {doi} verified_sources must be non-empty.")
                sources = [_verified_text(url, f"{doi} verified source") for url in value]
                if len(sources) != len(set(sources)):
                    raise ValueError(f"Citation metadata {doi} verified_sources are duplicated.")
                if any(urlparse(url).scheme != "https" or not urlparse(url).netloc
                       for url in sources):
                    raise ValueError(f"Citation metadata {doi} verified_sources must use HTTPS.")
            else:
                _verified_text(value, f"Citation metadata {doi} {key}")
        if "publication_date" in fields:
            value = fields["publication_date"]
            try:
                parsed = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"Citation metadata {doi} publication_date is invalid.") from exc
            if parsed.isoformat() != value or parsed.year != publication.get("year"):
                raise ValueError(f"Citation metadata {doi} publication_date disagrees with master year.")
        for key in ("issn", "eissn"):
            if key in fields and not re.fullmatch(r"\d{4}-\d{3}[\dX]", fields[key]):
                raise ValueError(f"Citation metadata {doi} {key} syntax is invalid.")
        if "pmid" in fields and not re.fullmatch(r"[1-9]\d*", fields["pmid"]):
            raise ValueError(f"Citation metadata {doi} PMID syntax is invalid.")
        if "pmcid" in fields and not re.fullmatch(r"PMC[1-9]\d*", fields["pmcid"]):
            raise ValueError(f"Citation metadata {doi} PMCID syntax is invalid.")
        first, last = fields.get("first_page"), fields.get("last_page")
        if first and last and first.isdecimal() and last.isdecimal() and int(first) > int(last):
            raise ValueError(f"Citation metadata {doi} page range is inverted.")
    return papers


def citation_skip_reason(publication):
    if publication.get("type") not in {"Article", "Preprint"}:
        return f"unsupported type: {publication.get('type') or 'missing'}"
    missing = [
        key for key in ("title", "journal", "year", "doi", "authors")
        if not publication.get(key)
    ]
    if missing:
        return "missing verified " + ", ".join(missing)
    if not _valid_doi(norm_doi(publication["doi"])):
        return "invalid DOI"
    if not publication_authors(publication):
        return "missing verified authors"
    validate_slug(publication.get("slug"))
    return ""


def citation_record(publication, enhancement, site_root):
    """Keep identity exclusively from master; enhancement contributes allowed details."""
    reason = citation_skip_reason(publication)
    if reason:
        return None
    doi = norm_doi(publication["doi"])
    slug = validate_slug(publication["slug"])
    record = {
        "id": slug,
        "type": publication["type"],
        "title": publication["title"],
        "authors": publication_authors(publication),
        "journal": publication["journal"],
        "year": publication["year"],
        "doi": doi,
        "canonical_url": f"{site_root}/papers/{slug}.html",
        "doi_url": f"https://doi.org/{doi}",
    }
    record.update(enhancement.get(doi, {}))
    return record


def citation_files(record):
    slug = validate_slug(record["id"])
    return {
        "bib": f"{slug}.bib",
        "ris": f"{slug}.ris",
        "csl": f"{slug}.csl.json",
    }


def citation_plain_text(record):
    authors = ", ".join(record["authors"])
    publication = f"{record['journal']}. {record['year']}"
    if record.get("volume"):
        publication += f";{record['volume']}"
        if record.get("issue"):
            publication += f"({record['issue']})"
        if record.get("first_page"):
            publication += f":{record['first_page']}"
            if record.get("last_page"):
                publication += f"–{record['last_page']}"
        elif record.get("article_number"):
            publication += f":{record['article_number']}"
    publication += "."
    return f"{authors}. {record['title']}. {publication} {record['doi_url']}"


def render_cite_html(record):
    slug = validate_slug(record["id"])
    files = citation_files(record)
    plain = html.escape(citation_plain_text(record))
    doi = html.escape(record["doi_url"], quote=True)
    return (
        '<section id="cite-this-paper" class="card"><h2>Cite this paper</h2>'
        '<h3>Plain citation</h3>'
        f'<p id="plain-citation-{slug}">{plain}</p>'
        '<p class="meta">Author-controlled citation; verify against the publisher '
        'version of record.</p><div class="links">'
        f'<button type="button" class="btn" data-copy-citation="plain-citation-{slug}" '
        'hidden>Copy citation</button>'
        f'<a class="btn" href="../citations/{files["bib"]}">BibTeX</a>'
        f'<a class="btn" href="../citations/{files["ris"]}">RIS / EndNote</a>'
        f'<a class="btn" href="../citations/{files["csl"]}">CSL JSON</a>'
        f'<a class="btn" href="{doi}">DOI</a>'
        '</div></section>'
    )


def _bib_text(value):
    escaped = {
        "\\": "\\textbackslash{}", "{": "\\{", "}": "\\}",
        "&": "\\&", "%": "\\%", "#": "\\#", "_": "\\_", "$": "\\$",
    }
    return "".join(escaped.get(character, character) for character in str(value))


def render_bibtex(record):
    kind = "article" if record["type"] == "Article" else "misc"
    fields = [
        ("title", record["title"]),
        ("author", " and ".join(record["authors"])),
        ("journal" if kind == "article" else "howpublished", record["journal"]),
        ("year", str(record["year"])),
    ]
    for key, output_key in (
        ("volume", "volume"), ("issue", "number"), ("publisher", "publisher")
    ):
        if record.get(key):
            fields.append((output_key, record[key]))
    if record.get("first_page"):
        pages = record["first_page"]
        if record.get("last_page"):
            pages += "--" + record["last_page"]
        fields.append(("pages", pages))
    elif record.get("article_number"):
        fields.append(("eid", record["article_number"]))
    fields.extend([("doi", record["doi"]), ("url", record["doi_url"])])
    if record.get("issn") or record.get("eissn"):
        fields.append(("issn", record.get("issn") or record["eissn"]))
    body = ",\n".join(f"  {key} = {{{_bib_text(value)}}}" for key, value in fields)
    return f"@{kind}{{{record['id']},\n{body}\n}}\n"


def render_ris(record):
    lines = ["TY  - JOUR" if record["type"] == "Article" else "TY  - GEN"]
    lines.extend(f"AU  - {author}" for author in record["authors"])
    lines.extend([
        f"TI  - {record['title']}",
        f"JO  - {record['journal']}",
        f"PY  - {record['year']}",
    ])
    if record.get("publication_date"):
        lines.append("DA  - " + record["publication_date"].replace("-", "/"))
    for key, tag in (
        ("volume", "VL"), ("issue", "IS"), ("first_page", "SP"),
        ("last_page", "EP"), ("issn", "SN"), ("eissn", "SN"),
        ("publisher", "PB"),
    ):
        if record.get(key):
            lines.append(f"{tag}  - {record[key]}")
    lines.extend([
        f"DO  - {record['doi']}",
        f"UR  - {record['doi_url']}",
        "ER  -",
        "",
    ])
    return "\n".join(lines)


def render_csl_json(record):
    issued = [record["year"]]
    if record.get("publication_date"):
        issued = [int(part) for part in record["publication_date"].split("-")]
    result = {
        "id": record["id"],
        "type": "article-journal" if record["type"] == "Article" else "manuscript",
        "title": record["title"],
        "author": [{"literal": name} for name in record["authors"]],
        "container-title": record["journal"],
        "issued": {"date-parts": [issued]},
        "DOI": record["doi"],
        "URL": record["doi_url"],
    }
    for source, destination in (
        ("volume", "volume"), ("issue", "issue"), ("publisher", "publisher")
    ):
        if record.get(source):
            result[destination] = record[source]
    if record.get("first_page"):
        result["page"] = record["first_page"] + (
            "-" + record["last_page"] if record.get("last_page") else ""
        )
    elif record.get("article_number"):
        result["article-number"] = record["article_number"]
    if record.get("issn") or record.get("eissn"):
        result["ISSN"] = record.get("issn") or record["eissn"]
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"
