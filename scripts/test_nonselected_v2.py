"""Reviewed evidence completeness is independent of curated list membership."""
import copy
import json
import unittest

from build_publications import public_record, render_paper_html
from site_common import ROOT, load_site_config, publication_token
from test_paper_geo_v2 import synthetic_multicohort_fixture


class NonSelectedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.publication, self.content = synthetic_multicohort_fixture()
        self.config = load_site_config()
        self.token = publication_token(self.publication)
        self.public_by_doi = {p['doi']: p for p in json.loads((ROOT/'publications.json').read_text(encoding='utf-8')) if p.get('doi')}

    def record(self, content, *, deep=False, featured=False):
        return public_record(self.publication, config=self.config,
                             deep_tokens={self.token} if deep else set(),
                             featured_tokens={self.token} if featured else set(),
                             deep_contents={self.token: content})

    def test_reviewed_v2_does_not_join_either_curated_list(self):
        before = copy.deepcopy(self.publication)
        item = self.record(self.content)
        self.assertEqual(item['paper_geo_status'], 'v2')
        self.assertFalse(item['deep_geo'])
        self.assertFalse(item['featured'])
        self.assertEqual(self.publication, before)
        self.assertTrue(item['paper_url'].endswith('/' + before['slug'] + '.html'))

    def test_missing_content_has_pending_state_only_for_deep_members(self):
        self.assertEqual(self.record(None)['paper_geo_status'], 'none')
        self.assertEqual(self.record(None, deep=True)['paper_geo_status'], 'pending')
        self.assertTrue(self.record(self.content, featured=True)['featured'])
        self.assertFalse(self.record(self.content, featured=True)['deep_geo'])

    def test_nonselected_legacy_payload_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'reviewed Paper GEO V2'):
            self.record({'version': 1})

    def test_full_evidence_is_visible_without_deep_badge(self):
        item = self.record(self.content)
        page = render_paper_html(item, config=self.config, deep_content=self.content,
                                 public_by_doi={**self.public_by_doi, item['doi']: item})
        self.assertIn('Paper GEO V2</span>', page)
        self.assertNotIn('<span class="badge">Deep GEO</span>', page)
        self.assertIn(self.content['research_question'], page)
        self.assertIn(self.content['author_summary'], page)
        self.assertEqual(page.count('id="ev-summary"'), 1)
        self.assertIn('data-paper-geo-version="2"', page)

    def test_curated_v2_badge_remains_deep_geo(self):
        item = self.record(self.content, deep=True)
        page = render_paper_html(item, config=self.config, deep_content=self.content,
                                 public_by_doi={**self.public_by_doi, item['doi']: item})
        self.assertIn('<span class="badge">Deep GEO</span>', page)
        self.assertNotIn('Paper GEO V2</span>', page)


if __name__ == '__main__':
    unittest.main()
