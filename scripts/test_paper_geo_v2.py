import copy
import json

from build_publications import (
    flatten_concepts,
    load_deep_content,
    render_paper_html,
    render_paper_markdown,
    resolve_related_papers,
    validate_deep_v2_content,
)
from site_common import (
    PAPERS_DIR,
    controller_token,
    index_master,
    load_deep_geo,
    load_featured,
    load_site_config,
)
from sync_common import is_withdrawn, load_master, norm_doi
from validate_site import (
    APVS_DOI,
    AIHFLEVEL_DOI,
    CLOCKPROCRC_DOI,
    CIRCADIAN_REVIEW_DOI,
    KIF13B_MERTK_DOI,
    KIF13B_VSMC_DOI,
    OLINK_DCM_DOI,
    SARS_COV2_HF_DOI,
    SMC_FATE_DOI,
    ValidationError,
    json_ld_objects,
    paper_json_ld_object,
    validate_apvs_v2_regression,
    validate_aihflevel_v2_regression,
    validate_clockprocrc_v2_regression,
    validate_circadian_review_v2_regression,
    validate_kif13b_mertk_v2_regression,
    validate_kif13b_vsmc_v2_regression,
    validate_olink_dcm_v2_regression,
    validate_sars_cov2_hf_v2_regression,
    validate_smc_fate_v2_regression,
    validate_v2_inventory,
    validate_v2_rendered_page,
    element_texts,
    meta_contents,
    visible_text,
)


SYNTHETIC_DOI = "10.9999/paper-geo-v2-multicohort-fixture"
PRIORITY_STATUS = (
    ("10.1038/s41467-024-50415-9", "v2"),
    ("10.1038/s41698-026-01699-1", "v2"),
    ("10.1016/j.isci.2023.107587", "v2"),
    ("10.1186/s12967-022-03795-9", "v2"),
    ("10.1002/ehf2.14003", "v2"),
    ("10.1093/eurheartj/ehaf523", "v2"),
    ("10.1002/mdr2.70052", "v2"),
    ("10.1200/po.24.00089", "v1"),
    ("10.1172/jci194175", "v2"),
    ("10.1021/acs.jproteome.4c00522", "v2"),
    ("10.1016/j.ejphar.2023.175569", "v1"),
    ("10.1002/mdr2.70004", "pending"),
    ("10.1111/jcmm.17789", "pending"),
    ("10.1136/jitc-2024-010127", "v1"),
    ("10.3389/fonc.2021.659217", "pending"),
    ("10.18632/aging.205564", "pending"),
    ("10.2147/ijn.s522157", "pending"),
    ("10.1016/j.joim.2025.06.003", "pending"),
    ("10.1111/jcmm.70258", "pending"),
    ("10.1186/s12915-025-02400-x", "pending"),
    ("10.3389/fcvm.2025.1724572", "pending"),
    ("10.71321/fy14v342", "pending"),
    ("10.1111/jcmm.70725", "pending"),
    ("10.1038/s41598-024-65236-5", "v1"),
    ("10.3389/fpubh.2025.1521372", "pending"),
    ("10.1002/ggn2.202500053", "pending"),
    ("10.1016/j.curpro.2025.100054", "pending"),
    ("10.1007/s11426-026-3629-x", "pending"),
)


def expect_value_error(callback, expected):
    try:
        callback()
    except ValueError as exc:
        assert expected.casefold() in str(exc).casefold(), str(exc)
    else:
        raise AssertionError(f"Expected ValueError containing {expected!r}.")


