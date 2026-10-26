"""Lower-homepage presentation/isolation contracts; no build or fixed work counts.

Scientific payload assertions continue to use the existing Visual3 contract.
The stylesheet check guards scope, not particular font sizes or visual spacing.
"""
from html.parser import HTMLParser
import re
import unittest
from urllib.parse import urlsplit
from xml.etree import ElementTree

from sync_common import ROOT
import test_visual3 as visual3


STYLESHEET = 'assets/home-editorial.css'
SECTIONS = {'#research', '#featured', '#home-questions', '#about'}


def split_selectors(text):
    parts, start, depth, quote = [], 0, 0, None
    escaped = False
    for position, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char in '([':
            depth += 1
        elif char in ')]':
            depth -= 1
        elif char == ',' and depth == 0:
            parts.append(text[start:position].strip())
            start = position + 1
    parts.append(text[start:].strip())
    return parts


def css_blocks(text):
    """Yield outer rule blocks, retaining nested media/supports scopes."""
    position = 0
    while text[position:].strip():
        opening = text.find('{', position)
        assert opening >= 0, 'Unexpected unscoped CSS statement'
        header, depth, quote, escaped = text[position:opening].strip(), 1, None, False
        cursor = opening + 1
        while cursor < len(text) and depth:
            char = text[cursor]
            if quote:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in ('"', "'"):
                quote = char
            elif char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            cursor += 1
        assert depth == 0, 'Unbalanced stylesheet block'
        yield header, text[opening + 1:cursor - 1]
        position = cursor


def assert_selector_scope(selector):
    theme = re.match(r'''^(?:html|:root)\[data-theme=(?:"(?:light|dark)"|'(?:light|dark)'|light|dark)\]\s+''', selector)
    scoped = selector[theme.end():] if theme else selector
    home = re.match(r'^(?:body)?\.home\s+', scoped)
    assert home, f'Selector is not homepage-only: {selector}'
    remaining = scoped[home.end():]
    grouped = re.match(r'^:(?:is|where)\(([^()]*)\)', remaining)
    if grouped:
        assert set(split_selectors(grouped[1])) <= SECTIONS, f'Non-editorial group: {selector}'
        assert split_selectors(grouped[1]) != [''], 'Empty editorial group'
        suffix = remaining[grouped.end():]
    else:
        region = re.match(r'^#(?:research|featured|home-questions|about)(?![\w-])', remaining)
        assert region, f'Selector targets the first screen or other content: {selector}'
        suffix = remaining[region.end():]
    assert not suffix.lstrip().startswith(('+', '~')), f'Selector escapes its section: {selector}'


def assert_stylesheet_scope(source):
    css = re.sub(r'/\*[\s\S]*?\*/', '', source)
    assert not re.search(r'@(?:import|font-face|(?:-\w+-)?keyframes|property|counter-style)\b', css, re.I), 'Global dependency/reset definition'
    assert not re.search(r'url\(\s*["\']?(?:https?:|//)', css, re.I), 'New external resource'
    found = []

    def visit(text):
        for header, body in css_blocks(text):
            if header.startswith('@'):
                assert re.match(r'^@(media|supports|container|layer)\b', header), f'Unsupported global rule: {header}'
                visit(body)
            else:
                for selector in split_selectors(header):
                    assert_selector_scope(selector)
                    found.append(selector)
    visit(css)
    assert found, 'No editorial selectors were checked'


class HeadStyles(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.editorial = []
        self.feed(source.split('</head>', 1)[0])

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            parsed = urlsplit(attrs.get('href', ''))
            if parsed.path.lstrip('/') == STYLESHEET:
                assert not parsed.scheme and not parsed.netloc, 'Editorial CSS must be local'
                self.editorial.append(attrs['href'])


class HomeEditorialTests(unittest.TestCase):
    def test_stylesheet_is_confined_to_the_four_lower_home_sections(self):
        assert_stylesheet_scope((ROOT / STYLESHEET).read_text(encoding='utf-8'))

    def test_scope_contract_rejects_global_resets_first_screen_and_leaks(self):
        for css in (
            ':root{--text:red}', 'body{font-size:1px}', 'body.home{--text:red}',
            'html[data-theme="light"]{--text:red}',
            'body.home .hero{display:none}', 'body.home #research,p{display:none}',
            'body.home #research + header{display:none}',
            'body.home :is(#research,header){display:none}',
            '@font-face{font-family:New;src:url(font.woff2)}',
            '@import url(other.css);body.home #research{color:red}',
        ):
            with self.subTest(css=css), self.assertRaises(AssertionError):
                assert_stylesheet_scope(css)
        assert_stylesheet_scope('''
            body.home :is(#research,#featured){--editorial-gap:clamp(1rem,2vw,3rem)}
            @media(max-width:700px){body.home #research .card{padding:1rem}}
            body.home #about a:is(:hover,:focus-visible){text-decoration:underline}
            html[data-theme="light"] body.home #about p{color:var(--text)}
            :root[data-theme=dark] .home #featured .paper{color:var(--text)}
        ''')

    def test_editorial_stylesheet_is_homepage_only_in_current_sitemap(self):
        locations = [node.find('{*}loc').text for node in ElementTree.parse(ROOT / 'sitemap.xml').getroot()]
        self.assertTrue(locations)
        home_count = 0
        for location in locations:
            relative = urlsplit(location).path.lstrip('/') or 'index.html'
            path = ROOT / relative
            self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
            with self.subTest(path=relative):
                styles = HeadStyles(path.read_text(encoding='utf-8')).editorial
                self.assertEqual(len(styles), 1 if relative == 'index.html' else 0)
            home_count += relative == 'index.html'
        self.assertEqual(home_count, 1)

    def test_generated_home_has_no_research_decoration_or_orphan_pause(self):
        source = (ROOT / 'index.html').read_text(encoding='utf-8')
        research, = visual3.Document(source).root.find('section', id='research')
        self.assertEqual(research.find('figure'), [])
        self.assertEqual(research.find(id='research-field'), [])
        self.assertEqual(research.find('button', **{'data-scene-pause': 'research-field'}), [])
        self.assertNotIn('/assets/scientific-visuals/field-', source)

    def test_selected_still_passes_the_existing_precise_source_contract(self):
        # Reuse the existing assertions instead of replacing them with looser
        # editorial checks or introducing a fixed publication/V2 count.
        visual3.Visual3Tests.setUpClass()
        checks = visual3.Visual3Tests()
        checks.assert_selected(checks.home)


if __name__ == '__main__':
    unittest.main()
