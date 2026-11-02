"""Source-bound navigation from research intents to existing reviewed evidence.

This layer contains questions and references, not a second answer store. Work and
Q&A identities are resolved against the unchanged question-discovery export.
"""
import copy
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from sync_common import ROOT

CONFIG_PATH = 'data/scientific_discovery_intents.json'
_ID = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*')
_DOI = re.compile(r'10\.\d{4,9}/[^\s<>"]+', re.I)


def _keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError('Intent navigation fields differ: ' + label)


def _text(value, label):
    if (not isinstance(value, str) or not value or value != value.strip()
            or any(ord(char) < 32 for char in value)):
        raise ValueError('Intent navigation requires plain non-empty text: ' + label)
    return value


def _identifier(value, label):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError('Unsafe intent navigation ID: ' + label)
    return value


def _unique(values, label):
    if (not isinstance(values, list)
            or any(not isinstance(value, str) or not value or value != value.strip() for value in values)
            or len(values) != len(set(values))):
        raise ValueError('Intent navigation list is invalid or duplicated: ' + label)
    return values


def _https(value, label):
    value = _text(value, label)
    try:
        url = urlsplit(value)
        valid = url.scheme == 'https' and url.hostname and not url.username and not url.password
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('Intent navigation URL requires public HTTPS: ' + label)
    return value


def _lookup(discovery):
    works = {work['id']: work for work in discovery['works']}
    questions = {question['id']: question for question in discovery['all_questions']}
    if (len(works) != len(discovery['works'])
            or len(questions) != len(discovery['all_questions'])):
        raise ValueError('Duplicate underlying intent work or question identity')
    return works, questions


def build_intent_layer(discovery, root=ROOT):
    """Validate an optional navigation controller and resolve its reference IDs.

    Existing fixture roots without this optional controller keep the old export
    contract. The production controller is deterministic; no network is involved.
    """
    path = Path(root) / CONFIG_PATH
    if not path.exists():
        return {}
    config = json.loads(path.read_text(encoding='utf-8'))
    _keys(config, ('version', 'sources', 'intents'), 'controller')
    if type(config['version']) is not int or config['version'] != 1:
        raise ValueError('Unsupported intent navigation version')
    if (not isinstance(config['sources'], list) or not config['sources']
            or not isinstance(config['intents'], list) or not config['intents']):
        raise ValueError('Intent sources and intents must be non-empty arrays')
    works, questions = _lookup(discovery)
    source_ids, sources = set(), []
    for source in config['sources']:
        _keys(source, ('id', 'title', 'doi', 'url', 'year', 'locator'), 'review source')
        sid = _identifier(source['id'], 'source')
        if sid in source_ids:
            raise ValueError('Duplicate intent review-source ID')
        source_ids.add(sid)
        for key in ('title', 'locator'):
            _text(source[key], sid + '/' + key)
        if not isinstance(source['doi'], str) or not _DOI.fullmatch(source['doi']):
            raise ValueError('Invalid intent review-source DOI')
        source_url = urlsplit(_https(source['url'], sid + '/url'))
        if (source_url.hostname in ('doi.org', 'dx.doi.org')
                and unquote(source_url.path.lstrip('/')).casefold() != source['doi'].casefold()):
            raise ValueError('Intent review-source DOI URL refers to a different work')
        if type(source['year']) is not int or not 1000 <= source['year'] <= 9999:
            raise ValueError('Invalid intent review-source year')
        sources.append(copy.deepcopy(source))
    seen, intents = set(), []
    for intent in config['intents']:
        _keys(intent, ('id', 'question', 'question_zh', 'source_ids', 'focused_queries'), 'broad intent')
        iid = _identifier(intent['id'], 'broad intent')
        if iid in seen:
            raise ValueError('Duplicate broad intent ID')
        seen.add(iid)
        for key in ('question', 'question_zh'):
            _text(intent[key], iid + '/' + key)
        refs = _unique(intent['source_ids'], iid + '/source IDs')
        if not refs or any(source not in source_ids for source in refs):
            raise ValueError('Unknown or absent intent review-source reference')
        if not isinstance(intent['focused_queries'], list) or not intent['focused_queries']:
            raise ValueError('A broad intent requires focused queries')
        focused, seen_queries = [], set()
        for query in intent['focused_queries']:
            _keys(query, ('id', 'question', 'question_zh', 'work_refs'), 'focused query')
            qid = _identifier(query['id'], iid + '/focused query')
            if qid in seen_queries:
                raise ValueError('Duplicate focused query ID within an intent')
            seen_queries.add(qid)
            for key in ('question', 'question_zh'):
                _text(query[key], qid + '/' + key)
            if not isinstance(query['work_refs'], list) or not query['work_refs']:
                raise ValueError('A focused query requires existing work references')
            links, seen_works = [], set()
            for ref in query['work_refs']:
                _keys(ref, ('work_id', 'question_ids', 'preview_question_id'), 'work reference')
                wid = ref['work_id']
                if not isinstance(wid, str) or wid not in works or wid in seen_works:
                    raise ValueError('Unknown or duplicate intent work reference')
                seen_works.add(wid)
                work = works[wid]
                paper_url = _https(work['paper_url'], wid + '/paper URL')
                qrefs = _unique(ref['question_ids'], wid + '/question IDs')
                if qrefs and work.get('evidence_status') != 'reviewed_v2':
                    raise ValueError('Unreviewed intent work cannot acquire reviewed answers')
                for question_id in qrefs:
                    qa = questions.get(question_id)
                    if not qa or qa['work_id'] != wid:
                        raise ValueError('Intent question reference belongs to another or unknown work')
                    if not qa['answer_url'].startswith(paper_url + '#qa-'):
                        raise ValueError('Intent question URL differs from its canonical work')
                preview = ref['preview_question_id']
                if preview is not None:
                    if preview not in qrefs:
                        raise ValueError('Intent preview must be one of its referenced questions')
                    qa = questions[preview]
                    findings = {finding['id'] for finding in work['key_findings']}
                    if (qa.get('evidence_refs_status') != 'resolved' or not qa.get('evidence_refs')
                            or any(fid not in findings for fid in qa['evidence_refs'])):
                        raise ValueError('Intent preview requires encoded, resolved finding references')
                scope_url = (paper_url + '#ev-scope' if work.get('evidence_status') == 'reviewed_v2'
                             else work.get('evidence_url') or paper_url)
                links.append({'work_id': wid, 'question_ids': list(qrefs), 'preview_question_id': preview,
                              'paper_url': paper_url, 'doi': work.get('doi'),
                              'doi_url': work.get('doi_url'), 'scope_url': scope_url,
                              'citation_url': paper_url + '#cite-this-paper'
                              if work.get('citation_csl_json_url') else None})
            focused.append({**{key: query[key] for key in ('id', 'question', 'question_zh')}, 'work_refs': links})
        intents.append({**{key: intent[key] for key in ('id', 'question', 'question_zh')},
                        'source_ids': list(refs), 'focused_queries': focused})
    return {'intent_layer_version': 1, 'intent_sources': sources, 'intents': intents}


