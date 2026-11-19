"""Deterministic, master-led citation records and static exports."""

import html
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from site_common import validate_slug, load_site_config
from sync_common import ROOT, norm_doi, publication_authors
from official_abstracts import abstract_text


CITATION_METADATA_PATH = ROOT / "data" / "citation_metadata.json"
CITATIONS_DIR = ROOT / "citations"
ENHANCEMENT_FIELDS = {
    "publication_date", "journal_abbrev", "issn", "eissn", "volume", "issue",
    "first_page", "last_page", "article_number", "publisher", "pmid", "pmcid",
    "verified_sources", "online_publication_date", "ris_authors", "ris_article_locator",
    "fulltext_pdf", "official_abstract", "highwire_article_locator",
}
PLACEHOLDERS = {"unknown", "n/a", "pending", "0", "null", "none", "-", "not available"}
EXPORT_SUFFIXES = (".bib", ".ris", ".csl.json")
JOURNAL_PUBLICATION_TYPES = {"Article", "Letter", "Correspondence"}
# Explicitly reviewed publisher-accepted source; other hosted PDFs remain VoR-only.
REVIEWED_ACCEPTED_PDFS = {
    "10.1097/re9.0000000000000037": "9cf98783d861852e896eb58b1d2e1a6d55761248b2161ddd5ee58c753eea7511",
}


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


def validate_fulltext_pdf(value, publication, verified_sources):
    """Associate reviewed CC BY source bytes and their actual publication version."""
    required = {"url", "source_url", "sha256", "license_url", "version"}
    if (not isinstance(value, dict) or set(value) != required
            or any(not isinstance(text, str) for text in value.values())):
        raise ValueError("Hosted fulltext PDF requires explicit provenance.")
    site = load_site_config()["site_url"].rstrip("/")
    slug = validate_slug(publication["slug"])
    source = urlparse(value["source_url"])
    accepted_hash = REVIEWED_ACCEPTED_PDFS.get(norm_doi(publication["doi"]))
    expected_version = "publisher_accepted_manuscript" if accepted_hash else "version_of_record"
    if (value["url"] != f"{site}/papers/{slug}.pdf"
            or value["version"] != expected_version
            or (accepted_hash and value["sha256"] != accepted_hash)
            or value["license_url"] != "https://creativecommons.org/licenses/by/4.0/"
            or not value["source_url"].startswith(site + "/assets/fulltext/")
            or source.query or source.fragment or source.username or source.password
            or not source.path.endswith(".pdf")
            or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"])):
        raise ValueError("Hosted fulltext PDF must retain its reviewed version, licence and same-directory URL.")
    if not {value["source_url"], value["license_url"],
            f"https://doi.org/{publication['doi']}"}.issubset(verified_sources):
        raise ValueError("Hosted fulltext PDF requires DOI, source and licence references.")
    original = (ROOT / source.path.lstrip("/")).resolve()
    sibling = ROOT / "papers" / f"{slug}.pdf"
    if not original.is_relative_to((ROOT / "assets" / "fulltext").resolve()):
        raise ValueError("Hosted fulltext source must stay within the public fulltext directory.")
    for path in [original, sibling]:
        data = path.read_bytes()
        if not data.startswith(b"%PDF-") or hashlib.sha256(data).hexdigest() != value["sha256"]:
            raise ValueError("Hosted fulltext PDF differs from its reviewed source bytes.")


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
            elif key == "fulltext_pdf":
                validate_fulltext_pdf(value, publication, fields.get("verified_sources", []))
            elif key == "highwire_article_locator":
                if (not isinstance(value, dict)
                        or set(value) != {"value", "source_url"}
                        or not fields.get("article_number")
                        or value["value"] != fields["article_number"]
                        or value["source_url"] not in fields.get("verified_sources", [])):
                    raise ValueError(f"Citation metadata {doi} Highwire locator requires a sourced article number.")
            elif key == "official_abstract":
                required = {"text", "source_url", "source_version", "license_url", "verbatim"}
                sources = fields.get("verified_sources", [])
                if (not isinstance(value, dict) or set(value) != required
                        or value.get("verbatim") is not True
                        or value.get("source_version") not in ("publisher_accepted_manuscript", "version_of_record")
                        or value.get("source_url") not in sources
                        or value.get("license_url") != "https://creativecommons.org/licenses/by/4.0/"
                        or value["license_url"] not in sources):
                    raise ValueError(f"Citation metadata {doi} abstract requires explicit verified source and licence.")
                text = _verified_text(value["text"], f"Citation metadata {doi} official abstract")
                # This invited Letter has no formal abstract; its author explanation is separate.
                if doi == "10.1002/ctm2.70900" or "\n" in text or "\r" in text:
                    raise ValueError(f"Citation metadata {doi} has no supported single-paragraph official abstract.")
            elif key == "ris_authors":
                authors = publication_authors(publication)
                if (not isinstance(value, list) or len(value) != len(authors)
                        or not authors or not fields.get("verified_sources")):
                    raise ValueError(f"Citation metadata {doi} requires sourced RIS names for every author.")
                for name, display_name in zip(value, authors):
                    if not isinstance(name, dict) or set(name) != {"family", "given"}:
                        raise ValueError(f"Citation metadata {doi} has invalid RIS name parts.")
                    family = _verified_text(name["family"], f"{doi} RIS family name")
                    given = _verified_text(name["given"], f"{doi} RIS given name")
                    if (any("," in part or not part.isprintable() for part in (family, given))
                            or f"{given} {family}" != display_name):
                        raise ValueError(f"Citation metadata {doi} RIS name parts disagree with master authors.")
            else:
                _verified_text(value, f"Citation metadata {doi} {key}")
        if "online_publication_date" in fields:
            value = fields["online_publication_date"]
            try:
                parsed = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"Citation metadata {doi} online_publication_date is invalid.") from exc
            if parsed.isoformat() != value:
                raise ValueError(f"Citation metadata {doi} online_publication_date must use YYYY-MM-DD.")
            if not fields.get("verified_sources"):
                raise ValueError(f"Citation metadata {doi} online_publication_date requires verified_sources.")
        if "publication_date" in fields:
            value = fields["publication_date"]
            # Validate a month against the calendar without exporting a fabricated day.
            calendar_date = value + "-01" if len(value) == 7 else value
            try:
                parsed = date.fromisoformat(calendar_date)
            except ValueError as exc:
                raise ValueError(f"Citation metadata {doi} publication_date is invalid.") from exc
            if parsed.isoformat() != calendar_date or parsed.year != publication.get("year"):
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
        if "ris_article_locator" in fields and (
            first or last or not fields.get("verified_sources")
            or fields["ris_article_locator"] != fields.get("article_number")
        ):
            raise ValueError(f"Citation metadata {doi} RIS locator requires a sourced article number without pagination.")
    return papers


