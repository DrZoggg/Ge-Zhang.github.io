"""Frozen production discovery/science contracts plus reviewed batch 2 additions.

The 3452075 production baseline has 35 V2 pages. Six source-frozen ordinary
works add V2 evidence without changing selected membership or citation identity.
These are transcription checks, not evidence of indexing or citation gains.
"""
import copy
from collections import Counter
import hashlib
import io
import json
import re
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from build_publications import (flatten_concepts, validate_deep_v2_content,
                                write_public_html_if_changed)
from evidence_discovery import without_evidence_ui
from evidence_reuse import render_csv
from paper_discovery import (KEYS, scientific_content, render_html, render_markdown,
                             search_text, validate_layer)
from research_guides import fingerprint, load as load_guide, resolve as resolve_guide
from sync_common import ROOT
from validate_site import (ValidationError, paper_json_ld_object,
                           validate_v2_rendered_page)
from site_common import load_site_config

BATCH = ROOT/'scripts/fixtures/ordinary_v2_batch2_20261016.json'
EXPORTS = ROOT/'scripts/fixtures/paper_discovery_batch2_exports_20261016.json'
BASELINE = '3452075cb5355fc17d45baab1a3989e72f8b5b39'
PENDING = set()
BACKLINK = re.compile(r'<aside\b[^>]*\bid="reviewed-backlinks"[^>]*>.*?</aside>',re.S)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def text_digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def frozen():
    paths = ['data', 'papers', 'citations', 'assets/evidence', 'assets/evidence-search.json',
             'sitemap.xml', 'publications.json', 'paper_index.json',
             'research/questions.json', 'research/questions.html']
    archive = subprocess.check_output(['git', '-c', 'core.autocrlf=false', 'archive', BASELINE,
                                       '--', *paths], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        return {m.name: tar.extractfile(m).read().decode('utf-8')
                for m in tar.getmembers() if m.isfile()}


class PaperDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = frozen()
        cls.batch = json.loads(BATCH.read_text(encoding='utf-8'))
        cls.exports = json.loads(EXPORTS.read_text(encoding='utf-8'))
        cls.items = json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        cls.old_items = json.loads(cls.old['publications.json'])
        cls.sources = {p['slug']: json.loads((ROOT/'data/deep_geo'/(p['slug']+'.json')).read_text(encoding='utf-8'))
                       for p in cls.items if p['paper_geo_status']=='v2'}
        cls.old_sources = {p['slug']: json.loads(cls.old['data/deep_geo/'+p['slug']+'.json'])
                           for p in cls.old_items if p['paper_geo_status']=='v2'}
        cls.new_slugs = {row['slug'] for row in cls.batch['papers'].values()}
        cls.ai = cls.sources['aihflevel']

    def test_exact_reviewed_scope_and_layer(self):
        self.assertEqual(self.batch['base_sha'],BASELINE)
        self.assertEqual(self.exports['base_sha'],BASELINE)
        self.assertEqual(len(self.old_sources),35)
        self.assertEqual(len(self.new_slugs),6)
        self.assertEqual(set(self.sources),set(self.old_sources)|self.new_slugs)
        self.assertEqual(len(self.sources),41)
        layers = {slug:c['discovery_layer'] for slug,c in self.old_sources.items()}
        self.assertEqual(digest(layers),self.exports['baseline_layer_sha256'])
        for c in self.sources.values():
            validate_deep_v2_content(c)
        for doi,row in self.batch['papers'].items():
            raw=(ROOT/'data/deep_geo'/(row['slug']+'.json')).read_bytes().replace(b'\r\n',b'\n')
            self.assertIn(row['content_sha256'],{hashlib.sha256(raw).hexdigest(),
                          hashlib.sha256(raw.replace(b'\n',b'\r\n')).hexdigest()},doi)
            self.assertEqual(self.sources[row['slug']]['doi'],doi)
        controlled=json.loads((ROOT/'data/deep_geo_papers.json').read_text(encoding='utf-8'))['papers']
        self.assertEqual(len(controlled),29)
        self.assertEqual({p['doi'] for p in self.items if p['paper_geo_status']=='pending'},PENDING)

    def test_every_original_scientific_field_stays_frozen(self):
        for slug,c in self.old_sources.items():
            self.assertEqual(self.sources[slug],c,slug)
        for slug,c in self.sources.items():
            # Independent projection: routing alone cannot change a science hash.
            expected={k:v for k,v in c.items() if k!='discovery_layer'}
            self.assertEqual(scientific_content(c),expected)
            altered=copy.deepcopy(c)
            altered['discovery_layer']['scientific_role'] += ' Reviewed routing only.'
            self.assertEqual(scientific_content(altered),expected)
            altered=copy.deepcopy(c)
            altered['key_findings'][0]['claim'] += ' Human treatment benefit is proven.'
            self.assertNotEqual(digest(scientific_content(altered)),digest(expected))
            altered=copy.deepcopy(c)
            altered['evidence_scope']['does_not_establish'][0]='No limitation.'
            self.assertNotEqual(digest(scientific_content(altered)),digest(expected))
            altered['invented_scientific_fact']='Unknown fields must not be silently stripped.'
            self.assertIn('invented_scientific_fact',scientific_content(altered))

    def test_original_html_markdown_and_jsonld_exactly_preserved(self):
        for slug,c in self.sources.items():
            page=(ROOT/'papers'/(slug+'.html')).read_text(encoding='utf-8')
            md=(ROOT/'papers'/(slug+'.md')).read_text(encoding='utf-8')
            block=render_html(c)
            self.assertEqual(page.count(block),1)
            md_block='\n'.join(render_markdown(c))+'\n'
            self.assertEqual(md.count(md_block),1)
            publication=next(p for p in self.items if p['slug']==slug)
            validate_v2_rendered_page(content=c,publication=publication,page=page,markdown=md,
                                     schema=paper_json_ld_object(page,slug),
                                     public_by_doi={p.get('doi'):p for p in self.items},config=load_site_config())
            if slug in self.old_sources:
                before=self.old['papers/'+slug+'.html']
                # Existing backlink UI can gain precisely pinned reviewed links;
                # all remaining HTML, Markdown and JSON-LD remain byte-for-byte.
                self.assertEqual(BACKLINK.sub('',page),BACKLINK.sub('',before),slug)
                self.assertEqual(paper_json_ld_object(page,slug),paper_json_ld_object(before,slug))
                self.assertEqual(without_evidence_ui(BACKLINK.sub('',page)),
                                 without_evidence_ui(BACKLINK.sub('',before)))
                self.assertEqual(md,self.old['papers/'+slug+'.md'])

    def test_protected_inventory_identity_exports_dates_and_pending(self):
        mutable_data={'data/question_index.json'} | {'data/deep_geo/'+s+'.json' for s in self.new_slugs}
        for path,text in self.old.items():
            protected=(path.startswith(('citations/','assets/evidence/'))
                       or path.startswith('data/') and path not in mutable_data)
            if protected:
                self.assertEqual((ROOT/path).read_text(encoding='utf-8'),text,path)
        for path,expected in self.batch['protected_hashes'].items():
            self.assertEqual((ROOT/path).read_text(encoding='utf-8'),self.old[path],path)
        before=json.loads(self.old['publications.json'])
        expected=copy.deepcopy(before)
        for item in expected:
            if item['slug'] in self.new_slugs:
                self.assertEqual(item['paper_geo_status'],'none')
                item['paper_geo_status']='v2'
        self.assertEqual(self.items,expected)
        index=json.loads((ROOT/'paper_index.json').read_text(encoding='utf-8'))['papers']
        self.assertEqual([{key:p.get(key) for key in old}for old,p in zip(self.batch['baseline_identity'],index)],
                         self.batch['baseline_identity'])
        self.assertEqual(len(index),77)
        self.assertEqual(sum(p['deep_geo'] for p in index),29)
        self.assertEqual(sum(p['featured'] for p in index),29)
        changed_backlinks={}
        for p in self.old_items:
            if p['slug'] in self.new_slugs:
                continue
            path='papers/'+p['slug']+'.html'
            page=(ROOT/path).read_text(encoding='utf-8');old=self.old[path]
            self.assertEqual(BACKLINK.sub('',page),BACKLINK.sub('',old),path)
            if BACKLINK.findall(page)!=BACKLINK.findall(old):
                changed_backlinks[path]=digest(BACKLINK.findall(page))
            path='papers/'+p['slug']+'.md'
            self.assertEqual((ROOT/path).read_text(encoding='utf-8'),self.old[path],path)
        self.assertEqual(changed_backlinks,self.exports['approved_backlink_blocks'])
        def sitemap(text):
            return {node.find('{*}loc').text:node.find('{*}lastmod').text
                    for node in ElementTree.fromstring(text)}
        old_map=sitemap(self.old['sitemap.xml'])
        now=sitemap((ROOT/'sitemap.xml').read_text(encoding='utf-8'))
        changed={url for url in old_map if old_map[url]!=now.get(url)}
        expected_urls={'https://drgezhang.com/papers/'+s+'.html' for s in self.new_slugs}
        expected_urls|={'https://drgezhang.com/'+path for path in self.exports['approved_backlink_blocks']}
        expected_urls|={'https://drgezhang.com/research/questions.html','https://drgezhang.com/publications.html'}
        expected_dates={url:self.exports['content_date'] for url in expected_urls}
        # Visual 3.0 changes the homepage presentation through the existing
        # lastmod algorithm; every paper and discovery date stays frozen.
        expected_dates['https://drgezhang.com/']='2026-10-25'
        self.assertEqual(set(now),set(old_map))
        self.assertEqual(changed,set(expected_dates))
        for url in changed:self.assertEqual(now[url],expected_dates[url])

    def test_machine_parity_and_unchanged_question_routes(self):
        index=json.loads((ROOT/'paper_index.json').read_text(encoding='utf-8'))
        before=json.loads(self.old['paper_index.json'])
        self.assertEqual({k:v for k,v in index.items() if k!='papers'},
                         {k:v for k,v in before.items() if k!='papers'})
        self.assertEqual([p['paper_url']for p in index['papers']],[p['paper_url']for p in before['papers']])
        abstracts=json.loads((ROOT/'data/official_abstracts.json').read_text(encoding='utf-8'))['papers']
        old_abstracts=json.loads(self.old['data/official_abstracts.json'])['papers']
        additions=set()  # Batch 2 carries reviewed evidence, no abstract edits.
        self.assertEqual(set(abstracts),set(old_abstracts)|additions)
        self.assertEqual({doi:abstracts[doi]for doi in old_abstracts},old_abstracts)
        for old,row in zip(before['papers'],index['papers']):
            slug=row['paper_url'].rsplit('/',1)[-1].removesuffix('.html')
            expected=copy.deepcopy(old)
            if slug in self.new_slugs:
                content=self.sources[slug]
                expected.update(paper_geo_status='v2',discovery_layer=content['discovery_layer'],
                                question_count=len(content['qa']),concept_count=len(flatten_concepts(content)),
                                evidence_csv_url='https://drgezhang.com/assets/evidence/'+slug+'.csv',
                                official_abstract_available=content['doi']in abstracts)
            self.assertEqual(row,expected,slug)
        old_q=json.loads(self.old['research/questions.json'])
        current=json.loads((ROOT/'research/questions.json').read_text(encoding='utf-8'))
        self.assertEqual({k:v for k,v in old_q.items() if k!='questions'},
                         {k:v for k,v in current.items() if k!='questions'})
        before={q['id']:q for q in old_q['questions']};now={q['id']:q for q in current['questions']}
        self.assertEqual(len(current['questions']),41)
        self.assertEqual(len(now),41)
        self.assertEqual(set(now),set(before)|self.new_slugs)
        self.assertEqual({slug:now[slug]for slug in before},before)
        for slug in self.new_slugs:
            row=now[slug];content=self.sources[slug]
            self.assertEqual(digest(row),self.exports['approved_question_additions'][content['doi']])
            self.assertEqual(row['question'],content['qa'][0]['question'])
            self.assertEqual(row['answer_url'],row['paper_url']+'#qa-1')
            self.assertEqual(row['field_entry'],content['discovery_layer']['field_entry'])
            self.assertEqual(row['review_topics'],content['discovery_layer']['review_topics'])
            self.assertEqual(row['discovery_url'],row['paper_url']+'#paper-discovery')
        config=json.loads((ROOT/'data/question_index.json').read_text(encoding='utf-8'))
        old_config=json.loads(self.old['data/question_index.json'])
        expected=copy.deepcopy(old_config)
        expected['papers'].update({doi:{'qa_index':1}for doi in self.batch['papers']})
        self.assertEqual(config,expected)
        page=(ROOT/'research/questions.html').read_text(encoding='utf-8')
        self.assertEqual(text_digest(page),self.exports['question_html_sha256'])

    def test_search_preserves_every_old_record_and_adds_only_visible_context(self):
        old=json.loads(self.old['assets/evidence-search.json'])
        current=json.loads((ROOT/'assets/evidence-search.json').read_text(encoding='utf-8'))
        self.assertEqual({k:v for k,v in current.items() if k!='documents'},
                         {k:v for k,v in old.items() if k!='documents'})
        clean=lambda row:{k:v for k,v in row.items() if k!='id'}
        # IDs are contiguous regenerated positions; compare every original payload
        # independently of insertion-driven renumbering, including multiplicity.
        counts=Counter(digest(clean(d))for d in old['documents'])
        additions=[]
        for row in current['documents']:
            payload=clean(row);h=digest(payload)
            if counts[h]:counts[h]-=1
            else:additions.append(payload)
        self.assertFalse(+counts,'An original search record was changed or removed')
        self.assertEqual(len(old['documents']),1185)
        self.assertEqual(len(additions),sum(v['count'] for v in self.exports['approved_search_additions'].values()))
        self.assertEqual(len(current['documents']),len(old['documents'])+len(additions))
        self.assertEqual([d['id']for d in current['documents']],list(range(len(current['documents']))))
        self.assertEqual({d['doi']for d in additions},set(self.batch['papers']))
        for doi,reviewed in self.exports['approved_search_additions'].items():
            rows=[d for d in additions if d['doi']==doi]
            self.assertEqual(len(rows),reviewed['count'])
            self.assertEqual(digest(rows),reviewed['payload_sha256'])
        contexts=[d for d in current['documents'] if d['category']=='Research & review context']
        self.assertEqual(len(contexts),41)
        by_doi={c['doi']:c for c in self.sources.values()}
        self.assertEqual({d['doi']for d in contexts},set(by_doi))
        for d in contexts:
            c=by_doi[d['doi']]
            self.assertEqual(d['text'],search_text(c['discovery_layer']))
            self.assertTrue(d['url'].endswith('#paper-discovery'))
            self.assertFalse(d['limitation'])

    def test_optional_backward_compatibility_and_schema_negatives(self):
        original=json.loads(self.old['data/deep_geo/aihflevel.json'])
        original.pop('discovery_layer')  # Exercise the optional pre-routing schema.
        validate_deep_v2_content(original)
        self.assertEqual(render_html(original),'')
        self.assertEqual(render_markdown(original),[])
        self.assertEqual(scientific_content(original),original)
        for key in KEYS:
            bad=copy.deepcopy(self.ai['discovery_layer']);del bad[key]
            with self.assertRaises(ValueError):validate_layer(bad)
        mutations=[lambda l:l.update(extra='Unreviewed field'),
                   lambda l:l.update(field_entry=[]),
                   lambda l:l.update(review_topics=['same','same']),
                   lambda l:l.update(field_entry=['one','two','three']),
                   lambda l:l.update(scientific_role='<script>hidden instruction</script>'),
                   lambda l:l.update(evidence_position=300),
                   lambda l:l.update(related_concepts=['x']*4),
                   lambda l:l.update(citation_contexts=[' ']),
                   lambda l:l.update(review_topics=[l['field_entry'][0]])]
        for mutation in mutations:
            bad=copy.deepcopy(self.ai['discovery_layer']);mutation(bad)
            with self.assertRaises(ValueError):validate_layer(bad)
            with self.assertRaises(ValueError):scientific_content({**self.ai,'discovery_layer':bad})

    def test_context_cannot_be_missing_changed_duplicated_moved_or_hidden(self):
        p=next(p for p in self.items if p['slug']=='aihflevel')
        page=(ROOT/'papers/aihflevel.html').read_text(encoding='utf-8')
        md=(ROOT/'papers/aihflevel.md').read_text(encoding='utf-8')
        block=render_html(self.ai)
        def check(text,markdown=md):
            validate_v2_rendered_page(content=self.ai, publication=p, page=text, markdown=markdown,
                                     schema=paper_json_ld_object(page,'fixture'),
                                     public_by_doi={p.get('doi'):p for p in self.items},
                                     config=load_site_config())
        check(page)
        for altered in [page.replace(block,'',1), page.replace(block,block+block,1),
                        page.replace('data-discovery-layer="1"','data-discovery-layer="1" hidden',1),
                        page.replace(block,'',1).replace('</main>',block+'</main>',1),
                        page.replace('Cardiorenal prognostic stratification','Clinically proven therapy',1)]:
            with self.assertRaises((ValidationError,ValueError)):check(altered)
        with self.assertRaises((ValidationError,ValueError)):check(page,md.replace('Cardiorenal prognostic stratification','Changed interpretation',1))

    def test_original_source_hashes_guide_and_csv_stay_valid(self):
        for p in self.items:
            if p['slug'] not in self.sources:
                continue
            c=self.sources[p['slug']]
            path='assets/evidence/'+p['slug']+'.csv'
            current=(ROOT/path).read_text(encoding='utf-8')
            if p['slug'] in self.old_sources:
                self.assertEqual(current,self.old[path],path)
            else:
                self.assertEqual(text_digest(current),self.exports['approved_csv_sha256'][p['slug']])
            self.assertEqual(render_csv(p,c,p['paper_url']),current)
        guide=load_guide();resolve_guide(guide)
        for row in guide['studies']:
            c=json.loads((ROOT/row['source_json']).read_text(encoding='utf-8'))
            self.assertEqual(fingerprint(scientific_content(c)),row['source_fingerprint'])
            c['evidence_scope']['does_not_establish'][0]='An altered boundary.'
            self.assertNotEqual(fingerprint(scientific_content(c)),row['source_fingerprint'])

    def test_existing_content_date_algorithm_ignores_navigation_not_science(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'paper.html'
            original='<p>Retrospective prediction, not treatment benefit.</p>'
            path.write_text(original,encoding='utf-8')
            routed=render_html(self.ai)+original
            self.assertFalse(write_public_html_if_changed(path,routed))
            self.assertEqual(path.read_text(encoding='utf-8'),routed)
            self.assertFalse(write_public_html_if_changed(path,routed))
            self.assertTrue(write_public_html_if_changed(path,routed.replace('not treatment benefit','proven treatment benefit')))


if __name__=='__main__':unittest.main()
