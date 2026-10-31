# Local multilingual evidence exploration

Use this optional consumer to find reviewed research questions from natural English or Chinese, then read the original answer, study identity, findings, scope and sources before selecting a formal paper for research or writing. It supplements the existing [read-only client](author-evidence-client.md); ordinary website search and exact DOI/identity lookup keep their existing lightweight route.

## Connect explicitly

A local clone, Node.js for the original packet client, and Python3.11+ are needed. Install the optional model runtime in an isolated environment:

```powershell
python -m venv .venv-evidence-semantic
& '.\.venv-evidence-semantic\Scripts\python.exe' -m pip install -r scripts/requirements-evidence-semantic.txt
New-Item -ItemType Directory -Force .evidence-semantic | Out-Null

# Explicitly download and verify the fixed public model data files.
& '.\.venv-evidence-semantic\Scripts\python.exe' scripts/author_evidence_semantic.py --prepare-model

& '.\.venv-evidence-semantic\Scripts\python.exe' scripts/author_evidence_semantic.py 'heart failure artificial intelligence external validation clinical utility' --mode explore --output .evidence-semantic/result.json
```

`--mode explore` is required for every search. Model preparation is the only exception. No web page loads this command or downloads its model. The two model files total135,429,554bytes; the default model/vector directory is the current user's `.cache/drgezhang-evidence-semantic/`, outside the repository. `--model-dir`, `--cache-dir` and `--root` select existing private storage and a local clone. Never commit model files, caches, environments or query results. Inference and packet reading are local; no query or credentials are transmitted.

An already connected research Agent can submit a batch as UTF-8 JSON:

```json
{"cases":[{"id":"q1","query":"为心力衰竭AI研究寻找外部验证的原始证据"}]}
```

```powershell
& '.\.venv-evidence-semantic\Scripts\python.exe' scripts/author_evidence_semantic.py --queries .evidence-semantic/queries.json --mode explore --output .evidence-semantic/results.json
```

This is explicit tool integration. It does not cause an unconnected AI/search provider to adopt the tool or prefer the author's website.

## Read and use the returned evidence

`rows[].ranked` contains stable QA/work IDs, DOI, answer URLs, similarity and per-work matched/unmatched query terms. Corresponding `evidence_packets` are fetched through the existing strict Node client, retaining publication identity, study type/profile, original reviewed answer, supporting findings and locators, full scope/limitations, source pointers, content version and citation links. Scores are similarities, not probabilities; exploration can include unrelated candidates, so check missing entities and the complete packet before citation.

The complete original English/Chinese query enters the pinned model without dictionary rewriting. Coverage metadata does not change ranking. Source-bound Chinese labels are topic cues rather than a complete translation. Embedding inputs are capped at512tokens, while returned evidence packets retain their full content. The local vector cache is bound to the source dataset and model revision; it rebuilds when that source changes. Works without reviewed QA retain their existing identity/lexical route rather than acquiring synthetic answers.

Keep query batches fixed when comparing runs: quantized scores and near-tied candidate order can vary with batch padding. Source versions are checked throughout each run; changed exports fail instead of mixing an old index with new evidence.

In actual connected-consumer exercises, the fixed English request above and an original Chinese Introduction/validation-design request found AIHFLevel. Reading the parent work's existing question directory located both the external-validation answer and the clinical-outcome boundary. The consumer selected [the formal paper, DOI10.1038/s41467-024-50415-9](https://doi.org/10.1038/s41467-024-50415-9), with the author's [QA3](https://drgezhang.com/papers/aihflevel.html#qa-3) and [QA8](https://drgezhang.com/papers/aihflevel.html#qa-8) as supplementary explanation. A narrative Correspondence was kept as background rather than counted as a primary validation study. Same-DOI representations count as one research unit. These are observed connected workflows, separate from natural search/citation measurements.

## Availability and model source

Missing dependencies or model files produce a clear error. An explicit fallback can instead invoke the unchanged lexical client:

```powershell
python scripts/author_evidence_semantic.py 'KIF13B atherosclerosis' --mode explore --on-unavailable lexical --output .evidence-semantic/fallback.json
```

The output then says `mode: "explicit_lexical_fallback"` and `semantic_executed: false`; successful model execution says `semantic_executed: true`. Data-validation failures still fail rather than returning mismatched evidence.

The model is [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small), fixed revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, declared MIT. Its official quantized ONNX and tokenizer files are checked against fixed LFS SHA256. ONNX Runtime is MIT, NumPy BSD-3-Clause and Tokenizers Apache-2.0; retain their package notices. Chinese topic labels use [Wikidata CC0 data](https://www.wikidata.org/wiki/Wikidata:Licensing) with disclosed editorial label variants. The source code preserves item URLs.

On the tested local CPU, model loading took about0.8–1.1seconds and the first362-QA index build about4seconds; a short consumer run peaked near0.55GB process memory. These measurements describe one machine rather than a device-independent latency promise. No server, MCP, vector database or default production dependency is introduced.

Run `python scripts/test_evidence_semantic.py` for the source-update and explicit-fallback checks; they require no model download or inference.
