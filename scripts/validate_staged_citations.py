"""Check citation delivery in the clean Pages artifact before upload."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from citation_common import CITATIONS_DIR, citation_files, citation_record, load_citation_metadata
from site_common import load_site_config
from sync_common import is_withdrawn, load_master
from validate_site import validate_citations


class DownloadLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            path = unquote(urlsplit(href).path)
            if path.endswith((".bib", ".ris", ".csl.json")):
                self.links.append(href)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def staged_target(stage, page_url, href):
    url = urlsplit(urljoin(page_url, href))
    origin = urlsplit(page_url)
    require((url.scheme, url.netloc) == (origin.scheme, origin.netloc),
            f"Citation link is not same-origin: {href}")
    path = unquote(url.path)
    require(not url.query and not url.fragment and "\\" not in path,
            f"Unsafe citation link: {href}")
    target = (stage / path.lstrip("/")).resolve()
    require(target.is_relative_to(stage / "citations"), f"Unsafe citation path: {href}")
    return target.relative_to(stage).as_posix()


def validate_staged(stage):
    stage = Path(stage).resolve()
    public = [item for item in load_master() if not is_withdrawn(item)]
    config = load_site_config()
    counts = validate_citations(public, config)
    enhancements = load_citation_metadata(public)
    expected_pages = {f"{item['slug']}.html" for item in public}
    actual_pages = {path.relative_to(stage / "papers").as_posix()
                    for path in (stage / "papers").rglob("*.html")}
    require(actual_pages == expected_pages, "Staged public paper inventory differs from current build")
    expected_files = set()
    for item in public:
        slug = item["slug"]
        page_url = f"{config['site_url']}/papers/{slug}.html"
        parser = DownloadLinks()
        parser.feed((stage / "papers" / f"{slug}.html").read_text(encoding="utf-8"))
        links = [staged_target(stage, page_url, href) for href in parser.links]
        record = citation_record(item, enhancements, config["site_url"])
        expected = {f"citations/{name}" for name in citation_files(record).values()} if record else set()
        require(set(links) == expected and len(links) == len(expected),
                f"Staged citation links differ from eligibility/source for {slug}")
        expected_files.update(expected)
    actual_files = {path.relative_to(stage).as_posix()
                    for path in (stage / "citations").rglob("*") if path.is_file()}
    require(actual_files == expected_files,
            f"Missing/unexpected staged citations: {sorted(actual_files ^ expected_files)}")
    for name in sorted(expected_files):
        target = stage / name
        require(target.resolve().is_relative_to(stage / "citations"), f"Unsafe staged file: {name}")
        require(target.read_bytes() == (CITATIONS_DIR / target.name).read_bytes(),
                f"Staged citation differs from generated source: {name}")
    return {**counts, "files": len(expected_files), "paper_html": len(expected_pages)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path, nargs="?", default=Path("_site"))
    print("STAGED CITATIONS PASS:", validate_staged(parser.parse_args().stage))
