"""Homepage contribution labels fail closed and never rewrite bibliographic data."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from homepage_author_roles import load_role_records, render_role_labels
from site_common import load_profile_config
from sync_common import ROOT
from test_visual3 import Document


class HomepageAuthorRolesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'data/homepage_author_roles.json'
        cls.owner = load_profile_config()['orcid']
        cls.data = json.loads(cls.path.read_text(encoding='utf-8'))
        cls.records = load_role_records(cls.path, cls.owner)

    def load_fixture(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'roles.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            return load_role_records(path, self.owner)

    def test_rendered_labels_match_exact_doi_and_review_status(self):
        page = Document((ROOT/'index.html').read_text(encoding='utf-8')).root
        rendered = page.find('div', **{'class': 'author-roles'})
        expected = {doi:r for doi,r in self.records.items() if r['status']=='verified'}
        self.assertEqual({n.attrs['data-author-role-doi'] for n in rendered}, set(expected))
        self.assertEqual(len(rendered), len(expected))
        cards = page.find('article', **{'class': 'card paper'})
        for card in cards:
            doi_links = [n.attrs.get('href','') for n in card.find('a') if n.text()=='DOI']
            labels = card.find('div', **{'class':'author-roles'})
            if not labels:
                continue
            node = labels[0];doi = node.attrs['data-author-role-doi'];record=expected[doi]
            self.assertEqual(doi_links,['https://doi.org/'+doi])
            self.assertEqual([a.text() for a in node.find('a')],record['roles'])
            self.assertTrue(all(a.attrs['href']==record['sources'][0]['url'] for a in node.find('a')))
            self.assertEqual(len(card.find('p')),1,'Role markup must not alter the summary paragraph')

    def test_same_name_and_equal_contribution_boundaries(self):
        self.assertEqual(self.records['10.1002/mdr2.70052']['roles'],['Corresponding author'])
        self.assertIn('author 23',self.records['10.1002/mdr2.70052']['identity_note'])
        self.assertIn(self.owner,self.records['10.1002/mdr2.70052']['identity_note'])
        jco = self.records['10.1200/po.24.00089']
        self.assertEqual(jco['roles'], ['Corresponding author', 'Co-first author'])
        self.assertEqual(jco['verified_on'], '2026-10-26')
        self.assertEqual(jco['sources'][0]['url'], 'https://ascopubs.org/doi/abs/10.1200/PO.24.00089')
        self.assertIn('Corresponding Author', jco['sources'][0]['locator'])
        self.assertIn('Shiqian Zhang, Ge Zhang and Ming Wang', jco['identity_note'])
        self.assertEqual(self.records['10.1172/jci194175']['roles'],['Co-author'])

    def test_unknown_or_pending_doi_has_no_fallback_label(self):
        self.assertEqual(render_role_labels('10.0000/not-reviewed',self.records),'')
        pending={'10.1234/pending':{'status':'pending','roles':['Co-first author']}}
        self.assertEqual(render_role_labels('10.1234/pending',pending),'')

    def test_probe_correspondence_and_idebenone_pending_boundary(self):
        record = self.records['10.1007/s11426-026-3629-x']
        self.assertEqual(record['status'], 'verified')
        self.assertEqual(record['roles'], ['Corresponding author'])
        self.assertEqual(record['verified_on'], '2026-10-26')
        self.assertEqual(record['sources'], [{
            'url': 'https://link.springer.com/article/10.1007/s11426-026-3629-x',
            'locator': 'Author information > Corresponding authors',
        }])
        pending = self.records['10.1016/j.ejphar.2023.175569']
        self.assertEqual(pending['status'], 'pending')
        self.assertEqual(pending['roles'], [])
        self.assertEqual(render_role_labels('10.1016/j.ejphar.2023.175569', self.records), '')

    def test_owner_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            load_role_records(self.path,'0000-0000-0000-0000')

    def test_luad_role_verification_preserves_bibliographic_review(self):
        doi = '10.71321/fy14v342'
        record = self.records[doi]
        self.assertEqual(record['status'], 'verified')
        self.assertEqual(record['roles'], ['Corresponding author'])
        self.assertEqual(record['verified_on'], '2026-10-26')
        self.assertEqual(record['sources'][0]['url'], 'https://www.lifeconflux.com/10.71321/fy14v342/')
        self.assertIn('Corresponding Author', record['sources'][0]['locator'])
        self.assertIn('IDENTITY_REVIEW_REQUIRED', record['identity_note'])
        featured = json.loads((ROOT/'data/featured_papers.json').read_text(encoding='utf-8'))['papers']
        summary = next(p['summary'] for p in featured if p['doi'] == doi)
        gold = json.loads((ROOT/'data/deep_geo/doi-10-71321-fy14v342.json').read_text(encoding='utf-8'))
        self.assertTrue(gold['summary'].startswith(summary + ' '))
        self.assertIn('prospective clinical utility.', summary)
        self.assertNotIn('IDENTITY_REVIEW_REQUIRED', summary)
        self.assertIn('IDENTITY_REVIEW_REQUIRED', gold['evidence_page_notice'])
        self.assertIn('IDENTITY_REVIEW_REQUIRED', (ROOT/'papers/doi-10-71321-fy14v342.html').read_text(encoding='utf-8'))

    def test_verified_without_evidence_rejected(self):
        for field in ('sources','verification_basis','roles'):
            data=copy.deepcopy(self.data);data['papers']['10.1126/science.aek9583'][field]=[]
            with self.subTest(field=field),self.assertRaises(ValueError):self.load_fixture(data)

    def test_unsupported_or_conflicting_roles_rejected(self):
        for roles in (['Lead author'],['First author','Co-first author'],['Co-author','Corresponding author'],['First author','First author']):
            data=copy.deepcopy(self.data);data['papers']['10.1126/science.aek9583']['roles']=roles
            with self.subTest(roles=roles),self.assertRaises(ValueError):self.load_fixture(data)

    def test_two_verified_complementary_roles_are_preserved(self):
        data=copy.deepcopy(self.data);record=data['papers']['10.1126/science.aek9583']
        record['roles']=['First author','Corresponding author']
        records=self.load_fixture(data)
        node=Document(render_role_labels('10.1126/SCIENCE.AEK9583',records)).root
        self.assertEqual([a.text() for a in node.find('a')],record['roles'])

    def test_unsafe_source_and_duplicate_doi_rejected(self):
        data=copy.deepcopy(self.data);data['papers']['10.1126/science.aek9583']['sources'][0]['url']='javascript:alert(1)'
        with self.assertRaises(ValueError):self.load_fixture(data)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'roles.json';path.write_text('{"version":1,"version":2}',encoding='utf-8')
            with self.assertRaises(ValueError):load_role_records(path,self.owner)


if __name__=='__main__':unittest.main()
