import copy
import csv
import html
import json
import re
import urllib.parse

from site_common import (
    DEEP_CONTENT_DIR,
    LEGACY_DEEP_SLUGS,
    PAPERS_DIR,
    controller_token,
    deep_content_path,
    ensure_public_slugs,
    index_master,
    load_deep_geo,
    load_featured,
    load_site_config,
    publication_token,
    validate_controller_entries,
)
from sync_common import ROOT, is_withdrawn, load_master, norm_doi, save_master


FEATURED_START = "<!-- FEATURED_PAPERS_START -->"
FEATURED_END = "<!-- FEATURED_PAPERS_END -->"
GENERATED_MARKER = "<!-- GEO_PHASE2_GENERATED -->"


def scholar_url(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote(f'"{title}"')


def doi_url(doi):
    return f"https://doi.org/{norm_doi(doi)}" if norm_doi(doi) else ""


def absolute(site_root, relative):
    return f"{site_root}/{str(relative).lstrip('/')}"


def schema_type(publication):
    publication_type = str(publication.get("type") or "").casefold()
    if publication_type in {"article", "review", "journal article"}:
        return "ScholarlyArticle"
    return "CreativeWork"


def load_deep_content(publication):
    path = deep_content_path(publication)
    if not path.is_file():
        raise ValueError(
            f"Deep GEO is enabled for {publication.get('title')!r}, but {path.relative_to(ROOT)} is missing."
        )
    content = json.loads(path.read_text(encoding="utf-8"))
    if content.get("version") != 1:
        raise ValueError(f"{path.relative_to(ROOT)} must use version 1.")
    configured_doi = norm_doi(content.get("doi"))
    publication_doi = norm_doi(publication.get("doi"))
    if configured_doi and configured_doi != publication_doi:
        raise ValueError(
            f"Deep GEO content DOI mismatch in {path.relative_to(ROOT)}: "
            f"{configured_doi} != {publication_doi}"
        )
    for list_key in ("keywords", "questions"):
        if content.get(list_key) is not None and not isinstance(content[list_key], list):
            raise ValueError(f"{path.relative_to(ROOT)} field {list_key!r} must be an array.")
    return content


def paper_schema(publication, paper_url):
    title = publication.get("title") or "Untitled work"
    result = {
        "@context": "https://schema.org",
        "@type": schema_type(publication),
        "name": title,
        "headline": title,
        "url": paper_url,
        "mainEntityOfPage": paper_url,
    }
    if publication.get("year"):
        result["datePublished"] = str(publication["year"])
    if publication.get("journal"):
        result["isPartOf"] = {
            "@type": "Periodical",
            "name": publication["journal"],
        }
    doi = norm_doi(publication.get("doi"))
    if doi:
        result["identifier"] = {
            "@type": "PropertyValue",
            "propertyID": "DOI",
            "value": doi,
        }
        result["sameAs"] = doi_url(doi)
    return result


def render_deep_html(content):
    summary = str(content.get("summary") or "").strip()
    keywords = [str(x).strip() for x in content.get("keywords", []) if str(x).strip()]
    questions = [str(x).strip() for x in content.get("questions", []) if str(x).strip()]
    sections = []
    if summary or keywords:
        body = ""
        if summary:
            body += f"<p>{html.escape(summary)}</p>"
        if keywords:
            body += '<div class="tags">' + "".join(
                f'<span class="tag">{html.escape(keyword)}</span>' for keyword in keywords
            ) + "</div>"
        sections.append(f'<div class="card"><h2>Why this study matters</h2>{body}</div>')
    if questions:
        question_items = "".join(f"<li>{html.escape(question)}</li>" for question in questions)
        sections.append(
            '<div class="card"><h2>Questions this paper can answer</h2>'
            f"<ol>{question_items}</ol></div>"
        )
    if not sections:
        return ""
    return '<section><div class="grid">' + "".join(sections) + "</div></section>"


def render_deep_markdown(content):
    parts = []
    summary = str(content.get("summary") or "").strip()
    keywords = [str(x).strip() for x in content.get("keywords", []) if str(x).strip()]
    questions = [str(x).strip() for x in content.get("questions", []) if str(x).strip()]
    if summary:
        parts.extend(["## Deep GEO context", "", summary, ""])
    if keywords:
        parts.extend(["### Semantic keywords", "", ", ".join(keywords), ""])
    if questions:
        parts.extend(
            ["### Questions this paper can answer", ""]
            + [f"- {question}" for question in questions]
            + [""]
        )
    return "\n".join(parts)


def render_paper_html(publication, *, config, deep_content=None):
    site_root = config["site_url"]
    title = publication.get("title") or "Untitled work"
    journal = publication.get("journal") or "Unknown source"
    year = publication.get("year") or "n.d."
    publication_type = publication.get("type") or "Work"
    slug = publication["slug"]
    doi = norm_doi(publication.get("doi"))
    canonical = absolute(site_root, f"papers/{slug}.html")
    markdown_url = absolute(site_root, f"papers/{slug}.md")
    deep_summary = str((deep_content or {}).get("summary") or "").strip()
    description = deep_summary or (
        f"Author-controlled academic record for {title}, published in {journal} ({year})."
    )
    links = []
    if doi:
        links.append(
            f'<a class="btn primary" href="{html.escape(doi_url(doi), quote=True)}">DOI / publisher</a>'
        )
    elif publication.get("url"):
        links.append(
            f'<a class="btn primary" href="{html.escape(str(publication["url"]), quote=True)}">Source</a>'
        )
    links.append(
        f'<a class="btn" href="{html.escape(scholar_url(title), quote=True)}">Google Scholar search</a>'
    )
    deep_badge = '<span class="badge">Deep GEO</span>' if deep_content is not None else ""
    citation = [
        f'<meta name="citation_title" content="{html.escape(str(title), quote=True)}">',
        f'<meta name="citation_journal_title" content="{html.escape(str(journal), quote=True)}">',
    ]
    if publication.get("year"):
        citation.append(
            f'<meta name="citation_publication_date" content="{html.escape(str(publication["year"]), quote=True)}">'
        )
    if doi:
        citation.append(f'<meta name="citation_doi" content="{html.escape(doi, quote=True)}">')
    deep_html = render_deep_html(deep_content or {}) if deep_content is not None else ""
    schema = paper_schema(publication, canonical)
    if deep_content and deep_content.get("keywords"):
        schema["keywords"] = [
            str(x).strip() for x in deep_content["keywords"] if str(x).strip()
        ]
    safe_schema = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html>
{GENERATED_MARKER}
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(str(title))} | Ge Zhang</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<link rel="alternate" type="text/markdown" href="{html.escape(markdown_url, quote=True)}">
<meta property="og:title" content="{html.escape(str(title), quote=True)}">
<meta property="og:description" content="{html.escape(description, quote=True)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{html.escape(canonical, quote=True)}">
{chr(10).join(citation)}
<link rel="stylesheet" href="../assets/style.css"></head><body>
<header><nav><a class="brand" href="../index.html">Ge Zhang</a><div class="navlinks"><a href="../index.html#research">Research</a><a href="../publications.html">All publications</a><a href="../index.html#profiles">Profiles</a></div></nav></header>
<main class="wrap">
<section class="hero" style="grid-template-columns:1fr"><div>
<div class="eyebrow">{html.escape(str(publication_type))} · {html.escape(str(year))} {deep_badge}</div>
<h1 style="font-size:clamp(2.2rem,5vw,4rem)">{html.escape(str(title))}</h1>
<p class="lead">{html.escape(str(journal))}</p>
<div class="links">{' '.join(links)}</div>
</div></section>
{deep_html}
<section><div class="notice"><strong>Author-controlled academic record for Ge Zhang.</strong> This page identifies the work as part of Ge Zhang’s publication record via ORCID <a href="https://orcid.org/{html.escape(config["orcid"], quote=True)}">{html.escape(config["orcid"])}</a>. It does not replace the publisher version or assert a complete author list.</div></section>
<section><div class="links"><a class="btn" href="../publications.html">All Publications</a> <a class="btn" href="../index.html">Homepage</a></div></section>
<script type="application/ld+json">{safe_schema}</script>
</main><footer><div class="wrap">© Ge Zhang · Academic website · ORCID: {html.escape(config["orcid"])}</div></footer>
</body></html>
'''


def render_paper_markdown(publication, *, config, deep_content=None):
    site_root = config["site_url"]
    title = publication.get("title") or "Untitled work"
    journal = publication.get("journal") or "Unknown source"
    year = publication.get("year") or "n.d."
    publication_type = publication.get("type") or "Work"
    slug = publication["slug"]
    doi = norm_doi(publication.get("doi"))
    html_url = absolute(site_root, f"papers/{slug}.html")
    md_url = absolute(site_root, f"papers/{slug}.md")
    lines = [
        f"# {title}",
        "",
        f"Journal: {journal}",
        f"Year: {year}",
        f"Type: {publication_type}",
        f"DOI: {doi or 'Not available'}",
        f"Canonical page: {html_url}",
        f"Markdown record: {md_url}",
        f"ORCID identity anchor: https://orcid.org/{config['orcid']}",
        "",
        "## About this record",
        "",
        "This is an author-controlled publication record in the Ge Zhang Academic Hub. "
        "It identifies this work as part of Ge Zhang’s publication record via ORCID; "
        "the publisher version remains the version of record.",
        "",
    ]
    if deep_content is not None:
        lines.append(render_deep_markdown(deep_content))
    lines.extend(
        [
            "## Links",
            "",
            *([f"- DOI: {doi_url(doi)}"] if doi else []),
            f"- HTML page: {html_url}",
            f"- Google Scholar query: {scholar_url(title)}",
            f"- ORCID: https://orcid.org/{config['orcid']}",
            "",
        ]
    )
    return "\n".join(lines)


def public_record(publication, *, config, deep_tokens, featured_tokens):
    item = copy.deepcopy(publication)
    item.pop("featured", None)
    token = publication_token(publication)
    slug = publication["slug"]
    item["paper_url"] = absolute(config["site_url"], f"papers/{slug}.html")
    item["markdown_url"] = absolute(config["site_url"], f"papers/{slug}.md")
    item["deep_geo"] = token in deep_tokens
    item["featured"] = token in featured_tokens
    return item


def render_publications_page(items, config):
    by_year = {}
    for publication in items:
        by_year.setdefault(int(publication.get("year") or 0), []).append(publication)
    sections = []
    for year in sorted(by_year, reverse=True):
        rows = []
        for publication in by_year[year]:
            title = publication.get("title") or "Untitled work"
            journal = publication.get("journal") or "Unknown source"
            publication_type = publication.get("type") or "Work"
            paper_url = f"papers/{publication['slug']}.html"
            links = [f'<a href="{html.escape(paper_url, quote=True)}">Paper page</a>']
            if publication["deep_geo"]:
                links.append('<span class="badge">Deep GEO</span>')
            doi = norm_doi(publication.get("doi"))
            if doi:
                links.append(f'<a href="{html.escape(doi_url(doi), quote=True)}">DOI</a>')
            elif publication.get("url"):
                links.append(
                    f'<a href="{html.escape(str(publication["url"]), quote=True)}">Source</a>'
                )
            links.append(
                f'<a href="{html.escape(scholar_url(title), quote=True)}">Scholar</a>'
            )
            rows.append(
                f'<article class="pub" data-paper-record="true" '
                f'data-title="{html.escape(str(title).lower(), quote=True)}" '
                f'data-journal="{html.escape(str(journal).lower(), quote=True)}">'
                f'<div class="pub-title"><a href="{html.escape(paper_url, quote=True)}">'
                f'{html.escape(str(title))}</a> '
                f'<span class="badge">{html.escape(str(publication_type))}</span></div>'
                f'<div class="pub-meta">{html.escape(str(journal))} · {year or "n.d."} · '
                f'{" · ".join(links)}</div></article>'
            )
        sections.append(
            f'<section class="year-group"><h2 class="year">{year or "Undated"}</h2>'
            f'{"".join(rows)}</section>'
        )
    schema = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "name": "Ge Zhang — Publications",
        "url": absolute(config["site_url"], "publications.html"),
        "mainEntity": {
            "@type": "Person",
            "name": config["researcher_name"],
            "identifier": f"https://orcid.org/{config['orcid']}",
        },
        "hasPart": [paper_schema(item, item["paper_url"]) for item in items],
    }
    safe_schema = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All Publications | Ge Zhang</title>
<meta name="description" content="Publication record of Ge Zhang, using ORCID {html.escape(config["orcid"], quote=True)} as the identity anchor.">
<link rel="canonical" href="{html.escape(absolute(config["site_url"], "publications.html"), quote=True)}">
<link rel="stylesheet" href="assets/style.css"></head><body>
<header><nav><a class="brand" href="index.html">Ge Zhang</a><div class="navlinks">
<a href="index.html#research">Research</a><a href="publications.html">All publications</a><a href="index.html#profiles">Profiles</a></div></nav></header>
<main class="wrap"><section class="hero" style="grid-template-columns:1fr"><div>
<div class="eyebrow">Publication record</div><h1 style="font-size:clamp(2.8rem,6vw,4.7rem)">Publications</h1>
<p class="lead">This author-controlled record uses ORCID {html.escape(config["orcid"])} as the identity anchor. Every public record has a permanent HTML page and a machine-friendly Markdown version.</p>
<div class="card" style="margin-top:20px"><div class="count">{len(items)}</div><div class="meta">public works in the current database</div></div>
</div></section>
<section><input id="pubSearch" class="search" placeholder="Search title or journal..." aria-label="Search publications">
<div id="pubList">{''.join(sections)}</div></section>
<section><div class="notice"><strong>Identity control:</strong> automated discovery uses the exact ORCID iD rather than the author name “Ge Zhang”, reducing same-name misattribution.</div></section>
<script>
const box=document.getElementById('pubSearch');box.addEventListener('input',()=>{{const q=box.value.toLowerCase().trim();document.querySelectorAll('.pub').forEach(x=>{{x.style.display=(!q||x.dataset.title.includes(q)||x.dataset.journal.includes(q))?'block':'none'}});document.querySelectorAll('.year-group').forEach(y=>{{y.style.display=[...y.querySelectorAll('.pub')].some(x=>x.style.display!=='none')?'block':'none'}})}})
</script>
<script type="application/ld+json">{safe_schema}</script>
</main><footer><div class="wrap">© Ge Zhang · Academic website · ORCID: {html.escape(config["orcid"])}</div></footer></body></html>
'''


