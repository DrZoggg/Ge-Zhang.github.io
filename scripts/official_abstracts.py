"""Optional, verbatim publisher/PMC abstract source layer."""

import json
from urllib.parse import urlparse

from sync_common import ROOT, is_withdrawn, norm_doi


PATH = ROOT / "data" / "official_abstracts.json"
LICENSE_URLS = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-NC-ND-4.0": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
}
SOURCES = {
    "10.1038/s41467-024-50415-9": ("www.nature.com", "/articles/s41467-024-50415-9"),
    "10.1038/s41698-026-01699-1": ("www.nature.com", "/articles/s41698-026-01699-1"),
    "10.1016/j.isci.2023.107587": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC10470306/"),
    "10.1186/s12967-022-03795-9": ("link.springer.com", "/article/10.1186/s12967-022-03795-9"),
    "10.1002/ehf2.14003": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC9349450/"),
    "10.1172/jci194175": ("www.jci.org", "/articles/view/194175"),
    "10.1021/acs.jproteome.4c00522": ("pmc.ncbi.nlm.nih.gov", "/articles/PMC11385702/"),
    "10.1002/mdr2.70052": ("onlinelibrary.wiley.com", "/doi/full/10.1002/mdr2.70052"),
}
EXCLUDED = {
    "10.1093/eurheartj/ehaf523",
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
        if record["source_type"] not in {"version_of_record", "publisher", "pmc"}:
            raise ValueError(f"Official abstract source type invalid for {doi}.")
        parsed = urlparse(record["source_url"])
        if (parsed.scheme, parsed.netloc, parsed.path) != ("https", *SOURCES[doi]) or parsed.query or parsed.fragment:
            raise ValueError(f"Official abstract source URL invalid for {doi}.")
        if record["license"] not in LICENSE_URLS or record["license_url"] != LICENSE_URLS[record["license"]]:
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
    return papers
