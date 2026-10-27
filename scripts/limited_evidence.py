"""Source-located notes for ordinary records that have not passed full V2 review."""
import html
import json
from datetime import date
from urllib.parse import urlsplit
from sync_common import ROOT, norm_doi

PATH = ROOT / 'data/limited_evidence.json'
HEADING = 'Research context and source limits'
NOTICE = ('Limited evidence note. Only the source material identified below has been '
          'reviewed; this is not a complete Paper GEO V2 assessment.')


def plain(value, limit=1800):
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > limit:
        raise ValueError('Limited evidence requires bounded non-empty text')
    if any(c in value for c in '\r\n<>'):
        raise ValueError('Limited evidence text must be plain text')


def source_url(value):
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Limited evidence requires a public HTTPS source URL')


def validate_record(doi, record, publication):
    required = {'slug', 'evidence_status', 'reviewed_on', 'scope', 'sections', 'limitations', 'sources'}
    if set(record) != required or record['evidence_status'] != 'limited':
        raise ValueError('Unsupported limited-evidence record')
    if (doi != norm_doi(doi) or doi != publication.get('doi')
            or record['slug'] != publication.get('slug')
            or publication.get('paper_geo_status') == 'v2'
            or publication.get('type') == 'Patent'):
        raise ValueError('Limited evidence cannot change identity or replace V2/patent evidence')
    if date.fromisoformat(record['reviewed_on']).isoformat() != record['reviewed_on']:
        raise ValueError('Invalid review date')
    plain(record['scope'], 500)
    if not isinstance(record['sections'], list) or not 1 <= len(record['sections']) <= 4:
        raise ValueError('Limited evidence requires one to four sourced sections')
    for row in record['sections']:
        if set(row) != {'heading', 'text', 'source_url', 'source_locator'}:
            raise ValueError('Each limited section requires an exact source locator')
        plain(row['heading'], 100); plain(row['text']); plain(row['source_locator'], 600)
        source_url(row['source_url'])
    for key, maximum in [('limitations', 5), ('sources', 5)]:
        if not isinstance(record[key], list) or not 1 <= len(record[key]) <= maximum:
            raise ValueError('Limited evidence requires explicit limits and provenance')
    for text in record['limitations']:
        plain(text, 700)
    for row in record['sources']:
        if set(row) != {'url', 'label', 'format', 'locator'}:
            raise ValueError('Unsupported source provenance')
        source_url(row['url'])
        for key in ['label', 'format', 'locator']:
            plain(row[key], 700)


def load(publications):
    payload = json.loads(PATH.read_text(encoding='utf-8'))
    if set(payload) != {'version', 'papers'} or payload['version'] != 1 or not isinstance(payload['papers'], dict):
        raise ValueError('Unsupported limited evidence file')
    public = {p['doi']: p for p in publications if p.get('doi')}
    for doi, record in payload['papers'].items():
        if doi not in public:
            raise ValueError('Limited evidence must refer to a public DOI')
        validate_record(doi, record, public[doi])
    return payload['papers']


def render_html(record):
    if record is None:
        return ''
    esc = html.escape
    parts = ['<section id="limited-evidence" aria-labelledby="limited-evidence-title" data-evidence-scope="limited">',
             '<h2 id="limited-evidence-title">' + HEADING + '</h2>',
             '<p class="notice">' + NOTICE + '</p><p>' + esc(record['scope']) + '</p>']
    for row in record['sections']:
        parts.append('<h3>' + esc(row['heading']) + '</h3><p>' + esc(row['text']) + '</p>')
        parts.append('<p class="muted">Source: <a href="' + esc(row['source_url'], quote=True) + '">'
                     + esc(row['source_locator']) + '</a></p>')
    parts.append('<h3>Evidence limits</h3><ul>' + ''.join('<li>' + esc(x) + '</li>' for x in record['limitations']) + '</ul>')
    parts.append('<h3>Provenance</h3><ul>')
    for source in record['sources']:
        parts.append('<li><a href="' + esc(source['url'], quote=True) + '">' + esc(source['label'])
                     + '</a> — ' + esc(source['format']) + '. ' + esc(source['locator']) + '</li>')
    parts.append('</ul><p class="muted">Source review: ' + record['reviewed_on'] + '.</p></section>\n')
    return ''.join(parts)


def render_markdown(record):
    if record is None:
        return ''
    parts = ['<a id="limited-evidence"></a>', '## ' + HEADING, '', NOTICE, '', record['scope'], '']
    for row in record['sections']:
        parts += ['### ' + row['heading'], '', row['text'], '',
                  'Source: [' + row['source_locator'] + '](' + row['source_url'] + ')', '']
    parts += ['### Evidence limits', '', *['- ' + x for x in record['limitations']], '', '### Provenance', '']
    for source in record['sources']:
        parts.append('- [' + source['label'] + '](' + source['url'] + ') — ' + source['format'] + '. ' + source['locator'])
    parts += ['', 'Source review: ' + record['reviewed_on'] + '.', '']
    return '\n'.join(parts)


def validate_generated(publications):
    records = load(publications)
    for record in records.values():
        for extension, render in [('html', render_html), ('md', render_markdown)]:
            text = (ROOT / 'papers' / (record['slug'] + '.' + extension)).read_text(encoding='utf-8')
            if text.count(render(record)) != 1:
                raise ValueError('Limited evidence is missing, duplicated or inconsistent: ' + record['slug'])
    return {'limited_evidence_pages': len(records), 'full_v2_status_changed': False}
