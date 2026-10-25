"""Reviewed DOI-specific labels for homepage cards; never infer from author order."""
import html
import json
from datetime import date
from urllib.parse import urlsplit

from sync_common import norm_doi

ROLES = {'First author', 'Co-first author', 'Corresponding author', 'Co-author'}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate author-role key: ' + key)
        result[key] = value
    return result


def load_role_records(path, expected_orcid):
    data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_object)
    if data.get('version') != 1 or data.get('researcher_orcid') != expected_orcid:
        raise ValueError('Homepage author-role identity/version mismatch')
    records = data.get('papers')
    if not isinstance(records, dict):
        raise ValueError('Homepage author roles must be indexed by DOI')
    for doi, record in records.items():
        if doi != norm_doi(doi) or not doi.startswith('10.'):
            raise ValueError('Author-role DOI must be normalized: ' + doi)
        if record.get('status') not in {'verified', 'pending'}:
            raise ValueError('Explicit author-role verification status required: ' + doi)
        roles = record.get('roles')
        if not isinstance(roles, list) or any(r not in ROLES for r in roles) or len(set(roles)) != len(roles):
            raise ValueError('Invalid or duplicate author roles: ' + doi)
        if {'First author', 'Co-first author'} <= set(roles) or ('Co-author' in roles and len(roles) > 1):
            raise ValueError('Conflicting author roles: ' + doi)
        if record['status'] == 'verified':
            if not roles or not record.get('verification_basis') or not record.get('sources'):
                raise ValueError('Verified author roles require evidence: ' + doi)
            date.fromisoformat(record.get('verified_on', ''))
            for source in record['sources']:
                url = urlsplit(source.get('url', ''))
                if url.scheme != 'https' or not url.netloc or not source.get('locator'):
                    raise ValueError('Authorship source URL and locator required: ' + doi)
    return records


def render_role_labels(doi, records):
    doi = norm_doi(doi)
    record = records.get(doi)
    if not record or record['status'] != 'verified':
        return ''
    source = html.escape(record['sources'][0]['url'], quote=True)
    labels = ''.join(f'<a class="author-role" href="{source}" title="Publication authorship source">{html.escape(role)}</a>' for role in record['roles'])
    return (f'<div class="author-roles" data-author-role-doi="{html.escape(doi, quote=True)}" '
            f'aria-label="Ge Zhang author roles">{labels}</div>')
