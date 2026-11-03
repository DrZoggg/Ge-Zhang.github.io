"""Reviewed finding previews answer focused queries without another fact store."""
import copy
import html
import unittest

import test_scientific_intents as legacy
from scientific_intents import render_intent_layer, validate_intent_html


class ScientificIntentFindingTests(unittest.TestCase):
    build = legacy.ScientificIntentTests.build

    def setUp(self):
        legacy.ScientificIntentTests.setUp(self)
        self.finding = self.work['key_findings'][0]
        self.finding.update(claim='Observed endothelial <states> & tissue classification.',
                            context='Cross-sectional expression; internal testing < 1 cohort.',
                            evidence=[{'label': 'Observed count', 'value': '9'}])
        self.ref['preview_finding_ids'] = ['KF1']

    def test_resolved_export_is_verbatim_deep_copy_without_mutating_evidence(self):
        before = copy.deepcopy(self.discovery)
        layer = self.build()
        exported = layer['intents'][0]['focused_queries'][0]['work_refs'][0]['finding_previews']
        self.assertEqual(exported, [self.finding])
        self.assertEqual(self.discovery, before)
        exported[0]['evidence'][0]['value'] = 'not the source'
        self.assertEqual(self.finding['evidence'][0]['value'], '9')

    def test_findings_precede_formula_and_preserve_scope_locator_and_escaping(self):
        discovery = {**self.discovery, **self.build()}
        page = render_intent_layer(discovery)
        self.assertLess(page.index(html.escape(self.finding['claim'])), page.index(html.escape(self.qa['answer'])))
        for value in ['claim', 'context', 'source_locator']:
            self.assertIn(html.escape(self.finding[value]), page)
        self.assertIn('data-intent-finding="work-a--KF1"', page)
        self.assertIn('https://example.org/papers/a.html#kf1', page)
        self.assertNotIn('<states>', page)
        validate_intent_html(page, discovery)

    def test_unrequested_previews_do_not_appear_or_change_export_shape(self):
        del self.ref['preview_finding_ids']
        layer = self.build()
        ref = layer['intents'][0]['focused_queries'][0]['work_refs'][0]
        self.assertNotIn('finding_previews', ref)
        self.assertNotIn('data-intent-finding=', render_intent_layer({**self.discovery, **layer}))

    def test_unknown_cross_work_or_unencoded_findings_are_rejected(self):
        for ids in [['UNKNOWN'], ['work-b--KF1']]:
            self.ref['preview_finding_ids'] = ids
            with self.assertRaisesRegex(ValueError, 'belong to this work'):
                self.build()
        self.ref['preview_finding_ids'] = ['KF1']
        self.ref['preview_question_id'] = None
        self.qa.update(evidence_refs=[], evidence_refs_status='not_encoded')
        with self.assertRaisesRegex(ValueError, 'referenced questions'):
            self.build()

    def test_limited_and_patent_records_cannot_acquire_reviewed_finding_previews(self):
        self.ref.update(question_ids=[], preview_question_id=None)
        for kind in ['limited', 'patent_record']:
            self.work['evidence_status'] = kind
            with self.assertRaisesRegex(ValueError, 'existing reviewed work'):
                self.build()

    def test_empty_duplicate_and_non_list_finding_requests_are_rejected(self):
        for value in [[], ['KF1', 'KF1'], 'KF1', None]:
            self.ref['preview_finding_ids'] = value
            with self.assertRaises(ValueError):
                self.build()

    def test_controller_cannot_supply_scientific_claims_or_derived_previews(self):
        for field in ['finding_previews', 'claim', 'context', 'evidence']:
            self.ref[field] = 'New text is not a reviewed source'
            with self.assertRaisesRegex(ValueError, 'fields differ'):
                self.build()
            del self.ref[field]

    def test_missing_claim_scope_or_locator_is_not_filled_by_navigation(self):
        for field in ['claim', 'context', 'source_locator']:
            value = self.finding.pop(field)
            with self.assertRaisesRegex(ValueError, 'plain non-empty text'):
                self.build()
            self.finding[field] = value

    def test_foreign_or_wrong_finding_anchor_is_rejected(self):
        for url in ['https://elsewhere.example/papers/a.html#kf1',
                    'https://example.org/papers/a.html#kf2',
                    'https://example.org/papers/a.html#qa-1']:
            self.finding['evidence_url'] = url
            with self.assertRaisesRegex(ValueError, 'canonical finding URL'):
                self.build()

    def test_static_canonical_finding_anchor_is_required_and_preview_cannot_be_dropped(self):
        self.ref.update(question_ids=['work-a--qa-1'], preview_question_id=None)
        discovery = {**self.discovery, **self.build()}
        page = render_intent_layer(discovery)
        papers = self.root / 'papers'
        papers.mkdir()
        target = papers / 'work-a.html'
        target.write_text('<i id="ev-scope"></i><i id="qa-1"></i>', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'anchor is missing'):
            validate_intent_html(page, discovery, self.root)
        target.write_text('<i id="ev-scope"></i><i id="qa-1"></i><i id="kf1"></i>', encoding='utf-8')
        validate_intent_html(page, discovery, self.root)
        with self.assertRaisesRegex(ValueError, 'differs'):
            validate_intent_html(page.replace(html.escape(self.finding['claim']), 'Dropped finding'), discovery)


if __name__ == '__main__':
    unittest.main()
