"""Contribution-first note rendering preserves the approved source records."""
import copy
import html
import json
import unittest
from html.parser import HTMLParser

import limited_evidence as notes
from scholarly_discovery import render_questions
from sync_common import ROOT


LEGACY_NOTICE = ('Limited evidence note. Only the source material identified below has been '
                 'reviewed; this is not a complete Paper GEO V2 assessment.')
NO_ANSWER_NOTICE = 'No full reviewed Gold Q&amp;A is indexed for this record.'


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.hrefs = []
        self.text = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if 'href' in attrs:
            self.hrefs.append(attrs['href'])

    def handle_data(self, data):
        self.text.append(data)


def fixture():
    return {
        'slug': 'source-note', 'evidence_status': 'limited', 'reviewed_on': '2026-11-07',
        'scope': 'Only the identified source sections were reviewed.',
        'sections': [
            {'heading': 'Research question', 'text': 'An existing question & its context.',
             'source_url': 'https://example.org/article?section=1&view=html',
             'source_locator': 'Introduction, paragraph 2 & Figure 1.'},
            {'heading': 'Contribution', 'text': 'An existing source-backed contribution.',
             'source_url': 'https://example.org/article#discussion',
             'source_locator': 'Discussion, paragraph 3.'},
        ],
        'limitations': ['The source does not establish a prospective outcome.'],
        'sources': [{'url': 'https://example.org/article', 'label': 'Original publication',
                     'format': 'Reviewed HTML sections', 'locator': 'Introduction and Discussion.'}],
    }


def work_record(note=None, status='limited'):
    record = fixture()
    return {
        'id': 'source-note', 'title': 'Existing publication', 'type': 'Article',
        'year': 2026, 'journal': 'Example Journal', 'doi': '10.1234/example',
        'paper_url': 'https://example.org/papers/source-note.html',
        'citation_csl_json_url': 'https://example.org/citations/source-note.csl.json',
        'scope': record['scope'], 'limitations': record['limitations'],
        'evidence_status': status,
        **({'author_evidence_note': note} if note is not None else {}),
    }


def card(work):
    page = render_questions([], {'site_url': 'https://example.org', 'researcher_name': 'Researcher'},
                            {'works': [work], 'all_questions': []})
    start = page.index('<article class="card" id="' + html.escape(work['id'], quote=True) + '"')
    return page[start:page.index('</article>', start) + len('</article>')]


