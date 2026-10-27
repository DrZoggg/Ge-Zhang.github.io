"""Exact source-reviewed additions on the frozen 43-V2 / Visual 5 baseline."""
import copy
import hashlib
import json
import subprocess
from sync_common import ROOT
from central_release_contract import newline_hashes
import author_account_release_contract as author_release

RELEASE = json.loads((ROOT/'scripts/fixtures/autonomous_evidence_release_20261026.json').read_text(encoding='utf-8'))
BASE = RELEASE['base_sha']
if set(RELEASE['papers']) & set(author_release.RELEASE['papers']):
    raise ValueError('Author-account additions cannot overwrite historical scientific approvals')
RELEASE['papers'].update(copy.deepcopy(author_release.RELEASE['papers']))
RELEASE['content_dates'] = {url: author_release.CONTENT_DATE for url in author_release.dated_urls()}

def old(path):
    return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)

def reviewed_source(slug, baseline):
    return copy.deepcopy(baseline)

def restore_reviewed_text(slug, before, after):
    if slug in RELEASE.get('non_v2_notes', {}):
        import patent_evidence
        row = RELEASE['non_v2_notes'][slug]
        if row['content_sha256'] not in newline_hashes((ROOT/row['path']).read_bytes()):
            raise ValueError('Reviewed patent note changed')
        content = json.loads((ROOT/row['path']).read_text(encoding='utf-8'))
        block = (patent_evidence.render_html(content) if before.startswith('<!doctype')
                 else patent_evidence.render_markdown(content) + '\n')
        if block in before or after.count(block) != 1:
            raise ValueError('Patent note must be one exact reviewed addition')
        return after.replace(block, '', 1)
    return after

def validate_new_source(doi, content):
    raw=json.dumps(content,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=RELEASE['papers'][doi]['canonical_json_sha256']:
        raise ValueError('Independently reviewed scientific source changed: '+doi)