def render_intent_layer(discovery):
    """Render public navigation and verbatim answers in ordinary static HTML."""
    if not discovery.get('intents'):
        return ''
    escape = html.escape
    works, questions = _lookup(discovery)
    sources = {source['id']: source for source in discovery['intent_sources']}
    sections = []
    navigation = []
    for intent in discovery['intents']:
        anchor = 'intent-' + intent['id']
        navigation.append('<li><a href="#' + escape(anchor, quote=True) + '">'
                          + escape(intent['question']) + '</a></li>')
        queries = []
        for query in intent['focused_queries']:
            evidence = []
            for ref in query['work_refs']:
                work = works[ref['work_id']]
                original_questions = [questions[qid] for qid in ref['question_ids']]
                preview = questions.get(ref['preview_question_id'])
                answer = ''
                if preview:
                    findings = {finding['id']: finding for finding in work['key_findings']}
                    answer = ('<p class="intent-answer"><strong>Reviewed answer from this paper:</strong> '
                              + '<span data-intent-answer="' + escape(preview['id'], quote=True) + '">'
                              + escape(preview['answer']) + '</span></p><ul class="intent-locators">'
                              + ''.join('<li><a href="' + escape(findings[fid]['evidence_url'], quote=True)
                                        + '">' + escape(fid) + '</a> · '
                                        + escape(findings[fid]['source_locator']) + '</li>'
                                        for fid in preview['evidence_refs']) + '</ul>')
                links = ('<a data-intent-paper href="' + escape(ref['paper_url'], quote=True)
                         + '">Paper evidence</a>')
                if ref['doi_url']:
                    links += ' · <a href="' + escape(ref['doi_url'], quote=True) + '">DOI: ' + escape(ref['doi']) + '</a>'
                if ref['citation_url']:
                    links += ' · <a href="' + escape(ref['citation_url'], quote=True) + '">Cite</a>'
                links += ' · <a href="' + escape(ref['scope_url'], quote=True) + '">Study evidence scope</a>'
                question_links = ('<ul class="intent-question-links">'
                                  + ''.join('<li><a data-intent-question href="'
                                            + escape(qa['answer_url'], quote=True) + '">'
                                            + escape(qa['question']) + '</a></li>' for qa in original_questions)
                                  + '</ul>') if original_questions else ''
                identity = ' · '.join(str(work.get(key) or '') for key in ('journal', 'year', 'type')).strip(' ·')
                profile = work.get('study_profile') or {}
                detail = ''
                if work.get('authors') or profile.get('study_design'):
                    detail = ('<details class="intent-study"><summary>Authors and study profile</summary>'
                              + ('<p>' + escape('; '.join(work['authors'])) + '</p>' if work.get('authors') else '')
                              + ('<p>' + escape(profile['study_design']) + '</p>' if profile.get('study_design') else '')
                              + '</details>')
                evidence.append('<div class="intent-evidence" data-intent-work="' + escape(work['id'], quote=True) + '">'
                                + '<h5><a href="' + escape(ref['paper_url'], quote=True) + '">'
                                + escape(work['title']) + '</a></h5><p class="meta">' + escape(identity) + '</p>'
                                + answer + detail + question_links + '<p class="links">' + links + '</p></div>')
            queries.append('<section class="intent-focused" id="' + escape(anchor + '--' + query['id'], quote=True)
                           + '" data-intent-focused="' + escape(query['id'], quote=True) + '"><h4>'
                           + escape(query['question']) + '</h4><p class="intent-translation" lang="zh">'
                           + escape(query['question_zh']) + '</p>' + ''.join(evidence) + '</section>')
        context = '<p class="intent-reviews"><strong>Review context:</strong> ' + ' · '.join(
            '<a href="' + escape(sources[sid]['url'], quote=True) + '">'
            + escape(sources[sid]['title']) + ' (' + str(sources[sid]['year']) + ')</a>'
            for sid in intent['source_ids']) + '</p>'
        sections.append('<article class="intent-topic" id="' + escape(anchor, quote=True)
                        + '" data-research-intent="' + escape(intent['id'], quote=True) + '"><h3>'
                        + escape(intent['question']) + '</h3><p class="intent-translation" lang="zh">'
                        + escape(intent['question_zh']) + '</p>' + ''.join(queries) + context + '</article>')
    return ('<section class="intent-layer" id="research-intents" data-intent-layer="1" aria-labelledby="intent-layer-title">'
            + '<h2 id="intent-layer-title">Start with a research question</h2>'
            + '<p>Explore broad research directions, focused questions and source-linked evidence from this research program. '
            + 'Related publications retain their original study identities and DOIs.</p>'
            + '<nav class="intent-navigation" aria-label="Research questions"><ol>' + ''.join(navigation) + '</ol></nav>'
            + ''.join(sections) + '</section>')


