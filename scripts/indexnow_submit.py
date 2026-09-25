import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "indexnow_config.json"
SITEMAP_PATH = ROOT / "sitemap.xml"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
CANONICAL_HOST = "drgezhang.com"
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
KEY_PATTERN = re.compile(r"[A-Za-z0-9-]{8,128}")
HTML_PATH_PATTERN = re.compile(
    r"/(?:[A-Za-z0-9._~-]+/)*[A-Za-z0-9._~-]+\.html"
)


class IndexNowError(RuntimeError):
    pass


@dataclass(frozen=True)
class SitemapChanges:
    added: tuple
    updated: tuple
    deleted: tuple

    @property
    def urls(self):
        return tuple(sorted((*self.added, *self.updated, *self.deleted)))


def append_summary(lines):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines).rstrip() + "\n")


def validate_config(config, key_root=ROOT):
    if not isinstance(config, dict):
        raise IndexNowError("IndexNow config must be a JSON object.")
    if not isinstance(config.get("enabled"), bool):
        raise IndexNowError("IndexNow config enabled must be a boolean.")
    host = config.get("host")
    if host != CANONICAL_HOST:
        raise IndexNowError(f"IndexNow host must be {CANONICAL_HOST}.")
    key = config.get("key")
    if not isinstance(key, str) or KEY_PATTERN.fullmatch(key) is None:
        raise IndexNowError(
            "IndexNow key must contain 8–128 letters, numbers, or dashes."
        )
    expected_location = f"https://{host}/{key}.txt"
    if config.get("key_location") != expected_location:
        raise IndexNowError(
            "IndexNow key_location must be the canonical HTTPS root key URL."
        )
    key_path = Path(key_root) / f"{key}.txt"
    if not key_path.is_file():
        raise IndexNowError(f"IndexNow root key file is missing: {key_path.name}")
    key_content = key_path.read_text(encoding="utf-8")
    if key_content not in {key, key + "\n"}:
        raise IndexNowError("IndexNow root key file content does not match the key.")
    return config


def load_config(path=CONFIG_PATH, key_root=ROOT):
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IndexNowError(f"Cannot read IndexNow config: {exc}") from exc
    return validate_config(config, key_root=key_root)


def validate_public_html_url(url, host):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != host
        or parsed.query
        or parsed.fragment
        or parsed.path in {"/404.html", "/index.html"}
        or (parsed.path != "/" and HTML_PATH_PATTERN.fullmatch(parsed.path) is None)
    ):
        raise IndexNowError(
            f"Sitemap URL is not a canonical public HTML URL on {host}: {url}"
        )
    return url


def parse_sitemap_text(content, host, label="sitemap"):
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise IndexNowError(f"Cannot parse {label}: {exc}") from exc
    namespace = f"{{{SITEMAP_NAMESPACE}}}"
    if root.tag != f"{namespace}urlset":
        raise IndexNowError(f"{label} does not use the canonical sitemap namespace.")

    entries = {}
    for entry in root.findall(f"{namespace}url"):
        loc_nodes = entry.findall(f"{namespace}loc")
        lastmod_nodes = entry.findall(f"{namespace}lastmod")
        if len(loc_nodes) != 1 or len(lastmod_nodes) != 1:
            raise IndexNowError(
                f"Each {label} entry must have exactly one loc and one lastmod."
            )
        url = str(loc_nodes[0].text or "").strip()
        lastmod = str(lastmod_nodes[0].text or "").strip()
        validate_public_html_url(url, host)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod):
            raise IndexNowError(f"Invalid lastmod in {label} for {url}: {lastmod!r}")
        try:
            parsed_lastmod = date.fromisoformat(lastmod)
        except ValueError as exc:
            raise IndexNowError(
                f"Invalid lastmod in {label} for {url}: {lastmod}"
            ) from exc
        if parsed_lastmod.isoformat() != lastmod:
            raise IndexNowError(f"Invalid lastmod in {label} for {url}: {lastmod}")
        if url in entries:
            raise IndexNowError(f"Duplicate URL in {label}: {url}")
        entries[url] = lastmod
    return entries


def detect_changes(previous, current):
    return detect_changes_with_html(previous, current, ())


def canonical_html_path(url):
    path = urlsplit(url).path
    return "index.html" if path == "/" else path.lstrip("/")


def detect_changes_with_html(previous, current, changed_html_paths):
    previous_urls = set(previous)
    current_urls = set(current)
    current_by_path = {
        canonical_html_path(url): url for url in current_urls
    }
    changed_urls = {
        current_by_path[path]
        for path in changed_html_paths
        if path in current_by_path and path != "404.html"
    }
    return SitemapChanges(
        added=tuple(sorted(current_urls - previous_urls)),
        updated=tuple(
            sorted(
                url
                for url in previous_urls & current_urls
                if previous[url] != current[url] or url in changed_urls
            )
        ),
        deleted=tuple(sorted(previous_urls - current_urls)),
    )


def changed_public_html_paths(previous_ref):
    result = subprocess.run(
        [
            "git", "diff", "--no-renames", "--name-only", "-z",
            "--diff-filter=AM", previous_ref, "HEAD", "--", "*.html",
        ],
        cwd=ROOT,
        capture_output=True,
    )
    if result.returncode != 0:
        diagnostic = re.sub(r"\s+", " ", result.stderr.decode("utf-8", errors="replace"))
        raise IndexNowError(
            f"Cannot diff public HTML from git ref {previous_ref!r}: {diagnostic.strip()[:300]}"
        )
    return tuple(sorted(set(result.stdout.decode("utf-8").rstrip("\0").split("\0")) - {""}))


