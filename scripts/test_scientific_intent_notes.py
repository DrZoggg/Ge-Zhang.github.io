"""Limited-note previews remain source selections rather than new Gold answers."""
import copy
import html
import unittest

import test_scientific_intents as legacy
from scientific_intents import render_intent_layer, validate_intent_html


class ScientificIntentNoteTests(unittest.TestCase):
    build = legacy.ScientificIntentTests.build

    def setUp(self):
        legacy.ScientificIntentTests.setUp(self)
        self.ref.update(question_ids=[], preview_question_id=None,
                        preview_note_headings=['Blood and brain expression context'])
        self.discovery['all_questions'] = []
        self.work.update(evidence_status='limited', key_findings=[],
                         evidence_url=self.work['paper_url'] + '#limited-evidence',
                         limitations=['The original material limitation remains.'])
        self.section = {'heading': 'Blood and brain expression context',
                        'text': 'Separate blood & brain expression comparisons; score < direct cell count.',
                        'source_url': 'https://publisher.example/article/original',
                        'source_locator': 'Original Results, blood and brain comparisons.'}
        self.note = {'reviewed_on': '2026-10-27',
                     'source_record': 'data/limited_evidence.json#/papers/10.1234~1a',
                     'sections': [self.section, {**self.section, 'heading': 'Other source context'}]}
        self.work['author_evidence_note'] = self.note

    def test_selected_section_and_provenance_are_verbatim_detached_from_original(self):
        before = copy.deepcopy(self.discovery)
        layer = self.build()
        ref = layer['intents'][0]['focused_queries'][0]['work_refs'][0]
        expected = {**self.section, 'reviewed_on': self.note['reviewed_on'],
                    'source_record': self.note['source_record']}
        self.assertEqual(ref['author_note_previews'], [expected])
        self.assertEqual(self.discovery, before)
        ref['author_note_previews'][0]['text'] = 'Caller mutation is not the source.'
        self.assertEqual(self.discovery, before)

    def test_context_is_public_before_scope_and_doi_without_qa_or_v2_promotion(self):
        discovery = {**self.discovery, **self.build()}
        page = render_intent_layer(discovery)
        self.assertIn('Author-reviewed research context:', page)
        self.assertIn('Original source context:', page)
        for field in ['heading', 'text', 'source_locator', 'source_url']:
            self.assertIn(html.escape(self.section[field], quote=True), page)
        self.assertIn(self.note['reviewed_on'], page)
        self.assertLess(page.index(html.escape(self.section['text'])), page.index('>DOI:'))
        self.assertLess(page.index(html.escape(self.section['text'])), page.index('>Study evidence scope'))
        self.assertNotIn('data-intent-answer=', page)
        self.assertNotIn('Reviewed answer from this paper:', page)
        self.assertNotIn('Principal findings from this paper:', page)
        self.assertNotIn('score < direct', page)
        self.assertEqual(self.work['limitations'], ['The original material limitation remains.'])
        self.assertEqual(self.work['evidence_status'], 'limited')
        validate_intent_html(page, discovery)

    def test_omitting_selector_keeps_the_old_export_and_html_contract(self):
        del self.ref['preview_note_headings']
        with_note = self.build()
        old_discovery = copy.deepcopy(self.discovery)
        del old_discovery['works'][0]['author_evidence_note']
        without_note = self.build(discovery=old_discovery)
        self.assertEqual(with_note, without_note)
        self.assertNotIn('author_note_previews', with_note['intents'][0]['focused_queries'][0]['work_refs'][0])
        self.assertEqual(render_intent_layer({**self.discovery, **with_note}),
                         render_intent_layer({**old_discovery, **without_note}))

    def test_only_limited_work_with_an_existing_note_is_eligible(self):
        for kind in ['reviewed_v2', 'patent_record', 'unknown']:
            self.work['evidence_status'] = kind
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'existing limited author evidence note'):
                self.build()
        self.work['evidence_status'] = 'limited'
        del self.work['author_evidence_note']
        with self.assertRaisesRegex(ValueError, 'existing limited author evidence note'):
            self.build()

    def test_unknown_partial_ambiguous_and_unusable_headings_fail_closed(self):
        for value in [[], None, 'Blood and brain expression context', ['Blood'],
                      ['Blood and brain expression context '], ['Unknown heading'],
                      ['Blood and brain expression context', 'Blood and brain expression context'],
                      ['Blood and brain expression context<script>']]:
            self.ref['preview_note_headings'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.build()
        self.ref['preview_note_headings'] = [self.section['heading']]
        self.note['sections'].append(copy.deepcopy(self.section))
        with self.assertRaisesRegex(ValueError, 'exactly one existing section'):
            self.build()

    def test_controller_cannot_supply_note_text_sections_or_exported_previews(self):
        for field in ['text', 'sections', 'author_note_previews', 'source_url', 'reviewed_on']:
            self.ref[field] = 'Controller-supplied text is not source evidence.'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'fields differ'):
                self.build()
            del self.ref[field]

    def test_note_source_record_review_date_and_section_shape_are_required(self):
        for change in [{'source_record': 'data/limited_evidence.json#/papers/10.1234~1other'},
                       {'source_record': '../../private.json#/secret'},
                       {'reviewed_on': '2026-1-2'}, {'reviewed_on': 'not a date'},
                       {'sections': []}, {'sections': 'Not an existing section list'}]:
            original = copy.deepcopy(self.note)
            self.note.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.build()
            self.note.clear()
            self.note.update(original)
        self.note['sections'][0]['new_text'] = 'An extra payload is not part of a source section.'
        with self.assertRaisesRegex(ValueError, 'fields differ'):
            self.build()

    def test_source_url_and_text_cannot_be_filled_by_navigation(self):
        for field in ['text', 'source_locator']:
            original = self.section[field]
            self.section[field] = ''
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'plain non-empty text'):
                self.build()
            self.section[field] = original
        for value in ['http://publisher.example/article', 'javascript:alert(1)',
                      'https://user:secret@publisher.example/article']:
            self.section['source_url'] = value
            with self.subTest(url=value), self.assertRaisesRegex(ValueError, 'public HTTPS'):
                self.build()

    def test_note_selection_does_not_allow_limited_work_to_acquire_gold_answers(self):
        self.discovery['all_questions'] = [self.qa]
        self.ref.update(question_ids=[self.qa['id']], preview_question_id=self.qa['id'])
        with self.assertRaisesRegex(ValueError, 'cannot acquire reviewed answers'):
            self.build()

    def test_note_source_and_scope_remain_canonical_and_html_inventory_is_checked(self):
        discovery = {**self.discovery, **self.build()}
        page = render_intent_layer(discovery)
        papers = self.root / 'papers'
        papers.mkdir()
        target = papers / 'work-a.html'
        target.write_text('<i id="limited-evidence"></i>', encoding='utf-8')
        validate_intent_html(page, discovery, self.root)
        target.write_text('<i id="unrelated"></i>', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'anchor is missing'):
            validate_intent_html(page, discovery, self.root)
        for changed in [page.replace(html.escape(self.section['text']), 'Changed context'),
                        page + '<i data-intent-note="injected">Extra note</i>']:
            with self.subTest(changed=changed[-80:]), self.assertRaises(ValueError):
                validate_intent_html(changed, discovery)


if __name__ == '__main__':
    unittest.main()