class _LayerParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.markers = {}

    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key == 'id':
                self.ids.append(value)
            if key.startswith('data-intent-') or key == 'data-research-intent':
                self.markers[key] = self.markers.get(key, 0) + 1


def validate_intent_html(page, discovery, root=None):
    """Normal Pages validation includes this source-bound additive contract."""
    expected = render_intent_layer(discovery)
    if expected and page.count(expected) != 1:
        raise ValueError('Scientific intent HTML differs from its source-bound navigation')
    if not expected and 'data-intent-layer=' in page:
        raise ValueError('Unexpected scientific intent HTML')
    parsed = _LayerParser()
    parsed.feed(page)
    if len(parsed.ids) != len(set(parsed.ids)):
        raise ValueError('Scientific intent HTML has duplicate IDs')
    intents = discovery.get('intents', [])
    queries = [query for intent in intents for query in intent['focused_queries']]
    refs = [ref for query in queries for ref in query['work_refs']]
    expected_markers = {'data-intent-layer': int(bool(intents)), 'data-research-intent': len(intents),
                        'data-intent-focused': len(queries), 'data-intent-paper': len(refs),
                        'data-intent-question': sum(len(ref['question_ids']) for ref in refs),
                        'data-intent-answer': sum(ref['preview_question_id'] is not None for ref in refs)}
    if any(parsed.markers.get(key, 0) != count for key, count in expected_markers.items()):
        raise ValueError('Scientific intent HTML reference or answer inventory differs')
    if root is not None:
        works, questions = _lookup(discovery)
        documents = {}
        for ref in refs:
            wid = ref['work_id']
            if wid not in documents:
                document = _LayerParser()
                document.feed((Path(root) / 'papers' / (wid + '.html')).read_text(encoding='utf-8'))
                documents[wid] = document.ids
            urls = [ref['scope_url'], *(questions[qid]['answer_url'] for qid in ref['question_ids'])]
            if ref['preview_question_id']:
                qa = questions[ref['preview_question_id']]
                findings = {finding['id']: finding for finding in works[wid]['key_findings']}
                urls += [findings[fid]['evidence_url'] for fid in qa['evidence_refs']]
            canonical = urlsplit(works[wid]['paper_url'])
            for url in urls:
                target = urlsplit(url)
                if ((target.scheme, target.netloc, target.path) != (canonical.scheme, canonical.netloc, canonical.path)
                        or (target.fragment and documents[wid].count(target.fragment) != 1)):
                    raise ValueError('Intent evidence or scope anchor is missing or outside its canonical paper')
    return {'broad_intents': len(intents), 'focused_queries': len(queries)}
