"""Navigation contracts: stable identities, exact answers and public HTML."""
import copy
import html
import json
import tempfile
import unittest
from pathlib import Path

from scientific_intents import build_intent_layer, render_intent_layer, validate_intent_html


class ScientificIntentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        self.source = {'id': 'review-context', 'title': 'A source review', 'doi': '10.1234/review',
                       'url': 'https://doi.org/10.1234/review', 'year': 2024, 'locator': 'Section 2'}
        self.work = {'id': 'work-a', 'title': 'A study <title>', 'doi': '10.1234/a',
                     'doi_url': 'https://doi.org/10.1234/a', 'paper_url': 'https://example.org/papers/a.html',
                     'journal': 'Journal A', 'year': 2023, 'type': 'Article', 'authors': ['A <Lead>', 'B'],
                     'citation_csl_json_url': 'https://example.org/citations/a.csl.json',
                     'evidence_status': 'reviewed_v2',
                     'study_profile': {'study_design': 'Retrospective <cohort>.'},
                     'evidence_scope': {'supports': ['Original scope.'], 'does_not_establish': ['Original limitation.']},
                     'key_findings': [{'id': 'KF1', 'source_locator': 'Original Figure 2 <panel>',
                                       'evidence_url': 'https://example.org/papers/a.html#kf1'}]}
        self.qa = {'id': 'work-a--qa-1', 'work_id': 'work-a', 'question': 'What did the study find?',
                   'answer': 'The original value was < 10 & retained its original scope.',
                   'answer_url': 'https://example.org/papers/a.html#qa-1',
                   'evidence_refs': ['KF1'], 'evidence_refs_status': 'resolved'}
        self.discovery = {'discovery_version': 2, 'works': [self.work], 'all_questions': [self.qa]}
        self.ref = {'work_id': 'work-a', 'question_ids': ['work-a--qa-1'], 'preview_question_id': 'work-a--qa-1'}
        self.query = {'id': 'specific-population', 'question': 'Which studies inform this <question>?',
                      'question_zh': '哪些研究可以提供线索？', 'work_refs': [self.ref]}
        self.intent = {'id': 'broad-research', 'question': 'What is the broader research question?',
                       'question_zh': '广泛科研问题是什么？', 'source_ids': ['review-context'],
                       'focused_queries': [self.query]}
        self.config = {'version': 1, 'sources': [self.source], 'intents': [self.intent]}

    def build(self, config=None, discovery=None):
        (self.root / 'data/scientific_discovery_intents.json').write_text(
            json.dumps(self.config if config is None else config, ensure_ascii=False), encoding='utf-8')
        return build_intent_layer(self.discovery if discovery is None else discovery, self.root)

    def test_missing_optional_controller_preserves_existing_contract(self):
        self.assertEqual(build_intent_layer(self.discovery, self.root), {})
        self.assertEqual(render_intent_layer(self.discovery), '')
        self.assertEqual(validate_intent_html('<main id="original"></main>', self.discovery),
                         {'broad_intents': 0, 'focused_queries': 0})

    def test_repeatable_reference_export_does_not_mutate_or_duplicate_answers(self):
        before = copy.deepcopy(self.discovery)
        first = self.build()
        self.assertEqual(first, self.build())
        self.assertEqual(self.discovery, before)
        self.assertNotIn('works', first)
        def keys(value):
            if isinstance(value, dict):
                return set(value).union(*(keys(item) for item in value.values()))
            if isinstance(value, list):
                return set().union(*(keys(item) for item in value))
            return set()
        self.assertNotIn('answer', keys(first))
        self.assertEqual(first['intent_layer_version'], 1)
        ref = first['intents'][0]['focused_queries'][0]['work_refs'][0]
        self.assertEqual(ref['scope_url'], self.work['paper_url'] + '#ev-scope')
        self.assertEqual(ref['doi'], self.work['doi'])
        self.assertEqual(ref['citation_url'], self.work['paper_url'] + '#cite-this-paper')

    def test_complete_original_answer_and_locators_are_public_and_escaped(self):
        discovery = {**self.discovery, **self.build()}
        document = render_intent_layer(discovery)
        self.assertIn(html.escape(self.qa['answer']), document)
        self.assertIn(html.escape(self.qa['question']), document)
        self.assertIn(html.escape(self.work['title']), document)
        self.assertIn(html.escape(self.work['key_findings'][0]['source_locator']), document)
        self.assertIn(html.escape(self.work['study_profile']['study_design']), document)
        self.assertIn('A &lt;Lead&gt;', document)
        self.assertIn('lang="zh"', document)
        self.assertNotIn('<script', document)
        self.assertNotIn('<aside', document)
        self.assertNotIn('data-question-route', document)
        self.assertNotIn('data-reviewed-answer=', document)
        self.assertIn('href="' + self.qa['answer_url'] + '"', document)
        self.assertEqual(validate_intent_html(document, discovery), {'broad_intents': 1, 'focused_queries': 1})

    def test_same_work_can_support_multiple_queries_without_new_studies(self):
        self.intent['focused_queries'].append({**copy.deepcopy(self.query), 'id': 'another-question'})
        layer = self.build()
        self.assertEqual(len(self.discovery['works']), 1)
        refs = [ref for q in layer['intents'][0]['focused_queries'] for ref in q['work_refs']]
        self.assertEqual(len(refs), 2)
        self.assertEqual({ref['doi'] for ref in refs}, {self.work['doi']})
        validate_intent_html(render_intent_layer({**self.discovery, **layer}), {**self.discovery, **layer})

    def test_limited_and_patent_records_have_identity_links_without_invented_answers(self):
        for kind, doi in [('limited', '10.1234/a'), ('patent_record', None)]:
            with self.subTest(kind=kind):
                work = {**self.work, 'evidence_status': kind, 'doi': doi,
                        'doi_url': 'https://doi.org/' + doi if doi else None,
                        'key_findings': [], 'citation_csl_json_url': None,
                        'evidence_url': self.work['paper_url'] + '#original-source'}
                self.ref.update(question_ids=[], preview_question_id=None)
                discovery = {'works': [work], 'all_questions': []}
                layer = self.build(discovery=discovery)
                ref = layer['intents'][0]['focused_queries'][0]['work_refs'][0]
                self.assertEqual(ref['scope_url'], work['evidence_url'])
                self.assertIsNone(ref['citation_url'])
                document = render_intent_layer({**discovery, **layer})
                self.assertNotIn('data-intent-answer=', document)
                self.assertNotIn('data-intent-question', document)
                validate_intent_html(document, {**discovery, **layer})

    def test_config_cannot_carry_answer_claim_or_other_unreviewed_fields(self):
        locations = [self.config, self.source, self.intent, self.query, self.ref]
        for target in locations:
            for key in ('answer', 'claim'):
                with self.subTest(target=list(target), field=key):
                    target[key] = 'New unreviewed scientific text'
                    with self.assertRaisesRegex(ValueError, 'fields differ'):
                        self.build()
                    del target[key]

    def test_unknown_and_cross_work_question_references_are_rejected(self):
        for question_id in ('missing--qa-1', 'work-b--qa-1'):
            with self.subTest(question_id=question_id):
                discovery = copy.deepcopy(self.discovery)
                discovery['all_questions'].append({**self.qa, 'id': 'work-b--qa-1', 'work_id': 'work-b'})
                self.ref.update(question_ids=[question_id], preview_question_id=None)
                with self.assertRaisesRegex(ValueError, 'another or unknown work'):
                    self.build(discovery=discovery)

    def test_unknown_or_duplicate_work_refs_fail_closed(self):
        self.ref['work_id'] = 'unknown-work'
        with self.assertRaisesRegex(ValueError, 'Unknown or duplicate intent work'):
            self.build()
        self.ref['work_id'] = 'work-a'
        self.query['work_refs'].append(copy.deepcopy(self.ref))
        with self.assertRaisesRegex(ValueError, 'Unknown or duplicate intent work'):
            self.build()

    def test_preview_needs_referenced_question_and_encoded_source_findings(self):
        self.ref['preview_question_id'] = 'unlisted--qa-1'
        with self.assertRaisesRegex(ValueError, 'preview must'):
            self.build()
        self.ref['preview_question_id'] = 'work-a--qa-1'
        for change in ({'evidence_refs_status': 'not_encoded'}, {'evidence_refs': []}, {'evidence_refs': ['UNKNOWN']}):
            with self.subTest(change=change):
                discovery = copy.deepcopy(self.discovery)
                discovery['all_questions'][0].update(change)
                with self.assertRaisesRegex(ValueError, 'encoded, resolved'):
                    self.build(discovery=discovery)

    def test_unencoded_questions_remain_linkable_without_a_preview(self):
        self.qa.update(evidence_refs=[], evidence_refs_status='not_encoded')
        self.ref['preview_question_id'] = None
        layer = self.build()
        document = render_intent_layer({**self.discovery, **layer})
        self.assertIn('href="' + self.qa['answer_url'] + '"', document)
        self.assertNotIn('data-intent-answer=', document)

    def test_unreviewed_work_cannot_be_promoted_by_navigation(self):
        self.work['evidence_status'] = 'limited'
        with self.assertRaisesRegex(ValueError, 'cannot acquire reviewed answers'):
            self.build()

    def test_invalid_duplicate_ids_and_references_are_rejected(self):
        mutations = [lambda: self.intent.update(id='../escape'),
                     lambda: self.config['intents'].append(copy.deepcopy(self.intent)),
                     lambda: self.intent['focused_queries'].append(copy.deepcopy(self.query)),
                     lambda: self.config['sources'].append(copy.deepcopy(self.source)),
                     lambda: self.intent.update(source_ids=['missing-source']),
                     lambda: self.intent.update(source_ids=['review-context', 'review-context']),
                     lambda: self.ref.update(question_ids=['work-a--qa-1', 'work-a--qa-1']),
                     lambda: self.ref.update(question_ids=[{}])]
        for mutate in mutations:
            self.setUp()
            mutate()
            with self.subTest(config=self.config), self.assertRaises(ValueError):
                self.build()

    def test_invalid_source_doi_or_sensitive_non_https_url_is_rejected(self):
        for url in ('http://example.org/review', 'javascript:alert(1)', 'https://user:secret@example.org/review'):
            self.source['url'] = url
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, 'public HTTPS'):
                self.build()
        self.source['url'] = 'https://doi.org/10.1234/review'
        self.source['doi'] = 'not a DOI'
        with self.assertRaisesRegex(ValueError, 'source DOI'):
            self.build()

    def test_review_url_cannot_claim_a_different_doi(self):
        self.source['url'] = 'https://doi.org/10.1234/different'
        with self.assertRaisesRegex(ValueError, 'different work'):
            self.build()

    def test_explicit_controller_cannot_silently_remove_all_intents(self):
        self.config['intents'] = []
        with self.assertRaisesRegex(ValueError, 'non-empty arrays'):
            self.build()

    def test_canonical_answer_finding_and_scope_anchors_must_actually_exist(self):
        discovery = {**self.discovery, **self.build()}
        document = render_intent_layer(discovery)
        (self.root / 'papers').mkdir()
        target = self.root / 'papers/work-a.html'
        target.write_text('<section id="qa-1"></section><section id="kf1"></section><section id="ev-scope"></section>', encoding='utf-8')
        validate_intent_html(document, discovery, self.root)
        for missing in ('qa-1', 'kf1', 'ev-scope'):
            target.write_text(''.join('<section id="' + anchor + '"></section>'
                                      for anchor in ('qa-1', 'kf1', 'ev-scope') if anchor != missing), encoding='utf-8')
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'anchor is missing'):
                validate_intent_html(document, discovery, self.root)

    def test_html_validator_rejects_missing_changed_extra_or_duplicate_content(self):
        discovery = {**self.discovery, **self.build()}
        document = render_intent_layer(discovery)
        for changed in ('', document.replace(html.escape(self.qa['answer']), 'Changed scientific answer'),
                        document + '<p data-intent-answer="extra">Extra answer</p>',
                        document + '<p id="research-intents">Duplicate ID</p>'):
            with self.subTest(changed=changed[-80:]), self.assertRaises(ValueError):
                validate_intent_html(changed, discovery)


if __name__ == '__main__':
    unittest.main()
