"""One source-reviewed patent note, deliberately separate from Paper GEO V2."""
import html
import json
from urllib.parse import urlsplit
from sync_common import ROOT

SLUG = "work-3d25d7e32b86959b"
PATH = ROOT / "data/patent_evidence.json"

def load(publication):
    if publication.get("slug") != SLUG:
        return None
    content = json.loads(PATH.read_text(encoding="utf-8"))
    if (publication.get("type") != "Patent" or publication.get("doi")
            or content.get("work_slug") != SLUG
            or content.get("module_type") != "patent_record"
            or content.get("ordinary_paper_v2") is not False):
        raise ValueError("Patent context must preserve the non-DOI, non-V2 identity")
    if not content.get("limitations") or not content.get("claim_scope"):
        raise ValueError("Patent context requires claim locators and limitations")
    for row in content["record_evidence"]:
        if urlsplit(row["source_url"]).scheme != "https" or not row["source_locator"]:
            raise ValueError("Patent record requires HTTPS sources and locators")
    return content

def blocks(content):
    """Shared text sequence guarantees identical scope in both formats."""
    if not content:
        return []
    out = [("Patent document evidence", content["evidence_notice"], None)]
    for row in content["record_evidence"]:
        out.append((row["label"], row["statement"],
                    (row["source_url"], row["source_locator"])))
    for row in content["claim_scope"]:
        heading = "Reported claim" + ("s" if len(row["claim_numbers"]) > 1 else "")
        heading += " " + ", ".join(map(str, row["claim_numbers"]))
        out.append((heading, row["summary"],
                    (content["provenance"]["source_url"], row["source_locator"])))
    context = content["research_context"]
    out.append(("Research context", context["summary"],
                (content["provenance"]["source_url"], " ".join(context["source_locators"]))))
    out.append(("Evidence and legal-status limits", " ".join(content["limitations"]), None))
    p = content["provenance"]
    out.append(("Source version", p["reviewed_version"] + " Uploaded by " + p["uploader"]
                + " on " + p["uploaded_on"] + "; reviewed " + p["accessed_on"] + ". "
                + p["source_format"] + ". " + p["copyright_note"],
                (p["source_url"], "Author-uploaded source")))
    return out

def render_html(content):
    if not content:
        return ""
    rows = []
    for i, (heading, text, source) in enumerate(blocks(content)):
        tag = "h2" if i == 0 else "h3"
        rows.append(f"<{tag}>{html.escape(heading)}</{tag}><p>{html.escape(text)}</p>")
        if source:
            rows.append('<p class="muted">Source: <a href="'
                        + html.escape(source[0], quote=True) + '">' + html.escape(source[1]) + "</a></p>")
    return '<section id="patent-document-evidence">' + "".join(rows) + "</section>\n"

def render_markdown(content):
    if not content:
        return ""
    rows = ['<a id="patent-document-evidence"></a>', ""]
    for i, (heading, text, source) in enumerate(blocks(content)):
        rows.extend([("## " if i == 0 else "### ") + heading, "", text, ""])
        if source:
            rows.extend(["Source: [" + source[1] + "](" + source[0] + ")", ""])
    return "\n".join(rows)
