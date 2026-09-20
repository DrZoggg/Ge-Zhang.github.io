import hashlib
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
CONTROLLER = [sys.executable, "scripts/profile_control.py"]
PROTECTED_IDENTITY_FIELDS = (
    "researcher_name",
    "researcher_name_zh",
    "given_name",
    "family_name",
    "person_id",
    "orcid",
    "external_links",
)


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
        CONTROLLER + list(args),
        cwd=repo,
        text=True,
        capture_output=True,
    )
    if success and result.returncode != 0:
        raise AssertionError(result.stdout + "\n" + result.stderr)
    if not success and result.returncode == 0:
        raise AssertionError("Command unexpectedly succeeded: " + " ".join(args))
    return result


def run_python(repo, script):
    result = subprocess.run(
        [sys.executable, script], cwd=repo, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + "\n" + result.stderr)
    return result


def digest(repo):
    hasher = hashlib.sha256()
    for path in sorted(repo.rglob("*")):
        if (
            not path.is_file()
            or "__pycache__" in path.parts
            or path.suffix == ".pyc"
        ):
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


def protected_identity(repo):
    profile = load_profile(repo)
    return {field: profile[field] for field in PROTECTED_IDENTITY_FIELDS}


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
    content = re.sub(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", f"<lastmod>{value}</lastmod>", content)
    path.write_text(content, encoding="utf-8")


def assert_identity_unchanged(repo, before):
    assert protected_identity(repo) == before


def assert_counts(repo):
    master = json.loads(
        (repo / "data/publications_master.json").read_text(encoding="utf-8")
    )
    public = [
        item
        for item in master
        if str(item.get("status") or "").casefold() != "withdrawn"
    ]
    withdrawn = [item for item in master if item not in public]
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
    assert (len(master), len(public), len(withdrawn)) == (74, 73, 1)
    assert (len(featured), len(deep_geo)) == (11, 11)
    assert len(dois) == len(set(dois))
    assert len(sitemap_lastmods(repo)) == 75


def main():
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)

        noop = copy_fixture(temp_root, "noop")
        before = digest(noop)
        result = run(noop)
        assert "Updated fields:\n- none" in result.stdout
        assert digest(noop) == before

        biography_en = copy_fixture(temp_root, "biography-en")
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        set_sitemap_lastmods(biography_en, yesterday)
        identity_before = protected_identity(biography_en)
        publication_before = publication_state_digest(biography_en)
        result = run(
            biography_en,
            "--biography-en",
            "Focused English biography for Profile Control Center testing.",
        )
        assert "- biography_en" in result.stdout
        assert load_profile(biography_en)["biography"]["en"].startswith("Focused English")
        homepage = (biography_en / "index.html").read_text(encoding="utf-8")
        assert "Focused English biography" in homepage
        lastmods = sitemap_lastmods(biography_en)
        assert lastmods["https://drgezhang.com/"] == datetime.now(timezone.utc).date().isoformat()
        assert all(
            value == yesterday
            for url, value in lastmods.items()
            if url != "https://drgezhang.com/"
        )
        assert publication_state_digest(biography_en) == publication_before
        assert_identity_unchanged(biography_en, identity_before)
        stable = digest(biography_en)
        run_python(biography_en, "scripts/build_publications.py")
        assert digest(biography_en) == stable

        biography_zh = copy_fixture(temp_root, "biography-zh")
        identity_before = protected_identity(biography_zh)
        run(
            biography_zh,
            "--biography-zh",
            "张格，专注心血管与计算生物学研究。",
        )
        assert load_profile(biography_zh)["biography"]["zh"] == "张格，专注心血管与计算生物学研究。"
        assert "张格，专注心血管与计算生物学研究。" in (
            biography_zh / "index.html"
        ).read_text(encoding="utf-8")
        assert_identity_unchanged(biography_zh, identity_before)

        affiliation = copy_fixture(temp_root, "affiliation")
        identity_before = protected_identity(affiliation)
        run(
            affiliation,
            "--primary-affiliation",
            "Profile Control Test University",
        )
        assert load_profile(affiliation)["affiliations"][0]["name"] == (
            "Profile Control Test University"
        )
        assert "Profile Control Test University" in (
            affiliation / "index.html"
        ).read_text(encoding="utf-8")
        assert_identity_unchanged(affiliation, identity_before)

        comma = copy_fixture(temp_root, "research-comma")
        identity_before = protected_identity(comma)
        run(
            comma,
            "--research-areas",
            "AI, Multi-omics, ai, Vascular Biology, Multi-omics",
        )
        assert load_profile(comma)["research_areas"] == [
            "AI",
            "Multi-omics",
            "Vascular Biology",
        ]
        assert_identity_unchanged(comma, identity_before)

        newline = copy_fixture(temp_root, "research-newline")
        identity_before = protected_identity(newline)
        run(
            newline,
            "--research-areas",
            "Cardiovascular AI\nCircadian biology\nHeart failure",
        )
        assert load_profile(newline)["research_areas"] == [
            "Cardiovascular AI",
            "Circadian biology",
            "Heart failure",
        ]
        assert_identity_unchanged(newline, identity_before)

        empty = copy_fixture(temp_root, "research-empty")
        before = digest(empty)
        result = run(empty, "--research-areas", ",,\n,", success=False)
        assert "at least one non-empty" in result.stderr
        assert digest(empty) == before

        descriptions = copy_fixture(temp_root, "descriptions")
        identity_before = protected_identity(descriptions)
        run(
            descriptions,
            "--description",
            "Profile Control Center test description.",
            "--disambiguating-description",
            "Profile Control Center test disambiguation.",
        )
        profile = load_profile(descriptions)
        assert profile["description"] == "Profile Control Center test description."
        assert profile["disambiguating_description"] == (
            "Profile Control Center test disambiguation."
        )
        assert_identity_unchanged(descriptions, identity_before)
        run_python(descriptions, "scripts/validate_site.py")
        assert_counts(descriptions)

    print("PROFILE CONTROL TESTS PASS")
    print("- no-op and no generated diff: PASS")
    print("- English and Chinese biography updates: PASS")
    print("- primary affiliation update: PASS")
    print("- comma/newline parsing and order-preserving de-duplication: PASS")
    print("- empty parsed research areas rejection: PASS")
    print("- protected identity fields: PASS")
    print("- selective accurate lastmod behavior: PASS")
    print("- 75 sitemap URLs and protected publication counts: PASS")
    print("- validator and second-build idempotence: PASS")


if __name__ == "__main__":
    main()
