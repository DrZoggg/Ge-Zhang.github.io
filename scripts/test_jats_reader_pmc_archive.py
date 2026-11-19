"""PMC OAI-PMH article envelopes follow the same reading contracts as bare JATS."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


READER = Path(__file__).parent / "jats-reader" / "jats_to_text.py"
ARCHIVE = "https://jats.nlm.nih.gov/ns/archiving/1.4/"
OAI = "http://www.openarchives.org/OAI/2.0/"
FRONT = (
    "<front><article-meta><article-id pub-id-type='doi'>10.1234/example</article-id>"
    "<title-group><article-title>Archive fixture</article-title></title-group>"
    "</article-meta></front>"
)
BODY = (
    "<body><sec><title>Methods</title><p>Body observation.</p></sec>"
    "<supplementary-material id='s1' xlink:href='appendix.pdf'>"
    "<label>Supplement</label></supplementary-material></body>"
)


def article(body: str = BODY) -> str:
    return f"<article xmlns='{ARCHIVE}' xmlns:xlink='http://www.w3.org/1999/xlink'>{FRONT}{body}</article>"


def get_record(content: str) -> str:
    return f"<OAI-PMH xmlns='{OAI}'><GetRecord><record><metadata>{content}</metadata></record></GetRecord></OAI-PMH>"


def read(xml: str, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-X", "utf8", "-B", str(READER), "-", *flags],
        input=xml.encode("utf-8"),
        capture_output=True,
    )


class PmcArchiveTests(unittest.TestCase):
    def test_bare_and_wrapped_article_emit_same_body_and_attachment(self):
        outputs = []
        for xml in (article(), get_record(article())):
            result = read(xml, "--include-supplementary-material")
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertIn("Body observation.", output["sections"][0]["text"])
            self.assertIn("10.1234/example", result.stdout.decode("utf-8"))
            self.assertIn("appendix.pdf", result.stdout.decode("utf-8"))
            outputs.append(output)
        self.assertEqual(outputs[0], outputs[1])

    def test_metadata_only_does_not_become_full_text(self):
        result = read(get_record(article("")))
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_multiple_articles_are_rejected_without_selecting_the_first(self):
        result = read(get_record(article() + article()))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(b"expected one JATS article", result.stderr)


if __name__ == "__main__":
    unittest.main()
