#!/usr/bin/env python3
"""Turn PMC / Europe PMC JATS XML into sectioned text, refusing metadata-only XML.

The failure this exists to stop: NCBI eFetch returns **HTTP 200** and a
well-formed `<pmc-articleset>` for articles whose publisher forbids XML
redistribution -- containing `<front>` metadata, no `<body>`, and the reason in
an XML *comment* that every standard parser discards. An agent that fetches,
parses, and reports "full text retrieved" has retrieved the title and author
list. See the hazard section of references/pmc.md.

So this script exits **2** when there is no `<body>`, and surfaces the discarded
comment as the explanation. Metadata is still emitted, clearly labelled as
metadata, so the caller can fall back to Europe PMC (a clean 404), Unpaywall, or
the abstract without a second fetch.

Handles both wrappers: eFetch's `<pmc-articleset><article>` and Europe PMC's bare
`<article>`.

    curl -s ".../efetch.fcgi?db=pmc&id=7029759&retmode=xml" | python3 jats_to_text.py -
    python3 jats_to_text.py article.xml --sections METHODS,RESULTS --text-only
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import InputError, collapse_ws, emit, fail, read_input  # noqa: E402

#: Tags whose text is not part of the reading order. `xref` and `label` are
#: excluded so citation markers and "Figure 1" labels do not land mid-sentence.
FOREIGN_TAGS = frozenset({"sub-article", "response", "article"})
SKIP_TAGS = frozenset({"xref", "label", "table-wrap", "graphic", "media", "inline-formula"}) | FOREIGN_TAGS

#: Block-level tags that must not run into their neighbours.
#:
#: NCBI serializes JATS with no whitespace between elements, so
#: `<title>Introduction</title><p>A mysterious illness...` concatenates to
#: "IntroductionA mysterious illness" unless a separator is inserted at these
#: boundaries. Inline tags (`italic`, `sup`, `xref`) are deliberately absent --
#: separating those would break words apart instead.
BLOCK_TAGS = frozenset(
    {
        "abstract",
        "body",
        "caption",
        "def-item",
        "disp-quote",
        "list-item",
        "p",
        "sec",
        "statement",
        "td",
        "th",
        "title",
        "tr",
    }
)

#: Publisher restriction notices arrive only as XML comments.
RESTRICTION_HINT = re.compile(r"does not allow|not allow downloading|restricted", re.IGNORECASE)


def parse(xml_text: str) -> ET.Element:
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as error:
        raise InputError(f"not parseable as XML: {error}") from error


def find_article(root: ET.Element) -> ET.Element:
    """The `<article>` element, whichever wrapper it arrived in."""
    if root.tag == "article":
        return root
    article = root.find(".//article")
    if article is None:
        raise InputError(
            f"no <article> element (root was <{root.tag}>); "
            "this is not a JATS document -- check whether the response was an error page"
        )
    return article


def comments_in(xml_text: str) -> list[str]:
    """XML comments, which ElementTree drops.

    Read from the raw text on purpose: the publisher-restriction notice that
    explains a missing `<body>` exists *only* as a comment, so parsing it away is
    what makes the failure silent.
    """
    return [collapse_ws(match) for match in re.findall(r"<!--(.*?)-->", xml_text, re.DOTALL)]


def element_text(element: ET.Element) -> str:
    """Flattened text of an element, skipping non-reading-order tags."""
    parts: list[str] = []

    def walk(node: ET.Element) -> None:
        if node.tag in SKIP_TAGS:
            # Keep the tail: text following an <xref> continues the sentence.
            if node.tail:
                parts.append(node.tail)
            return
        block = node.tag in BLOCK_TAGS
        if block:
            parts.append(" ")
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
        if block:
            parts.append(" ")
        if node.tail:
            parts.append(node.tail)

    walk(element)
    return collapse_ws("".join(parts))


def section_title(section: ET.Element) -> str:
    title = section.find("title")
    return element_text(title) if title is not None else ""


def collect_sections(body: ET.Element) -> list[dict[str, Any]]:
    """Keep top-level section text and interleaved direct body text in source order."""
    if not body.findall("sec"):
        text = element_text(body)
        return [{"title": "", "sec_type": None, "text": text}] if text else []
    sections: list[dict[str, Any]] = []
    pending: list[str] = []

    def flush() -> None:
        if pending:
            sections.append({"title": "", "sec_type": None, "text": collapse_ws(" ".join(pending))})
            pending.clear()

    for child in body:
        if child.tag == "sec":
            flush()
            sections.append({"title": section_title(child), "sec_type": child.get("sec-type"),
                             "text": element_text(child)})
        elif child.tag not in SKIP_TAGS:
            text = element_text(child)
            if text:
                pending.append(text)
    flush()
    return sections


#: JATS `pub-id-type` values, mapped to the field names this script emits.
#: PMC tags its own accession as `pmcid` (the bare `pmc` form appears in older
#: documents), alongside `pmcid-ver`/`pmcaid`/`pmcaiid` variants that are not the
#: canonical PMCID and must not be mistaken for it.
ID_TYPES = {"pmid": "pmid", "pmcid": "pmcid", "pmc": "pmcid", "doi": "doi"}


def extract_metadata(article: ET.Element) -> dict[str, Any]:
    front = article.find("front")
    metadata: dict[str, Any] = {
        "title": None,
        "journal": None,
        "pmid": None,
        "pmcid": None,
        "doi": None,
        "authors": [],
        "abstract": None,
    }
    if front is None:
        return metadata

    front = ET.fromstring(ET.tostring(front, encoding="unicode"))
    for parent in list(front.iter()):
        for child in list(parent):
            if child.tag in FOREIGN_TAGS:
                parent.remove(child)

    title = front.find(".//title-group/article-title")
    if title is not None:
        metadata["title"] = element_text(title)

    journal = front.find(".//journal-title")
    if journal is not None:
        metadata["journal"] = element_text(journal)

    # First occurrence per type wins. F1000Research and similar journals nest peer
    # review reports as sub-articles with their own DOIs; last-wins would report a
    # review's DOI as the article's.
    for article_id in front.findall(".//article-id"):
        field_name = ID_TYPES.get(article_id.get("pub-id-type") or "")
        if field_name and metadata[field_name] is None:
            metadata[field_name] = collapse_ws(article_id.text)

    for contributor in front.findall(".//contrib"):
        surname = contributor.find(".//surname")
        given = contributor.find(".//given-names")
        name = " ".join(
            part
            for part in (
                element_text(given) if given is not None else "",
                element_text(surname) if surname is not None else "",
            )
            if part
        )
        if name:
            metadata["authors"].append(name)

    abstract = front.find(".//abstract")
    if abstract is not None:
        metadata["abstract"] = element_text(abstract)

    return metadata



def owned_nodes(root: ET.Element):
    """Walk one article's content without entering foreign sub-articles/responses."""
    yield root
    for child in root:
        if child.tag not in FOREIGN_TAGS:
            yield from owned_nodes(child)


