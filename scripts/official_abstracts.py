"""Optional, verbatim publisher/PMC abstract source layer."""

import json
from urllib.parse import urlparse

from sync_common import ROOT, is_withdrawn, norm_doi


PATH = ROOT / "data" / "official_abstracts.json"
LICENSE_URLS = {
    "CC-BY-NC-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-NC-ND-4.0": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
}
# EHJ author reuse permits this article's abstract/citation, not its full text.
# This permission is article-specific and must not authorize other sources.
DOI_LICENSE_URLS = {
    "10.1016/j.ejphar.2023.175569": {
        "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    },
    "10.1093/eurheartj/ehaf523": {
        "OUP-AUTHOR-ABSTRACT-REUSE": "https://academic.oup.com/pages/open-research/open-access/charges-licences-and-self-archiving/author-self-archiving-policy",
    },
}
SOURCES = {
    "10.1002/ggn2.202500053": ("advanced.onlinelibrary.wiley.com", "/doi/full/10.1002/ggn2.202500053"),
    "10.18632/aging.205564": ("www.aging-us.com", "/article/205564/text"),
    '10.3389/fcvm.2025.1724572': ('www.frontiersin.org', '/journals/cardiovascular-medicine/articles/10.3389/fcvm.2025.1724572/full'),
    '10.3389/fpubh.2025.1521372': ('www.frontiersin.org', '/journals/public-health/articles/10.3389/fpubh.2025.1521372/full'),

    "10.1038/s41598-024-65236-5": ("www.nature.com", "/articles/s41598-024-65236-5"),
    "10.1002/mdr2.70004": ("onlinelibrary.wiley.com", "/doi/full/10.1002/mdr2.70004"),
    "10.1111/jcmm.17789": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC10339102/"),
    "10.1111/jcmm.70258": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC11668728/"),
    "10.2147/ijn.s522157": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC12315914/"),
    "10.1186/s12915-025-02400-x": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC12465141/"),
    "10.1136/jitc-2024-010127": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC11749606/"),
    "10.1038/s41467-024-50415-9": ("www.nature.com", "/articles/s41467-024-50415-9"),
    "10.1038/s41698-026-01699-1": ("www.nature.com", "/articles/s41698-026-01699-1"),
    "10.1016/j.isci.2023.107587": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC10470306/"),
    "10.1186/s12967-022-03795-9": ("link.springer.com", "/article/10.1186/s12967-022-03795-9"),
    "10.1002/ehf2.14003": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC9349450/"),
    "10.1172/jci194175": ("www.jci.org", "/articles/view/194175"),
    "10.1021/acs.jproteome.4c00522": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC11385702/"),
    "10.1002/mdr2.70052": ("onlinelibrary.wiley.com", "/doi/full/10.1002/mdr2.70052"),
    "10.3389/fonc.2021.659217": ("www.frontiersin.org", "/journals/oncology/articles/10.3389/fonc.2021.659217/full"),
    "10.1111/jcmm.70725": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC12328994/"),
    "10.1093/eurheartj/ehaf523": ("academic.oup.com", "/eurheartj/article/46/45/4969/8212255"),
    "10.1016/j.ejphar.2023.175569": ("pubmed.ncbi.nlm.nih.gov", "/36740037/"),
}
EXCLUDED = {
    "10.1200/po.24.00089",
}


def abstract_text(record):
    abstract = record["abstract"]
    if abstract["type"] == "unstructured":
        return abstract["text"]
    return "\n".join(
        f"{section['label']}: {section['text']}"
        for section in abstract["sections"]
    )


def load_official_abstracts(publications):
    if not PATH.is_file():
        return {}
    data = json.loads(PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"version", "papers"} or data["version"] != 1:
        raise ValueError("official_abstracts must have version 1 and papers only.")
    papers = data["papers"]
    if not isinstance(papers, dict):
        raise ValueError("official_abstracts.papers must be an object.")
    public_dois = [norm_doi(item.get("doi")) for item in publications if not is_withdrawn(item)]
    for doi, record in papers.items():
        if doi != norm_doi(doi) or public_dois.count(doi) != 1 or doi not in SOURCES or doi in EXCLUDED:
            raise ValueError(f"Official abstract DOI is not one permitted public paper: {doi}")
        required = {"source_type", "source_url", "license", "license_url", "verbatim", "abstract"}
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError(f"Official abstract fields invalid for {doi}.")
        # This indexed abstract is permitted only with its exact DOI/PMID and
        # independently verified article-specific publisher CC BY grant.
        source_types = ({"pubmed"} if doi == "10.1016/j.ejphar.2023.175569"
                        else {"version_of_record", "publisher", "pmc"})
        if record["source_type"] not in source_types:
            raise ValueError(f"Official abstract source type invalid for {doi}.")
        parsed = urlparse(record["source_url"])
        if (parsed.scheme, parsed.netloc, parsed.path) != ("https", *SOURCES[doi]) or parsed.query or parsed.fragment:
            raise ValueError(f"Official abstract source URL invalid for {doi}.")
        permitted_licenses = DOI_LICENSE_URLS.get(doi, LICENSE_URLS)
        if record["license"] not in permitted_licenses or record["license_url"] != permitted_licenses[record["license"]]:
            raise ValueError(f"Official abstract license invalid for {doi}.")
        if record["verbatim"] is not True:
            raise ValueError(f"Official abstract must be verbatim for {doi}.")
        abstract = record["abstract"]
        if not isinstance(abstract, dict) or abstract.get("type") not in {"structured", "unstructured"}:
            raise ValueError(f"Official abstract format invalid for {doi}.")
        if abstract["type"] == "unstructured":
            if set(abstract) != {"type", "text"} or not isinstance(abstract["text"], str) or not abstract["text"].strip():
                raise ValueError(f"Official abstract text invalid for {doi}.")
        else:
            sections = abstract.get("sections")
            if set(abstract) != {"type", "sections"} or not isinstance(sections, list) or not sections:
                raise ValueError(f"Official abstract sections invalid for {doi}.")
            for section in sections:
                if (not isinstance(section, dict) or set(section) != {"label", "text"}
                        or not all(isinstance(section[key], str) and section[key].strip() for key in ("label", "text"))):
                    raise ValueError(f"Official abstract section invalid for {doi}.")
            if len({section["label"] for section in sections}) != len(sections):
                raise ValueError(f"Official abstract section labels duplicate for {doi}.")
            if doi == "10.1186/s12967-022-03795-9" and [s["label"] for s in sections] != ["Background", "Methods", "Results", "Conclusions"]:
                raise ValueError("SMC-fate official abstract section order changed.")
            if doi == "10.1002/ehf2.14003" and [s["label"] for s in sections] != ["Aims", "Methods", "Results", "Conclusions"]:
                raise ValueError("COVID-HF official abstract section order changed.")
            expected = {
                "10.2147/ijn.s522157": ["Purpose", "Methods", "Results", "Conclusion"],
                "10.1186/s12915-025-02400-x": ["Background", "Results", "Conclusions"],
                "10.1136/jitc-2024-010127": ["Background", "Methods", "Results", "Conclusions"],
            }.get(doi)
            if expected and [s["label"] for s in sections] != expected:
                raise ValueError(f"Official abstract section order changed for {doi}.")
    return papers
