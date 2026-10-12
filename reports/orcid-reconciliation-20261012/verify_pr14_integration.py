"""Verify existing PR #14 in a disposable detached worktree, without editing it.

Usage: python verify_pr14_integration.py <detached-worktree-path>
Only new DOI data are copied; every existing PR #14 master record is retained.
The candidate Science V2 is enabled in this local verification worktree only.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SCIENCE = "10.1126/science.aek9583"
MEDICINE = "10.1016/j.medd.2026.100004"


def read(path):
    return json.loads(path.read_text("utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    integration = Path(sys.argv[1]).resolve()
    intended = (ROOT.parent / "orcid-reconciliation-20261012-evidence").resolve()
    assert intended in integration.parents, "Verification workspace must be isolated in the task evidence directory"
    ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=integration).decode().strip()
    assert ref == "eca81a3f5600cf523c6dc5663f70ca30dab863fc"
    before = json.loads(subprocess.check_output(["git", "show", "HEAD:data/publications_master.json"], cwd=integration))
    added = [r for r in read(ROOT / "data/publications_master.json") if r.get("doi") in {SCIENCE, MEDICINE}]
    current = before + added
    assert len({r.get("doi") or r["title"] for r in current}) == len(current)
    write(integration / "data/publications_master.json", current)
    for name in ("citation_metadata", "scholarly_identifiers"):
        target = integration / f"data/{name}.json"
        payload = read(target)
        incoming = read(ROOT / f"data/{name}.json")["papers"]
        payload["papers"].update({d: incoming[d] for d in (SCIENCE, MEDICINE)})
        write(target, payload)
    for name in ("featured_papers", "deep_geo_papers"):
        shutil.copyfile(ROOT / f"data/{name}.json", integration / f"data/{name}.json")
    shutil.copyfile(OUT / "science/SCIENCE_V2_READY.json", integration / "data/deep_geo/doi-10-1126-science-aek9583.json")
    questions = read(integration / "data/question_index.json")
    questions["papers"][SCIENCE] = {"qa_index": 1}
    write(integration / "data/question_index.json", questions)
    log = []
    for script in ("build_publications.py", "validate_site.py"):
        run = subprocess.run([sys.executable, f"scripts/{script}"], cwd=integration, capture_output=True)
        log.append((run.stdout.decode("utf-8", errors="replace") + run.stderr.decode("utf-8", errors="replace")).replace("\r\n", "\n"))
        assert run.returncode == 0, log[-1]
    for old in before:
        assert [r for r in read(integration / "data/publications_master.json") if (r.get("doi") or r["title"]) == (old.get("doi") or old["title"])] == [old]
    md = (integration / "papers/doi-10-1126-science-aek9583.md").read_text("utf-8")
    page = (integration / "papers/doi-10-1126-science-aek9583.html").read_text("utf-8")
    assert '"@type": "ScholarlyArticle"' in page
    assert "Key Arguments" in page and "Key Arguments" in md
    assert "2026/10/01" in page and "38" in page and "39" in page
    assert "1. Ge Zhang" in md and "5. Teng Li" in md
    for ext in (".bib", ".ris", ".csl.json"):
        assert SCIENCE in (integration / f"citations/doi-10-1126-science-aek9583{ext}").read_text("utf-8")
    csl = read(integration / "citations/doi-10-1126-science-aek9583.csl.json")
    assert csl["type"] == "article-journal" and csl["issued"]["date-parts"] == [[2026, 10, 1]]
    assert csl["page"] == "38-39"
    schema_check = {
        "pr14_head_sha": ref, "integration_only": True,
        "existing_pr14_records_preserved": len(before), "production_renderer_changed": False,
        "build": "PASS", "validate_site": "PASS",
        "science_v2_html_markdown_schema_authors_citation_exports": "PASS",
        "science_evidence_csv": "PASS" if (integration / "assets/evidence/doi-10-1126-science-aek9583.csv").is_file() else "FAIL",
        "medicine_correspondence_exports": "DEFERRED_SHARED_TYPE_SUPPORT",
        "disposition": "Verification only. Activate Science's reviewed V2 after PR #14 is merged and rerun on latest main; current independent Draft remains pending.",
    }
    (OUT / "pr14-integration.log").write_text("\n".join(log), encoding="utf-8")
    write(OUT / "PR14_INTEGRATION_ACCEPTANCE.json", schema_check)
    print(json.dumps(schema_check, indent=2))


if __name__ == "__main__":
    main()
