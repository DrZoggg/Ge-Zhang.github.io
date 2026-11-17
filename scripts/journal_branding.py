"""Local, decorative journal/publisher marks for Selected Research cards."""

import html
import json
import re

from sync_common import ROOT


def load_journal_branding():
    path = ROOT / "data/journal_branding.json"
    return json.loads(path.read_text(encoding="utf-8"))["journals"]


def render_journal_mark(journal, branding):
    record = branding.get(journal, {})
    abbreviation = record.get("abbreviation") or "".join(
        word[0] for word in re.findall(r"[A-Za-z0-9]+", journal)
        if word.lower() not in {"of", "the", "and", "in", "for"}
    )[:4].upper() or "J"
    asset = record.get("asset", "")
    # Assets are build-time local files. A future, unmapped journal still has a
    # plain typographic identifier; it is never assigned another journal's mark.
    if not asset.startswith("assets/journal-logos/") or ".." in asset or not (ROOT / asset).is_file():
        return (
            '<span class="journal-brand journal-brand--fallback" aria-hidden="true" '
            'data-brand-kind="neutral-abbreviation">'
            + html.escape(abbreviation) + '</span>'
        )
    surface = "dark" if record.get("surface") == "dark" else "light"
    shape = "icon" if record.get("shape") == "icon" else "wordmark"
    brand = html.escape(record["brand"], quote=True)
    return (
        f'<span class="journal-brand journal-brand--{surface} journal-brand--{shape}" '
        f'aria-hidden="true" data-brand="{brand}" data-brand-kind="{record["kind"]}">'
        f'<img src="{html.escape(asset, quote=True)}" alt="" '
        f'width="{int(record["width"])}" height="{int(record["height"])}" '
        'loading="lazy" decoding="async"></span>'
    )
