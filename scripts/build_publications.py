import copy
import csv
import html
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone

from citation_common import (
    CITATIONS_DIR,
    citation_files,
    citation_record,
    load_citation_metadata,
    render_bibtex,
    render_cite_html,
    render_csl_json,
    render_ris,
)
from official_abstracts import abstract_text, load_official_abstracts
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
    load_profile_config,
    load_site_config,
    publication_token,
    validate_controller_entries,
)
from sync_common import (
    ROOT,
    exact_name_match,
    is_withdrawn,
    load_master,
    norm_doi,
    publication_authors,
    save_master,
)


FEATURED_START = "<!-- FEATURED_PAPERS_START -->"
FEATURED_END = "<!-- FEATURED_PAPERS_END -->"
HOME_ORIGIN_START = "<!-- HOME_ORIGIN_START -->"
HOME_ORIGIN_END = "<!-- HOME_ORIGIN_END -->"
HOME_IDENTITY_START = "<!-- HOME_IDENTITY_START -->"
HOME_IDENTITY_END = "<!-- HOME_IDENTITY_END -->"
GENERATED_MARKER = "<!-- GEO_PHASE2_GENERATED -->"
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
SITEMAP_BASELINE_DATE = "2026-09-20"
GA4_MEASUREMENT_ID = "G-65LDZXWWQK"
GA4_TAG = (
    "<!-- Google tag (gtag.js) -->\n"
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"></script>\n'
    "<script>\n"
    "  window.dataLayer = window.dataLayer || [];\n"
    "  function gtag(){dataLayer.push(arguments);}\n"
    "  gtag('js', new Date());\n"
    f"  gtag('config', '{GA4_MEASUREMENT_ID}');\n"
    "</script>\n"
)
GA4_INSERTION = "\n" + GA4_TAG
PENDING_NOTICE = (
    "Selected for Deep GEO evidence expansion. The evidence-oriented content "
    "layer is pending scientific review. The publisher version remains the "
    "version of record."
)
SELECTED_EVIDENCE_NOTICE = (
    "These are selected evidence sources used to verify claims on this "
    "author-controlled evidence page; they are not the complete reference list "
    "of the published review."
)


def scholar_url(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote(f'"{title}"')


def doi_url(doi):
    return f"https://doi.org/{norm_doi(doi)}" if norm_doi(doi) else ""


def absolute(site_root, relative):
    return f"{site_root}/{str(relative).lstrip('/')}"


def orcid_url(config):
    return config["profile"]["external_links"]["orcid"]


def schema_affiliations(config):
    affiliations = [
        {"@type": "Organization", "name": item["name"]}
        for item in config["profile"]["affiliations"]
    ]
    return affiliations[0] if len(affiliations) == 1 else affiliations


def researcher_reference(config):
    return {
        "@type": "Person",
        "@id": config["person_id"],
        "name": config["researcher_name"],
        "alternateName": [config["researcher_name_zh"]],
        "url": f"{config['site_url']}/",
        "sameAs": orcid_url(config),
    }


def homepage_profile_schema(config):
    researcher = researcher_reference(config)
    researcher.update(
        {
            "givenName": config["profile"]["given_name"],
            "familyName": config["profile"]["family_name"],
            "identifier": orcid_url(config),
            "sameAs": [
                orcid_url(config),
                config["google_scholar_url"],
                config["researchgate_url"],
                config["github_url"],
            ],
            "affiliation": schema_affiliations(config),
            "description": config["profile"]["description"],
            "disambiguatingDescription": config["profile"][
                "disambiguating_description"
            ],
            "knowsAbout": config["profile"]["research_areas"],
        }
    )
    return {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "@id": f"{config['site_url']}/#profile",
        "url": f"{config['site_url']}/",
        "name": (
            f"{config['researcher_name']} ({config['researcher_name_zh']}) "
            "— Academic Profile"
        ),
        "mainEntity": researcher,
    }


def homepage_website_schema(config):
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{config['site_url']}/#website",
        "url": f"{config['site_url']}/",
        "name": f"{config['researcher_name']} Academic Hub",
        "creator": {"@id": config["person_id"]},
    }


def write_text_if_changed(path, content):
    previous = path.read_text(encoding="utf-8") if path.is_file() else None
    changed = previous != content
    if changed:
        path.write_text(content, encoding="utf-8")
    return changed


def with_ga4_tag(page):
    if GA4_INSERTION in page:
        if page.count(GA4_INSERTION) != 1:
            raise ValueError("Google tag must occur exactly once in the HTML head.")
        return page
    if page.count("<head>") != 1:
        raise ValueError("Google tag requires exactly one HTML head.")
    return page.replace("<head>", "<head>" + GA4_INSERTION, 1)


def write_public_html_if_changed(path, content):
    previous = path.read_text(encoding="utf-8") if path.is_file() else None
    content_changed = previous is None or (
        previous.replace(GA4_INSERTION, "") != content.replace(GA4_INSERTION, "")
    )
    write_text_if_changed(path, content)
    return content_changed


def load_sitemap_lastmods(path):
    if not path.is_file():
        return {}
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Cannot preserve sitemap lastmod values: {exc}") from exc
    result = {}
    prefix = f"{{{SITEMAP_NAMESPACE}}}"
    for entry in root.findall(f"{prefix}url"):
        loc_node = entry.find(f"{prefix}loc")
        if loc_node is None or not str(loc_node.text or "").strip():
            raise ValueError("Cannot preserve sitemap lastmod values: sitemap entry lacks loc.")
        url = str(loc_node.text).strip()
        if url in result:
            raise ValueError(f"Cannot preserve sitemap lastmod values: duplicate URL {url}")
        lastmod_node = entry.find(f"{prefix}lastmod")
        lastmod = str(lastmod_node.text or "").strip() if lastmod_node is not None else ""
        if lastmod:
            try:
                parsed = date.fromisoformat(lastmod)
            except ValueError as exc:
                raise ValueError(f"Invalid existing sitemap lastmod for {url}: {lastmod}") from exc
            if parsed.isoformat() != lastmod or parsed > datetime.now(timezone.utc).date():
                raise ValueError(f"Invalid existing sitemap lastmod for {url}: {lastmod}")
        result[url] = lastmod
    return result


def resolve_lastmod(url, changed, previous_lastmods, today):
    if changed or url not in previous_lastmods:
        return today
    return previous_lastmods[url] or SITEMAP_BASELINE_DATE


def render_homepage_research(profile):
    section = profile["homepage_research"]
    cards = "".join(
        "\n<div class=\"card\"><h3>"
        + html.escape(theme["title"])
        + "</h3><p>"
        + html.escape(theme["description"])
        + "</p></div>"
        for theme in section["themes"]
        if theme["enabled"]
    )
    return (
        '<section id="research"><div class="eyebrow">'
        + html.escape(section["label"])
        + "</div><h2>"
        + html.escape(section["heading"])
        + '</h2><div class="grid themes">'
        + cards
        + "</div></section>"
    )


def update_homepage(index_html, config):
    homepage_url = f"{config['site_url']}/"
    bilingual_name = f"{config['researcher_name']} ({config['researcher_name_zh']})"
    page_title = (
        f"{bilingual_name} — Cardiovascular AI, Multi-omics & Circadian Biology"
    )
    meta_description = (
        f"Academic profile of {bilingual_name}, a cardiovascular and computational biology "
        "researcher working in artificial intelligence, multi-omics, atherosclerosis, heart "
        f"failure and circadian biology. ORCID {config['orcid']}."
    )
    index_html, title_count = re.subn(
        r"<title>.*?</title>",
        f"<title>{html.escape(page_title)}</title>",
        index_html,
        count=1,
        flags=re.DOTALL,
    )
    if title_count != 1:
        raise ValueError("index.html must contain exactly one title element.")
    index_html, description_count = re.subn(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{html.escape(meta_description, quote=True)}">',
        index_html,
        count=1,
    )
    if description_count != 1:
        raise ValueError("index.html must contain exactly one meta description.")

    origin_block = (
        f'{HOME_ORIGIN_START}\n'
        f'<link rel="canonical" href="{html.escape(homepage_url, quote=True)}">\n'
        f'<meta property="og:title" content="{html.escape(page_title, quote=True)}">\n'
        f'<meta property="og:description" content="{html.escape(meta_description, quote=True)}">\n'
        f'<meta property="og:type" content="website">\n'
        f'<meta property="og:url" content="{html.escape(homepage_url, quote=True)}">\n'
        f'{HOME_ORIGIN_END}'
    )
    if index_html.count(HOME_ORIGIN_START) == index_html.count(HOME_ORIGIN_END) == 1:
        before, remainder = index_html.split(HOME_ORIGIN_START, 1)
        _, after = remainder.split(HOME_ORIGIN_END, 1)
        index_html = before + origin_block + after
    elif HOME_ORIGIN_START not in index_html and HOME_ORIGIN_END not in index_html:
        stylesheet = '<link rel="stylesheet" href="assets/style.css">'
        if index_html.count(stylesheet) != 1:
            raise ValueError("index.html must contain exactly one homepage stylesheet link.")
        index_html = index_html.replace(stylesheet, origin_block + "\n" + stylesheet, 1)
    else:
        raise ValueError("index.html homepage origin markers are incomplete or duplicated.")

    schema_pattern = re.compile(
        r'(<script type="application/ld\+json">)(.*?)(</script>)', re.DOTALL
    )
    profile_schema_count = 0

    def update_schema(match):
        nonlocal profile_schema_count
        payload = json.loads(match.group(2))
        if payload.get("@type") not in {"Person", "ProfilePage"}:
            return match.group(0)
        profile_schema_count += 1
        serialized = json.dumps(
            homepage_profile_schema(config), ensure_ascii=False
        ).replace("</", "<\\/")
        return match.group(1) + serialized + match.group(3)

    index_html = schema_pattern.sub(update_schema, index_html)
    if profile_schema_count != 1:
        raise ValueError("index.html must contain exactly one identity ProfilePage JSON-LD object.")

    website_schema = json.dumps(
        homepage_website_schema(config), ensure_ascii=False
    ).replace("</", "<\\/")
    website_script = f'<script type="application/ld+json">{website_schema}</script>'
    website_matches = [
        match
        for match in schema_pattern.finditer(index_html)
        if json.loads(match.group(2)).get("@type") == "WebSite"
    ]
    if len(website_matches) == 1:
        match = website_matches[0]
        index_html = index_html[:match.start()] + website_script + index_html[match.end():]
    elif not website_matches:
        profile_matches = [
            match
            for match in schema_pattern.finditer(index_html)
            if json.loads(match.group(2)).get("@type") == "ProfilePage"
        ]
        if len(profile_matches) != 1:
            raise ValueError("index.html must contain exactly one ProfilePage JSON-LD object.")
        insertion_point = profile_matches[0].end()
        index_html = (
            index_html[:insertion_point]
            + website_script
            + index_html[insertion_point:]
        )
    else:
        raise ValueError("index.html must contain at most one WebSite JSON-LD object.")

    identity_block = (
        f"{HOME_IDENTITY_START}\n"
        f"<h1>{html.escape(config['researcher_name'])} "
        f'<span class="name-zh" lang="zh-CN">'
        f"{html.escape(config['researcher_name_zh'])}</span></h1>\n"
        f'<p class="identity-zh" lang="zh-CN">'
        f"{html.escape(config['profile']['biography']['zh'])}</p>\n{HOME_IDENTITY_END}"
    )
    if index_html.count(HOME_IDENTITY_START) == index_html.count(HOME_IDENTITY_END) == 1:
        before, remainder = index_html.split(HOME_IDENTITY_START, 1)
        _, after = remainder.split(HOME_IDENTITY_END, 1)
        index_html = before + identity_block + after
    elif HOME_IDENTITY_START not in index_html and HOME_IDENTITY_END not in index_html:
        index_html, heading_count = re.subn(
            r"<h1>.*?</h1>", identity_block, index_html, count=1, flags=re.DOTALL
        )
        if heading_count != 1:
            raise ValueError("index.html must contain exactly one homepage h1.")
    else:
        raise ValueError("index.html homepage identity markers are incomplete or duplicated.")

    index_html, biography_count = re.subn(
        r'<p class="lead">.*?</p>',
        f'<p class="lead">{html.escape(config["profile"]["biography"]["en"])}</p>',
        index_html,
        count=1,
        flags=re.DOTALL,
    )
    if biography_count != 1:
        raise ValueError("index.html must contain exactly one primary English biography.")

    links = config["profile"]["external_links"]
    profile_links = (
        '<div class="buttons" id="profiles">'
        f'<a class="btn primary" href="{links["google_scholar"]}">Google Scholar</a>'
        f'<a class="btn" href="{links["researchgate"]}">ResearchGate</a>'
        f'<a class="btn" href="{links["orcid"]}">ORCID</a>'
        f'<a class="btn" href="{links["github"]}">GitHub</a></div>'
    )
    index_html, links_count = re.subn(
        r'<div class="buttons" id="profiles">.*?</div>',
        profile_links,
        index_html,
        count=1,
        flags=re.DOTALL,
    )
    if links_count != 1:
        raise ValueError("index.html must contain exactly one profile links block.")

    primary_affiliation = config["profile"]["affiliations"][0]["name"]
    homepage_top_label = config["profile"]["homepage_top_label"].strip()
    homepage_top_text = (
        f"{homepage_top_label} · {primary_affiliation}"
        if homepage_top_label
        else primary_affiliation
    )
    index_html, affiliation_count = re.subn(
        r'(<main class="wrap"><section class="hero"><div><div class="eyebrow">)'
        r'.*?(</div>)',
        lambda match: (
            match.group(1) + html.escape(homepage_top_text) + match.group(2)
        ),
        index_html,
        count=1,
        flags=re.DOTALL,
    )
    if affiliation_count != 1:
        raise ValueError("index.html must contain exactly one homepage affiliation label.")

    index_html, research_count = re.subn(
        r'<section id="research">.*?</section>',
        lambda _: render_homepage_research(config["profile"]),
        index_html,
        count=1,
        flags=re.DOTALL,
    )
    if research_count != 1:
        raise ValueError("index.html must contain exactly one homepage research section.")

    replacements = (
        (
            r'<a class="brand" href="index\.html">.*?</a>',
            f'<a class="brand" href="index.html">{html.escape(config["researcher_name"])}</a>',
            "homepage brand",
        ),
        (
            r'<footer><div class="wrap">© .*? · Academic website · Updated 2026-09</div></footer>',
            '<footer><div class="wrap">© '
            f'{html.escape(config["researcher_name"])} · Academic website · Updated 2026-09'
            '</div></footer>',
            "homepage footer identity",
        ),
    )
    for pattern, replacement, label in replacements:
        index_html, replacement_count = re.subn(
            pattern, replacement, index_html, count=1, flags=re.DOTALL
        )
        if replacement_count != 1:
            raise ValueError(f"index.html must contain exactly one {label}.")
    return with_ga4_tag(index_html)


