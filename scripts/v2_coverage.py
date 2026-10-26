"""Required V2 module coverage, with explicit frozen field-source exceptions.

This is an engineering transcription check, not a new scientific review.
The existing renderer and content/citation validators remain authoritative.
"""
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from build_publications import (
    validate_deep_v2_content, validate_citation_layer, validate_citation_pilot,
    v2_article_label, v2_study_heading, paper_schema,
)
from site_common import load_site_config
from paper_discovery import validate_layer, render_html, render_markdown

# Five pre-existing answers cite profile/model/scope fields rather than a KF.
# Freeze both the exact QA object and its supporting fields. Any change requires
# a fresh editorial decision; missing refs on every other QA are a failure.
FIELD_SOURCE_EXCEPTIONS = {
    ("10.1038/s41467-024-50415-9", 2): ("dab7189b525618168a56f0bcb8acfab46bfc3ab04141d0538e176de57ba2c4a2", ("/study_profile/unique_total_n", "/study_profile/cohorts"), "464d645730c607b977e4bcceb121a59077ccac2fb46774efdeeb9383d7740a1f"),
    ("10.1038/s41467-024-50415-9", 6): ("d855e91b476605e3ff8af964fdf1f8c7fdcd4b8b9fde0a015d5fd0d02d7f17f5", ("/model_profile/final_predictors",), "42bb38339162462cd0231c75acad38506c7cb8f904e960b27f9256c9820792d0"),
    ("10.1038/s41467-024-50415-9", 8): ("0cc6078805287ed33f7b8d0f071e601e4869a37ba7d372c1e6371e3e2ac0aa56", ("/evidence_scope/does_not_establish", "/limitations"), "79665d1d4dbef43ba0da6b2bacce6dd0cebc9b3d5f628ac4ac1a396987d20aae"),
    ("10.1016/j.isci.2023.107587", 8): ("c843e3c851407d6809ad68f008c1a80765b39862c11e2aecec1ddc157f7404c8", ("/evidence_scope/does_not_establish", "/limitations"), "ca24a541f45620fccc89b9b370c1ab6fbf349a6ab8a2ac9559cc3ba14a62a175"),
    ("10.1186/s12967-022-03795-9", 8): ("6ccb85d31b3beaaf6a1122473c0d668c0ed9d350a65cd002d9f3788b2f8041cc", ("/evidence_scope/does_not_establish", "/limitations"), "27e2234bfbca7457b46ecd9b88ebdfbcc2e46a58762fadf366362bf568e3b29c"),
}
PILOT_ALTERNATIVES = {"10.1002/mdr2.70052": "Existing narrative-review chronotherapy evidence matrix and selected evidence sources"}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def pointer(value, path):
    for key in path.strip("/").split("/"):
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def check_qa_refs(content):
    findings = {finding["id"] for finding in content["key_findings"]}
    exceptions = []
    for position, qa in enumerate(content["qa"], 1):
        refs = qa.get("evidence_refs", [])
        if refs:
            if not isinstance(refs, list) or len(refs) != len(set(refs)) or any(ref not in findings for ref in refs):
                raise ValueError(f"{content['doi']} QA {position} has invalid evidence_refs")
            continue
        fixture = FIELD_SOURCE_EXCEPTIONS.get((content["doi"], position))
        if fixture is None:
            raise ValueError(f"{content['doi']} QA {position} requires evidence_refs or an explicitly reviewed field-source exception")
        qa_hash, paths, fields_hash = fixture
        if fingerprint(qa) != qa_hash or fingerprint({path: pointer(content, path) for path in paths}) != fields_hash:
            raise ValueError(f"{content['doi']} QA {position} field-source exception changed; editorial re-review required")
        exceptions.append({"qa_index": position, "status": "FIELD_SOURCE_EXCEPTION", "source_paths": list(paths)})
    return exceptions