def sitemap_at_git_ref(ref):
    result = subprocess.run(
        ["git", "show", f"{ref}:sitemap.xml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        diagnostic = re.sub(r"\s+", " ", result.stderr).strip()[:300]
        raise IndexNowError(
            f"Cannot read the previous sitemap from git ref {ref!r}: {diagnostic}"
        )
    return result.stdout


def safe_response_text(raw, key):
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"\s+", " ", text).strip().replace(key, "[redacted]")
    return text[:500]


def submit_urls(config, urls, opener=urllib.request.urlopen):
    if not urls:
        raise IndexNowError("Refusing to send an empty IndexNow request.")
    if len(urls) > 10000:
        raise IndexNowError("IndexNow bulk requests may contain at most 10,000 URLs.")
    for url in urls:
        validate_public_html_url(url, config["host"])
    payload = {
        "host": config["host"],
        "key": config["key"],
        "keyLocation": config["key_location"],
        "urlList": list(urls),
    }
    request = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Ge-Zhang-Academic-Hub-IndexNow/1.0",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=30) as response:
            status = response.getcode()
            body = response.read(2048)
    except urllib.error.HTTPError as exc:
        diagnostic = safe_response_text(exc.read(2048), config["key"])
        suffix = f" — {diagnostic}" if diagnostic else ""
        raise IndexNowError(f"IndexNow API HTTP {exc.code}{suffix}") from exc
    except urllib.error.URLError as exc:
        raise IndexNowError(f"IndexNow API network error: {exc.reason}") from exc
    if status not in {200, 202}:
        diagnostic = safe_response_text(body, config["key"])
        suffix = f" — {diagnostic}" if diagnostic else ""
        raise IndexNowError(f"IndexNow API HTTP {status}{suffix}")
    return status


def process_entries(config, previous, current, submitter=submit_urls, dry_run=False,
                    changed_html_paths=()):
    changes = detect_changes_with_html(previous, current, changed_html_paths)
    print(
        "IndexNow URL changes: "
        f"added={len(changes.added)}, updated={len(changes.updated)}, "
        f"deleted={len(changes.deleted)}."
    )
    if not changes.urls:
        print("INDEXNOW NO-OP: no changed canonical public HTML URLs.")
        return {"changes": changes, "submitted": False, "status": None}
    if dry_run:
        print(f"INDEXNOW DRY RUN: {len(changes.urls)} URL(s) would be submitted.")
        return {"changes": changes, "submitted": False, "status": None}
    status = submitter(config, changes.urls)
    print(f"INDEXNOW ACCEPTED: HTTP {status}; submitted={len(changes.urls)}.")
    return {"changes": changes, "submitted": True, "status": status}


def run_submission(
    config_path=CONFIG_PATH,
    current_sitemap=SITEMAP_PATH,
    previous_ref="HEAD^",
    previous_sitemap=None,
    dry_run=False,
    submitter=submit_urls,
):
    config_path = Path(config_path)
    config = load_config(config_path, key_root=config_path.resolve().parents[1])
    if not config["enabled"]:
        print("INDEXNOW NO-OP: notifications are disabled.")
        return {"changes": SitemapChanges((), (), ()), "submitted": False, "status": None}
    current_text = Path(current_sitemap).read_text(encoding="utf-8")
    previous_text = (
        Path(previous_sitemap).read_text(encoding="utf-8")
        if previous_sitemap
        else sitemap_at_git_ref(previous_ref)
    )
    previous = parse_sitemap_text(previous_text, config["host"], "previous sitemap")
    current = parse_sitemap_text(current_text, config["host"], "current sitemap")
    return process_entries(
        config, previous, current, submitter=submitter, dry_run=dry_run,
        changed_html_paths=changed_public_html_paths(previous_ref),
    )


def parser():
    result = argparse.ArgumentParser(
        description="Submit changed canonical public HTML URLs to IndexNow."
    )
    result.add_argument("--config", default=str(CONFIG_PATH))
    result.add_argument("--current-sitemap", default=str(SITEMAP_PATH))
    previous = result.add_mutually_exclusive_group()
    previous.add_argument(
        "--previous-ref",
        default=os.environ.get("INDEXNOW_PREVIOUS_REF", "HEAD^"),
    )
    previous.add_argument("--previous-sitemap")
    result.add_argument("--dry-run", action="store_true")
    return result


def main():
    args = parser().parse_args()
    try:
        result = run_submission(
            config_path=args.config,
            current_sitemap=args.current_sitemap,
            previous_ref=args.previous_ref,
            previous_sitemap=args.previous_sitemap,
            dry_run=args.dry_run,
        )
        changes = result["changes"]
        request_status = (
            f"HTTP {result['status']}" if result["submitted"] else "skipped"
        )
        append_summary(
            [
                "## IndexNow",
                f"- Added URLs: {len(changes.added)}",
                f"- Updated URLs: {len(changes.updated)}",
                f"- Deleted URLs: {len(changes.deleted)}",
                f"- API request: {request_status}",
            ]
        )
    except (IndexNowError, OSError) as exc:
        append_summary(["## IndexNow", f"- FAILED: {exc}"])
        print(f"INDEXNOW FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
