"""Source-bound extraction and fail-closed selection; not scientific proof."""
import copy
import html
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import research_guides as g


class ExtractiveGuideTests(unittest.TestCase):
    def setUp(self): self.data = g.load_comparisons()[0]

    def test_verbatim_profile_scope_answers_and_source_locator_parity(self):
        packet = g.comparison_packet(self.data)
        page, md, raw = g.render_comparison(packet)
        self.assertEqual(json.loads(raw), packet)
        g.validate_page(page, packet['canonical_url'])
        self.assertEqual(len({s['evidence_unit'] for s in packet['studies']}), 3)
        for row,s in zip(self.data['studies'], packet['studies']):
            c = json.loads((g.ROOT/row['source_json']).read_text(encoding='utf-8'))
            for key in ('study_profile','evidence_scope','limitations'):
                self.assertEqual(c[key], s[key])
            for n,qa in zip(row['qa_indices'],s['selected_questions']):
                original = c['qa'][n-1]
                for key in original: self.assertEqual(original[key], qa[key])
                self.assertIn(html.escape(qa['answer']), page)
                self.assertIn(qa['answer'], md)
                self.assertIn(qa['answer_url'],page)
                for ref in qa['supporting_evidence']:
                    self.assertEqual(ref,next(f for f in c['key_findings'] if f['id']==ref['id']))
                    self.assertIn(html.escape(ref['source_locator']), page)
                    self.assertIn(ref['source_locator'],md)
            self.assertIn(c['study_profile']['counting_note'],md)
            for limit in c['limitations']: self.assertIn(limit,md)
        self.assertIn('not a systematic review',packet['scope'])
        self.assertNotIn('ScholarlyArticle',page)

    def test_changed_selection_cannot_silently_publish(self):
        changed = copy.deepcopy(self.data)
        changed['studies'][0]['qa_indices'] = [1]
        with self.assertRaisesRegex(ValueError,'contract'): g.comparison_packet(changed)

    def test_scientific_source_drift_fails_even_if_selection_unchanged(self):
        original = Path.read_text
        source = self.data['studies'][0]['source_json']
        def read(path,*args,**kwargs):
            text = original(path,*args,**kwargs)
            if path.as_posix().endswith(source):
                c = json.loads(text); c['qa'][1]['answer'] += ' Unreviewed assertion.'
                return json.dumps(c)
            return text
        with patch.object(Path,'read_text',read):
            with self.assertRaisesRegex(ValueError,'source changed'): g.comparison_packet(self.data)

    def test_known_scope_traps_kept_with_source_identity(self):
        packet = g.comparison_packet(self.data)
        ihd, crc, review = packet['studies']
        self.assertIn('not 436 independent patients',ihd['study_profile']['counting_note'])
        self.assertIn('not to CRC diagnosis or patient-level prediction',crc['selected_questions'][1]['answer'])
        self.assertIn('not a systematic count of independent studies',review['selected_questions'][2]['answer'])
        self.assertTrue(all(s['doi_url'].endswith(s['doi']) for s in packet['studies']))


if __name__ == '__main__': unittest.main()
