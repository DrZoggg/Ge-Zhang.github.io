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
    paper = resolve_paper(args.paper, master)
    token = publication_token(paper)
    title = paper.get("title") or "Untitled work"
    doi = norm_doi(paper.get("doi"))
    slug = paper.get("slug") or ""
    if is_withdrawn(paper) and (args.deep_geo == "enable" or args.featured == "add"):
        raise ValueError("Withdrawn records cannot be enabled for Deep GEO or added to Featured.")

    deep_entries = load_deep_geo()
    featured_entries = load_featured()
    deep_before = token in {controller_token(entry) for entry in deep_entries}
    featured_before_tokens = [controller_token(entry) for entry in featured_entries]
    featured_before = token in featured_before_tokens
    position_before = (
        featured_before_tokens.index(token) + 1 if featured_before else None
    )
    changed = False
    notes = []

    if args.deep_geo == "enable":
        if not deep_before:
            deep_entries.append(controller_reference(paper))
            save_deep_geo(deep_entries)
            changed = True
        content_path = deep_content_path(paper)
        if not content_path.is_file():
            create_safe_starter(paper)
            notes.append(f"Created conservative starter: {content_path.relative_to(DEEP_CONTENT_DIR.parent.parent)}")
            changed = True
    elif args.deep_geo == "disable" and deep_before:
        deep_entries = [entry for entry in deep_entries if controller_token(entry) != token]
        save_deep_geo(deep_entries)
        changed = True

    summary_input = str(args.featured_summary or "").strip()
    featured_tokens = [controller_token(entry) for entry in featured_entries]
    current_index = featured_tokens.index(token) if token in featured_tokens else None

    if args.featured == "remove":
        if current_index is not None:
            featured_entries.pop(current_index)
            save_featured(featured_entries)
            changed = True
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
            position, note = parse_position(args.featured_position, len(featured_entries) + 1)
            position = position or len(featured_entries) + 1
            featured_entries.insert(position - 1, entry)
            if note:
                notes.append(note)
            save_featured(featured_entries)
            changed = True
            current_index = position - 1
        else:
            entry = featured_entries[current_index]
            if summary_input and entry.get("summary", "") != summary_input:
                entry["summary"] = summary_input
                changed = True
            position, note = parse_position(args.featured_position, len(featured_entries))
            if position is not None and position != current_index + 1:
                move_featured(featured_entries, current_index, position)
                changed = True
            if note:
                notes.append(note)
            if changed:
                save_featured(featured_entries)
    else:
        if (summary_input or str(args.featured_position or "").strip()) and current_index is None:
            raise ValueError(
                "This paper is not Featured. Choose Featured = add before setting its position or summary."
            )
        if current_index is not None:
            entry = featured_entries[current_index]
            local_changed = False
            if summary_input and entry.get("summary", "") != summary_input:
                entry["summary"] = summary_input
                local_changed = True
            position, note = parse_position(args.featured_position, len(featured_entries))
            if position is not None and position != current_index + 1:
                move_featured(featured_entries, current_index, position)
                local_changed = True
            if note:
                notes.append(note)
            if local_changed:
                save_featured(featured_entries)
                changed = True

    build_result = build_site()
    validation = validate_site()
    deep_after = token in {controller_token(entry) for entry in load_deep_geo()}
    final_featured = load_featured()
    final_tokens = [controller_token(entry) for entry in final_featured]
    featured_after = token in final_tokens
    position_after = final_tokens.index(token) + 1 if featured_after else None
    output_value("changed", str(changed).lower())
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
        f"- **Build:** PASS",
        f"- **Validation:** PASS",
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
    except Exception as exc:
        message = f"# Paper Control Center\n\n**FAILED:** {exc}"
        append_summary(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