def render_featured_cards(featured_entries, master_by_token, deep_tokens):
    cards = []
    for entry in featured_entries:
        token = controller_token(entry)
        publication = master_by_token[token]
        title = publication.get("title") or "Untitled work"
        journal = publication.get("journal") or "Unknown source"
        year = publication.get("year") or "n.d."
        page_url = f"papers/{publication['slug']}.html"
        summary = str(entry.get("summary") or "").strip()
        if not summary and token in deep_tokens:
            summary = str(load_deep_content(publication).get("summary") or "").strip()
        if not summary:
            summary = f'A publication in {journal} ({year}) titled “{title}”.'
        links = [f'<a class="btn" href="{html.escape(page_url, quote=True)}">Research page</a>']
        doi = norm_doi(publication.get("doi"))
        if doi:
            links.append(f'<a class="btn" href="{html.escape(doi_url(doi), quote=True)}">DOI</a>')
        badge = ' <span class="badge">Deep GEO</span>' if token in deep_tokens else ""
        cards.append(
            f'<article class="card paper"><div class="eyebrow">'
            f'{html.escape(str(journal))} · {html.escape(str(year))}{badge}</div>'
            f'<h3><a href="{html.escape(page_url, quote=True)}">{html.escape(str(title))}</a></h3>'
            f'<p>{html.escape(summary)}</p><div class="links">{" ".join(links)}</div></article>'
        )
    return '<div class="grid">' + "".join(cards) + "</div>"


