"""Run existing citation regressions on their original, locked metadata fixture.

The two new unsupported genres are checked separately by verify_delivery.py.
Do not modify the shared renderer or claim their exports passed this regression.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import test_citations
from citation_common import citation_skip_reason

load_all = test_citations.load_citation_metadata
NEW_UNSUPPORTED = {"10.1126/science.aek9583", "10.1016/j.medd.2026.100004"}


def original_fixture(publications, *args, **kwargs):
    full = load_all(publications, *args, **kwargs)
    if args or kwargs:
        return full
    for doi in NEW_UNSUPPORTED:
        record = next(r for r in publications if r.get("doi") == doi)
        assert citation_skip_reason(record).startswith("unsupported type:")
    return {doi: fields for doi, fields in full.items() if doi not in NEW_UNSUPPORTED}


test_citations.load_citation_metadata = original_fixture
test_citations.run_tests()
print("Scope: existing corpus exports only; new Letter/Correspondence exports remain explicitly deferred.")
