"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

async function main() {
  const source = fs.readFileSync(path.join(__dirname, "..", "assets", "citation.js"), "utf8");
  const events = [];
  const callbacks = {};
  let copyFails = false;
  const doiLink = { getAttribute: () => "https://doi.org/10.1234/example" };
  const section = { querySelector: () => doiLink };
  const button = {
    dataset: { copyCitation: "plain-citation-paper" }, hidden: true, textContent: "Copy citation",
    closest: () => section,
    addEventListener: (type, callback) => { callbacks.copy = callback; },
  };
  const document = {
    addEventListener: (type, callback) => { callbacks.click = callback; },
    querySelectorAll: () => [button],
    getElementById: () => ({ textContent: "  Citation text  " }),
  };
  const window = { location: { pathname: "/papers/paper.html" }, setTimeout: () => {} };
  const navigator = { clipboard: { writeText: async (text) => {
    assert.equal(text, "Citation text");
    if (copyFails) throw new Error("clipboard denied");
  } } };
  vm.runInNewContext(source, { document, window, navigator });
  assert.equal(button.hidden, false);
  await callbacks.copy(); // No gtag: citation copy still works.
  assert.equal(button.textContent, "Copied");
  window.gtag = (type, name, params) => events.push({ type, name, params });
  copyFails = true;
  await callbacks.copy();
  assert.equal(events.length, 0); // Failed copy is not measured.
  copyFails = false;
  await callbacks.copy();
  for (const [href, format] of [
    ["../citations/paper.bib", "bibtex"],
    ["../citations/paper.ris", "ris"],
    ["../citations/paper.csl.json", "csl_json"],
  ]) {
    const link = { getAttribute: () => href, closest: () => section };
    callbacks.click({ target: { closest: () => link } });
    assert.equal(events.at(-1).name, "citation_export");
    assert.equal(events.at(-1).params.citation_format, format);
  }
  callbacks.click({ target: { closest: () => ({ getAttribute: () => "https://doi.org/10.1234/example", closest: () => section }) } });
  assert.deepEqual(events.map((entry) => entry.name), [
    "citation_copy", "citation_export", "citation_export", "citation_export", "citation_doi_click",
  ]);
  for (const event of events) {
    assert.equal(event.type, "event");
    assert.equal(event.params.paper_doi, "10.1234/example");
    assert.equal(event.params.paper_path, "/papers/paper.html");
  }
  callbacks.click({ target: { closest: () => null } });
  assert.equal(events.length, 5);
  console.log("CITATION INTERACTION TESTS PASS: successful copy, exports, DOI, absent gtag and failed copy");
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
