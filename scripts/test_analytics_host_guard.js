'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Execute the actual generated inline analytics initializer with no browser,
// network, credentials or real GA events.
const page = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const scripts = [...page.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)]
  .map(match => match[1]).filter(text => text.includes('googletagmanager.com/gtag/js'));
assert.equal(scripts.length, 1);
const measurement = 'G-65LDZXWWQK';
const cases = [
  ['https:', 'drgezhang.com', true], ['https:', 'www.drgezhang.com', true],
  ['http:', 'drgezhang.com', false], ['https:', 'localhost', false],
  ['http:', 'localhost', false], ['http:', '127.0.0.1', false],
  ['https:', '127.0.0.1', false], ['http:', '[::1]', false],
  ['file:', '', false], ['file:', 'drgezhang.com', false],
  ['https:', 'preview.drgezhang.com', false],
  ['https:', 'drzoggg.github.io', false],
  ['https:', 'drgezhang.com.example.org', false],
  ['https:', 'other-drgezhang.com', false]
];
for (const [protocol, hostname, allowed] of cases) {
  const added = [];
  const window = {location: {protocol, hostname}};
  const document = {
    createElement(name) {
      assert.equal(allowed, true, 'Nonproduction host tried to create a loader');
      assert.equal(name, 'script');
      return {};
    },
    head: {appendChild(script) { added.push(script); }}
  };
  vm.runInNewContext(scripts[0], {window, document}, {timeout: 1000});
  assert.equal(added.length, allowed ? 1 : 0, protocol + hostname);
  if (allowed) {
    assert.equal(added[0].async, true);
    assert.equal(added[0].src, 'https://www.googletagmanager.com/gtag/js?id=' + measurement);
    assert.equal(typeof window.gtag, 'function');
    assert.equal(window.dataLayer.length, 2);
    assert.equal(window.dataLayer[0][0], 'js');
    assert.equal(window.dataLayer[1][0], 'config');
    assert.equal(window.dataLayer[1][1], measurement);
    window.gtag('event', 'citation_export', {citation_format: 'bibtex'});
    assert.equal(window.dataLayer.length, 3);
    assert.equal(window.dataLayer[2][1], 'citation_export');
  } else {
    assert.equal(window.dataLayer, undefined);
    assert.equal(window.gtag, undefined);
  }
}
// Existing production dataLayer entries survive initialization.
const seed = ['existing-entry'];
const window = {location: {protocol: 'https:', hostname: 'drgezhang.com'}, dataLayer: seed};
vm.runInNewContext(scripts[0], {window, document: {createElement() {return {};},
  head: {appendChild() {}}}}, {timeout: 1000});
assert.equal(window.dataLayer, seed);
assert.equal(seed[0], 'existing-entry');
assert.equal(seed.length, 3);
console.log('ANALYTICS HOST GUARD PASS: ' + cases.length + ' origins, preserved production queue and citation-event interface; no network sent');
