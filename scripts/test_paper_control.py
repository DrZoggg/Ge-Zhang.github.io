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


def run_python(repo, script):
    result = subprocess.run(
        ["python", script], cwd=repo, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + "\n" + result.stderr)
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


def token(item):
    if item.get("doi"):
        return "doi:" + item["doi"].strip().lower()
    return "slug:" + item["slug"].strip()


def controller_tokens(repo, filename):
    return {
        token(item)
        for item in load(repo / "data" / filename)["papers"]
    }


def paper_sets(repo):
    master = load(repo / "data/publications_master.json")
    public = [
        item for item in master
        if str(item.get("status") or "").casefold() != "withdrawn"
    ]
    withdrawn = [item for item in master if item not in public]
    deep_tokens = controller_tokens(repo, "deep_geo_papers.json")
    featured_tokens = controller_tokens(repo, "featured_papers.json")
    enabled = [item for item in public if token(item) in deep_tokens]
    disabled = [
        item for item in public
        if item.get("doi") and token(item) not in deep_tokens
    ]
    nonfeatured = [
        item for item in public
        if item.get("doi") and token(item) not in featured_tokens
    ]
    assert len(disabled) >= 10
    assert enabled and withdrawn and nonfeatured
    return public, withdrawn, enabled, disabled, nonfeatured


def assert_failed_without_changes(repo, args, expected):
    before = digest(repo)
    result = run(repo, *args, success=False)
    assert expected.casefold() in result.stderr.casefold(), result.stderr
    assert "Batch aborted:** yes" in result.stderr
    assert "Changed:** 0" in result.stderr
    assert "Deployment:** no" in result.stderr
    assert digest(repo) == before


