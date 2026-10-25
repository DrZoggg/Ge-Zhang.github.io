"""Visual 3.0 protects evidence and source-visible progressive enhancement.

The baseline is the verified production commit before this presentation release.
Browser interaction/viewport acceptance is separate; these tests never claim it.
"""
import hashlib
import io
import json
import subprocess
import tarfile
import unittest
from html.parser import HTMLParser
from urllib.parse import urljoin
from xml.etree import ElementTree

from sync_common import ROOT

BASE = '0cdd95afa12e2198e63175c6093e54c2f32890ea'
PROTECTED_ROOTS = ('data/', 'papers/', 'citations/', 'research/', 'assets/evidence/', '.github/')
PROTECTED_FILES = {
    'publications.html', 'publications.json', 'paper_index.json', 'publication_inventory.csv',
    'assets/evidence-search.json', 'robots.txt', 'llms.txt', 'llms-full.txt', 'CNAME',
    'scripts/sync_common.py', 'scripts/site_common.py', 'scripts/citation_common.py',
    'scripts/profile_control.py', 'scripts/research_themes_control.py', 'scripts/paper_control.py',
    'scripts/indexnow_submit.py',
}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def normalized(value):
    return ' '.join(value.split())


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        return ''.join(c if isinstance(c, str) else c.text() for c in self.children)

    def find(self, tag=None, **attrs):
        result = []
        for c in self.children:
            if isinstance(c, str):
                continue
            if (tag is None or c.tag == tag) and all(c.attrs.get(k) == v for k, v in attrs.items()):
                result.append(c)
            result.extend(c.find(tag, **attrs))
        return result


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, text):
        self.stack[-1].children.append(text)


