"""Exact evidence payload/source correspondence, including semantic boundaries."""
import json
import re
from html import unescape
from evidence_reuse import finding_payload, is_argument
from build_publications import load_deep_content
from sync_common import ROOT


def check():
    count=0; papers=0
    for p in json.loads((ROOT/'publications.json').read_text(encoding='utf-8')):
        if p['paper_geo_status']!='v2': continue
        c=load_deep_content(p);papers+=1
        page=(ROOT/'papers'/(p['slug']+'.html')).read_text(encoding='utf-8')
        ids=re.findall(r'\sid="([^"]+)"',page)
        assert len(ids)==len(set(ids))
        for anchor in ['ev-summary','ev-findings','ev-scope','cite-this-paper']:
            assert anchor in ids
        for f in c['key_findings']:
            m=re.search(r'<script type="application/json" id="ev-copy-'+f['id'].lower()+r'">(.*?)</script>',page,re.S)
            data=json.loads(m[1]);expected=finding_payload(p,c,p['paper_url'],f)
            assert data=={'doi':c['doi'],'finding_id':f['id'],'text':expected}
            for value in [f['claim'],f['context'],f['source_locator'],c['doi'],*c['evidence_scope']['does_not_establish']]:
                assert value in expected
            for e in f['evidence']:
                assert e['label']+': '+e['value'] in expected
            for row in c.get('citation_layer',{}).get('evidence_matrix',[]):
                if row.get('evidence_refs')==[f['id']]: assert row['scope'] in expected
            assert ('Argument ID: ' if is_argument(c) else 'Finding ID: ')+f['id'] in expected
            assert p['paper_url']+'#'+f['id'].lower() in expected
            assert f['id'].lower() in ids
            count+=1
        if is_argument(c): assert '>Key arguments</a>' in page and '<h2>Key Arguments</h2>' in page
    print(f'REUSE PASS: {count} exact contextual payloads in {papers} V2 pages; unique anchors, scope, labels')


if __name__=='__main__': check()
