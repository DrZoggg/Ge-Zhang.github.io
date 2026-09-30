"""Offline regression for additive, source-bound scholarly discovery navigation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from scholarly_discovery import reviewed_backlinks, backlink_html, validate_backlink_html, load_identifiers


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.items = [{'doi': d, 'title': 'Work ' + d, 'paper_url': 'https://drgezhang.com/papers/' + d + '.html'} for d in ['a','b','c']]
        self.contents = {'a': {'version': 2, 'related_papers': [
            {'doi': 'b', 'relationship': 'Reviewed association, not shared validation.'},
            {'doi': 'withdrawn', 'relationship': 'Not public.'}]},
            'b': {'version': 2, 'related_papers': [{'doi': 'c', 'relationship': 'Another reviewed relationship.'}]}}

    def test_only_existing_relation_for_isolated_public_source(self):
        before = copy.deepcopy(self.contents)
        rows = reviewed_backlinks(self.items, self.contents)
        self.assertEqual(set(rows), {'b'})
        self.assertEqual(rows['b'], [{'source_doi':'a', 'title':'Work a',
            'url':'https://drgezhang.com/papers/a.html', 'relationship':self.contents['a']['related_papers'][0]['relationship']}])
        self.assertEqual(self.contents, before)

    def test_no_existing_relation_means_no_invented_link(self):
        self.assertEqual(reviewed_backlinks(self.items, {}), {})
        self.assertEqual(backlink_html(None), '')
        validate_backlink_html('<main>Unchanged science</main>', None)

    def test_exact_markup_and_scientific_relation_fail_closed(self):
        rows = reviewed_backlinks(self.items, self.contents)['b']
        page = backlink_html(rows)
        validate_backlink_html(page, rows)
        for changed in ['', page + page, page.replace('not shared validation', 'shared validation'),
                        page.replace('/a.html', '/c.html'), page.replace('Work a', 'Unreviewed title')]:
            with self.assertRaises(ValueError): validate_backlink_html(changed, rows)
        with self.assertRaises(ValueError): validate_backlink_html(page, None)

    def test_escape_reviewed_text(self):
        rows = [{'title':'A < B', 'url':'https://drgezhang.com/papers/a.html', 'relationship':'A & B'}]
        self.assertIn('A &lt; B', backlink_html(rows))
        self.assertIn('A &amp; B', backlink_html(rows))

    def test_public_nonpriority_identity_allowed_nonpublic_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'data').mkdir()
            payload = {'version':1, 'papers':{'a':{'openalex_id':'https://openalex.org/W123',
                'verified_sources':['https://api.openalex.org/works/W123'], 'verified_at':'2026-09-30'}}}
            def write(): (root/'data/scholarly_identifiers.json').write_text(json.dumps(payload), encoding='utf-8')
            write()
            self.assertEqual(set(load_identifiers(self.items, {}, root)), {'a'})
            payload['papers']['withdrawn'] = payload['papers'].pop('a'); write()
            with self.assertRaises(ValueError): load_identifiers(self.items, {}, root)


if __name__ == '__main__': unittest.main()
