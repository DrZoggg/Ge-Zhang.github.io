"""Reviewed search display text for existing canonical HTML routes."""

import html
import json
import re
from urllib.parse import urlsplit


SOURCE_PATH = "data/search_metadata.json"
SAMPLE_MAP_PATH = "assets/research/gse59867-sample-followup-map.html"
TITLE_MAX = 69
DESCRIPTION_MIN = 25
DESCRIPTION_MAX = 160
TAGS = {
    "title": re.compile(r"<title>(.*?)</title>", re.DOTALL),
    "description": re.compile(r'<meta name="description" content="([^"]*)">'),
}


def route(url):
    return urlsplit(url).path.lstrip("/") or "index.html"


def unique_fields(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise ValueError(f"Duplicate search metadata key: {key}")
        record[key] = value
    return record


def load(root):
    path = root / SOURCE_PATH
    if not path.is_file():
        return {}
    records = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_fields)
    if not isinstance(records, dict):
        raise ValueError(f"{SOURCE_PATH} must be an object keyed by HTML route")
    for path, fields in records.items():
        if not re.fullmatch(r"(?:[a-z0-9_-]+/)*[a-z0-9_-]+\.html", path):
            raise ValueError(f"Invalid search metadata route: {path}")
        if not isinstance(fields, dict) or not fields or fields.keys() - TAGS.keys():
            raise ValueError(f"Expected title or description for {path}")
        for field, text in fields.items():
            if (not isinstance(text, str) or not text or text != " ".join(text.split())
                    or re.search(r"[\x00-\x1f\x7f]|<[/!a-zA-Z]", text)
                    or "..." in text or "…" in text):
                raise ValueError(f"Invalid search {field} text for {path}")
            if field == "title" and len(text) > TITLE_MAX:
                raise ValueError(f"Search title exceeds {TITLE_MAX} characters for {path}")
            if field == "description" and (
                not DESCRIPTION_MIN <= len(text) <= DESCRIPTION_MAX or text[-1] not in ".!?"
            ):
                raise ValueError(
                    f"Search description for {path} must be a complete sentence of "
                    f"{DESCRIPTION_MIN}–{DESCRIPTION_MAX} characters"
                )
    return records


def head(page):
    before, opening, rest = page.partition("<head>")
    content, closing, after = rest.partition("</head>")
    if not opening or not closing or "<head>" in rest or "</head>" in after:
        raise ValueError("Expected exactly one HTML head for search metadata")
    return before + opening, content, closing + after


def project(page, fields):
    if not fields:
        return page
    prefix, content, suffix = head(page)
    for field, value in fields.items():
        escaped = html.escape(value, quote=(field == "description"))
        replacement = (
            f"<title>{escaped}</title>" if field == "title"
            else f'<meta name="description" content="{escaped}">'
        )
        content, count = TAGS[field].subn(lambda match: replacement, content)
        if count != 1:
            raise ValueError(f"Expected exactly one HTML search {field} tag, found {count}")
    return prefix + content + suffix


def read(page):
    _, content, _ = head(page)
    fields = {}
    for field, pattern in TAGS.items():
        values = pattern.findall(content)
        if len(values) != 1 or not values[0].strip():
            raise ValueError(f"Expected exactly one nonempty HTML search {field} tag")
        fields[field] = html.unescape(values[0])
    return fields


def validate_published(root, records, routes):
    unknown = records.keys() - routes
    if unknown:
        raise ValueError(f"Unknown search metadata routes: {', '.join(sorted(unknown))}")

    seen = {field: {} for field in TAGS}
    for path in sorted(routes):
        actual = read((root / path).read_text(encoding="utf-8"))
        for field, value in actual.items():
            key = value.casefold()
            previous = seen[field].get(key)
            if previous and (field in records.get(path, {}) or field in records.get(previous, {})):
                raise ValueError(f"Duplicate search {field} across {previous} and {path}")
            if previous is None:
                seen[field][key] = path
            expected = records.get(path, {}).get(field)
            if expected is not None and value != expected:
                raise ValueError(f"Search {field} differs from reviewed text for {path}")
