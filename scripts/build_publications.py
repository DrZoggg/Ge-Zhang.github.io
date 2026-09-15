import json, html, urllib.parse
from sync_common import ROOT, load_master

SITE_ROOT = "https://drzoggg.github.io/Ge-Zhang.github.io"
items = sorted(load_master(), key=lambda x: (-int(x.get("year") or 0), (x.get("title") or "").lower()))
(ROOT / "publications.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

def scholar(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote(f'"{title}"')

def doi_link(doi):
    return "https://doi.org/" + doi

by_year = {}
for p in items:
    by_year.setdefault(int(p.get("year") or 0), []).append(p)
sections = []
for yr in sorted(by_year, reverse=True):
    rows = []
    for p in by_year[yr]:
        title = p.get("title") or "Untitled work"
        journal = p.get("journal") or "Unknown source"
        typ = p.get("type") or "Work"
        links = []
        if p.get("doi"):
            links.append(f'<a href="{doi_link(p["doi"])}">DOI</a>')
        elif p.get("url"):
            links.append(f'<a href="{html.escape(p["url"], quote=True)}">Source</a>')
        if p.get("featured") and p.get("slug"):
            links.append(f'<a href="papers/{html.escape(p["slug"])}.html">GEO page</a>')
        links.append(f'<a href="{scholar(title)}">Scholar</a>')
        rows.append(
            f'<article class="pub" data-title="{html.escape(title.lower())}" data-journal="{html.escape(journal.lower())}">'
            f'<div class="pub-title">{html.escape(title)} <span class="badge">{html.escape(str(typ))}</span></div>'
            f'<div class="pub-meta">{html.escape(journal)} · {yr or "n.d."} · {" · ".join(links)}</div></article>'
        )
    sections.append(f'<section class="year-group"><h2 class="year">{yr or "Undated"}</h2>{"".join(rows)}</section>')

schema = {
    "@context": "https://schema.org", "@type": "ProfilePage", "name": "Ge Zhang — Publications",
    "mainEntity": {"@type": "Person", "name": "Ge Zhang", "identifier": "https://orcid.org/0000-0002-3116-3246"},
    "hasPart": []
}
for p in items:
    obj = {
        "@type": "ScholarlyArticle" if p.get("type") in ("Article", "Review") else "CreativeWork",
        "name": p.get("title") or "Untitled work",
        "datePublished": str(p.get("year") or ""),
    }
    if p.get("journal"):
        obj["isPartOf"] = {"@type": "Periodical", "name": p["journal"]}
    if p.get("doi"):
        obj["sameAs"] = doi_link(p["doi"])
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
page = page.replace("__COUNT__", str(len(items))).replace("__SECTIONS__", "".join(sections)).replace("__SCHEMA__", json.dumps(schema, ensure_ascii=False))
(ROOT / "publications.html").write_text(page, encoding="utf-8")

idx = ROOT / "index.html"
txt = idx.read_text(encoding="utf-8")
txt = txt.replace("View all 71 publications", 'View all <span id="pubCount">71</span> publications')
if 'fetch("publications.json")' not in txt:
    txt = txt.replace("</body>", '<script>fetch("publications.json").then(r=>r.json()).then(x=>{const e=document.getElementById("pubCount");if(e)e.textContent=x.length}).catch(()=>{});</script></body>')
idx.write_text(txt, encoding="utf-8")

urls = [f"{SITE_ROOT}/", f"{SITE_ROOT}/publications.html"]
for p in items:
    if p.get("featured") and p.get("slug"):
        urls.append(f'{SITE_ROOT}/papers/{p["slug"]}.html')
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += "\n".join(f"  <url><loc>{html.escape(u)}</loc></url>" for u in urls)
sitemap += "\n</urlset>\n"
(ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
print(f"Built publications page with {len(items)} records.")