def synthetic_multicohort_fixture():
    publication = {
        "title": "Synthetic multicohort omics validation fixture",
        "journal": "Synthetic Test Journal",
        "year": 2099,
        "type": "Article",
        "doi": SYNTHETIC_DOI,
        "slug": "synthetic-multicohort-v2",
        "authors": ["Ge Zhang", "Synthetic Collaborator"],
    }
    content = {
        "version": 2,
        "doi": SYNTHETIC_DOI,
        "display_title": "Synthetic multicohort omics framework fixture",
        "summary": "Synthetic content used only to validate multicohort rendering.",
        "research_question": "Can the V2 framework represent heterogeneous omics scales without deriving a participant total?",
        "author_summary": "This synthetic fixture exercises multicohort omics validation and rendering without making a scientific claim.",
        "study_profile": {
            "profile_type": "multicohort_omics",
            "study_design": "Synthetic multicohort integration fixture",
            "evidence_type": "Synthetic test evidence",
            "population": "Synthetic public omics datasets",
            "primary_endpoint": "Framework validation",
            "secondary_endpoint": "HTML and Markdown parity",
            "data_modalities": [
                "bulk transcriptomics",
                "single-cell transcriptomics",
            ],
            "external_validation": False,
            "scale_metrics": [
                {"label": "bulk transcriptomic cohorts", "value": "22"},
                {"label": "single-cell cohorts", "value": "2"},
            ],
            "counting_note": "Datasets, samples, specimens, and cells use different counting conventions; no unique participant total is derived.",
        },
        "key_findings": [
            {
                "id": "KF1",
                "claim": "The synthetic profile preserves modality-specific scale metrics.",
                "context": "This is a test-only claim about renderer behavior.",
                "evidence": [
                    {"label": "bulk transcriptomic cohorts", "value": "22"},
                    {"label": "single-cell cohorts", "value": "2"},
                ],
                "source_locator": "Synthetic fixture: scale metrics",
            }
        ],
        "what_this_adds": [
            "A synthetic regression fixture for multicohort omics profiles."
        ],
        "evidence_scope": {
            "supports": ["Validation of profile-specific rendering behavior."],
            "does_not_establish": ["Any biomedical or clinical conclusion."],
        },
        "qa": [
            {
                "question": "Does the fixture derive a participant total?",
                "answer": "No; it preserves modality-specific counting conventions.",
                "evidence_refs": ["KF1"],
            },
            {
                "question": "Does it include bulk transcriptomic scale?",
                "answer": "Yes; the synthetic scale is twenty-two cohorts.",
                "evidence_refs": ["KF1"],
            },
            {
                "question": "Does it include single-cell scale?",
                "answer": "Yes; the synthetic scale is two cohorts.",
                "evidence_refs": ["KF1"],
            },
            {
                "question": "Is this scientific evidence?",
                "answer": "No; it is explicitly a software validation fixture.",
            },
        ],
        "concepts": {
            "methods": ["multicohort integration"],
            "modalities": ["bulk transcriptomics", "single-cell transcriptomics"],
        },
        "limitations": ["All content in this fixture is synthetic."],
        "related_papers": [
            {
                "doi": AIHFLEVEL_DOI,
                "relationship": "Exact-DOI resolution regression target.",
            }
        ],
        "provenance": {
            "publisher_url": "https://example.org/synthetic-paper",
            "code_url": "https://example.org/synthetic-code",
            "evidence_basis": "Synthetic test-only fixture",
        },
        "evidence_page_notice": "Synthetic author-controlled evidence-page fixture. It exists only for framework testing.",
    }
    return publication, content


def rendered_v2(publication, content, config, public_by_doi):
    validate_deep_v2_content(content, f"{publication['slug']} test fixture")
    page = render_paper_html(
        publication,
        config=config,
        deep_content=content,
        public_by_doi=public_by_doi,
    )
    markdown = render_paper_markdown(
        publication,
        config=config,
        deep_content=content,
        public_by_doi=public_by_doi,
    )
    schema = paper_json_ld_object(page, f"{publication['slug']} test page")
    validate_v2_rendered_page(
        content,
        publication,
        page,
        markdown,
        schema,
        public_by_doi,
        config,
    )
    return page, markdown, schema