class LimitedEvidenceOrderTests(unittest.TestCase):
    def assert_record_preserved(self, record):
        before = copy.deepcopy(record)
        rendered = notes.render_html(record)
        markdown = notes.render_markdown(record)
        document = Document(rendered)
        self.assertEqual(record, before)
        self.assertEqual(document.ids, ['limited-evidence', 'limited-evidence-title'])
        self.assertIn('aria-labelledby="limited-evidence-title" data-evidence-scope="limited"', rendered)
        self.assertTrue(markdown.startswith('<a id="limited-evidence"></a>\n## Author evidence note\n'))
        self.assertIn('<h2 id="limited-evidence-title">Author evidence note</h2>', rendered)
        self.assertNotIn(LEGACY_NOTICE, rendered)
        self.assertNotIn(LEGACY_NOTICE, markdown)
        scope_at = rendered.index('<h3>Evidence scope and limitations</h3>')
        md_scope_at = markdown.index('### Evidence scope and limitations')
        previous = -1
        md_previous = -1
        for section in record['sections']:
            section_at = rendered.index('<h3>' + html.escape(section['heading']) + '</h3>')
            md_section_at = markdown.index('### ' + section['heading'])
            self.assertLess(previous, section_at)
            self.assertLess(md_previous, md_section_at)
            self.assertLess(rendered.index(html.escape(section['text']), section_at), scope_at)
            self.assertLess(markdown.index(section['text'], md_section_at), md_scope_at)
            self.assertIn(section['text'], document.text)
            self.assertIn(section['source_url'], document.hrefs)
            self.assertLess(rendered.index(html.escape(section['source_locator']), section_at), scope_at)
            self.assertIn('Source: [' + section['source_locator'] + '](' + section['source_url'] + ')', markdown)
            previous, md_previous = section_at, md_section_at
        self.assertGreater(rendered.index(html.escape(record['scope']), scope_at), scope_at)
        self.assertGreater(markdown.index(record['scope'], md_scope_at), md_scope_at)
        provenance_at = rendered.index('<h3>Provenance</h3>')
        md_provenance_at = markdown.index('### Provenance')
        for limitation in record['limitations']:
            self.assertLess(scope_at, rendered.index('<li>' + html.escape(limitation) + '</li>'))
            self.assertLess(rendered.index('<li>' + html.escape(limitation) + '</li>'), provenance_at)
            self.assertLess(md_scope_at, markdown.index('- ' + limitation))
            self.assertLess(markdown.index('- ' + limitation), md_provenance_at)
        for source in record['sources']:
            self.assertIn(source['url'], document.hrefs)
            self.assertGreater(rendered.index(' — ' + html.escape(source['format']) + '. '
                                            + html.escape(source['locator'])), provenance_at)
            self.assertIn('- [' + source['label'] + '](' + source['url'] + ') — '
                          + source['format'] + '. ' + source['locator'], markdown)
        self.assertIn('Source review: ' + record['reviewed_on'] + '.', rendered)
        self.assertIn('Source review: ' + record['reviewed_on'] + '.', markdown)

    def test_literal_sections_precede_exact_scope_limits_and_provenance(self):
        self.assert_record_preserved(fixture())

    def test_current_approved_notes_preserve_every_sourced_section(self):
        path = ROOT / 'data/limited_evidence.json'
        original = path.read_bytes()
        records = json.loads(original)['papers']
        self.assertTrue(records)
        for doi, record in records.items():
            with self.subTest(doi=doi):
                self.assert_record_preserved(record)
        self.assertEqual(path.read_bytes(), original)

    def test_none_remains_empty(self):
        self.assertEqual(notes.render_html(None), '')
        self.assertEqual(notes.render_markdown(None), '')

    def test_questions_preview_uses_only_first_original_sourced_section(self):
        record = fixture()
        work = work_record({'sections': record['sections']})
        before = copy.deepcopy(work)
        rendered = card(work)
        first, second = record['sections']
        self.assertEqual(work, before)
        self.assertIn('style="scroll-margin-top:108px"', rendered)
        self.assertIn('Author evidence note', rendered)
        self.assertIn(html.escape(first['heading']), rendered)
        self.assertIn(first['text'], Document(rendered).text)
        self.assertIn(first['source_url'], Document(rendered).hrefs)
        self.assertLess(rendered.index(html.escape(first['text'])), rendered.index(html.escape(work['scope'])))
        self.assertLess(rendered.index(html.escape(first['source_locator'])), rendered.index(html.escape(work['scope'])))
        self.assertLess(rendered.index(html.escape(work['scope'])), rendered.index(html.escape(work['limitations'][0])))
        self.assertNotIn(second['text'], rendered)
        self.assertNotIn(NO_ANSWER_NOTICE, rendered)
        self.assertIn(work['paper_url'], Document(rendered).hrefs)

    def test_current_limited_work_previews_preserve_source_wording(self):
        data = json.loads((ROOT / 'research/questions.json').read_text(encoding='utf-8'))
        records = json.loads((ROOT / 'data/limited_evidence.json').read_text(encoding='utf-8'))['papers']
        by_doi = {work['doi']: work for work in data['works'] if work.get('doi')}
        for doi, record in records.items():
            with self.subTest(doi=doi):
                work = by_doi[doi]
                first = record['sections'][0]
                rendered = card(work)
                document = Document(rendered)
                self.assertIn(first['text'], document.text)
                self.assertIn(first['source_url'], document.hrefs)
                self.assertLess(rendered.index(html.escape(first['source_locator'])),
                                rendered.index(html.escape(record['scope'])))
                self.assertIn(html.escape(record['scope']), rendered)
                for limitation in record['limitations']:
                    self.assertIn(html.escape(limitation), rendered)
                self.assertNotIn(NO_ANSWER_NOTICE, rendered)

    def test_no_note_and_patent_keep_existing_scope_and_no_answer_notice(self):
        for work in [work_record(), work_record({'sections': []}),
                     work_record({'sections': fixture()['sections']}, status='patent_record')]:
            with self.subTest(work=work):
                rendered = card(work)
                self.assertNotIn('Author evidence note', rendered)
                self.assertNotIn('scroll-margin-top', rendered)
                self.assertIn(html.escape(work['scope']), rendered)
                self.assertIn(NO_ANSWER_NOTICE, rendered)
                self.assertIn(work['paper_url'], Document(rendered).hrefs)


if __name__ == '__main__':
    unittest.main()
