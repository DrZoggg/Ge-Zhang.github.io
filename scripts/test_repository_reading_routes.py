"""Validate explicit repository provenance without changing scientific notes."""
import copy
import json
import unittest
from sync_common import ROOT
import limited_evidence as notes


class RepositoryReadingRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doi = '10.1016/j.gendis.2026.102480'
        cls.publications = json.loads((ROOT / 'publications.json').read_text(encoding='utf-8'))
        cls.publication = next(p for p in cls.publications if p.get('doi') == cls.doi)
        cls.record = notes.load(cls.publications)[cls.doi]

    def test_annotation_preserves_rendered_scientific_text(self):
        before = copy.deepcopy(self.record)
        before['sources'][0].pop('reading_route')
        notes.validate_record(self.doi, before, self.publication)
        for render in [notes.render_html, notes.render_markdown]:
            self.assertEqual(render(before), render(self.record))

    def test_wrong_identity_or_ambiguous_version_cannot_be_published(self):
        invalid = [None, {}, {'kind': 'metadata', 'doi': self.doi, 'version': 'journal_pre_proof'},
                   {'kind': 'institutional_repository_pdf', 'doi': '10.0000/other', 'version': 'journal_pre_proof'},
                   {'kind': 'institutional_repository_pdf', 'doi': self.doi, 'version': 'unknown'},
                   {'kind': 'institutional_repository_pdf', 'doi': self.doi, 'version': []}]
        for route in invalid:
            with self.subTest(route=route):
                record = copy.deepcopy(self.record)
                record['sources'][0]['reading_route'] = route
                with self.assertRaises(ValueError):
                    notes.validate_record(self.doi, record, self.publication)

    def test_local_signed_or_metadata_urls_cannot_be_published_as_pdfs(self):
        for url in ['file:///private/copy.pdf', 'https://example.org/paper.pdf?token=secret',
                    'https://api.crossref.org/works/' + self.doi, 'https://example.org/paper.pdf#page=2',
                    'https://user:secret@example.org/paper.pdf']:
            with self.subTest(url=url):
                record = copy.deepcopy(self.record)
                record['sources'][0]['url'] = url
                with self.assertRaises(ValueError):
                    notes.validate_record(self.doi, record, self.publication)


if __name__ == '__main__':
    unittest.main()