def frozen():
    archive = subprocess.check_output(['git', '-c', 'core.autocrlf=false', 'archive', BASE], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        return {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}


class Visual3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = frozen()
        cls.before = Document(cls.old['index.html'].decode('utf-8')).root
        cls.home_raw = (ROOT / 'index.html').read_text(encoding='utf-8')
        cls.home = Document(cls.home_raw).root
        cls.profile = json.loads(cls.old['data/profile_config.json'])
        cls.selected = json.loads(cls.old['data/featured_papers.json'])['papers']
        cls.questions = json.loads(cls.old['research/questions.json'])['questions']

    def one(self, root, tag=None, **attrs):
        matches = root.find(tag, **attrs)
        self.assertEqual(len(matches), 1, (tag, attrs))
        return matches[0]

    def test_science_bibliography_identity_inventory_and_pipeline_unchanged(self):
        protected = {p: raw for p, raw in self.old.items()
                     if p.startswith(PROTECTED_ROOTS) or p in PROTECTED_FILES
                     or p.startswith('scripts/sync_')}
        for path, raw in protected.items():
            with self.subTest(path=path):
                current = (ROOT / path).read_bytes().replace(b'\r\n', b'\n')
                self.assertEqual(hashlib.sha256(current).digest(), hashlib.sha256(raw.replace(b'\r\n', b'\n')).digest())
        for folder in ('data/deep_geo', 'papers', 'citations', 'assets/evidence'):
            expected = {p for p in self.old if p.startswith(folder + '/')}
            current = {p.relative_to(ROOT).as_posix() for p in (ROOT / folder).rglob('*') if p.is_file()}
            self.assertEqual(current, expected, folder)

    def test_biographies_themes_person_and_original_profiles_are_preserved(self):
        about = self.one(self.home, 'section', id='about')
        english = self.one(about, 'p', id='biography-en')
        self.assertEqual(english.attrs.get('class'), 'lead')
        self.assertEqual(normalized(english.text()), normalized(self.profile['biography']['en']))
        chinese = self.one(about, 'p', **{'class': 'identity-zh', 'lang': 'zh-CN'})
        self.assertEqual(normalized(chinese.text()), normalized(self.profile['biography']['zh']))
        hero = self.one(self.home, 'section', **{'class': 'hero'})
        self.assertNotIn(self.profile['biography']['en'], hero.text())
        self.assertNotIn(self.profile['biography']['zh'], hero.text())
        h1 = self.one(self.home, 'h1')
        self.assertEqual(normalized(h1.text()), normalized(self.one(self.before, 'h1').text()))
        for anchor in ('research', 'featured', 'profiles'):
            self.one(self.home, id=anchor)
        before_research = self.one(self.before, 'section', id='research')
        research = self.one(self.home, 'section', id='research')
        for tag in ('h2', 'h3', 'p'):
            self.assertEqual([normalized(n.text()) for n in research.find(tag)],
                             [normalized(n.text()) for n in before_research.find(tag)])
        profiles = self.one(self.home, id='profiles')
        self.assertEqual({a.attrs['href'] for a in profiles.find('a')}, set(self.profile['external_links'].values()))
        def schemas(doc):
            return [json.loads(s.text()) for s in doc.find('script', type='application/ld+json')]
        self.assertEqual(schemas(self.home), schemas(self.before))
        self.assertEqual(self.one(self.home, 'link', rel='canonical').attrs,
                         self.one(self.before, 'link', rel='canonical').attrs)

    def test_full_selected_payload_stays_in_initial_html_and_original_order(self):
        region = self.one(self.home, id='featured-papers')
        cards = region.find('article', **{'class': 'card paper'})
        old_cards = self.before.find('article', **{'class': 'card paper'})
        self.assertEqual(len(cards), len(self.selected))
        self.assertEqual(len(cards), len(old_cards))
        for current, original in zip(cards, old_cards):
            self.assertNotIn('hidden', current.attrs)
            self.assertNotIn('style', current.attrs)
            title = self.one(current, 'h3')
            old_title = self.one(original, 'h3')
            self.assertEqual(normalized(title.text()), normalized(old_title.text()))
            self.assertEqual(self.one(title, 'a').attrs['href'], self.one(old_title, 'a').attrs['href'])
            self.assertEqual([normalized(p.text()) for p in current.find('p')],
                             [normalized(p.text()) for p in original.find('p')])
            old_links = {a.attrs['href'] for a in original.find('a')}
            self.assertTrue(old_links <= {a.attrs['href'] for a in current.find('a')})
        button = self.one(self.home, 'button', id='featured-toggle')
        self.assertIn('hidden', button.attrs)
        self.assertEqual(button.attrs.get('type'), 'button')
        self.assertEqual(button.attrs.get('aria-controls'), 'featured-papers')
        self.assertEqual(button.attrs.get('aria-expanded'), 'true')
        self.assertNotIn('hidden', region.attrs)

    def test_home_question_routes_reuse_exact_reviewed_questions_and_context(self):
        section = self.one(self.home, 'section', id='home-questions')
        cards = section.find('article', **{'class': 'home-question'})
        expected_dois = [p['doi'] for p in self.selected[:3]]
        self.assertEqual(len(cards), len(expected_dois))
        by_doi = {q['doi']: q for q in self.questions}
        for card, doi in zip(cards, expected_dois):
            source = by_doi[doi]
            link = self.one(self.one(card, 'h3'), 'a')
            self.assertEqual(normalized(link.text()), normalized(source['question']))
            self.assertEqual(urljoin('https://drgezhang.com/', link.attrs['href']), source['answer_url'])
            self.assertIn(normalized(source['title']), [normalized(p.text()) for p in card.find('p')])

    def test_sitemap_urls_and_nonhome_content_dates_are_unchanged(self):
        def mapping(raw):
            return {node.find('{*}loc').text: node.find('{*}lastmod').text for node in ElementTree.fromstring(raw)}
        old = mapping(self.old['sitemap.xml'])
        current = mapping((ROOT / 'sitemap.xml').read_bytes())
        self.assertEqual(set(current), set(old))
        for url, date in old.items():
            if url != 'https://drgezhang.com/':
                self.assertEqual(current[url], date, url)


if __name__ == '__main__':
    unittest.main()
