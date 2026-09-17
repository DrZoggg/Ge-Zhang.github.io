import csv
import html
import json
import re
import sys
import xml.etree.ElementTree as ET

from site_common import (
    LEGACY_DEEP_SLUGS,
    PAPERS_DIR,
    controller_token,
    deep_content_path,
    index_master,
    load_deep_geo,
    load_featured,
    load_site_config,
    publication_token,
    validate_controller_entries,
    validate_slug,
)
from sync_common import ROOT, is_withdrawn, load_master, norm_doi


class ValidationError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def validate_site():
    config = load_site_config()
    master = load_master()
    public_expected = [item for item in master if not is_withdrawn(item)]
    withdrawn = [item for item in master if is_withdrawn(item)]
    public_json = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
    paper_index_payload = json.loads((ROOT / "paper_index.json").read_text(encoding="utf-8"))
    paper_index = paper_index_payload.get("papers", [])
    featured = load_featured()
    deep_geo = load_deep_geo()
    master_by_token = index_master(master)
    validate_controller_entries(featured, master_by_token, "Featured")
    validate_controller_entries(deep_geo, master_by_token, "Deep GEO")

    master_dois = [norm_doi(item.get("doi")) for item in master if norm_doi(item.get("doi"))]
    require(
        len(master_dois) == len(set(master_dois)),
        "Master database contains duplicate DOI values.",
    )
    require(
        all("featured" not in item for item in master),
        "Legacy Featured flags remain in master metadata.",
    )
    require(
        len(public_json) == len(public_expected),
        f"publications.json count {len(public_json)} != expected {len(public_expected)}.",
    )
    require(
        len(paper_index) == len(public_expected),
        f"paper_index count {len(paper_index)} != expected {len(public_expected)}.",
    )
    require(
        not any(is_withdrawn(item) for item in public_json),
        "Withdrawn record appears in publications.json.",
    )
    withdrawn_dois = {norm_doi(item.get("doi")) for item in withdrawn if item.get("doi")}
    require(
        not withdrawn_dois.intersection(
            norm_doi(item.get("doi")) for item in paper_index if item.get("doi")
        ),
        "Withdrawn DOI appears in paper_index.json.",
    )

    slugs = [validate_slug(item.get("slug")) for item in public_expected]
    require(len(slugs) == len(set(slugs)), "Public paper slugs are not unique.")
    html_files = sorted(PAPERS_DIR.glob("*.html"))
    md_files = sorted(PAPERS_DIR.glob("*.md"))
    require(
        len(html_files) == len(public_expected),
        f"HTML paper count {len(html_files)} != public count {len(public_expected)}.",
    )
    require(
        len(md_files) == len(public_expected),
        f"Markdown paper count {len(md_files)} != public count {len(public_expected)}.",
    )
    require(
        {path.stem for path in html_files} == set(slugs),
        "HTML paper slugs do not exactly match public master records.",
    )
    require(
        {path.stem for path in md_files} == set(slugs),
        "Markdown paper slugs do not exactly match public master records.",
    )
    for item in withdrawn:
        slug = str(item.get("slug") or "").strip()
        if slug:
            require(not (PAPERS_DIR / f"{slug}.html").exists(), "Withdrawn HTML page exists.")
            require(not (PAPERS_DIR / f"{slug}.md").exists(), "Withdrawn Markdown page exists.")
    for slug in LEGACY_DEEP_SLUGS:
        require((PAPERS_DIR / f"{slug}.html").is_file(), f"Legacy URL missing: {slug}.html")
        require((PAPERS_DIR / f"{slug}.md").is_file(), f"Legacy Markdown missing: {slug}.md")

    canonical_urls = []
    public_by_token = {publication_token(item): item for item in public_expected}
    deep_tokens = {controller_token(entry) for entry in deep_geo}
    featured_tokens = {controller_token(entry) for entry in featured}
    for item in public_expected:
        slug = item["slug"]
        page = (PAPERS_DIR / f"{slug}.html").read_text(encoding="utf-8")
        markdown = (PAPERS_DIR / f"{slug}.md").read_text(encoding="utf-8")
        canonical_matches = re.findall(
            r'<link rel="canonical" href="([^"]+)"', page, flags=re.I
        )
        require(len(canonical_matches) == 1, f"{slug}.html must have one canonical URL.")
        canonical = html.unescape(canonical_matches[0])
        canonical_urls.append(canonical)
        expected_url = f"{config['site_url']}/papers/{slug}.html"
        require(canonical == expected_url, f"Wrong canonical URL for {slug}.html.")
        require(item.get("title", "") in page, f"Title missing from {slug}.html.")
        require(config["orcid"] in page, f"ORCID anchor missing from {slug}.html.")
        require(expected_url in markdown, f"HTML URL missing from {slug}.md.")
        require(
            f"{config['site_url']}/papers/{slug}.md" in page,
            f"Markdown alternate missing from {slug}.html.",
        )
        doi = norm_doi(item.get("doi"))
        if doi:
            require(f"https://doi.org/{doi}" in page, f"DOI link missing from {slug}.html.")
        token = publication_token(item)
        if token in deep_tokens:
            content_path = deep_content_path(item)
            require(content_path.is_file(), f"Deep GEO content missing for {slug}.")
            content = json.loads(content_path.read_text(encoding="utf-8"))
            for value in [
                content.get("summary"),
                *(content.get("keywords") or []),
                *(content.get("questions") or []),
            ]:
                if str(value or "").strip():
                    require(
                        html.escape(str(value), quote=False) in page
                        or str(value) in page,
                        f"Deep GEO content lost from {slug}.html: {value!r}",
                    )
                    require(str(value) in markdown, f"Deep GEO content lost from {slug}.md.")
        require(
            ('<span class="badge">Deep GEO</span>' in page) == (token in deep_tokens),
            f"Deep GEO badge/state mismatch for {slug}.html.",
        )
    require(
        len(canonical_urls) == len(set(canonical_urls)),
        "Paper canonical URLs are not unique.",
    )

    require(
        {publication_token(item) for item in public_json}
        == {publication_token(item) for item in public_expected},
        "publications.json identities do not match public master records.",
    )
    for item in public_json:
        token = publication_token(item)
        require(bool(item.get("deep_geo")) == (token in deep_tokens), "Deep GEO flag mismatch.")
        require(bool(item.get("featured")) == (token in featured_tokens), "Featured flag mismatch.")

    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    featured_titles = [master_by_token[controller_token(entry)]["title"] for entry in featured]
    positions = [index_html.find(title) for title in featured_titles]
    require(all(position >= 0 for position in positions), "Featured title missing from homepage.")
    require(positions == sorted(positions), "Homepage Featured order differs from controller.")
    require(
        index_html.count('<article class="card paper">') == len(featured),
        "Homepage Featured card count differs from controller.",
    )

    publications_html = (ROOT / "publications.html").read_text(encoding="utf-8")
    require(
        publications_html.count('data-paper-record="true"') == len(public_expected),
        "publications.html paper count differs from public master count.",
    )
    require(
        not any(item.get("title", "") in publications_html for item in withdrawn),
        "Withdrawn title appears in publications.html.",
    )

    with (ROOT / "publication_inventory.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        csv_rows = list(csv.DictReader(handle))
    require(
        len(csv_rows) == len(public_expected),
        f"CSV count {len(csv_rows)} != public count {len(public_expected)}.",
    )
    required_csv = {
        "year", "title", "journal", "type", "doi", "paper_url", "deep_geo", "featured"
    }
    require(required_csv.issubset(csv_rows[0].keys()), "CSV required fields are missing.")

    tree = ET.parse(ROOT / "sitemap.xml")
    sitemap_urls = [
        node.text for node in tree.getroot().iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]
    expected_urls = [
        f"{config['site_url']}/",
        f"{config['site_url']}/publications.html",
        *[f"{config['site_url']}/papers/{slug}.html" for slug in slugs],
    ]
    require(len(sitemap_urls) == len(set(sitemap_urls)), "Sitemap contains duplicate URLs.")
    require(set(sitemap_urls) == set(expected_urls), "Sitemap URLs do not match public pages.")
    for item in withdrawn:
        slug = str(item.get("slug") or "")
        require(not slug or not any(slug in url for url in sitemap_urls), "Withdrawn in sitemap.")
    for entry in featured:
        item = public_by_token[controller_token(entry)]
        require(
            f"{config['site_url']}/papers/{item['slug']}.html" in sitemap_urls,
            "Featured URL missing from sitemap.",
        )

    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    llms_full = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    require(f"{config['site_url']}/paper_index.json" in llms, "paper_index missing from llms.txt.")
    require(llms.count("](https://") >= len(deep_geo), "Deep GEO list incomplete in llms.txt.")
    require(llms_full.count("\n## ") == len(public_expected), "llms-full paper count mismatch.")
    for item in withdrawn:
        require(item.get("title", "") not in llms_full, "Withdrawn title in llms-full.txt.")

    result = {
        "master": len(master),
        "public": len(public_expected),
        "withdrawn": len(withdrawn),
        "featured": len(featured),
        "deep_geo": len(deep_geo),
        "html_pages": len(html_files),
        "markdown_pages": len(md_files),
        "sitemap_urls": len(sitemap_urls),
        "doi_duplicates": len(master_dois) - len(set(master_dois)),
    }
    print("VALIDATION PASS")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    try:
        validate_site()
    except (ValidationError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
