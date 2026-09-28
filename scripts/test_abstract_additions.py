"""Reviewed abstract-only migration of historical page protection contracts."""
import hashlib
import html
import json
import re
import unittest

from official_abstracts import PATH, abstract_text
from sync_common import ROOT

FIXTURE = ROOT / 'scripts/fixtures/official_abstract_additions_20260928.json'


def fixtures():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))['papers']


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate article schema key: ' + key)
        value[key] = item
    return value


def reviewed_record(doi):
    expected = fixtures()[doi]
    record = json.loads(PATH.read_text(encoding='utf-8'))['papers'][doi]
    serialized = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    if hashlib.sha256(serialized.encode('utf-8')).hexdigest() != expected['record_sha256']:
        raise ValueError('Reviewed Official Abstract source fixture changed: ' + doi)
    return record


def expected_block(record, doi):
    """Independent exact HTML expectation, not copied from candidate renderer output."""
    abstract = record['abstract']
    if abstract['type'] == 'structured':
        body = ''.join('<h3>' + html.escape(s['label']) + '</h3><p>' + html.escape(s['text']) + '</p>' for s in abstract['sections'])
    else:
        body = '<p>' + html.escape(abstract['text']) + '</p>'
    source = {'version_of_record': 'Version of Record', 'publisher': 'publisher', 'pmc': 'PMC', 'pubmed': 'PubMed indexed abstract'}[record['source_type']]
    return ('<section id="official-abstract" class="paper-geo-v2__section"><h2>Official Abstract</h2>' + body
            + '<p class="paper-geo-v2__source">Text reproduced verbatim from ' + source
            + ' (<a href="' + html.escape(record['source_url'], quote=True) + '">source</a>); '
            + '<a href="https://doi.org/' + doi + '">DOI</a>; '
            + '<a href="' + html.escape(record['license_url'], quote=True) + '">'
            + html.escape(record['license']) + '</a>.</p></section>')


def without_approved_abstract(before, after, doi):
    if doi not in fixtures():
        return after
    record = reviewed_record(doi)
    text = abstract_text(record)
    block = expected_block(record, doi)
    meta = '<meta name="citation_abstract" content="' + html.escape(text, quote=True) + '">\n'
    if 'id="official-abstract"' in before or 'name="citation_abstract"' in before:
        raise ValueError('Unexpected preexisting abstract in addition fixture')
    if after.count(block) != 1 or after.count('id="official-abstract"') != 1:
        raise ValueError('Missing/changed/hidden/duplicated reviewed abstract block')
    if after.count(meta) != 1 or after.count('name="citation_abstract"') != 1:
        raise ValueError('Reviewed abstract metadata changed')
    after = after.replace(meta, '', 1)
    pattern = r'<script type="application/ld\+json">(.*?)</script>'
    old = list(re.finditer(pattern, before, re.S)); new = list(re.finditer(pattern, after, re.S))
    if len(old) != 1 or len(new) != 1:
        raise ValueError('Expected one article schema')
    old_schema = json.loads(old[0][1], object_pairs_hook=unique_object)
    new_schema = json.loads(new[0][1], object_pairs_hook=unique_object)
    if new_schema.pop('abstract', None) != text or new_schema != old_schema:
        raise ValueError('Abstract/schema scientific or identity data changed')
    after = after[:new[0].start(1)] + old[0][1] + after[new[0].end(1):]
    hero_pattern = r'<section class="hero"[^>]*>.*?</section>\n'
    old_hero = list(re.finditer(hero_pattern, before, re.S))
    new_hero = list(re.finditer(hero_pattern, after, re.S))
    if len(old_hero) != 1 or len(new_hero) != 1 or old_hero[0][0] != new_hero[0][0]:
        raise ValueError('Original hero boundary changed')
    insertion = new_hero[0].end()
    if not after.startswith(block + '\n', insertion):
        raise ValueError('Reviewed abstract moved from its original insertion position')
    return after[:insertion] + after[insertion + len(block) + 1:]


class AbstractAdditionTests(unittest.TestCase):
    def test_existing_abstracts_unchanged(self):
        frozen = json.loads(FIXTURE.read_text(encoding='utf-8'))
        records = json.loads(PATH.read_text(encoding='utf-8'))['papers']
        original = {doi: records[doi] for doi in frozen['baseline_dois']}
        serialized = json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        self.assertEqual(hashlib.sha256(serialized.encode('utf-8')).hexdigest(), frozen['baseline_records_sha256'])
        self.assertEqual(set(records), set(frozen['baseline_dois']) | set(frozen['papers']))

    def test_reviewed_record_and_text_hashes(self):
        for doi, fixture in fixtures().items():
            with self.subTest(doi=doi):
                record = reviewed_record(doi)
                self.assertEqual(hashlib.sha256(abstract_text(record).encode('utf-8')).hexdigest(), fixture['text_sha256'])

    def test_exact_addition_and_negative_mutations(self):
        from test_evidence_presentation import baseline, validate_pair
        for doi, fixture in fixtures().items():
            with self.subTest(doi=doi):
                name = 'papers/' + fixture['slug'] + '.html'
                before = baseline(name); after = (ROOT / name).read_text(encoding='utf-8')
                validate_pair(before, after, doi)
                block = expected_block(reviewed_record(doi), doi)
                mutations = [
                    after.replace('id="official-abstract"', 'id="official-abstract" hidden', 1),
                    after.replace(block, block + block, 1),
                    after.replace(block + '\n', '', 1).replace('</main>', block + '\n</main>', 1),
                    after.replace('<h2>Official Abstract</h2>', '<h2>Altered Abstract</h2>', 1),
                    after.replace('name="citation_abstract"', 'name="changed_abstract"', 1),
                    after.replace('"abstract":', '"unapproved_abstract":', 1),
                    after.replace('data-v2-section="research-question"', 'data-v2-section="changed-science"', 1),
                    after.replace('</main>', '<p>Unauthorized science</p></main>', 1),
                ]
                for mutated in mutations:
                    self.assertNotEqual(mutated, after)
                    with self.assertRaises(ValueError):
                        validate_pair(before, mutated, doi)


if __name__ == '__main__':
    unittest.main()