def schema_type(publication):
    publication_type = str(publication.get("type") or "").casefold()
    if publication_type in {"article", "review", "journal article"}:
        return "ScholarlyArticle"
    return "CreativeWork"


def load_deep_content(publication, *, allow_missing=False):
    path = deep_content_path(publication)
    if not path.is_file():
        if allow_missing:
            return None
        raise ValueError(
            f"Deep GEO is enabled for {publication.get('title')!r}, but {path.relative_to(ROOT)} is missing."
        )
    content = json.loads(path.read_text(encoding="utf-8"))
    version = content.get("version")
    if version not in {1, 2}:
        raise ValueError(f"{path.relative_to(ROOT)} must use version 1 or 2.")
    configured_doi = norm_doi(content.get("doi"))
    publication_doi = norm_doi(publication.get("doi"))
    if configured_doi and configured_doi != publication_doi:
        raise ValueError(
            f"Deep GEO content DOI mismatch in {path.relative_to(ROOT)}: "
            f"{configured_doi} != {publication_doi}"
        )
    if version == 1:
        for list_key in ("keywords", "questions"):
            if content.get(list_key) is not None and not isinstance(content[list_key], list):
                raise ValueError(
                    f"{path.relative_to(ROOT)} field {list_key!r} must be an array."
                )
    else:
        validate_deep_v2_content(content, path.relative_to(ROOT))
    return content


def required_text(value, label):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be non-empty trimmed text.")
    return value


def required_text_list(value, label, *, minimum=1):
    if not isinstance(value, list) or len(value) < minimum:
        raise ValueError(f"{label} must be an array with at least {minimum} item(s).")
    result = [required_text(item, f"{label} item") for item in value]
    if len({item.casefold() for item in result}) != len(result):
        raise ValueError(f"{label} must not contain duplicate items.")
    return result


def flatten_concepts(content):
    concepts = content.get("concepts") or {}
    flattened = []
    seen = set()
    for values in concepts.values():
        for value in values:
            text = str(value).strip()
            key = text.casefold()
            if text and key not in seen:
                seen.add(key)
                flattened.append(text)
    return flattened