def write_machine_indexes(items, deep_items, config):
    paper_index = {
        "version": 1,
        "papers": [
            {
                "title": item.get("title"),
                "journal": item.get("journal"),
                "year": item.get("year"),
                "type": item.get("type"),
                "doi": item.get("doi", ""),
                "paper_url": item["paper_url"],
                "markdown_url": item["markdown_url"],
                "deep_geo": item["deep_geo"],
                "featured": item["featured"],
            }
            for item in items
        ],
    }
    (ROOT / "paper_index.json").write_text(
        json.dumps(paper_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    short_lines = [
        "# Ge Zhang Academic Hub",
        "",
        f"- ORCID: https://orcid.org/{config['orcid']}",
        f"- Homepage: {config['site_url']}/",
        f"- All Publications: {config['site_url']}/publications.html",
        f"- Publications JSON: {config['site_url']}/publications.json",
        f"- Paper index: {config['site_url']}/paper_index.json",
        "",
        "## Deep GEO",
        "",
    ]
    for item in deep_items:
        doi_text = f" — DOI: {item['doi']}" if item.get("doi") else ""
        short_lines.append(f"- [{item['title']}]({item['paper_url']}){doi_text}")
    short_lines.append("")
    (ROOT / "llms.txt").write_text("\n".join(short_lines), encoding="utf-8")
    full_lines = [
        "# Ge Zhang Academic Hub — Full Publication Index",
        "",
        f"ORCID: https://orcid.org/{config['orcid']}",
        "",
    ]
    for item in items:
        full_lines.extend(
            [
                f"## {item['title']}",
                f"- Journal: {item.get('journal') or 'Unknown source'}",
                f"- Year: {item.get('year') or 'n.d.'}",
                f"- Type: {item.get('type') or 'Work'}",
                f"- DOI: {item.get('doi') or 'Not available'}",
                f"- HTML: {item['paper_url']}",
                f"- Markdown: {item['markdown_url']}",
                f"- Deep GEO: {'yes' if item['deep_geo'] else 'no'}",
                "",
            ]
        )
    (ROOT / "llms-full.txt").write_text("\n".join(full_lines), encoding="utf-8")


def build_site():
    config = load_site_config()
    master, _ = save_master(load_master())
    if ensure_public_slugs(master):
        master, _ = save_master(master)
    featured_entries = load_featured()
    deep_entries = load_deep_geo()
    master_by_token = index_master(master)
    validate_controller_entries(featured_entries, master_by_token, "Featured")
    validate_controller_entries(deep_entries, master_by_token, "Deep GEO")
    featured_tokens = {controller_token(entry) for entry in featured_entries}
    deep_tokens = {controller_token(entry) for entry in deep_entries}
    public_master = [publication for publication in master if not is_withdrawn(publication)]
    public_items = [
        public_record(
            publication,
            config=config,
            deep_tokens=deep_tokens,
            featured_tokens=featured_tokens,
        )
        for publication in public_master
    ]
    public_by_token = {publication_token(item): item for item in public_items}
    expected_slugs = {item["slug"] for item in public_items}
    missing_legacy = sorted(set(LEGACY_DEEP_SLUGS) - expected_slugs)
    if missing_legacy:
        raise ValueError("Protected legacy paper slug(s) missing: " + ", ".join(missing_legacy))
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    DEEP_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    for item in public_items:
        token = publication_token(item)
        deep_content = load_deep_content(item) if token in deep_tokens else None
        (PAPERS_DIR / f"{item['slug']}.html").write_text(
            render_paper_html(item, config=config, deep_content=deep_content), encoding="utf-8"
        )
        (PAPERS_DIR / f"{item['slug']}.md").write_text(
            render_paper_markdown(item, config=config, deep_content=deep_content), encoding="utf-8"
        )
    for path in list(PAPERS_DIR.glob("*.html")) + list(PAPERS_DIR.glob("*.md")):
        if path.stem not in expected_slugs and GENERATED_MARKER in path.read_text(
            encoding="utf-8", errors="ignore"
        ):
            path.unlink()

    (ROOT / "publications.json").write_text(
        json.dumps(public_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (ROOT / "publication_inventory.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "year", "title", "journal", "type", "doi",
                "paper_url", "deep_geo", "featured",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for item in public_items:
            writer.writerow(
                {
                    "year": item.get("year") or "",
                    "title": item.get("title") or "Untitled work",
                    "journal": item.get("journal") or "Unknown source",
                    "type": item.get("type") or "Work",
                    "doi": item.get("doi") or "",
                    "paper_url": item["paper_url"],
                    "deep_geo": str(bool(item["deep_geo"])).lower(),
                    "featured": str(bool(item["featured"])).lower(),
                }
            )
    (ROOT / "publications.html").write_text(
        render_publications_page(public_items, config), encoding="utf-8"
    )

    index_path = ROOT / "index.html"
    index_html = index_path.read_text(encoding="utf-8")
    if index_html.count(FEATURED_START) != 1 or index_html.count(FEATURED_END) != 1:
        raise ValueError("index.html must contain exactly one Featured controller marker pair.")
    before, remainder = index_html.split(FEATURED_START, 1)
    _, after = remainder.split(FEATURED_END, 1)
    index_html = (
        before + FEATURED_START + "\n"
        + render_featured_cards(featured_entries, master_by_token, deep_tokens)
        + "\n" + FEATURED_END + after
    )
    index_html = re.sub(
        r'View all (?:<span id="pubCount">\d+</span>|\d+) publications',
        f'View all <span id="pubCount">{len(public_items)}</span> publications',
        index_html,
    )
    index_path.write_text(index_html, encoding="utf-8")

    deep_items = [public_by_token[controller_token(entry)] for entry in deep_entries]
    write_machine_indexes(public_items, deep_items, config)
    urls = [
        f"{config['site_url']}/",
        absolute(config["site_url"], "publications.html"),
        *[item["paper_url"] for item in public_items],
    ]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls)
        + "\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    result = {
        "master": len(master),
        "public": len(public_items),
        "withdrawn": len(master) - len(public_items),
        "featured": len(featured_entries),
        "deep_geo": len(deep_entries),
        "sitemap": len(urls),
    }
    print(
        f"Built {result['public']} public paper pages from {result['master']} unique master "
        f"records; Featured={result['featured']}, Deep GEO={result['deep_geo']}, "
        f"withdrawn={result['withdrawn']}."
    )
    return result


if __name__ == "__main__":
    build_site()
