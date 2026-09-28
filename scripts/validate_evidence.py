"""Small delivery gate for generated evidence assets and their linked payloads."""
import json
import re
from urllib.parse import urlsplit
from evidence_discovery import search_corpus
from evidence_reuse import render_csv, finding_payload


def validate_evidence(root, public, contents):
    actual = json.loads((root/'assets/evidence-search.json').read_text(encoding='utf-8'))
    if actual != search_corpus(root,public,contents):
        raise ValueError('Discovery corpus differs from visible public content')
    expected = set()
    for p in public:
        c=contents.get(p.get('doi',''))
        if not c or c.get('version')!=2: continue
        name=p['slug']+'.csv';expected.add(name)
        url=p['paper_url'];page=(root/'papers'/(p['slug']+'.html')).read_text(encoding='utf-8')
        if (root/'assets/evidence'/name).read_bytes()!=render_csv(p,c,url).encode('utf-8'):
            raise ValueError('Evidence CSV differs from source: '+name)
        ids=re.findall(r'\sid="([^"]+)"',page)
        if len(ids)!=len(set(ids)) or '../assets/evidence/'+name not in page:
            raise ValueError('Evidence links/IDs invalid: '+name)
        for f in c['key_findings']:
            m=re.search(r'<script type="application/json" id="ev-copy-'+f['id'].lower()+r'">(.*?)</script>',page,re.S)
            if not m or json.loads(m[1]) != {'doi':c['doi'],'finding_id':f['id'],'text':finding_payload(p,c,url,f)}:
                raise ValueError('Evidence copy payload differs from source: '+name+'/'+f['id'])
        for anchor in ['ev-summary','ev-findings','ev-scope']:
            if anchor not in ids: raise ValueError('Evidence navigation target missing: '+name)
    if expected!={p.name for p in (root/'assets/evidence').glob('*.csv')}:
        raise ValueError('Evidence CSV inventory differs from current public V2 scope')
    return {'csv_files':len(expected),'search_sections':len(actual['documents'])}
