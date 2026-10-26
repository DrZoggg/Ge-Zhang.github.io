"""Frozen 41-V2 production plus centrally reviewed, source-pinned release.

Only 13 approved JSON-pointer values and the named ordinary V2 additions may
change. These are transcription checks, not external AI citation statistics.
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
                                write_public_html_if_changed, with_ga4_tag)
from evidence_discovery import without_evidence_ui
from evidence_reuse import render_csv
from paper_discovery import (KEYS, scientific_content, render_html, render_markdown,
                             search_text, validate_layer)
from research_guides import fingerprint, load as load_guide, resolve as resolve_guide
from sync_common import ROOT
from validate_site import (ValidationError, paper_json_ld_object,
                           validate_v2_rendered_page)
from site_common import load_site_config
from theme_shell import without_theme_shell
from scholarly_discovery import (reviewed_backlinks, validate_backlink_html,
                                 render_questions, question_records)
from central_release_contract import (BASE as BASELINE, RELEASE,
                                      reviewed_source, restore_reviewed_text,
                                      newline_hashes, validate_new_source)

BACKLINK = re.compile(r'<aside\b[^>]*\bid="reviewed-backlinks"[^>]*>.*?</aside>', re.S)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def frozen():
    paths = ['data', 'papers', 'citations', 'assets/evidence', 'assets/evidence-search.json',
             'sitemap.xml', 'index.html', 'publications.html', 'publications.json', 'paper_index.json',
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
        cls.items = json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        cls.old_items = json.loads(cls.old['publications.json'])
        cls.sources = {p['slug']: json.loads((ROOT/'data/deep_geo'/(p['slug']+'.json')).read_text(encoding='utf-8'))
                       for p in cls.items if p['paper_geo_status']=='v2'}
        cls.old_sources = {p['slug']: json.loads(cls.old['data/deep_geo/'+p['slug']+'.json'])
                           for p in cls.old_items if p['paper_geo_status']=='v2'}
        cls.new_slugs = {row['slug'] for row in RELEASE['papers'].values()}
        cls.ai = cls.sources['aihflevel']

    def test_exact_reviewed_scope_and_layer(self):
        self.assertEqual(len(self.old_sources), 41)
        self.assertEqual(set(self.sources), set(self.old_sources) | self.new_slugs)
        for c in self.sources.values():
            validate_deep_v2_content(c)
        for doi, row in RELEASE['papers'].items():
            raw=(ROOT/'data/deep_geo'/(row['slug']+'.json')).read_bytes()
            self.assertIn(row['content_sha256'], newline_hashes(raw), doi)
            self.assertEqual(self.sources[row['slug']]['doi'], doi)
            validate_new_source(doi, self.sources[row['slug']])
        self.assertEqual(sum(p['deep_geo'] for p in self.items), 29)
        self.assertEqual(sum(p['featured'] for p in self.items), 29)
        self.assertFalse(any(p['paper_geo_status']=='pending' for p in self.items))

    def test_every_original_scientific_field_stays_frozen_except_exact_approval(self):
        for slug, c in self.old_sources.items():
            self.assertEqual(self.sources[slug], reviewed_source(slug, c), slug)
        for slug,c in self.sources.items():
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

    def test_original_html_markdown_and_jsonld_exactly_preserved_except_approval(self):
        current_backlinks = reviewed_backlinks(self.items, {c['doi']: c for c in self.sources.values()})
        for p in self.items:
            slug=p['slug']
            page=(ROOT/'papers'/(slug+'.html')).read_text(encoding='utf-8')
            md=(ROOT/'papers'/(slug+'.md')).read_text(encoding='utf-8')
            validate_backlink_html(page, current_backlinks.get(p.get('doi')))
            c=self.sources.get(slug)
            if c:
                self.assertEqual(page.count(render_html(c)),1)
                self.assertEqual(md.count('\n'.join(render_markdown(c))+'\n'),1)
                validate_v2_rendered_page(content=c,publication=p,page=page,markdown=md,
                    schema=paper_json_ld_object(page,slug),
                    public_by_doi={q.get('doi'):q for q in self.items},config=load_site_config())
            if slug not in self.new_slugs:
                before=self.old['papers/'+slug+'.html']
                self.assertEqual(BACKLINK.sub('',restore_reviewed_text(slug,before,page)),
                                 BACKLINK.sub('',before),slug)
                self.assertEqual(paper_json_ld_object(page,slug),paper_json_ld_object(before,slug))
                before_md=self.old['papers/'+slug+'.md']
                self.assertEqual(restore_reviewed_text(slug,before_md,md),before_md,slug)

    def test_protected_inventory_identity_exports_and_source_files(self):
        expected=copy.deepcopy(self.old_items)
        for item in expected:
            if item['slug'] in self.new_slugs:
                self.assertEqual(item['paper_geo_status'],'none')
                item['paper_geo_status']='v2'
        self.assertEqual(self.items,expected)
        self.assertEqual(len(self.items),77)
        patch_paths={'data/deep_geo/'+s+'.json' for s in RELEASE['patches']}
        for path, text in self.old.items():
            if path.startswith('citations/'):
                self.assertEqual((ROOT/path).read_text(encoding='utf-8'),text,path)
            elif path.startswith('data/') and path not in patch_paths and path!='data/question_index.json':
                self.assertEqual((ROOT/path).read_text(encoding='utf-8'),text,path)
        # Canonical DOI/author/year/URL identity is invariant even for upgrades.
        old_index=json.loads(self.old['paper_index.json'])['papers']
        current=json.loads((ROOT/'paper_index.json').read_text(encoding='utf-8'))['papers']
        fields=('doi','title','authors','journal','year','type','paper_url','markdown_url',
                'deep_geo','featured','citation_bibtex_url','citation_ris_url','citation_csl_json_url')
        self.assertEqual([{k:r.get(k) for k in fields} for r in current],
                         [{k:r.get(k) for k in fields} for r in old_index])

    def test_machine_parity_and_unchanged_question_routes(self):
        index=json.loads((ROOT/'paper_index.json').read_text(encoding='utf-8'))
        before=json.loads(self.old['paper_index.json'])
        self.assertEqual({k:v for k,v in index.items() if k!='papers'},
                         {k:v for k,v in before.items() if k!='papers'})
        abstracts=json.loads((ROOT/'data/official_abstracts.json').read_text(encoding='utf-8'))['papers']
        for old,row in zip(before['papers'],index['papers']):
            slug=row['paper_url'].rsplit('/',1)[-1].removesuffix('.html')
            expected=copy.deepcopy(old)
            if slug in self.new_slugs:
                content=self.sources[slug]
                expected.update(paper_geo_status='v2',discovery_layer=content['discovery_layer'],
                    question_count=len(content['qa']),concept_count=len(flatten_concepts(content)),
                    evidence_csv_url='https://drgezhang.com/assets/evidence/'+slug+'.csv',
                    official_abstract_available=content['doi'] in abstracts)
            self.assertEqual(row,expected,slug)
        old_q=json.loads(self.old['research/questions.json'])
        current=json.loads((ROOT/'research/questions.json').read_text(encoding='utf-8'))
        self.assertEqual({k:v for k,v in old_q.items() if k!='questions'},
                         {k:v for k,v in current.items() if k!='questions'})
        prior={q['id']:q for q in old_q['questions']};now={q['id']:q for q in current['questions']}
        self.assertEqual(set(now),set(prior)|self.new_slugs)
        self.assertEqual({slug:now[slug] for slug in prior},prior)
        fields={r['paper_url'].rsplit('/',1)[-1].removesuffix('.html'):r for r in index['papers']}
        self.assertEqual(current['questions'],question_records(self.items,{c['doi']:c for c in self.sources.values()},fields))
        expected=json.loads(self.old['data/question_index.json'])
        expected['papers'].update({doi:{'qa_index':1} for doi in RELEASE['papers']})
        self.assertEqual(json.loads((ROOT/'data/question_index.json').read_text(encoding='utf-8')),expected)
        self.assertEqual((ROOT/'research/questions.html').read_text(encoding='utf-8'),
                         with_ga4_tag(render_questions(current['questions'],load_site_config())))

    def test_search_preserves_every_old_record_with_exact_locator_changes(self):
        old=json.loads(self.old['assets/evidence-search.json'])
        current=json.loads((ROOT/'assets/evidence-search.json').read_text(encoding='utf-8'))
        self.assertEqual({k:v for k,v in current.items() if k!='documents'},
                         {k:v for k,v in old.items() if k!='documents'})
        by_doi={p['doi']:p for p in RELEASE['patches'].values()}
        reviewed_old=copy.deepcopy(old['documents'])
        for row in reviewed_old:
            pairs=dict.fromkeys((c['before'],c['after']) for c in by_doi.get(row['doi'],{}).get('changes',[]))
            for before,after in pairs:
                row['text']=row['text'].replace(before,after)
        clean=lambda row:{k:v for k,v in row.items() if k!='id'}
        counts=Counter(digest(clean(d)) for d in reviewed_old)
        additions=[]
        for row in current['documents']:
            payload=clean(row);h=digest(payload)
            if counts[h]:counts[h]-=1
            else:additions.append(payload)
        self.assertFalse(+counts,'An original search record was changed or removed beyond an approved locator')
        self.assertEqual({d['doi'] for d in additions},set(RELEASE['papers']))
        self.assertEqual(len(additions),sum(7+len(self.sources[s]['key_findings'])+len(self.sources[s]['qa'])+
            len(self.sources[s]['citation_layer']['citation_use_cases']) for s in self.new_slugs))
        self.assertEqual([d['id'] for d in current['documents']],list(range(len(current['documents']))))
        contexts=[d for d in current['documents'] if d['category']=='Research & review context']
        by_doi={c['doi']:c for c in self.sources.values()}
        self.assertEqual({d['doi'] for d in contexts},set(by_doi))
        self.assertEqual(len(contexts),len(by_doi))
        for d in contexts:
            self.assertEqual(d['text'],search_text(by_doi[d['doi']]['discovery_layer']))
            self.assertTrue(d['url'].endswith('#paper-discovery'))
            self.assertFalse(d['limitation'])

    def test_sitemap_inventory_and_real_content_dates(self):
        def sitemap(text):
            return {node.find('{*}loc').text:node.find('{*}lastmod').text for node in ElementTree.fromstring(text)}
        old_map=sitemap(self.old['sitemap.xml'])
        now=sitemap((ROOT/'sitemap.xml').read_text(encoding='utf-8'))
        self.assertEqual(set(now),set(old_map))
        for url,prior_date in old_map.items():
            relative=url.removeprefix('https://drgezhang.com/') or 'index.html'
            if relative in self.old and relative.endswith('.html'):
                current=(ROOT/relative).read_text(encoding='utf-8')
                changed=without_evidence_ui(without_theme_shell(current))!=without_evidence_ui(without_theme_shell(self.old[relative]))
                self.assertEqual(now[url],RELEASE['content_date'] if changed else prior_date,url)
            else:
                self.assertEqual(now[url],prior_date,url)

    def test_original_source_hashes_guide_and_csv_stay_valid(self):
        for p in self.items:
            slug=p['slug']
            if slug not in self.sources:continue
            c=self.sources[slug]
            current=(ROOT/'assets/evidence'/(slug+'.csv')).read_text(encoding='utf-8')
            self.assertEqual(render_csv(p,c,p['paper_url']),current)
            if slug in self.old_sources and slug not in RELEASE['patches']:
                self.assertEqual(current,self.old['assets/evidence/'+slug+'.csv'])
        guide=load_guide();resolve_guide(guide)
        for row in guide['studies']:
            c=json.loads((ROOT/row['source_json']).read_text(encoding='utf-8'))
            self.assertEqual(fingerprint(scientific_content(c)),row['source_fingerprint'])
            c['evidence_scope']['does_not_establish'][0]='An altered boundary.'
            self.assertNotEqual(fingerprint(scientific_content(c)),row['source_fingerprint'])

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
