"""Source contracts for the selected clinical-prediction writing guide."""
import copy
import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

import research_guides as g


SLUG = 'cardiovascular-prediction-evidence'
EXPECTED = {
    'aihflevel': ('10.1038/s41467-024-50415-9', [1, 3]),
    'doi-10-2147-cia-s462542': ('10.2147/cia.s462542', [3, 1, 2, 4]),
    'doi-10-1016-j-medd-2026-100004': ('10.1016/j.medd.2026.100004', [1, 3, 4]),
}


class CardiovascularGuideTests(unittest.TestCase):
    def setUp(self):
        self.data = next(d for d in g.load_comparisons() if d['slug'] == SLUG)

    def packet(self, changed):
        # Bypass only the selection digest to exercise the deeper source guards.
        with patch.dict(g.COMPARISONS, {SLUG: g.fingerprint(changed)}):
            return g.comparison_packet(changed)

    def assert_source_parity(self, packet, page, markdown):
        self.assertEqual([s['id'] for s in packet['studies']], list(EXPECTED))
        master = {p['doi']: p for p in json.loads((g.ROOT / 'data/publications_master.json').read_text(encoding='utf-8')) if p.get('doi')}
        for study in packet['studies']:
            doi, positions = EXPECTED[study['id']]
            source = json.loads((g.ROOT / ('data/deep_geo/' + study['id'] + '.json')).read_text(encoding='utf-8'))
            self.assertEqual(study['doi'], doi)
            self.assertEqual(study['evidence_unit'], 'doi:' + doi)
            publication = {key: master[doi][key] for key in ('authors', 'year', 'journal', 'type') if key in master[doi]}
            self.assertEqual(study['publication'], publication)
            fragment = page.split('<article id="' + study['id'] + '">', 1)[1].split('</article>', 1)[0]
            metadata_md = markdown.split('### ' + study['title'] + '\n\n', 1)[1]
            encoded = re.search(r'<p class="guide-publication-authors"><strong>Authors:</strong> (.*?)</p>', fragment).group(1)
            rendered = metadata_md.split('\n\n', 1)[0].removeprefix('**Authors:** ')
            self.assertEqual(html.unescape(encoded).split('; '), publication['authors'])
            self.assertEqual(rendered.split('; '), publication['authors'])
            encoded_details = html.unescape(re.search(r'<p class="guide-publication-details">(.*?)</p>', fragment).group(1))
            rendered_details = metadata_md.split('\n\n', 2)[1]
            fields = [('year', 'Year'), ('journal', 'Journal'), ('type', 'Publication type')]
            self.assertEqual(encoded_details, ' · '.join(label + ': ' + str(publication[key]) for key, label in fields))
            self.assertEqual(rendered_details, ' · '.join('**' + label + ':** ' + str(publication[key]) for key, label in fields))
            for key in ('study_profile', 'evidence_scope', 'limitations'):
                self.assertEqual(study[key], source[key])
            expected_qa = [source['qa'][i - 1] for i in positions]
            self.assertEqual(len(study['selected_questions']), len(expected_qa))
            for actual, original, position in zip(study['selected_questions'], expected_qa, positions):
                for key, value in original.items():
                    self.assertEqual(actual[key], value)
                self.assertIn(html.escape(original['answer']), page)
                self.assertIn(original['answer'], markdown)
                self.assertTrue(actual['answer_url'].endswith('#qa-' + str(position)))
                findings = {f['id']: f for f in source['key_findings']}
                self.assertEqual(actual['supporting_evidence'], [findings[r] for r in original['evidence_refs']])
                for ref in original['evidence_refs']:
                    locator = findings[ref]['source_locator']
                    self.assertIn(html.escape(locator), page)
                    self.assertIn(locator, markdown)
            for suffix in ('.bib', '.ris', '.csl.json'):
                url = 'https://drgezhang.com/citations/' + study['id'] + suffix
                self.assertIn(url, page)
                self.assertIn(url, markdown)
            self.assertIn('https://doi.org/' + doi, page)
            self.assertIn('https://doi.org/' + doi, markdown)

    def test_exact_sources_and_clinical_decision_boundaries(self):
        packet = g.comparison_packet(self.data)
        page, markdown, raw = g.render_comparison(packet)
        self.assertEqual(json.loads(raw), packet)
        self.assert_source_parity(packet, page, markdown)
        hf, tyg, proposal = packet['studies']
        self.assertEqual(hf['study_profile']['unique_total_n'], 1736)
        self.assertEqual([c['n'] for c in hf['study_profile']['cohorts']], [498, 214, 712, 1024])
        self.assertEqual(hf['study_profile']['cohorts'][0]['subset_of'], 'CRCCD Meta')
        self.assertTrue(hf['study_profile']['external_validation'])
        self.assertEqual(hf['study_profile']['primary_endpoint'], 'All-cause mortality')
        self.assertEqual(tyg['study_profile']['unique_total_n'], 717)
        self.assertFalse(tyg['study_profile']['external_validation'])
        self.assertIn('non-cardiovascular death', tyg['study_profile']['primary_endpoint'])
        self.assertIn('same 717', tyg['selected_questions'][2]['answer'])
        self.assertEqual(proposal['study_profile']['narrative_genre'], 'correspondence')
        self.assertNotIn('unique_total_n', proposal['study_profile'])
        self.assertNotIn('external_validation', proposal['study_profile'])
        self.assertIn('no new dataset or validated performance result', proposal['selected_questions'][-1]['answer'])
        self.assertNotIn('ScholarlyArticle', page)
        self.assertNotIn('name="citation_doi"', page)
        self.assertEqual(packet['presentation'], 'contribution-first-v1')
        self.assertIn('Selected author evidence guide', page)
        for study in packet['studies']:
            # The first selected source answer and its locator precede the profile.
            fragment = page.split('<article id="' + study['id'] + '">', 1)[1].split('</article>', 1)[0]
            first = study['selected_questions'][0]
            self.assertLess(fragment.index(html.escape(first['answer'])), fragment.index('Reviewed study profile'))
            self.assertLess(fragment.index(html.escape(first['supporting_evidence'][0]['source_locator'])), fragment.index('Reviewed study profile'))

    def test_wrong_doi_rejected_by_source_identity(self):
        changed = copy.deepcopy(self.data)
        changed['studies'][0]['source_doi'] = '10.9999/not-the-source'
        with self.assertRaisesRegex(ValueError, 'identity/version'):
            self.packet(changed)

    def test_global_intro_is_main_content_and_legacy_scope_semantics_retained(self):
        class IntroParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.path, self.scopes, self.paragraphs = [], [], []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if attrs.get('id') == 'scope':
                    self.scopes.append((tag, [t for t, _ in self.path], attrs))
                if tag == 'p' and any(a.get('id') == 'scope' for _, a in self.path):
                    self.paragraphs.append('')
                if tag not in ('meta', 'link', 'br', 'hr', 'img', 'input'):
                    self.path.append((tag, attrs))

            def handle_endtag(self, tag):
                if self.path and self.path[-1][0] == tag:
                    self.path.pop()

            def handle_data(self, data):
                if any(a.get('id') == 'scope' for _, a in self.path) and self.path[-1][0] == 'p':
                    self.paragraphs[-1] += data

        packet = g.comparison_packet(self.data)
        parser = IntroParser()
        parser.feed(g.render_comparison(packet)[0])
        self.assertEqual(len(parser.scopes), 1)
        tag, ancestors, attrs = parser.scopes[0]
        self.assertIn(tag, ('div', 'section'))
        self.assertIn('main', ancestors)
        self.assertFalse(set(ancestors) & {'aside', 'nav', 'header', 'footer'})
        self.assertNotEqual(attrs.get('role'), 'complementary')
        self.assertEqual(parser.paragraphs, [packet['scope'], packet['reading_rule']])
        # Main/secondary content semantics remain explicit for existing guides.
        legacy = g.load()
        circadian = next(d for d in g.load_comparisons() if d['slug'] == 'circadian-evidence-levels')
        circadian_packet = g.comparison_packet(circadian)
        legacy_cases = [
            (g.render(legacy, g.resolve(legacy))[0], [legacy['scope']]),
            (g.render_comparison(circadian_packet)[0],
             [circadian_packet['scope'], circadian_packet['reading_rule']]),
        ]
        for page, expected_paragraphs in legacy_cases:
            with self.subTest(expected_paragraphs=expected_paragraphs):
                old_parser = IntroParser()
                old_parser.feed(page)
                self.assertEqual(old_parser.scopes[0][0], 'aside')
                self.assertEqual(old_parser.paragraphs, expected_paragraphs)


    def test_invalid_and_unencoded_questions_rejected(self):
        for index, error in ((999, 'question index'), (8, 'encoded source locators')):
            changed = copy.deepcopy(self.data)
            changed['studies'][0]['qa_indices'] = [index]
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, error):
                self.packet(changed)

    def test_scientific_source_drift_rejected(self):
        original = Path.read_text
        def changed_read(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            if path.as_posix().endswith('data/deep_geo/aihflevel.json'):
                content = json.loads(text)
                content['study_profile']['primary_endpoint'] = 'Unreviewed endpoint'
                return json.dumps(content)
            return text
        with patch.object(Path, 'read_text', changed_read):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                g.comparison_packet(self.data)

    def test_parity_check_detects_lost_answer_or_locator(self):
        packet = g.comparison_packet(self.data)
        page, markdown, _ = g.render_comparison(packet)
        answer = packet['studies'][0]['selected_questions'][0]['answer']
        with self.assertRaises(AssertionError):
            self.assert_source_parity(packet, page.replace(html.escape(answer), 'Truncated answer', 1), markdown)
        with self.assertRaises(AssertionError):
            self.assert_source_parity(packet, page, markdown.replace('Fig. 6d', 'Locator omitted'))
        publication = packet['studies'][0]['publication']
        with self.assertRaises(AssertionError):
            self.assert_source_parity(packet, page.replace(html.escape('; '.join(publication['authors'])), html.escape('; '.join(publication['authors'][1:])), 1), markdown)
        changed = copy.deepcopy(packet)
        changed['studies'][0]['publication']['type'] = 'Unreviewed publication category'
        with self.assertRaises(AssertionError):
            self.assert_source_parity(changed, page, markdown)

    def test_same_doi_cannot_be_two_evidence_units(self):
        changed = copy.deepcopy(self.data)
        changed['studies'].append(copy.deepcopy(changed['studies'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate DOI'):
            self.packet(changed)


if __name__ == '__main__':
    unittest.main()
