"""Source-preserving evidence actions, shared by HTML controls and exports."""
import html
import csv
import hashlib
import io
import json
import re
from evidence_discovery import ui
from paper_discovery import scientific_content

EXPORT_NOTICE = ('Study-level author-maintained evidence summary. '
                 'Not participant-level data and not a ready-to-pool meta-analysis dataset. '
                 'For formal citation, use the original article DOI.')
CSV_SAFETY = ('Formula safety: cells starting with =, +, -, @ (after leading whitespace), '
              'or tab/CR/LF are prefixed with an apostrophe. Treat all cells as text; '
              'remove only that safety prefix when recovering the original string.')
CSV_FIELDS = ['doi','paper_title','canonical_paper_url','finding_url','finding_id','record_kind',
              'study_design','evidence_type','claim','context','reported_evidence','source_locator',
              'scope_does_not_establish','limitations','single_finding_matrix_scope',
              'scientific_source_sha256','export_notice','csv_safety']


def csv_safe(value):
    value = str(value)
    if value.startswith(('\t','\r','\n')) or value.lstrip().startswith(('=','+','-','@')):
        return "'" + value
    return value


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def evidence_rows(publication, content, canonical):
    # Runtime-only resolved related-research helpers are not scientific source fields.
    source = scientific_content({k:v for k,v in content.items() if not k.startswith('_')})
    fingerprint = hashlib.sha256(canonical_json(source).encode('utf-8')).hexdigest()
    for f in content['key_findings']:
        yield {'doi':content['doi'],'paper_title':publication['title'],'canonical_paper_url':canonical,
               'finding_url':canonical+'#'+f['id'].lower(),'finding_id':f['id'],
               'record_kind':'argument' if is_argument(content) else 'finding',
               'study_design':content['study_profile']['study_design'],
               'evidence_type':content['study_profile']['evidence_type'],
               'claim':f['claim'],'context':f['context'],'reported_evidence':canonical_json(f['evidence']),
               'source_locator':f['source_locator'],
               'scope_does_not_establish':canonical_json(content['evidence_scope']['does_not_establish']),
               'limitations':canonical_json(content['limitations']),
               'single_finding_matrix_scope':canonical_json([r['scope'] for r in content.get('citation_layer',{}).get('evidence_matrix',[]) if r.get('evidence_refs')==[f['id']]]),
               'scientific_source_sha256':fingerprint,'export_notice':EXPORT_NOTICE,'csv_safety':CSV_SAFETY}


def render_csv(publication, content, canonical):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream,fieldnames=CSV_FIELDS,lineterminator='\n')
    writer.writeheader()
    for row in evidence_rows(publication,content,canonical):
        writer.writerow({k:csv_safe(v) for k,v in row.items()})
    return stream.getvalue()


def export_html(publication, content):
    return ui('<section class="evidence-export"><h2>Study-level evidence table</h2><p>'+EXPORT_NOTICE+'</p>'
              '<a download data-evidence-export="'+html.escape(content['doi'],quote=True)+'" href="../assets/evidence/'
              +html.escape(publication['slug'],quote=True)+'.csv">Download study-level evidence CSV (UTF-8)</a>'
              '<p>'+CSV_SAFETY+'</p></section>')


def is_argument(content):
    p = content['study_profile']
    return p['profile_type'] == 'narrative_review' and p.get('narrative_genre') in ('perspective', 'correspondence')


def finding_payload(publication, content, canonical, finding):
    kind = 'Argument' if is_argument(content) else 'Finding'
    scopes = [row['scope'] for row in content.get('citation_layer', {}).get('evidence_matrix', [])
              if row.get('evidence_refs') == [finding['id']]]
    parts = ['Author-maintained evidence summary — not a quotation from the publication.',
             'Paper title: ' + publication['title'], kind + ' ID: ' + finding['id'],
             'Claim: ' + finding['claim'], 'Context: ' + finding['context'], 'Reported evidence:']
    parts += [row['label'] + ': ' + row['value'] for row in finding['evidence']]
    parts += ['Source locator: ' + finding['source_locator']]
    if scopes:
        parts += ['Single-' + kind.lower() + ' matrix scope:', *scopes]
    parts += ['Does Not Establish:', *content['evidence_scope']['does_not_establish'],
              'Original article DOI: https://doi.org/' + content['doi'],
              'Finding URL: ' + canonical + '#' + finding['id'].lower()]
    return '\n'.join(parts)


def enhance_html(markup, publication, content, canonical):
    for section, anchor in [('author-summary','ev-summary'),('key-findings','ev-findings'),('evidence-scope','ev-scope')]:
        markup = markup.replace('data-v2-section="' + section + '"',
                                'data-v2-section="' + section + '" id="' + anchor + '"', 1)
    for finding in content['key_findings']:
        anchor = finding['id'].lower()
        payload = {'doi':content['doi'], 'finding_id':finding['id'],
                   'text':finding_payload(publication,content,canonical,finding)}
        safe = json.dumps(payload, ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
        controls = ui('<div class="evidence-actions"><a href="' + html.escape(canonical+'#'+anchor,quote=True)
                      + '">Permalink to ' + html.escape(finding['id']) + '</a> '
                      + '<button type="button" hidden data-copy-evidence="ev-copy-' + anchor + '">Copy evidence with source</button>'
                      + '<span class="evidence-copy-status" role="status" aria-live="polite"></span>'
                      + '<textarea hidden readonly class="evidence-copy-fallback" aria-label="Complete evidence with source for manual copying"></textarea>'
                      + '<script type="application/json" id="ev-copy-' + anchor + '">' + safe + '</script></div>')
        pattern = r'(<article\b[^>]*data-key-finding-id="' + re.escape(finding['id']) + r'"[^>]*>)(.*?)(</article>)'
        def insert(match):
            opening = match[1]
            if not re.search(r'\sid="', opening):
                opening = opening[:-1] + ' id="' + anchor + '">'
            return opening + match[2] + controls + match[3]
        markup, count = re.subn(pattern, insert, markup, count=1, flags=re.S)
        if count != 1:
            raise ValueError('Missing unique finding for evidence action: ' + finding['id'])
    return markup


def navigation(content, has_citation):
    links = [('#ev-summary','Evidence summary'),('#ev-findings','Key arguments' if is_argument(content) else 'Key findings'),('#ev-scope','Evidence scope')]
    if has_citation:
        links.append(('#cite-this-paper','Cite the original paper'))
    return ui('<nav class="evidence-navigation" aria-label="Paper evidence navigation">'
              + ' · '.join('<a href="'+url+'">'+label+'</a>' for url,label in links) + '</nav>')
