# Optional manuscript-packet metadata fidelity

This adaptation keeps publication genre separate from research design. A Letter
can report an original trial or cohort, or contribute a reporting proposal;
mentioning another trial does not make the Letter itself a clinical trial.
It retains these sources as possible Introduction and Discussion material.

The example is opt-in, source-neutral and local. It changes neither search
queries nor preferred authors, domains or DOIs. Corrected metadata can change
packet order under the consumer's existing quality-based ranking. No external
AI service automatically installs or uses this patch.

## Apply to the pinned consumer

Use an isolated copy of
[`K-Dense-AI/scientific-agent-skills` at `5f2bc0341354fd5590aef76a533ada1e1e5b4e62`](https://github.com/K-Dense-AI/scientific-agent-skills/tree/5f2bc0341354fd5590aef76a533ada1e1e5b4e62).
The target is `skills/research-lookup/scripts/manuscript_packet.py`, whose original
SHA256 is `604ab0e92b6ba62de10f7a4c3bc52247a5e86e28d9e26c07fb49d215302f91cf`.
The patch SHA256 is
`61a19f9fee791c2c7c1ddb2e6da0aae03ca2631b4fbec9841e508f5039d9066e`.

From that consumer checkout, after checking the version and original file hash:

```sh
git -c core.autocrlf=false apply --check /path/to/metadata-fidelity.patch
git -c core.autocrlf=false apply /path/to/metadata-fidelity.patch
python /path/to/verify_metadata_fidelity.py skills/research-lookup/scripts/manuscript_packet.py
```

The applied helper SHA256 should be
`151516044e53664105e1ffa83a518552febb9eca31b9cc1304f052378f37c101`.
The per-command Git setting avoids Windows line-ending changes; it does not
modify global configuration. Python 3.10+ and the standard library suffice for
this offline check. The helper is a module, not a new network search CLI.

## Supply actual source metadata

The existing `normalize_reference(source, index)` and packet-building functions
accept the same source dictionaries. This adaptation additionally recognizes:

- `publication_type`: a whole genre/design name or list, such as `Letter`,
  `Journal Article` or `Randomized Controlled Trial`.
- `study_design`: a separately supplied design, such as `cohort study`,
  `randomized controlled trial` or `narrative argument`.
- `evidence_quality`: a supplied grade is retained as a caller assertion. Its
  `quality_rationale` or `evidence_quality_basis` is retained with provenance;
  `evidence_quality_verified: true` records a caller attestation. If none is
  supplied, the output explicitly records the missing appraisal basis. None
  of these fields is independent verification by the helper.

Use the source's actual metadata and design description. If neither is available,
the fallback recognizes limited self-study wording and otherwise leaves design
unknown. `summary` is a snippet fallback only when no excerpt field exists; it
never overrides an explicit empty extraction and does not change reading status. It distinguishes negated, planned and quoted trial mentions from an
explicit completed design; null trial results still retain their trial design.
The text fallback is deliberately not a complete scientific-language parser.

Output preserves publication genre and research design as independent fields.
Study design does not automatically generate a quality appraisal: without a
supplied assessment, quality stays unknown even for an RCT or systematic review.
Supplied moderate or low grades are not overwritten by design-only high labels.
Retraction handling has priority over a supplied grade. The consumer's sorting
labels do not assess risk of bias or a source's value for every writing purpose. Identity, excerpts, citation formatting and
Introduction/Discussion relevance remain available. No new source filter is added.

The actual packet path retains summary snippets and later same-DOI metadata when
joining search and typed representations. It keeps each supplied metadata bundle
with its source URL in `metadata_assertions` for joined typed sources. Conflicting
genre, design or quality assertions are exposed in `metadata_conflicts` and the
affected output field becomes unknown, rather than silently choosing the last
representation. A grade stays bundled with its own rationale; matching grades
can retain multiple caller rationales. These are supplied assertions, not newly
verified facts or independent studies. Existing DOI deduplication still counts
them as one work. These assertion bundles also survive the existing runner's
repeated deduplication, extraction join and final packet-building sequence.

The included verification runs synthetic boundary cases, summary-only and
same-DOI duplicate and repeated-deduplication packet paths, conflicting assertions,
search-to-extract joining, and actual packet file
exports without network access or licensed article text. This demonstrates local
consumer behavior, not increased natural discovery or new published citations.

## License and origin

The patch modifies one helper from the pinned MIT-licensed upstream version,
Copyright (c) 2025 K-Dense Inc. The full notice is retained in
[LICENSE.kdense.md](LICENSE.kdense.md). It adds metadata recognition, separates
genre/design, narrows text-based design inference, preserves supplied metadata through the
packet's duplicate-joining path, and keeps quality assessments with provenance
instead of inferring them from study design. Other consumer helpers and this site's scientific content
are unchanged.
