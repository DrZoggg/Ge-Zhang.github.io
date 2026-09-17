import argparse
import json
import os
import re
import sys

from build_publications import build_site
from site_common import (
    DEEP_CONTENT_DIR,
    controller_reference,
    controller_token,
    deep_content_path,
    ensure_public_slugs,
    load_deep_geo,
    load_featured,
    publication_token,
    save_deep_geo,
    save_featured,
    write_json,
)
from sync_common import is_withdrawn, load_master, norm_doi, norm_title, save_master
from validate_site import validate_site


STOPWORDS = {
    "a", "an", "and", "as", "at", "based", "by", "for", "from", "in", "into",
    "of", "on", "or", "the", "through", "to", "using", "via", "with",
}


class BatchValidationError(ValueError):
    def __init__(self, failures, requested, resolved=0):
        self.failures = failures
        self.requested = requested
        self.resolved = resolved
        super().__init__("Batch validation failed; no files were changed.")


def append_summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(text.rstrip() + "\n")


def output_value(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def resolve_paper(query, master):
    query = str(query or "").strip()
    if not query:
        raise ValueError("Paper is required. Enter a DOI, exact slug, exact title, or unique title substring.")
    query_doi = norm_doi(query)
    doi_matches = [item for item in master if query_doi and norm_doi(item.get("doi")) == query_doi]
    if len(doi_matches) == 1:
        return doi_matches[0]
    slug_matches = [
        item for item in master
        if str(item.get("slug") or "").casefold() == query.casefold()
    ]
    if len(slug_matches) == 1:
        return slug_matches[0]
    exact_title = [
        item for item in master
        if str(item.get("title") or "").strip().casefold() == query.casefold()
    ]
    if len(exact_title) == 1:
        return exact_title[0]
    normalized_query = norm_title(query)
    substring_matches = [
        item for item in master
        if normalized_query and normalized_query in norm_title(item.get("title"))
    ]
    if len(substring_matches) == 1:
        return substring_matches[0]
    if len(substring_matches) > 1:
        candidates = "\n".join(
            f"- {item.get('title')} | DOI: {item.get('doi') or 'none'} | slug: {item.get('slug') or 'none'}"
            for item in substring_matches
        )
        raise ValueError(
            "Paper title substring is ambiguous. Use a DOI or exact slug. Candidates:\n" + candidates
        )
    raise ValueError(f"No paper matched {query!r}. Use the DOI from Publications for the safest match.")


def parse_paper_queries(raw, master):
    """Parse newline-first input while preserving resolvable titles containing commas."""
    lines = [line.strip() for line in str(raw or "").splitlines() if line.strip()]
    if not lines:
        raise ValueError(
            "Paper is required. Enter a DOI, exact slug, exact title, or unique title substring."
        )

    expanded = []
    for line in lines:
        if "," not in line:
            expanded.append(line)
            continue
        try:
            resolve_paper(line, master)
        except ValueError:
            parts = [part.strip() for part in line.split(",") if part.strip()]
            expanded.extend(parts or [line])
        else:
            expanded.append(line)

    queries = []
    seen = set()
    for query in expanded:
        key = query.casefold()
        if key in seen:
            continue
        seen.add(key)
        queries.append(query)
    return {
        "queries": queries,
        "batch_mode": len(expanded) > 1,
        "input_duplicates": len(expanded) - len(queries),
    }


def resolve_papers(raw, master):
    parsed = parse_paper_queries(raw, master)
    failures = []
    papers = []
    seen_tokens = set()
    target_duplicates = 0
    for query in parsed["queries"]:
        try:
            paper = resolve_paper(query, master)
        except ValueError as exc:
            failures.append((query, str(exc)))
            continue
        if parsed["batch_mode"] and is_withdrawn(paper):
            failures.append((query, "Withdrawn records are not valid batch targets."))
            continue
        token = publication_token(paper)
        if token in seen_tokens:
            target_duplicates += 1
            continue
        seen_tokens.add(token)
        papers.append(paper)

    if failures:
        if parsed["batch_mode"]:
            raise BatchValidationError(
                failures, len(parsed["queries"]), resolved=len(papers)
            )
        raise ValueError(failures[0][1])
    parsed.update({"papers": papers, "target_duplicates": target_duplicates})
    return parsed


def starter_keywords(title):
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+-]*", str(title))
    result = []
    for word in words:
        if word.casefold() in STOPWORDS or len(word) < 3:
            continue
        if word.casefold() not in {item.casefold() for item in result}:
            result.append(word)
        if len(result) == 10:
            break
    return result


def safe_fallback_summary(publication):
    title = publication.get("title") or "Untitled work"
    journal = publication.get("journal") or "Unknown source"
    year = publication.get("year") or "n.d."
    return f'A publication in {journal} ({year}) titled “{title}”.'