def element_locators(article: ET.Element) -> dict[ET.Element, str]:
    paths = {article: "article"}

    def walk(parent: ET.Element) -> None:
        counts: dict[str, int] = {}
        for child in parent:
            counts[child.tag] = counts.get(child.tag, 0) + 1
            if child.tag in FOREIGN_TAGS:
                continue
            paths[child] = f"{paths[parent]}/{child.tag}[{counts[child.tag]}]"
            walk(child)

    walk(article)
    return paths


def declared_supplementary_material(article: ET.Element) -> list[dict[str, Any]]:
    """Report article-owned attachment declarations without resolving or opening them."""
    paths = element_locators(article)
    declarations = []
    for node in paths:
        if node.tag not in {"supplementary-material", "inline-supplementary-material"}:
            continue
        label = node.find("label")
        for attachment in (node, *node):
            if attachment is not node and attachment.tag not in {"media", "graphic"}:
                continue
            href = attachment.get("{http://www.w3.org/1999/xlink}href") or attachment.get("href")
            if not href or not href.strip() or not href.isprintable():
                continue
            declarations.append({
                "supplement_id": node.get("id"),
                "label": collapse_ws("".join(label.itertext())) if label is not None else None,
                "locator": paths[attachment],
                "declared_href": href,
                "attachment_reading_status": "not_observed_by_parser",
            })
    return declarations