def coverage_rows(publications, contents, root, read_text=None):
    """Return a DOI-sorted matrix; read_text permits a frozen Git-object audit."""
    root = Path(root)
    read = read_text or (lambda path: (root / path).read_text(encoding="utf-8"))
    rows = []
    for publication in sorted((p for p in publications if p.get("paper_geo_status") == "v2"), key=lambda p: p["doi"]):
        doi, slug = publication["doi"], publication["slug"]
        content = contents[doi]
        row = {"doi": doi, "title": publication["title"], "publication_type": publication["type"], "profile_type": content.get("study_profile", {}).get("profile_type"), "field_source_exceptions": [], "problems": []}
        page, markdown = read(f"papers/{slug}.html"), read(f"papers/{slug}.md")

        def status(name, source, visible, md):
            missing = [label for label, present in (("source", source), ("HTML", visible), ("Markdown", md)) if not present]
            row[name] = "PASS" if not missing else "MISSING_" + "_".join(missing)
            if missing:
                row["problems"].append(name + ": missing " + ", ".join(missing))

        def section(name, key, marker, heading):
            status(name, bool(content.get(key)), f'data-v2-section="{marker}"' in page, "## " + heading in markdown)

        try:
            if content.get("doi") != doi or content.get("version") != 2:
                raise ValueError(doi + " V2 source identity/version mismatch")
            validate_deep_v2_content(content, doi)
            row["source_schema"] = "PASS"
        except (ValueError, KeyError, TypeError) as error:
            row["source_schema"] = "FAIL"
            row["problems"].append(str(error))
        schemas = [json.loads(text) for text in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
        articles = [schema for schema in schemas if schema.get("@type") == "ScholarlyArticle"]
        schema = articles[0] if len(articles) == 1 else {}
        authors = publication.get("authors", [])
        def meta(name):
            return [html.unescape(value) for value in re.findall(r'<meta name="' + re.escape(name) + r'" content="([^"]*)">', page)]
        canonical = publication["paper_url"]
        identity_html = meta("citation_title") == [publication["title"]] and meta("citation_doi") == [doi] and meta("citation_author") == authors and f'<link rel="canonical" href="{canonical}">' in page
        identity_md = markdown.startswith("# " + publication["title"] + "\n") and f"DOI: {doi}" in markdown and f"Canonical page: {canonical}" in markdown and all(f"{i}. {name}" in markdown for i, name in enumerate(authors, 1)) and all(f"{label}: {publication[key]}\n" in markdown for label, key in (("Type", "type"), ("Journal", "journal"), ("Year", "year")))
        # The established renderer canonicalizes only the site's researcher
        # reference (e.g. GE ZHANG -> Ge Zhang), including its ORCID/@id.
        # Compare complete ordered author objects, never case-fold all authors.
        expected_authors = paper_schema(publication, canonical, load_site_config())["author"]
        identity_schema = schema.get("name") == publication["title"] and schema.get("url") == canonical and schema.get("identifier", {}).get("value") == doi and schema.get("author") == expected_authors and schema.get("description") == content.get("author_summary")
        status("publication_identity", bool(authors), identity_html, identity_md)
        row["html_md_jsonld_parity"] = "PASS" if identity_html and identity_md and identity_schema else "FAIL"
        if row["html_md_jsonld_parity"] != "PASS":
            row["problems"].append("Publication identity differs across JSON, HTML, Markdown or JSON-LD")
        section("research_question", "research_question", "research-question", "Research Question")
        section("author_evidence_summary", "author_summary", "author-summary", "Author Evidence Summary")
        snapshot = "Evidence Base" if row["profile_type"] == "narrative_review" else "Evidence Snapshot" if row["profile_type"] == "clinical_cohort" else "Evidence Scale"
        status("evidence_snapshot_study_profile", bool(content.get("study_profile")), 'data-v2-section="evidence-snapshot"' in page and 'data-v2-section="study-design"' in page, "## " + snapshot in markdown and "## " + v2_study_heading(content) in markdown)
        section("key_findings_arguments", "key_findings", "key-findings", v2_article_label(content, "Key Findings"))
        section("what_this_adds", "what_this_adds", "what-this-adds", v2_article_label(content, "What This Review Adds") if row["profile_type"] == "narrative_review" else "What This Study Adds")
        section("evidence_scope", "evidence_scope", "evidence-scope", "Evidence Scope")
        section("qa_and_refs", "qa", "qa", "Q&A")
        try:
            row["field_source_exceptions"] = check_qa_refs(content)
            if row["field_source_exceptions"] and row["qa_and_refs"] == "PASS":
                row["qa_and_refs"] = "FIELD_SOURCE_EXCEPTION"
            for i, qa in enumerate(content["qa"], 1):
                if f'id="qa-{i}"' not in page or "### " + qa["question"] not in markdown:
                    raise ValueError(f"{doi} QA {i} loses its HTML anchor or Markdown question heading")
                if html.escape(qa["question"]) not in page or html.escape(qa["answer"]) not in page or qa["question"] not in markdown or qa["answer"] not in markdown:
                    raise ValueError(f"{doi} QA {i} differs across source/HTML/Markdown")
                refs = qa.get("evidence_refs", [])
                qa_markup = re.search(r'<article\b[^>]*id="qa-' + str(i) + r'"[^>]*>(.*?)</article>', page, re.S)
                # Existing QA renders explicit KF labels as text, not links.
                if refs and (qa_markup is None or '<strong>Evidence:</strong> ' + html.escape(", ".join(refs)) not in qa_markup[1] or "Evidence: " + ", ".join(refs) not in markdown):
                    raise ValueError(f"{doi} QA {i} loses its rendered finding references")
        except (ValueError, KeyError, TypeError) as error:
            row["qa_and_refs"] = "FAIL"
            row["problems"].append(str(error))
        layer = content.get("discovery_layer")
        status("discovery_context", bool(layer), 'data-discovery-layer="1"' in page, "## Research & review context" in markdown)
        if layer:
            try:
                validate_layer(layer, doi)
                if page.count(render_html(content)) != 1 or "\n".join(render_markdown(content)) not in markdown:
                    raise ValueError(doi + " discovery context differs from source")
            except ValueError as error:
                row["discovery_context"] = "FAIL"
                row["problems"].append(str(error))
        try:
            if content.get("citation_layer"):
                validate_citation_layer(content["citation_layer"], content["key_findings"], doi)
                status("citation_contexts", True, 'id="citation-use-cases"' in page and 'id="evidence-matrix"' in page, '<a id="citation-use-cases"></a>' in markdown and '<a id="evidence-matrix"></a>' in markdown)
            elif content.get("citation_pilot") and doi in PILOT_ALTERNATIVES and row["profile_type"] == "narrative_review":
                validate_citation_pilot(content["citation_pilot"], {finding["id"] for finding in content["key_findings"]}, doi)
                status("citation_contexts", True, 'data-citation-pilot-section="matrix"' in page and 'data-citation-pilot-section="sources"' in page, "## Chronotherapy Evidence Matrix" in markdown and "## Selected Evidence Sources" in markdown)
                if row["citation_contexts"] == "PASS":
                    row["citation_contexts"] = "CITATION_PILOT_ALTERNATIVE"
                    row["citation_alternative_reason"] = PILOT_ALTERNATIVES[doi]
            else:
                status("citation_contexts", False, False, False)
        except (ValueError, KeyError, TypeError) as error:
            row["citation_contexts"] = "FAIL"
            row["problems"].append(str(error))
        section("concepts", "concepts", "concepts", "Concepts & Entities")
        section("related_research", "related_papers", "related-research", "Related Research")
        section("provenance_doi", "provenance", "provenance", "Publication & Provenance")
        base_url = urlsplit(canonical)
        citation_root = base_url.scheme + "://" + base_url.netloc + "/citations/"
        exports_ok = True
        try:
            for suffix, key in (("bib", "citation_bibtex_url"), ("ris", "citation_ris_url"), ("csl.json", "citation_csl_json_url")):
                path = f"citations/{slug}.{suffix}"
                export = read(path)
                expected_url = citation_root + slug + "." + suffix
                # publications.json carries canonical URLs; paper_index carries
                # explicit citation URL fields and is checked by validate_site.
                exports_ok &= bool(export) and publication.get(key, expected_url) == expected_url and f'../{path}' in page
                if suffix == "csl.json":
                    csl = json.loads(export)
                    exports_ok &= csl.get("DOI") == doi and [author.get("literal") for author in csl.get("author", [])] == authors and csl.get("type") == "article-journal"
                    if publication["type"] in {"Letter", "Correspondence"}:
                        exports_ok &= csl.get("genre") == publication["type"]
        except (OSError, KeyError, ValueError) as error:
            exports_ok = False
            row["problems"].append(str(error))
        row["formal_citation_exports"] = "PASS" if exports_ok else "FAIL"
        if not exports_ok:
            row["problems"].append("Missing/inconsistent formal citation URL, download, DOI, genre or authors")
        row["status"] = "PASS" if not row["problems"] else "FAIL"
        rows.append(row)
    return rows


def validate_v2_coverage(publications, contents, root):
    rows = coverage_rows(publications, contents, root)
    failures = [(row["doi"], problem) for row in rows for problem in row["problems"]]
    if failures:
        raise ValueError("V2 module coverage failed: " + "; ".join(doi + ": " + problem for doi, problem in failures))
    return {"v2_pages": len(rows), "covered_pages": len(rows), "field_source_qa_exceptions": sum(len(row["field_source_exceptions"]) for row in rows), "citation_pilot_alternatives": sum(row["citation_contexts"] == "CITATION_PILOT_ALTERNATIVE" for row in rows)}
