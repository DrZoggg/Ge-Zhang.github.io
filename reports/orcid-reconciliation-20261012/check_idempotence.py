"""Second-build byte equality for all website source and generated artifacts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def hashes():
    paths = [p for folder in ("assets", "citations", "data", "papers", "research", "scripts", ".github")
             for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    paths += [p for p in ROOT.iterdir() if p.is_file() and p.suffix in {".html", ".json", ".xml", ".txt", ".csv"}]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


before = hashes()
run = subprocess.run([sys.executable, "scripts/build_publications.py"], cwd=ROOT, capture_output=True)
assert run.returncode == 0, run.stderr.decode(errors="replace")
after = hashes()
assert before == after, sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
result = {"second_build": "PASS", "compared_files": len(before), "changed_files": []}
(OUT / "IDEMPOTENCE.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