def validate_deep_v2_content(content, label="Paper GEO 2.0 content"):
    for key in (
        "doi",
        "display_title",
        "summary",
        "research_question",
        "author_summary",
        "evidence_page_notice",
    ):
        required_text(content.get(key), f"{label} {key}")

    study = content.get("study_profile")
    if not isinstance(study, dict):
        raise ValueError(f"{label} study_profile must be an object.")
    profile_type = required_text(
        study.get("profile_type"), f"{label} study_profile.profile_type"
    )
    if profile_type not in {"clinical_cohort", "multicohort_omics", "narrative_review"}:
        raise ValueError(
            f"{label} study_profile.profile_type must be clinical_cohort, "
            "multicohort_omics, or narrative_review."
        )
    detail_keys = ["study_design", "evidence_type"]
    if profile_type == "narrative_review":
        detail_keys.append("translation_scope")
        for key in ("evidence_domains", "diseases_covered"):
            required_text_list(study.get(key), f"{label} study_profile.{key}")
        if any(key in study for key in (
            "population", "primary_endpoint", "secondary_endpoint",
            "unique_total_n", "cohorts", "data_modalities", "external_validation",
        )) or "model_profile" in content:
            raise ValueError(f"{label} narrative_review must not invent cohort or model fields.")
    else:
        detail_keys.extend(("population", "primary_endpoint", "secondary_endpoint"))
        required_text_list(
            study.get("data_modalities"), f"{label} study_profile.data_modalities"
        )
        if not isinstance(study.get("external_validation"), bool):
            raise ValueError(f"{label} study_profile.external_validation must be boolean.")
    for key in detail_keys:
        required_text(study.get(key), f"{label} study_profile.{key}")
    if profile_type == "clinical_cohort":
        unique_total = study.get("unique_total_n")
        if type(unique_total) is not int or unique_total <= 0:
            raise ValueError(f"{label} study_profile.unique_total_n must be positive.")
        cohorts = study.get("cohorts")
        if not isinstance(cohorts, list) or not cohorts:
            raise ValueError(f"{label} study_profile.cohorts must be a non-empty array.")
        cohort_by_name = {}
        for position, cohort in enumerate(cohorts, start=1):
            if not isinstance(cohort, dict):
                raise ValueError(f"{label} cohort {position} must be an object.")
            name = required_text(cohort.get("name"), f"{label} cohort {position} name")
            required_text(cohort.get("role"), f"{label} cohort {name} role")
            if type(cohort.get("n")) is not int or cohort["n"] <= 0:
                raise ValueError(f"{label} cohort {name} n must be positive.")
            if name.casefold() in cohort_by_name:
                raise ValueError(f"{label} cohort names must be unique.")
            cohort_by_name[name.casefold()] = cohort
        for cohort in cohorts:
            parent_name = cohort.get("subset_of")
            if parent_name is not None:
                parent_name = required_text(
                    parent_name, f"{label} cohort {cohort['name']} subset_of"
                )
                parent = cohort_by_name.get(parent_name.casefold())
                if not parent or parent is cohort or cohort["n"] > parent["n"]:
                    raise ValueError(f"{label} has an invalid cohort subset hierarchy.")
                if cohort["name"] not in (parent.get("contains") or []):
                    raise ValueError(f"{label} cohort contains/subset_of mismatch.")
            contains = cohort.get("contains")
            if contains is not None:
                children = required_text_list(
                    contains, f"{label} cohort {cohort['name']} contains"
                )
                resolved = [cohort_by_name.get(name.casefold()) for name in children]
                if any(child is None for child in resolved):
                    raise ValueError(f"{label} cohort contains an unknown child.")
                if any(child.get("subset_of") != cohort["name"] for child in resolved):
                    raise ValueError(f"{label} cohort contains/subset_of mismatch.")
                if sum(child["n"] for child in resolved) != cohort["n"]:
                    raise ValueError(f"{label} cohort child counts do not equal parent n.")
        root_total = sum(
            cohort["n"] for cohort in cohorts if not cohort.get("subset_of")
        )
        if root_total != unique_total:
            raise ValueError(
                f"{label} independent cohort counts do not equal unique_total_n."
            )
    else:
        scale_metrics = study.get("scale_metrics")
        if not isinstance(scale_metrics, list) or not scale_metrics:
            raise ValueError(
                f"{label} study_profile.scale_metrics must be a non-empty array."
            )
        metric_pairs = []
        for position, metric in enumerate(scale_metrics, start=1):
            if not isinstance(metric, dict) or set(metric) != {"label", "value"}:
                raise ValueError(
                    f"{label} study_profile scale metric {position} must contain only "
                    "label and value."
                )
            metric_pairs.append(
                (
                    required_text(
                        metric.get("label"),
                        f"{label} study_profile scale metric {position} label",
                    ),
                    required_text(
                        metric.get("value"),
                        f"{label} study_profile scale metric {position} value",
                    ),
                )
            )
        if len(metric_pairs) != len(set(metric_pairs)):
            raise ValueError(
                f"{label} study_profile.scale_metrics must not contain duplicate items."
            )
        required_text(
            study.get("counting_note"), f"{label} study_profile.counting_note"
        )

    model = content.get("model_profile")
    if model is not None and not isinstance(model, dict):
        raise ValueError(f"{label} model_profile must be an object when present.")

    findings = content.get("key_findings")
    if not isinstance(findings, list) or not findings:
        raise ValueError(f"{label} key_findings must be a non-empty array.")
    finding_ids = []
    required_finding_keys = {"id", "claim", "context", "evidence", "source_locator"}
    for position, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict) or set(finding) != required_finding_keys:
            raise ValueError(
                f"{label} key finding {position} must use only the normalized V2 fields."
            )
        finding_id = required_text(finding.get("id"), f"{label} key finding id")
        if not re.fullmatch(r"KF[1-9][0-9]*", finding_id):
            raise ValueError(f"{label} key finding IDs must use KF<number>.")
        finding_ids.append(finding_id)
        for key in ("claim", "context", "source_locator"):
            required_text(finding.get(key), f"{label} {finding_id} {key}")
        evidence = finding.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"{label} {finding_id} evidence must be non-empty.")
        pairs = []
        for item in evidence:
            if not isinstance(item, dict) or set(item) != {"label", "value"}:
                raise ValueError(f"{label} {finding_id} evidence is not normalized.")
            pair = (
                required_text(item.get("label"), f"{label} {finding_id} evidence label"),
                required_text(item.get("value"), f"{label} {finding_id} evidence value"),
            )
            pairs.append(pair)
        if len(pairs) != len(set(pairs)):
            raise ValueError(f"{label} {finding_id} contains duplicate evidence.")
    if len(finding_ids) != len(set(finding_ids)):
        raise ValueError(f"{label} key finding IDs must be unique.")

    required_text_list(content.get("what_this_adds"), f"{label} what_this_adds")
    scope = content.get("evidence_scope")
    if not isinstance(scope, dict):
        raise ValueError(f"{label} evidence_scope must be an object.")
    for key in ("supports", "does_not_establish"):
        required_text_list(scope.get(key), f"{label} evidence_scope.{key}")

    qa = content.get("qa")
    max_qa = (
        12 if profile_type == "narrative_review"
        else 10 if profile_type == "multicohort_omics"
        else 8
    )
    if not isinstance(qa, list) or not 4 <= len(qa) <= max_qa:
        raise ValueError(f"{label} qa must contain 4–{max_qa} objects.")
    seen_questions = set()
    finding_id_set = set(finding_ids)
    for position, item in enumerate(qa, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{label} Q&A {position} must be an object.")
        question = required_text(item.get("question"), f"{label} Q&A {position} question")
        required_text(item.get("answer"), f"{label} Q&A {position} answer")
        if question.casefold() in seen_questions:
            raise ValueError(f"{label} Q&A questions must be unique.")
        seen_questions.add(question.casefold())
        refs = item.get("evidence_refs", [])
        if not isinstance(refs, list) or any(ref not in finding_id_set for ref in refs):
            raise ValueError(f"{label} Q&A evidence_refs must reference real finding IDs.")
        if len(refs) != len(set(refs)):
            raise ValueError(f"{label} Q&A evidence_refs must be unique.")

    concepts = content.get("concepts")
    if not isinstance(concepts, dict) or not concepts:
        raise ValueError(f"{label} concepts must be a non-empty categorized object.")
    for category, values in concepts.items():
        required_text(category, f"{label} concept category")
        required_text_list(values, f"{label} concepts.{category}")
    if not flatten_concepts(content):
        raise ValueError(f"{label} concepts must contain scientific terms.")
    required_text_list(content.get("limitations"), f"{label} limitations")

    related = content.get("related_papers")
    if not isinstance(related, list) or not related:
        raise ValueError(f"{label} related_papers must be a non-empty array.")
    related_dois = []
    for position, item in enumerate(related, start=1):
        if not isinstance(item, dict) or set(item) != {"doi", "relationship"}:
            raise ValueError(f"{label} related paper {position} is invalid.")
        doi = norm_doi(item.get("doi"))
        if not doi:
            raise ValueError(f"{label} related paper {position} DOI is invalid.")
        required_text(item.get("relationship"), f"{label} related paper relationship")
        related_dois.append(doi)
    if len(related_dois) != len(set(related_dois)):
        raise ValueError(f"{label} related paper DOIs must be unique.")

    provenance = content.get("provenance")
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError(f"{label} provenance must be a non-empty object.")
    for key, value in provenance.items():
        value = required_text(value, f"{label} provenance.{key}")
        if key.endswith("_url"):
            parsed = urllib.parse.urlparse(value)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"{label} provenance.{key} must be an HTTPS URL.")
    if "citation_pilot" in content:
        validate_citation_pilot(content["citation_pilot"], set(finding_ids), label)
    if "citation_layer" in content:
        validate_citation_layer(content["citation_layer"], content["key_findings"], label)


def validate_citation_layer(layer, findings, label):
    prefix = f"{label} citation_layer"
    if not isinstance(layer, dict) or set(layer) != {
        "citation_use_cases", "not_appropriate_as_evidence_for", "evidence_matrix"
    }:
        raise ValueError(f"{prefix} fields are invalid.")
    finding_by_id = {finding["id"]: finding for finding in findings}
    required_text_list(layer["not_appropriate_as_evidence_for"], f"{prefix} boundaries")
    for collection, fields in (
        ("citation_use_cases", {"id", "query", "supported_scope", "evidence_refs"}),
        ("evidence_matrix", {"id", "component", "context", "finding", "evidence_level", "scope", "source_locator", "evidence_refs"}),
    ):
        rows = layer[collection]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{prefix}.{collection} must be a non-empty array.")
        ids = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != fields:
                raise ValueError(f"{prefix}.{collection} row fields are invalid.")
            row_id = required_text(row["id"], f"{prefix} row ID")
            if not re.fullmatch(r"CU[1-9][0-9]*" if collection == "citation_use_cases"
                                else r"evidence-[a-z0-9]+(?:-[a-z0-9]+)*", row_id):
                raise ValueError(f"{prefix} row ID is invalid.")
            ids.append(row_id)
            for key in fields - {"id", "evidence_refs"}:
                required_text(row[key], f"{prefix} {row_id} {key}")
            refs = row["evidence_refs"]
            if (not isinstance(refs, list) or not refs or len(refs) != len(set(refs))
                    or any(ref not in finding_by_id for ref in refs)):
                raise ValueError(f"{prefix} {row_id} evidence_refs are invalid.")
            if collection == "evidence_matrix" and len(refs) == 1 and row["source_locator"] != finding_by_id[refs[0]]["source_locator"]:
                raise ValueError(f"{prefix} {row_id} source locator must match its KF.")
        if len(ids) != len(set(ids)):
            raise ValueError(f"{prefix}.{collection} IDs must be unique.")


def resolve_research_clusters(deep_contents, public_by_doi):
    """Validate optional clusters against current public papers and accepted KFs."""
    path = ROOT / "data" / "research_clusters.json"
    if not path.is_file():
        if any(content and content.get("research_cluster_id") for content in deep_contents.values()):
            raise ValueError("Referenced research cluster file is missing.")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("clusters"), dict):
        raise ValueError("Research clusters must use version 1 and a clusters object.")
    content_by_doi = {
        norm_doi(content["doi"]): content for content in deep_contents.values()
        if content and content.get("version") == 2
    }
    referenced = set()
    for cluster_id, cluster in data["clusters"].items():
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", cluster_id):
            raise ValueError("Invalid research cluster ID.")
        if set(cluster) != {"heading", "entity", "relationship_type", "synthesis", "boundaries", "members"}:
            raise ValueError(f"Invalid research cluster fields: {cluster_id}.")
        for field in ("heading", "entity", "relationship_type", "synthesis"):
            required_text(cluster[field], f"{cluster_id}.{field}")
        required_text_list(cluster["boundaries"], f"{cluster_id}.boundaries")
        if not isinstance(cluster["members"], list) or len(cluster["members"]) < 2:
            raise ValueError(f"{cluster_id} must have at least two members.")
        resolved = []
        for member in cluster["members"]:
            fields = {"doi", "cell_context", "mechanistic_axis", "disease_context", "human_evidence", "causal_evidence", "preclinical_intervention", "clinical_boundary", "evidence_refs"}
            if not isinstance(member, dict) or set(member) != fields:
                raise ValueError(f"Invalid member fields in {cluster_id}.")
            doi = norm_doi(member["doi"])
            if doi != member["doi"] or doi not in content_by_doi or doi not in public_by_doi:
                raise ValueError(f"Cluster member {doi} must be a canonical public Deep GEO V2 paper.")
            content = content_by_doi[doi]
            if content.get("research_cluster_id") != cluster_id:
                raise ValueError(f"Cluster member {doi} does not reference {cluster_id}.")
            for field in fields - {"doi", "evidence_refs"}:
                required_text(member[field], f"{cluster_id}.{doi}.{field}")
            refs = required_text_list(member["evidence_refs"], f"{cluster_id}.{doi}.evidence_refs")
            finding_ids = {finding["id"] for finding in content["key_findings"]}
            if not set(refs) <= finding_ids:
                raise ValueError(f"Unknown evidence ref for cluster member {doi}.")
            publication = public_by_doi[doi]
            resolved.append({**member, "paper_url": publication["paper_url"], "title": publication["title"]})
            referenced.add(doi)
        if len({member["doi"] for member in resolved}) != len(resolved):
            raise ValueError(f"Duplicate cluster member in {cluster_id}.")
        for member in resolved:
            content_by_doi[member["doi"]]["_research_cluster"] = {**cluster, "id": cluster_id, "members": resolved}
    dangling = {doi for doi, content in content_by_doi.items() if content.get("research_cluster_id")} - referenced
    if dangling:
        raise ValueError(f"Unresolved research cluster member(s): {sorted(dangling)}")


def with_research_cluster(content, public_by_doi):
    """Resolve optional cluster links for a direct, standalone page render."""
    cluster_id = content.get("research_cluster_id")
    if not cluster_id or content.get("_research_cluster"):
        return content
    data = json.loads((ROOT / "data/research_clusters.json").read_text(encoding="utf-8"))
    cluster = data["clusters"].get(cluster_id)
    if cluster is None:
        raise ValueError(f"Unknown research cluster: {cluster_id}.")
    members = []
    for member in cluster["members"]:
        publication = (public_by_doi or {}).get(member["doi"])
        if publication is None:
            raise ValueError(f"Research cluster member is not public: {member['doi']}.")
        paper_url = publication.get("paper_url") or absolute(
            load_site_config()["site_url"], f"papers/{publication['slug']}.html"
        )
        members.append({**member, "paper_url": paper_url,
                        "title": publication["title"]})
    return {**content, "_research_cluster": {**cluster, "id": cluster_id,
                                                "members": members}}


