"""Pilot-only layout and exact content contracts; no extractor dependencies."""
import collections
import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from evidence_presentation import PILOT_DOIS, STYLESHEET, enabled, guide_navigation
from sync_common import ROOT, load_master

BASE = '72075bc52098e0fab8a22bd33828e15601fe6c6a'
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
# Independently reviewed R2 fixtures; not a production PMCID data source.
PMC_LINKS = {
    '10.1038/s41467-024-50415-9': 'PMC11310499',
    '10.1021/acs.jproteome.4c00522': 'PMC11385702',
    '10.1186/s12967-022-03795-9': 'PMC9724432',
    '10.1016/j.isci.2023.107587': 'PMC10470306',
    '10.1172/jci194175': 'PMC12987658',
}


def without_approved_pmc_link(before, after, doi):
    pmcid = PMC_LINKS.get(doi)
    if not pmcid:
        return after
    url = f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/'
    plain = f'<dt>PMCID</dt><dd>{pmcid}</dd>'
    linked = f'<dt>PMCID</dt><dd><a href="{url}">{pmcid}</a></dd>'
    pattern = r'(<section[^>]* data-v2-section="provenance">)(.*?)(</section>)'
    old = list(re.finditer(pattern, before, re.S))
    new = list(re.finditer(pattern, after, re.S))
    if len(old) != 1 or len(new) != 1 or old[0][2].count(plain) != 1:
        raise ValueError('Missing original PMCID provenance fixture')
    if new[0][2] != old[0][2].replace(plain, linked, 1):
        raise ValueError('Missing/changed/moved/duplicated PMC provenance link')
    # Remove only this independently checked wrapper, in this exact section.
    return after[:new[0].start(2)] + new[0][2].replace(linked, plain, 1) + after[new[0].end(2):]


