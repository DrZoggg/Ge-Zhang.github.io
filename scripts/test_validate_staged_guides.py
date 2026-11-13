"""Small source-opted-in CSV distribution cases in isolated site fixtures."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import validate_staged_guides as gate


class WorkspaceStagedGuideTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='geo-staged-guide-csv-test-')
        temporary = Path(self.temporary.name).resolve()
        self.assertTrue(temporary.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.assertTrue(temporary.name.startswith('geo-staged-guide-csv-test-'))
        self.addCleanup(self.temporary.cleanup)
        self.source = temporary/'source'; self.stage = temporary/'site'
        for root in (self.source,self.stage):
            (root/'research').mkdir(parents=True)
        self.guide_urls = ['https://drgezhang.com/research/legacy-fixture.html',
                           'https://drgezhang.com/research/comparison-fixture.html']

    def pair(self, name, text):
        for root in (self.source,self.stage):
            (root/name).write_text(text,encoding='utf-8')

    def prepare(self, with_workspace=True):
        self.pair('publications.html','<!doctype html><html><body>Fixture publications</body></html>')
        for url in self.guide_urls:
            slug=Path(url).stem
            links='<a href="../publications.html">Publications</a>'
            if with_workspace and slug=='comparison-fixture':
                links += '<a href="comparison-fixture.worksheet.csv">Worksheet</a>'
                links += '<a href="comparison-fixture.blank.csv">Blank</a>'
            page='<!doctype html><html><head><link rel="canonical" href="'+url+'"></head><body><h1 id="fixture">Fixture guide</h1>'+links+'</body></html>'
            self.pair('research/'+slug+'.html',page)
            self.pair('research/'+slug+'.md','# Fixture guide\n')
        self.pair('research/comparison-fixture.json','{"fixture":true}\n')
        self.pair('research/questions.html','<!doctype html><html><body><a href="comparison-fixture.html#fixture">Fixture</a></body></html>')
        self.pair('research/questions.json','{"fixture":true}\n')
        urls=self.guide_urls+['https://drgezhang.com/research/questions.html']
        self.pair('sitemap.xml','<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                  +''.join('<url><loc>'+url+'</loc></url>' for url in urls)+'</urlset>')
        comparison={'slug':'comparison-fixture'}
        if with_workspace:
            comparison['research_use']={'task_workspace':{}}
            self.pair('research/comparison-fixture.worksheet.csv','Model,DOI\nFixture,10.1000/fixture\n')
            self.pair('research/comparison-fixture.blank.csv','Model,DOI\n,\n')
        self.comparisons=[comparison]

    def validate(self):
        with patch.object(gate,'guide_urls',return_value=self.guide_urls), \
             patch.object(gate,'COMPARISONS',{'comparison-fixture':'fixture-contract'}), \
             patch.object(gate,'load_comparisons',return_value=self.comparisons) as load:
            result=gate.validate_staged(self.stage,self.source)
            load.assert_called_once_with(self.source)
            return result

    def test_both_opted_in_csvs_are_present_and_source_byte_exact(self):
        self.prepare()
        result=self.validate()
        self.assertEqual(result['guides'],2)
        self.assertEqual(result['sitemap_urls'],3)

    def test_each_missing_workspace_csv_is_rejected(self):
        self.prepare()
        for suffix in ('worksheet.csv','blank.csv'):
            with self.subTest(suffix=suffix):
                name='research/comparison-fixture.'+suffix;target=self.stage/name
                target.unlink()
                with self.assertRaisesRegex(ValueError,'Missing staged guide: '+name): self.validate()
                target.write_bytes((self.source/name).read_bytes())

    def test_each_tampered_workspace_csv_is_rejected(self):
        self.prepare()
        for suffix in ('worksheet.csv','blank.csv'):
            with self.subTest(suffix=suffix):
                name='research/comparison-fixture.'+suffix;target=self.stage/name
                target.write_bytes((self.source/name).read_bytes()+b'Extra,row\n')
                with self.assertRaisesRegex(ValueError,'Staged guide payload differs: '+name): self.validate()
                target.write_bytes((self.source/name).read_bytes())

    def test_missing_generated_source_csv_is_rejected(self):
        self.prepare()
        (self.source/'research/comparison-fixture.worksheet.csv').unlink()
        with self.assertRaisesRegex(ValueError,'Missing generated guide source'): self.validate()

    def test_unexpected_research_csv_is_still_rejected(self):
        self.prepare()
        (self.stage/'research/unexpected.csv').write_text('Unexpected\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Unexpected staged research inventory'): self.validate()

    def test_legacy_no_workspace_needs_no_csv(self):
        self.prepare(with_workspace=False)
        self.assertEqual(self.validate()['guides'],2)
        self.assertFalse(list((self.stage/'research').glob('*.csv')))

    def test_matching_csv_filename_is_not_opt_in_without_source_config(self):
        self.prepare(with_workspace=False)
        self.pair('research/comparison-fixture.worksheet.csv','Model,DOI\nFixture,10.1000/fixture\n')
        with self.assertRaisesRegex(ValueError,'Unexpected staged research inventory'): self.validate()


if __name__=='__main__': unittest.main()
