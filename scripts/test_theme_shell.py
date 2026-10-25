"""Focused theme-shell integration and content-date protection; no site build."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_publications import (GA4_INSERTION, render_homepage_research,
                                resolve_lastmod, with_ga4_tag,
                                write_public_html_if_changed)
import research_guides as guides
from site_common import load_profile_config
from sync_common import ROOT
from theme_shell import (GUIDE_THEME_STYLESHEET, THEME_INIT, THEME_RUNTIME,
                         THEME_TOGGLE, with_theme_shell, without_theme_shell)


FIXTURE = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<title>Evidence fixture</title><meta name="citation_doi" content="10.5555/fixture">'
    '<link rel="canonical" href="https://example.org/papers/fixture.html">'
    '<script type="application/ld+json">{"@type":"ScholarlyArticle","name":"Evidence fixture"}</script>'
    '<link rel="stylesheet" href="/assets/style.css"></head><body>'
    '<header><nav><a href="/">Home</a></nav></header>'
    '<main><h1>Evidence fixture</h1><p>Retrospective association, not treatment benefit.</p>'
    '<a href="https://doi.org/10.5555/fixture">DOI</a></main></body></html>'
)


class ThemeShellTests(unittest.TestCase):
    def assert_shell(self, page):
        for fragment in (THEME_INIT, THEME_RUNTIME, THEME_TOGGLE):
            self.assertEqual(page.count(fragment), 1)
        self.assertIn('<head>' + THEME_INIT, page)
        self.assertLess(page.index(THEME_INIT), page.index('<link'))
        self.assertLess(page.index(THEME_RUNTIME), page.index('</head>'))
        self.assertIn('type="button"', THEME_TOGGLE)
        self.assertIn(' hidden>', THEME_TOGGLE)
        self.assertIn('aria-label="Switch to light theme"', THEME_TOGGLE)
        self.assertNotIn('scientific-visuals', THEME_INIT + THEME_RUNTIME + THEME_TOGGLE)

    def test_each_reading_page_family_is_exactly_reversible(self):
        items = json.loads((ROOT / 'publications.json').read_text(encoding='utf-8'))
        ordinary = next(p['slug'] for p in items if p['paper_geo_status'] == 'none')
        for filename in ('papers/aihflevel.html', f'papers/{ordinary}.html',
                         'publications.html', 'research/questions.html',
                         f'research/{guides.SLUG}.html'):
            with self.subTest(path=filename):
                source = (ROOT / filename).read_text(encoding='utf-8')
                themed = with_theme_shell(source, guide=filename.endswith(guides.SLUG + '.html'))
                self.assert_shell(themed)
                self.assertEqual(without_theme_shell(themed), without_theme_shell(source))
                self.assertEqual(with_theme_shell(themed, guide=filename.endswith(guides.SLUG + '.html')), themed)

    def test_existing_ga4_integration_keeps_initializer_first_and_is_idempotent(self):
        page = with_ga4_tag(FIXTURE)
        self.assert_shell(page)
        self.assertEqual(page.count(GA4_INSERTION), 1)
        self.assertLess(page.index(THEME_INIT), page.index(GA4_INSERTION))
        self.assertEqual(with_ga4_tag(page), page)

    def test_theme_only_write_preserves_lastmod_and_real_edits_change_it(self):
        url = 'https://example.org/papers/fixture.html'
        previous = {url: '2026-01-01'}
        themed = with_theme_shell(FIXTURE)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.html'
            path.write_text(FIXTURE, encoding='utf-8')
            changed = write_public_html_if_changed(path, themed)
            self.assertFalse(changed)
            self.assertEqual(resolve_lastmod(url, changed, previous, '2026-10-25'), previous[url])
            self.assertEqual(path.read_text(encoding='utf-8'), themed)
            first = path.read_bytes()
            self.assertFalse(write_public_html_if_changed(path, themed))
            self.assertEqual(path.read_bytes(), first)
            mutations = {
                'science': themed.replace('not treatment benefit', 'proven treatment benefit'),
                'citation': themed.replace('content="10.5555/fixture"', 'content="10.5555/wrong"'),
                'canonical': themed.replace('https://example.org/papers/fixture.html', 'https://example.org/wrong.html'),
                'jsonld': themed.replace('"name":"Evidence fixture"', '"name":"Changed claim"'),
                'doi_link': themed.replace('https://doi.org/10.5555/fixture', 'https://doi.org/10.5555/wrong'),
                'unknown_script': themed.replace('</head>', '<script src="/unreviewed.js"></script></head>'),
                'altered_control': themed.replace('Switch to light theme', 'Unreviewed control'),
            }
            for name, altered in mutations.items():
                with self.subTest(mutation=name):
                    path.write_text(themed, encoding='utf-8')
                    self.assertTrue(write_public_html_if_changed(path, altered))

    def test_shell_normalization_does_not_hide_arbitrary_marked_content(self):
        extra = '<p data-theme-shell="unrecognized">An unreviewed claim.</p>'
        self.assertIn(extra, without_theme_shell(with_theme_shell(FIXTURE).replace('</main>', extra + '</main>')))
        with self.assertRaises(ValueError):
            with_theme_shell(FIXTURE.replace('</main>', extra + '</main>'))
        with self.assertRaises(ValueError):
            without_theme_shell(THEME_INIT + THEME_INIT + FIXTURE)

    def test_guide_render_and_writer_preserve_content_dates_and_markdown(self):
        rendered = guides.render(guides.load(), guides.resolve(guides.load()))
        path = ROOT / 'research' / (guides.SLUG + '.html')
        old = path.read_text(encoding='utf-8')
        md = path.with_suffix('.md').read_text(encoding='utf-8')
        self.assert_shell(rendered[0])
        self.assertEqual(without_theme_shell(rendered[0]), without_theme_shell(old))
        self.assertEqual(rendered[1], md)
        self.assertGreater(rendered[0].index(GUIDE_THEME_STYLESHEET), rendered[0].index('</style>'))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'research').mkdir()
            target = root / 'research' / (guides.SLUG + '.html')
            target.write_text(without_theme_shell(old), encoding='utf-8')
            target.with_suffix('.md').write_text(md, encoding='utf-8')
            with patch.object(guides, 'load', return_value={}), \
                 patch.object(guides, 'resolve', return_value={}), \
                 patch.object(guides, 'render', return_value=rendered):
                self.assertFalse(guides.build(root))
                first = target.read_bytes()
                self.assertFalse(guides.build(root))
                self.assertEqual(target.read_bytes(), first)
                self.assertEqual(target.with_suffix('.md').read_text(encoding='utf-8'), md)

    def test_research_illustration_preserves_controlled_theme_text(self):
        profile = load_profile_config()
        rendered = render_homepage_research(profile)
        self.assertEqual(rendered.count('id="research-field"'), 1)
        from test_visual3 import Document
        document = Document(rendered).root
        figure, = document.find('figure', **{'class': 'research-visual'})
        self.assertIn('not a representation of experimental data', figure.attrs['aria-label'])
        self.assertEqual(figure.find('figcaption'), [])
        button, = figure.find('button', **{'data-scene-pause': 'research-field'})
        for name, value in {'type': 'button', 'aria-controls': 'research-field',
                            'aria-pressed': 'false', 'aria-label': 'Pause research field animation'}.items():
            self.assertEqual(button.attrs.get(name), value)
        self.assertIn('hidden', button.attrs)
        icon, = button.find('svg')
        self.assertEqual(icon.attrs.get('aria-hidden'), 'true')
        self.assertLess(rendered.index('id="research-field"'), rendered.index('class="grid themes"'))
        import html
        for theme in profile['homepage_research']['themes']:
            if theme['enabled']:
                self.assertEqual(rendered.count('<h3>' + html.escape(theme['title']) + '</h3>'), 1)
                self.assertEqual(rendered.count('<p>' + html.escape(theme['description']) + '</p>'), 1)


if __name__ == '__main__':
    unittest.main()
