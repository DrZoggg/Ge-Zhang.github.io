import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = [sys.executable, "scripts/research_themes_control.py"]
EXPECTED_RESEARCH = {
    "label": "Research themes",
    "heading": "Four connected directions",
    "themes": [
        {
            "enabled": True,
            "title": "AI & clinical risk prediction",
            "description": (
                "Explainable machine learning, multimodal clinical data, survival "
                "analysis and decision-support tools for cardiovascular disease."
            ),
        },
        {
            "enabled": True,
            "title": "Atherosclerosis & vascular biology",
            "description": (
                "Plaque vulnerability, vascular smooth muscle cell states, single-cell "
                "genomics and molecular heterogeneity."
            ),
        },
        {
            "enabled": True,
            "title": "Multi-omics & translational biomarkers",
            "description": (
                "Transcriptomics, proteomics, metabolomics and integrated systems "
                "biology for biomarker discovery and validation."
            ),
        },
        {
            "enabled": True,
            "title": "Circadian cardiovascular biology",
            "description": (
                "Circadian disruption, chronobiology, vascular inflammation and "
                "precision cardiovascular medicine."
            ),
        },
    ],
}


def copy_fixture(temp_root, name):
    target = temp_root / name
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "_site"),
    )
    return target


def run(repo, *args, success=True):
    result = subprocess.run(
        CONTROLLER + list(args), cwd=repo, text=True, capture_output=True
    )
    if success and result.returncode != 0:
        raise AssertionError(result.stdout + "\n" + result.stderr)
    if not success and result.returncode == 0:
        raise AssertionError("Command unexpectedly succeeded: " + " ".join(args))
    return result


def run_python(repo, script, success=True):
    result = subprocess.run(
        [sys.executable, script], cwd=repo, text=True, capture_output=True
    )
    if success and result.returncode != 0:
        raise AssertionError(result.stdout + "\n" + result.stderr)
    if not success and result.returncode == 0:
        raise AssertionError(f"Command unexpectedly succeeded: {script}")
    return result


def digest(repo):
    hasher = hashlib.sha256()
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        hasher.update(str(path.relative_to(repo)).encode())
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def paths_digest(repo, relative_paths):
    hasher = hashlib.sha256()
    paths = []
    for relative in relative_paths:
        path = repo / relative
        paths.extend(sorted(path.rglob("*")) if path.is_dir() else [path])
    for path in paths:
        if path.is_file():
            hasher.update(str(path.relative_to(repo)).encode())
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def load_profile(repo):
    return json.loads((repo / "data/profile_config.json").read_text(encoding="utf-8"))


