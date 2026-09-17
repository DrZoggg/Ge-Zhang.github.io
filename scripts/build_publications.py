import copy
import csv
import html
import json
import re
import urllib.parse

from sync_common import ROOT, is_withdrawn, load_master, norm_doi, save_master


SITE_ROOT = "https://drzoggg.github.io/Ge-Zhang.github.io"
FEATURED_CONFIG = ROOT / "data" / "featured_papers.json"
PAPERS_DIR = ROOT / "papers"
FEATURED_START = "<!-- FEATURED_PAPERS_START -->"
FEATURED_END = "<!-- FEATURED_PAPERS_END -->"


def load_featured_controller():
    if not FEATURED_CONFIG.exists():
        raise SystemExit(f"Missing Featured Paper Controller: {FEATURED_CONFIG}")

    payload = json.loads(FEATURED_CONFIG.read_text(encoding="utf-8"))
    if payload.get("version") != 1 or not isinstance(payload.get("papers"), list):
        raise SystemExit("data/featured_papers.json must contain version 1 and a papers array.")

    entries = []
    seen = set()
    for position, raw in enumerate(payload["papers"], start=1):
        if not isinstance(raw, dict):
            raise SystemExit(f"Featured entry {position} must be a JSON object.")
        doi = norm_doi(raw.get("doi"))
        if not doi:
            raise SystemExit(f"Featured entry {position} is missing a valid DOI.")
        if doi in seen:
            raise SystemExit(f"Featured DOI is listed more than once: {doi}")
        seen.add(doi)
        entries.append({
            "doi": doi,
            "summary": str(raw.get("summary") or "").strip(),
        })
    return entries


def deep_geo_url(publication):
    slug = str(publication.get("slug") or "").strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        return ""
    relative_url = f"papers/{slug}.html"
    return relative_url if (ROOT / relative_url).is_file() else ""


