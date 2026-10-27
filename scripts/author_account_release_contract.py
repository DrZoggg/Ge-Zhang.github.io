"""Exact author-account source approvals on the unchanged 55-V2 baseline.

Gold hashes use LF-normalized file bytes. Limited-note hashes use canonical
JSON (sorted keys, UTF-8, no extra separators). Historical fixtures stay intact.
"""
import copy
from functools import lru_cache
import hashlib
import json
import re
import subprocess
from sync_common import ROOT

FIXTURE = ROOT / 'scripts/fixtures/author_account_release_20261027.json'
RELEASE = json.loads(FIXTURE.read_text(encoding='utf-8'))
BASE = RELEASE['base_sha']
CONTENT_DATE = RELEASE.get('content_date', '2026-10-27')
ICM = '10.1016/j.intimp.2024.112574'
HMG = '10.1093/hmg/ddae189'
BACKLINK = re.compile(r'<aside\b[^>]*\bid="reviewed-backlinks"[^>]*>.*?</aside>', re.S)
BACKLINK_ONLY = {
    'time-cart', 'doi-10-3389-fpubh-2025-1521372',
    'doi-10-1038-s41598-025-98859-3', 'icd-cart',
}

if BASE != 'e388001d7b3de97c32931a372fc17e9d66644206':
    raise ValueError('Author-account release requires the reviewed 55-V2 baseline')
if RELEASE['public_works'] != 77 or RELEASE['baseline_v2'] != 55:
    raise ValueError('Unexpected author-account baseline inventory')
if set(RELEASE['limited_evidence_updates']) != {ICM, HMG}:
    raise ValueError('Only the reviewed ICM and HMG limited notes may change')
if not RELEASE['papers'] or set(RELEASE['papers']) & set(RELEASE['limited_evidence_updates']):
    raise ValueError('New V2 works and limited-note updates must be explicit and disjoint')
if (set(RELEASE.get('backlink_only_slugs', [])) != BACKLINK_ONLY
        or len(RELEASE['backlink_only_slugs']) != len(BACKLINK_ONLY)):
    raise ValueError('Only the four reviewed incoming-link navigation pages may change')
for group in ('papers', 'limited_evidence_updates'):
    for doi, row in RELEASE[group].items():
        if doi != doi.lower() or not re.fullmatch(r'[a-z0-9-]+', row['slug']):
            raise ValueError('Release identity must use the existing normalized DOI and slug')
        keys = ['content_sha256'] + (['canonical_json_sha256'] if group == 'papers' else [])
        for key in keys:
            if not re.fullmatch(r'[0-9a-f]{64}', row.get(key, '')):
                raise ValueError('Pending or invalid approved hash: ' + doi + ' ' + key)


@lru_cache(maxsize=None)
def old(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT).replace(b'\r\n', b'\n')


def now(path):
    return (ROOT / path).read_bytes().replace(b'\r\n', b'\n')


def canonical_hash(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def with_upgrades(items):
    """Only named status fields may differ; preserve every identity and ordering field."""
    expected = copy.deepcopy(items)
    present = {p.get('doi') for p in expected}
    if not set(RELEASE['papers']) <= present:
        raise ValueError('An approved upgrade is absent from the original public inventory')
    for item in expected:
        if item.get('doi') in RELEASE['papers']:
            if item['slug'] != RELEASE['papers'][item['doi']]['slug']:
                raise ValueError('Approved DOI/slug relation changed')
            item['paper_geo_status'] = 'v2'
    return expected


def reviewed_note_rows(historical_rows):
    expected = copy.deepcopy(historical_rows)
    for doi in RELEASE['papers']:
        if doi not in expected:
            raise ValueError('Upgrade must replace an existing reviewed limited note: ' + doi)
        del expected[doi]
    for doi, row in RELEASE['limited_evidence_updates'].items():
        if doi not in expected or expected[doi]['slug'] != row['slug']:
            raise ValueError('Limited-note identity changed: ' + doi)
        expected[doi] = copy.deepcopy(row)
    return expected


def new_slugs():
    return {r['slug'] for r in RELEASE['papers'].values()}


def changed_slugs():
    return new_slugs() | {r['slug'] for r in RELEASE['limited_evidence_updates'].values()}


@lru_cache(maxsize=2)
def backlink_context(baseline=False):
    """Compute exact old/current blocks using the existing relationship generator."""
    from scholarly_discovery import reviewed_backlinks
    read = old if baseline else now
    items = json.loads(read('publications.json'))
    sources = {p['doi']: json.loads(read('data/deep_geo/' + p['slug'] + '.json'))
               for p in items if p['paper_geo_status'] == 'v2'}
    return {p['slug']: p for p in items}, reviewed_backlinks(items, sources)


def backlink_core(slug, page, baseline=False):
    """Strip only a validated exact navigation block on an explicitly named page."""
    from scholarly_discovery import validate_backlink_html
    if slug not in BACKLINK_ONLY:
        raise ValueError('Unapproved relationship-only page: ' + slug)
    items, rows = backlink_context(baseline)
    validate_backlink_html(page, rows.get(items[slug].get('doi')))
    return BACKLINK.sub('', page)


DERIVED_PATHS = frozenset({
    'publications.json', 'paper_index.json', 'publication_inventory.csv',
    'publications.html', 'research/questions.html', 'research/questions.json',
    'assets/evidence-search.json', 'sitemap.xml',
})


def allowed_production_paths():
    paths = set(DERIVED_PATHS) | {'data/limited_evidence.json', 'data/question_index.json'}
    paths.update('data/deep_geo/' + slug + '.json' for slug in new_slugs())
    paths.update('assets/evidence/' + slug + '.csv' for slug in new_slugs())
    paths.update('papers/' + slug + '.' + ext for slug in changed_slugs() for ext in ('html', 'md'))
    paths.update('papers/' + slug + '.html' for slug in BACKLINK_ONLY)
    return paths


def dated_urls():
    return {f'https://drgezhang.com/papers/{slug}.html' for slug in changed_slugs() | BACKLINK_ONLY} | {
        'https://drgezhang.com/publications.html',
        'https://drgezhang.com/research/questions.html',
    }


def changed_paths(*paths):
    return set(subprocess.check_output(
        ['git', '-c', 'core.quotepath=false', 'diff', '--name-only', BASE, '--', *paths],
        cwd=ROOT, text=True, encoding='utf-8').splitlines())
