"""Document-level profile semantics without changing the five existing profiles."""
import json
import subprocess
import types
import unittest

from build_publications import (
    render_deep_v2_html, render_deep_v2_markdown, validate_deep_v2_content,
)
from sync_common import ROOT
from test_paper_geo_v2 import synthetic_multicohort_fixture

BASE = 'd29956ac5e8b390e72c4f6bc1856f5ebff4bcb29'


def fixture():
    _, content = synthetic_multicohort_fixture()
    content['study_profile'] = {
        'profile_type': 'bibliometric_corpus',
        'study_design': 'Synthetic bibliometric test fixture',
        'evidence_type': 'Synthetic document-level analysis',
        'population': 'Ten synthetic bibliographic records',
        'primary_endpoint': 'Document distribution',
        'secondary_endpoint': 'Keyword co-occurrence',
        'external_validation': False,
        'data_modalities': ['Bibliographic metadata', 'Keyword records'],
        'scale_metrics': [{'label': 'documents', 'value': '10'}],
        'counting_note': 'Documents are not patients or clinical events.',
    }
    return content


class BibliometricProfileTests(unittest.TestCase):
    def test_document_profile_and_html_markdown_labels(self):
        content = fixture()
        validate_deep_v2_content(content)
        page = render_deep_v2_html(content, [])
        markdown = render_deep_v2_markdown(content, [])
        labels = {
            'Corpus': 'Ten synthetic bibliographic records',
            'Primary analysis': 'Document distribution',
            'Additional analysis': 'Keyword co-occurrence',
            'Independent corpus evaluation': 'No',
        }
        for label, value in labels.items():
            self.assertIn(f'<dt>{label}</dt><dd>{value}</dd>', page)
            self.assertIn(f'- {label}: {value}', markdown)
        for label in ('Population', 'Primary Endpoint', 'Secondary Endpoint',
                      'External validation', 'External dataset evaluation', 'Unique total'):
            self.assertNotIn(f'<dt>{label}</dt>', page)
            self.assertNotIn(f'- {label}:', markdown)
        self.assertIn('Documents are not patients or clinical events.', page)
        self.assertIn('Documents are not patients or clinical events.', markdown)

    def test_reject_clinical_totals_and_prediction_models(self):
        for key, value in [('unique_total_n', 10), ('cohorts', [])]:
            content = fixture()
            content['study_profile'][key] = value
            with self.assertRaisesRegex(ValueError, 'bibliometric_corpus must not use clinical cohort'):
                validate_deep_v2_content(content)
        content = fixture()
        content['model_profile'] = {}
        with self.assertRaisesRegex(ValueError, 'bibliometric_corpus must not use clinical cohort'):
            validate_deep_v2_content(content)

    def test_required_scales_and_counting_boundaries_remain_enforced(self):
        for change in [lambda p: p.update(scale_metrics=[]),
                       lambda p: p.update(counting_note=''),
                       lambda p: p.update(external_validation='not measured'),
                       lambda p: p.update(data_modalities=[])]:
            content = fixture()
            change(content['study_profile'])
            with self.assertRaises(ValueError):
                validate_deep_v2_content(content)

    def test_existing_43_profile_outputs_are_byte_identical(self):
        legacy = types.ModuleType('pre_bibliometric_builder')
        legacy.__file__ = str(ROOT / 'scripts/build_publications.py')
        code = subprocess.check_output(['git', 'show', BASE + ':scripts/build_publications.py'], cwd=ROOT)
        exec(compile(code, legacy.__file__, 'exec'), legacy.__dict__)
        public = json.loads(subprocess.check_output(['git', 'show', BASE + ':publications.json'], cwd=ROOT))
        original = [p for p in public if p['paper_geo_status'] == 'v2']
        self.assertEqual(len(original), 43)
        profile_types = set()
        for paper in original:
            content = json.loads((ROOT / 'data/deep_geo' / (paper['slug'] + '.json')).read_text(encoding='utf-8'))
            profile_types.add(content['study_profile']['profile_type'])
            validate_deep_v2_content(content)
            legacy.validate_deep_v2_content(content)
            self.assertEqual(render_deep_v2_html(content, []), legacy.render_deep_v2_html(content, []), paper['doi'])
            self.assertEqual(render_deep_v2_markdown(content, []), legacy.render_deep_v2_markdown(content, []), paper['doi'])
        self.assertEqual(profile_types, {'clinical_cohort', 'multicohort_omics',
                         'multicohort_observational', 'narrative_review', 'preclinical_multimodal'})


if __name__ == '__main__':
    unittest.main()
