import hashlib
import json
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from indexnow_submit import (
    IndexNowError,
    detect_changes,
    load_config,
    parse_sitemap_text,
    process_entries,
    submit_urls,
)


ROOT = Path(__file__).resolve().parents[1]
HOME = "https://drgezhang.com/"
PUBLICATIONS = "https://drgezhang.com/publications.html"
PAPER = "https://drgezhang.com/papers/indexnow-test.html"


def sitemap(entries):
    rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url, lastmod in entries:
        rows.extend(
            [
                "  <url>",
                f"    <loc>{escape(url)}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                "  </url>",
            ]
        )
    rows.append("</urlset>")
    return "\n".join(rows) + "\n"


def run_python(script):
    result = subprocess.run(
        [sys.executable, script], cwd=ROOT, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + "\n" + result.stderr)
    return result


def paths_digest(relative_paths):
    hasher = hashlib.sha256()
    paths = []
    for relative in relative_paths:
        path = ROOT / relative
        paths.extend(sorted(path.rglob("*")) if path.is_dir() else [path])
    for path in paths:
        if path.is_file():
            hasher.update(str(path.relative_to(ROOT)).encode())
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def publication_state_digest():
    return paths_digest(
        (
            "data/publications_master.json",
            "data/featured_papers.json",
            "data/deep_geo_papers.json",
            "data/deep_geo",
            "publications.json",
            "publication_inventory.csv",
            "paper_index.json",
            "papers",
        )
    )


def generated_site_digest():
    return paths_digest(
        (
            "index.html",
            "publications.html",
            "publications.json",
            "publication_inventory.csv",
            "paper_index.json",
            "robots.txt",
            "sitemap.xml",
            "llms.txt",
            "llms-full.txt",
            "papers",
        )
    )


def publication_counts():
    master = json.loads(
        (ROOT / "data/publications_master.json").read_text(encoding="utf-8")
    )
    public = [
        item
        for item in master
        if str(item.get("status") or "").casefold() != "withdrawn"
    ]
    featured = json.loads(
        (ROOT / "data/featured_papers.json").read_text(encoding="utf-8")
    )["papers"]
    deep_geo = json.loads(
        (ROOT / "data/deep_geo_papers.json").read_text(encoding="utf-8")
    )["papers"]
    dois = [
        str(item.get("doi") or "").strip().casefold()
        for item in master
        if str(item.get("doi") or "").strip()
    ]
    current_sitemap = parse_sitemap_text(
        (ROOT / "sitemap.xml").read_text(encoding="utf-8"), "drgezhang.com"
    )
    return {
        "master": len(master),
        "public": len(public),
        "withdrawn": len(master) - len(public),
        "featured": len(featured),
        "deep_geo": len(deep_geo),
        "doi_duplicates": len(dois) - len(set(dois)),
        "sitemap_urls": len(current_sitemap),
    }


class FakeResponse:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def getcode(self):
        return self.status

    def read(self, _limit):
        return b""


def main():
    config = load_config()
    assert config["enabled"] is True
    assert config["host"] == "drgezhang.com"
    assert config["key_location"] == (
        f"https://drgezhang.com/{config['key']}.txt"
    )
    assert (ROOT / f"{config['key']}.txt").read_text(encoding="utf-8").strip() == (
        config["key"]
    )

    previous = parse_sitemap_text(
        sitemap([(HOME, "2026-09-20")]), config["host"]
    )
    current = parse_sitemap_text(
        sitemap([(HOME, "2026-09-20"), (PAPER, "2026-09-21")]),
        config["host"],
    )
    changes = detect_changes(previous, current)
    assert changes.added == (PAPER,)
    assert not changes.updated and not changes.deleted

    previous = parse_sitemap_text(
        sitemap([(HOME, "2026-09-20")]), config["host"]
    )
    current = parse_sitemap_text(
        sitemap([(HOME, "2026-09-21")]), config["host"]
    )
    changes = detect_changes(previous, current)
    assert changes.updated == (HOME,)
    assert not changes.added and not changes.deleted

    previous = parse_sitemap_text(
        sitemap([(HOME, "2026-09-20"), (PAPER, "2026-09-20")]),
        config["host"],
    )
    current = parse_sitemap_text(
        sitemap([(HOME, "2026-09-20")]), config["host"]
    )
    changes = detect_changes(previous, current)
    assert changes.deleted == (PAPER,)
    assert not changes.added and not changes.updated

    unchanged = parse_sitemap_text(
        sitemap(
            [(HOME, "2026-09-20"), (PUBLICATIONS, "2026-09-20")]
        ),
        config["host"],
    )
    calls = []

    def reject_submission(_config, _urls):
        calls.append(True)
        raise AssertionError("No-op detection attempted an API request.")

    result = process_entries(
        config, unchanged, unchanged, submitter=reject_submission
    )
    assert result["submitted"] is False and not calls
    assert not result["changes"].urls

    for rejected in (
        "https://example.com/page.html",
        "http://drgezhang.com/page.html",
        "https://www.drgezhang.com/page.html",
        "https://drgezhang.com/paper_index.json",
        "https://drgezhang.com/page.html?preview=1",
    ):
        try:
            parse_sitemap_text(
                sitemap([(rejected, "2026-09-20")]), config["host"]
            )
        except IndexNowError:
            pass
        else:
            raise AssertionError(f"Noncanonical URL was accepted: {rejected}")

    captured = {}

    def fake_opener(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["content_type"] = request.headers["Content-type"]
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(202)

    status = submit_urls(config, [HOME], opener=fake_opener)
    assert status == 202
    assert captured["url"] == "https://api.indexnow.org/indexnow"
    assert captured["timeout"] == 30
    assert captured["content_type"] == "application/json; charset=utf-8"
    assert captured["payload"] == {
        "host": config["host"],
        "key": config["key"],
        "keyLocation": config["key_location"],
        "urlList": [HOME],
    }

    workflow = (ROOT / ".github/workflows/static.yml").read_text(encoding="utf-8")
    deploy_position = workflow.index("uses: actions/deploy-pages@v5")
    indexnow_position = workflow.index("python scripts/indexnow_submit.py")
    assert deploy_position < indexnow_position
    assert "if: github.event_name == 'push'" in workflow
    assert "INDEXNOW_PREVIOUS_REF: ${{ github.event.before }}" in workflow
    assert "fetch-depth: 0" in workflow

    counts_before = publication_counts()
    publication_before = publication_state_digest()
    sitemap_before = (ROOT / "sitemap.xml").read_bytes()
    key_before = (ROOT / f"{config['key']}.txt").read_bytes()
    run_python("scripts/build_publications.py")
    run_python("scripts/validate_site.py")
    first_build = generated_site_digest()
    run_python("scripts/build_publications.py")
    assert generated_site_digest() == first_build
    assert publication_state_digest() == publication_before
    assert publication_counts() == counts_before
    assert (ROOT / "sitemap.xml").read_bytes() == sitemap_before
    assert (ROOT / f"{config['key']}.txt").read_bytes() == key_before

    print("INDEXNOW TESTS PASS")
    print("- config and stable root key file: PASS")
    print("- added URL detection: PASS")
    print("- updated-by-lastmod detection: PASS")
    print("- deleted URL detection: PASS")
    print("- unchanged URL no-op: PASS")
    print("- external and noncanonical URL rejection: PASS")
    print("- official bulk request and HTTP 202 handling: PASS")
    print("- post-deployment workflow ordering: PASS")
    print("- publication state and sitemap semantics: PASS")
    print("- validator and second-build idempotence: PASS")


if __name__ == "__main__":
    main()
