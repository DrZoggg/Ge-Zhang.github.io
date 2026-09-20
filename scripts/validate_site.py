import csv
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

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


CANONICAL_SITE_URL = "https://drgezhang.com"
LEGACY_SITE_URL = "https://drzoggg.github.io/Ge-Zhang.github.io"


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def normalized_source_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalized_parsed_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


class ElementTextParser(HTMLParser):
    """Collect decoded visible text from matching HTML elements."""

    def __init__(self, tag, required_attributes=None):
        super().__init__(convert_charrefs=True)
        self.tag = tag.casefold()
        self.required_attributes = required_attributes or {}
        self.depth = 0
        self.buffer = []
        self.texts = []

    def matches(self, tag, attributes):
        if tag.casefold() != self.tag:
            return False
        attributes = {name.casefold(): (value or "") for name, value in attributes}
        for name, expected in self.required_attributes.items():
            actual = attributes.get(name.casefold(), "")
            if name.casefold() == "class":
                if expected not in actual.split():
                    return False
            elif actual != expected:
                return False
        return True

    def handle_starttag(self, tag, attributes):
        if self.depth:
            self.depth += 1
        elif self.matches(tag, attributes):
            self.depth = 1
            self.buffer = []

    def handle_endtag(self, tag):
        if not self.depth:
            return
        self.depth -= 1
        if self.depth == 0:
            self.texts.append(normalized_parsed_text("".join(self.buffer)))
            self.buffer = []

    def handle_data(self, data):
        if self.depth:
            self.buffer.append(data)