def create_safe_starter(publication):
    title = publication.get("title") or "Untitled work"
    payload = {
        "version": 1,
        **controller_reference(publication),
        "display_title": title,
        "summary": safe_fallback_summary(publication),
        "keywords": starter_keywords(title),
        "questions": [f"What does this publication investigate regarding “{title}”?"],
    }
    write_json(deep_content_path(publication), payload)


def parse_position(raw, total):
    raw = str(raw or "").strip()
    if not raw:
        return None, ""
    try:
        requested = int(raw)
    except ValueError as exc:
        raise ValueError("Featured position must be a whole number starting from 1.") from exc
    if requested < 1:
        applied = 1
    elif requested > total:
        applied = total
    else:
        applied = requested
    note = ""
    if applied != requested:
        note = f"Requested position {requested} was safely clamped to {applied}."
    return applied, note


def move_featured(entries, index, position):
    entry = entries.pop(index)
    entries.insert(position - 1, entry)


def run_control(args):
    master, _ = save_master(load_master())
    if ensure_public_slugs(master):
        master, _ = save_master(master)

    resolved = resolve_papers(args.paper, master)
    papers = resolved["papers"]
    batch_mode = resolved["batch_mode"]
    summary_input = str(args.featured_summary or "").strip()
    position_input = str(args.featured_position or "").strip()
    if batch_mode and (args.featured != "no_change" or position_input or summary_input):
        raise BatchValidationError(
            [
                (
                    "Homepage Featured",
                    "Batch mode only supports Deep GEO. Set Homepage Featured to no_change "
                    "and leave Featured position/summary blank.",
                )
            ],
            len(resolved["queries"]),
            resolved=len(papers),
        )

    paper = papers[0] if len(papers) == 1 else None
    if paper and is_withdrawn(paper) and (
        args.deep_geo == "enable" or args.featured == "add"
    ):
        raise ValueError("Withdrawn records cannot be enabled for Deep GEO or added to Featured.")

    deep_entries = load_deep_geo()
    featured_entries = load_featured()
    deep_before_tokens = {controller_token(entry) for entry in deep_entries}
    original_deep_tokens = set(deep_before_tokens)
    changed = False
    notes = []
    enabled_count = 0
    disabled_count = 0
    noop_count = resolved["input_duplicates"] + resolved["target_duplicates"]
    starters = []

    if args.deep_geo == "enable":
        for target in papers:
            token = publication_token(target)
            content_path = deep_content_path(target)
            if token not in deep_before_tokens:
                deep_entries.append(controller_reference(target))
                deep_before_tokens.add(token)
                enabled_count += 1
                changed = True
            elif content_path.is_file():
                noop_count += 1
            if not content_path.is_file():
                starters.append((target, content_path))
                changed = True
        if enabled_count:
            save_deep_geo(deep_entries)
        for target, content_path in starters:
            create_safe_starter(target)
            notes.append(
                "Created conservative starter: "
                f"{content_path.relative_to(DEEP_CONTENT_DIR.parent.parent)}"
            )
    elif args.deep_geo == "disable":
        target_tokens = {publication_token(target) for target in papers}
        disabled_count = len(target_tokens & deep_before_tokens)
        noop_count += len(target_tokens - deep_before_tokens)
        if disabled_count:
            deep_entries = [
                entry for entry in deep_entries
                if controller_token(entry) not in target_tokens
            ]
            save_deep_geo(deep_entries)
            changed = True
    else:
        noop_count += len(papers)

    featured_before = False
    position_before = None
    if paper:
        token = publication_token(paper)
        featured_before_tokens = [controller_token(entry) for entry in featured_entries]
        featured_before = token in featured_before_tokens
        position_before = (
            featured_before_tokens.index(token) + 1 if featured_before else None
        )
        current_index = (
            featured_before_tokens.index(token) if featured_before else None
        )
        featured_changed = False

        if args.featured == "remove":
            if current_index is not None:
                featured_entries.pop(current_index)
                featured_changed = True
        elif args.featured == "add":
            if current_index is None:
                summary = summary_input
                if not summary:
                    content_path = deep_content_path(paper)
                    if content_path.is_file():
                        summary = str(
                            json.loads(content_path.read_text(encoding="utf-8")).get("summary") or ""
                        ).strip()
                if not summary:
                    summary = safe_fallback_summary(paper)
                entry = {**controller_reference(paper), "summary": summary}
                position, note = parse_position(
                    args.featured_position, len(featured_entries) + 1
                )
                position = position or len(featured_entries) + 1
                featured_entries.insert(position - 1, entry)
                current_index = position - 1
                featured_changed = True
                if note:
                    notes.append(note)
            else:
                entry = featured_entries[current_index]
                if summary_input and entry.get("summary", "") != summary_input:
                    entry["summary"] = summary_input
                    featured_changed = True
                position, note = parse_position(
                    args.featured_position, len(featured_entries)
                )
                if position is not None and position != current_index + 1:
                    move_featured(featured_entries, current_index, position)
                    featured_changed = True
                if note:
                    notes.append(note)
        else:
            if (summary_input or position_input) and current_index is None:
                raise ValueError(
                    "This paper is not Featured. Choose Featured = add before setting its position or summary."
                )
            if current_index is not None:
                entry = featured_entries[current_index]
                if summary_input and entry.get("summary", "") != summary_input:
                    entry["summary"] = summary_input
                    featured_changed = True
                position, note = parse_position(
                    args.featured_position, len(featured_entries)
                )
                if position is not None and position != current_index + 1:
                    move_featured(featured_entries, current_index, position)
                    featured_changed = True
                if note:
                    notes.append(note)

        if featured_changed:
            save_featured(featured_entries)
            changed = True

    build_result = build_site()
    validation = validate_site()
    output_value("changed", str(changed).lower())
    if batch_mode:
        report = [
            "# Paper Control Center",
            "",
            "- **Batch mode:** yes",
            f"- **Requested papers:** {len(resolved['queries'])}",
            f"- **Resolved papers:** {len(papers)}",
            f"- **Deep GEO enabled:** {enabled_count}",
            f"- **Deep GEO disabled:** {disabled_count}",
            f"- **Already enabled / disabled / no-op:** {noop_count}",
            "- **Failed:** 0",
            f"- **Public records:** {validation['public']}",
            f"- **Master records:** {validation['master']}",
            f"- **Withdrawn:** {validation['withdrawn']}",
            "- **Build:** PASS",
            "- **Validation:** PASS",
            f"- **Repository change:** {'YES — commit and Pages deployment will follow' if changed else 'NO — no commit or deployment'}",
        ]
    else:
        token = publication_token(paper)
        title = paper.get("title") or "Untitled work"
        doi = norm_doi(paper.get("doi"))
        slug = paper.get("slug") or ""
        deep_before = token in original_deep_tokens
        deep_after = token in {controller_token(entry) for entry in load_deep_geo()}
        final_featured = load_featured()
        final_tokens = [controller_token(entry) for entry in final_featured]
        featured_after = token in final_tokens
        position_after = final_tokens.index(token) + 1 if featured_after else None
        output_value("slug", slug)
        report = [
            "# Paper Control Center",
            "",
            f"- **Title:** {title}",
            f"- **DOI:** {doi or 'Not available'}",
            f"- **Slug:** {slug}",
            f"- **Deep GEO:** {'ON' if deep_before else 'OFF'} → {'ON' if deep_after else 'OFF'}",
            f"- **Featured:** {'ON' if featured_before else 'OFF'} → {'ON' if featured_after else 'OFF'}",
            f"- **Featured position:** {position_before or 'not featured'} → {position_after or 'not featured'}",
            f"- **Public records:** {validation['public']}",
            f"- **Master records:** {validation['master']}",
            f"- **Withdrawn:** {validation['withdrawn']}",
            "- **Build:** PASS",
            "- **Validation:** PASS",
            f"- **Repository change:** {'YES — commit and Pages deployment will follow' if changed else 'NO — no commit or deployment'}",
        ]
    if notes:
        report.extend(["", "## Notes", *[f"- {note}" for note in notes]])
    append_summary("\n".join(report))
    print("\n".join(report))
    return {"changed": changed, "build": build_result, "validation": validation}


