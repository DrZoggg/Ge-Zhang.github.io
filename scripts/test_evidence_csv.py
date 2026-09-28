"""Study-level CSV round trips; safety is reversible, never silently destructive."""
import copy
import csv
import io
import json
from evidence_reuse import CSV_FIELDS, csv_safe, evidence_rows, render_csv, is_argument
from build_publications import load_deep_content
from sync_common import ROOT


def check():
    paths=set();count=0
    for p in json.loads((ROOT/'publications.json').read_text(encoding='utf-8')):
        if p['paper_geo_status']!='v2': continue
        c=load_deep_content(p)
        path=ROOT/'assets/evidence'/(p['slug']+'.csv');paths.add(path.name)
        raw=path.read_bytes()
        assert raw==render_csv(p,c,p['paper_url']).encode('utf-8')
        reader=csv.DictReader(io.StringIO(raw.decode('utf-8'),newline=''))
        actual=list(reader);expected=list(evidence_rows(p,c,p['paper_url']))
        assert reader.fieldnames==CSV_FIELDS and len(actual)==len(c['key_findings'])
        assert actual==[{k:csv_safe(v) for k,v in row.items()} for row in expected]
        for row,f in zip(actual,c['key_findings']):
            assert json.loads(row['reported_evidence'])==f['evidence']
            assert json.loads(row['scope_does_not_establish'])==c['evidence_scope']['does_not_establish']
            assert json.loads(row['limitations'])==c['limitations']
            assert row['record_kind']==('argument' if is_argument(c) else 'finding')
        page=(ROOT/'papers'/(p['slug']+'.html')).read_text(encoding='utf-8')
        assert '../assets/evidence/'+path.name in page
        count+=len(actual)
    assert paths=={p.name for p in (ROOT/'assets/evidence').glob('*.csv')}
    for value in ['=1+1','+cmd','-1+2','@SUM(A1)',' \t=1','\tplain','\rplain','\nplain']:
        assert csv_safe(value)=="'"+value
    for value in ['normal','α,β "quoted"\nsecond line','95% CI (1.2–3.4)','["=1"]']:
        assert csv_safe(value)==value
    c=copy.deepcopy(c); c['key_findings'][0]['claim']='=HYPERLINK("bad")\nα,β "quoted"'
    rows=list(csv.DictReader(io.StringIO(render_csv(p,c,p['paper_url']),newline='')))
    assert rows[0]['claim']=="'"+c['key_findings'][0]['claim']
    assert json.loads(rows[0]['reported_evidence'])==c['key_findings'][0]['evidence']
    print(f'CSV PASS: {len(paths)} files / {count} exact source rows; JSON lists, narrative kind, commas/quotes/newlines/Unicode/formula injection')


if __name__=='__main__': check()
