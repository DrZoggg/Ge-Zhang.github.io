"""Owner-authorized CR/CTM upgrade: identities, original order and sourced exports."""
import json
from pathlib import Path
import re
import subprocess
import unittest

from sync_common import ROOT
from build_publications import validate_deep_v2_content
from v2_coverage import check_qa_refs

BASE = '39400ec15ba1ea4b069107145e1e04e441e4b8b1'
TARGETS = ('10.1097/re9.0000000000000037', '10.1002/ctm2.70900')
SLUGS = ('doi-10-1097-re9-0000000000000037', 'doi-10-1002-ctm2-70900')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def old(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def ordered_originals(current, baseline):
    original = {p['doi'] for p in baseline}
    return [p for p in current if p['doi'] in original] == baseline


class CRCTMReleaseTests(unittest.TestCase):
    def test_selected_prefix_and_independent_membership_preserve_originals(self):
        for name in ('featured_papers', 'deep_geo_papers'):
            path = 'data/' + name + '.json'
            before = json.loads(old(path))['papers']
            now = json.loads(read(path))['papers']
            self.assertTrue(ordered_originals(now, before), name)
            dois = [p['doi'] for p in now]
            self.assertEqual(len(dois), len(set(dois)), name)
            self.assertTrue(set(TARGETS) <= set(dois))
            if name == 'featured_papers':
                self.assertEqual(now[:12], before[:12])
                self.assertEqual(dois[12:14], list(TARGETS))
                self.assertTrue(all(p['summary'].strip() for p in now[12:14]))
        self.assertIn('const firstCount = 14;', read('assets/biocommand.js'))

    def test_complete_sources_keep_evidence_references_and_static_context(self):
        for doi, slug in zip(TARGETS, SLUGS):
            with self.subTest(doi=doi):
                source = json.loads(read('data/deep_geo/' + slug + '.json'))
                self.assertEqual(source['doi'], doi)
                self.assertEqual(source['version'], 2)
                validate_deep_v2_content(source, slug)
                self.assertEqual(check_qa_refs(source), [])
                page, md = read('papers/' + slug + '.html'), read('papers/' + slug + '.md')
                self.assertIn('data-v2-section="key-findings"', page)
                self.assertIn('id="cite-this-paper"', page)
                self.assertNotIn('id="limited-evidence"', page)
                for finding in source['key_findings']:
                    self.assertTrue(finding['source_locator'].strip())
                    self.assertIn(finding['source_locator'], md)
                self.assertTrue((ROOT / ('assets/evidence/' + slug + '.csv')).is_file())

    def test_original_science_identity_and_existing_question_routes_are_preserved(self):
        self.assertEqual(json.loads(read('data/publications_master.json')),
                         json.loads(old('data/publications_master.json')))
        before = json.loads(old('data/question_index.json'))['papers']
        now = json.loads(read('data/question_index.json'))['papers']
        self.assertEqual({doi: now[doi] for doi in before}, before)
        self.assertTrue(set(TARGETS) <= set(now))
        before_content = subprocess.check_output(
            ['git', 'ls-tree', '-r', '--name-only', BASE, '--', 'data/deep_geo'],
            cwd=ROOT, text=True).splitlines()
        for path in before_content:
            self.assertEqual(json.loads(read(path)), json.loads(old(path)), path)
        for slug in SLUGS:
            for ext in ('bib', 'ris', 'csl.json'):
                path = 'citations/' + slug + '.' + ext
                current = (ROOT / path).read_bytes()
                prior = subprocess.run(['git', 'show', BASE + ':' + path], cwd=ROOT,
                                       capture_output=True)
                if prior.returncode == 0:
                    self.assertEqual(current.replace(b'\r\n', b'\n'),
                                     prior.stdout.replace(b'\r\n', b'\n'), path)
                else:
                    # The deployment already generated some recent exports at
                    # build time; a missing tracked artifact is not a new identity.
                    self.assertIn(TARGETS[SLUGS.index(slug)].encode(), current)

    def test_all_selected_cards_remove_only_standalone_type_labels(self):
        home = read('index.html')
        selected = home.split('<!-- FEATURED_PAPERS_START -->', 1)[1].split('<!-- FEATURED_PAPERS_END -->', 1)[0]
        self.assertNotIn('paper-kind', selected)
        self.assertNotRegex(selected, r'>\s*(?:Article|Letter|Review|Correspondence)\s*</span>')
        for slug in SLUGS:
            self.assertIn('papers/' + slug + '.html', selected)


if __name__ == '__main__':
    unittest.main()
