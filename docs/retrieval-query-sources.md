# Query component sources and limits

The same local retrieval engine runs in Node and in the browser. It generates no
scientific answers, changes no reviewed evidence, and sends no query to a server.
All result text and `#qa-N` routes come from the existing public export.

## English question location

- Existing [MiniSearch 7.2.0](https://github.com/lucaong/minisearch/blob/v7.2.0/README.md)
  supplies field boosting, tokenization, term processing and BM25-style ranking.
  Question, answer, title and other visible text are separate derived fields.
- [words/stemmer 2.0.1](https://github.com/words/stemmer/tree/2.0.1) supplies the
  English Porter stemmer. The fixed source is inlined in `assets/evidence-search.js`
  with its complete MIT notice; only the ESM export is adapted to the existing
  browser closure. Original source SHA256:
  `154936155f541e1dca18bb75f0fe47c5d881f7b68b2953d92bd33254aca5cc39`.
  Source license SHA256:
  `9966260ba3ea9d6a5f839297dca80ddc99735a34b4ae82811cac7b956d2e3afd`.

Word forms are not biological entity identity. Rare title/concept terms must
remain in a candidate work; unmatched terms are reported. A matched clinical
word or a returned denial passage never validates a treatment premise.

## Tested alternatives and current limits

A bounded Chinese label adapter and multilingual semantic candidates were
actually compared with the same frozen queries. They are not silently enabled
by this English lexical release. Partial term mapping can discard meaning or
block valid questions; unfiltered semantic similarity can return unrelated
studies. Publishing this component does not establish natural AI discovery or
citation growth. Use the original evidence scope and DOI and keep assisted
translation or explicit client use separate from blind external discovery.
