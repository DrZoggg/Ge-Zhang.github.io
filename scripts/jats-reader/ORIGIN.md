# Portable JATS reader: origin and use

This directory packages the existing K-Dense JATS reader with the cumulative
[optional reference-sidecar patch](../../examples/review-citation-contexts/kdense-jats-reference-sidecar.patch)
already applied. It is an explicitly invoked local-file CLI, not an upstream
default, installed Skill, source-preference rule or article-retrieval service.
No Node author-client hook, account, package install or model call is required.

## Source and license

Upstream: [K-Dense-AI/scientific-agent-skills at
5f2bc0341354fd5590aef76a533ada1e1e5b4e62](https://github.com/K-Dense-AI/scientific-agent-skills/tree/5f2bc0341354fd5590aef76a533ada1e1e5b4e62),
paper-lookup v2.4, `skills/paper-lookup/scripts/jats_to_text.py` and `_common.py`.
The upstream reader SHA-256 before the patch is
`2185a4994dc41216e160ab173183cda42b5d3e5be82547f470df6dcd6fe3a53d`.
The cumulative patch applies to that original version, not an already patched reader.
Its SHA-256 is `6ba78d271fd7b5babf4edde12f8cda5e1446fa0df2c5d6908c82d0efe64ef21a`.
The [existing patch instructions and structural verifier](../../examples/review-citation-contexts/README.md)
remain available for consumers maintaining a separate pinned upstream checkout.

The complete upstream MIT notice, Copyright (c) 2025 K-Dense Inc., is retained in
[LICENSE.kdense.md](LICENSE.kdense.md). `_common.py` is unchanged. The bundled
reader also includes the optional attachment and exact table-ID flags below.
Shipped SHA-256:

| File | SHA-256 |
| --- | --- |
| `jats_to_text.py` | `d1b05ed17ae56b313e9bbaa79eb77da6f2265feeb6c5e99ad5edefea857d7934` |
| `_common.py` | `4c6962ddbcb8cb89adc6c6ac02199835310f04b2ab93ffab9855adef38efd369` |
| `LICENSE.kdense.md` | `09b02a3c9df3053c55531d503357a9c7cde275970e6c3ceaa1ddf5f0e90b40c1` |

## Direct calls

Use Python 3.10+ and its standard library. Run from this repository's root after
saving a lawfully accessible JATS article locally:

```sh
python -X utf8 -B scripts/jats-reader/jats_to_text.py article.xml --include-cited-references -o reading.json
```

The source argument `-` reads stdin. For example, in a POSIX shell:

```sh
cat article.xml | python -X utf8 -B scripts/jats-reader/jats_to_text.py - --include-cited-references -o reading.json
```

A consumer can invoke the same argument list with its existing subprocess tool,
supply XML on stdin and retain the returned JSON with its own reading record.
The bundled CLI writes UTF-8 to redirected stdout for both JSON and text output,
including on Windows. Decode captured stdout as UTF-8. The separate upstream
sidecar patch covers extraction only.
The reader does not download articles or select papers for the consumer.

Add `--include-supplementary-material` to return the article's declared attachment
filenames or hrefs, supplement labels and XML locators alongside the body.
The sidecar covers the owning article even when the body is section-filtered.
Treat its hrefs as source declarations. Confirm the selected attachment in the
publisher's article page or the [official versioned PMC dataset](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/)
before opening it. For PMC, check the DOI and version in the corresponding
`metadata/PMC….<version>.json` object, then match the declared filename against
`media_urls` and verify its checksum. Compare the actual table headings, study
direction and values with the body before using the article as evidence.
Continue to cite the formal paper DOI.

The section text omits tables. For a claim that depends on table values, use the
exact, case-sensitive XML ID from the article's table cross-reference, such as
`rid="tab2"` in the original JATS:

```sh
python -B scripts/jats-reader/jats_to_text.py article.xml --sections results --table-id tab2
```

Repeat `--table-id` to request more tables. In a full-text result, each selection
returns its status, article-relative locator and, when uniquely found, the
reserialized `table-wrap` XML. The XML retains cell spans and footnotes. Table
lookup covers the owning article, including floating tables, even when section
text is filtered. A located graphic or attachment-only table has
`has_embedded_table: false`. The reader leaves its external file unopened.

## Compatibility and repair scope

With neither opt-in flag, the original release's default JSON schema is retained.
Direct body paragraphs interleaved with sections are now included in
source order, which can correct section/word counts for that layout. The owning
article's text and metadata exclude foreign sub-articles and responses.

The opt-in flag adds `citation_contexts` and `bibliography_references`: exact
source locators, bibliography cross-reference groups and explicit typed identities.
Same-citation `citation-alternatives` representations remain one reference; legacy
direct-citation precedence is preserved. Conflicting fields and duplicate reference
IDs stay unresolved with their candidates and locators; other readable text and
unambiguous fields remain available. Numeric citation ranges expand only when the
explicit label map is unique, complete and consistent. No title, arbitrary URL or
unlabelled prose is used to guess a DOI.

The original body-required behavior remains: metadata-only input emits metadata
and exits 2 unless the caller explicitly supplies `--allow-metadata-only`.
`--sections` uses top-level title/sec-type substring filtering, and `--text-only`
emits text without JSON sidecars. A parsed reference does not establish that its
original was read, supports a claim, was used in a draft or received a published
citation. A consumer must actually invoke this CLI to use it; distribution alone
does not upgrade a consumer or establish adoption.
