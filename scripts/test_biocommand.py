"""Static contracts for the small progressive visual layer; browser QA is external."""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Nodes(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.nodes = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


class BioCommandTests(unittest.TestCase):
    def test_progressive_script_is_deferred_and_surface_scoped(self):
        for name in ('index.html', 'publications.html'):
            nodes = Nodes((ROOT / name).read_text(encoding='utf-8')).nodes
            scripts = [a for tag, a in nodes if tag == 'script' and a.get('src') == 'assets/biocommand.js']
            self.assertEqual(len(scripts), 1)
            self.assertIn('defer', scripts[0])
        for paper in (ROOT / 'papers').glob('*.html'):
            self.assertNotIn('biocommand.js', paper.read_text(encoding='utf-8'))

    def test_decorative_scene_and_pause_control(self):
        nodes = Nodes((ROOT / 'index.html').read_text(encoding='utf-8')).nodes
        scenes = [a for tag, a in nodes if tag == 'svg' and a.get('class') == 'bio-scene']
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]['aria-hidden'], 'true')
        self.assertEqual(scenes[0]['focusable'], 'false')
        controls = [a for tag, a in nodes if tag == 'button' and a.get('class') == 'motion-toggle']
        self.assertEqual(len(controls), 1)
        self.assertIn('hidden', controls[0])  # no dead no-JS control
        self.assertEqual(controls[0]['aria-pressed'], 'false')
        ids = [a['id'] for _, a in nodes if 'id' in a]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_scroll_hijack_or_content_loading(self):
        js = (ROOT / 'assets/biocommand.js').read_text(encoding='utf-8')
        for forbidden in ('fetch(', 'innerHTML', 'document.write', 'preventDefault', 'setInterval', 'requestAnimationFrame'):
            self.assertNotIn(forbidden, js)
        self.assertNotRegex(js, r'addEventListener\([\'"](?:scroll|wheel|touchmove)[\'"]')
        self.assertIn('prefers-reduced-motion: reduce', js)
        self.assertIn('Math.max(-8, Math.min(8, value))', js)
        self.assertIn('visibilitychange', js)
        self.assertIn('IntersectionObserver', js)

    def test_css_does_not_hide_content_or_page_overflow(self):
        css = (ROOT / 'assets/style.css').read_text(encoding='utf-8')
        self.assertNotIn('scroll-behavior:smooth', css)
        for selectors, declarations in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
            if re.search(r'\b(?:html|body|main)\b', selectors):
                self.assertNotRegex(declarations, r'overflow(?:-x)?\s*:\s*(?:hidden|clip)')
        self.assertIn('@media(prefers-reduced-motion:reduce)', css)
        self.assertIn('.featured-intro{position:static}', css)


if __name__ == '__main__':
    unittest.main()
