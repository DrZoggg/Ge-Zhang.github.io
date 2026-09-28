"""Isolated negative staging cases and generic IndexNow guide support."""
import shutil
import tempfile
import unittest
from pathlib import Path
from research_guides import ROOT, SLUG, URL
from validate_staged_guides import validate_staged
from indexnow_submit import detect_changes_with_html, validate_public_html_url


class StagedGuideTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.stage=Path(self.tmp.name)
        for folder in ('research','papers','assets','citations'):
            shutil.copytree(ROOT/folder,self.stage/folder)
        for name in ('index.html','publications.html','sitemap.xml'):
            shutil.copy2(ROOT/name,self.stage/name)

    def test_complete(self): self.assertEqual(validate_staged(self.stage)['guides'],1)

    def test_missing_research(self):
        shutil.rmtree(self.stage/'research')
        with self.assertRaisesRegex(ValueError,'Missing staged guide'): validate_staged(self.stage)

    def test_missing_markdown(self):
        (self.stage/'research'/(SLUG+'.md')).unlink()
        with self.assertRaisesRegex(ValueError,'Missing staged guide'): validate_staged(self.stage)

    def test_missing_anchor(self):
        p=self.stage/'papers/olink-dcm.html'
        p.write_text(p.read_text(encoding='utf-8').replace('id="kf3"','id="removed"'),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'anchor'): validate_staged(self.stage)

    def test_sitemap_missing_file(self):
        p=self.stage/'sitemap.xml'
        p.write_text(p.read_text().replace('</urlset>','<url><loc>https://drgezhang.com/research/missing.html</loc><lastmod>2026-09-28</lastmod></url></urlset>'))
        with self.assertRaisesRegex(ValueError,'no staged file'): validate_staged(self.stage)

    def test_existing_indexnow_support(self):
        self.assertEqual(validate_public_html_url(URL,'drgezhang.com'),URL)
        current={URL:'2026-09-28'}
        self.assertEqual(detect_changes_with_html({},current,['research/'+SLUG+'.html']).added,(URL,))
        self.assertEqual(detect_changes_with_html(current,current,['research/'+SLUG+'.html']).updated,(URL,))
        self.assertFalse(detect_changes_with_html(current,current,['research/'+SLUG+'.md']).urls)


if __name__=='__main__': unittest.main()
