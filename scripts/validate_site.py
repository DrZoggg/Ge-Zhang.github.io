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
    v2_label,
    v2_value,
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
APVS_DOI = "10.1016/j.isci.2023.107587"
SMC_FATE_DOI = "10.1186/s12967-022-03795-9"
OLINK_DCM_DOI = "10.1021/acs.jproteome.4c00522"


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


def single_property_meta_content(markup, property_name, label):
    return single_html_url(
        markup,
        rf'<meta property="{re.escape(property_name)}" content="([^"]*)">',
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
        for key, item in value.items():
            if key == "profile_type":
                continue
            yield from string_leaves(item)


def validate_v2_rendered_page(
    content, publication, page, markdown, schema, public_by_doi, config
):
    label = f"{publication.get('slug') or publication.get('title')} Paper GEO 2.0"
    validate_deep_v2_content(content, label)
    require(content.get("version") == 2, f"{label} must use version 2.")
    require(
        norm_doi(content.get("doi")) == norm_doi(publication.get("doi")),
        f"{label} DOI does not match its master record.",
    )

    study = content["study_profile"]
    profile_type = study["profile_type"]
    findings = {item["id"]: item for item in content["key_findings"]}
    for finding_id, finding in findings.items():
        expected_occurrences = 2 if len(finding["evidence"]) > 1 else 1
        require(
            page.count(f'data-key-finding-id="{finding_id}"') == expected_occurrences,
            f"{label} {finding_id} evidence rendering changed.",
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

    snapshot_heading = (
        "Evidence Snapshot" if profile_type == "clinical_cohort" else "Evidence Scale"
    )
    expected_study_heading = (
        "Study Design & Model Development"
        if content.get("model_profile")
        else "Study Design & Analytical Framework"
    )
    unexpected_study_heading = (
        "Study Design & Analytical Framework"
        if content.get("model_profile")
        else "Study Design & Model Development"
    )
    expected_external_label = (
        "External validation"
        if profile_type == "clinical_cohort"
        else "External dataset evaluation"
    )
    unexpected_external_label = (
        "External dataset evaluation"
        if profile_type == "clinical_cohort"
        else "External validation"
    )
    expected_headings = [
        "Full Authors",
        snapshot_heading,
        "Research Question",
        "Author Evidence Summary",
        "Key Findings",
        expected_study_heading,
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
    snapshot_markup = page.split(
        'data-v2-section="evidence-snapshot"', 1
    )[1].split('data-v2-section="research-question"', 1)[0]
    study_markup = page.split('data-v2-section="study-design"', 1)[1].split(
        'data-v2-section="what-this-adds"', 1
    )[0]
    require(
        f"## {expected_study_heading}" in markdown,
        f"{label} Markdown study heading changed.",
    )
    require(
        f"## {unexpected_study_heading}" not in markdown,
        f"{label} Markdown renders a study heading for the wrong source semantics.",
    )
    study_labels = element_texts(study_markup, "dt")
    require(
        study_labels.count(expected_external_label) == 1,
        f"{label} external evidence label changed.",
    )
    require(
        unexpected_external_label not in study_labels,
        f"{label} renders an external evidence label for the wrong profile type.",
    )
    external_value = v2_value(study["external_validation"])
    require(
        f"<dt>{expected_external_label}</dt><dd>{external_value}</dd>"
        in study_markup,
        f"{label} external evidence value changed.",
    )
    require(
        f"- {expected_external_label}: {external_value}" in markdown,
        f"{label} Markdown external evidence label changed.",
    )
    require(
        f"- {unexpected_external_label}:" not in markdown,
        f"{label} Markdown renders an external evidence label for the wrong profile type.",
    )
    if profile_type == "clinical_cohort":
        require("Unique total" in snapshot_markup, f"{label} unique total is missing.")
        require("Cohort hierarchy" in study_markup, f"{label} cohort hierarchy is missing.")
        require(
            f"n={study['unique_total_n']:,}" in snapshot_markup,
            f"{label} unique total is not rendered in HTML.",
        )
        require(
            str(study["unique_total_n"]) in markdown
            or f"{study['unique_total_n']:,}" in markdown,
            f"{label} unique total is not rendered in Markdown.",
        )
        for cohort in study["cohorts"]:
            require(
                f"{cohort['n']:,}" in visible_text(study_markup),
                f"{label} cohort count is missing from HTML: {cohort['name']}",
            )
            require(
                str(cohort["n"]) in markdown or f"{cohort['n']:,}" in markdown,
                f"{label} cohort count is missing from Markdown: {cohort['name']}",
            )
    else:
        require("Counting note" in snapshot_markup, f"{label} counting note is missing.")
        require("### Counting note" in markdown, f"{label} Markdown counting note is missing.")
        require(
            "Unique total" not in study_markup and "Cohort hierarchy" not in study_markup,
            f"{label} must not render a clinical cohort total or hierarchy.",
        )
        for metric in study["scale_metrics"]:
            require(
                metric["label"] in page_text and metric["value"] in page_text,
                f"{label} evidence scale metric is missing from HTML.",
            )
            require(
                metric["label"] in markdown and metric["value"] in markdown,
                f"{label} evidence scale metric is missing from Markdown.",
            )
    for value in string_leaves(content):
        require(
            normalized_source_text(value) in page_text,
            f"{label} content lost from HTML: {value!r}",
        )
        require(value in markdown, f"{label} content lost from Markdown: {value!r}")
    for key, value in (content.get("model_profile") or {}).items():
        if key in {"final_predictors", "interpretability"}:
            continue
        rendered_label = v2_label(key)
        rendered_value = v2_value(value)
        require(
            rendered_label in page_text
            and normalized_source_text(rendered_value) in page_text,
            f"{label} model profile lost from HTML: {key}",
        )
        require(
            f"- {rendered_label}: {rendered_value}" in markdown,
            f"{label} model profile lost from Markdown: {key}",
        )

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


def validate_aihflevel_v2_regression(content, publication, page):
    label = "AIHFLevel Paper GEO 2.0 Gold Standard"
    require(content.get("version") == 2, f"{label} must use version 2.")
    require(norm_doi(content.get("doi")) == AIHFLEVEL_DOI, f"{label} DOI changed.")
    require(
        norm_doi(publication.get("doi")) == AIHFLEVEL_DOI,
        f"{label} does not match its master record.",
    )

    study = content["study_profile"]
    require(
        study.get("profile_type") == "clinical_cohort",
        f"{label} profile type changed.",
    )
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
    require(len(content["qa"]) == 8, f"{label} Q&A count changed.")
    require(
        element_texts(page, "h2")[1] == "Evidence Snapshot",
        f"{label} evidence snapshot heading changed.",
    )


def validate_apvs_v2_regression(content, publication, page):
    label = "APVS Paper GEO 2.0 Gold Standard"
    require(content.get("version") == 2, f"{label} must use version 2.")
    require(norm_doi(content.get("doi")) == APVS_DOI, f"{label} DOI changed.")
    require(
        norm_doi(publication.get("doi")) == APVS_DOI,
        f"{label} does not match its master record.",
    )
    require(
        content["study_profile"].get("profile_type") == "multicohort_omics",
        f"{label} profile type changed.",
    )

    model = content["model_profile"]
    require(
        {
            "candidate_dcpgs": model.get("candidate_dcpgs"),
            "algorithm_count": model.get("algorithm_count"),
            "signature_size": model.get("signature_size"),
        }
        == {
            "candidate_dcpgs": 96,
            "algorithm_count": 9,
            "signature_size": 14,
        },
        f"{label} model facts changed.",
    )

    findings = {item["id"]: item for item in content["key_findings"]}
    require(
        list(findings) == [f"KF{number}" for number in range(1, 8)],
        f"{label} finding IDs changed.",
    )
    expected_external_auc = [
        ("GSE59867 STEMI vs CCS AUC", "0.985"),
        ("GSE62646 STEMI vs CCS AUC", "0.997"),
        ("GSE28829 advanced vs early plaque AUC", "0.952"),
        ("GSE41571 ruptured vs stable plaque AUC", "0.972"),
        ("GSE48060 STEMI vs healthy AUC", "0.871"),
        ("GSE60993 STEMI vs healthy AUC", "0.916"),
        ("GSE141512 STEMI vs healthy AUC", "1.000"),
    ]
    require(
        [
            (item["label"], item["value"])
            for item in findings["KF2"]["evidence"]
        ]
        == expected_external_auc,
        f"{label} external AUC evidence changed.",
    )
    require(
        ("MACE association", "HR 3.819; p<0.01")
        in [
            (item["label"], item["value"])
            for item in findings["KF3"]["evidence"]
        ],
        f"{label} MACE hazard ratio changed.",
    )
    require(
        [
            (item["label"], item["value"])
            for item in findings["KF4"]["evidence"]
            if item["label"] in {"GSE159677 cells", "GSE184073 cells"}
        ]
        == [("GSE159677 cells", "43,964"), ("GSE184073 cells", "2,237")],
        f"{label} single-cell counts changed.",
    )
    require(
        "Final predictor set" not in element_texts(page, "h3")
        and "Interpretability" not in element_texts(page, "h3"),
        f"{label} renders empty optional model sections.",
    )


def validate_smc_fate_v2_regression(content, publication, page):
    label = "SMC fate Paper GEO 2.0 Gold Standard"
    require(content.get("version") == 2, f"{label} must use version 2.")
    require(norm_doi(content.get("doi")) == SMC_FATE_DOI, f"{label} DOI changed.")
    require(
        norm_doi(publication.get("doi")) == SMC_FATE_DOI,
        f"{label} does not match its master record.",
    )
    require(publication.get("slug") == "smc-fate", f"{label} slug changed.")
    require(
        single_html_url(
            page,
            r'<link rel="canonical" href="([^"]*)">',
            f"{label} canonical URL",
        )
        == f"{CANONICAL_SITE_URL}/papers/smc-fate.html",
        f"{label} canonical URL changed.",
    )

    study = content["study_profile"]
    require(
        study.get("profile_type") == "multicohort_omics",
        f"{label} profile type changed.",
    )
    require("unique_total_n" not in study, f"{label} must not derive a unique total n.")
    require("model_profile" not in content, f"{label} must not invent a model profile.")
    expected_scale = {
        "single-cell donors": "4 cardiac transplant recipients with diseased right-coronary-artery segments",
        "single cells after quality control": "11,756",
        "major plaque cell populations": "8",
        "SMCs analyzed in depth": "5,419",
        "SMC transcriptional clusters": "9",
        "SMC pseudotime states": "5",
        "SMC cell-fate leader genes": "1,072",
        "Mfuzz temporal gene modules": "8",
        "bulk transcriptomic scale reported in Abstract": "1,070 samples across six bulk cohorts",
        "discovery cohort": "GSE20680; 195 blood-expression samples stratified by coronary stenosis severity",
        "SCFDS molecular subtypes": "3",
        "external NTP cohorts": "5",
    }
    require(
        {item["label"]: item["value"] for item in study["scale_metrics"]}
        == expected_scale,
        f"{label} evidence scale changed.",
    )
    require(
        study["counting_note"]
        == "The article reports 1,070 bulk transcriptomic samples across six bulk cohorts in the Abstract, while the Methods states that 1,074 samples from seven independent public cohorts were enrolled and separately describes the four-donor single-cell dataset. Participants, longitudinal samples, bulk transcriptomic samples and single cells represent different counting units and are therefore preserved by modality rather than combined into a derived unique-participant total. The article also contains minor inconsistencies in cohort enumeration, so dataset-level provenance is reported explicitly.",
        f"{label} counting note changed.",
    )

    findings = {item["id"]: item for item in content["key_findings"]}
    expected_evidence = {
        "KF1": [
            ("single-cell donors", "4"),
            ("post-QC plaque cells", "11,756"),
            ("major plaque cell populations", "8"),
            ("SMCs analyzed", "5,419"),
            ("SMC clusters", "9"),
        ],
        "KF2": [
            ("pseudotime states", "5"),
            ("trajectory structure", "five cellular states separated at two key time points"),
            ("early-state enrichment", "SMC4 and SMC6"),
            ("intermediate high-plasticity enrichment", "SMC2, SMC5 and SMC7"),
            ("terminal-state enrichment", "SMC1, SMC8 and SMC9"),
            ("phenotypic trend", "contractile-like features declined; fibroblast-like markers increased through the middle-to-late trajectory before decreasing at the terminal end"),
        ],
        "KF3": [
            ("SMC cell-fate leader genes", "1,072"),
            ("Mfuzz temporal modules", "8"),
            ("SCFDS modules", "Cluster 2 and Cluster 6, representing progressively upregulated and downregulated programs"),
            ("upregulated SCFDS programs", "extracellular matrix, inflammatory response and TGF-beta-related processes"),
            ("downregulated SCFDS programs", "vasculature development and AGE-RAGE-related processes"),
        ],
        "KF4": [
            ("optimal subtype number", "3"),
            ("C1", "DNA-damage repair type"),
            ("C2", "immune-activated type"),
            ("C3", "stromal-rich type"),
            ("coronary stenosis association", "C2 showed greater stenosis severity and C3 lower severity; p<0.05 in the discovery analysis"),
        ],
        "KF5": [
            ("template construction", "top 300 subtype-specific upregulated genes per subtype"),
            ("external cohorts", "5"),
            ("datasets shown in Fig. 6", "GSE20681, GSE21545, GSE59867, GSE62646 and GSE90074"),
            ("validation type", "retrospective expression-template reproducibility across distinct platforms"),
        ],
        "KF6": [
            ("C1 programs", "base-excision repair, DNA replication, nucleotide-excision repair and oxidative phosphorylation"),
            ("C2 programs", "stronger immune and inflammatory activation with a more complex inflammatory lesion environment"),
            ("C3 programs", "stromal/ECM metabolism, greater fibrous content and a relatively immune-suppressed microenvironment"),
        ],
    }
    expected_locators = {
        "KF1": "Results: The landscapes of human atherosclerotic plaques revealed by scRNA-seq analysis, Fig. 2A; Results: SMC lineages' phenotypic and functional heterogeneity, Fig. 3A-E",
        "KF2": "Results: Trajectory reconstruction revealed SMC cell fate decisions, Fig. 4A-C",
        "KF3": "Results: Trajectory reconstruction revealed SMC cell fate decisions, Fig. 4D-H; Additional file 3: Table S1; Additional file 4: Table S2",
        "KF4": "Results: The molecular subtyping of atherosclerosis based on cell fate decision signature, Fig. 5A-I; coronary stenosis comparison in Fig. 5E",
        "KF5": "Results: Performance of SCFDS subtypes verified by nearest template prediction, Fig. 6B-C",
        "KF6": "Results: The molecular subtyping of atherosclerosis based on cell fate decision signature, Fig. 5G-I; Results: Assessment of multi-dimensional potential biological implications, Fig. 7A-G",
    }
    require(
        list(findings) == [f"KF{number}" for number in range(1, 7)],
        f"{label} finding IDs changed.",
    )
    for finding_id, expected in expected_evidence.items():
        require(
            [
                (item["label"], item["value"])
                for item in findings[finding_id]["evidence"]
            ]
            == expected,
            f"{label} {finding_id} evidence changed.",
        )
        require(
            findings[finding_id]["source_locator"] == expected_locators[finding_id],
            f"{label} {finding_id} source locator changed.",
        )

    provenance = content["provenance"]
    require(provenance.get("pmcid") == "PMC9724432", f"{label} PMCID changed.")
    require(
        provenance.get("external_cohorts")
        == "GSE20681; GSE21545; GSE59867; GSE62646; GSE90074",
        f"{label} external cohort provenance changed.",
    )
    require(
        provenance.get("bulk_discovery")
        == "GSE20680; 195 samples stratified by coronary stenosis. The article Methods describes these as PBMC samples, whereas the GEO accession describes whole-blood cell expression profiling.",
        f"{label} discovery sample-type discrepancy changed.",
    )
    require(
        provenance.get("source_note_counting")
        == "The Abstract reports 1,070 bulk samples across six bulk cohorts, whereas the Methods states 1,074 samples across seven independent public cohorts while separately describing the four-donor single-cell dataset. Counts are preserved by modality and are not collapsed into a derived unique-participant total.",
        f"{label} cohort-count discrepancy changed.",
    )
    require(
        provenance.get("source_note_sample_type")
        == "For GSE20680, the article Methods uses the term PBMC samples, whereas the NCBI GEO record describes whole-blood cell gene-expression profiling. This evidence page preserves the discrepancy rather than silently harmonizing the sample type.",
        f"{label} GSE20680 sample-type provenance changed.",
    )
    require(
        provenance.get("source_note_accession")
        == "The Results narrative contains GSE26081 once, whereas Fig. 6 identifies GSE20681. NCBI GEO confirms GSE20681 as the PREDICT coronary artery disease dataset; GSE26081 is an unrelated breast-cancer ER-alpha dataset. This evidence page therefore uses GSE20681 while retaining the discrepancy in provenance.",
        f"{label} external accession discrepancy changed.",
    )
    non_accession_note_text = string_leaves(
        {
            **{key: value for key, value in content.items() if key != "provenance"},
            "provenance": {
                key: value
                for key, value in provenance.items()
                if key != "source_note_accession"
            },
        }
    )
    require(
        not any("GSE26081" in value for value in non_accession_note_text),
        f"{label} uses GSE26081 outside the documented accession discrepancy.",
    )
    require(
        provenance.get("supplementary_material")
        == "Additional file 1: Figure S1, single-cell RNA-seq quality control; Additional file 2: Figure S2, plaque cell-type mapping; Additional file 3: Table S1, SMC cell-fate leader genes; Additional file 4: Table S2, Mfuzz gene modules",
        f"{label} supplementary-material provenance changed.",
    )

    require(len(content["qa"]) == 8, f"{label} Q&A count changed.")
    valid_finding_ids = set(findings)
    require(
        all(
            set(item.get("evidence_refs", [])).issubset(valid_finding_ids)
            for item in content["qa"]
        ),
        f"{label} Q&A evidence references are invalid.",
    )
    stenosis_answer = next(
        item["answer"]
        for item in content["qa"]
        if item["question"]
        == "Which SCFDS subtype was associated with more severe coronary stenosis?"
    )
    require(
        stenosis_answer
        == "C2, the immune-activated subtype, showed greater coronary stenosis severity in the discovery analysis, whereas C3 showed lower severity. This was an association and does not establish that the subtype causes the difference in stenosis.",
        f"{label} stenosis association scope changed.",
    )
    prospective_answer = next(
        item["answer"]
        for item in content["qa"]
        if item["question"]
        == "Has SCFDS been prospectively validated for clinical decision-making or treatment selection?"
    )
    require(
        prospective_answer
        == "No. The study was retrospective and primarily computational. The authors explicitly called for additional experimental validation and prospective multicenter studies before clinical relevance or treatment-guided utility can be established.",
        f"{label} prospective-validation scope changed.",
    )

    require(
        [norm_doi(item["doi"]) for item in content["related_papers"]]
        == [
            "10.1016/j.isci.2023.107587",
            "10.1172/jci194175",
            "10.1093/eurheartj/ehaf523",
        ],
        f"{label} related research changed.",
    )
    page_text = visible_text(page)
    for item in content["related_papers"]:
        require(
            item["relationship"] in page_text,
            f"{label} related relationship missing from HTML.",
        )
    required_scope_boundaries = [
        "That pseudotime directly observes individual human SMCs transforming longitudinally within the same lesion.",
        "That C1, C2 and C3 are prospectively validated clinical diagnostic or prognostic classes.",
        "That C2 causes coronary stenosis progression or that C3 causally protects against plaque progression or clinical events.",
        "That pathway enrichment or inferred cell-composition differences prove the underlying mechanisms.",
        "That retrospective NTP reproducibility is equivalent to prospective multicenter clinical validation.",
        "That SCFDS-guided treatment improves myocardial infarction, mortality or other clinical outcomes.",
        "That the therapeutic hypotheses discussed by the authors constitute validated treatment recommendations.",
    ]
    require(
        all(
            boundary in content["evidence_scope"]["does_not_establish"]
            and boundary in page_text
            for boundary in required_scope_boundaries
        ),
        f"{label} scientific scope boundaries changed.",
    )


def validate_olink_dcm_v2_regression(content, publication, page):
    label = "Olink DCM Paper GEO 2.0 Gold Standard"
    require(content.get("version") == 2, f"{label} must use version 2.")
    require(norm_doi(content.get("doi")) == OLINK_DCM_DOI, f"{label} DOI changed.")
    require(norm_doi(publication.get("doi")) == OLINK_DCM_DOI, f"{label} master DOI changed.")
    require(publication.get("slug") == "olink-dcm", f"{label} slug changed.")
    canonical = f"{CANONICAL_SITE_URL}/papers/olink-dcm.html"
    require(
        single_html_url(page, r'<link rel="canonical" href="([^"]*)">', f"{label} canonical URL")
        == canonical,
        f"{label} canonical URL changed.",
    )

    study = content["study_profile"]
    require(study.get("profile_type") == "multicohort_omics", f"{label} profile changed.")
    require("unique_total_n" not in study, f"{label} must not derive an external total n.")
    require("model_profile" not in content, f"{label} must not invent a model.")
    expected_scale = {
        "local participants": "103: 50 DCM-HF and 53 healthy controls",
        "Olink discovery cohort": "38 participants: 20 DCM-HF and 18 healthy controls",
        "Olink panel": "92 cardiovascular-related proteins",
        "proteins differing at p<0.05": "33",
        "focused differentially abundant proteins": "13; all higher in DCM-HF, P<0.001 in Results and significant after FDR correction",
        "prioritized candidate markers": "5: SPP1, IGFBP7, F11R, CHI3L1 and PLAUR",
        "independent ELISA cohort": "65 participants: 30 DCM-HF and 35 healthy controls",
        "external cardiac transcriptomic datasets": "3: GSE116250, GSE141910 and GSE165303",
        "combined five-gene AUCs": "0.959, 0.773 and 0.803, respectively",
        "external-evaluation modality": "human cardiac gene expression; not independent plasma proteomics",
    }
    require(
        {item["label"]: item["value"] for item in study["scale_metrics"]}
        == expected_scale,
        f"{label} evidence scale or cohort separation changed.",
    )
    require(
        "not aggregated into a derived external total n" in study["counting_note"]
        and "38 participants in the Olink discovery cohort" in study["counting_note"]
        and "65 participants in the ELISA validation cohort" in study["counting_note"],
        f"{label} counting distinction changed.",
    )

    findings = {item["id"]: item for item in content["key_findings"]}
    require(
        list(findings) == [f"KF{number}" for number in range(1, 7)],
        f"{label} finding IDs changed.",
    )
    require(
        all(str(item["source_locator"]).strip() for item in findings.values()),
        f"{label} source locator missing.",
    )
    evidence = {
        finding_id: {item["label"]: item["value"] for item in finding["evidence"]}
        for finding_id, finding in findings.items()
    }
    require(
        evidence["KF1"] == {
            "discovery cohort": "20 DCM-HF and 18 healthy controls",
            "proteins profiled": "92",
            "overall abundance direction": "75 higher and 17 lower in DCM-HF",
            "proteins at p<0.05": "33",
            "focused DEP set": "13 proteins; all higher in DCM-HF",
            "focused DEP significance": "P<0.001 in Results; remained significant after FDR correction",
            "Fig. 1D display threshold": "absolute logFC >0.5 and p<0.05",
        },
        f"{label} Olink discovery evidence changed.",
    )
    require(
        evidence["KF2"] == {
            "prioritized markers": "SPP1, IGFBP7, F11R, CHI3L1 and PLAUR",
            "Methods selection description": "DEPs with at least 1.3-fold change and pivotal roles in KEGG pathways",
            "Results selection description": "selected based on the highest fold changes and bioinformatics analysis",
        },
        f"{label} candidate-selection provenance changed.",
    )
    require(
        evidence["KF3"] == {
            "ELISA cohort": "65 participants",
            "DCM-HF": "30",
            "healthy controls": "35",
            "markers": "SPP1, IGFBP7, F11R, CHI3L1 and PLAUR",
            "direction": "all five higher in DCM-HF",
            "reported group-comparison significance": "P<0.001",
        },
        f"{label} independent ELISA evidence changed.",
    )
    require(
        evidence["KF4"] == {
            "GSE116250 combined AUC": "0.959; 95% CI 0.905-0.996",
            "GSE141910 combined AUC": "0.773; 95% CI 0.719-0.820",
            "GSE165303 combined AUC": "0.803; 95% CI 0.706-0.888",
            "external modality": "human cardiac transcriptomics",
            "interpretation boundary": "diagnostic discrimination in existing datasets, not prospective incident-DCM prediction",
        },
        f"{label} external transcriptomic evidence changed.",
    )
    require(len(content["qa"]) == 8, f"{label} Q&A count changed.")
    require(
        all(set(item.get("evidence_refs", [])).issubset(findings) for item in content["qa"]),
        f"{label} Q&A finding references changed.",
    )

    provenance = content["provenance"]
    require(provenance.get("pmcid") == "PMC11385702", f"{label} PMCID changed.")
    require(
        provenance.get("pubmed_url") == "https://pubmed.ncbi.nlm.nih.gov/39129220/",
        f"{label} PMID changed.",
    )
    require(
        provenance.get("version_of_record")
        == "Journal of Proteome Research, Volume 23, Issue 9, pages 4139-4150; published online 12 August 2024 and in issue 6 September 2024",
        f"{label} version of record changed.",
    )
    require("CC BY-NC-ND 4.0" in provenance.get("license", ""), f"{label} license changed.")
    require("2022-KT-105" in provenance.get("local_ethics", ""), f"{label} ethics changed.")
    require(
        all(
            item in provenance.get("supporting_material", "")
            for item in ("Table S1", "Tables S2-S4", "Table S5")
        )
        and all(f"Figure S{number}" in provenance.get("supporting_material", "") for number in range(1, 4)),
        f"{label} supporting-information provenance changed.",
    )
    require(
        "No dedicated article-specific code repository" in provenance.get("code_repository", ""),
        f"{label} code repository provenance changed.",
    )
    external_note = provenance.get("source_note_external_counts", "")
    require(
        all(
            value in external_note
            for value in (
                "GSE116250 as 15 controls and 38 DCM",
                "GSE141910 as 162 controls and 162 DCM",
                "GSE165303 as 48 controls and 74 DCM",
                "Native or independently documented dataset composition differs",
                "exact filtering logic used to obtain the article-reported analyzed counts is not fully specified",
                "does not aggregate an external total n",
            )
        ),
        f"{label} external GEO count discrepancy changed.",
    )
    registration_note = provenance.get("source_note_registration", "")
    require(
        "ChiCTR2100051469" in registration_note
        and "magnetocardiography/myocardial-ischemia" in registration_note
        and "linkage is treated as unresolved" in registration_note,
        f"{label} unresolved registration note changed.",
    )
    mouse_note = provenance.get("source_note_mouse_models", "")
    require(
        "Methods and Results do not describe an original animal experiment" in mouse_note
        and "derives from cited prior studies" in mouse_note,
        f"{label} mouse-model provenance note changed.",
    )
    require(
        [norm_doi(item["doi"]) for item in content["related_papers"]]
        == [
            "10.2147/jir.s495784",
            "10.1111/jcmm.17789",
            "10.1007/s10238-026-02130-6",
        ],
        f"{label} related research changed.",
    )
    require(
        not any(item.get("@type") == "ClinicalTrial" for item in json_ld_objects(page)),
        f"{label} must not assert a verified ClinicalTrial.",
    )
    page_text = visible_text(page)
    require(
        "the corresponding five-gene expression panel" in page_text
        and "not independent plasma proteomics" in page_text
        and "not prospective incident-DCM prediction" in page_text,
        f"{label} protein/gene or diagnostic scope changed.",
    )
    require(
        all(item["relationship"] in page_text for item in content["related_papers"]),
        f"{label} related-paper relationships missing from HTML.",
    )


def validate_v2_inventory(v2_dois):
    require(v2_dois, "At least one Paper GEO 2.0 page is required.")
    require(
        AIHFLEVEL_DOI in v2_dois,
        "AIHFLevel must remain a Paper GEO 2.0 Gold Standard page.",
    )
    require(
        APVS_DOI in v2_dois,
        "APVS must remain a Paper GEO 2.0 Gold Standard page.",
    )
    require(
        SMC_FATE_DOI in v2_dois,
        "SMC fate must remain a Paper GEO 2.0 Gold Standard page.",
    )
    require(
        OLINK_DCM_DOI in v2_dois,
        "Olink DCM must remain a Paper GEO 2.0 Gold Standard page.",
    )
    require(
        len(v2_dois) == len(set(v2_dois)),
        "Paper GEO 2.0 DOI values must be unique.",
    )


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
                content_doi = norm_doi(content.get("doi"))
                v2_dois.append(content_doi)
                validate_v2_rendered_page(
                    content,
                    item,
                    page,
                    markdown,
                    schema,
                    public_by_doi,
                    config,
                )
                if content_doi == AIHFLEVEL_DOI:
                    validate_aihflevel_v2_regression(content, item, page)
                elif content_doi == APVS_DOI:
                    validate_apvs_v2_regression(content, item, page)
                elif content_doi == SMC_FATE_DOI:
                    validate_smc_fate_v2_regression(content, item, page)
                elif content_doi == OLINK_DCM_DOI:
                    validate_olink_dcm_v2_regression(content, item, page)
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
    validate_v2_inventory(v2_dois)

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
    homepage_description = single_meta_content(
        index_html, "description", "Homepage meta description"
    )
    require(
        single_property_meta_content(index_html, "og:title", "Homepage Open Graph title")
        == expected_homepage_title,
        "Homepage Open Graph title must match the page title.",
    )
    require(
        single_property_meta_content(
            index_html, "og:description", "Homepage Open Graph description"
        )
        == homepage_description,
        "Homepage Open Graph description must match the meta description.",
    )
    require(
        single_property_meta_content(index_html, "og:type", "Homepage Open Graph type")
        == "website",
        "Homepage Open Graph type must be website.",
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
    website_schema = json_ld_object(index_html, "WebSite", "Homepage")
    require(
        website_schema
        == {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{config['site_url']}/#website",
            "url": homepage_url,
            "name": f"{config['researcher_name']} Academic Hub",
            "creator": {"@id": config["person_id"]},
        },
        "Homepage WebSite schema does not match the stable site identity.",
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
    expected_publications_title = (
        f"All Publications | {config['researcher_name']} "
        f"({config['researcher_name_zh']})"
    )
    publications_description = single_meta_content(
        publications_html, "description", "Publications meta description"
    )
    require(
        single_property_meta_content(
            publications_html, "og:title", "Publications Open Graph title"
        )
        == expected_publications_title,
        "Publications Open Graph title must match the page title.",
    )
    require(
        single_property_meta_content(
            publications_html,
            "og:description",
            "Publications Open Graph description",
        )
        == publications_description,
        "Publications Open Graph description must match the meta description.",
    )
    require(
        single_property_meta_content(
            publications_html, "og:type", "Publications Open Graph type"
        )
        == "website",
        "Publications Open Graph type must be website.",
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
    require(
        llms.startswith(
            f"# {config['researcher_name']} Academic Hub\n\n"
            "> An author-controlled academic evidence hub for verified publications and research pages.\n\n"
        ),
        "llms.txt must contain the approved description immediately after its H1.",
    )
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