class Contract(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source=source; self.stack=[]; self.text=[]; self.nodes=[]; self.ids=[]; self.fields=collections.defaultdict(list)
        self.offsets=[0]
        for line in source.splitlines(keepends=True):self.offsets.append(self.offsets[-1]+len(line))
        self.ranges={}; self.feed(source)
        if self.stack:raise ValueError('Unclosed HTML tags')
    def pos(self):
        line,col=self.getpos();return self.offsets[line-1]+col
    def handle_starttag(self, tag, attrs):
        a=dict(attrs); token=tag
        if a.get('id'):self.ids.append(a['id'])
        if tag=='section' and a.get('class')=='paper-geo-v2__finding':token='article'
        if not (tag=='article' and not attrs) and not (tag=='link' and a.get('href')=='../assets/evidence-presentation.css'):
            self.nodes.append((token,tuple(attrs)))
        keys=[]
        if a.get('data-v2-section'):keys.append('section:'+a['data-v2-section'])
        if a.get('class')=='paper-geo-v2__finding':keys.append('finding:'+a['data-key-finding-id'])
        if a.get('class')=='paper-geo-v2__author':keys.append('authors')
        if tag=='script':keys.append('scripts')
        if tag not in VOID:self.stack.append((tag,keys,a.get('id'),self.pos()))
    def handle_endtag(self, tag):
        if tag in VOID:return
        if not self.stack or self.stack[-1][0]!=tag:raise ValueError('Unbalanced HTML: '+tag)
        _,_,identifier,start=self.stack.pop()
        if identifier:self.ranges[identifier]=(start,self.pos()+len('</'+tag+'>'))
    def handle_data(self, data):
        if data.strip():self.text.append(data)
        for _,keys,_,_ in self.stack:
            for key in keys:self.fields[key].append(data)
    def handle_entityref(self,name):self.handle_data('&'+name+';')
    def handle_charref(self,name):self.handle_data('&#'+name+';')


def validate_pair(before, after, doi):
    after = without_approved_pmc_link(before, after, doi)
    navigation = guide_navigation(doi)
    if navigation:
        if after.count(navigation) != 1:raise ValueError('Missing/changed/duplicated guide navigation')
        after = after.replace(navigation, '', 1)
    if 'id="related-evidence-guide"' in after:raise ValueError('Unfounded guide navigation')
    if not enabled(doi):
        if before!=after:raise ValueError('Non-allowlist page changed')
        return
    old,new=Contract(before),Contract(after)
    if collections.Counter(old.text)!=collections.Counter(new.text):raise ValueError('Original text/payload changed')
    if collections.Counter(old.nodes)!=collections.Counter(new.nodes):raise ValueError('Original metadata/attributes changed')
    if old.fields!=new.fields:raise ValueError('Scientific context, authors, citation or copy payload changed')
    if len(new.ids)!=len(set(new.ids)) or collections.Counter(old.ids)!=collections.Counter(new.ids):raise ValueError('Duplicate/lost anchor')
    if after.count(STYLESHEET)!=1:raise ValueError('Missing unique pilot stylesheet')
    positions=[after.index(s) for s in ['class="paper-geo-v2__authors"','id="official-abstract"','data-v2-section="research-question"','id="ev-summary"','id="cite-this-paper"','data-v2-section="evidence-snapshot"']]
    if positions!=sorted(positions):raise ValueError('Official Abstract/summary reading order changed')
    if after.count('<main class="wrap"><article>')!=1:raise ValueError('Missing main article')


def baseline(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode('utf-8')


def validate_css(css):
    for selector, declarations in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        if re.search(r'\b(?:html|body)\b', selector) and re.search(r'overflow(?:-x)?\s*:\s*(?:hidden|clip)', declarations):
            raise ValueError('Whole-page overflow masking is not a repair')


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doi='10.1021/acs.jproteome.4c00522';cls.before=baseline('papers/olink-dcm.html')
        cls.after=(ROOT/'papers/olink-dcm.html').read_text(encoding='utf-8')
    def reject(self, value):
        with self.assertRaises(ValueError):validate_pair(self.before,value,self.doi)
    def test_all_current_pages(self):
        count=0
        for p in load_master():
            if not p.get('slug'):continue
            file=ROOT/'papers'/(p['slug']+'.html')
            if not file.exists():continue
            validate_pair(baseline(file.relative_to(ROOT).as_posix()),file.read_text(encoding='utf-8'),p.get('doi',''))
            count+=1
        self.assertEqual(count,74)
    def test_hidden_abstract(self):self.reject(self.after.replace('id="official-abstract"','id="official-abstract" hidden',1))
    def test_abstract_at_end(self):
        a,b=Contract(self.after).ranges['official-abstract'];section=self.after[a:b]
        self.reject((self.after[:a]+self.after[b:]).replace('</main>',section+'</main>',1))
    def test_author_missing_or_reordered(self):
        self.reject(self.after.replace('<li class="paper-geo-v2__author">Shuai Xu</li>','',1))
        self.reject(self.after.replace('>Shuai Xu</li><li class="paper-geo-v2__author">Ge Zhang</li>','>Ge Zhang</li><li class="paper-geo-v2__author">Shuai Xu</li>',1))
    def test_number_retained_unit_or_qualification_lost(self):
        self.reject(self.after.replace('20 DCM-HF and 18 healthy controls','20 and 18',1))
        self.reject(self.after.replace('not prospective incident-DCM prediction','prospective incident-DCM prediction',1))
    def test_duplicate_kf_anchor(self):self.reject(self.after.replace('id="kf2"','id="kf1"',1))
    def test_nonallowlist_change(self):
        before=baseline('papers/apvs.html')
        after=(ROOT/'papers/apvs.html').read_text(encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Non-allowlist'):
            validate_pair(before,after.replace('</main>','<p>Unauthorized change</p></main>',1),'10.1016/j.isci.2023.107587')
    def test_citation_or_copy_payload_change(self):
        self.reject(self.after.replace('Plain citation','Changed citation',1))
        self.reject(self.after.replace('"finding_id": "KF1"','"finding_id": "KF9"',1))
    def test_no_page_overflow_masking(self):
        validate_css((ROOT/'assets/evidence-presentation.css').read_text(encoding='utf-8'))
        for bad in ['html,body{overflow-x:hidden}', 'body {overflow:clip}']:
            with self.assertRaises(ValueError):validate_css(bad)
    def test_guide_navigation_source_mapping(self):
        expected = {'10.1021/acs.jproteome.4c00522','10.1111/jcmm.17789','10.1111/jcmm.70258'}
        self.assertEqual({p['doi'].lower() for p in load_master() if guide_navigation(p.get('doi',''))}, expected)
        self.reject(self.after.replace('related-evidence-guide', 'unexpected-guide', 1))
        self.reject(self.after + guide_navigation(self.doi))
        with self.assertRaises(ValueError):
            validate_pair('original', 'original' + guide_navigation(self.doi), '10.1016/j.isci.2023.107587')


if __name__=='__main__':unittest.main()
