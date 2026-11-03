"""Source identity and consumer-path regressions for the HF methods answer."""
import copy
import html
import json
import unittest
from unittest.mock import patch

import research_guides as guides
from scientific_intents import build_intent_layer, render_intent_layer, validate_intent_html


SLUG = 'cardiovascular-prediction-evidence'


class HeartFailureResearchUseTests(unittest.TestCase):
    def setUp(self):
        self.data = next(d for d in guides.load_comparisons() if d['slug'] == SLUG)
        self.packet = guides.comparison_packet(self.data)
        self.use = self.packet['research_use']
        self.discovery = json.loads((guides.ROOT / 'research/questions.json').read_text(encoding='utf-8'))

    def changed_packet(self, mutate):
        data = copy.deepcopy(self.data)
        mutate(data['research_use'])
        with patch.dict(guides.COMPARISONS, {SLUG: guides.fingerprint(data)}):
            return guides.comparison_packet(data)

    def test_guide_answer_metrics_sources_and_locators_survive_all_formats(self):
        page, markdown, raw = guides.render_comparison(self.packet)
        self.assertEqual(json.loads(raw)['research_use'], self.use)
        self.assertIn('id="model-evaluation"', page)
        for value in [self.use['answer'], self.use['answer_zh'], self.use['comparison_note']]:
            self.assertIn(html.escape(value), page)
            self.assertIn(value, markdown)
        for row in self.use['comparison']['rows']:
            for key in ('design', 'population', 'endpoint', 'validation', 'metrics', 'doi'):
                self.assertIn(html.escape(row[key]), page)
                self.assertIn(row[key], markdown)
        for source in self.use['sources']:
            for key in ('title', 'doi', 'url', 'locator'):
                self.assertIn(html.escape(source[key], quote=True), page)
                self.assertIn(source[key], markdown)
        self.assertLess(page.index(html.escape(self.use['answer'])), page.index('<article id="aihflevel">'))
        self.assertIn('original published equation', self.use['study_roles'][0]['text'])
        self.assertIn('1 / 2 / 3 / 4 years', self.use['comparison']['rows'][0]['metrics'])
        self.assertIn('same analyzed cohort', self.use['comparison']['rows'][1]['validation'])
        self.assertIn('no new empirical cohort', self.use['comparison']['rows'][2]['population'])

    def test_old_gold_answers_profiles_and_scopes_remain_verbatim(self):
        for study, selection in zip(self.packet['studies'], self.data['studies']):
            source = json.loads((guides.ROOT / selection['source_json']).read_text(encoding='utf-8'))
            for key in ('study_profile', 'evidence_scope', 'limitations'):
                self.assertEqual(study[key], source[key])
            for position, qa in zip(selection['qa_indices'], study['selected_questions']):
                self.assertEqual({key: qa[key] for key in source['qa'][position - 1]}, source['qa'][position - 1])

    def test_questions_derives_one_context_answer_before_the_original_gold_preview(self):
        before = copy.deepcopy(self.discovery)
        layer = build_intent_layer(self.discovery)
        combined = {**self.discovery, **layer}
        all_queries = [query for intent in layer['intents'] for query in intent['focused_queries']]
        contextual = [query for query in all_queries if 'context_answer' in query]
        self.assertEqual([query['id'] for query in contextual], ['ai-heart-failure-2'])
        query = contextual[0]
        self.assertEqual(query['context_answer']['answer'], self.use['answer'])
        self.assertEqual(query['context_answer']['answer_zh'], self.use['answer_zh'])
        self.assertEqual(query['context_answer']['guide_url'],
                         'https://drgezhang.com/research/' + SLUG + '.html#model-evaluation')
        self.assertEqual({source['id'] for source in query['context_answer']['sources']}, set(self.use['answer_source_ids']))
        self.assertEqual(self.discovery, before)
        self.assertEqual(combined['works'], before['works'])
        self.assertEqual(combined['all_questions'], before['all_questions'])
        page = render_intent_layer(combined)
        qa_id = query['work_refs'][0]['preview_question_id']
        original = next(qa for qa in combined['all_questions'] if qa['id'] == qa_id)
        fragment = page.split('data-intent-focused="ai-heart-failure-2"', 1)[1].split('</section>', 1)[0]
        self.assertLess(fragment.index(html.escape(self.use['answer'])), fragment.index(html.escape(original['answer'])))
        validate_intent_html(page, combined, guides.ROOT)
        with self.assertRaises(ValueError):
            validate_intent_html(page.replace(html.escape(self.use['answer']), 'Truncated synthesis'), combined)

    def test_optional_section_absent_keeps_legacy_guides_byte_identical(self):
        circadian = next(d for d in guides.load_comparisons() if d['slug'] == 'circadian-evidence-levels')
        packet = guides.comparison_packet(circadian)
        self.assertNotIn('research_use', packet)
        for ext, rendered in zip(('html', 'md', 'json'), guides.render_comparison(packet)):
            self.assertEqual(rendered, (guides.ROOT / 'research' / (circadian['slug'] + '.' + ext)).read_text(encoding='utf-8'))

    def test_unknown_source_missing_source_and_changed_study_identity_fail(self):
        changes = [lambda u: u.update(answer_source_ids=['unknown-source']),
                   lambda u: u['checklist'][0].update(source_ids=[]),
                   lambda u: u['comparison']['rows'][0].update(doi='10.1234/another-study'),
                   lambda u: u['sources'][2].update(title='Another paper'),
                   lambda u: u['study_roles'].reverse(),
                   lambda u: u['sources'][0].update(url='https://user:secret@example.org/paper'),
                   lambda u: u['sources'][0].update(url='https://doi.org/10.1234/another-study'),
                   lambda u: u['sources'][0].update(locator=''),
                   lambda u: u.update(id='../outside')]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.changed_packet(change)

    def test_unknown_guide_and_section_fail_closed(self):
        for slug, section in (('unknown-guide', 'model-evaluation'), (SLUG, 'unknown-section')):
            with self.subTest(slug=slug, section=section), self.assertRaises(ValueError):
                guides.resolve_research_use(slug, section)

    def test_guide_controller_still_requires_reviewed_fingerprint(self):
        data = copy.deepcopy(self.data)
        data['research_use']['answer'] += ' Unreviewed change.'
        with self.assertRaisesRegex(ValueError, 'contract'):
            guides.comparison_packet(data)


if __name__ == '__main__':
    unittest.main()
