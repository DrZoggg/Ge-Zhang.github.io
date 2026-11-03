#!/usr/bin/env python3
"""Offline synthetic checks for the optional pinned K-Dense JATS adaptation.

Usage: python verify_reference_sidecar.py /path/to/jats_to_text.py
Only synthetic structural XML is sent to the existing helper's stdin. No HTTP,
licensed article text, fixture files, installation or third-party packages.
"""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import unittest

HELPER = None

def article(body, refs="", front_extra="", article_type="review"):
    return ('<article xmlns:xlink="http://www.w3.org/1999/xlink" article-type="'+article_type+'">'
        '<front><article-meta><title-group><article-title>Synthetic source</article-title></title-group>'
        '<article-id pub-id-type="doi">10.1234/source</article-id></article-meta>'+front_extra+'</front>'
        '<body>'+body+'</body><back><ref-list>'+refs+'</ref-list></back></article>')

def ref(n, rid=None, doi=None, encoding="pub-id"):
    rid = rid or 'ref'+str(n)
    doi = doi or '10.1234/study'+str(n)
    identity = ('<pub-id pub-id-type="doi">'+doi+'</pub-id>' if encoding=='pub-id' else
        '<ext-link ext-link-type="doi" xlink:href="'+doi+'"/>')
    return ('<ref id="'+rid+'"><label>'+str(n)+'.</label><mixed-citation publication-type="journal">'
        '<article-title>Synthetic cited work '+str(n)+'</article-title>'+identity+'</mixed-citation></ref>')

def xref(rid, label):
    return '<xref ref-type="bibr" rid="'+rid+'">'+str(label)+'</xref>'

def run(xml, *args):
    return subprocess.run([sys.executable,'-X','utf8','-B',str(HELPER),'-',*args],input=xml,
        capture_output=True,text=True,encoding='utf-8',timeout=15)

def output(xml,*args):
    p=run(xml,*args)
    if p.returncode:
        raise AssertionError((p.returncode,p.stderr))
    return json.loads(p.stdout)

