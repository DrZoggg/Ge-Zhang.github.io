"""Additive work intake with a strict projection onto the unchanged old corpus."""
import hashlib
import json
import subprocess
import unittest
from xml.etree import ElementTree

from sync_common import ROOT
from limited_evidence import render_html, render_markdown, validate_record
from validate_site import paper_json_ld_object

FIXTURE = ROOT / 'scripts/fixtures/verified_work_intake_20261105.json'

def normalized(path):
    return (ROOT / path).read_bytes().replace(b'\r\n', b'\n')

def canon(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()

class VerifiedWorkIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = json.loads(FIXTURE.read_text(encoding='utf-8'))
        cls.base = cls.f['base_sha']
        cls.public = json.loads(normalized('publications.json'))
        cls.master = json.loads(normalized('data/publications_master.json'))
        cls.notes = json.loads(normalized('data/limited_evidence.json'))['papers']
        cls.ids = set(cls.f['papers'])
        cls.updated_notes = cls.f.get('updated_notes', {})
        cls.bydoi = {p.get('doi'):p for p in cls.public}
        cls.old_public = json.loads(cls.old('publications.json'))

    @classmethod
    def old(cls,path):
        return subprocess.check_output(['git','show',cls.base+':'+path],cwd=ROOT).replace(b'\r\n',b'\n')

    def test_only_source_approved_identities_are_added(self):
        self.assertEqual(len(self.public), len(self.old_public)+len(self.ids))
        self.assertEqual([p for p in self.public if p.get('doi') not in self.ids],self.old_public)
        self.assertEqual([p for p in self.master if p.get('doi') not in self.ids],json.loads(self.old('data/publications_master.json')))
        self.assertEqual(sum(p['paper_geo_status']=='v2' for p in self.public),59)
        for doi,row in self.f['papers'].items():
            p=self.bydoi[doi]
            self.assertEqual({k:p[k] for k in row['identity']},row['identity'])
            self.assertEqual(p['paper_geo_status'],'none')
            self.assertFalse(p['featured']);self.assertFalse(p['deep_geo'])

    def test_old_notes_gold_scientific_pages_citations_and_visuals_are_exact(self):
        old_notes=json.loads(self.old('data/limited_evidence.json'))['papers']
        changed = self.ids | set(self.updated_notes)
        self.assertEqual({d:n for d,n in self.notes.items() if d not in changed},
                         {d:n for d,n in old_notes.items() if d not in changed})
        revised_pages = {f"papers/{row['slug']}.{ext}"
                         for row in self.updated_notes.values() for ext in ('html','md')}
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',self.base,'--',
            'papers','citations','data/deep_geo','assets','data/featured_papers.json',
            'data/deep_geo_papers.json','data/profile_config.json','data/homepage_author_roles.json',
            'data/patent_evidence.json','data/official_abstracts.json','data/scholarly_identifiers.json',
            'data/scientific_discovery_intents.json','robots.txt','CNAME','.github'],cwd=ROOT,text=True).splitlines()
        for p in paths:
            if p != 'assets/evidence-search.json' and p not in revised_pages:
                self.assertEqual(normalized(p),self.old(p),p)
        current=normalized('index.html').decode();before=self.old('index.html').decode()
        for start,end in [('<section class="hero"','</section>'),('<div id="featured-papers"','</section>')]:
            if start in before:
                first=before.index(start);last=before.index(end,first)+len(end)
                self.assertIn(before[first:last],current,start)

    def test_new_notes_preserve_original_explanation_and_citation_routes(self):
        questions=json.loads(normalized('research/questions.json'))
        works={w['doi']:w for w in questions['works'] if w.get('doi')}
        old_questions=json.loads(self.old('research/questions.json'))
        self.assertEqual(questions['all_questions'],old_questions['all_questions'])
        self.assertEqual(len(questions['all_questions']),362)
        changed = self.ids | set(self.updated_notes)
        self.assertEqual([w for w in questions['works'] if w.get('doi') not in changed],
                         [w for w in old_questions['works'] if w.get('doi') not in changed])
        for doi,row in self.updated_notes.items():
            note = self.notes[doi]
            prior = json.loads(self.old('data/limited_evidence.json'))['papers'][doi]
            self.assertEqual(canon(prior),row['previous_note_sha256'])
            self.assertEqual(canon(note),row['note_sha256'])
            validate_record(doi,note,self.bydoi[doi])
            self.assertEqual(works[doi]['author_evidence_note']['sections'],note['sections'])
            for ext, render in [('html',render_html),('md',render_markdown)]:
                self.assertIn(render(note),normalized(f"papers/{row['slug']}.{ext}").decode())
        for doi,row in self.f['papers'].items():
            note=self.notes[doi];slug=row['identity']['slug'];work=works[doi]
            validate_record(doi,note,self.bydoi[doi])
            self.assertEqual(canon(note),row['note_sha256'])
            page=normalized('papers/'+slug+'.html').decode()
            md=normalized('papers/'+slug+'.md').decode()
            self.assertIn(render_html(note),page)
            self.assertIn(render_markdown(note),md)
            if row.get('pmid'):
                self.assertIn('https://pubmed.ncbi.nlm.nih.gov/'+row['pmid']+'/',page)
            self.assertIn('https://doi.org/'+doi,page)
            self.assertEqual(work['question_count'],0)
            self.assertEqual(work['key_findings'],[])
            self.assertEqual(work['evidence_status'],'limited')
            self.assertEqual(work['author_evidence_note']['sections'],note['sections'])
            self.assertNotIn('official-abstract',page)

    def test_first_online_and_assigned_citation_dates_are_distinct(self):
        for doi,row in self.f['papers'].items():
            slug=row['identity']['slug']
            schema=paper_json_ld_object(normalized('papers/'+slug+'.html').decode(),slug)
            self.assertEqual(schema['datePublished'],row['first_online'])
            self.assertEqual(schema['identifier'],{'@type':'PropertyValue','propertyID':'DOI','value':doi})
            csl=json.loads(normalized('citations/'+slug+'.csl.json'))
            self.assertEqual(csl['DOI'],doi)
            self.assertEqual(csl['issued']['date-parts'][0],row['citation_date_parts'])
            self.assertIn('PY  - '+str(row['identity']['year']),normalized('citations/'+slug+'.ris').decode())

    def test_sitemap_is_additive_and_keeps_existing_paper_dates(self):
        def sitemap(raw):
            return {e.find('{*}loc').text:e.find('{*}lastmod').text for e in ElementTree.fromstring(raw)}
        old=sitemap(self.old('sitemap.xml'));now=sitemap(normalized('sitemap.xml'))
        extra={self.bydoi[d]['paper_url'] for d in self.ids}
        self.assertEqual(set(now)-set(old),extra)
        self.assertTrue(set(old)<=set(now))
        for p in self.old_public:
            url = p['paper_url']
            if p.get('doi') in self.updated_notes:
                self.assertGreaterEqual(now[url],old[url])
            else:
                self.assertEqual(now[url],old[url])

if __name__=='__main__':unittest.main()
