"""Presentation contracts against current sources, without historical Git locks.

Scientific-content contracts remain in their dedicated regression tests. These
checks allow approved source updates and verify their generated presentation;
browser interaction/viewport acceptance remains a separate check.
"""
from copy import deepcopy
from datetime import date
import json
import re
import unittest
from html.parser import HTMLParser
from urllib.parse import urljoin
from xml.etree import ElementTree

from build_publications import update_homepage
from citation_common import citation_skip_reason
from research_guides import URL as GUIDE_URL
from scholarly_discovery import QUESTION_PATH
from site_common import (controller_token, deep_content_path, index_master,
                         load_deep_geo, load_featured, load_profile_config,
                         load_site_config, publication_token)
from sync_common import ROOT, load_master, norm_doi

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


class Visual3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home_raw = (ROOT / 'index.html').read_text(encoding='utf-8')
        cls.home = Document(cls.home_raw).root
        cls.profile = load_profile_config()
        cls.config = load_site_config(cls.profile)
        cls.site = cls.config['site_url'] + '/'
        cls.master = load_master()
        cls.master_by_token = index_master(cls.master)
        cls.selected = load_featured()
        cls.deep = load_deep_geo()
        cls.publications = json.loads((ROOT / 'publications.json').read_text(encoding='utf-8'))
        cls.paper_index = json.loads((ROOT / 'paper_index.json').read_text(encoding='utf-8'))
        cls.questions = json.loads((ROOT / 'research/questions.json').read_text(encoding='utf-8'))['questions']
        cls.contents = {}
        deep_tokens = {controller_token(p) for p in cls.deep}
        for token, publication in cls.master_by_token.items():
            path = deep_content_path(publication)
            if path.is_file():
                content = json.loads(path.read_text(encoding='utf-8'))
                # The established publisher leaves archived ordinary V1 inactive.
                if token in deep_tokens or content.get('version') == 2:
                    cls.contents[token] = content
        cls.sitemap = [(node.find('{*}loc').text, node.find('{*}lastmod').text)
                       for node in ElementTree.parse(ROOT / 'sitemap.xml').getroot()]

    def one(self, root, tag=None, **attrs):
        matches = root.find(tag, **attrs)
        self.assertEqual(len(matches), 1, (tag, attrs))
        return matches[0]

    def assert_inventory(self, master, publications, paper_index, sitemap):
        """Compare current controller/source records, not a particular release."""
        source = index_master(master)
        public = {publication_token(p): p for p in publications}
        self.assertEqual(len(public), len(publications), 'duplicate public identity')
        self.assertEqual(set(public), set(source), 'public inventory differs from master')
        selected = {controller_token(p) for p in self.selected}
        deep = {controller_token(p) for p in self.deep}
        self.assertTrue(selected <= set(source), 'Featured controller has missing work')
        self.assertTrue(deep <= set(source), 'Deep GEO controller has missing work')
        indexed = {p['paper_url']: p for p in paper_index['papers']}
        self.assertEqual(len(indexed), len(paper_index['papers']), 'duplicate indexed URL')
        expected_urls = {urljoin(self.site, f"papers/{p['slug']}.html") for p in source.values()}
        self.assertEqual(set(indexed), expected_urls, 'indexed URL inventory differs from master')
        for token, original in source.items():
            record = public[token]
            for key in ('title', 'journal', 'year', 'type', 'doi', 'authors', 'citation_author', 'slug'):
                self.assertEqual(record.get(key), original.get(key), f'public {key}: {token}')
            expected = {key: original.get(key) for key in ('title', 'journal', 'year', 'type')}
            content = self.contents.get(token)
            status = ('v2' if content.get('version') == 2 else 'v1') if content else (
                'pending' if token in deep else 'none')
            expected.update(doi=original.get('doi', ''),
                            paper_url=urljoin(self.site, f"papers/{original['slug']}.html"),
                            markdown_url=urljoin(self.site, f"papers/{original['slug']}.md"),
                            featured=token in selected, deep_geo=token in deep,
                            paper_geo_status=status)
            for key, value in expected.items():
                # Public records preserve an absent DOI; the machine index emits ''.
                public_value = original.get('doi') if key == 'doi' else value
                self.assertEqual(record.get(key), public_value, f'public {key}: {token}')
                self.assertEqual(indexed[expected['paper_url']].get(key), value, f'index {key}: {token}')
        expected_urls |= {self.site, urljoin(self.site, 'publications.html'),
                          urljoin(self.site, QUESTION_PATH), GUIDE_URL}
        self.assertEqual(len(sitemap), len(dict(sitemap)), 'duplicate sitemap URL')
        self.assertEqual(set(dict(sitemap)), expected_urls, 'sitemap URL inventory differs from sources')
        for url, lastmod in sitemap:
            self.assertEqual(date.fromisoformat(lastmod).isoformat(), lastmod, url)

    def test_current_master_controllers_indexes_and_sitemap_agree(self):
        self.assert_inventory(self.master, self.publications, self.paper_index, self.sitemap)
        self.assertEqual(self.paper_index['researcher'], {
            'name': self.profile['researcher_name'],
            'alternateName': self.profile['researcher_name_zh'],
            'url': self.profile['person_id'], 'orcid': self.profile['orcid'],
        })
        self.assertEqual(self.one(self.home, 'span', id='pubCount').text(), str(len(self.publications)))
        # The Deep GEO list uses its independent controller, including its order.
        llms = (ROOT / 'llms.txt').read_text(encoding='utf-8').split('## Deep GEO\n', 1)[1]
        actual = re.findall(r'^- \[.*?\]\(([^)]+)\)', llms, flags=re.M)
        expected = [urljoin(self.site, f"papers/{self.master_by_token[controller_token(p)]['slug']}.html")
                    for p in self.deep]
        self.assertEqual(actual, expected)

    def test_biographies_themes_person_and_profiles_match_current_profile(self):
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
        self.assertEqual(normalized(h1.text()), self.profile['researcher_name'] + ' ' + self.profile['researcher_name_zh'])
        self.assertEqual(self.one(h1, 'span', lang='zh-CN').text(), self.profile['researcher_name_zh'])
        for anchor in ('research', 'featured', 'profiles'):
            self.one(self.home, id=anchor)
        research = self.one(self.home, 'section', id='research')
        themes = self.profile['homepage_research']
        enabled = [t for t in themes['themes'] if t['enabled']]
        self.assertEqual(normalized(self.one(research, 'h2').text()), themes['heading'])
        self.assertEqual(normalized(self.one(research, 'div', **{'class': 'eyebrow'}).text()), themes['label'])
        self.assertEqual([normalized(n.text()) for n in research.find('h3')], [t['title'] for t in enabled])
        self.assertEqual([normalized(n.text()) for n in research.find('p')], [t['description'] for t in enabled])
        profiles = self.one(self.home, id='profiles')
        self.assertEqual({a.attrs['href'] for a in profiles.find('a')}, set(self.profile['external_links'].values()))
        schemas = [json.loads(s.text()) for s in self.home.find('script', type='application/ld+json')]
        self.assertCountEqual([s['@type'] for s in schemas], ['ProfilePage', 'WebSite'])
        profile_schema = next(s for s in schemas if s['@type'] == 'ProfilePage')
        self.assertEqual(profile_schema['url'], self.site)
        self.assertEqual(profile_schema['@id'], self.site + '#profile')
        person = profile_schema['mainEntity']
        expected = {'@type': 'Person', '@id': self.profile['person_id'],
                    'name': self.profile['researcher_name'],
                    'alternateName': [self.profile['researcher_name_zh']], 'url': self.site,
                    'givenName': self.profile['given_name'], 'familyName': self.profile['family_name'],
                    'identifier': self.profile['external_links']['orcid'],
                    'description': self.profile['description'],
                    'disambiguatingDescription': self.profile['disambiguating_description'],
                    'knowsAbout': self.profile['research_areas']}
        for key, value in expected.items():
            self.assertEqual(person[key], value, key)
        self.assertEqual(set(person['sameAs']), set(self.profile['external_links'].values()))
        affiliations = person['affiliation']
        if isinstance(affiliations, dict):
            affiliations = [affiliations]
        self.assertEqual([a['name'] for a in affiliations], [a['name'] for a in self.profile['affiliations']])
        website = next(s for s in schemas if s['@type'] == 'WebSite')
        self.assertEqual(website['url'], self.site)
        self.assertEqual(website['creator'], {'@id': self.profile['person_id']})
        self.assertEqual(self.one(self.home, 'link', rel='canonical').attrs['href'], self.site)

    def assert_selected(self, home):
        region = self.one(home, id='featured-papers')
        cards = region.find('article', **{'class': 'card paper'})
        self.assertEqual(len(cards), len(self.selected))
        for current, entry in zip(cards, self.selected):
            token = controller_token(entry)
            original = self.master_by_token[token]
            page_url = f"papers/{original['slug']}.html"
            self.assertNotIn('hidden', current.attrs)
            self.assertNotIn('style', current.attrs)
            title = self.one(current, 'h3')
            self.assertEqual(normalized(title.text()), normalized(original.get('title') or 'Untitled work'), 'Selected title/order')
            self.assertEqual(self.one(title, 'a').attrs['href'], page_url, 'Selected URL/order')
            summary = (entry.get('summary') or self.contents.get(token, {}).get('summary') or '').strip()
            if not summary:
                summary = (f"A publication in {original.get('journal') or 'Unknown source'} "
                           f"({original.get('year') or 'n.d.'}) titled “{original.get('title') or 'Untitled work'}”.")
            self.assertEqual([normalized(p.text()) for p in current.find('p')], [normalized(summary)], 'Selected summary')
            kind = self.one(current, 'span', **{'class': 'paper-kind'})
            self.assertEqual(kind.text(), original.get('type') or '')
            expected_links = [page_url]
            doi = norm_doi(original.get('doi'))
            if doi:
                expected_links.append('https://doi.org/' + doi)
                if not citation_skip_reason(original):
                    expected_links.append(page_url + '#cite-this-paper')
            links = self.one(current, 'div', **{'class': 'links'})
            self.assertEqual([a.attrs['href'] for a in links.find('a')], expected_links)
        # JavaScript may collapse later; initial HTML exposes every controlled row.
        button = self.one(home, 'button', id='featured-toggle')
        self.assertIn('hidden', button.attrs)
        self.assertEqual(button.attrs.get('type'), 'button')
        self.assertEqual(button.attrs.get('aria-controls'), 'featured-papers')
        self.assertEqual(button.attrs.get('aria-expanded'), 'true')
        self.assertNotIn('hidden', region.attrs)
        self.assertNotIn('style', region.attrs)
        self.assertNotIn('hidden', self.one(home, 'section', id='featured').attrs)
        self.assertEqual(region.attrs.get('class'), 'grid')

    def test_full_selected_payload_stays_in_initial_html_and_controller_order(self):
        self.assert_selected(self.home)

    def test_home_question_routes_reuse_exact_reviewed_questions_and_context(self):
        section = self.one(self.home, 'section', id='home-questions')
        cards = section.find('article', **{'class': 'home-question'})
        by_doi = {q['doi']: q for q in self.questions}
        self.assertEqual(len(by_doi), len(self.questions), 'duplicate question work')
        selection = json.loads((ROOT / 'data/question_index.json').read_text(encoding='utf-8'))['papers']
        navigation = json.loads((ROOT / 'data/evidence_navigation.json').read_text(encoding='utf-8'))
        self.assertEqual(set(by_doi), set(selection))
        self.assertEqual(set(by_doi), {norm_doi(self.master_by_token[token].get('doi'))
                                     for token, content in self.contents.items()
                                     if content.get('version') == 2})
        for doi, question in by_doi.items():
            token = 'doi:' + doi
            original = self.master_by_token[token]
            self.assertEqual(question['title'], original['title'])
            self.assertEqual(question['paper_url'], urljoin(self.site, f"papers/{original['slug']}.html"))
            choice = selection[doi]
            if choice == {'navigation': True}:
                position, source = next((i, row) for i, row in enumerate(navigation) if row['doi'] == doi)
                pointer, anchor = f'data/evidence_navigation.json#/{position}/question', source['anchor']
            else:
                position = choice['qa_index'] - 1
                source = self.contents[token]['qa'][position]
                pointer = f"data/deep_geo/{original['slug']}.json#/qa/{position}/question"
                anchor = f'qa-{position + 1}'
            self.assertEqual(question['source'], pointer)
            self.assertEqual(question['question'], source['question'])
            self.assertEqual(question['answer_url'], question['paper_url'] + '#' + anchor)
        expected_dois = [norm_doi(self.master_by_token[controller_token(p)].get('doi')) for p in self.selected]
        expected_dois = [doi for doi in expected_dois if doi in by_doi][:3]
        self.assertEqual(len(cards), len(expected_dois))
        for card, doi in zip(cards, expected_dois):
            source = by_doi[doi]
            link = self.one(self.one(card, 'h3'), 'a')
            self.assertEqual(normalized(link.text()), normalized(source['question']))
            self.assertEqual(urljoin(self.site, link.attrs['href']), source['answer_url'])
            self.assertIn(normalized(source['title']), [normalized(p.text()) for p in card.find('p')])

    def test_legitimate_ordinary_update_and_addition_do_not_require_a_new_baseline(self):
        # In-memory source/output fixtures: no build, repository writes or network.
        master, publications, paper_index = deepcopy((self.master, self.publications, self.paper_index))
        ordinary = next(p for p in publications if not p['featured'] and p['paper_geo_status'] == 'none')
        token = publication_token(ordinary)
        title = ordinary['title'] + ' — controlled metadata fixture'
        index_master(master)[token]['title'] = title
        ordinary['title'] = title
        next(p for p in paper_index['papers'] if p['paper_url'] == ordinary['paper_url'])['title'] = title
        self.assert_inventory(master, publications, paper_index, self.sitemap)

        new = {'title': 'Controlled ordinary publication fixture', 'journal': 'Fixture journal',
               'year': 2030, 'type': 'Article', 'doi': '10.5555/visual31.fixture',
               'slug': 'visual31-ordinary-fixture', 'authors': ['Fixture Author']}
        self.assertNotIn(publication_token(new), self.master_by_token)
        master.append(new)
        record = dict(new, paper_url=urljoin(self.site, 'papers/' + new['slug'] + '.html'),
                      markdown_url=urljoin(self.site, 'papers/' + new['slug'] + '.md'),
                      featured=False, deep_geo=False, paper_geo_status='none')
        publications.append(record)
        paper_index['papers'].append(deepcopy(record))
        sitemap = self.sitemap + [(record['paper_url'], date.today().isoformat())]
        self.assert_inventory(master, publications, paper_index, sitemap)
        self.assert_selected(self.home)
        with self.assertRaisesRegex(AssertionError, 'index title'):
            paper_index['papers'][-1]['title'] = 'Stale generated title'
            self.assert_inventory(master, publications, paper_index, sitemap)

    def test_selected_contract_rejects_order_url_summary_and_visibility_damage(self):
        for damage in ('order', 'url', 'summary', 'hidden'):
            with self.subTest(damage=damage):
                home = deepcopy(self.home)
                region = self.one(home, id='featured-papers')
                cards = region.find('article', **{'class': 'card paper'})
                if damage == 'order':
                    a, b = region.children.index(cards[0]), region.children.index(cards[1])
                    region.children[a], region.children[b] = region.children[b], region.children[a]
                elif damage == 'url':
                    self.one(self.one(cards[0], 'h3'), 'a').attrs['href'] = 'papers/wrong.html'
                elif damage == 'summary':
                    self.one(cards[0], 'p').children = ['Unsourced replacement text']
                else:
                    cards[-1].attrs['hidden'] = None
                with self.assertRaises(AssertionError):
                    self.assert_selected(home)

    def test_homepage_footer_is_date_free_and_updates_are_idempotent(self):
        footer = self.one(self.home, 'footer')
        self.assertEqual(normalized(footer.text()), f"© {self.profile['researcher_name']} · Academic website")
        legacy = re.sub(r'(Academic website)(</div></footer>)', r'\1 · Updated 2020-01\2', self.home_raw)
        self.assertIn(' · Updated 2020-01</div></footer>', legacy)
        for source in (self.home_raw, legacy):
            with self.subTest(legacy=source is legacy):
                updated = update_homepage(source, self.config)
                self.assertEqual(normalized(self.one(Document(updated).root, 'footer').text()), normalized(footer.text()))
                self.assertEqual(update_homepage(updated, self.config), updated)


if __name__ == '__main__':
    unittest.main()