def bibliography(article: ET.Element) -> list[dict[str, Any]]:
    """Explicit identifiers from reference lists in the owning article only."""
    paths = element_locators(article)
    records: list[dict[str, Any]] = []
    for container in owned_nodes(article):
        if container.tag != "ref-list":
            continue
        for ref in container.findall("ref"):
            ref_id = ref.get("id")
            citation = ref.find("mixed-citation")
            if citation is None:
                citation = ref.find("element-citation")
            # JATS alternatives are representations of this one citation, not
            # additional works. Keep legacy direct-citation selection unchanged.
            citations = [citation] if citation is not None else [
                child for alternatives in ref.findall("citation-alternatives")
                for child in alternatives
                if child.tag in {"element-citation", "mixed-citation", "nlm-citation"}]
            identities: dict[str, str] = {}
            sources: list[dict[str, str]] = []
            issues: list[dict[str, str]] = []
            candidates: dict[str, list[dict[str, str]]] = {}
            conflicts: dict[str, Any] = {}
            for representation in citations:
                for node in owned_nodes(representation):
                    if node.tag not in {"pub-id", "ext-link"}:
                        continue
                    kind = node.get("pub-id-type" if node.tag == "pub-id" else "ext-link-type")
                    if kind not in {"doi", "pmid", "pmcid", "pmc"}:
                        continue
                    field = "pmcid" if kind == "pmc" else kind
                    value = collapse_ws(node.text) if node.tag == "pub-id" else collapse_ws(
                        node.get("{http://www.w3.org/1999/xlink}href") or node.get("href") or node.text)
                    if field == "doi":
                        value = re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE)
                        if "://" in value:
                            try:
                                url = urlsplit(value)
                                valid_url = (url.scheme.lower() in {"http", "https"}
                                    and url.hostname in {"doi.org", "dx.doi.org"}
                                    and not url.username and not url.password and not url.query and not url.fragment
                                    and url.port in {None, 80, 443})
                                value = unquote(url.path[1:]) if valid_url else ""
                            except ValueError:
                                value = ""
                        valid = re.fullmatch(r"10\.\d{4,9}/\S+", value) is not None
                    elif field == "pmid":
                        valid = re.fullmatch(r"\d+", value) is not None
                    else:
                        value = value.upper()
                        valid = re.fullmatch(r"PMC\d+", value) is not None
                    if not valid:
                        issues.append({"field": field, "reason": "invalid_explicit_identifier",
                                       "locator": paths[node]})
                        continue
                    values = candidates.setdefault(field, [])
                    values.append({"value": value, "encoding": node.tag, "locator": paths[node]})
                    if len({item["value"].casefold() for item in values}) > 1:
                        identities.pop(field, None)
                        conflicts[field] = {"status": "unresolved", "candidates": values}
                    else:
                        # Preserve a clean field's first spelling; never choose a conflicting value.
                        identities.setdefault(field, value)
                    sources.append({"field": field, "encoding": node.tag, "locator": paths[node]})
            title = next((node for item in citations
                          if (node := item.find("article-title")) is not None), None)
            publication_type = (citation.get("publication-type") if citation is not None else
                                next((item.get("publication-type") for item in citations
                                      if item.get("publication-type")), None))
            record = {"reference_id": ref_id, "label": collapse_ws(ref.findtext("label")),
                "title": element_text(title) if title is not None else None,
                "publication_type": publication_type,
                "identifiers": identities, "reference_locator": paths[ref],
                "identifier_sources": sources, "identifier_issues": issues,
                "citation_available": bool(citations)}
            if conflicts:
                record["identifier_conflicts"] = conflicts
            records.append(record)
    locations: dict[str, list[str]] = {}
    for record in records:
        if record["reference_id"]:
            locations.setdefault(record["reference_id"], []).append(record["reference_locator"])
    for record in records:
        matches = locations.get(record["reference_id"], [])
        if len(matches) > 1:
            record["reference_id_status"] = "ambiguous_duplicate"
            record["reference_id_candidate_locators"] = matches
    return records


