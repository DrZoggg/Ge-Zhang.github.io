"""Exact allowlist for discovery additions in historical presentation fixtures.

Each addition is checked before removal; scientific text/attributes, author order,
copy payloads and prior negative tests remain under the original strict comparison.
"""
import html
import json
import re
from sync_common import ROOT, load_master, publication_authors


def without_discovery_additions(before, after, doi):
    publications = json.loads((ROOT / 'publications.json').read_text(encoding='utf-8'))
    item = next((p for p in publications if p.get('doi','') == doi), None)
    if item is None or 'citation_title' not in before:
        return after
    def remove_once(value):
        nonlocal after
        if after.count(value) != 1: raise ValueError('Missing/changed/duplicated discovery addition')
        after = after.replace(value, '', 1)
    remove_once('<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">')
    eligible = bool(item.get('doi') and item.get('authors'))
    if eligible:
        head = [f'<link rel="cite-as" href="https://doi.org/{doi}">']
        for mime, suffix in [('application/vnd.citationstyles.csl+json','.csl.json'),('application/x-bibtex','.bib'),('application/x-research-info-systems','.ris')]:
            head.append(f'<link rel="alternate" type="{mime}" href="../citations/{item["slug"]}{suffix}">')
        remove_once('\n' + '\n'.join(head))
        remove_once(' <a class="btn" href="#cite-this-paper">Cite</a>')
    else:
        alternate = f'<link rel="alternate" type="text/markdown" href="{item["markdown_url"]}">\n'
        if alternate+'\n' not in after:raise ValueError('Missing Markdown alternate')
        after = after.replace(alternate+'\n',alternate,1)
    metadata = json.loads((ROOT/'data/citation_metadata.json').read_text(encoding='utf-8'))['papers'].get(doi,{})
    if metadata.get('eissn') and not metadata.get('issn'):
        remove_once('\n<meta name="citation_issn" content="'+metadata['eissn']+'">')
    if item['paper_geo_status'] != 'v2' and item.get('authors'):
        remove_once('<p class="paper-authors">'+html.escape('; '.join(publication_authors(item)))+'</p>')
    if item['paper_geo_status'] == 'v2':
        opening = '<section class="paper-geo-v2__section" data-v2-section="qa"'
        if after.count(opening+' id="qa">') != 1: raise ValueError('Missing Q&A navigation target')
        after=after.replace(opening+' id="qa">',opening+'>',1)
        n=before.count('<article class="paper-geo-v2__qa">')
        for i in range(1,n+1):
            new=f'<article class="paper-geo-v2__qa" id="qa-{i}">'
            if after.count(new)!=1: raise ValueError('Missing/changed Q&A answer target')
            after=after.replace(new,'<article class="paper-geo-v2__qa">',1)
    from scholarly_discovery import identifier_html, identity_links
    row=json.loads((ROOT/'data/scholarly_identifiers.json').read_text(encoding='utf-8'))['papers'].get(doi)
    if row:
        remove_once(identifier_html(row))
        expected=list(dict.fromkeys(['https://doi.org/'+doi]+[url for _,url in identity_links(row)]))
        token='"sameAs": '+json.dumps(expected,ensure_ascii=False)
        if after.count(token)!=1:raise ValueError('Changed scholarly identity links')
        after=after.replace(token,'"sameAs": '+json.dumps('https://doi.org/'+doi),1)
    return after
