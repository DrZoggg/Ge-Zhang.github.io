import csv
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from html.parser import HTMLParser

from build_publications import (
    flatten_concepts,
    resolve_related_papers,
    validate_deep_v2_content,
)
from site_common import (
    LEGACY_DEEP_SLUGS,
    PAPERS_DIR,
    PROFILE_CONFIG_PATH,
    SITE_CONFIG_PATH,
    controller_token,
    deep_content_path,
    index_master,
    load_deep_geo,
    load_featured,
    load_profile_config,
    load_site_config,
    publication_token,
    validate_controller_entries,
    validate_homepage_research,
    validate_slug,
)
from sync_common import (
    ROOT,
    exact_name_match,
    is_withdrawn,
    load_master,
    norm_doi,
    normalize_authors,
)


class ValidationError(RuntimeError):
    pass


CANONICAL_SITE_URL = "https://drgezhang.com"
LEGACY_SITE_URL = "https://drzoggg.github.io/Ge-Zhang.github.io"
INDEXNOW_CONFIG_PATH = ROOT / "data" / "indexnow_config.json"
AIHFLEVEL_DOI = "10.1038/s41467-024-50415-9"


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


def single_meta_content(markup, name, label):
    return single_html_url(
        markup,
        rf'<meta name="{re.escape(name)}" content="([^"]*)">',
        label,
    )


def meta_contents(markup, name):
    return [
        html.unescape(value)
        for value in re.findall(
            rf'<meta name="{re.escape(name)}" content="([^"]*)">',
            markup,
            flags=re.I,
        )
    ]


def same_as_values(value):
    if isinstance(value, list):
        return value
    return [value] if value else []


def validate_researcher_reference(person, config, label):
    require(isinstance(person, dict), f"{label} must be a Person object.")
    require(person.get("@type") == "Person", f"{label} must use @type Person.")
    require(person.get("@id") == config["person_id"], f"Wrong Person @id in {label}.")
    require(person.get("name") == config["researcher_name"], f"Wrong Person name in {label}.")
    alternate_names = person.get("alternateName") or []
    if not isinstance(alternate_names, list):
        alternate_names = [alternate_names]
    require(
        alternate_names == [config["researcher_name_zh"]],
        f"alternateName in {label} must contain only the verified Chinese name.",
    )
    require(person.get("url") == f"{config['site_url']}/", f"Wrong Person URL in {label}.")
    require(
        f"https://orcid.org/{config['orcid']}" in same_as_values(person.get("sameAs")),
        f"ORCID sameAs missing from {label}.",
    )


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