class VisibleTextParser(HTMLParser):
    """Collect page text while excluding scripts and styles."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attributes):
        if tag.casefold() in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag):
        if tag.casefold() in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data):
        if not self.hidden_depth:
            self.parts.append(data)


def element_texts(markup, tag, required_attributes=None):
    parser = ElementTextParser(tag, required_attributes)
    parser.feed(markup)
    parser.close()
    return parser.texts


def visible_text(markup):
    parser = VisibleTextParser()
    parser.feed(markup)
    parser.close()
    return normalized_parsed_text(" ".join(parser.parts))


def single_html_url(markup, pattern, label):
    matches = re.findall(pattern, markup, flags=re.I)
    require(len(matches) == 1, f"{label} must appear exactly once.")
    return html.unescape(matches[0])


def json_ld_objects(markup):
    payloads = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', markup, flags=re.I | re.S
    )
    return [json.loads(payload) for payload in payloads]


def json_ld_object(markup, schema_type, label):
    matches = [item for item in json_ld_objects(markup) if item.get("@type") == schema_type]
    require(len(matches) == 1, f"{label} must contain exactly one {schema_type} JSON-LD object.")
    return matches[0]


def paper_json_ld_object(markup, label):
    matches = [
        item
        for item in json_ld_objects(markup)
        if item.get("@type") in {"ScholarlyArticle", "CreativeWork"}
    ]
    require(len(matches) == 1, f"{label} must contain exactly one paper JSON-LD object.")
    return matches[0]


def validate_html_text_decoding(master):
    pap_title = (
        "PAPPA2 c.392G>C Heterozygous Mutation Associates Primary Open-Angle "
        "Glaucoma in a Chinese Family"
    )
    real_titles = [str(item.get("title") or "") for item in master]
    require(pap_title in real_titles, "PAPPA2 title regression fixture is missing.")
    apostrophe_titles = [title for title in real_titles if "'" in title]
    require(apostrophe_titles, "ASCII-apostrophe title regression fixture is missing.")
    regression_titles = [
        pap_title,
        apostrophe_titles[0],
        'Synthetic A < B & "quoted" patient\'s title',
    ]
    for title in regression_titles:
        serialized = f"<h1>{html.escape(title)}</h1>"
        require(
            element_texts(serialized, "h1") == [normalized_source_text(title)],
            f"HTML title decoding regression failed: {title!r}",
        )
    literal_entity_cases = [
        ("<h1>A &amp;gt; B &amp;amp; C</h1>", "A &gt; B &amp; C"),
        ("<h1>A &amp;amp;gt; B &amp;amp;amp; C</h1>", "A &amp;gt; B &amp;amp; C"),
    ]
    for serialized, parsed in literal_entity_cases:
        require(
            element_texts(serialized, "h1") == [parsed],
            f"Literal HTML entity regression failed: {serialized!r}",
        )


def validate_site():
    config = load_site_config()
    require(
        config["site_url"] == CANONICAL_SITE_URL,
        f"Canonical site origin must be {CANONICAL_SITE_URL}.",
    )
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
    validate_html_text_decoding(master)

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
        canonical = single_html_url(
            page,
            r'<link rel="canonical" href="([^"]+)"',
            f"{slug}.html canonical URL",
        )
        canonical_urls.append(canonical)
        expected_url = f"{config['site_url']}/papers/{slug}.html"
        expected_markdown_url = f"{config['site_url']}/papers/{slug}.md"
        require(canonical == expected_url, f"Wrong canonical URL for {slug}.html.")
        og_url = single_html_url(
            page,
            r'<meta property="og:url" content="([^"]+)"',
            f"{slug}.html Open Graph URL",
        )
        require(og_url == expected_url, f"Wrong Open Graph URL for {slug}.html.")
        schema = paper_json_ld_object(page, f"{slug}.html")
        require(schema.get("url") == expected_url, f"Wrong Schema.org URL for {slug}.html.")
        require(
            schema.get("mainEntityOfPage") == expected_url,
            f"Wrong Schema.org mainEntityOfPage for {slug}.html.",
        )
        h1_titles = element_texts(page, "h1")
        require(len(h1_titles) == 1, f"{slug}.html must have exactly one h1 title.")
        require(
            h1_titles[0] == normalized_source_text(item.get("title", "")),
            f"Visible h1 title mismatch in {slug}.html.",
        )
        require(config["orcid"] in page, f"ORCID anchor missing from {slug}.html.")
        require(
            f"Canonical page: {expected_url}" in markdown,
            f"Canonical page URL missing from {slug}.md.",
        )
        require(
            f"Markdown record: {expected_markdown_url}" in markdown,
            f"Markdown record URL missing from {slug}.md.",
        )
        require(
            expected_markdown_url in page,
            f"Markdown alternate missing from {slug}.html.",
        )
        require(LEGACY_SITE_URL not in page, f"Legacy origin remains in {slug}.html.")
        require(LEGACY_SITE_URL not in markdown, f"Legacy origin remains in {slug}.md.")
        doi = norm_doi(item.get("doi"))
        if doi:
            require(f"https://doi.org/{doi}" in page, f"DOI link missing from {slug}.html.")
        token = publication_token(item)
        if token in deep_tokens:
            content_path = deep_content_path(item)
            require(content_path.is_file(), f"Deep GEO content missing for {slug}.")
            content = json.loads(content_path.read_text(encoding="utf-8"))
            page_text = visible_text(page)
            for value in [
                content.get("summary"),
                *(content.get("keywords") or []),
                *(content.get("questions") or []),
            ]:
                if str(value or "").strip():
                    require(
                        normalized_source_text(value) in page_text,
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
    expected_html_urls = {f"{config['site_url']}/papers/{slug}.html" for slug in slugs}
    expected_markdown_urls = {f"{config['site_url']}/papers/{slug}.md" for slug in slugs}
    for payload, label in ((public_json, "publications.json"), (paper_index, "paper_index.json")):
        require(
            {item.get("paper_url") for item in payload} == expected_html_urls,
            f"{label} paper URLs do not match the canonical origin.",
        )
        require(
            {item.get("markdown_url") for item in payload} == expected_markdown_urls,
            f"{label} Markdown URLs do not match the canonical origin.",
        )

    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    homepage_url = f"{config['site_url']}/"
    require(
        single_html_url(
            index_html,
            r'<link rel="canonical" href="([^"]+)"',
            "Homepage canonical URL",
        ) == homepage_url,
        "Wrong homepage canonical URL.",
    )
    require(
        single_html_url(
            index_html,
            r'<meta property="og:url" content="([^"]+)"',
            "Homepage Open Graph URL",
        ) == homepage_url,
        "Wrong homepage Open Graph URL.",
    )
    homepage_schema = json_ld_object(index_html, "Person", "Homepage")
    require(homepage_schema.get("url") == homepage_url, "Wrong homepage Schema.org URL.")
    featured_titles = [
        normalized_source_text(master_by_token[controller_token(entry)]["title"])
        for entry in featured
    ]
    featured_start = "<!-- FEATURED_PAPERS_START -->"
    featured_end = "<!-- FEATURED_PAPERS_END -->"
    require(
        index_html.count(featured_start) == 1 and index_html.count(featured_end) == 1,
        "Homepage Featured markers are missing or duplicated.",
    )
    featured_html = index_html.split(featured_start, 1)[1].split(featured_end, 1)[0]
    rendered_featured_titles = element_texts(featured_html, "h3")
    require(
        rendered_featured_titles == featured_titles,
        "Homepage Featured titles or order differ from controller.",
    )
    require(
        index_html.count('<article class="card paper">') == len(featured),
        "Homepage Featured card count differs from controller.",
    )

    publications_html = (ROOT / "publications.html").read_text(encoding="utf-8")
    publications_url = f"{config['site_url']}/publications.html"
    require(
        single_html_url(
            publications_html,
            r'<link rel="canonical" href="([^"]+)"',
            "Publications canonical URL",
        ) == publications_url,
        "Wrong publications canonical URL.",
    )
    require(
        single_html_url(
            publications_html,
            r'<meta property="og:url" content="([^"]+)"',
            "Publications Open Graph URL",
        ) == publications_url,
        "Wrong publications Open Graph URL.",
    )
    publications_schema = json_ld_object(publications_html, "ProfilePage", "Publications page")
    require(
        publications_schema.get("url") == publications_url,
        "Wrong publications Schema.org URL.",
    )
    require(
        publications_html.count('data-paper-record="true"') == len(public_expected),
        "publications.html paper count differs from public master count.",
    )
    publication_title_regions = element_texts(
        publications_html, "div", {"class": "pub-title"}
    )
    for item in withdrawn:
        withdrawn_title = normalized_source_text(item.get("title", ""))
        require(
            not any(withdrawn_title in title for title in publication_title_regions),
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
    require(
        {row["paper_url"] for row in csv_rows} == expected_html_urls,
        "CSV paper URLs do not match the canonical origin.",
    )

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

    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    require(
        robots == f"User-agent: *\nAllow: /\nSitemap: {config['site_url']}/sitemap.xml\n",
        "robots.txt does not use the canonical sitemap URL.",
    )

    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    llms_full = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    for expected in (
        f"{config['site_url']}/",
        f"{config['site_url']}/publications.html",
        f"{config['site_url']}/publications.json",
        f"{config['site_url']}/paper_index.json",
    ):
        require(expected in llms, f"Canonical link missing from llms.txt: {expected}")
    require(f"{config['site_url']}/paper_index.json" in llms, "paper_index missing from llms.txt.")
    require(llms.count("](https://") >= len(deep_geo), "Deep GEO list incomplete in llms.txt.")
    require(llms_full.count("\n## ") == len(public_expected), "llms-full paper count mismatch.")
    for expected in expected_html_urls | expected_markdown_urls:
        require(expected in llms_full, f"Canonical paper link missing from llms-full.txt: {expected}")
    require(LEGACY_SITE_URL not in llms, "Legacy origin remains in llms.txt.")
    require(LEGACY_SITE_URL not in llms_full, "Legacy origin remains in llms-full.txt.")
    require(LEGACY_SITE_URL not in robots, "Legacy origin remains in robots.txt.")
    require(LEGACY_SITE_URL not in (ROOT / "sitemap.xml").read_text(encoding="utf-8"),
            "Legacy origin remains in sitemap.xml.")
    require(LEGACY_SITE_URL not in index_html, "Legacy origin remains in index.html.")
    require(LEGACY_SITE_URL not in publications_html,
            "Legacy origin remains in publications.html.")
    require(LEGACY_SITE_URL not in json.dumps(public_json, ensure_ascii=False),
            "Legacy origin remains in publications.json.")
    require(LEGACY_SITE_URL not in json.dumps(paper_index_payload, ensure_ascii=False),
            "Legacy origin remains in paper_index.json.")
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
