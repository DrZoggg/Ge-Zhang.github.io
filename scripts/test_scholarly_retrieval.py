"""Offline regression for additive, source-bound scholarly discovery navigation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from scholarly_discovery import reviewed_backlinks, backlink_html, validate_backlink_html, load_identifiers, index_fields


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

    def test_trial_context_requires_the_reported_registry_and_publisher_method(self):
        doi = '10.1234/example'
        item = {'doi': doi, 'slug': 'example'}
        note = {'registry_id': 'NCT03521219', 'registry_last_posted': '2018-05-11',
                'registered_primary_endpoint': 'one-month disease control',
                'published_primary_endpoint': 'objective response',
                'published_methods_url': f'https://publisher.example/{doi}/full#methods'}
        row = {'publisher_url': f'https://publisher.example/{doi}/full',
               'verified_sources': [f'https://doi.org/{doi}'], 'verified_at': '2026-11-06',
               'trial_registry_context': note}
        gold = {'version': 2, 'qa': [], 'concepts': {}, 'provenance': {'trial_registration': 'NCT03521219 as reported'}}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            path = root / 'data/scholarly_identifiers.json'
            def fields():
                path.write_text(json.dumps({'version': 1, 'papers': {doi: row}}), encoding='utf-8')
                identifiers = load_identifiers([item], {}, root)
                return index_fields(item, None, gold, None, 'https://drgezhang.com', identifiers[doi])
            context = fields()['trial_registry_context']
            self.assertEqual(context['registry_url'], 'https://clinicaltrials.gov/study/NCT03521219')
            self.assertEqual(context['registry_data_url'], 'https://clinicaltrials.gov/api/v2/studies/NCT03521219')
            note['registry_id'] = 'NCT03521218'
            with self.assertRaisesRegex(ValueError, 'not bound'):
                fields()
            note['registry_id'] = 'NCT03521219'
            note['published_methods_url'] = f'https://other.example/{doi}/full#methods'
            with self.assertRaisesRegex(ValueError, 'formal publication Methods'):
                fields()
            note['published_methods_url'] = f'https://publisher.example/{doi}0/full#methods'
            with self.assertRaisesRegex(ValueError, 'formal publication Methods'):
                fields()


if __name__ == '__main__': unittest.main()
