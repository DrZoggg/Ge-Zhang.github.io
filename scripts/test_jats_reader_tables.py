"""Exact table handoff through the bundled reader."""

import json
from pathlib import Path
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET


READER = Path(__file__).parent / "jats-reader" / "jats_to_text.py"
XML = b"""<article><body><sec><title>Results</title>
<p>See <xref ref-type="table" rid="T2">Table 2</xref>.</p></sec></body>
<floats-group>
<table-wrap id="T2"><table><thead><tr><th colspan="2">Adjusted model</th></tr></thead>
<tbody><tr><td>Reference</td><td>1.25 (1.04-1.51)</td></tr></tbody></table>
<table-wrap-foot><p>Adjusted for age.</p></table-wrap-foot></table-wrap>outside
<table-wrap id="image"><graphic href="external.png"/></table-wrap>
<table-wrap id="duplicate"/><table-wrap id="duplicate"/>
<table-wrap id="invalid"><response><p>Foreign content.</p></response></table-wrap>
</floats-group><sub-article><body><table-wrap id="T2"/>
<table-wrap id="foreign"/></body></sub-article></article>"""


def read(*args):
    run = subprocess.run(
        [sys.executable, "-B", str(READER), "-", *args],
        input=XML,
        capture_output=True,
        check=True,
    )
    return json.loads(run.stdout)


class JatsTableTests(unittest.TestCase):
    def test_explicit_table_retains_cells_and_footnotes(self):
        baseline = read("--sections", "results")
        result = read("--sections", "results", "--table-id", "T2")
        table, = result.pop("tables")
        self.assertEqual(result, baseline)
        self.assertEqual(table["locator"], "article/floats-group[1]/table-wrap[1]")
        self.assertTrue(table["has_embedded_table"])
        xml = ET.fromstring(table["table_xml"])
        self.assertEqual(xml.find(".//th").get("colspan"), "2")
        self.assertEqual(xml.findall(".//td")[1].text, "1.25 (1.04-1.51)")
        self.assertEqual(xml.findtext("./table-wrap-foot/p"), "Adjusted for age.")
        self.assertNotIn("outside", table["table_xml"])

    def test_unresolved_and_attachment_only_tables_are_distinct(self):
        output = read("--table-id", "t2", "--table-id", "foreign",
                      "--table-id", "duplicate", "--table-id", "invalid",
                      "--table-id", "image")
        missing, foreign, duplicate, invalid, image = output["tables"]
        self.assertEqual([missing["status"], foreign["status"]], ["not_found", "not_found"])
        self.assertEqual(duplicate["status"], "ambiguous")
        self.assertEqual(len(duplicate["candidate_locators"]), 2)
        self.assertEqual(invalid["status"], "unsupported_nested_article")
        self.assertNotIn("table_xml", invalid)
        self.assertFalse(image["has_embedded_table"])
        self.assertIn("external.png", image["table_xml"])


if __name__ == "__main__":
    unittest.main()