def string_leaves(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from string_leaves(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from string_leaves(item)


def validate_aihflevel_v2(content, publication, page, markdown, schema, public_by_doi, config):
    label = "AIHFLevel Paper GEO 2.0"
    validate_deep_v2_content(content, label)
    require(content.get("version") == 2, f"{label} must use version 2.")
    require(norm_doi(content.get("doi")) == AIHFLEVEL_DOI, f"{label} DOI changed.")
    require(
        norm_doi(publication.get("doi")) == AIHFLEVEL_DOI,
        f"{label} does not match its master record.",
    )

    study = content["study_profile"]
    require(study["unique_total_n"] == 1736, f"{label} unique total changed.")
    cohorts = {item["name"]: item for item in study["cohorts"]}
    require(
        {name: cohorts[name]["n"] for name in cohorts}
        == {
            "CRCCD Discovery": 498,
            "CRCCD Replication": 214,
            "CRCCD Meta": 712,
            "BIDMC": 1024,
        },
        f"{label} cohort sample counts changed.",
    )
    require(
        cohorts["CRCCD Discovery"].get("subset_of") == "CRCCD Meta"
        and cohorts["CRCCD Replication"].get("subset_of") == "CRCCD Meta",
        f"{label} cohort hierarchy changed.",
    )
    require(
        cohorts["CRCCD Meta"].get("contains")
        == ["CRCCD Discovery", "CRCCD Replication"],
        f"{label} parent cohort membership changed.",
    )

    model = content["model_profile"]
    require(
        {
            "initial_variables": model.get("initial_variables"),
            "candidate_survival_features": model.get("candidate_survival_features"),
            "algorithm_count": model.get("algorithm_count"),
            "modeling_schemes": model.get("modeling_schemes"),
            "final_predictor_count": model.get("final_predictor_count"),
        }
        == {
            "initial_variables": 93,
            "candidate_survival_features": 46,
            "algorithm_count": 12,
            "modeling_schemes": 132,
            "final_predictor_count": 12,
        },
        f"{label} model counts changed.",
    )
    findings = {item["id"]: item for item in content["key_findings"]}
    expected_evidence = {
        "KF1": [("average C-index", "0.821")],
        "KF2": [
            ("6-month AUC", "0.902"),
            ("12-month AUC", "0.932"),
            ("24-month AUC", "0.932"),
            ("30-month AUC", "0.903"),
        ],
        "KF3": [
            ("6-month AUC", "0.931"),
            ("12-month AUC", "0.952"),
            ("24-month AUC", "0.973"),
            ("30-month AUC", "0.976"),
        ],
        "KF4": [
            ("1-year AUC", "0.788"),
            ("2-year AUC", "0.816"),
            ("3-year AUC", "0.824"),
            ("4-year AUC", "0.846"),
        ],
        "KF5": [
            ("low risk", "AIHFLevel <= 0.435"),
            ("intermediate risk", "0.435 < AIHFLevel <= 1.548"),
            ("high risk", "AIHFLevel > 1.548"),
        ],
    }
    expected_locators = {
        "KF1": "Results: Survival assessment system AIHFLevel; Fig. 2b",
        "KF2": "Fig. 2e",
        "KF3": "Supplementary Fig. 3c",
        "KF4": "Fig. 6d",
        "KF5": "Fig. 4a-c",
    }
    require(list(findings) == list(expected_evidence), f"{label} finding IDs changed.")
    for finding_id, expected in expected_evidence.items():
        actual = [
            (item["label"], item["value"])
            for item in findings[finding_id]["evidence"]
        ]
        require(actual == expected, f"{label} {finding_id} evidence changed.")
        require(
            findings[finding_id]["source_locator"] == expected_locators[finding_id],
            f"{label} {finding_id} source locator changed.",
        )
        if len(expected) > 1:
            require(
                page.count(f'data-key-finding-id="{finding_id}"') == 2,
                f"{label} {finding_id} must render a semantic evidence table.",
            )

    finding_ids = set(findings)
    require(len(content["qa"]) == 8, f"{label} Q&A count changed.")
    for item in content["qa"]:
        require(
            set(item.get("evidence_refs", [])).issubset(finding_ids),
            f"{label} Q&A references an unknown finding.",
        )
    require("<details" not in page.casefold(), f"{label} Q&A must remain ordinary HTML.")
    require(
        not any(item.get("@type") == "FAQPage" for item in json_ld_objects(page)),
        f"{label} must not emit FAQPage schema.",
    )

    expected_authors = normalize_authors(publication.get("authors"))
    require(
        element_texts(page, "li", {"class": "paper-geo-v2__author"})
        == expected_authors,
        f"{label} visible full authors differ from master order.",
    )
    for position, author in enumerate(expected_authors, start=1):
        require(
            f"{position}. {author}" in markdown,
            f"{label} Markdown author order differs from master.",
        )

    expected_headings = [
        "Full Authors",
        "Evidence Snapshot",
        "Research Question",
        "Author Evidence Summary",
        "Key Findings",
        "Study Design & Model Development",
        "What This Study Adds",
        "Evidence Scope",
        "Q&A",
        "Concepts & Entities",
        "Related Research",
        "Publication & Provenance",
    ]
    require(element_texts(page, "h2") == expected_headings, f"{label} section order changed.")
    require(
        page.index('class="paper-geo-v2__authors"')
        < page.index('data-v2-section="evidence-snapshot"'),
        f"{label} authors must precede the evidence snapshot.",
    )
    section_markers = [
        "evidence-snapshot",
        "research-question",
        "author-summary",
        "key-findings",
        "study-design",
        "what-this-adds",
        "evidence-scope",
        "qa",
        "concepts",
        "related-research",
        "provenance",
    ]
    positions = [page.index(f'data-v2-section="{marker}"') for marker in section_markers]
    require(positions == sorted(positions), f"{label} HTML section order changed.")
    require(
        page.index('class="paper-geo-v2__notice"') > positions[-1],
        f"{label} evidence-page notice must follow provenance.",
    )
    require(
        "does not replace the publisher version or assert a complete author list" not in page,
        f"{label} retains the obsolete author-list notice.",
    )

    page_text = visible_text(page)
    for value in string_leaves(content):
        require(
            normalized_source_text(value) in page_text,
            f"{label} content lost from HTML: {value!r}",
        )
        require(value in markdown, f"{label} content lost from Markdown: {value!r}")

    concepts = flatten_concepts(content)
    require(
        len(concepts) == len({item.casefold() for item in concepts}),
        f"{label} flattened concepts contain duplicates.",
    )
    require(schema.get("@type") == "ScholarlyArticle", f"{label} schema type changed.")
    require(
        schema.get("description") == content["author_summary"],
        f"{label} JSON-LD description must equal author_summary.",
    )
    require(schema.get("keywords") == concepts, f"{label} JSON-LD keywords changed.")
    require(
        single_meta_content(page, "description", f"{label} meta description")
        == content["summary"],
        f"{label} meta description must use the short summary.",
    )
    require(
        single_html_url(
            page,
            r'<meta property="og:description" content="([^"]*)">',
            f"{label} Open Graph description",
        )
        == content["summary"],
        f"{label} Open Graph description must use the short summary.",
    )

    related = resolve_related_papers(content, public_by_doi, config["site_url"])
    for item in related:
        require(item["url"] in page, f"{label} related canonical URL missing from HTML.")
        require(item["url"] in markdown, f"{label} related canonical URL missing from Markdown.")
        require(item["title"] in page_text, f"{label} related title missing from HTML.")
    for key, value in content["provenance"].items():
        if key.endswith("_url"):
            require(value in page and value in markdown, f"{label} provenance URL missing: {value}")


def validate_site():
    require(PROFILE_CONFIG_PATH.is_file(), "data/profile_config.json is missing.")
    profile = load_profile_config()
    require(
        bool(str(profile.get("researcher_name") or "").strip()),
        "English researcher name is missing from profile_config.json.",
    )
    require(
        bool(str(profile.get("researcher_name_zh") or "").strip()),
        "Chinese researcher name is missing from profile_config.json.",
    )
    biography = profile.get("biography")
    require(
        isinstance(biography, dict)
        and isinstance(biography.get("en"), str)
        and bool(biography["en"].strip()),
        "profile_config.json biography.en must be non-empty.",
    )
    require(
        isinstance(biography, dict)
        and isinstance(biography.get("zh"), str)
        and bool(biography["zh"].strip()),
        "profile_config.json biography.zh must be non-empty.",
    )
    require(
        isinstance(profile.get("affiliations"), list)
        and bool(profile["affiliations"])
        and isinstance(profile["affiliations"][0], dict)
        and isinstance(profile["affiliations"][0].get("name"), str)
        and bool(profile["affiliations"][0]["name"].strip()),
        "profile_config.json primary affiliation must be non-empty.",
    )
    require(
        "homepage_top_label" in profile
        and isinstance(profile["homepage_top_label"], str)
        and profile["homepage_top_label"] == profile["homepage_top_label"].strip(),
        "profile_config.json homepage_top_label must be a trimmed string.",
    )
    homepage_research = validate_homepage_research(profile)
    require(
        isinstance(profile.get("research_areas"), list)
        and bool(profile["research_areas"])
        and all(
            isinstance(value, str) and bool(value.strip())
            for value in profile["research_areas"]
        ),
        "profile_config.json research_areas must be a non-empty array of non-empty strings.",
    )
    require(
        isinstance(profile.get("description"), str)
        and bool(profile["description"].strip()),
        "profile_config.json description must be non-empty.",
    )
    require(
        isinstance(profile.get("disambiguating_description"), str)
        and bool(profile["disambiguating_description"].strip()),
        "profile_config.json disambiguating_description must be non-empty.",
    )
    require(
        bool(re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", profile.get("orcid", ""))),
        "profile_config.json ORCID must use the 0000-0000-0000-0000 format.",
    )
    require(
        profile["external_links"]["orcid"]
        == f"https://orcid.org/{profile['orcid']}",
        "profile_config.json ORCID URL does not match its ORCID value.",
    )
    require(
        all(
            isinstance(item, dict) and bool(str(item.get("name") or "").strip())
            for item in profile["affiliations"]
        ),
        "profile_config.json affiliations must contain named organizations.",
    )
    require(
        all(str(value).startswith("https://") for value in profile["external_links"].values()),
        "profile_config.json external links must use HTTPS.",
    )
    site_config_payload = json.loads(SITE_CONFIG_PATH.read_text(encoding="utf-8"))
    duplicated_profile_keys = {
        "researcher_name",
        "researcher_name_zh",
        "person_id",
        "orcid",
        "google_scholar_url",
        "researchgate_url",
        "github_url",
    }
    require(
        not duplicated_profile_keys.intersection(site_config_payload),
        "Profile identity fields must only be stored in profile_config.json.",
    )
    config = load_site_config(profile)
    require(
        config["site_url"] == CANONICAL_SITE_URL,
        f"Canonical site origin must be {CANONICAL_SITE_URL}.",
    )
    require(INDEXNOW_CONFIG_PATH.is_file(), "data/indexnow_config.json is missing.")
    indexnow_config = json.loads(INDEXNOW_CONFIG_PATH.read_text(encoding="utf-8"))
    require(
        indexnow_config.get("enabled") is True,
        "IndexNow notifications must be enabled.",
    )
    require(
        indexnow_config.get("host") == "drgezhang.com",
        "IndexNow host must be drgezhang.com.",
    )
    indexnow_key = indexnow_config.get("key")
    require(
        isinstance(indexnow_key, str)
        and bool(re.fullmatch(r"[A-Za-z0-9-]{8,128}", indexnow_key)),
        "IndexNow key must contain 8–128 letters, numbers, or dashes.",
    )
    expected_key_location = f"{CANONICAL_SITE_URL}/{indexnow_key}.txt"
    require(
        indexnow_config.get("key_location") == expected_key_location,
        "IndexNow key_location must be the canonical HTTPS root key URL.",
    )
    indexnow_key_path = ROOT / f"{indexnow_key}.txt"
    require(indexnow_key_path.is_file(), "IndexNow root key file is missing.")
    indexnow_key_content = indexnow_key_path.read_text(encoding="utf-8")
    require(
        indexnow_key_content in {indexnow_key, indexnow_key + "\n"},
        "IndexNow root key file content does not exactly match the configured key.",
    )
    require(
        config["person_id"] == f"{config['site_url']}/#person",
        "Canonical Person @id must use the site origin and #person fragment.",
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
    for item in master:
        if "authors" not in item:
            continue
        require(
            isinstance(item["authors"], list)
            and bool(item["authors"])
            and item["authors"] == normalize_authors(item["authors"]),
            f"Invalid authors list for {item.get('title')!r}.",
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
        paper_index_payload.get("researcher")
        == {
            "name": config["researcher_name"],
            "alternateName": config["researcher_name_zh"],
            "url": config["person_id"],
            "orcid": config["orcid"],
        },
        "paper_index.json researcher identity is wrong.",
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
    public_by_doi = {
        norm_doi(item.get("doi")): item
        for item in public_expected
        if norm_doi(item.get("doi"))
    }
    deep_tokens = {controller_token(entry) for entry in deep_geo}
    featured_tokens = {controller_token(entry) for entry in featured}
    citation_author_pages = 0
    schema_author_array_pages = 0
    v2_dois = []
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
        expected_title = str(item.get("title") or "Untitled work")
        expected_journal = str(item.get("journal") or "Unknown source")
        require(schema.get("name") == expected_title, f"Schema.org name changed for {slug}.html.")
        require(
            schema.get("headline") == expected_title,
            f"Schema.org headline changed for {slug}.html.",
        )
        expected_authors = normalize_authors(item.get("authors"))
        citation_authors = meta_contents(page, "citation_author")
        require(
            citation_authors == expected_authors,
            f"citation_author order/content mismatch in {slug}.html.",
        )
        author = schema.get("author")
        if expected_authors:
            citation_author_pages += 1
            schema_author_array_pages += 1
            require(isinstance(author, list), f"{slug}.html author must be an array.")
            require(
                len(author) == len(expected_authors),
                f"Schema.org author count mismatch in {slug}.html.",
            )
            for expected_name, person in zip(expected_authors, author):
                require(
                    isinstance(person, dict)
                    and person.get("@type") == "Person",
                    f"Schema.org author order/content mismatch in {slug}.html.",
                )
                if exact_name_match(expected_name, config["researcher_name"]):
                    validate_researcher_reference(
                        person, config, f"{slug}.html author {expected_name!r}"
                    )
                    require(
                        person.get("sameAs") == f"https://orcid.org/{config['orcid']}",
                        f"Researcher ORCID mismatch in {slug}.html.",
                    )
                else:
                    require(
                        person == {"@type": "Person", "name": expected_name},
                        f"Co-author inherited researcher identity in {slug}.html.",
                    )
        else:
            require(
                not citation_authors,
                f"Unexpected citation_author in {slug}.html without master authors.",
            )
            validate_researcher_reference(author, config, f"{slug}.html author")
            require(
                author.get("sameAs") == f"https://orcid.org/{config['orcid']}",
                f"Author sameAs must be the canonical ORCID URL in {slug}.html.",
            )
        require(
            single_meta_content(page, "citation_title", f"{slug}.html citation_title")
            == expected_title,
            f"citation_title changed for {slug}.html.",
        )
        require(
            single_meta_content(
                page, "citation_journal_title", f"{slug}.html citation_journal_title"
            )
            == expected_journal,
            f"citation_journal_title changed for {slug}.html.",
        )
        if item.get("journal"):
            require(
                schema.get("isPartOf", {}).get("name") == item["journal"],
                f"Schema.org journal changed for {slug}.html.",
            )
        if item.get("year"):
            expected_year = str(item["year"])
            require(
                single_meta_content(
                    page,
                    "citation_publication_date",
                    f"{slug}.html citation_publication_date",
                )
                == expected_year,
                f"citation_publication_date changed for {slug}.html.",
            )
            require(
                schema.get("datePublished") == expected_year,
                f"Schema.org publication year changed for {slug}.html.",
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
        for identity_line in (
            f"Researcher: {config['researcher_name']}",
            f"Chinese name: {config['researcher_name_zh']}",
            f"ORCID identity anchor: https://orcid.org/{config['orcid']}",
            f"Canonical researcher: {config['person_id']}",
        ):
            require(identity_line in markdown, f"Identity line missing from {slug}.md.")
        require(
            expected_markdown_url in page,
            f"Markdown alternate missing from {slug}.html.",
        )
        require(LEGACY_SITE_URL not in page, f"Legacy origin remains in {slug}.html.")
        require(LEGACY_SITE_URL not in markdown, f"Legacy origin remains in {slug}.md.")
        doi = norm_doi(item.get("doi"))
        if doi:
            require(f"https://doi.org/{doi}" in page, f"DOI link missing from {slug}.html.")
            require(
                single_meta_content(page, "citation_doi", f"{slug}.html citation_doi") == doi,
                f"citation_doi changed for {slug}.html.",
            )
            require(
                schema.get("identifier", {}).get("value") == doi,
                f"Schema.org DOI changed for {slug}.html.",
            )
        else:
            require(
                not re.search(r'<meta name="citation_doi"\s', page),
                f"Unexpected citation_doi in {slug}.html.",
            )
        token = publication_token(item)
        if token in deep_tokens:
            content_path = deep_content_path(item)
            require(content_path.is_file(), f"Deep GEO content missing for {slug}.")
            content = json.loads(content_path.read_text(encoding="utf-8"))
            if content.get("version") == 2:
                v2_dois.append(norm_doi(content.get("doi")))
                validate_aihflevel_v2(
                    content,
                    item,
                    page,
                    markdown,
                    schema,
                    public_by_doi,
                    config,
                )
            else:
                require(
                    content.get("version") == 1,
                    f"Unsupported Deep GEO content version for {slug}.",
                )
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
                        require(
                            str(value) in markdown,
                            f"Deep GEO content lost from {slug}.md.",
                        )
        require(
            ('<span class="badge">Deep GEO</span>' in page) == (token in deep_tokens),
            f"Deep GEO badge/state mismatch for {slug}.html.",
        )
    require(
        len(canonical_urls) == len(set(canonical_urls)),
        "Paper canonical URLs are not unique.",
    )
    require(
        v2_dois == [AIHFLEVEL_DOI],
        "AIHFLevel must be the only Paper GEO 2.0 pilot; all other Deep GEO pages must remain V1.",
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
    homepage_top_label = profile["homepage_top_label"]
    expected_homepage_top = (
        f"{homepage_top_label} · {profile['affiliations'][0]['name']}"
        if homepage_top_label
        else profile["affiliations"][0]["name"]
    )
    require(
        single_html_url(
            index_html,
            r'<main class="wrap"><section class="hero"><div>'
            r'<div class="eyebrow">([^<]*)</div>',
            "Homepage top label",
        )
        == expected_homepage_top,
        "Homepage top label does not match profile_config.json.",
    )
    require(
        f'<span class="name-zh" lang="zh-CN">{config["researcher_name_zh"]}</span>'
        in index_html,
        "Homepage must contain a visible zh-CN researcher name span.",
    )
    expected_homepage_title = (
        f"{config['researcher_name']} ({config['researcher_name_zh']}) — "
        "Cardiovascular AI, Multi-omics & Circadian Biology"
    )
    require(
        element_texts(index_html, "title") == [expected_homepage_title],
        "Homepage title does not use the canonical bilingual identity.",
    )
    require(
        element_texts(
            index_html,
            "p",
            {"class": "identity-zh", "lang": "zh-CN"},
        )
        == [profile["biography"]["zh"]],
        "Homepage Chinese identity description is missing or changed.",
    )
    require(
        profile["biography"]["en"]
        in element_texts(index_html, "p", {"class": "lead"}),
        "Homepage English biography does not match profile_config.json.",
    )
    require(
        config["researcher_name_zh"] in visible_text(index_html),
        "Chinese researcher identity is not visible on the homepage.",
    )
    require(
        f"{config['researcher_name']} ({config['researcher_name_zh']})"
        in single_meta_content(index_html, "description", "Homepage meta description"),
        "Bilingual researcher identity missing from homepage meta description.",
    )
    homepage_schema = json_ld_object(index_html, "ProfilePage", "Homepage")
    require(homepage_schema.get("url") == homepage_url, "Wrong homepage Schema.org URL.")
    require(
        homepage_schema.get("@id") == f"{config['site_url']}/#profile",
        "Wrong homepage ProfilePage @id.",
    )
    homepage_person = homepage_schema.get("mainEntity")
    validate_researcher_reference(homepage_person, config, "Homepage ProfilePage mainEntity")
    require(
        homepage_person.get("identifier") == f"https://orcid.org/{config['orcid']}",
        "Homepage Person ORCID identifier is wrong.",
    )
    require(
        homepage_person.get("givenName") == profile["given_name"]
        and homepage_person.get("familyName") == profile["family_name"],
        "Homepage Person name components do not match profile_config.json.",
    )
    schema_organizations = [
        {"@type": "Organization", "name": item["name"]}
        for item in profile["affiliations"]
    ]
    expected_affiliation = (
        schema_organizations[0] if len(schema_organizations) == 1 else schema_organizations
    )
    require(
        homepage_person.get("affiliation") == expected_affiliation,
        "Homepage Person affiliation does not match profile_config.json.",
    )
    require(
        homepage_person.get("description") == profile["description"],
        "Homepage Person description does not match profile_config.json.",
    )
    require(
        homepage_person.get("disambiguatingDescription")
        == profile["disambiguating_description"],
        "Homepage Person disambiguatingDescription does not match profile_config.json.",
    )
    require(
        homepage_person.get("knowsAbout") == profile["research_areas"],
        "Homepage Person research areas do not match profile_config.json.",
    )
    expected_profiles = {
        profile["external_links"]["orcid"],
        profile["external_links"]["google_scholar"],
        profile["external_links"]["researchgate"],
        profile["external_links"]["github"],
    }
    require(
        set(same_as_values(homepage_person.get("sameAs"))) == expected_profiles,
        "Homepage Person sameAs profiles do not match verified site configuration.",
    )
    for label, url in (
        ("Google Scholar", profile["external_links"]["google_scholar"]),
        ("ResearchGate", profile["external_links"]["researchgate"]),
        ("ORCID", profile["external_links"]["orcid"]),
        ("GitHub", profile["external_links"]["github"]),
    ):
        require(
            f'href="{url}">{label}</a>' in index_html,
            f"Homepage {label} link does not match profile_config.json.",
        )

    research_sections = re.findall(
        r'<section id="research">(.*?)</section>', index_html, flags=re.DOTALL
    )
    require(
        len(research_sections) == 1,
        "Homepage must contain exactly one generated research section.",
    )
    research_html = research_sections[0]
    enabled_themes = [
        theme for theme in homepage_research["themes"] if theme["enabled"]
    ]
    require(
        element_texts(research_html, "div", {"class": "eyebrow"})
        == [homepage_research["label"]],
        "Homepage research label does not match profile_config.json.",
    )
    require(
        element_texts(research_html, "h2") == [homepage_research["heading"]],
        "Homepage research heading does not match profile_config.json.",
    )
    require(
        element_texts(research_html, "h3")
        == [theme["title"] for theme in enabled_themes],
        "Homepage research theme titles or order differ from profile_config.json.",
    )
    require(
        element_texts(research_html, "p")
        == [theme["description"] for theme in enabled_themes],
        "Homepage research theme descriptions differ from profile_config.json.",
    )
    require(
        research_html.count('<div class="card">') == len(enabled_themes),
        "Homepage research card count differs from profile_config.json.",
    )

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
    publications_person = publications_schema.get("mainEntity")
    validate_researcher_reference(
        publications_person,
        config,
        "Publications ProfilePage mainEntity",
    )
    require(
        publications_person.get("sameAs") == f"https://orcid.org/{config['orcid']}",
        "Publications Person sameAs must be the canonical ORCID URL.",
    )
    require(
        f"{config['researcher_name']} ({config['researcher_name_zh']})"
        in visible_text(publications_html),
        "Bilingual researcher identity is not visible on publications.html.",
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
    sitemap_namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    sitemap_entries = []
    for entry in tree.getroot().findall(f"{sitemap_namespace}url"):
        loc_nodes = entry.findall(f"{sitemap_namespace}loc")
        lastmod_nodes = entry.findall(f"{sitemap_namespace}lastmod")
        require(len(loc_nodes) == 1, "Each sitemap entry must have exactly one loc.")
        require(len(lastmod_nodes) == 1, "Each sitemap entry must have exactly one lastmod.")
        url = str(loc_nodes[0].text or "").strip()
        lastmod = str(lastmod_nodes[0].text or "").strip()
        require(bool(url), "Sitemap loc must not be empty.")
        require(
            bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod)),
            f"Invalid sitemap lastmod format for {url}: {lastmod!r}",
        )
        try:
            parsed_lastmod = date.fromisoformat(lastmod)
        except ValueError as exc:
            raise ValidationError(f"Invalid sitemap lastmod date for {url}: {lastmod}") from exc
        require(parsed_lastmod.isoformat() == lastmod, f"Invalid sitemap lastmod for {url}.")
        require(
            parsed_lastmod <= datetime.now(timezone.utc).date(),
            f"Future sitemap lastmod for {url}: {lastmod}",
        )
        sitemap_entries.append((url, lastmod))
    sitemap_urls = [url for url, _ in sitemap_entries]
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
    identity_lines = (
        f"- Researcher: {config['researcher_name']}",
        f"- Chinese name: {config['researcher_name_zh']}",
        f"- Canonical person: {config['person_id']}",
        f"- ORCID: https://orcid.org/{config['orcid']}",
    )
    for identity_line in identity_lines:
        require(identity_line in llms, f"Identity missing from llms.txt: {identity_line}")
        require(
            identity_line in llms_full,
            f"Identity missing from llms-full.txt: {identity_line}",
        )
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
        "citation_author_pages": citation_author_pages,
        "schema_author_array_pages": schema_author_array_pages,
        "paper_geo_v2_pages": len(v2_dois),
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
