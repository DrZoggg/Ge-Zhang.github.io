"""One faithful question route per current V2, without new scientific prose."""
import json
import hashlib
import html
import tempfile
import unittest
from pathlib import Path
from sync_common import ROOT
from test_machine_interfaces import Document, local
from urllib.parse import urlparse

def validate_questions():
    items=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
    rows=json.loads((ROOT/'research/questions.json').read_text(encoding='utf-8'))['questions']
    expected={p['doi'] for p in items if p['paper_geo_status']=='v2'}
    assert {r['doi'] for r in rows}==expected and len(rows)==len(expected)
    assert len({r['question'] for r in rows})==len(rows)
    page=(ROOT/'research/questions.html').read_text(encoding='utf-8');document=Document(page)
    assert 'Questions addressed by publications in this research program' in page
    assert 'not an exhaustive or systematic review' in page
    assert page.count('<strong>Does not establish:</strong>') == len(rows)
    assert 'FAQPage' not in page and 'QAPage' not in page and 'ScholarlyArticle' not in page
    for row in rows:
        file,pointer=row['source'].split('#')
        source=json.loads((ROOT/file).read_text(encoding='utf-8'))
        for key in pointer.strip('/').split('/'):
            source=source[int(key)] if isinstance(source,list) else source[key]
        assert source==row['question']
        target=Document(local(row['answer_url']).read_text(encoding='utf-8'))
        assert target.ids.count(urlparse(row['answer_url']).fragment)==1
        assert any(l.get('href')==row['answer_url'] for l in document.links)
        content=json.loads((ROOT/'data/deep_geo'/f'{row["id"]}.json').read_text(encoding='utf-8'))
        assert row['evidence_scope'] in content['evidence_scope']['does_not_establish']
        assert row['evidence_scope_kind'] == 'does_not_establish'
        assert row['concepts']==[v for values in content['concepts'].values() for v in values]
    return len(rows)
class QuestionTests(unittest.TestCase):
    def test_source_bound_routes(self):validate_questions()
    def test_complete_question_catalog_is_static_and_points_to_existing_answers(self):
        payload=json.loads((ROOT/'research/questions.json').read_text(encoding='utf-8'))
        public=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        self.assertEqual(payload['version'],1)
        self.assertEqual(payload['discovery_version'],2)
        self.assertEqual([w['id'] for w in payload['works']],[p['slug'] for p in public])
        page=(ROOT/'research/questions.html').read_text(encoding='utf-8');document=Document(page)
        self.assertEqual(page.count('data-question-route'),len(payload['all_questions']))
        self.assertEqual(len(document.ids),len(set(document.ids)))
        for work in payload['works']:
            self.assertTrue(any(link.get('href')==work['paper_url'] for link in document.links))
        for question in payload['all_questions']:
            self.assertIn(html.escape(question['question']),page)
            self.assertIn(html.escape(question['answer_url'],quote=True),page)
            target=Document(local(question['answer_url']).read_text(encoding='utf-8'))
            self.assertEqual(target.ids.count(urlparse(question['answer_url']).fragment),1)
        self.assertIn('<noscript>',page)
        self.assertNotIn('https://drgezhang.com/data/',page)
    def test_reviewed_answer_previews_are_complete_source_bound_and_additive(self):
        rows=json.loads((ROOT/'research/questions.json').read_text(encoding='utf-8'))['questions']
        settings=json.loads((ROOT/'data/question_index.json').read_text(encoding='utf-8'))
        previews=[row for row in rows if 'answer_preview' in row]
        self.assertEqual({r['doi'] for r in previews},set(settings['answer_previews']))
        self.assertLessEqual(len(previews),6)
        page=(ROOT/'research/questions.html').read_text(encoding='utf-8')
        self.assertEqual(page.count('data-reviewed-answer='),len(previews))
        for row in previews:
            preview=row['answer_preview'];path,pointer=preview['source'].split('#')
            text=(ROOT/path).read_text(encoding='utf-8');gold=json.loads(text)
            choice=settings['papers'][row['doi']];qa=gold['qa'][choice['qa_index']-1]
            self.assertEqual(pointer,f"/qa/{choice['qa_index']-1}/answer")
            self.assertEqual(row['question'],qa['question'])
            self.assertEqual(preview['answer'],qa['answer'])
            self.assertEqual(preview['answer_sha256'],hashlib.sha256(qa['answer'].encode('utf-8')).hexdigest())
            self.assertEqual(preview['source_content_sha256'],hashlib.sha256(text.encode('utf-8')).hexdigest())
            self.assertEqual(preview['does_not_establish'],gold['evidence_scope']['does_not_establish'])
            self.assertEqual(preview['evidence_refs'],qa['evidence_refs'])
            self.assertIn(html.escape(preview['answer']),page)
            target=Document(local(row['paper_url']).read_text(encoding='utf-8'))
            for ref in preview['evidence_sources']:
                kf=next(f for f in gold['key_findings'] if f['id']==ref['id'])
                self.assertEqual(ref['source_locator'],kf['source_locator'])
                self.assertEqual(ref['source'],path+'#/key_findings/'+str(gold['key_findings'].index(kf)))
                self.assertEqual(target.ids.count(urlparse(ref['evidence_url']).fragment),1)
                self.assertIn(html.escape(ref['evidence_url'],quote=True),page)

    def test_preview_pilot_rejects_overflow_and_navigation_answer_guessing(self):
        from scholarly_discovery import question_records
        items=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        contents={p['doi']:json.loads((ROOT/'data/deep_geo'/f"{p['slug']}.json").read_text(encoding='utf-8'))
                  for p in items if p['paper_geo_status']=='v2'}
        fields={p['slug']:{k:None for k in ['citation_bibtex_url','citation_ris_url','citation_csl_json_url']} for p in items}
        settings=json.loads((ROOT/'data/question_index.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data').mkdir()
            (root/'data/evidence_navigation.json').write_text((ROOT/'data/evidence_navigation.json').read_text(encoding='utf-8'),encoding='utf-8')
            for selected in [list(settings['papers'])[:7],['10.1038/s41467-024-50415-9']]:
                settings['answer_previews']=selected
                (root/'data/question_index.json').write_text(json.dumps(settings),encoding='utf-8')
                with self.assertRaises(ValueError):question_records(items,contents,fields,root)
if __name__=='__main__':unittest.main()
