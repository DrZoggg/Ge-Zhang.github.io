# Optional review-to-original citation contexts

This example adds an opt-in citation-context field to the existing K-Dense JATS
reader. It helps a research writer follow a relevant review paragraph to the
original studies before flattening or summarizing the text.

It is a local adaptation, not an upstream feature or a newly installed Skill.
No search ranking, preferred author, website, gene or DOI is built into it.

## Apply to the pinned consumer

The patch targets
[`K-Dense-AI/scientific-agent-skills` at `5f2bc0341354fd5590aef76a533ada1e1e5b4e62`](https://github.com/K-Dense-AI/scientific-agent-skills/tree/5f2bc0341354fd5590aef76a533ada1e1e5b4e62),
file `skills/paper-lookup/scripts/jats_to_text.py` (SHA256
`2185a4994dc41216e160ab173183cda42b5d3e5be82547f470df6dcd6fe3a53d`).
Use an isolated checkout of that version, retaining its other helper files:

```sh
git apply --check /path/to/kdense-jats-reference-sidecar.patch
git apply /path/to/kdense-jats-reference-sidecar.patch
python skills/paper-lookup/scripts/jats_to_text.py article.xml --include-cited-references
```

`article.xml` is a legitimately available JATS article selected by the caller.
The example does not download articles, authenticate, call a paid service, or
submit anything to a search engine. Keep the article's license and provenance.

Without the new flag, the reader's existing JSON output is unchanged. With it,
`citation_contexts` contains paragraph text, section identity, exact bibliography
cross-references and the cited works' available DOI/PMID/PMCID. Missing references
remain explicit. Bibliography identities stay separate from the source article's
identity; co-citation is a reading route, not proof that every reference supports
every clause. Read the selected original study before using its specific findings.

## Use in a research-writing workflow

1. Search normally for the research question and retain relevant competing studies.
2. Resolve the selected review to the consumer's canonical record ID. If an ID is
   not recognized, record that resolution failure rather than reporting no references.
3. Use a bounded citation-graph expansion for general related evidence. For a
   specific mechanism or method in the review, inspect its paragraph-level
   `citation_contexts` as a separate route; a ranked top-k list need not cover it.
4. Select originals by their contribution to the task, record the actual abstract
   or body read, and cite the formal paper's DOI. Deduplicate multiple representations.

The adaptation was run on an official review JATS document and retained the
relevant paragraph's competing references. That is explicit consumer compatibility,
not evidence that unconnected AI tools automatically use this example or that
natural academic citations have increased.

## License and origin

Upstream K-Dense code is MIT, Copyright (c) 2025 K-Dense Inc.; its license is
retained in [LICENSE.kdense.md](LICENSE.kdense.md). The local modification adds
`collect_citation_contexts`, the opt-in argument, and the separate output field.
It preserves the existing reader's metadata-only refusal and default output.
