"""Additive discovery contracts, independent frozen science and negative fixtures.

These are engineering transcription checks, not evidence of external indexing,
retrieval ranking, claim support in a generated answer or academic citation gain.
"""
import copy
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

from build_publications import validate_deep_v2_content, write_public_html_if_changed
from evidence_discovery import without_evidence_ui
from evidence_reuse import render_csv
from paper_discovery import (KEYS, scientific_content, render_html, render_markdown,
                             search_text, validate_layer)
from research_guides import fingerprint, load as load_guide, resolve as resolve_guide
from sync_common import ROOT
from validate_site import (ValidationError, paper_json_ld_object,
                           validate_v2_rendered_page)
from site_common import load_site_config

BASELINE = 'f215c9cb2414fbe1e02b1d16f53c0afd4a578a4f'
# Reviewed routing proposal, fixed independently of current/mutated source inputs.
LAYER_SHA256 = '317b30da3945d32f10ded5b3a0f2b25d42e390dac881f42825e6fdf78669465d'
PENDING = {'10.71321/fy14v342', '10.1007/s11426-026-3629-x'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


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
        cls.items = json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
        cls.sources = {p['slug']: json.loads((ROOT/'data/deep_geo'/(p['slug']+'.json')).read_text(encoding='utf-8'))
                       for p in cls.items if p['paper_geo_status']=='v2'}
        cls.ai = cls.sources['aihflevel']

    def test_exact_reviewed_scope_and_layer(self):
        self.assertEqual(len(self.sources), 26)
        layers = {slug: c['discovery_layer'] for slug,c in self.sources.items()}
        self.assertEqual(digest(layers), LAYER_SHA256, 'Reviewed routing interpretation changed')
        for c in self.sources.values():
            validate_deep_v2_content(c)
        controlled = json.loads((ROOT/'data/deep_geo_papers.json').read_text(encoding='utf-8'))['papers']
        self.assertEqual(len(controlled), 28)
        self.assertEqual({p['doi'] for p in self.items if p['paper_geo_status']=='pending'}, PENDING)

    def test_every_original_scientific_field_stays_frozen(self):
        for slug,c in self.sources.items():
            old = json.loads(self.old['data/deep_geo/'+slug+'.json'])
            # Independent projection, not the implementation's own hash function.
            self.assertEqual({k:v for k,v in c.items() if k!='discovery_layer'}, old, slug)
            self.assertEqual(scientific_content(c), old)
            altered = copy.deepcopy(c)
            altered['key_findings'][0]['claim'] += ' Human treatment benefit is proven.'
            self.assertNotEqual(digest(scientific_content(altered)), digest(old))
            altered = copy.deepcopy(c)
            altered['evidence_scope']['does_not_establish'][0] = 'No limitation.'
            self.assertNotEqual(digest(scientific_content(altered)), digest(old))
            altered['invented_scientific_fact'] = 'Unknown fields must not be silently stripped.'
            self.assertIn('invented_scientific_fact', scientific_content(altered))

    def test_original_html_markdown_and_jsonld_exactly_preserved(self):
        for slug,c in self.sources.items():
            page = (ROOT/'papers'/(slug+'.html')).read_text(encoding='utf-8')
            old = self.old['papers/'+slug+'.html']
            block = render_html(c)
            self.assertEqual(page.count(block), 1)
            self.assertEqual(page.replace(block,'',1), old)
            self.assertEqual(paper_json_ld_object(page,slug), paper_json_ld_object(old,slug))
            self.assertEqual(without_evidence_ui(page), without_evidence_ui(old))
            md = (ROOT/'papers'/(slug+'.md')).read_text(encoding='utf-8')
            md_block = '\n'.join(render_markdown(c))+'\n'
            self.assertEqual(md.count(md_block), 1)
            self.assertEqual(md.replace(md_block,'',1), self.old['papers/'+slug+'.md'])

    def test_protected_inventory_identity_exports_dates_and_pending(self):
        for path,text in self.old.items():
            protected = (path.startswith(('citations/','assets/evidence/'))
                         or path in {'sitemap.xml','publications.json'}
                         or path.startswith('data/') and not path.startswith('data/deep_geo/'))
            if protected:
                self.assertEqual((ROOT/path).read_text(encoding='utf-8'),text,path)
        for p in self.items:
            if p['paper_geo_status']!='v2':
                for suffix in ['html','md']:
                    path='papers/'+p['slug']+'.'+suffix
                    self.assertEqual((ROOT/path).read_text(encoding='utf-8'),self.old[path],path)
                self.assertNotIn(p['slug'],self.sources)
                if p.get('doi') in PENDING:
                    self.assertFalse((ROOT/'data/deep_geo'/(p['slug']+'.json')).exists())

    def test_machine_parity_and_unchanged_question_routes(self):
        index=json.loads((ROOT/'paper_index.json').read_text(encoding='utf-8'))
        before=json.loads(self.old['paper_index.json'])
        for old,row in zip(before['papers'],index['papers']):
            self.assertEqual({k:v for k,v in row.items() if k!='discovery_layer'},old)
            slug=row['paper_url'].rsplit('/',1)[-1].removesuffix('.html')
            self.assertEqual(row.get('discovery_layer'),self.sources.get(slug,{}).get('discovery_layer'))
        before=json.loads(self.old['research/questions.json'])['questions']
        current=json.loads((ROOT/'research/questions.json').read_text(encoding='utf-8'))['questions']
        self.assertEqual(len(before),len(current))
        for a,b in zip(before,current):
            self.assertEqual({k:v for k,v in b.items() if k not in {'field_entry','review_topics','discovery_url'}},a)
            layer=self.sources[b['id']]['discovery_layer']
            self.assertEqual(b['field_entry'],layer['field_entry'])
            self.assertEqual(b['review_topics'],layer['review_topics'])
            self.assertEqual(b['discovery_url'],b['paper_url']+'#paper-discovery')
        page=(ROOT/'research/questions.html').read_text(encoding='utf-8')
        self.assertEqual(without_evidence_ui(page),without_evidence_ui(self.old['research/questions.html']))

    def test_search_preserves_every_old_record_and_adds_only_visible_context(self):
        before=json.loads(self.old['assets/evidence-search.json'])['documents']
        now=json.loads((ROOT/'assets/evidence-search.json').read_text(encoding='utf-8'))['documents']
        self.assertEqual(now[:len(before)],before)
        self.assertEqual(len(now),len(before)+26)
        self.assertEqual(len({d['id'] for d in now}),len(now))
        by_doi={c['doi']:c for c in self.sources.values()}
        for d in now[len(before):]:
            c=by_doi[d['doi']]
            self.assertEqual(d['category'],'Research & review context')
            self.assertEqual(d['text'],search_text(c['discovery_layer']))
            self.assertTrue(d['url'].endswith('#paper-discovery'))
            self.assertFalse(d['limitation'])  # Mixed context is explicitly qualified, not an affirmative finding.
        self.assertFalse(any(d['doi'] in PENDING for d in now[len(before):]))

    def test_optional_backward_compatibility_and_schema_negatives(self):
        original=json.loads(self.old['data/deep_geo/aihflevel.json'])
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
            if p['slug'] in self.sources:
                c=self.sources[p['slug']]
                expected=self.old['assets/evidence/'+p['slug']+'.csv']
                self.assertEqual(render_csv(p,c,p['paper_url']),expected)
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
