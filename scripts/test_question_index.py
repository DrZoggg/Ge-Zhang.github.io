"""One faithful question route per current V2, without new scientific prose."""
import json
import unittest
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
if __name__=='__main__':unittest.main()
