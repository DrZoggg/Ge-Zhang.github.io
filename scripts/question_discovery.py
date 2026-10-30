"""Normalized question discovery data copied from current reviewed sources.

Answers remain on their existing canonical paper pages. This additive export
links exact Gold text to its paper identity, complete scope and encoded evidence
references; a missing question-level reference is reported, never inferred.
"""
import copy
import hashlib
import json
import re
from pathlib import Path

from sync_common import ROOT


REPOSITORY_SOURCE = 'https://github.com/DrZoggg/Ge-Zhang.github.io/blob/main/'
IDENTITY_FIELDS = (
    'doi_url', 'publisher_url', 'pmid', 'pmcid', 'openalex_id',
    'semantic_scholar_id', 'citation_bibtex_url', 'citation_ris_url',
    'citation_csl_json_url',
)


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError('Question discovery requires exact non-empty text: ' + label)
    return value


def _read(path):
    # Universal-newline reading matches the existing reviewed-preview contract.
    text = path.read_text(encoding='utf-8')
    return json.loads(text), hashlib.sha256(text.encode('utf-8')).hexdigest()


def _limited_sources(root, items):
    path = root / 'data/limited_evidence.json'
    if not path.exists():
        return {}
    payload, _ = _read(path)
    if (set(payload) != {'version', 'papers'} or payload['version'] != 1
            or not isinstance(payload['papers'], dict)):
        raise ValueError('Unsupported limited evidence discovery source')
    from limited_evidence import validate_record
    public = {item['doi']: item for item in items if item.get('doi')}
    for doi, record in payload['papers'].items():
        if doi not in public:
            raise ValueError('Limited discovery source is not a public work')
        validate_record(doi, record, public[doi])
    return payload['papers']


