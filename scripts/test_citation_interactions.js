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
  const doiHref = "https://doi.org/10.1234/example";
  const doiLink = { getAttribute: () => doiHref };
  const section = { querySelector: () => doiLink };
  function clickLink(href, area) {
    const link = {
      getAttribute: () => href,
      closest: (selector) => {
        if (selector === "#cite-this-paper") return area === "citation" ? section : null;
        assert.equal(selector, "main .hero .links");
        return area === "hero" ? {} : null;
      },
    };
    const target = { closest: (selector) => {
      if (selector === "#cite-this-paper a[href]") return area === "citation" ? link : null;
      assert.equal(selector, "a[href]");
      return link;
    } };
    callbacks.click({ target });
  }
  const button = {
    dataset: { copyCitation: "plain-citation-paper" }, hidden: true, textContent: "Copy citation",
    closest: () => section,
    addEventListener: (type, callback) => { callbacks.copy = callback; },
  };
  const document = {
    addEventListener: (type, callback) => { callbacks.click = callback; },
    querySelectorAll: () => [button],
    getElementById: (id) => id === "cite-this-paper" ? section : { textContent: "  Citation text  " },
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
    clickLink(href, "citation");
    assert.equal(events.at(-1).name, "citation_export");
    assert.equal(events.at(-1).params.citation_format, format);
  }
  clickLink(doiHref, "citation");
  clickLink(doiHref, "hero");
  assert.equal(events.length, 6, "The hero DOI click must emit the same event as the citation DOI click");
  clickLink("https://doi.org/10.1234/reference", "hero");
  clickLink("https://doi.org/10.1234/reference", "citation");
  clickLink("https://doi.org/10.1234/reference", "reference");
  clickLink(doiHref, "reference");
  assert.deepEqual(events.map((entry) => entry.name), [
    "citation_copy", "citation_export", "citation_export", "citation_export", "citation_doi_click",
    "citation_doi_click",
  ]);
  for (const event of events) {
    assert.equal(event.type, "event");
    assert.equal(event.params.paper_doi, "10.1234/example");
    assert.equal(event.params.paper_path, "/papers/paper.html");
  }
  callbacks.click({ target: { closest: () => null } });
  assert.equal(events.length, 6);
  console.log("CITATION INTERACTION TESTS PASS: copy, exports, original DOI links and ignored references");
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
