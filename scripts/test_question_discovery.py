"""Source fidelity and fail-closed checks for the complete question export."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from question_discovery import build_discovery
from sync_common import ROOT
from test_machine_interfaces import Document


class QuestionDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = json.loads((ROOT / 'publications.json').read_text(encoding='utf-8'))
        cls.contents = {
            p['doi']: json.loads((ROOT / 'data/deep_geo' / (p['slug'] + '.json')).read_text(encoding='utf-8'))
            for p in cls.items if p['paper_geo_status'] == 'v2'
        }
        index = json.loads((ROOT / 'paper_index.json').read_text(encoding='utf-8'))
        by_url = {p['paper_url']: p for p in index['papers']}
        cls.fields = {p['slug']: by_url[p['paper_url']] for p in cls.items}
        cls.data = build_discovery(cls.items, cls.contents, cls.fields, ROOT)

    def test_exact_current_inventory_order_and_all_reviewed_questions(self):
        self.assertNotIn('version', self.data)
        self.assertEqual(self.data['discovery_version'], 2)
        self.assertEqual([w['id'] for w in self.data['works']], [p['slug'] for p in self.items])
        expected = [(p['slug'], i, qa) for p in self.items if p['paper_geo_status'] == 'v2'
                    for i, qa in enumerate(self.contents[p['doi']]['qa'], 1)]
        self.assertEqual(len(self.data['all_questions']), len(expected))
        self.assertEqual(len({q['id'] for q in self.data['all_questions']}), len(expected))
        for row, (slug, i, qa) in zip(self.data['all_questions'], expected):
            self.assertEqual((row['work_id'], row['qa_index']), (slug, i))
            self.assertEqual(row['id'], slug + '--qa-' + str(i))
            self.assertEqual(row['question'], qa['question'])
            self.assertEqual(row['answer'], qa['answer'])
            self.assertEqual(row['answer_sha256'], hashlib.sha256(qa['answer'].encode('utf-8')).hexdigest())

    def test_scope_provenance_and_evidence_refs_resolve_to_current_sources(self):
        work_by_id = {w['id']: w for w in self.data['works']}
        document_by_id = {}
        for item, work in zip(self.items, self.data['works']):
            for field in ('title', 'doi', 'type', 'year', 'journal', 'paper_url', 'markdown_url', 'paper_geo_status'):
                self.assertEqual(work[field], item.get(field))
            if item['paper_geo_status'] != 'v2':
                continue
            gold = self.contents[item['doi']]
            source = 'data/deep_geo/' + item['slug'] + '.json'
            self.assertEqual(work['concepts'], gold['concepts'])
            self.assertEqual(work['field_entry'], gold['discovery_layer']['field_entry'])
            self.assertEqual(work['review_topics'], gold['discovery_layer']['review_topics'])
            self.assertEqual(work['evidence_scope'], gold['evidence_scope'])
            self.assertEqual(work['limitations'], gold['limitations'])
            self.assertEqual(work['provenance'], gold['provenance'])
            self.assertEqual(work['study_profile'], gold['study_profile'])
            self.assertEqual(work['study_profile_source'], source + '#/study_profile')
            self.assertEqual(work['model_profile'], gold.get('model_profile'))
            self.assertEqual(work['model_profile_source'], source + '#/model_profile' if 'model_profile' in gold else None)
            self.assertEqual(work['gold_content_sha256'], hashlib.sha256((ROOT / source).read_text(encoding='utf-8').encode('utf-8')).hexdigest())
            # Gold files are in the public repository, not in the Pages artifact.
            self.assertTrue(work['gold_source_url'].startswith('https://github.com/DrZoggg/Ge-Zhang.github.io/blob/main/'))
            self.assertFalse(work['gold_source_url'].startswith('https://drgezhang.com/data/'))
            document_by_id[item['slug']] = Document((ROOT / 'papers' / (item['slug'] + '.html')).read_text(encoding='utf-8'))
            for index, ref in enumerate(work['key_findings']):
                self.assertEqual({key: ref[key] for key in gold['key_findings'][index]}, gold['key_findings'][index])
                self.assertEqual(ref['id'], gold['key_findings'][index]['id'])
                self.assertEqual(ref['source_locator'], gold['key_findings'][index]['source_locator'])
                self.assertEqual(ref['source'], source + '#/key_findings/' + str(index))
                self.assertEqual(document_by_id[item['slug']].ids.count(urlsplit(ref['evidence_url']).fragment), 1)
        no_encoded_refs = []
        for question in self.data['all_questions']:
            work = work_by_id[question['work_id']]
            gold = self.contents[work['doi']]
            qa = gold['qa'][question['qa_index'] - 1]
            self.assertEqual(question['evidence_refs'], qa.get('evidence_refs', []))
            expected_status = 'resolved' if qa.get('evidence_refs') else 'not_encoded'
            self.assertEqual(question['evidence_refs_status'], expected_status)
            if expected_status == 'not_encoded':
                no_encoded_refs.append((work['id'], question['qa_index']))
            expected_pointer = work['gold_source'] + '#/qa/' + str(question['qa_index'] - 1)
            self.assertEqual(question['question_source'], expected_pointer + '/question')
            self.assertEqual(question['answer_source'], expected_pointer + '/answer')
            refs = {ref['id'] for ref in work['key_findings']}
            self.assertTrue(set(question['evidence_refs']).issubset(refs))
            self.assertEqual(question['answer_url'], work['paper_url'] + '#qa-' + str(question['qa_index']))
            self.assertEqual(document_by_id[work['id']].ids.count(urlsplit(question['answer_url']).fragment), 1)
        self.assertEqual(no_encoded_refs, [(p['slug'], i) for p in self.items if p['paper_geo_status'] == 'v2'
                                         for i, qa in enumerate(self.contents[p['doi']]['qa'], 1)
                                         if not qa.get('evidence_refs')])

    def test_limited_and_patent_records_reuse_scope_without_generating_answers(self):
        limited = json.loads((ROOT / 'data/limited_evidence.json').read_text(encoding='utf-8'))['papers']
        patent = json.loads((ROOT / 'data/patent_evidence.json').read_text(encoding='utf-8'))
        question_ids = {q['work_id'] for q in self.data['all_questions']}
        for work in self.data['works']:
            if work['paper_geo_status'] == 'v2':
                continue
            self.assertNotIn(work['id'], question_ids)
            self.assertEqual(work['question_count'], 0)
            self.assertIsNone(work['evidence_scope'])
            self.assertEqual(work['key_findings'], [])
            if work['doi'] in limited:
                note = limited[work['doi']]
                self.assertEqual(work['evidence_status'], 'limited')
                self.assertEqual(work['scope'], note['scope'])
                self.assertEqual(work['evidence_notice'], note['scope'])
                self.assertEqual(work['limitations'], note['limitations'])
                self.assertEqual(work['provenance'], note['sources'])
            elif work['type'] == 'Patent':
                self.assertIsNone(work['doi'])
                self.assertIsNone(work['doi_url'])
                self.assertEqual(work['evidence_status'], 'patent_record')
                self.assertEqual(work['scope'], patent['evidence_notice'])
                self.assertEqual(work['evidence_notice'], patent['evidence_notice'])
                self.assertEqual(work['limitations'], patent['limitations'])

    def fixture(self, root):
        item = {'slug': 'example', 'doi': '10.1234/example', 'title': 'Example research record',
                'type': 'Article', 'paper_geo_status': 'v2',
                'paper_url': 'https://drgezhang.com/papers/example.html',
                'markdown_url': 'https://drgezhang.com/papers/example.md'}
        gold = {'version': 2, 'doi': item['doi'], 'study_profile': {'profile_type': 'narrative_review'},
                'evidence_scope': {'supports': ['Stated scope.'], 'does_not_establish': ['Stated limitation.']},
                'limitations': ['Additional source limitation.'], 'concepts': {'methods': ['Example method']},
                'qa': [{'question': 'What was reviewed?', 'answer': 'The stated material was reviewed.', 'evidence_refs': ['KF1']}],
                'key_findings': [{'id': 'KF1', 'source_locator': 'Original record, section 1.'}]}
        (root / 'data/deep_geo').mkdir(parents=True)
        return item, gold, {'example': {}}

    def test_source_mutation_and_invalid_refs_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item, gold, fields = self.fixture(root)
            source = root / 'data/deep_geo/example.json'
            source.write_text(json.dumps(gold), encoding='utf-8')
            mutated = copy.deepcopy(gold)
            mutated['qa'][0]['answer'] = 'A changed answer is not the Gold source.'
            with self.assertRaisesRegex(ValueError, 'differs from its Gold'):
                build_discovery([item], {item['doi']: mutated}, fields, root)
            for mutation in ('unresolved', 'duplicate_ref', 'duplicate_finding', 'empty_answer', 'empty_locator'):
                candidate = copy.deepcopy(gold)
                if mutation == 'unresolved':
                    candidate['qa'][0]['evidence_refs'] = ['UNKNOWN']
                elif mutation == 'duplicate_ref':
                    candidate['qa'][0]['evidence_refs'] = ['KF1', 'KF1']
                elif mutation == 'duplicate_finding':
                    candidate['key_findings'].append(copy.deepcopy(candidate['key_findings'][0]))
                elif mutation == 'empty_answer':
                    candidate['qa'][0]['answer'] = ''
                else:
                    candidate['key_findings'][0]['source_locator'] = ''
                source.write_text(json.dumps(candidate), encoding='utf-8')
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    build_discovery([item], {item['doi']: candidate}, fields, root)

    def test_only_known_runtime_cluster_attachment_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item, gold, fields = self.fixture(root)
            (root / 'data/deep_geo/example.json').write_text(json.dumps(gold), encoding='utf-8')
            expected = build_discovery([item], {item['doi']: gold}, fields, root)
            runtime = {**copy.deepcopy(gold), '_research_cluster': {'id': 'resolved-navigation'}}
            self.assertEqual(build_discovery([item], {item['doi']: runtime}, fields, root), expected)
            self.assertNotIn('_research_cluster', json.dumps(expected))
            runtime['qa'][0]['answer'] = 'This changed answer is not accepted.'
            with self.assertRaisesRegex(ValueError, 'differs from its Gold'):
                build_discovery([item], {item['doi']: runtime}, fields, root)
            unknown = {**copy.deepcopy(gold), '_unknown_attachment': {}}
            with self.assertRaisesRegex(ValueError, 'differs from its Gold'):
                build_discovery([item], {item['doi']: unknown}, fields, root)

    def test_missing_gold_and_unsafe_or_duplicate_work_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item, gold, fields = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'lacks reviewed Gold'):
                build_discovery([item], {}, fields, root)
            (root / 'data/deep_geo/example.json').write_text(json.dumps(gold), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'duplicate discovery work ID'):
                build_discovery([item, copy.deepcopy(item)], {item['doi']: gold}, fields, root)
            unsafe = {**item, 'slug': '../other'}
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                build_discovery([unsafe], {}, fields, root)
            identity_only = {**item, 'paper_geo_status': 'none'}
            result = build_discovery([identity_only], {}, fields, root)
            self.assertEqual(result['all_questions'], [])
            self.assertEqual(result['works'][0]['evidence_status'], 'identity_only')
            with self.assertRaisesRegex(ValueError, 'cannot silently promote'):
                build_discovery([identity_only], {item['doi']: gold}, fields, root)


if __name__ == '__main__':
    unittest.main()
