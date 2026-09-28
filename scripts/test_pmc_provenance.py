"""Narrow PMC link authorization, unchanged science, and existing date semantics."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from build_publications import (load_deep_content, verified_pmc_provenance,
                                write_public_html_if_changed, resolve_lastmod)
from citation_common import load_citation_metadata
from sync_common import ROOT, load_master, is_withdrawn, norm_doi
from test_evidence_presentation import PMC_LINKS, baseline, validate_pair


class PMCProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = [p for p in load_master() if not is_withdrawn(p)]
        cls.papers = {norm_doi(p.get('doi')): p for p in cls.public}
        cls.metadata = load_citation_metadata(cls.public)
        cls.paper = cls.papers['10.1038/s41467-024-50415-9']
        cls.content = load_deep_content(cls.paper)
        cls.meta = cls.metadata[cls.paper['doi']]

    def test_reviewed_sources_and_rendered_parity(self):
        for doi, pmcid in PMC_LINKS.items():
            with self.subTest(doi=doi):
                p=self.papers[doi];c=load_deep_content(p);m=self.metadata[doi]
                url=f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/'
                self.assertEqual(c['version'],2)
                self.assertEqual(c['provenance']['pmcid'],pmcid)
                self.assertEqual(m['pmcid'],pmcid)
                self.assertIn(url,m['verified_sources'])
                self.assertEqual(verified_pmc_provenance(p,c,m),url)
                path=f"papers/{p['slug']}.html"
                page=(ROOT/path).read_text(encoding='utf-8')
                validate_pair(baseline(path),page,doi)
                self.assertEqual(page.count(f'<dt>PMCID</dt><dd><a href="{url}">{pmcid}</a></dd>'),1)
                md=(ROOT/'papers'/f"{p['slug']}.md").read_text(encoding='utf-8')
                self.assertEqual(md.count(f'- PMCID: [{pmcid}]({url})'),1)

    def test_missing_conflicting_or_invalid_ids(self):
        for value in ('', 'PMC0', 'PMC0123', 'pmc11310499', 'PMC1" onclick="x', None):
            c=copy.deepcopy(self.content);c['provenance']['pmcid']=value
            self.assertEqual(verified_pmc_provenance(self.paper,c,self.meta),'')
        self.assertEqual(verified_pmc_provenance(self.paper,self.content,dict(self.meta,pmcid='PMC9724432')),'')
        self.assertEqual(verified_pmc_provenance(self.paper,self.content,{}),'')

    def test_only_exact_verified_official_source(self):
        bad=['https://pmc.ncbi.nlm.nih.gov.evil.test/articles/PMC11310499/',
             'https://user@pmc.ncbi.nlm.nih.gov/articles/PMC11310499/',
             'https://pmc.ncbi.nlm.nih.gov:443/articles/PMC11310499/',
             'https://pmc.ncbi.nlm.nih.gov/articles/PMC9724432/',
             'http://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/',
             'https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/?x=1',
             'https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/#fragment',
             'https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/\n']
        for url in bad:
            with self.subTest(url=url):
                self.assertEqual(verified_pmc_provenance(self.paper,self.content,dict(self.meta,verified_sources=[url])),'')
        self.assertEqual(verified_pmc_provenance(self.paper,self.content,dict(self.meta,verified_sources=[])),'')

    def test_existing_link_and_non_v2_noop(self):
        p=self.papers['10.1002/ehf2.14003'];c=load_deep_content(p)
        self.assertEqual(verified_pmc_provenance(p,c,self.metadata[p['doi']]),'')
        self.assertEqual(verified_pmc_provenance(self.paper,dict(self.content,version=1),self.meta),'')
        self.assertEqual(verified_pmc_provenance(self.paper,None,self.meta),'')
        self.assertEqual(verified_pmc_provenance(self.paper,dict(self.content,doi='10.9999/wrong'),self.meta),'')
        p=next(p for p in load_master() if is_withdrawn(p))
        self.assertEqual(verified_pmc_provenance(p,self.content,self.meta),'')

    def test_precise_contract_rejects_link_mutations(self):
        for doi,pmcid in PMC_LINKS.items():
            p=self.papers[doi];path=f"papers/{p['slug']}.html"
            before=baseline(path);after=(ROOT/path).read_text(encoding='utf-8')
            url=f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/'
            anchor=f'<a href="{url}">{pmcid}</a>'
            mutations={
                'missing':after.replace(anchor,pmcid,1),
                'wrong_id':after.replace(anchor,anchor.replace(pmcid,'PMC1'),1),
                'wrong_url':after.replace(anchor,anchor.replace('/articles/','/wrong/'),1),
                'spoofed_host':after.replace(anchor,anchor.replace('gov/','gov.evil.test/'),1),
                'extra_attribute':after.replace(anchor,anchor.replace('<a ','<a target="_blank" ',1),1),
                'duplicate':after.replace(anchor,anchor+anchor,1),
                'extra_anchor':after.replace(anchor,anchor+'<a href="https://example.org/">x</a>',1),
                'moved':after.replace(anchor,pmcid,1).replace('</main>',anchor+'</main>',1),
                'visible_id':after.replace(anchor,f'<a href="{url}">PMC1</a>',1),
                'science_changed':after.replace('</main>','<p>Unsupported scientific claim</p></main>',1),
            }
            for name,changed in mutations.items():
                with self.subTest(doi=doi,mutation=name),self.assertRaises(ValueError):
                    validate_pair(before,changed,doi)

    def test_existing_lastmod_algorithm_and_second_write(self):
        url='https://example.org/papers/test.html';old={url:'2026-01-01'}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.html';path.write_text('<dd>PMC1</dd>',encoding='utf-8')
            changed='<dd><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC1/">PMC1</a></dd>'
            self.assertTrue(write_public_html_if_changed(path,changed))
            self.assertEqual(resolve_lastmod(url,True,old,'2026-01-02'),'2026-01-02')
            self.assertEqual(resolve_lastmod(url,False,old,'2026-01-02'),'2026-01-01')
            first=path.read_bytes();self.assertFalse(write_public_html_if_changed(path,changed))
            self.assertEqual(path.read_bytes(),first)
            self.assertEqual(resolve_lastmod(url,False,{url:'2026-01-02'},'2026-01-03'),'2026-01-02')


if __name__=='__main__':unittest.main()
