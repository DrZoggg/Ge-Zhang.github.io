"""Five individually licensed V1.6 abstracts; historical sources stay frozen."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import official_abstracts as abstracts
from build_publications import render_official_abstract_html, render_official_abstract_markdown
from sync_common import ROOT, load_master
from test_abstract_additions import V16_FIXTURE, expected_block, reviewed_record, v16_fixtures


class V16AbstractTests(unittest.TestCase):
    def setUp(self):
        self.frozen=json.loads(V16_FIXTURE.read_text(encoding='utf-8'))
        self.records=abstracts.load_official_abstracts(load_master())

    def test_exact_five_approved_sources_and_complete_record_hashes(self):
        self.assertEqual(set(v16_fixtures()), {'10.2147/cia.s462542','10.1186/s10020-024-00963-z',
                                            '10.18063/ijb.740','10.1111/jdi.70462','10.15212/bioi-2026-0017'})
        for doi,fixture in v16_fixtures().items():
            with self.subTest(doi=doi):
                record=reviewed_record(doi)
                self.assertEqual(hashlib.sha256(abstracts.abstract_text(record).encode('utf-8')).hexdigest(),fixture['text_sha256'])
                for key in ('source_url','license','license_url'):
                    self.assertEqual(record[key],fixture[key])
        self.assertNotIn('10.1007/s10238-026-02130-6', self.records)

    def test_all_previous_abstract_records_remain_identical(self):
        previous={doi:self.records[doi]for doi in self.frozen['baseline_dois']}
        digest=hashlib.sha256(json.dumps(previous,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
        self.assertEqual(digest,self.frozen['baseline_records_sha256'])
        self.assertEqual(set(self.records),set(self.frozen['baseline_dois'])|set(v16_fixtures()))

    def test_selected_lists_and_original_29_scientific_payloads_stay_frozen(self):
        paths=self.frozen['protected_files_sha256']
        self.assertEqual(sum(name.startswith('data/deep_geo/')for name in paths),29)
        for name,digest in paths.items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_text(encoding='utf-8').encode('utf-8')).hexdigest(),digest)

    def test_complete_source_abstracts_render_without_rewriting(self):
        for doi in v16_fixtures():
            with self.subTest(doi=doi):
                record=reviewed_record(doi)
                self.assertEqual(render_official_abstract_html(record,doi),expected_block(record,doi))
                markdown=render_official_abstract_markdown(record,doi)
                self.assertIn(record['source_url'],markdown)
                self.assertIn(record['license_url'],markdown)
                paragraphs=record['abstract'].get('sections',[{'text':record['abstract'].get('text','')}])
                for section in paragraphs:self.assertIn(section['text'],markdown)

    def test_article_specific_licenses_and_source_paths_are_not_generalized(self):
        self.assertNotIn('CC-BY-NC-3.0',abstracts.LICENSE_URLS)
        with tempfile.TemporaryDirectory()as temp:
            target=Path(temp)/'abstracts.json'
            with patch.object(abstracts,'PATH',target):
                for doi,changes in [
                    ('10.2147/cia.s462542',{'license':'CC-BY-NC-4.0','license_url':'https://creativecommons.org/licenses/by-nc/4.0/'}),
                    ('10.1111/jdi.70462',{'license':'CC-BY-4.0','license_url':'https://creativecommons.org/licenses/by/4.0/'}),
                    ('10.18063/ijb.740',{'license':'CC-BY-NC-3.0','license_url':'https://creativecommons.org/licenses/by-nc/3.0/'}),
                    ('10.15212/bioi-2026-0017',{'source_url':'https://bio-integration.org/10-15212-bioi-2026-0017/?other=1'}),
                    ('10.1186/s10020-024-00963-z',{'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC1/'}),
                ]:
                    with self.subTest(doi=doi,changes=changes):
                        records=copy.deepcopy(self.records);records[doi].update(changes)
                        target.write_text(json.dumps({'version':1,'papers':records}),encoding='utf-8')
                        with self.assertRaises(ValueError):abstracts.load_official_abstracts(load_master())


if __name__=='__main__':unittest.main()