def write_profile(repo, profile):
    (repo / "data/profile_config.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def protected_profile(repo):
    return {
        key: value
        for key, value in load_profile(repo).items()
        if key != "homepage_research"
    }


def publication_state_digest(repo):
    return paths_digest(
        repo,
        (
            "data/publications_master.json",
            "data/featured_papers.json",
            "data/deep_geo_papers.json",
            "data/deep_geo",
            "publications.json",
            "publication_inventory.csv",
            "paper_index.json",
            "papers",
        ),
    )


def sitemap_lastmods(repo):
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    entries = {}
    root = ET.parse(repo / "sitemap.xml").getroot()
    for node in root.findall(f"{namespace}url"):
        location = node.find(f"{namespace}loc")
        lastmod = node.find(f"{namespace}lastmod")
        entries[location.text.strip()] = lastmod.text.strip()
    return entries


def set_sitemap_lastmods(repo, value):
    path = repo / "sitemap.xml"
    content = path.read_text(encoding="utf-8")
    path.write_text(
        re.sub(
            r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
            f"<lastmod>{value}</lastmod>",
            content,
        ),
        encoding="utf-8",
    )


def rendered_research(repo):
    homepage = (repo / "index.html").read_text(encoding="utf-8")
    matches = re.findall(
        r'<section id="research">(.*?)</section>', homepage, flags=re.DOTALL
    )
    assert len(matches) == 1
    section = matches[0]
    label = html.unescape(
        re.search(r'<div class="eyebrow">(.*?)</div>', section).group(1)
    )
    heading = html.unescape(re.search(r"<h2>(.*?)</h2>", section).group(1))
    cards = [
        {"title": html.unescape(title), "description": html.unescape(description)}
        for title, description in re.findall(
            r'<div class="card"><h3>(.*?)</h3><p>(.*?)</p></div>',
            section,
            flags=re.DOTALL,
        )
    ]
    return {"label": label, "heading": heading, "cards": cards}


def publication_counts(repo):
    master = json.loads(
        (repo / "data/publications_master.json").read_text(encoding="utf-8")
    )
    public = [
        item
        for item in master
        if str(item.get("status") or "").casefold() != "withdrawn"
    ]
    featured = json.loads(
        (repo / "data/featured_papers.json").read_text(encoding="utf-8")
    )["papers"]
    deep_geo = json.loads(
        (repo / "data/deep_geo_papers.json").read_text(encoding="utf-8")
    )["papers"]
    dois = [
        str(item.get("doi") or "").strip().casefold()
        for item in master
        if str(item.get("doi") or "").strip()
    ]
    return {
        "master": len(master),
        "public": len(public),
        "withdrawn": len(master) - len(public),
        "featured": len(featured),
        "deep_geo": len(deep_geo),
        "doi_duplicates": len(dois) - len(set(dois)),
        "sitemap_urls": len(sitemap_lastmods(repo)),
    }


def main():
    expected_counts = publication_counts(ROOT)
    profile = load_profile(ROOT)
    assert profile["homepage_research"] == EXPECTED_RESEARCH
    initial_render = rendered_research(ROOT)
    assert initial_render["label"] == EXPECTED_RESEARCH["label"]
    assert initial_render["heading"] == EXPECTED_RESEARCH["heading"]
    assert initial_render["cards"] == [
        {"title": theme["title"], "description": theme["description"]}
        for theme in EXPECTED_RESEARCH["themes"]
    ]

    workflow = (ROOT / ".github/workflows/research-themes-control.yml").read_text(
        encoding="utf-8"
    )
    assert "name: Research Themes Control Center" in workflow
    assert "group: publication-data-updates" in workflow
    for position in range(1, 5):
        for field in ("action", "title", "description"):
            assert f"theme_{position}_{field}:" in workflow

    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)

        noop = copy_fixture(temp_root, "noop")
        before = digest(noop)
        result = run(noop)
        assert "Updated fields:\n- none" in result.stdout
        assert digest(noop) == before

        heading = copy_fixture(temp_root, "heading")
        yesterday = (
            datetime.now(timezone.utc).date() - timedelta(days=1)
        ).isoformat()
        set_sitemap_lastmods(heading, yesterday)
        profile_before = protected_profile(heading)
        publication_before = publication_state_digest(heading)
        result = run(heading, "--section-heading", "Connected research directions")
        assert "- section_heading" in result.stdout
        assert load_profile(heading)["homepage_research"]["heading"] == (
            "Connected research directions"
        )
        assert rendered_research(heading)["heading"] == "Connected research directions"
        lastmods = sitemap_lastmods(heading)
        assert lastmods["https://drgezhang.com/"] == (
            datetime.now(timezone.utc).date().isoformat()
        )
        assert all(
            value == yesterday
            for url, value in lastmods.items()
            if url != "https://drgezhang.com/"
        )
        assert protected_profile(heading) == profile_before
        assert publication_state_digest(heading) == publication_before
        assert publication_counts(heading) == expected_counts
        run_python(heading, "scripts/validate_site.py")
        stable = digest(heading)
        run_python(heading, "scripts/build_publications.py")
        assert digest(heading) == stable

        theme_text = copy_fixture(temp_root, "theme-text")
        profile_before = protected_profile(theme_text)
        publication_before = publication_state_digest(theme_text)
        run(
            theme_text,
            "--theme-1-title",
            "AI-guided clinical risk prediction",
        )
        assert rendered_research(theme_text)["cards"][0]["title"] == (
            "AI-guided clinical risk prediction"
        )
        run(
            theme_text,
            "--theme-2-description",
            "Updated vascular biology presentation text.",
        )
        assert rendered_research(theme_text)["cards"][1]["description"] == (
            "Updated vascular biology presentation text."
        )
        assert protected_profile(theme_text) == profile_before
        assert publication_state_digest(theme_text) == publication_before

        enable_disable = copy_fixture(temp_root, "enable-disable")
        run(enable_disable, "--theme-4-action", "disable")
        assert len(rendered_research(enable_disable)["cards"]) == 3
        assert not load_profile(enable_disable)["homepage_research"]["themes"][3][
            "enabled"
        ]
        run(enable_disable, "--theme-4-action", "enable")
        assert len(rendered_research(enable_disable)["cards"]) == 4
        assert load_profile(enable_disable)["homepage_research"]["themes"][3][
            "enabled"
        ]

        invalid_title = copy_fixture(temp_root, "invalid-title")
        invalid_profile = load_profile(invalid_title)
        invalid_profile["homepage_research"]["themes"][0]["title"] = ""
        write_profile(invalid_title, invalid_profile)
        before = digest(invalid_title)
        result = run(invalid_title, success=False)
        assert "title must be non-empty" in result.stderr
        assert digest(invalid_title) == before

        invalid_description = copy_fixture(temp_root, "invalid-description")
        invalid_profile = load_profile(invalid_description)
        invalid_profile["homepage_research"]["themes"][0]["description"] = ""
        write_profile(invalid_description, invalid_profile)
        before = digest(invalid_description)
        result = run(invalid_description, success=False)
        assert "description must be non-empty" in result.stderr
        assert digest(invalid_description) == before

        too_few = copy_fixture(temp_root, "too-few")
        invalid_profile = load_profile(too_few)
        for theme in invalid_profile["homepage_research"]["themes"][1:]:
            theme["enabled"] = False
        write_profile(too_few, invalid_profile)
        before = digest(too_few)
        result = run(too_few, success=False)
        assert "2–6 enabled themes" in result.stderr
        assert digest(too_few) == before

        duplicate = copy_fixture(temp_root, "duplicate")
        invalid_profile = load_profile(duplicate)
        invalid_profile["homepage_research"]["themes"][1]["title"] = (
            invalid_profile["homepage_research"]["themes"][0]["title"].upper()
        )
        write_profile(duplicate, invalid_profile)
        result = run_python(duplicate, "scripts/validate_site.py", success=False)
        assert "unique case-insensitively" in result.stderr

    print("RESEARCH THEMES CONTROL TESTS PASS")
    print("- initial visible migration: PASS")
    print("- workflow inputs and safe concurrency: PASS")
    print("- no-op behavior: PASS")
    print("- heading, title and description editing: PASS")
    print("- enable and disable behavior: PASS")
    print("- invalid enabled fields and enabled-count rejection: PASS")
    print("- duplicate enabled-title rejection: PASS")
    print("- protected profile and publication state: PASS")
    print("- homepage-only accurate lastmod behavior: PASS")
    print("- validator and second-build idempotence: PASS")


if __name__ == "__main__":
    main()