def parser():
    result = argparse.ArgumentParser(description="Control Deep GEO and Homepage Featured state.")
    result.add_argument("--paper", default=os.environ.get("PAPER_INPUT", ""))
    result.add_argument(
        "--deep-geo",
        choices=("no_change", "enable", "disable"),
        default=os.environ.get("DEEP_GEO_INPUT", "no_change"),
    )
    result.add_argument(
        "--featured",
        choices=("no_change", "add", "remove"),
        default=os.environ.get("FEATURED_INPUT", "no_change"),
    )
    result.add_argument(
        "--featured-position", default=os.environ.get("FEATURED_POSITION_INPUT", "")
    )
    result.add_argument(
        "--featured-summary", default=os.environ.get("FEATURED_SUMMARY_INPUT", "")
    )
    return result


def main():
    args = parser().parse_args()
    try:
        run_control(args)
    except BatchValidationError as exc:
        report = [
            "# Paper Control Center",
            "",
            "- **Batch mode:** yes",
            "- **Batch aborted:** yes",
            f"- **Requested papers:** {exc.requested}",
            f"- **Resolved papers:** {exc.resolved}",
            f"- **Failed:** {len(exc.failures)}",
            "- **Changed:** 0",
            "- **Commit:** no",
            "- **Deployment:** no",
            "",
            "## Failed inputs",
            *[f"- `{query}` — {reason}" for query, reason in exc.failures],
        ]
        message = "\n".join(report)
        output_value("changed", "false")
        append_summary(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        message = f"# Paper Control Center\n\n**FAILED:** {exc}"
        output_value("changed", "false")
        append_summary(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
