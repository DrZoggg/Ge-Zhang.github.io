"""Frozen contract and source mapping regressions, not new scientific verification."""
import copy
import json
import unittest
import research_guides as g


class GuideTests(unittest.TestCase):
    def setUp(self): self.data = g.load()

    def rejected(self, edit):
        changed = copy.deepcopy(self.data); edit(changed)
        with self.assertRaises(ValueError): g.resolve(changed)

    def test_current_source_mapping_and_rendering(self):
        sources = g.resolve(self.data)
        page, md = g.render(self.data, sources)
        g.validate_page(page)
        for row in self.data['studies']:
            s = sources[row['id']]
            for ref in row['evidence_refs']:
                self.assertIn(s['url'] + '#' + ref.lower(), page)
                self.assertIn(s['findings'][ref]['source_locator'], md)
            for key, _ in g.FIELDS:
                if key in row: self.assertIn(row[key], md)
        self.assertEqual(g.render(self.data, sources), (page, md))

    def test_nonexistent_doi(self):
        self.rejected(lambda d: d['studies'][0].update(source_doi='10.9999/missing'))

    def test_nonexistent_kf(self):
        self.rejected(lambda d: d['studies'][0]['evidence_refs'].append('KF999'))

    def test_source_drift(self):
        self.rejected(lambda d: d['studies'][0].update(source_fingerprint='0'*64))

    def test_transcriptomic_not_plasma_replication(self):
        self.rejected(lambda d: d['studies'][0].update(boundary='Independent plasma-proteomic replication.'))

    def test_mirna_discovery_count_qualification(self):
        self.rejected(lambda d: d['studies'][1].update(boundary='miR-185-5p is not in the external panel.'))

    def test_circrna_platform_qualification(self):
        self.rejected(lambda d: d['studies'][2].update(boundary='No prospective diagnostic utility is established.'))

    def test_circrna_nine_ten_qualification(self):
        self.rejected(lambda d: d['studies'][2].update(follow_up='External qRT-PCR in 6 DCM patients and 4 controls.'))

    def test_no_synthetic_total_or_joint_model(self):
        for text in ['A combined clinical model is established.', 'The cross-study total is 137 participants.']:
            with self.subTest(text=text):
                self.rejected(lambda d: d['sections'][1].update(text=text))

    def test_guide_not_publication(self):
        master = json.loads((g.ROOT/'data/publications_master.json').read_text(encoding='utf-8'))
        master.append({'slug':g.SLUG,'title':self.data['title']})
        with self.assertRaisesRegex(ValueError, 'master'): g.resolve(self.data, master=master)

    def test_no_source_doi_impersonation(self):
        page, _ = g.render(self.data, g.resolve(self.data))
        with self.assertRaises(ValueError):
            g.validate_page(page.replace('</head>', '<meta name="citation_doi" content="10.1111/jcmm.17789"></head>'))
        with self.assertRaises(ValueError):
            g.validate_page(page.replace('rel="canonical" href="'+g.URL, 'rel="canonical" href="https://doi.org/10.1111/jcmm.17789'))
        self.rejected(lambda d: d.update(doi='10.1111/jcmm.17789'))


if __name__ == '__main__': unittest.main()
