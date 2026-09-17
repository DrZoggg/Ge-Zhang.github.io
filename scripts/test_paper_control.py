import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ["python", "scripts/paper_control.py"]


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


def digest(repo):
    hasher = hashlib.sha256()
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        hasher.update(str(path.relative_to(repo)).encode())
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        errors = copy_fixture(temp_root, "errors")
        unknown = run(
            errors, "--paper", "10.9999/not-a-real-paper",
            "--deep-geo", "enable", success=False,
        )
        assert "No paper matched" in unknown.stderr
        withdrawn = run(
            errors, "--paper", "10.21203/rs.3.rs-3395716/v1",
            "--deep-geo", "enable", success=False,
        )
        assert "Withdrawn records cannot" in withdrawn.stderr
        ambiguous = run(
            errors, "--paper", "cancer", "--featured", "add", success=False,
        )
        assert "ambiguous" in ambiguous.stderr.lower()

        deep = copy_fixture(temp_root, "deep")
        target_doi = "10.1038/s41698-026-01699-1"
        run(deep, "--paper", target_doi, "--deep-geo", "enable")
        master = load(deep / "data/publications_master.json")
        paper = next(item for item in master if item.get("doi") == target_doi)
        slug = paper["slug"]
        content = deep / "data/deep_geo" / f"{slug}.json"
        assert content.is_file()
        content_hash = hashlib.sha256(content.read_bytes()).hexdigest()
        before_repeat = digest(deep)
        repeat = run(deep, "--paper", target_doi, "--deep-geo", "enable")
        assert "Repository change:** NO" in repeat.stdout
        assert digest(deep) == before_repeat
        run(deep, "--paper", target_doi, "--deep-geo", "disable")
        assert content.is_file()
        assert (deep / "papers" / f"{slug}.html").is_file()
        assert (deep / "papers" / f"{slug}.md").is_file()
        assert '<span class="badge">Deep GEO</span>' not in (
            deep / "papers" / f"{slug}.html"
        ).read_text(encoding="utf-8")
        run(deep, "--paper", target_doi, "--deep-geo", "enable")
        assert hashlib.sha256(content.read_bytes()).hexdigest() == content_hash

        featured = copy_fixture(temp_root, "featured")
        run(
            featured, "--paper", target_doi, "--featured", "add",
            "--featured-position", "1",
            "--featured-summary", "User-controlled test summary.",
        )
        entries = load(featured / "data/featured_papers.json")["papers"]
        assert entries[0]["doi"] == target_doi
        before_repeat = digest(featured)
        repeated_add = run(
            featured, "--paper", target_doi, "--featured", "add",
            "--featured-position", "1",
            "--featured-summary", "User-controlled test summary.",
        )
        assert "Repository change:** NO" in repeated_add.stdout
        assert digest(featured) == before_repeat
        run(
            featured, "--paper", "10.1016/j.ejphar.2023.175569",
            "--featured", "no_change", "--featured-position", "1",
        )
        entries = load(featured / "data/featured_papers.json")["papers"]
        assert entries[0]["doi"] == "10.1016/j.ejphar.2023.175569"
        run(featured, "--paper", target_doi, "--featured", "remove")
        entries = load(featured / "data/featured_papers.json")["papers"]
        assert target_doi not in [entry.get("doi") for entry in entries]
        assert (featured / "papers" / f"{slug}.html").is_file()
        assert (featured / "papers" / f"{slug}.md").is_file()

    print("PAPER CONTROL TESTS PASS")
    print("- unknown DOI: PASS")
    print("- withdrawn protection: PASS")
    print("- ambiguous title protection: PASS")
    print("- Deep GEO enable/disable/re-enable: PASS")
    print("- repeated Deep GEO enable no-op: PASS")
    print("- Featured add/remove/reorder: PASS")
    print("- repeated Featured add no-op: PASS")


if __name__ == "__main__":
    main()