def citation_ids(paragraph: ET.Element, records: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """Literal xrefs plus complete, unambiguous numeric-label ranges; never ID-order guesses."""
    labels: dict[int, list[str]] = {}
    for ref in records:
        match = re.fullmatch(r"(\d+)\.?", ref["label"])
        if match and ref["reference_id"] and ref.get("reference_id_status") != "ambiguous_duplicate":
            labels.setdefault(int(match[1]), []).append(ref["reference_id"])
    parents = {child: parent for parent in owned_nodes(paragraph) for child in parent
               if child.tag not in FOREIGN_TAGS}
    ids: list[str] = []
    ranges: list[dict[str, Any]] = []
    for xref in owned_nodes(paragraph):
        if xref.tag != "xref" or xref.get("ref-type") != "bibr":
            continue
        ids.extend((xref.get("rid") or "").split())
        if not re.fullmatch(r"\s*[-–−]\s*", xref.tail or ""):
            continue
        siblings = list(parents[xref])
        index = siblings.index(xref)
        right = siblings[index + 1] if index + 1 < len(siblings) else None
        if right is None or right.tag != "xref" or right.get("ref-type") != "bibr":
            continue
        left_text = collapse_ws("".join(xref.itertext()))
        right_text = collapse_ws("".join(right.itertext()))
        event: dict[str, Any] = {"endpoint_reference_ids": [xref.get("rid"), right.get("rid")],
                                 "endpoint_labels": [left_text, right_text], "status": "unresolved"}
        if left_text.isdecimal() and right_text.isdecimal():
            lo, hi = int(left_text), int(right_text)
            if (0 < hi - lo <= 1000 and all(len(labels.get(n, [])) == 1 for n in range(lo, hi + 1))
                    and labels[lo][0] == xref.get("rid") and labels[hi][0] == right.get("rid")):
                resolved = [labels[n][0] for n in range(lo, hi + 1)]
                ids.extend(resolved)
                event.update(status="resolved", reference_ids=resolved, method="explicit_numeric_label_range")
        if event["status"] != "resolved":
            event["reason"] = "nonascending_incomplete_or_ambiguous_numeric_label_range"
        ranges.append(event)
    return list(dict.fromkeys(ids)), ranges


def collect_citation_contexts(article: ET.Element, body: ET.Element, wanted: list[str]) -> list[dict[str, Any]]:
    """Keep source-relative citation groups, not assertions of original reading/use."""
    records = bibliography(article)
    refs = {ref["reference_id"]: ref for ref in records
            if ref["reference_id"] and ref.get("reference_id_status") != "ambiguous_duplicate"}
    ambiguous_ids = {ref["reference_id"]: ref["reference_id_candidate_locators"] for ref in records
                     if ref.get("reference_id_status") == "ambiguous_duplicate"}
    paths = element_locators(article)
    metadata = extract_metadata(article)
    source = {"identifiers": {key: metadata[key] for key in ("doi", "pmid", "pmcid")},
              "publication_type": article.get("article-type")}
    contexts: list[dict[str, Any]] = []
    blocks: list[ET.Element] = [body] if not wanted else []
    for outer in body.findall("sec"):
        if not wanted or matches({"title": section_title(outer), "sec_type": outer.get("sec-type")}, wanted):
            blocks.extend(node for node in owned_nodes(outer) if node.tag == "sec")
    # A body without section children is already handled by the body block.
    for block in blocks:
        for index, paragraph in enumerate(block.findall("p"), start=1):
            ref_ids, ranges = citation_ids(paragraph, records)
            if not ref_ids:
                continue
            unresolved = [rid for rid in ref_ids if rid not in refs or not refs[rid]["citation_available"]]
            cited = [dict(refs[rid]) for rid in ref_ids if rid in refs and refs[rid]["citation_available"]]
            context = {"section_id": block.get("id"), "section_title": section_title(block),
                "paragraph_index": index, "text": element_text(paragraph), "reference_ids": ref_ids,
                "references": cited, "unresolved_reference_ids": unresolved,
                "attribution": "co-cited group; individual subclaim support requires reading each cited study",
                "source_article": source, "section_locator": paths[block],
                "paragraph_locator": paths[paragraph], "range_expansions": ranges,
                "original_reading_status": "not_observed_by_parser", "draft_use_status": "not_observed_by_parser"}
            link_issues = [{"reference_id": rid, "reason": "ambiguous_duplicate_reference_id",
                            "candidate_locators": ambiguous_ids[rid]} for rid in ref_ids if rid in ambiguous_ids]
            if link_issues:
                context["reference_link_issues"] = link_issues
            contexts.append(context)
    return contexts


def bibliography_sidecar(article: ET.Element, body: ET.Element, contexts: list[dict[str, Any]], wanted: list[str]) -> list[dict[str, Any]]:
    all_contexts = collect_citation_contexts(article, body, []) if wanted else contexts
    all_ids = {rid for group in all_contexts for rid in group["reference_ids"]}
    selected = {rid for group in contexts for rid in group["reference_ids"]}
    ambiguous = any(event["status"] != "resolved" for group in all_contexts for event in group["range_expansions"])
    records = bibliography(article)
    for ref in records:
        rid = ref["reference_id"]
        ref["context_status"] = ("missing_reference_id" if not rid else
            "unresolved_duplicate_reference_id" if ref.get("reference_id_status") == "ambiguous_duplicate" else
            "cited_in_selected_contexts" if rid in selected else
            "cited_outside_selected_contexts" if rid in all_ids else
            "not_linked_with_unresolved_ranges" if ambiguous else "uncited_in_scanned_body_paragraphs")
        ref["original_reading_status"] = "not_observed_by_parser"
        ref["draft_use_status"] = "not_observed_by_parser"
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert PMC/Europe PMC JATS XML to sectioned text. Exits 2 when the document "
            "carries no <body>, which is how eFetch signals a non-open-access article "
            "while still returning HTTP 200."
        ),
        epilog="python3 %(prog)s article.xml --sections METHODS,RESULTS",
    )
    parser.add_argument("source", help="path to a JATS XML file, or - for stdin")
    parser.add_argument("-o", "--output", help="write here instead of stdout")
    parser.add_argument(
        "--sections",
        help=(
            "comma-separated section filter, matched case-insensitively against the "
            "section title and sec-type (e.g. METHODS,RESULTS)"
        ),
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="emit plain text rather than JSON",
    )
    parser.add_argument(
        "--allow-metadata-only",
        action="store_true",
        help=(
            "exit 0 instead of 2 when there is no <body>. Only for callers that have "
            "explicitly decided metadata is enough -- the default refusal is the point."
        ),
    )
    parser.add_argument("--include-cited-references", action="store_true",
        help="retain selected-section citation groups and cited-work identity as a separate sidecar")
    parser.add_argument("--include-supplementary-material", action="store_true",
        help="retain declared attachment locators in JSON without resolving or reading the files")
    return parser