def build_discovery(items, contents, fields, root=ROOT):
    """Return additive, deterministic arrays without changing the 59-route API.

    Work order and metadata follow ``items``. Only explicitly V2 work identities
    with a matching Gold file can contribute Q&A. No source text is shortened,
    ranked as stronger evidence, or synthesized for limited/patent records.
    """
    root = Path(root)
    works, questions, seen = [], [], set()
    limited = _limited_sources(root, items)
    patent_path = root / 'data/patent_evidence.json'
    patent = _read(patent_path)[0] if patent_path.exists() else None
    for item in items:
        slug = item['slug']
        if (not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug)
                or slug in seen):
            raise ValueError('Missing, unsafe or duplicate discovery work ID')
        seen.add(slug)
        doi = item.get('doi')
        content = contents.get((doi or '').lower())
        work = {
            'id': slug,
            **{key: copy.deepcopy(item.get(key)) for key in (
                'title', 'doi', 'year', 'journal', 'type', 'paper_url',
                'markdown_url', 'paper_geo_status', 'authors')},
            **{key: fields[slug].get(key) for key in IDENTITY_FIELDS},
            'evidence_status': 'identity_only',
            'question_count': 0,
            'field_entry': [],
            'review_topics': [],
            'concepts': {},
            'evidence_scope': None,
            'limitations': [],
            'key_findings': [],
        }
        _text(work['title'], slug + '/title')
        if item.get('paper_geo_status') == 'v2':
            if not content or content.get('version') != 2:
                raise ValueError('V2 discovery work lacks reviewed Gold: ' + slug)
            source = 'data/deep_geo/' + slug + '.json'
            gold, source_hash = _read(root / source)
            # The existing renderer attaches one transient, resolved cluster
            # object. It is navigation state, not a Gold source mutation.
            # Reject every other difference, including unknown underscore keys.
            source_content = {key: value for key, value in content.items()
                              if key != '_research_cluster'}
            if gold != source_content or gold.get('doi') != doi:
                raise ValueError('Discovery content differs from its Gold source: ' + slug)
            content = gold
            if not isinstance(content.get('qa'), list) or not content['qa']:
                raise ValueError('Reviewed question array missing: ' + slug)
            scope = content.get('evidence_scope')
            if (not isinstance(scope, dict) or not scope.get('does_not_establish')
                    or not isinstance(content.get('limitations'), list)):
                raise ValueError('Full reviewed scope missing: ' + slug)
            layer = content.get('discovery_layer', {})
            work.update({
                'evidence_status': 'reviewed_v2',
                'question_count': len(content['qa']),
                'field_entry': copy.deepcopy(layer.get('field_entry', [])),
                'review_topics': copy.deepcopy(layer.get('review_topics', [])),
                'concepts': copy.deepcopy(content.get('concepts', {})),
                'evidence_scope': copy.deepcopy(scope),
                'limitations': copy.deepcopy(content['limitations']),
                'profile_type': content['study_profile']['profile_type'],
                'study_profile': copy.deepcopy(content['study_profile']),
                'study_profile_source': source + '#/study_profile',
                'model_profile': copy.deepcopy(content.get('model_profile')),
                'model_profile_source': source + '#/model_profile' if 'model_profile' in content else None,
                'narrative_genre': content['study_profile'].get('narrative_genre'),
                'gold_source': source,
                'gold_source_url': REPOSITORY_SOURCE + source,
                'gold_content_sha256': source_hash,
                'scope_source': source + '#/evidence_scope',
                'provenance': copy.deepcopy(content.get('provenance', {})),
            })
            for key in ('scientific_role', 'evidence_position', 'related_concepts', 'citation_contexts'):
                if key in layer:
                    work[key] = copy.deepcopy(layer[key])
            findings = {}
            for position, finding in enumerate(content['key_findings']):
                ref = _text(finding['id'], slug + '/finding ID')
                if ref in findings:
                    raise ValueError('Duplicate reviewed finding ID: ' + slug)
                locator = _text(finding['source_locator'], slug + '/' + ref + '/locator')
                findings[ref] = {
                    **copy.deepcopy(finding),
                    'id': ref,
                    'source': source + '#/key_findings/' + str(position),
                    'source_locator': locator,
                    'evidence_url': item['paper_url'] + '#' + ref.lower(),
                }
            work['key_findings'] = list(findings.values())
            for position, qa in enumerate(content['qa'], 1):
                question = _text(qa['question'], slug + '/question')
                answer = _text(qa['answer'], slug + '/answer')
                refs = qa.get('evidence_refs', [])
                if (not isinstance(refs, list)
                        or any(not isinstance(ref, str) for ref in refs)
                        or len(refs) != len(set(refs))
                        or any(ref not in findings for ref in refs)):
                    raise ValueError('Unresolved or duplicate question evidence reference: ' + slug)
                pointer = source + '#/qa/' + str(position - 1)
                questions.append({
                    'id': slug + '--qa-' + str(position),
                    'work_id': slug,
                    'qa_index': position,
                    'question': question,
                    'answer': answer,
                    'answer_url': item['paper_url'] + '#qa-' + str(position),
                    'question_source': pointer + '/question',
                    'answer_source': pointer + '/answer',
                    'answer_sha256': hashlib.sha256(answer.encode('utf-8')).hexdigest(),
                    'evidence_refs': list(refs),
                    'evidence_refs_status': 'resolved' if refs else 'not_encoded',
                })
        elif content and content.get('version') == 2:
            raise ValueError('Gold V2 content cannot silently promote a non-V2 work: ' + slug)
        elif doi in limited:
            record = limited[doi]
            work.update({
                'evidence_status': 'limited',
                'scope': record['scope'],
                'evidence_notice': record['scope'],
                'limitations': copy.deepcopy(record['limitations']),
                'evidence_url': item['paper_url'] + '#limited-evidence',
                'scope_source': 'data/limited_evidence.json#/papers/'
                                + doi.replace('~', '~0').replace('/', '~1') + '/scope',
                'source_url': REPOSITORY_SOURCE + 'data/limited_evidence.json',
                'provenance': copy.deepcopy(record['sources']),
            })
        elif item.get('type') == 'Patent':
            if (doi or not patent or patent.get('work_slug') != slug
                    or patent.get('module_type') != 'patent_record'
                    or patent.get('ordinary_paper_v2') is not False):
                raise ValueError('Patent discovery must preserve its reviewed non-DOI identity')
            work.update({
                'evidence_status': 'patent_record',
                'scope': _text(patent['evidence_notice'], slug + '/patent notice'),
                'evidence_notice': _text(patent['evidence_notice'], slug + '/patent notice'),
                'limitations': copy.deepcopy(patent['limitations']),
                'evidence_url': item['paper_url'] + '#patent-document-evidence',
                'scope_source': 'data/patent_evidence.json#/evidence_notice',
                'source_url': REPOSITORY_SOURCE + 'data/patent_evidence.json',
                'provenance': copy.deepcopy(patent['provenance']),
            })
        works.append(work)
    return {'discovery_version': 2, 'works': works, 'all_questions': questions}
