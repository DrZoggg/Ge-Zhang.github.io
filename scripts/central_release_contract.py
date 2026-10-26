"""Exact reviewed science extension; no arbitrary baseline regeneration.

The prior 41 sources remain frozen except for 13 approved JSON-pointer values.
New source hashes come from the centrally reviewed package, not build output.
"""
import copy
import hashlib
import html
import json
import subprocess

from sync_common import ROOT

FIXTURE = ROOT / 'scripts/fixtures/central_review_release_20261026.json'
RELEASE = json.loads(FIXTURE.read_text(encoding='utf-8'))
BASE = RELEASE['base_sha']


def old(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def newline_hashes(value):
    value = value.replace(b'\r\n', b'\n')
    return {hashlib.sha256(value).hexdigest(),
            hashlib.sha256(value.replace(b'\n', b'\r\n')).hexdigest()}


def reviewed_source(slug, baseline):
    patch = RELEASE['patches'].get(slug)
    if not patch:
        return copy.deepcopy(baseline)
    raw = old('data/deep_geo/' + slug + '.json')
    if patch['gold_sha256'] not in newline_hashes(raw):
        raise ValueError('Approved source fingerprint changed: ' + slug)
    if json.loads(raw) != baseline:
        raise ValueError('Unexpected pre-release source: ' + slug)
    expected = copy.deepcopy(baseline)
    for change in patch['changes']:
        keys = change['json_pointer'].strip('/').split('/')
        target = expected
        for key in keys[:-1]:
            target = target[int(key)] if isinstance(target, list) else target[key]
        key = int(keys[-1]) if isinstance(target, list) else keys[-1]
        if target[key] != change['before']:
            raise ValueError('Reviewed before value changed: ' + change['json_pointer'])
        target[key] = change['after']
    return expected


def validate_new_source(doi, content):
    """Only the version-gate disclosure may differ from the reviewed package."""
    row = RELEASE['papers'][doi]
    original = copy.deepcopy(content)
    for change in row.get('version_disclosure_changes', []):
        keys = change['json_pointer'].strip('/').split('/')
        target = original
        for key in keys[:-1]:
            target = target[int(key)] if isinstance(target, list) else target[key]
        key = int(keys[-1]) if isinstance(target, list) else keys[-1]
        if target[key] != change['after']:
            raise ValueError('Version-gate disclosure changed: ' + doi)
        target[key] = change['before']
    raw = json.dumps(original, sort_keys=True, ensure_ascii=False,
                     separators=(',', ':')).encode('utf-8')
    if hashlib.sha256(raw).hexdigest() != row['approved_package_json_sha256']:
        raise ValueError('Centrally approved scientific content changed: ' + doi)


def restore_reviewed_text(slug, before, after):
    """Undo only approved rendered strings, with exact baseline multiplicity.

The caller still compares the entire restored document with the frozen output.
This cannot hide another scientific edit, removal, duplicate or new number.
"""
    changes = RELEASE['patches'].get(slug, {}).get('changes', [])
    pairs = dict.fromkeys((c['before'], c['after']) for c in changes)
    for source, replacement in pairs:
        variants = dict.fromkeys(((source, replacement),
                                 (html.escape(source), html.escape(replacement))))
        for prior, current in variants:
            occurrences = before.count(prior)
            if occurrences:
                if after.count(current) != occurrences:
                    raise ValueError('Reviewed rendered multiplicity changed: ' + slug)
                after = after.replace(current, prior)
    return after