def matches(section: dict[str, Any], wanted: list[str]) -> bool:
    haystack = f"{section['title']} {section['sec_type'] or ''}".lower()
    return any(want in haystack for want in wanted)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        xml_text = read_input(args.source)
        root = parse(xml_text)
        article = find_article(root)
    except InputError as error:
        fail(str(error))

    metadata = extract_metadata(article)
    body = article.find("body")

    if body is None:
        comments = comments_in(xml_text)
        restriction = next((c for c in comments if RESTRICTION_HINT.search(c)), None)
        payload = {
            "full_text_available": False,
            "reason": restriction
            or "document has no <body> element and gave no stated reason",
            "metadata": metadata,
            "guidance": (
                "This is metadata only, not full text. Do not present it as the article. "
                "Try Europe PMC /{PMCID}/fullTextXML (returns 404 rather than a bodyless 200), "
                "consult PMC Article Datasets for supported bulk access, or fall back to "
                "Unpaywall/CORE for an open-access copy."
            ),
        }
        if comments:
            payload["xml_comments"] = comments
        emit(payload, args.output)
        if args.allow_metadata_only:
            return 0
        fail(
            "no <body> element: this document is metadata only, not full text"
            + (f" -- {restriction}" if restriction else ""),
            code=2,
        )

    sections = collect_sections(body)
    if args.sections:
        wanted = [part.strip().lower() for part in args.sections.split(",") if part.strip()]
        selected = [section for section in sections if matches(section, wanted)]
        if not selected:
            available = ", ".join(s["title"] or s["sec_type"] or "(untitled)" for s in sections)
            fail(f"no section matched {args.sections!r}; available: {available}")
        sections = selected

    if args.text_only:
        blocks = []
        if metadata["title"]:
            blocks.append(metadata["title"])
        for section in sections:
            heading = section["title"]
            blocks.append(f"{heading}\n{section['text']}" if heading else section["text"])
        text = "\n\n".join(blocks) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0

    payload = {
            "full_text_available": True,
            "metadata": metadata,
            "section_count": len(sections),
            "word_count": sum(len(section["text"].split()) for section in sections),
            "sections": sections,
        }
    if args.include_cited_references:
        wanted = [part.strip().lower() for part in (args.sections or "").split(",") if part.strip()]
        try:
            payload["citation_contexts"] = collect_citation_contexts(article, body, wanted)
            payload["bibliography_references"] = bibliography_sidecar(article, body, payload["citation_contexts"], wanted)
        except InputError as error:
            fail(str(error))
    if args.include_supplementary_material:
        payload["supplementary_material"] = declared_supplementary_material(article)
    emit(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