def main():
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        source = copy_fixture(temp_root, "source")
        public, withdrawn, enabled, disabled, nonfeatured = paper_sets(source)

        deep = copy_fixture(temp_root, "deep")
        single = disabled[0]
        single_run = run(
            deep, "--paper", single["doi"], "--deep-geo", "enable"
        )
        assert "Deep GEO:** OFF → ON" in single_run.stdout
        assert token(single) in controller_tokens(deep, "deep_geo_papers.json")

        comma_title = next(item for item in public if "," in item.get("title", ""))
        before_comma_title = digest(deep)
        comma_title_run = run(deep, "--paper", comma_title["title"])
        assert "Batch mode:** yes" not in comma_title_run.stdout
        assert digest(deep) == before_comma_title

        before_repeat = digest(deep)
        repeated_enable = run(
            deep, "--paper", single["doi"], "--deep-geo", "enable"
        )
        assert "Repository change:** NO" in repeated_enable.stdout
        assert digest(deep) == before_repeat

        newline_targets = disabled[1:3]
        newline_run = run(
            deep,
            "--paper", "\n\n".join(item["doi"] for item in newline_targets),
            "--deep-geo", "enable",
        )
        assert "Batch mode:** yes" in newline_run.stdout
        assert "Requested papers:** 2" in newline_run.stdout
        assert "Deep GEO enabled:** 2" in newline_run.stdout

        comma_targets = disabled[3:5]
        comma_run = run(
            deep,
            "--paper", ", ".join(item["doi"] for item in comma_targets),
            "--deep-geo", "enable",
        )
        assert "Deep GEO enabled:** 2" in comma_run.stdout

        duplicate = disabled[5]
        before_count = len(controller_tokens(deep, "deep_geo_papers.json"))
        duplicate_run = run(
            deep,
            "--paper", f"{duplicate['doi']}\n{duplicate['doi']}",
            "--deep-geo", "enable",
        )
        assert "Batch mode:** yes" in duplicate_run.stdout
        assert "Deep GEO enabled:** 1" in duplicate_run.stdout
        assert len(controller_tokens(deep, "deep_geo_papers.json")) == before_count + 1

        mixed_targets = disabled[6:8]
        mixed_run = run(
            deep,
            "--paper", f"{mixed_targets[0]['doi']}\n{mixed_targets[1]['slug']}",
            "--deep-geo", "enable",
        )
        assert "Resolved papers:** 2" in mixed_run.stdout
        assert "Deep GEO enabled:** 2" in mixed_run.stdout

        still_disabled = disabled[8]
        before_disabled_noop = digest(deep)
        disabled_noop = run(
            deep, "--paper", still_disabled["doi"], "--deep-geo", "disable"
        )
        assert "Repository change:** NO" in disabled_noop.stdout
        assert digest(deep) == before_disabled_noop

        before_batch_noop = digest(deep)
        batch_noop = run(
            deep,
            "--paper", "\n".join(item["doi"] for item in newline_targets),
            "--deep-geo", "enable",
        )
        assert "Already enabled / disabled / no-op:** 2" in batch_noop.stdout
        assert "Repository change:** NO" in batch_noop.stdout
        assert digest(deep) == before_batch_noop

        batch_disable = run(
            deep,
            "--paper", "\n".join(item["doi"] for item in newline_targets),
            "--deep-geo", "disable",
        )
        assert "Deep GEO disabled:** 2" in batch_disable.stdout
        before_batch_disable_noop = digest(deep)
        batch_disable_noop = run(
            deep,
            "--paper", "\n".join(item["doi"] for item in newline_targets),
            "--deep-geo", "disable",
        )
        assert "Already enabled / disabled / no-op:** 2" in batch_disable_noop.stdout
        assert "Repository change:** NO" in batch_disable_noop.stdout
        assert digest(deep) == before_batch_disable_noop
        run(
            deep,
            "--paper", "\n".join(item["doi"] for item in newline_targets),
            "--deep-geo", "enable",
        )

        preserved = next(
            item for item in enabled
            if (deep / "data/deep_geo" / f"{item['slug']}.json").is_file()
        )
        content = deep / "data/deep_geo" / f"{preserved['slug']}.json"
        content_hash = hashlib.sha256(content.read_bytes()).hexdigest()
        run(deep, "--paper", preserved["doi"], "--deep-geo", "disable")
        assert content.is_file()
        assert (deep / "papers" / f"{preserved['slug']}.html").is_file()
        assert (deep / "papers" / f"{preserved['slug']}.md").is_file()
        assert '<span class="badge">Deep GEO</span>' not in (
            deep / "papers" / f"{preserved['slug']}.html"
        ).read_text(encoding="utf-8")
        run(deep, "--paper", preserved["doi"], "--deep-geo", "enable")
        assert hashlib.sha256(content.read_bytes()).hexdigest() == content_hash

        errors = copy_fixture(temp_root, "errors")
        valid_pair = "\n".join(item["doi"] for item in disabled[:2])
        assert_failed_without_changes(
            errors,
            (
                "--paper", f"{disabled[0]['doi']}\n10.9999/not-a-real-paper",
                "--deep-geo", "enable",
            ),
            "10.9999/not-a-real-paper",
        )
        assert_failed_without_changes(
            errors,
            (
                "--paper", f"{disabled[0]['doi']}\n{withdrawn[0]['doi']}",
                "--deep-geo", "enable",
            ),
            "Withdrawn records",
        )
        assert_failed_without_changes(
            errors,
            (
                "--paper", f"{disabled[0]['doi']}\ncancer",
                "--deep-geo", "enable",
            ),
            "ambiguous",
        )
        for featured_action in ("add", "remove"):
            assert_failed_without_changes(
                errors,
                (
                    "--paper", valid_pair,
                    "--deep-geo", "enable",
                    "--featured", featured_action,
                ),
                "Batch mode only supports Deep GEO",
            )
        assert_failed_without_changes(
            errors,
            (
                "--paper", valid_pair,
                "--deep-geo", "enable",
                "--featured-position", "1",
            ),
            "Batch mode only supports Deep GEO",
        )

        featured = copy_fixture(temp_root, "featured")
        featured_target = nonfeatured[0]
        run(
            featured,
            "--paper", featured_target["doi"],
            "--featured", "add",
            "--featured-position", "1",
            "--featured-summary", "User-controlled test summary.",
        )
        entries = load(featured / "data/featured_papers.json")["papers"]
        assert entries[0].get("doi") == featured_target["doi"]
        assert entries[0]["summary"] == "User-controlled test summary."
        before_featured_repeat = digest(featured)
        repeated_add = run(
            featured,
            "--paper", featured_target["doi"],
            "--featured", "add",
            "--featured-position", "1",
            "--featured-summary", "User-controlled test summary.",
        )
        assert "Repository change:** NO" in repeated_add.stdout
        assert digest(featured) == before_featured_repeat
        run(
            featured,
            "--paper", featured_target["doi"],
            "--featured", "no_change",
            "--featured-position", "2",
            "--featured-summary", "Updated user-controlled summary.",
        )
        entries = load(featured / "data/featured_papers.json")["papers"]
        assert entries[1].get("doi") == featured_target["doi"]
        assert entries[1]["summary"] == "Updated user-controlled summary."
        run(featured, "--paper", featured_target["doi"], "--featured", "remove")
        entries = load(featured / "data/featured_papers.json")["papers"]
        assert featured_target["doi"] not in [entry.get("doi") for entry in entries]
        assert (featured / "papers" / f"{featured_target['slug']}.html").is_file()
        assert (featured / "papers" / f"{featured_target['slug']}.md").is_file()

        stable = copy_fixture(temp_root, "stable")
        run_python(stable, "scripts/build_publications.py")
        first_build = digest(stable)
        run_python(stable, "scripts/build_publications.py")
        assert digest(stable) == first_build
        run_python(stable, "scripts/validate_site.py")

    print("PAPER CONTROL TESTS PASS")
    print("- single DOI enable and no-op: PASS")
    print("- newline/comma batch, comma-title single mode, and de-duplication: PASS")
    print("- mixed DOI + exact slug: PASS")
    print("- batch enable/disable no-op: PASS")
    print("- unknown/withdrawn/ambiguous transaction abort: PASS")
    print("- batch + Featured add/remove rejection: PASS")
    print("- Deep GEO content preservation and restore: PASS")
    print("- single-paper Featured compatibility: PASS")
    print("- build, validator, and double-build stability: PASS")


if __name__ == "__main__":
    main()