def highwire_first_page(record):
    """Use the verified publisher locator only for unpaginated HTML records."""
    if record.get("first_page") or record.get("last_page"):
        return record.get("first_page")
    return record.get("highwire_article_locator", {}).get("value")


def citation_skip_reason(publication):
    if publication.get("type") not in JOURNAL_PUBLICATION_TYPES | {"Preprint"}:
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


def citation_record(publication, enhancement, site_root, official_abstract=None):
    """Keep master identity; optional abstract comes from load_official_abstracts."""
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
    if official_abstract is not None:
        record["official_abstract_text"] = abstract_text(official_abstract)
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
    elif record.get("article_number"):
        publication += f"; article {record['article_number']}"
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


def _bib_authors(authors):
    """Protect existing hyphenated name tokens without inferring name parts."""
    def token(match):
        value = match.group()
        escaped = _bib_text(value)
        return "{" + escaped + "}" if "-" in value else escaped

    return " and ".join(re.sub(r"\S+", token, author) for author in authors)


def render_bibtex(record):
    kind = "article" if record["type"] in JOURNAL_PUBLICATION_TYPES else "misc"
    fields = [
        ("title", record["title"]),
        ("author", record["authors"]),
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
    if record.get("article_number"):
        fields.append(("eid", record["article_number"]))
    if record["type"] in JOURNAL_PUBLICATION_TYPES - {"Article"}:
        fields.append(("note", record["type"]))
    fields.extend([("doi", record["doi"]), ("url", record["doi_url"])])
    if record.get("issn") or record.get("eissn"):
        fields.append(("issn", record.get("issn") or record["eissn"]))
    body = ",\n".join(
        f"  {key} = {{{_bib_authors(value) if key == 'author' else _bib_text(value)}}}"
        for key, value in fields
    )
    return f"@{kind}{{{record['id']},\n{body}\n}}\n"


def citation_abstract_text(record):
    """Only explicit verified sources; never infer an abstract from a description."""
    if "official_abstract_text" in record:
        return record["official_abstract_text"]
    return record.get("official_abstract", {}).get("text")


def render_ris(record):
    lines = ["TY  - JOUR" if record["type"] in JOURNAL_PUBLICATION_TYPES else "TY  - GEN"]
    authors = record["authors"]
    if "ris_authors" in record:
        authors = [f"{name['family']}, {name['given']}" for name in record["ris_authors"]]
    lines.extend(f"AU  - {author}" for author in authors)
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
    if record.get("article_number"):
        if record.get("ris_article_locator"):
            lines.append(f"SP  - {record['ris_article_locator']}")
        lines.append(f"C7  - {record['article_number']}")
    if record["type"] in JOURNAL_PUBLICATION_TYPES - {"Article"}:
        lines.append(f"M3  - {record['type']}")
    abstract = citation_abstract_text(record)
    if abstract:
        # Keep section labels/words while folding line breaks into one RIS field.
        lines.append("AB  - " + abstract.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " "))
    if record.get("fulltext_pdf"):
        lines.append(f"L1  - {record['fulltext_pdf']['url']}")
        if record["fulltext_pdf"]["version"] == "publisher_accepted_manuscript":
            lines.append("N1  - Full text PDF: publisher accepted manuscript (Publish Ahead of Print).")
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
    # Reuse the complete name pairs already verified against the publication.
    authors = record.get("ris_authors")
    if authors is None:
        authors = [{"literal": name} for name in record["authors"]]
    result = {
        "id": record["id"],
        "type": "article-journal" if record["type"] in JOURNAL_PUBLICATION_TYPES else "manuscript",
        "title": record["title"],
        "author": authors,
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
    if record.get("article_number"):
        result["number"] = record["article_number"]
    if record["type"] in JOURNAL_PUBLICATION_TYPES - {"Article"}:
        result["genre"] = record["type"]
    if record.get("issn") or record.get("eissn"):
        result["ISSN"] = record.get("issn") or record["eissn"]
    abstract = citation_abstract_text(record)
    if abstract:
        result["abstract"] = abstract
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"