def scholar(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote(f'"{title}"')


def doi_link(doi):
    return "https://doi.org/" + doi


featured_entries = load_featured_controller()
featured_dois = {entry["doi"] for entry in featured_entries}

# Featured status is presentation state owned by featured_papers.json, not publication metadata.
raw_master = load_master()
for record in raw_master:
    record.pop("featured", None)
master, _ = save_master(raw_master)

master_by_doi = {}
for publication in master:
    doi = norm_doi(publication.get("doi"))
    if not doi:
        continue
    if doi in master_by_doi:
        raise SystemExit(f"Duplicate DOI in master database: {doi}")
    master_by_doi[doi] = publication

missing_featured = [entry["doi"] for entry in featured_entries if entry["doi"] not in master_by_doi]
if missing_featured:
    raise SystemExit(
        "Featured DOI(s) not found in master database: " + ", ".join(missing_featured)
    )

withdrawn_featured = [
    entry["doi"]
    for entry in featured_entries
    if is_withdrawn(master_by_doi[entry["doi"]])
]
if withdrawn_featured:
    raise SystemExit(
        "Withdrawn work(s) cannot be Featured: " + ", ".join(withdrawn_featured)
    )

items = []
for publication in master:
    if is_withdrawn(publication):
        continue
    is_featured = norm_doi(publication.get("doi")) in featured_dois
    public_item = {}
    for key, value in copy.deepcopy(publication).items():
        public_item[key] = value
        if key == "doi" and is_featured:
            public_item["featured"] = True
    if is_featured and "featured" not in public_item:
        public_item["featured"] = True
    items.append(public_item)

(ROOT / "publications.json").write_text(
    json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
)

with (ROOT / "publication_inventory.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=["year", "title", "journal", "type", "doi", "featured"],
        extrasaction="ignore",
    )
    writer.writeheader()
    for item in items:
        writer.writerow({
            "year": item.get("year") or "",
            "title": item.get("title") or "Untitled work",
            "journal": item.get("journal") or "Unknown source",
            "type": item.get("type") or "Work",
            "doi": item.get("doi") or "",
            "featured": True if item.get("featured") else "",
        })

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
        links = []
        if publication.get("doi"):
            links.append(f'<a href="{doi_link(publication["doi"])}">DOI</a>')
        elif publication.get("url"):
            links.append(f'<a href="{html.escape(publication["url"], quote=True)}">Source</a>')
        deep_url = deep_geo_url(publication)
        if deep_url:
            links.append(f'<a href="{html.escape(deep_url, quote=True)}">GEO page</a>')
        links.append(f'<a href="{scholar(title)}">Scholar</a>')
        rows.append(
            f'<article class="pub" data-title="{html.escape(title.lower())}" '
            f'data-journal="{html.escape(journal.lower())}">'
            f'<div class="pub-title">{html.escape(title)} '
            f'<span class="badge">{html.escape(str(publication_type))}</span></div>'
            f'<div class="pub-meta">{html.escape(journal)} · {year or "n.d."} · '
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
    "mainEntity": {
        "@type": "Person",
        "name": "Ge Zhang",
        "identifier": "https://orcid.org/0000-0002-3116-3246",
    },
    "hasPart": [],
}
for publication in items:
    obj = {
        "@type": "ScholarlyArticle"
        if publication.get("type") in ("Article", "Review")
        else "CreativeWork",
        "name": publication.get("title") or "Untitled work",
        "datePublished": str(publication.get("year") or ""),
    }
    if publication.get("journal"):
        obj["isPartOf"] = {"@type": "Periodical", "name": publication["journal"]}
    if publication.get("doi"):
        obj["sameAs"] = doi_link(publication["doi"])
    schema["hasPart"].append(obj)

page = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All Publications | Ge Zhang</title>
<meta name="description" content="Publication record of Ge Zhang, using ORCID 0000-0002-3116-3246 as the identity anchor.">
<link rel="stylesheet" href="assets/style.css"></head><body>
<header><nav><a class="brand" href="index.html">Ge Zhang</a><div class="navlinks">
<a href="index.html#research">Research</a><a href="publications.html">All publications</a><a href="index.html#profiles">Profiles</a></div></nav></header>
<main class="wrap"><section class="hero" style="grid-template-columns:1fr"><div>
<div class="eyebrow">Publication record</div><h1 style="font-size:clamp(2.8rem,6vw,4.7rem)">Publications</h1>
<p class="lead">This author-controlled record uses ORCID 0000-0002-3116-3246 as the identity anchor. DOI-registered publications can be automatically discovered through Crossref using the same ORCID identifier.</p>
<div class="card" style="margin-top:20px"><div class="count">__COUNT__</div><div class="meta">works in the current master database</div></div>
</div></section>
<section><input id="pubSearch" class="search" placeholder="Search title or journal..." aria-label="Search publications">
<div id="pubList">__SECTIONS__</div></section>
<section><div class="notice"><strong>Identity control:</strong> automated discovery uses the exact ORCID iD rather than the author name “Ge Zhang”, reducing same-name misattribution.</div></section>
<script>
const box=document.getElementById('pubSearch');box.addEventListener('input',()=>{const q=box.value.toLowerCase().trim();document.querySelectorAll('.pub').forEach(x=>{x.style.display=(!q||x.dataset.title.includes(q)||x.dataset.journal.includes(q))?'block':'none'});document.querySelectorAll('.year-group').forEach(y=>{y.style.display=[...y.querySelectorAll('.pub')].some(x=>x.style.display!=='none')?'block':'none'})})
</script>
<script type="application/ld+json">__SCHEMA__</script>
</main><footer><div class="wrap">© Ge Zhang · Academic website · ORCID: 0000-0002-3116-3246</div></footer></body></html>'''
page = (
    page.replace("__COUNT__", str(len(items)))
    .replace("__SECTIONS__", "".join(sections))
    .replace("__SCHEMA__", json.dumps(schema, ensure_ascii=False))
)
(ROOT / "publications.html").write_text(page, encoding="utf-8")


def render_featured_cards():
    cards = []
    for entry in featured_entries:
        publication = master_by_doi[entry["doi"]]
        title = publication.get("title") or "Untitled work"
        journal = publication.get("journal") or "Unknown source"
        year = publication.get("year") or "n.d."
        deep_url = deep_geo_url(publication)
        doi_url = doi_link(entry["doi"])
        primary_url = deep_url or doi_url or publication.get("url") or "publications.html"
        summary = entry["summary"] or f"Research publication in {journal}."

        links = []
        if deep_url:
            links.append(f'<a class="btn" href="{html.escape(deep_url, quote=True)}">Research page</a>')
        if entry["doi"]:
            links.append(f'<a class="btn" href="{doi_url}">DOI</a>')
        elif publication.get("url"):
            links.append(
                f'<a class="btn" href="{html.escape(publication["url"], quote=True)}">Source</a>'
            )
        else:
            links.append('<a class="btn" href="publications.html">Publication record</a>')

        cards.append(
            f'<article class="card paper"><div class="eyebrow">'
            f'{html.escape(str(journal))} · {html.escape(str(year))}</div>'
            f'<h3><a href="{html.escape(str(primary_url), quote=True)}">'
            f'{html.escape(str(title))}</a></h3><p>{html.escape(summary)}</p>'
            f'<div class="links">{" ".join(links)}</div></article>'
        )
    return '<div class="grid">' + "".join(cards) + "</div>"


index_path = ROOT / "index.html"
index_html = index_path.read_text(encoding="utf-8")
if index_html.count(FEATURED_START) != 1 or index_html.count(FEATURED_END) != 1:
    raise SystemExit("index.html must contain exactly one Featured controller marker pair.")

before_featured, remainder = index_html.split(FEATURED_START, 1)
_, after_featured = remainder.split(FEATURED_END, 1)
index_html = (
    before_featured
    + FEATURED_START
    + "\n"
    + render_featured_cards()
    + "\n"
    + FEATURED_END
    + after_featured
)
index_html = re.sub(
    r"View all (?:<span id=\"pubCount\">\d+</span>|\d+) publications",
    f'View all <span id="pubCount">{len(items)}</span> publications',
    index_html,
)
index_path.write_text(index_html, encoding="utf-8")

urls = [f"{SITE_ROOT}/", f"{SITE_ROOT}/publications.html"]
known_urls = set(urls)

# Deep GEO URLs are independent of Featured status. Preserve every existing page URL.
for publication in items:
    deep_url = deep_geo_url(publication)
    if deep_url:
        absolute_url = f"{SITE_ROOT}/{deep_url}"
        if absolute_url not in known_urls:
            urls.append(absolute_url)
            known_urls.add(absolute_url)
for paper_path in sorted(PAPERS_DIR.glob("*.html")):
    absolute_url = f"{SITE_ROOT}/papers/{paper_path.name}"
    if absolute_url not in known_urls:
        urls.append(absolute_url)
        known_urls.add(absolute_url)

sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls)
sitemap += "\n</urlset>\n"
(ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

print(
    f"Built publications page with {len(items)} public records "
    f"from {len(master)} unique master records; "
    f"rendered {len(featured_entries)} Featured cards."
)
