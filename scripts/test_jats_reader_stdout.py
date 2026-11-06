"""The bundled reader's redirected stdout is UTF-8 on legacy locales."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


READER = Path(__file__).parent / "jats-reader" / "jats_to_text.py"
OBSERVATION = "The mirror moved −0.25 µm."
XML = f"<article><body><sec><title>Results</title><p>{OBSERVATION}</p></sec></body></article>"


class JatsReaderStdoutTests(unittest.TestCase):
    def test_json_and_text_use_utf8_when_piped(self):
        env = dict(os.environ, PYTHONIOENCODING="gbk:strict")
        for flags in ([], ["--text-only"]):
            with self.subTest(flags=flags):
                result = subprocess.run(
                    [sys.executable, "-B", str(READER), "-", *flags],
                    input=XML.encode("utf-8"),
                    capture_output=True,
                    env=env,
                    check=True,
                )
                text = result.stdout.decode("utf-8")
                if not flags:
                    text = json.loads(text)["sections"][0]["text"]
                self.assertIn(OBSERVATION, text)


if __name__ == "__main__":
    unittest.main()