class ReferenceChecks(unittest.TestCase):
    def test_default_has_no_optional_fields(self):
        d=output(article('<sec id="s"><title>Discussion</title><p>Unchanged scientific text.</p></sec>'))
        self.assertEqual(set(d),{'full_text_available','metadata','section_count','word_count','sections'})
        self.assertEqual(d['sections'][0]['text'],'Discussion Unchanged scientific text.')

    def test_mixed_body_source_order_and_no_duplication(self):
        d=output(article('<p>Lead scientific paragraph.</p><sec id="s"><title>Methods</title>'
            '<p>Retained scientific paragraph.</p></sec><p>Tail scientific paragraph.</p>'))
        self.assertEqual([s['text'] for s in d['sections']],['Lead scientific paragraph.',
            'Methods Retained scientific paragraph.','Tail scientific paragraph.'])

    def test_plain_body_fallback(self):
        d=output(article('<p>One paragraph.</p><p>Another paragraph.</p>'))
        self.assertEqual(d['section_count'],1)
        self.assertEqual(d['sections'][0]['text'],'One paragraph. Another paragraph.')

    def test_existing_fields_and_distinct_identity(self):
        d=output(article('<sec id="s"><title>Discussion</title><p>Claim '+xref('a',1)+'.</p></sec>',
            ref(1,'a')), '--include-cited-references')
        c=d['citation_contexts'][0]
        self.assertTrue({'section_id','section_title','paragraph_index','text','reference_ids',
            'references','unresolved_reference_ids','attribution'}<=set(c))
        self.assertEqual((c['section_id'],c['paragraph_index'],c['reference_ids']),('s',1,['a']))
        self.assertEqual(d['metadata']['doi'],'10.1234/source')
        self.assertEqual(c['source_article']['identifiers']['doi'],'10.1234/source')
        self.assertEqual(c['references'][0]['identifiers']['doi'],'10.1234/study1')
        self.assertEqual(c['draft_use_status'],'not_observed_by_parser')
        self.assertIn('co-cited group',c['attribution'])
        self.assertTrue(c['paragraph_locator'].endswith('/p[1]'))

    def range_doc(self, separator='–', labels=(5,6,7,8), left=5, right=8):
        names={5:'start-z',6:'middle-a',7:'middle-q',8:'end-b'}
        refs=''.join(ref(n,names[n]) for n in labels)
        body='<sec id="s"><title>Introduction</title><p>Prior work <sup>'+xref(names[left],left)+separator+xref(names[right],right)+'</sup>.</p></sec>'
        return article(body,refs)

    def test_numeric_range_uses_explicit_labels_not_id_order(self):
        c=output(self.range_doc(),'--include-cited-references')['citation_contexts'][0]
        self.assertEqual(c['reference_ids'],['start-z','middle-a','middle-q','end-b'])
        self.assertEqual(c['range_expansions'][0]['method'],'explicit_numeric_label_range')

    def test_comma_is_not_range(self):
        c=output(self.range_doc(','),'--include-cited-references')['citation_contexts'][0]
        self.assertEqual(c['reference_ids'],['start-z','end-b'])
        self.assertEqual(c['range_expansions'],[])

    def test_incomplete_range_is_not_guessed(self):
        d=output(self.range_doc(labels=(5,7,8)),'--include-cited-references');c=d['citation_contexts'][0]
        self.assertEqual(c['reference_ids'],['start-z','end-b'])
        self.assertEqual(c['range_expansions'][0]['status'],'unresolved')
        self.assertEqual(next(r for r in d['bibliography_references'] if r['reference_id']=='middle-q')['context_status'],
            'not_linked_with_unresolved_ranges')

    def test_duplicate_label_range_is_not_guessed(self):
        xml=self.range_doc().replace('</ref-list>',ref(6,'duplicate-label')+'</ref-list>')
        c=output(xml,'--include-cited-references')['citation_contexts'][0]
        self.assertEqual(c['reference_ids'],['start-z','end-b'])
        self.assertEqual(c['range_expansions'][0]['status'],'unresolved')

    def test_reversed_range_is_not_guessed(self):
        c=output(self.range_doc(left=8,right=5),'--include-cited-references')['citation_contexts'][0]
        self.assertEqual(c['reference_ids'],['end-b','start-z'])
        self.assertEqual(c['range_expansions'][0]['status'],'unresolved')

    def test_nested_body_bibliography_and_doi_ext_link(self):
        xml=article('<p>Editorial context '+xref('r18',18)+'.</p><sec id="refs"><sec><ref-list>'+
            ref(18,'r18',encoding='ext-link')+'</ref-list></sec></sec>',article_type='editorial')
        d=output(xml,'--include-cited-references');c=d['citation_contexts'][0]
        self.assertEqual(c['source_article']['publication_type'],'editorial')
        self.assertEqual(c['reference_ids'],['r18'])
        self.assertEqual(c['references'][0]['identifiers']['doi'],'10.1234/study18')
        self.assertIn('/body[1]/sec[1]/sec[1]/ref-list[1]/ref[1]',c['references'][0]['reference_locator'])

    def test_resolver_ext_link_and_matching_pub_id(self):
        r=ref(1,'a').replace('</mixed-citation>',
            '<ext-link ext-link-type="doi" xlink:href="https://doi.org/10.1234/STUDY1"/></mixed-citation>')
        d=output(article('<p>Claim '+xref('a',1)+'.</p>',r),'--include-cited-references')
        self.assertEqual(d['citation_contexts'][0]['references'][0]['identifiers']['doi'],'10.1234/study1')

    def test_no_title_or_google_scholar_doi_inference(self):
        r=('<ref id="a"><label>1.</label><mixed-citation><article-title>Not an identifier 10.1234/title</article-title>'
            '<ext-link ext-link-type="google-scholar" xlink:href="https://scholar.google.com/?doi=10.1234/guess"/>'
            '<ext-link ext-link-type="doi" xlink:href="https://example.org/10.1234/wronghost"/>'
            '</mixed-citation></ref>')
        d=output(article('<p>Claim '+xref('a',1)+'.</p>',r),'--include-cited-references')
        self.assertEqual(d['citation_contexts'][0]['references'][0]['identifiers'],{})

    def test_explicit_doi_spelling_preserved(self):
        r=ref(1,'a','10.1234/UPPER')
        d=output(article('<p>Claim '+xref('a',1)+'.</p>',r),'--include-cited-references')
        self.assertEqual(d['citation_contexts'][0]['references'][0]['identifiers']['doi'],'10.1234/UPPER')

    def test_malformed_resolver_port_stays_unknown(self):
        r=ref(1,'a','https://doi.org:bad/10.1234/no',encoding='ext-link')
        d=output(article('<p>Claim '+xref('a',1)+'.</p>',r),'--include-cited-references')
        self.assertEqual(d['citation_contexts'][0]['references'][0]['identifiers'],{})
        self.assertTrue(d['citation_contexts'][0]['references'][0]['identifier_issues'])

    def test_optional_fields_are_additive_to_same_body(self):
        xml=article('<sec id="s"><title>Discussion</title><p>Claim '+xref('a',1)+'.</p></sec>',ref(1,'a'))
        before=output(xml);after=output(xml,'--include-cited-references')
        self.assertEqual(set(after)-set(before),{'citation_contexts','bibliography_references'})
        self.assertTrue(all(after[k]==v for k,v in before.items()))

    def test_conflicting_identifiers_fail_closed(self):
        r=ref(1,'a').replace('</mixed-citation>',
            '<ext-link ext-link-type="doi" xlink:href="10.1234/conflict"/></mixed-citation>')
        p=run(article('<p>Claim '+xref('a',1)+'.</p>',r),'--include-cited-references')
        self.assertNotEqual(p.returncode,0);self.assertIn('conflicting doi',p.stderr)

    def test_duplicate_reference_ids_fail_closed(self):
        p=run(article('<p>Claim '+xref('a',1)+'.</p>',ref(1,'a')+ref(2,'a')),'--include-cited-references')
        self.assertNotEqual(p.returncode,0);self.assertIn('duplicate bibliography ref id',p.stderr)

    def test_subarticle_text_metadata_and_refs_do_not_leak(self):
        foreign=('<sub-article><front><article-meta><article-id pub-id-type="doi">10.1234/foreign</article-id>'
            '</article-meta></front><body><sec><p>FOREIGN TEXT '+xref('a',1)+'</p></sec></body>'
            '<back><ref-list>'+ref(1,'a','10.1234/foreignref')+'</ref-list></back></sub-article>')
        xml=article('<p>Own '+xref('a',1)+'.</p><sec><p>Own section.</p>'+foreign+'</sec>',
            ref(1,'a'),front_extra=foreign)
        d=output(xml,'--include-cited-references')
        self.assertEqual(d['metadata']['doi'],'10.1234/source')
        self.assertNotIn('FOREIGN TEXT',json.dumps(d))
        self.assertEqual(len(d['bibliography_references']),1)
        self.assertEqual(d['bibliography_references'][0]['identifiers']['doi'],'10.1234/study1')
        missing=xml.replace('<article-id pub-id-type="doi">10.1234/source</article-id>','')
        self.assertIsNone(output(missing,'--include-cited-references')['metadata']['doi'])

    def test_missing_reference_remains_explicit(self):
        d=output(article('<p>Unknown '+xref('missing',1)+'.</p>'),'--include-cited-references')
        self.assertEqual(d['citation_contexts'][0]['unresolved_reference_ids'],['missing'])
        self.assertEqual(d['citation_contexts'][0]['references'],[])

    def test_uncited_bibliography_is_not_a_claim_or_read(self):
        d=output(article('<p>No citation here.</p>',ref(7,'unlinked')),'--include-cited-references')
        self.assertEqual(d['citation_contexts'],[])
        r=d['bibliography_references'][0]
        self.assertEqual(r['context_status'],'uncited_in_scanned_body_paragraphs')
        self.assertEqual(r['original_reading_status'],'not_observed_by_parser')

    def test_section_filter_preserves_top_level_semantics(self):
        body='<sec id="m"><title>Methods</title><sec id="nested"><title>Nested</title><p>Method '+xref('a',1)+'.</p></sec></sec>'
        body+='<sec id="d"><title>Discussion</title><p>Other '+xref('b',2)+'.</p></sec>'
        d=output(article(body,ref(1,'a')+ref(2,'b')),'--include-cited-references','--sections','Methods')
        self.assertEqual(d['citation_contexts'][0]['section_id'],'nested')
        self.assertEqual(d['citation_contexts'][0]['reference_ids'],['a'])
        self.assertEqual(next(r for r in d['bibliography_references'] if r['reference_id']=='b')['context_status'],
            'cited_outside_selected_contexts')

    def test_metadata_only_refusal_and_text_only_contract(self):
        xml='<article><front><article-meta/></front></article>'
        p=run(xml,'--include-cited-references')
        self.assertEqual(p.returncode,2);self.assertFalse(json.loads(p.stdout)['full_text_available'])
        p=run(xml,'--allow-metadata-only','--include-cited-references');self.assertEqual(p.returncode,0)
        self.assertNotIn('citation_contexts',json.loads(p.stdout))
        p=run(article('<p>Readable synthetic text.</p>'),'--text-only','--include-cited-references')
        self.assertEqual(p.returncode,0);self.assertIn('Readable synthetic text.',p.stdout)
        self.assertNotIn('citation_contexts',p.stdout)

def main():
    global HELPER
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('helper',type=Path);args=p.parse_args()
    HELPER=args.helper.resolve()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReferenceChecks))
    print(json.dumps({'status':'PASS' if result.wasSuccessful() else 'FAIL','synthetic_cases':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'new_HTTP_requests':0}))
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