def validate_citation_pilot(pilot, finding_ids, label):
    prefix = f"{label} citation_pilot"
    required = {"methodology_boundaries", "evidence_matrix", "selected_evidence_sources"}
    if not isinstance(pilot, dict) or set(pilot) != required:
        raise ValueError(f"{prefix} must contain only the three pilot structures.")
    required_text_list(pilot["methodology_boundaries"], f"{prefix} methodology_boundaries")
    rows = pilot["evidence_matrix"]
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{prefix} evidence_matrix must be a non-empty array.")
    row_keys = {
        "id", "intervention", "rationale", "timing_tested", "evidence_level",
        "main_endpoint", "hard_outcome_status", "source_locator",
    }
    row_ids = []
    for position, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or set(row) != row_keys:
            raise ValueError(f"{prefix} matrix row {position} has invalid fields.")
        row_id = required_text(row["id"], f"{prefix} matrix row ID")
        if not re.fullmatch(r"evidence-[a-z0-9]+(?:-[a-z0-9]+)*", row_id):
            raise ValueError(f"{prefix} matrix row {position} has an invalid anchor ID.")
        row_ids.append(row_id)
        for key in row_keys - {"id"}:
            required_text(row[key], f"{prefix} matrix row {position} {key}")
    if len(row_ids) != len(set(row_ids)):
        raise ValueError(f"{prefix} matrix row IDs must be unique.")
    sources = pilot["selected_evidence_sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"{prefix} selected_evidence_sources must be a non-empty array.")
    source_dois = []
    for position, source in enumerate(sources, start=1):
        if not isinstance(source, dict) or set(source) != {
            "doi", "title", "relationship", "evidence_refs"
        }:
            raise ValueError(f"{prefix} source {position} has invalid fields.")
        doi = required_text(source["doi"], f"{prefix} source {position} DOI")
        if doi != norm_doi(doi) or not re.fullmatch(r"10\.\d{4,9}/\S+", doi):
            raise ValueError(f"{prefix} source {position} DOI must be normalized and valid.")
        source_dois.append(doi)
        required_text(source["title"], f"{prefix} source {position} title")
        required_text(source["relationship"], f"{prefix} source {position} relationship")
        refs = required_text_list(
            source["evidence_refs"], f"{prefix} source {position} evidence_refs"
        )
        if any(ref not in finding_ids for ref in refs):
            raise ValueError(f"{prefix} source {position} evidence_refs must resolve to findings.")
    if len(source_dois) != len(set(source_dois)):
        raise ValueError(f"{prefix} selected evidence DOIs must be unique.")


def resolve_related_papers(content, public_by_doi, site_root):
    resolved = []
    current_doi = norm_doi(content.get("doi"))
    for relationship in content.get("related_papers", []):
        doi = norm_doi(relationship.get("doi"))
        publication = (public_by_doi or {}).get(doi)
        if doi == current_doi or publication is None:
            raise ValueError(f"Related DOI {doi!r} does not resolve to another public paper.")
        resolved.append(
            {
                "doi": doi,
                "relationship": relationship["relationship"],
                "title": publication.get("title") or "Untitled work",
                "url": publication.get("paper_url")
                or absolute(site_root, f"papers/{publication['slug']}.html"),
            }
        )
    return resolved


def paper_schema(publication, paper_url, config):
    title = publication.get("title") or "Untitled work"
    authors = publication_authors(publication)
    explicit_positions = publication.get("researcher_author_positions")
    if explicit_positions is not None and any(
        not exact_name_match(authors[position - 1], config["researcher_name"])
        for position in explicit_positions
    ):
        raise ValueError("researcher_author_positions must identify the site's researcher.")
    result = {
        "@context": "https://schema.org",
        "@type": schema_type(publication),
        "name": title,
        "headline": title,
        "url": paper_url,
        "mainEntityOfPage": paper_url,
        "author": (
            [
                researcher_reference(config)
                if (position in explicit_positions if explicit_positions is not None
                    else exact_name_match(author, config["researcher_name"]))
                else {"@type": "Person", "name": author}
                for position, author in enumerate(authors, start=1)
            ]
            if authors
            else researcher_reference(config)
        ),
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


def render_deep_v1_html(content):
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


def render_deep_v1_markdown(content):
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


def v2_label(key):
    labels = {
        "unique_total_n": "Unique total",
        "initial_variables": "Initial predictors",
        "candidate_survival_features": "Candidate survival features",
        "algorithm_count": "Algorithms",
        "modeling_schemes": "Modeling schemes",
        "selected_algorithms": "Selected algorithms",
        "feature_selection": "Feature selection",
        "final_predictor_count": "Final predictors",
        "final_predictors": "Final predictor set",
        "external_validation": "External validation",
        "models_tools": "Models & Tools",
        "datasets_cohorts": "Datasets & Cohorts",
        "publisher_url": "Publisher",
        "pubmed_url": "PubMed",
        "pmcid": "PMCID",
        "code_url": "Code",
        "tool_url": "Clinical tool",
    }
    return labels.get(key, key.replace("_", " ").title())


def v2_study_heading(content):
    if content["study_profile"]["profile_type"] == "narrative_review":
        return "Review Design & Evidence Synthesis"
    return (
        "Study Design & Model Development"
        if content.get("model_profile")
        else "Study Design & Analytical Framework"
    )


def v2_study_label(key, profile_type):
    if key == "external_validation":
        return (
            "External validation"
            if profile_type == "clinical_cohort"
            else "External dataset evaluation"
        )
    return v2_label(key)


def v2_value(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def v2_snapshot_items(content):
    study = content["study_profile"]
    if study["profile_type"] != "clinical_cohort":
        return [(item["label"], item["value"]) for item in study["scale_metrics"]]
    model = content.get("model_profile") or {}
    items = [("Unique total", f"n={study['unique_total_n']:,}")]
    for cohort in study["cohorts"]:
        relation = f"; subset of {cohort['subset_of']}" if cohort.get("subset_of") else ""
        items.append((cohort["name"], f"n={cohort['n']:,}{relation}"))
    for key in (
        "initial_variables",
        "candidate_survival_features",
        "algorithm_count",
        "modeling_schemes",
        "final_predictor_count",
    ):
        if key in model:
            items.append((v2_label(key), v2_value(model[key])))
    for finding in content["key_findings"]:
        for evidence in finding["evidence"]:
            if evidence["label"].casefold() == "average c-index":
                items.append((evidence["label"], evidence["value"]))
    return items


def render_v2_evidence_html(finding):
    evidence = finding["evidence"]
    finding_id = html.escape(finding["id"], quote=True)
    if len(evidence) > 1:
        rows = "".join(
            "<tr><th scope=\"row\">"
            + html.escape(item["label"])
            + "</th><td>"
            + html.escape(item["value"])
            + "</td></tr>"
            for item in evidence
        )
        return (
            f'<table class="paper-geo-v2__evidence-table" data-key-finding-id="{finding_id}">'
            f"<caption>Evidence for {finding_id}</caption>"
            "<thead><tr><th scope=\"col\">Measure</th><th scope=\"col\">Value</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )
    item = evidence[0]
    return (
        '<dl class="paper-geo-v2__single-evidence">'
        f"<dt>{html.escape(item['label'])}</dt><dd>{html.escape(item['value'])}</dd></dl>"
    )


def render_citation_pilot_html(pilot):
    columns = (
        ("Intervention / drug class", "intervention"),
        ("Rhythmic biological rationale", "rationale"),
        ("Timing directly tested?", "timing_tested"),
        ("Evidence level", "evidence_level"),
        ("Main endpoint", "main_endpoint"),
        ("Hard cardiovascular outcome status", "hard_outcome_status"),
        ("Review locator", "source_locator"),
    )


    boundaries = "".join(
        f"<li>{html.escape(item)}</li>" for item in pilot["methodology_boundaries"]
    )
    headers = "".join(f'<th scope="col">{html.escape(label)}</th>' for label, _ in columns)
    rows = "".join(
        "<tr>"
        f'<th scope="row" id="{html.escape(row["id"], quote=True)}">'
        f'{html.escape(row["intervention"])}</th>'
        + "".join(
            f"<td>{html.escape(row[key])}</td>" for _, key in columns[1:]
        )
        + "</tr>"
        for row in pilot["evidence_matrix"]
    )
    sources = "".join(
        "<li><strong>"
        + html.escape(source["title"])
        + "</strong><br><a href=\""
        + html.escape(doi_url(source["doi"]), quote=True)
        + "\">"
        + html.escape(doi_url(source["doi"]))
        + "</a><p>"
        + html.escape(source["relationship"])
        + "</p><p>Evidence: "
        + html.escape(", ".join(source["evidence_refs"]))
        + "</p></li>"
        for source in pilot["selected_evidence_sources"]
    )
    return (
        '<section class="paper-geo-v2__section" id="methodological-boundaries" '
        'data-citation-pilot-section="boundaries"><h2>Methodological &amp; '
        f'Translation Boundaries</h2><ol>{boundaries}</ol></section>'
        '<section class="paper-geo-v2__section" id="chronotherapy-evidence-matrix" '
        'data-citation-pilot-section="matrix"><h2>Chronotherapy Evidence Matrix</h2>'
        '<div class="paper-geo-v2__table-wrap"><table class="paper-geo-v2__table">'
        f'<caption>Chronotherapy evidence levels and outcomes</caption><thead><tr>{headers}'
        f'</tr></thead><tbody>{rows}</tbody></table></div></section>'
        '<section class="paper-geo-v2__section" id="selected-evidence-sources" '
        'data-citation-pilot-section="sources"><h2>Selected Evidence Sources</h2>'
        f'<p>{html.escape(SELECTED_EVIDENCE_NOTICE)}</p><ol>{sources}</ol></section>'
    )


def render_citation_layer_html(layer):
    refs = lambda row: ", ".join(
        f'<a href="#{html.escape(ref.lower(), quote=True)}">{html.escape(ref)}</a>'
        for ref in row["evidence_refs"]
    )
    use_cases = "".join(
        f'<li id="{html.escape(row["id"].lower(), quote=True)}"><strong>'
        f'{html.escape(row["id"])}: {html.escape(row["query"])}</strong>'
        f'<p>{html.escape(row["supported_scope"])}</p>'
        f'<p>Evidence: {refs(row)}</p></li>'
        for row in layer["citation_use_cases"]
    )
    boundaries = "".join(
        f'<li>{html.escape(text)}</li>'
        for text in layer["not_appropriate_as_evidence_for"]
    )
    columns = ("component", "context", "finding", "evidence_level", "scope", "source_locator")
    headers = "".join(f'<th scope="col">{html.escape(v2_label(key))}</th>' for key in columns)
    rows = "".join(
        f'<tr id="{html.escape(row["id"], quote=True)}">'
        f'<th scope="row">{html.escape(row["id"])}</th>'
        + "".join(f'<td>{html.escape(row[key])}</td>' for key in columns)
        + f'<td>{refs(row)}</td></tr>'
        for row in layer["evidence_matrix"]
    )
    return (
        '<section class="paper-geo-v2__section" id="citation-use-cases">'
        f'<h2>When This Study Is Useful to Cite</h2><ol>{use_cases}</ol></section>'
        '<section class="paper-geo-v2__section" id="citation-boundaries">'
        f'<h2>What This Study Should Not Be Cited to Claim</h2><ul>{boundaries}</ul></section>'
        '<section class="paper-geo-v2__section" id="evidence-matrix">'
        '<h2>Evidence Matrix</h2><div class="paper-geo-v2__table-wrap">'
        '<table class="paper-geo-v2__table"><thead><tr>'
        f'<th scope="col">Row ID</th>{headers}<th scope="col">Evidence refs</th></tr></thead><tbody>{rows}</tbody>'
        '</table></div></section>'
    )


def render_research_cluster_html(cluster):
    columns = ("cell_context", "mechanistic_axis", "human_evidence", "causal_evidence", "preclinical_intervention", "clinical_boundary")
    rows = "".join(
        '<tr><th scope="row"><a href="' + html.escape(member["paper_url"], quote=True)
        + '">' + html.escape(member["title"]) + '</a><br><a href="'
        + html.escape(doi_url(member["doi"]), quote=True) + '">'
        + html.escape(member["doi"]) + '</a></th>'
        + "".join(f'<td>{html.escape(member[key] + ("; " + member["disease_context"] if key == "cell_context" else ""))}</td>' for key in columns)
        + '</tr>' for member in cluster["members"]
    )
    headers = "".join(f'<th scope="col">{html.escape(v2_label(key))}</th>' for key in columns)
    boundaries = "".join(f'<li>{html.escape(item)}</li>' for item in cluster["boundaries"])
    return (
        '<section class="paper-geo-v2__section" id="research-cluster-'
        + html.escape(cluster["id"], quote=True) + '"><h2>'
        + html.escape(cluster["heading"]) + '</h2><p><strong>Shared entity: '
        + html.escape(cluster["entity"]) + '</strong>; relationship: '
        + html.escape(cluster["relationship_type"]) + '.</p><p>'
        + html.escape(cluster["synthesis"]) + '</p><div class="paper-geo-v2__table-wrap">'
        + '<table class="paper-geo-v2__table"><thead><tr><th scope="col">Paper</th>'
        + headers + '</tr></thead><tbody>' + rows + '</tbody></table></div><ul>'
        + boundaries + '</ul></section>'
    )


def render_deep_v2_html(content, related_papers):
    study = content["study_profile"]
    profile_type = study["profile_type"]
    model = content.get("model_profile") or {}
    snapshot = "".join(
        '<div class="paper-geo-v2__evidence"><dt>'
        + html.escape(label)
        + "</dt><dd>"
        + html.escape(value)
        + "</dd></div>"
        for label, value in v2_snapshot_items(content)
    )
    findings = "".join(
        '<article class="paper-geo-v2__finding" data-key-finding-id="'
        + html.escape(finding["id"], quote=True)
        + (
            '" id="' + html.escape(finding["id"].lower(), quote=True)
            if content.get("citation_pilot") or content.get("citation_layer") else ""
        )
        + '"><h3><span class="paper-geo-v2__finding-id">'
        + html.escape(finding["id"])
        + "</span> "
        + html.escape(finding["claim"])
        + '</h3><p class="paper-geo-v2__context">'
        + html.escape(finding["context"])
        + "</p>"
        + render_v2_evidence_html(finding)
        + '<p class="paper-geo-v2__source"><strong>Source locator:</strong> '
        + html.escape(finding["source_locator"])
        + "</p></article>"
        for finding in content["key_findings"]
    )
    cohort_rows = "".join(
        "<tr><th scope=\"row\">"
        + html.escape(cohort["name"])
        + "</th><td>"
        + html.escape(cohort["role"])
        + "</td><td>"
        + f"{cohort['n']:,}"
        + "</td><td>"
        + html.escape(
            (
                "Subset of " + cohort["subset_of"]
                if cohort.get("subset_of")
                else "Contains " + ", ".join(cohort["contains"])
                if cohort.get("contains")
                else "Independent cohort"
            )
        )
        + "</td></tr>"
        for cohort in study.get("cohorts", [])
    )
    study_detail_keys = (
        ["study_design", "evidence_type", "diseases_covered", "translation_scope"]
        if profile_type == "narrative_review"
        else ["study_design", "evidence_type", "population", "primary_endpoint",
              "secondary_endpoint", "external_validation"]
    )
    if profile_type == "clinical_cohort":
        study_detail_keys.insert(2, "unique_total_n")
    study_details = "".join(
        f"<dt>{html.escape(v2_study_label(key, profile_type))}</dt>"
        f"<dd>{html.escape(v2_value(study[key]))}</dd>"
        for key in study_detail_keys
    )
    modalities = "".join(
        f"<li>{html.escape(item)}</li>" for item in study[
            "evidence_domains" if profile_type == "narrative_review" else "data_modalities"
        ]
    )
    model_html = ""
    if model:
        model_details = "".join(
            f"<dt>{html.escape(v2_label(key))}</dt><dd>{html.escape(v2_value(value))}</dd>"
            for key, value in model.items()
            if key not in {"final_predictors", "interpretability"}
        )
        final_predictors = model.get("final_predictors") or []
        interpretability = model.get("interpretability") or []
        predictors = "".join(
            f"<li>{html.escape(item)}</li>" for item in final_predictors
        )
        interpretations = "".join(
            f"<li>{html.escape(item)}</li>" for item in interpretability
        )
        model_html = (
            "<h3>Model development</h3>"
            f'<dl class="paper-geo-v2__profile">{model_details}</dl>'
        )
        if final_predictors:
            model_html += (
                "<h3>Final predictor set</h3>"
                f'<ol class="paper-geo-v2__compact-list">{predictors}</ol>'
            )
        if interpretability:
            model_html += (
                "<h3>Interpretability</h3>"
                f'<ul class="paper-geo-v2__compact-list">{interpretations}</ul>'
            )
    additions = "".join(
        f"<li>{html.escape(item)}</li>" for item in content["what_this_adds"]
    )
    scope = content["evidence_scope"]
    supports = "".join(f"<li>{html.escape(item)}</li>" for item in scope["supports"])
    does_not = "".join(
        f"<li>{html.escape(item)}</li>" for item in scope["does_not_establish"]
    )
    limitations = "".join(
        f"<li>{html.escape(item)}</li>" for item in content["limitations"]
    )
    qa = "".join(
        '<article class="paper-geo-v2__qa"><h3>'
        + html.escape(item["question"])
        + "</h3><p>"
        + html.escape(item["answer"])
        + "</p>"
        + (
            '<p class="paper-geo-v2__refs"><strong>Evidence:</strong> '
            + html.escape(", ".join(item["evidence_refs"]))
            + "</p>"
            if item.get("evidence_refs")
            else ""
        )
        + "</article>"
        for item in content["qa"]
    )
    concepts = "".join(
        '<div class="paper-geo-v2__concept-group"><h3>'
        + html.escape(v2_label(category))
        + '</h3><div class="tags">'
        + "".join(f'<span class="tag">{html.escape(item)}</span>' for item in values)
        + "</div></div>"
        for category, values in content["concepts"].items()
    )
    related = "".join(
        '<li><a href="'
        + html.escape(item["url"], quote=True)
        + '">'
        + html.escape(item["title"])
        + "</a><br><span class=\"meta\">"
        + html.escape(item["relationship"])
        + " · DOI: "
        + html.escape(item["doi"])
        + "</span></li>"
        for item in related_papers
    )
    provenance_rows = [
        (
            "DOI",
            doi_url(content["doi"]),
            doi_url(content["doi"]),
        )
    ]
    for key, value in content["provenance"].items():
        provenance_rows.append(
            (v2_label(key), value if key.endswith("_url") else "", value)
        )
    provenance = "".join(
        "<dt>"
        + html.escape(label)
        + "</dt><dd>"
        + (
            f'<a href="{html.escape(url, quote=True)}">{html.escape(value)}</a>'
            if url
            else html.escape(value)
        )
        + "</dd>"
        for label, url, value in provenance_rows
    )
    notice = content["evidence_page_notice"]
    notice_first, _, notice_rest = notice.partition(". ")
    notice_html = (
        f"<strong>{html.escape(notice_first)}.</strong> {html.escape(notice_rest)}"
        if notice_rest
        else html.escape(notice)
    )
    snapshot_heading = (
        "Evidence Base" if profile_type == "narrative_review" else
        "Evidence Snapshot" if profile_type == "clinical_cohort" else "Evidence Scale"
    )
    counting_note_html = (
        "<h3>Counting note</h3><p>"
        + html.escape(study["counting_note"])
        + "</p>"
        if profile_type != "clinical_cohort"
        else ""
    )
    cohort_html = (
        '<h3>Cohort hierarchy</h3><div class="paper-geo-v2__table-wrap">'
        '<table class="paper-geo-v2__table"><thead><tr><th scope="col">Cohort</th>'
        '<th scope="col">Role</th><th scope="col">n</th><th scope="col">Relationship</th>'
        f"</tr></thead><tbody>{cohort_rows}</tbody></table></div>"
        if profile_type == "clinical_cohort"
        else ""
    )
    pilot_html = (
        render_citation_pilot_html(content["citation_pilot"])
        if content.get("citation_pilot") else ""
    )
    layer_html = (
        render_citation_layer_html(content["citation_layer"])
        if content.get("citation_layer") else ""
    )
    cluster_html = (
        render_research_cluster_html(content["_research_cluster"])
        if content.get("_research_cluster") else ""
    )
    return f'''<div class="paper-geo-v2" data-paper-geo-version="2">
<section class="paper-geo-v2__section" data-v2-section="evidence-snapshot"><h2>{snapshot_heading}</h2><p><strong>{html.escape(content["display_title"])}</strong></p><p>{html.escape(content["summary"])}</p><dl class="paper-geo-v2__evidence-grid">{snapshot}</dl>{counting_note_html}</section>
<section class="paper-geo-v2__section" data-v2-section="research-question"><h2>Research Question</h2><p>{html.escape(content["research_question"])}</p></section>
<section class="paper-geo-v2__section" data-v2-section="author-summary"><h2>Author Evidence Summary</h2><p>{html.escape(content["author_summary"])}</p></section>
<section class="paper-geo-v2__section" data-v2-section="key-findings"><h2>Key Findings</h2><div class="paper-geo-v2__findings">{findings}</div></section>
<section class="paper-geo-v2__section" data-v2-section="study-design"><h2>{html.escape(v2_study_heading(content))}</h2><h3>{'Review profile' if profile_type == 'narrative_review' else 'Study profile'}</h3><dl class="paper-geo-v2__profile">{study_details}</dl>{cohort_html}<h3>{'Evidence domains' if profile_type == 'narrative_review' else 'Data modalities'}</h3><ul class="paper-geo-v2__compact-list">{modalities}</ul>{model_html}</section>
<section class="paper-geo-v2__section" data-v2-section="what-this-adds"><h2>{'What This Review Adds' if profile_type == 'narrative_review' else 'What This Study Adds'}</h2><ul>{additions}</ul></section>
<section class="paper-geo-v2__section" data-v2-section="evidence-scope"><h2>Evidence Scope</h2><div class="paper-geo-v2__scope"><div><h3>Supports</h3><ul>{supports}</ul></div><div><h3>Does Not Establish</h3><ul>{does_not}</ul></div></div><h3>Limitations</h3><ul>{limitations}</ul></section>{pilot_html}{layer_html}{cluster_html}
<section class="paper-geo-v2__section" data-v2-section="qa"><h2>Q&amp;A</h2><div class="paper-geo-v2__qa-list">{qa}</div></section>
<section class="paper-geo-v2__section" data-v2-section="concepts"><h2>Concepts &amp; Entities</h2><div class="paper-geo-v2__concepts">{concepts}</div></section>
<section class="paper-geo-v2__section" data-v2-section="related-research"><h2>Related Research</h2><ul class="paper-geo-v2__related">{related}</ul></section>
<section class="paper-geo-v2__section" data-v2-section="provenance"><h2>Publication &amp; Provenance</h2><dl class="paper-geo-v2__provenance">{provenance}</dl></section>
<section class="paper-geo-v2__notice"><div class="notice">{notice_html}</div></section>
</div>'''


def markdown_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_citation_pilot_markdown(pilot):
    columns = (
        ("Intervention / drug class", "intervention"),
        ("Rhythmic biological rationale", "rationale"),
        ("Timing directly tested?", "timing_tested"),
        ("Evidence level", "evidence_level"),
        ("Main endpoint", "main_endpoint"),
        ("Hard cardiovascular outcome status", "hard_outcome_status"),
        ("Review locator", "source_locator"),
    )
    parts = [
        "## Methodological & Translation Boundaries",
        "",
        *[
            f"{position}. {item}"
            for position, item in enumerate(pilot["methodology_boundaries"], start=1)
        ],
        "",
        "## Chronotherapy Evidence Matrix",
        "",
        "| " + " | ".join(label for label, _ in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
        *[
            "| " + " | ".join(markdown_cell(row[key]) for _, key in columns) + " |"
            for row in pilot["evidence_matrix"]
        ],
        "",
        "## Selected Evidence Sources",
        "",
        SELECTED_EVIDENCE_NOTICE,
        "",
    ]
    for position, source in enumerate(pilot["selected_evidence_sources"], start=1):
        url = doi_url(source["doi"])
        parts.extend([
            f"{position}. **{source['title']}** — [{url}]({url})",
            f"   Relationship: {source['relationship']}",
            f"   Evidence: {', '.join(source['evidence_refs'])}",
            "",
        ])
    return parts


def render_citation_layer_markdown(layer):
    parts = [
        '<a id="citation-use-cases"></a>',
        "## When This Study Is Useful to Cite", "",
    ]
    for row in layer["citation_use_cases"]:
        parts.extend([
            f"### {row['id']}: {row['query']}", "",
            row["supported_scope"], "",
            "Evidence: " + ", ".join(f"[{ref}](#{ref.lower()})" for ref in row["evidence_refs"]),
            "",
        ])
    parts.extend([
        '<a id="citation-boundaries"></a>',
        "## What This Study Should Not Be Cited to Claim", "",
        *[f"- {boundary}" for boundary in layer["not_appropriate_as_evidence_for"]],
        "", '<a id="evidence-matrix"></a>', "## Evidence Matrix", "",
    ])
    for row in layer["evidence_matrix"]:
        parts.extend([f'<a id="{row["id"]}"></a>', f"### {row['component']}", ""])
        for key in ("context", "finding", "evidence_level", "scope", "source_locator"):
            parts.append(f"- {v2_label(key)}: {row[key]}")
        parts.extend([
            "- Evidence refs: " + ", ".join(f"[{ref}](#{ref.lower()})" for ref in row["evidence_refs"]),
            "",
        ])
    return parts


def render_research_cluster_markdown(cluster):
    parts = [
        f'<a id="research-cluster-{cluster["id"]}"></a>',
        f'## {cluster["heading"]}', "",
        f'Shared entity: {cluster["entity"]}; relationship: {cluster["relationship_type"]}.', "",
        cluster["synthesis"], "",
        '| Paper | Cell context | Mechanistic axis | Human evidence | Causal evidence | Preclinical intervention | Clinical boundary |',
        '| --- | --- | --- | --- | --- | --- | --- |',
    ]
    keys = ("cell_context", "mechanistic_axis", "human_evidence", "causal_evidence", "preclinical_intervention", "clinical_boundary")
    for member in cluster["members"]:
        paper = f'[{member["title"]}]({member["paper_url"]}) ([DOI]({doi_url(member["doi"])}))'
        cells = [member[key] + ("; " + member["disease_context"] if key == "cell_context" else "") for key in keys]
        parts.append('| ' + ' | '.join([markdown_cell(paper), *(markdown_cell(cell) for cell in cells)]) + ' |')
    parts.extend(["", *[f'- {boundary}' for boundary in cluster["boundaries"]], ""])
    return parts


def render_deep_v2_markdown(content, related_papers):
    study = content["study_profile"]
    profile_type = study["profile_type"]
    model = content.get("model_profile") or {}
    snapshot_heading = (
        "Evidence Base" if profile_type == "narrative_review" else
        "Evidence Snapshot" if profile_type == "clinical_cohort" else "Evidence Scale"
    )
    snapshot_tail = (
        ["### Counting note", "", study["counting_note"], ""]
        if profile_type != "clinical_cohort"
        else []
    )
    parts = [
        f"## {snapshot_heading}",
        "",
        f"**{content['display_title']}**",
        "",
        content["summary"],
        "",
        "| Evidence | Value |",
        "| --- | --- |",
        *[
            f"| {markdown_cell(label)} | {markdown_cell(value)} |"
            for label, value in v2_snapshot_items(content)
        ],
        "",
        *snapshot_tail,
        "## Research Question",
        "",
        content["research_question"],
        "",
        "## Author Evidence Summary",
        "",
        content["author_summary"],
        "",
        "## Key Findings",
        "",
    ]
    for finding in content["key_findings"]:
        parts.extend(
            [
                *([f'<a id="{finding["id"].lower()}"></a>'] if content.get("citation_layer") else []),
                f"### {finding['id']}: {finding['claim']}",
                "",
                f"Context: {finding['context']}",
                "",
                "| Evidence | Value |",
                "| --- | --- |",
                *[
                    f"| {markdown_cell(item['label'])} | {markdown_cell(item['value'])} |"
                    for item in finding["evidence"]
                ],
                "",
                f"Source locator: {finding['source_locator']}",
                "",
            ]
        )
    study_detail_keys = (
        ["study_design", "evidence_type", "diseases_covered", "translation_scope"]
        if profile_type == "narrative_review"
        else ["study_design", "evidence_type", "population", "primary_endpoint",
              "secondary_endpoint", "external_validation"]
    )
    if profile_type == "clinical_cohort":
        study_detail_keys.insert(2, "unique_total_n")
    parts.extend(
        [
            f"## {v2_study_heading(content)}",
            "",
            "### Review profile" if profile_type == "narrative_review" else "### Study profile",
            "",
            *[
                f"- {v2_study_label(key, profile_type)}: {v2_value(study[key])}"
                for key in study_detail_keys
            ],
            ("- Evidence domains: " + ", ".join(study["evidence_domains"])
             if profile_type == "narrative_review"
             else "- Data modalities: " + ", ".join(study["data_modalities"])),
            "",
        ]
    )
    if profile_type == "clinical_cohort":
        parts.extend(
            [
                "### Cohort hierarchy",
                "",
                "| Cohort | Role | n | Relationship |",
                "| --- | --- | ---: | --- |",
            ]
        )
        for cohort in study["cohorts"]:
            relationship = (
                "Subset of " + cohort["subset_of"]
                if cohort.get("subset_of")
                else "Contains " + ", ".join(cohort["contains"])
                if cohort.get("contains")
                else "Independent cohort"
            )
            parts.append(
                f"| {markdown_cell(cohort['name'])} | {markdown_cell(cohort['role'])} | "
                f"{cohort['n']} | {markdown_cell(relationship)} |"
            )
        parts.append("")
    if model:
        parts.extend(["### Model development", ""])
        for key, value in model.items():
            if key not in {"final_predictors", "interpretability"}:
                parts.append(f"- {v2_label(key)}: {v2_value(value)}")
        if model.get("final_predictors"):
            parts.extend(
                [
                    "",
                    "### Final predictor set",
                    "",
                    *[
                        f"{position}. {item}"
                        for position, item in enumerate(model["final_predictors"], 1)
                    ],
                ]
            )
        if model.get("interpretability"):
            parts.extend(
                [
                    "",
                    "### Interpretability",
                    "",
                    *[f"- {item}" for item in model["interpretability"]],
                ]
            )
        parts.append("")
    parts.extend(
        [
            "## What This Review Adds" if profile_type == "narrative_review"
            else "## What This Study Adds",
            "",
            *[f"- {item}" for item in content["what_this_adds"]],
            "",
            "## Evidence Scope",
            "",
            "### Supports",
            "",
            *[f"- {item}" for item in content["evidence_scope"]["supports"]],
            "",
            "### Does Not Establish",
            "",
            *[
                f"- {item}"
                for item in content["evidence_scope"]["does_not_establish"]
            ],
            "",
            "### Limitations",
            "",
            *[f"- {item}" for item in content["limitations"]],
            "",
        ]
    )
    if content.get("citation_pilot"):
        parts.extend(render_citation_pilot_markdown(content["citation_pilot"]))
    if content.get("citation_layer"):
        parts.extend(render_citation_layer_markdown(content["citation_layer"]))
    if content.get("_research_cluster"):
        parts.extend(render_research_cluster_markdown(content["_research_cluster"]))
    parts.extend(["## Q&A", ""])
    for item in content["qa"]:
        parts.extend([f"### {item['question']}", "", item["answer"], ""])
        if item.get("evidence_refs"):
            parts.extend(["Evidence: " + ", ".join(item["evidence_refs"]), ""])
    parts.extend(["## Concepts & Entities", ""])
    for category, values in content["concepts"].items():
        parts.extend([f"### {v2_label(category)}", "", ", ".join(values), ""])
    parts.extend(["## Related Research", ""])
    for item in related_papers:
        parts.extend(
            [
                f"- [{item['title']}]({item['url']}) — {item['relationship']} "
                f"(DOI: {item['doi']})"
            ]
        )
    parts.extend(
        [
            "",
            "## Publication & Provenance",
            "",
            f"- DOI: {doi_url(content['doi'])}",
            *[
                f"- {v2_label(key)}: {value}"
                for key, value in content["provenance"].items()
            ],
            "",
            "## Evidence-page notice",
            "",
            content["evidence_page_notice"],
            "",
        ]
    )
    return "\n".join(parts)


def render_deep_html(content, *, related_papers=None):
    if content.get("version") == 2:
        return render_deep_v2_html(content, related_papers or [])
    return render_deep_v1_html(content)


def render_deep_markdown(content, *, related_papers=None):
    if content.get("version") == 2:
        return render_deep_v2_markdown(content, related_papers or [])
    return render_deep_v1_markdown(content)


def render_official_abstract_html(record, doi):
    abstract = record["abstract"]
    if abstract["type"] == "structured":
        body = "".join(
            f'<h3>{html.escape(section["label"])}</h3>'
            f'<p>{html.escape(section["text"])}</p>'
            for section in abstract["sections"]
        )
    else:
        body = f'<p>{html.escape(abstract["text"])}</p>'
    source = {
        "version_of_record": "Version of Record",
        "publisher": "publisher",
        "pmc": "PMC",
    }[record["source_type"]]
    return (
        '<section id="official-abstract" class="paper-geo-v2__section">'
        f'<h2>Official Abstract</h2>{body}'
        '<p class="paper-geo-v2__source">Text reproduced verbatim from '
        f'{html.escape(source)} (<a href="{html.escape(record["source_url"], quote=True)}">source</a>); '
        f'<a href="{html.escape(doi_url(doi), quote=True)}">DOI</a>; '
        f'<a href="{html.escape(record["license_url"], quote=True)}">{html.escape(record["license"])}</a>.'
        '</p></section>'
    )


def render_official_abstract_markdown(record, doi):
    abstract = record["abstract"]
    parts = ["## Official Abstract", ""]
    if abstract["type"] == "structured":
        for section in abstract["sections"]:
            parts.extend([f"### {section['label']}", "", section["text"], ""])
    else:
        parts.extend([abstract["text"], ""])
    source = {"version_of_record": "Version of Record", "publisher": "publisher", "pmc": "PMC"}[record["source_type"]]
    parts.extend([
        f"Text reproduced verbatim from {source} ([source]({record['source_url']})); "
        f"[DOI]({doi_url(doi)}); [{record['license']}]({record['license_url']}).",
        "",
    ])
    return "\n".join(parts)


def render_paper_html(publication, *, config, deep_content=None, public_by_doi=None,
                      citation_data=None, official_abstract=None):
    site_root = config["site_url"]
    title = publication.get("title") or "Untitled work"
    journal = publication.get("journal") or "Unknown source"
    year = publication.get("year") or "n.d."
    publication_type = publication.get("type") or "Work"
    slug = publication["slug"]
    doi = norm_doi(publication.get("doi"))
    authors = publication_authors(publication)
    canonical = absolute(site_root, f"papers/{slug}.html")
    markdown_url = absolute(site_root, f"papers/{slug}.md")
    is_v2 = bool(deep_content and deep_content.get("version") == 2)
    is_pending = publication.get("paper_geo_status") == "pending"
    related_papers = (
        resolve_related_papers(deep_content, public_by_doi, site_root) if is_v2 else []
    )
    if is_v2:
        deep_content = with_research_cluster(deep_content, public_by_doi)
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
    if is_pending:
        deep_badge = '<span class="badge">Deep GEO · Pending</span>'
    elif deep_content is not None:
        deep_badge = '<span class="badge">Deep GEO</span>'
    else:
        deep_badge = ""
    citation = [
        f'<meta name="citation_title" content="{html.escape(str(title), quote=True)}">',
        f'<meta name="citation_journal_title" content="{html.escape(str(journal), quote=True)}">',
    ]
    citation.extend(
        f'<meta name="citation_author" content="{html.escape(author, quote=True)}">'
        for author in authors
    )
    if publication.get("year"):
        citation_date = (
            citation_data["publication_date"].replace("-", "/")
            if citation_data and citation_data.get("publication_date")
            else str(publication["year"])
        )
        citation.append(
            f'<meta name="citation_publication_date" content="{html.escape(citation_date, quote=True)}">'
        )
        if citation_data and citation_data.get("publication_date"):
            citation.append(
                f'<meta name="citation_date" content="{html.escape(citation_date, quote=True)}">'
            )
    if doi:
        citation.append(f'<meta name="citation_doi" content="{html.escape(doi, quote=True)}">')
    if official_abstract:
        citation.append(
            f'<meta name="citation_abstract" content="{html.escape(abstract_text(official_abstract), quote=True)}">'
        )
    if citation_data:
        for key, tag in (
            ("volume", "citation_volume"), ("issue", "citation_issue"),
            ("first_page", "citation_firstpage"),
            ("last_page", "citation_lastpage"),
            ("article_number", "citation_article_number"),
            ("issn", "citation_issn"), ("eissn", "citation_eIssn"),
            ("publisher", "citation_publisher"), ("pmid", "citation_pmid"),
        ):
            if citation_data.get(key):
                citation.append(
                    f'<meta name="{tag}" content="{html.escape(citation_data[key], quote=True)}">'
                )
    v2_authors_html = ""
    if is_v2:
        author_items = "".join(
            f'<li class="paper-geo-v2__author">{html.escape(author)}</li>'
            for author in authors
        )
        v2_authors_html = (
            '<div class="paper-geo-v2__authors"><h2>Full Authors</h2>'
            f'<ol class="paper-geo-v2__author-list">{author_items}</ol></div>'
        )
    deep_html = (
        render_deep_html(deep_content or {}, related_papers=related_papers)
        if deep_content is not None
        else ""
    )
    pending_html = (
        f'<section><div class="notice">{html.escape(PENDING_NOTICE)}</div></section>'
        if is_pending else ""
    )
    schema = paper_schema(publication, canonical, config)
    if official_abstract:
        schema["abstract"] = abstract_text(official_abstract)
    if is_v2:
        schema["description"] = deep_content["author_summary"]
        schema["keywords"] = flatten_concepts(deep_content)
    elif deep_content and deep_content.get("keywords"):
        schema["keywords"] = [
            str(x).strip() for x in deep_content["keywords"] if str(x).strip()
        ]
    notice_html = ""
    if not is_v2:
        notice_html = (
            f'<section><div class="notice"><strong>Author-controlled academic record for '
            f'{html.escape(config["researcher_name"])} '
            f'({html.escape(config["researcher_name_zh"])}; ORCID '
            f'<a href="{html.escape(orcid_url(config), quote=True)}">'
            f'{html.escape(config["orcid"])}</a>).</strong> This page identifies the work as '
            f'part of {html.escape(config["researcher_name"])}’s publication record. It does '
            "not replace the publisher version or assert a complete author list.</div></section>"
        )
    safe_schema = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
    return with_ga4_tag(f'''<!doctype html>
{GENERATED_MARKER}
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(str(title))} | {html.escape(config["researcher_name"])}</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<link rel="alternate" type="text/markdown" href="{html.escape(markdown_url, quote=True)}">
<meta property="og:title" content="{html.escape(str(title), quote=True)}">
<meta property="og:description" content="{html.escape(description, quote=True)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{html.escape(canonical, quote=True)}">
{chr(10).join(citation)}
<link rel="stylesheet" href="../assets/style.css">{'<script defer src="../assets/citation.js"></script>' if citation_data else ''}</head><body>
<header><nav><a class="brand" href="../index.html">{html.escape(config["researcher_name"])}</a><div class="navlinks"><a href="../index.html#research">Research</a><a href="../publications.html">All publications</a><a href="../index.html#profiles">Profiles</a></div></nav></header>
<main class="wrap">
<section class="hero" style="grid-template-columns:1fr"><div>
<div class="eyebrow">{html.escape(str(publication_type))} · {html.escape(str(year))} {deep_badge}</div>
<h1 style="font-size:clamp(2.2rem,5vw,4rem)">{html.escape(str(title))}</h1>
<p class="lead">{html.escape(str(journal))}</p>{v2_authors_html}
<div class="links">{' '.join(links)}</div>
</div></section>
{(render_official_abstract_html(official_abstract, doi) + chr(10)) if official_abstract else ''}{(render_cite_html(citation_data) + chr(10)) if citation_data else ''}{deep_html}{pending_html}
{notice_html}
<section><div class="links"><a class="btn" href="../publications.html">All Publications</a> <a class="btn" href="../index.html">Homepage</a></div></section>
<script type="application/ld+json">{safe_schema}</script>
</main><footer><div class="wrap">© {html.escape(config["researcher_name"])} · Academic website · ORCID: {html.escape(config["orcid"])}</div></footer>
</body></html>
''')


def render_paper_markdown(publication, *, config, deep_content=None, public_by_doi=None,
                          official_abstract=None):
    site_root = config["site_url"]
    title = publication.get("title") or "Untitled work"
    journal = publication.get("journal") or "Unknown source"
    year = publication.get("year") or "n.d."
    publication_type = publication.get("type") or "Work"
    slug = publication["slug"]
    doi = norm_doi(publication.get("doi"))
    html_url = absolute(site_root, f"papers/{slug}.html")
    md_url = absolute(site_root, f"papers/{slug}.md")
    is_v2 = bool(deep_content and deep_content.get("version") == 2)
    related_papers = (
        resolve_related_papers(deep_content, public_by_doi, site_root) if is_v2 else []
    )
    if is_v2:
        deep_content = with_research_cluster(deep_content, public_by_doi)
    lines = [
        f"# {title}",
        "",
        f"Researcher: {config['researcher_name']}",
        f"Chinese name: {config['researcher_name_zh']}",
        f"ORCID identity anchor: {orcid_url(config)}",
        f"Canonical researcher: {config['person_id']}",
        "",
        f"Journal: {journal}",
        f"Year: {year}",
        f"Type: {publication_type}",
        f"DOI: {doi or 'Not available'}",
        f"Canonical page: {html_url}",
        f"Markdown record: {md_url}",
        "",
    ]
    if is_v2:
        lines.extend(
            [
                "## Full Authors",
                "",
                *[
                    f"{position}. {author}"
                    for position, author in enumerate(
                        publication_authors(publication), start=1
                    )
                ],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## About this record",
                "",
                f"This is an author-controlled publication record in the {config['researcher_name']} "
                "Academic Hub. "
                f"It identifies this work as part of {config['researcher_name']}’s publication record "
                "via ORCID; "
                "the publisher version remains the version of record.",
                "",
            ]
        )
    if deep_content is not None:
        if official_abstract:
            lines.append(render_official_abstract_markdown(official_abstract, doi))
        lines.append(render_deep_markdown(deep_content, related_papers=related_papers))
    elif official_abstract:
        lines.append(render_official_abstract_markdown(official_abstract, doi))
    if publication.get("paper_geo_status") == "pending":
        lines.extend(["## Deep GEO · Pending", "", PENDING_NOTICE, ""])
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


def public_record(publication, *, config, deep_tokens, featured_tokens, deep_contents):
    item = copy.deepcopy(publication)
    item.pop("featured", None)
    token = publication_token(publication)
    slug = publication["slug"]
    item["paper_url"] = absolute(config["site_url"], f"papers/{slug}.html")
    item["markdown_url"] = absolute(config["site_url"], f"papers/{slug}.md")
    item["deep_geo"] = token in deep_tokens
    content = deep_contents.get(token)
    if not item["deep_geo"]:
        item["paper_geo_status"] = "none"
    elif content is None:
        item["paper_geo_status"] = "pending"
    else:
        item["paper_geo_status"] = "v2" if content["version"] == 2 else "v1"
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
                badge = (
                    "Deep GEO · Pending"
                    if publication["paper_geo_status"] == "pending" else "Deep GEO"
                )
                links.append(f'<span class="badge">{badge}</span>')
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
        "name": f"{config['researcher_name']} — Publications",
        "url": absolute(config["site_url"], "publications.html"),
        "mainEntity": researcher_reference(config),
        "hasPart": [paper_schema(item, item["paper_url"], config) for item in items],
    }
    safe_schema = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
    page_title = (
        f"All Publications | {config['researcher_name']} "
        f"({config['researcher_name_zh']})"
    )
    meta_description = (
        f"Publication record of {config['researcher_name']} "
        f"({config['researcher_name_zh']}), using ORCID {config['orcid']} "
        "as the identity anchor."
    )
    publications_url = absolute(config["site_url"], "publications.html")
    return with_ga4_tag(f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(page_title)}</title>
<meta name="description" content="{html.escape(meta_description, quote=True)}">
<link rel="canonical" href="{html.escape(publications_url, quote=True)}">
<meta property="og:title" content="{html.escape(page_title, quote=True)}">
<meta property="og:description" content="{html.escape(meta_description, quote=True)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{html.escape(publications_url, quote=True)}">
<link rel="stylesheet" href="assets/style.css"></head><body>
<header><nav><a class="brand" href="index.html">{html.escape(config["researcher_name"])}</a><div class="navlinks">
<a href="index.html#research">Research</a><a href="publications.html">All publications</a><a href="index.html#profiles">Profiles</a></div></nav></header>
<main class="wrap"><section class="hero" style="grid-template-columns:1fr"><div>
<div class="eyebrow">Publication record</div><h1 style="font-size:clamp(2.8rem,6vw,4.7rem)">Publications</h1>
<p class="lead">This author-controlled publication record for {html.escape(config["researcher_name"])} ({html.escape(config["researcher_name_zh"])}) uses ORCID {html.escape(config["orcid"])} as the identity anchor. Every public record has a permanent HTML page and a machine-friendly Markdown version.</p>
<div class="card" style="margin-top:20px"><div class="count">{len(items)}</div><div class="meta">public works in the current database</div></div>
</div></section>
<section><input id="pubSearch" class="search" placeholder="Search title or journal..." aria-label="Search publications">
<div id="pubList">{''.join(sections)}</div></section>
<section><div class="notice"><strong>Identity control:</strong> automated discovery links {html.escape(config["researcher_name"])} ({html.escape(config["researcher_name_zh"])}) to the exact ORCID iD rather than relying on the author name alone, reducing same-name misattribution.</div></section>
<script>
const box=document.getElementById('pubSearch');box.addEventListener('input',()=>{{const q=box.value.toLowerCase().trim();document.querySelectorAll('.pub').forEach(x=>{{x.style.display=(!q||x.dataset.title.includes(q)||x.dataset.journal.includes(q))?'block':'none'}});document.querySelectorAll('.year-group').forEach(y=>{{y.style.display=[...y.querySelectorAll('.pub')].some(x=>x.style.display!=='none')?'block':'none'}})}})
</script>
<script type="application/ld+json">{safe_schema}</script>
</main><footer><div class="wrap">© {html.escape(config["researcher_name"])} · Academic website · ORCID: {html.escape(config["orcid"])}</div></footer></body></html>
''')


def render_featured_cards(featured_entries, public_by_token, deep_contents):
    cards = []
    for entry in featured_entries:
        token = controller_token(entry)
        publication = public_by_token[token]
        title = publication.get("title") or "Untitled work"
        journal = publication.get("journal") or "Unknown source"
        year = publication.get("year") or "n.d."
        page_url = f"papers/{publication['slug']}.html"
        summary = str(entry.get("summary") or "").strip()
        if not summary and deep_contents.get(token):
            summary = str(deep_contents[token].get("summary") or "").strip()
        if not summary:
            summary = f'A publication in {journal} ({year}) titled “{title}”.'
        links = [f'<a class="btn" href="{html.escape(page_url, quote=True)}">Research page</a>']
        doi = norm_doi(publication.get("doi"))
        if doi:
            links.append(f'<a class="btn" href="{html.escape(doi_url(doi), quote=True)}">DOI</a>')
        status = publication["paper_geo_status"]
        if status == "pending":
            badge = ' <span class="badge">Deep GEO · Pending</span>'
        elif status in {"v1", "v2"}:
            badge = ' <span class="badge">Deep GEO</span>'
        else:
            badge = ""
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
        "researcher": {
            "name": config["researcher_name"],
            "alternateName": config["researcher_name_zh"],
            "url": config["person_id"],
            "orcid": config["orcid"],
        },
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
                "paper_geo_status": item["paper_geo_status"],
                "featured": item["featured"],
            }
            for item in items
        ],
    }
    (ROOT / "paper_index.json").write_text(
        json.dumps(paper_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    short_lines = [
        f"# {config['researcher_name']} Academic Hub",
        "",
        "> An author-controlled academic evidence hub for verified publications and research pages.",
        "",
        f"- Researcher: {config['researcher_name']}",
        f"- Chinese name: {config['researcher_name_zh']}",
        f"- Canonical person: {config['person_id']}",
        f"- ORCID: {orcid_url(config)}",
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
        f"# {config['researcher_name']} Academic Hub — Full Publication Index",
        "",
        f"- Researcher: {config['researcher_name']}",
        f"- Chinese name: {config['researcher_name_zh']}",
        f"- Canonical person: {config['person_id']}",
        f"- ORCID: {orcid_url(config)}",
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
    profile = load_profile_config()
    config = load_site_config(profile)
    previous_lastmods = load_sitemap_lastmods(ROOT / "sitemap.xml")
    today = datetime.now(timezone.utc).date().isoformat()
    html_changed = {}
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
    citation_metadata = load_citation_metadata(public_master)
    official_abstracts = load_official_abstracts(public_master)
    deep_contents = {
        publication_token(publication): load_deep_content(publication, allow_missing=True)
        for publication in public_master
        if publication_token(publication) in deep_tokens
    }
    public_items = [
        public_record(
            publication,
            config=config,
            deep_tokens=deep_tokens,
            featured_tokens=featured_tokens,
            deep_contents=deep_contents,
        )
        for publication in public_master
    ]
    public_by_token = {publication_token(item): item for item in public_items}
    public_by_doi = {
        norm_doi(item.get("doi")): item
        for item in public_items
        if norm_doi(item.get("doi"))
    }
    resolve_research_clusters(deep_contents, public_by_doi)
    citation_by_slug = {
        item["slug"]: citation_record(item, citation_metadata, config["site_url"])
        for item in public_items
    }
    expected_slugs = {item["slug"] for item in public_items}
    missing_legacy = sorted(set(LEGACY_DEEP_SLUGS) - expected_slugs)
    if missing_legacy:
        raise ValueError("Protected legacy paper slug(s) missing: " + ", ".join(missing_legacy))
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    DEEP_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    for item in public_items:
        token = publication_token(item)
        deep_content = deep_contents.get(token)
        paper_url = item["paper_url"]
        html_changed[paper_url] = write_public_html_if_changed(
            PAPERS_DIR / f"{item['slug']}.html",
            render_paper_html(
                item,
                config=config,
                deep_content=deep_content,
                public_by_doi=public_by_doi,
                citation_data=citation_by_slug[item["slug"]],
                official_abstract=official_abstracts.get(norm_doi(item.get("doi"))),
            ),
        )
        write_text_if_changed(
            PAPERS_DIR / f"{item['slug']}.md",
            render_paper_markdown(
                item,
                config=config,
                deep_content=deep_content,
                public_by_doi=public_by_doi,
                official_abstract=official_abstracts.get(norm_doi(item.get("doi"))),
            ),
        )
    CITATIONS_DIR.mkdir(parents=True, exist_ok=True)
    expected_citation_files = set()
    for record in citation_by_slug.values():
        if record is None:
            continue
        files = citation_files(record)
        for name, render in (
            (files["bib"], render_bibtex),
            (files["ris"], render_ris),
            (files["csl"], render_csl_json),
        ):
            expected_citation_files.add(name)
            write_text_if_changed(CITATIONS_DIR / name, render(record))
    unexpected_citation_files = {
        path.name for path in CITATIONS_DIR.iterdir()
    } - expected_citation_files
    if unexpected_citation_files:
        raise ValueError("Unexpected citation exports: " + ", ".join(sorted(unexpected_citation_files)))
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
                "paper_url", "deep_geo", "paper_geo_status", "featured",
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
                    "paper_geo_status": item["paper_geo_status"],
                    "featured": str(bool(item["featured"])).lower(),
                }
            )
    publications_url = absolute(config["site_url"], "publications.html")
    html_changed[publications_url] = write_public_html_if_changed(
        ROOT / "publications.html", render_publications_page(public_items, config)
    )

    index_path = ROOT / "index.html"
    index_html = index_path.read_text(encoding="utf-8")
    if index_html.count(FEATURED_START) != 1 or index_html.count(FEATURED_END) != 1:
        raise ValueError("index.html must contain exactly one Featured controller marker pair.")
    before, remainder = index_html.split(FEATURED_START, 1)
    _, after = remainder.split(FEATURED_END, 1)
    index_html = (
        before + FEATURED_START + "\n"
        + render_featured_cards(featured_entries, public_by_token, deep_contents)
        + "\n" + FEATURED_END + after
    )
    index_html = re.sub(
        r'View all (?:<span id="pubCount">\d+</span>|\d+) publications',
        f'View all <span id="pubCount">{len(public_items)}</span> publications',
        index_html,
    )
    index_html = update_homepage(index_html, config)
    homepage_url = f"{config['site_url']}/"
    html_changed[homepage_url] = write_public_html_if_changed(index_path, index_html)

    deep_items = [public_by_token[controller_token(entry)] for entry in deep_entries]
    write_machine_indexes(public_items, deep_items, config)
    urls = [
        homepage_url,
        publications_url,
        *[item["paper_url"] for item in public_items],
    ]
    lastmods = {
        url: resolve_lastmod(url, html_changed[url], previous_lastmods, today)
        for url in urls
    }
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(
            "  <url>\n"
            f"    <loc>{html.escape(url)}</loc>\n"
            f"    <lastmod>{lastmods[url]}</lastmod>\n"
            "  </url>"
            for url in urls
        )
        + "\n</urlset>\n"
    )
    write_text_if_changed(ROOT / "sitemap.xml", sitemap)
    (ROOT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {absolute(config['site_url'], 'sitemap.xml')}\n",
        encoding="utf-8",
    )
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
