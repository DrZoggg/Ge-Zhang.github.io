"""Exact source-reviewed additions on the frozen 43-V2 / Visual 5 baseline."""
import copy
import hashlib
import json
import subprocess
from sync_common import ROOT
from central_release_contract import newline_hashes

RELEASE = json.loads((ROOT/'scripts/fixtures/autonomous_evidence_release_20261026.json').read_text(encoding='utf-8'))
BASE = RELEASE['base_sha']

def old(path):
    return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)

def reviewed_source(slug, baseline):
    return copy.deepcopy(baseline)

def restore_reviewed_text(slug, before, after):
    return after

def validate_new_source(doi, content):
    raw=json.dumps(content,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=RELEASE['papers'][doi]['canonical_json_sha256']:
        raise ValueError('Independently reviewed scientific source changed: '+doi)
