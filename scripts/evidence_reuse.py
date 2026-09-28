"""Source-preserving evidence actions, shared by HTML controls and exports."""
import html
import json
import re
from evidence_discovery import ui


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