def run_tests():
    config = load_site_config()
    master = load_master()
    public = [item for item in master if not is_withdrawn(item)]
    master_by_token = index_master(master)
    public_by_doi = {
        norm_doi(item.get("doi")): item
        for item in public
        if norm_doi(item.get("doi"))
    }

    deep_entries = load_deep_geo()
    featured_entries = load_featured()
    expected_dois = [doi for doi, _ in PRIORITY_STATUS]
    assert [norm_doi(entry["doi"]) for entry in featured_entries] == expected_dois
    assert [norm_doi(entry["doi"]) for entry in deep_entries] == expected_dois
    v1_count = 0
    v2_items = []
    pending_count = 0
    for entry, (expected_doi, expected_status) in zip(deep_entries, PRIORITY_STATUS):
        publication = master_by_token[controller_token(entry)]
        assert norm_doi(publication["doi"]) == expected_doi
        if expected_status == "pending":
            assert load_deep_content(publication, allow_missing=True) is None
            pending_count += 1
            continue
        content = load_deep_content(publication)
        assert f"v{content['version']}" == expected_status
        if content["version"] == 2:
            v2_items.append((publication, content))
            continue
        v1_count += 1
        assert content["version"] == 1
        assert render_paper_html(
            publication,
            config=config,
            deep_content=content,
            public_by_doi=public_by_doi,
        ) == (PAPERS_DIR / f"{publication['slug']}.html").read_text(encoding="utf-8")
        assert render_paper_markdown(
            publication,
            config=config,
            deep_content=content,
            public_by_doi=public_by_doi,
        ) == (PAPERS_DIR / f"{publication['slug']}.md").read_text(encoding="utf-8")

    assert (len(v2_items), v1_count, pending_count) == (9, 4, 15)
    assert len(v2_items) >= 1
    aihf_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == AIHFLEVEL_DOI
    ]
    assert len(aihf_items) == 1
    apvs_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == APVS_DOI
    ]
    assert len(apvs_items) == 1
    smc_fate_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == SMC_FATE_DOI
    ]
    assert len(smc_fate_items) == 1
    olink_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == OLINK_DCM_DOI
    ]
    assert len(olink_items) == 1
    clockprocrc_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == CLOCKPROCRC_DOI
    ]
    assert len(clockprocrc_items) == 1
    sars_cov2_hf_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == SARS_COV2_HF_DOI
    ]
    assert len(sars_cov2_hf_items) == 1
    kif13b_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == KIF13B_MERTK_DOI
    ]
    assert len(kif13b_items) == 1
    review_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == CIRCADIAN_REVIEW_DOI
    ]
    assert len(review_items) == 1
    jci_items = [
        item for item in v2_items if norm_doi(item[0].get("doi")) == KIF13B_VSMC_DOI
    ]
    assert len(jci_items) == 1
    assert norm_doi(deep_entries[9].get("doi")) == OLINK_DCM_DOI
    assert norm_doi(load_featured()[9].get("doi")) == OLINK_DCM_DOI
    expected_production_labels = {
        AIHFLEVEL_DOI: (
            "Study Design & Model Development",
            "External validation",
        ),
        APVS_DOI: (
            "Study Design & Model Development",
            "External dataset evaluation",
        ),
        SMC_FATE_DOI: (
            "Study Design & Analytical Framework",
            "External dataset evaluation",
        ),
        OLINK_DCM_DOI: (
            "Study Design & Analytical Framework",
            "External dataset evaluation",
        ),
        CLOCKPROCRC_DOI: (
            "Study Design & Analytical Framework",
            "External dataset evaluation",
        ),
        SARS_COV2_HF_DOI: (
            "Study Design & Analytical Framework",
            "External dataset evaluation",
        ),
        KIF13B_MERTK_DOI: (
            "Study Design & Analytical Framework",
            "External dataset evaluation",
        ),
        CIRCADIAN_REVIEW_DOI: (
            "Review Design & Evidence Synthesis",
            None,
        ),
        KIF13B_VSMC_DOI: (
            "Study Design & Analytical Framework",
            "External dataset evaluation",
        ),
    }
    assert {norm_doi(item[0].get("doi")) for item in v2_items} == set(
        expected_production_labels
    )

    for publication, content in v2_items:
        page, markdown, schema = rendered_v2(
            publication, content, config, public_by_doi
        )
        assert schema["description"] == content["author_summary"]
        assert schema["keywords"] == flatten_concepts(content)
        doi = norm_doi(publication.get("doi"))
        expected_heading, expected_external_label = expected_production_labels[doi]
        html_heading = expected_heading.replace("&", "&amp;")
        assert f'data-v2-section="study-design"><h2>{html_heading}</h2>' in page
        assert f"## {expected_heading}" in markdown
        if expected_external_label is None:
            assert "<h3>Review profile</h3>" in page
            assert "<h3>Evidence domains</h3>" in page
            assert "### Review profile" in markdown
            assert "- Evidence domains:" in markdown
        else:
            assert f"<dt>{expected_external_label}</dt><dd>Yes</dd>" in page
            assert f"- {expected_external_label}: Yes" in markdown
        unexpected_heading = (
            "Study Design & Analytical Framework"
            if "Model Development" in expected_heading
            else "Study Design & Model Development"
        )
        unexpected_external_label = (
            "External dataset evaluation"
            if expected_external_label == "External validation"
            else "External validation"
        )
        assert f"## {unexpected_heading}" not in markdown
        assert f"<dt>{unexpected_external_label}</dt>" not in page
        assert f"- {unexpected_external_label}:" not in markdown
        if norm_doi(publication.get("doi")) == AIHFLEVEL_DOI:
            validate_aihflevel_v2_regression(content, publication, page)
            assert page == (PAPERS_DIR / "aihflevel.html").read_text(encoding="utf-8")
            assert markdown == (PAPERS_DIR / "aihflevel.md").read_text(encoding="utf-8")
        elif norm_doi(publication.get("doi")) == APVS_DOI:
            validate_apvs_v2_regression(content, publication, page)
            assert "Final predictor set" not in page
            assert "Interpretability" not in page
            assert "### Final predictor set" not in markdown
            assert "### Interpretability" not in markdown
            assert page == (PAPERS_DIR / "apvs.html").read_text(encoding="utf-8")
            assert markdown == (PAPERS_DIR / "apvs.md").read_text(encoding="utf-8")
        elif norm_doi(publication.get("doi")) == SMC_FATE_DOI:
            validate_smc_fate_v2_regression(content, publication, page)
            assert page == (PAPERS_DIR / "smc-fate.html").read_text(encoding="utf-8")
            assert markdown == (PAPERS_DIR / "smc-fate.md").read_text(
                encoding="utf-8"
            )
        elif norm_doi(publication.get("doi")) == OLINK_DCM_DOI:
            validate_olink_dcm_v2_regression(content, publication, page)
            assert publication["slug"] == "olink-dcm"
            assert page == (PAPERS_DIR / "olink-dcm.html").read_text(encoding="utf-8")
            assert markdown == (PAPERS_DIR / "olink-dcm.md").read_text(encoding="utf-8")
            assert not any(item.get("@type") == "ClinicalTrial" for item in json_ld_objects(page))
            for scientific_guard in (
                "38 participants: 20 DCM-HF and 18 healthy controls",
                "65 participants: 30 DCM-HF and 35 healthy controls",
                "SPP1, IGFBP7, F11R, CHI3L1 and PLAUR",
                "0.959; 95% CI 0.905-0.996",
                "0.773; 95% CI 0.719-0.820",
                "0.803; 95% CI 0.706-0.888",
                "not independent plasma proteomics",
                "not prospective incident-DCM prediction",
                "linkage is treated as unresolved",
                "Methods and Results do not describe an original animal experiment",
            ):
                assert scientific_guard in page
                assert scientific_guard in markdown
        elif norm_doi(publication.get("doi")) == CLOCKPROCRC_DOI:
            validate_clockprocrc_v2_regression(content, publication, page)
            assert page == (
                PAPERS_DIR / "doi-10-1038-s41698-026-01699-1.html"
            ).read_text(encoding="utf-8")
            assert markdown == (
                PAPERS_DIR / "doi-10-1038-s41698-026-01699-1.md"
            ).read_text(encoding="utf-8")
            for finding in content["key_findings"]:
                assert finding["source_locator"] in page
                assert finding["source_locator"] in markdown
        elif norm_doi(publication.get("doi")) == SARS_COV2_HF_DOI:
            validate_sars_cov2_hf_v2_regression(content, publication, page)
            assert page == (
                PAPERS_DIR / "doi-10-1002-ehf2-14003.html"
            ).read_text(encoding="utf-8")
            assert markdown == (
                PAPERS_DIR / "doi-10-1002-ehf2-14003.md"
            ).read_text(encoding="utf-8")
            for finding in content["key_findings"]:
                assert finding["source_locator"] in page
                assert finding["source_locator"] in markdown
            for false_claim in (
                "The panel achieved 96% diagnostic accuracy.",
                "AUC 0.96 established clinical diagnosis.",
                "GSH treats COVID-19.",
                "The study enrolled a COVID-HF cohort.",
            ):
                inflated = copy.deepcopy(content)
                inflated["author_summary"] += " " + false_claim
                try:
                    validate_sars_cov2_hf_v2_regression(inflated, publication, page)
                except ValidationError as exc:
                    assert "unsupported positive scientific claim" in str(exc)
                else:
                    raise AssertionError(f"Unsupported claim was accepted: {false_claim}")
            false_accession = copy.deepcopy(content)
            false_accession["concepts"]["datasets"].append("GSE26687")
            try:
                validate_sars_cov2_hf_v2_regression(false_accession, publication, page)
            except ValidationError as exc:
                assert "Figure 1 typo" in str(exc)
            else:
                raise AssertionError("Figure 1 typo became a scientific dataset.")
        elif norm_doi(publication.get("doi")) == KIF13B_MERTK_DOI:
            validate_kif13b_mertk_v2_regression(content, publication, page)
            target = "doi-10-1093-eurheartj-ehaf523"
            assert page == (PAPERS_DIR / f"{target}.html").read_text(encoding="utf-8")
            assert markdown == (PAPERS_DIR / f"{target}.md").read_text(encoding="utf-8")
            for finding in content["key_findings"]:
                assert finding["source_locator"] in page
                assert finding["source_locator"] in markdown
            for text in (
                "one library per genotype", "CBL and CBLB are distinct genes",
                "20 weeks of Western diet", "12 weeks of high-fat diet",
                "does not unambiguously validate",
            ):
                assert text in page and text in markdown
            for false_claim in (
                "NX-1607 treats atherosclerosis patients.",
                "NX-1607 Phase I atherosclerosis trial.",
                "CBL and CBLB are the same gene.",
                "Five independent scRNA libraries per genotype.",
                "Macrophages were transplanted.",
            ):
                inflated = copy.deepcopy(content)
                inflated["author_summary"] += " " + false_claim
                try:
                    validate_kif13b_mertk_v2_regression(inflated, publication, page)
                except ValidationError as exc:
                    assert "unsupported positive scientific claim" in str(exc)
                else:
                    raise AssertionError(f"Unsupported claim was accepted: {false_claim}")
            wrong_target = copy.deepcopy(content)
            wrong_target["provenance"]["nx_target_identity_note"] = "NX-1607 validates CBL."
            try:
                validate_kif13b_mertk_v2_regression(wrong_target, publication, page)
            except ValidationError as exc:
                assert "target identity" in str(exc)
            else:
                raise AssertionError("CBL/CBLB target-identity distinction was lost.")
        elif norm_doi(publication.get("doi")) == CIRCADIAN_REVIEW_DOI:
            validate_circadian_review_v2_regression(content, publication, page)
            target = "doi-10-1002-mdr2-70052"
            assert page == (PAPERS_DIR / f"{target}.html").read_text(encoding="utf-8")
            assert markdown == (PAPERS_DIR / f"{target}.md").read_text(encoding="utf-8")
            assert len(content["qa"]) == 11
            assert [item["id"] for item in content["key_findings"]] == [
                f"KF{i}" for i in range(1, 9)
            ]
            pilot = content["citation_pilot"]
            assert len(pilot["methodology_boundaries"]) == 6
            assert len(pilot["evidence_matrix"]) == 8
            assert len(pilot["selected_evidence_sources"]) == 6
            for finding in content["key_findings"]:
                assert page.count(f'id="{finding["id"].lower()}"') == 1
            for anchor in (
                "methodological-boundaries", "chronotherapy-evidence-matrix",
                "selected-evidence-sources",
            ):
                assert page.count(f'id="{anchor}"') == 1
            for row in pilot["evidence_matrix"]:
                assert page.count(f'id="{row["id"]}"') == 1
                assert row["intervention"] in markdown
            for source in pilot["selected_evidence_sources"]:
                url = f"https://doi.org/{source['doi']}"
                assert page.count(f'href="{url}"') == 1
                assert f"]({url})" in markdown
                assert source["relationship"] in markdown
            for heading in (
                "Methodological & Translation Boundaries",
                "Chronotherapy Evidence Matrix", "Selected Evidence Sources",
            ):
                assert f"## {heading}" in markdown
            assert "<caption>Chronotherapy evidence levels and outcomes</caption>" in page
            assert "not the complete reference list" in page
            assert "not the complete reference list" in markdown
            for finding in content["key_findings"]:
                assert finding["source_locator"] in page
                assert finding["source_locator"] in markdown
            for phrase in (
                "narrative Review Article", "392 bibliography entries",
                "No new data were created or analyzed", "Hygia", "BedMed",
                "does not support a universal bedtime recommendation",
            ):
                assert phrase in page and phrase in markdown
            for false_claim in (
                "This is a systematic review.",
                "The article performed a meta-analysis.",
                "REV-ERB agonists clinically proven for cardiovascular disease.",
                "All antihypertensives should be taken at bedtime.",
                "Bedtime aspirin prevents myocardial infarction.",
                "SR9009 clinically effective.",
                "The review enrolled 392 participants.",
                "The bibliography contains 392 independent studies.",
            ):
                inflated = copy.deepcopy(content)
                inflated["author_summary"] += " " + false_claim
                try:
                    validate_circadian_review_v2_regression(inflated, publication, page)
                except ValidationError as exc:
                    assert "unsupported positive scientific claim" in str(exc)
                else:
                    raise AssertionError(f"Unsupported review claim was accepted: {false_claim}")
            false_data = copy.deepcopy(content)
            false_data["provenance"]["data_availability"] = "New patient data were collected."
            try:
                validate_circadian_review_v2_regression(false_data, publication, page)
            except ValidationError as exc:
                assert "provenance" in str(exc)
            else:
                raise AssertionError("New-data inflation was accepted for the review.")
            duplicate_row = copy.deepcopy(content)
            duplicate_row["citation_pilot"]["evidence_matrix"][1]["id"] = (
                duplicate_row["citation_pilot"]["evidence_matrix"][0]["id"]
            )
            expect_value_error(
                lambda: validate_deep_v2_content(duplicate_row, "duplicate matrix row"),
                "matrix row IDs must be unique",
            )
            duplicate_source = copy.deepcopy(content)
            duplicate_source["citation_pilot"]["selected_evidence_sources"][1]["doi"] = (
                duplicate_source["citation_pilot"]["selected_evidence_sources"][0]["doi"]
            )
            expect_value_error(
                lambda: validate_deep_v2_content(duplicate_source, "duplicate source"),
                "selected evidence DOIs must be unique",
            )
            bad_ref = copy.deepcopy(content)
            bad_ref["citation_pilot"]["selected_evidence_sources"][0]["evidence_refs"] = ["KF999"]
            expect_value_error(
                lambda: validate_deep_v2_content(bad_ref, "bad citation reference"),
                "must resolve to findings",
            )
            bad_doi = copy.deepcopy(content)
            bad_doi["citation_pilot"]["selected_evidence_sources"][0]["doi"] = (
                "10.1161/HYPERTENSIONAHA.114.04980"
            )
            expect_value_error(
                lambda: validate_deep_v2_content(bad_doi, "unnormalized source DOI"),
                "must be normalized and valid",
            )
        elif norm_doi(publication.get("doi")) == KIF13B_VSMC_DOI:
            validate_kif13b_vsmc_v2_regression(content, publication, page)
            target = "doi-10-1172-jci194175"
            assert publication["title"] == content["display_title"]
            assert publication["slug"] == target
            assert page == (PAPERS_DIR / f"{target}.html").read_text(encoding="utf-8")
            assert markdown == (PAPERS_DIR / f"{target}.md").read_text(encoding="utf-8")
            assert [item["id"] for item in content["key_findings"]] == [
                f"KF{i}" for i in range(1, 8)
            ]
            assert len(content["qa"]) == 10
            assert len(publication["authors"]) == 20
            assert publication["authors"][4] == "Ge Zhang"
            assert "researcher_author_positions" not in publication
            assert element_texts(page, "li", {"class": "paper-geo-v2__author"}) == publication["authors"]
            assert meta_contents(page, "citation_author") == publication["authors"]
            markdown_authors = markdown.split("## Full Authors\n\n", 1)[1].split("\n\n## ", 1)[0]
            assert markdown_authors.splitlines() == [
                f"{position}. {name}"
                for position, name in enumerate(publication["authors"], start=1)
            ]
            assert len(schema["author"]) == 20
            assert [author["name"] for author in schema["author"]] == publication["authors"]
            assert schema["author"][4]["@id"] == config["person_id"]
            assert schema["author"][4]["sameAs"] == f"https://orcid.org/{config['orcid']}"
            assert sum(author.get("@id") == config["person_id"]
                       for author in schema["author"]) == 1
            for section in (
                "Research Question", "Author Evidence Summary", "Key Findings",
                "Evidence Scale", "Study Design & Analytical Framework",
                "What This Study Adds", "Evidence Scope", "Limitations",
                "Q&A", "Concepts & Entities", "Related Research",
                "Publication & Provenance",
            ):
                assert section.replace("&", "&amp;") in page and section in markdown
            assert content["evidence_page_notice"] in visible_text(page)
            assert content["evidence_page_notice"] in markdown
            for finding in content["key_findings"]:
                assert finding["source_locator"] in page
                assert finding["source_locator"] in markdown
            for phrase in (
                "6 patients", "4 stable and 4 unstable", "stable n=19",
                "unstable n=38", "87 human carotid plaques overall",
                "n=8 per group", "five mice were pooled into one",
                "20-week Western diet", "12-week Western diet",
                "VSMC-Fib4", "VSMC-Fib1", "10 µM", "1 mg/kg/day",
                "final 12 weeks", "n=6 per group",
            ):
                assert phrase in page and phrase in markdown
            related = resolve_related_papers(content, public_by_doi, config["site_url"])
            assert [item["doi"] for item in related] == [
                "10.1093/eurheartj/ehaf523", "10.1186/s12967-022-03795-9"
            ]
            assert [item["url"] for item in related] == [
                "https://drgezhang.com/papers/doi-10-1093-eurheartj-ehaf523.html",
                "https://drgezhang.com/papers/smc-fate.html",
            ]
            for item in related:
                assert item["relationship"] in page and item["relationship"] in markdown
            for false_claim in (
                "Kenpaullone is a selective KLF4 inhibitor.",
                "Kenpaullone has human treatment efficacy.",
                "Five independent scRNA libraries were analyzed.",
                "Prospective clinical validation was performed.",
                "KIF13B directly binds KCTD10.",
            ):
                inflated = copy.deepcopy(content)
                inflated["author_summary"] += " " + false_claim
                try:
                    validate_kif13b_vsmc_v2_regression(inflated, publication, page)
                except ValidationError as exc:
                    assert "unsupported positive scientific claim" in str(exc)
                else:
                    raise AssertionError(f"Unsupported JCI claim was accepted: {false_claim}")
            excess_qa = copy.deepcopy(content)
            excess_qa["qa"].append({"question": "Extra test question?", "answer": "Extra answer."})
            expect_value_error(
                lambda: validate_deep_v2_content(excess_qa, "extra JCI Q&A"),
                "qa must contain",
            )

    publication, content = aihf_items[0]
    related = resolve_related_papers(content, public_by_doi, config["site_url"])
    assert [item["doi"] for item in related] == [
        "10.2147/cia.s462542",
        "10.1002/ggn2.202500053",
    ]
    assert [item["url"] for item in related] == [
        "https://drgezhang.com/papers/doi-10-2147-cia-s462542.html",
        "https://drgezhang.com/papers/doi-10-1002-ggn2-202500053.html",
    ]

    smc_publication, smc_content = smc_fate_items[0]
    related = resolve_related_papers(
        smc_content, public_by_doi, config["site_url"]
    )
    assert [item["doi"] for item in related] == [
        "10.1016/j.isci.2023.107587",
        "10.1172/jci194175",
        "10.1093/eurheartj/ehaf523",
    ]
    assert [item["url"] for item in related] == [
        "https://drgezhang.com/papers/apvs.html",
        "https://drgezhang.com/papers/doi-10-1172-jci194175.html",
        "https://drgezhang.com/papers/doi-10-1093-eurheartj-ehaf523.html",
    ]
    persisted_page = (PAPERS_DIR / "smc-fate.html").read_text(encoding="utf-8")
    persisted_markdown = (PAPERS_DIR / "smc-fate.md").read_text(encoding="utf-8")
    for item in related:
        assert item["relationship"] in persisted_page
        assert item["relationship"] in persisted_markdown

    olink_publication, olink_content = olink_items[0]
    assert olink_publication["slug"] == "olink-dcm"
    assert olink_content["version"] == 2
    assert norm_doi(olink_content["doi"]) == OLINK_DCM_DOI
    assert olink_content["study_profile"]["profile_type"] == "multicohort_omics"
    assert [item["id"] for item in olink_content["key_findings"]] == [
        f"KF{number}" for number in range(1, 7)
    ]
    assert all(item["source_locator"].strip() for item in olink_content["key_findings"])
    assert len(olink_content["qa"]) == 8
    assert all(
        set(item.get("evidence_refs", [])).issubset(
            {finding["id"] for finding in olink_content["key_findings"]}
        )
        for item in olink_content["qa"]
    )
    assert "unique_total_n" not in olink_content["study_profile"]
    assert "model_profile" not in olink_content
    olink_related = resolve_related_papers(
        olink_content, public_by_doi, config["site_url"]
    )
    assert [item["doi"] for item in olink_related] == [
        "10.2147/jir.s495784",
        "10.1111/jcmm.17789",
        "10.1007/s10238-026-02130-6",
    ]
    assert [item["url"] for item in olink_related] == [
        "https://drgezhang.com/papers/doi-10-2147-jir-s495784.html",
        "https://drgezhang.com/papers/doi-10-1111-jcmm-17789.html",
        "https://drgezhang.com/papers/doi-10-1007-s10238-026-02130-6.html",
    ]
    olink_page = (PAPERS_DIR / "olink-dcm.html").read_text(encoding="utf-8")
    olink_markdown = (PAPERS_DIR / "olink-dcm.md").read_text(encoding="utf-8")
    for item in olink_related:
        assert item["relationship"] in olink_page
        assert item["relationship"] in olink_markdown

    synthetic_publication, synthetic = synthetic_multicohort_fixture()
    synthetic_page, synthetic_markdown, synthetic_schema = rendered_v2(
        synthetic_publication, synthetic, config, public_by_doi
    )
    validate_v2_inventory(
        [norm_doi(item[0]["doi"]) for item in v2_items] + [SYNTHETIC_DOI]
    )
    assert "<h2>Evidence Scale</h2>" in synthetic_page
    assert "<h3>Counting note</h3>" in synthetic_page
    assert "Cohort hierarchy" not in synthetic_page
    assert "Unique total" not in synthetic_page
    assert "## Evidence Scale" in synthetic_markdown
    assert "### Counting note" in synthetic_markdown
    assert "### Cohort hierarchy" not in synthetic_markdown
    assert synthetic_schema["description"] == synthetic["author_summary"]
    assert synthetic_schema["keywords"] == flatten_concepts(synthetic)

    bad_hierarchy = copy.deepcopy(content)
    bad_hierarchy["study_profile"]["cohorts"][0]["n"] = 499
    expect_value_error(
        lambda: validate_deep_v2_content(bad_hierarchy, "bad hierarchy"),
        "child counts",
    )

    missing_metrics = copy.deepcopy(synthetic)
    del missing_metrics["study_profile"]["scale_metrics"]
    expect_value_error(
        lambda: validate_deep_v2_content(missing_metrics, "missing metrics"),
        "scale_metrics",
    )

    missing_counting_note = copy.deepcopy(synthetic)
    del missing_counting_note["study_profile"]["counting_note"]
    expect_value_error(
        lambda: validate_deep_v2_content(
            missing_counting_note, "missing counting note"
        ),
        "counting_note",
    )

    malformed_metric = copy.deepcopy(synthetic)
    malformed_metric["study_profile"]["scale_metrics"][0]["unit"] = "cohorts"
    expect_value_error(
        lambda: validate_deep_v2_content(malformed_metric, "malformed metric"),
        "only label and value",
    )

    duplicate_metric = copy.deepcopy(synthetic)
    duplicate_metric["study_profile"]["scale_metrics"].append(
        copy.deepcopy(duplicate_metric["study_profile"]["scale_metrics"][0])
    )
    expect_value_error(
        lambda: validate_deep_v2_content(duplicate_metric, "duplicate metric"),
        "duplicate items",
    )

    unknown_profile = copy.deepcopy(synthetic)
    unknown_profile["study_profile"]["profile_type"] = "single_cell"
    expect_value_error(
        lambda: validate_deep_v2_content(unknown_profile, "unknown profile"),
        "profile_type",
    )

    bad_ref = copy.deepcopy(synthetic)
    bad_ref["qa"][0]["evidence_refs"] = ["KF999"]
    expect_value_error(
        lambda: validate_deep_v2_content(bad_ref, "bad Q&A"),
        "real finding IDs",
    )

    bad_finding = copy.deepcopy(synthetic)
    bad_finding["key_findings"][0]["metric"] = "synthetic metric"
    expect_value_error(
        lambda: validate_deep_v2_content(bad_finding, "bad finding"),
        "normalized V2 fields",
    )

    bad_related = copy.deepcopy(synthetic)
    bad_related["related_papers"][0]["doi"] = "10.9999/not-public"
    expect_value_error(
        lambda: resolve_related_papers(
            bad_related, public_by_doi, config["site_url"]
        ),
        "does not resolve",
    )

    bad_provenance = copy.deepcopy(synthetic)
    bad_provenance["provenance"]["publisher_url"] = "http://example.org/paper"
    expect_value_error(
        lambda: validate_deep_v2_content(bad_provenance, "bad provenance"),
        "HTTPS URL",
    )

    print("PAPER GEO V2 TESTS PASS")
    print(
        json.dumps(
            {
                "v1_pages": v1_count,
                "v2_pages": len(v2_items),
                "pending_pages": pending_count,
                "multicohort_synthetic": "pass",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run_tests()
