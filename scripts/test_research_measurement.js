'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const tracker = read('assets/research-handoff.js');
const map = '/assets/research/gse59867-sample-followup-map.html';
const targets = [...read('sitemap.xml').matchAll(/<loc>https:\/\/drgezhang\.com(\/research\/[^<]+)<\/loc>/g)]
  .map(match => match[1]).filter(route => route !== '/research/questions.html').concat(map);
const expectedTargets = [
  '/research/dcm-hf-circulating-biomarkers.html',
  '/research/circadian-evidence-levels.html',
  '/research/cardiovascular-prediction-evidence.html',
  '/research/atherosclerosis-cell-mechanisms.html',
  '/research/cancer-omics-validation.html',
  '/research/gist-resection-evidence.html',
  map,
];
assert.deepEqual([...targets].sort(), [...expectedTargets].sort());

function install(initializer, address, referrer = '') {
  const window = {location: new URL(address)};
  const listeners = new Map();
  const loaders = [];
  const document = {
    referrer,
    createElement(tagName) {
      assert.equal(tagName, 'script');
      return {};
    },
    head: {appendChild(script) { loaders.push(script); }},
    addEventListener(type, listener) {
      assert.equal(listeners.has(type), false);
      listeners.set(type, listener);
    },
  };
  vm.runInNewContext(initializer, {URL, window, document}, {timeout: 1000});
  vm.runInNewContext(tracker, {URL, window, document}, {timeout: 1000});
  return {window, listeners, loaders};
}

function click(installed, destination, {type = 'click', button = 0, defaultPrevented = false} = {}) {
  const link = {href: destination};
  const target = {closest: selector => selector === 'a[href]' ? link : null};
  installed.listeners.get(type)?.({type, button, target, defaultPrevented});
}

for (const route of targets) {
  const page = read(route.slice(1));
  const [head] = page.split('</head>');
  const inline = [...head.matchAll(/<script>([\s\S]*?)<\/script>/g)]
    .map(match => match[1]).filter(script => script.includes('googletagmanager.com/gtag/js'));
  assert.equal(inline.length, 1, route);
  assert.equal([...page.matchAll(/\/assets\/research-handoff\.js/g)].length, 1);
  const production = install(inline[0], 'https://drgezhang.com' + route + '?q=PRIVATE_SEARCH#private-fragment',
    'https://example.net/private/referrer/path?q=UNSENT_REFERRER#fragment');
  const {window, listeners, loaders} = production;
  assert.equal(loaders.length, 1, route);
  assert.equal(loaders[0].async, true);
  assert.equal(loaders[0].src, 'https://www.googletagmanager.com/gtag/js?id=G-65LDZXWWQK');
  assert.deepEqual(Array.from(window.dataLayer, entry => entry[0]), ['js', 'config']);
  const conf = JSON.parse(JSON.stringify(window.dataLayer[1][2]));
  assert.deepEqual(conf, {
    page_location: 'https://drgezhang.com' + route,
    page_referrer: 'https://example.net',
  });
  for (const [query, campaign] of [
    ['utm_source=chatgpt.com&utm_medium=referral&q=PRIVATE_SEARCH'
      + '&utm_campaign=PRIVATE_CAMPAIGN&utm_term=PRIVATE_TERM&utm_content=PRIVATE_CONTENT#PRIVATE_HASH',
      {campaign_source: 'chatgpt.com', campaign_medium: 'referral'}],
    ['utm_source=chatgpt.com&utm_medium=PRIVATE_MEDIUM', {campaign_source: 'chatgpt.com'}],
    ['utm_source=PRIVATE_SOURCE&utm_medium=referral', {}],
    ['utm_medium=referral&q=PRIVATE_SEARCH', {}],
  ]) {
    const tagged = install(inline[0], 'https://drgezhang.com' + route + '?' + query);
    assert.equal(tagged.loaders.length, 1);
    assert.deepEqual(Array.from(tagged.window.dataLayer, entry => entry[0]), ['js', 'config']);
    assert.deepEqual(JSON.parse(JSON.stringify(tagged.window.dataLayer[1][2])), {
      page_location: 'https://drgezhang.com' + route,
      page_referrer: '',
      ...campaign,
    });
  }

  // The one config call owns the implicit GA4 page_view.
  assert.equal(Object.hasOwn(conf, 'send_page_view'), false);
  assert.deepEqual([...listeners.keys()], ['click', 'auxclick']);

  click(production, 'https://drgezhang.com/papers/olink-dcm.html?query=UNSENT_TARGET#kf2');
  assert.equal(window.dataLayer.length, 3);
  assert.deepEqual(JSON.parse(JSON.stringify(Array.from(window.dataLayer[2]))),
    ['event', 'research_handoff', {paper_path: '/papers/olink-dcm.html'}]);
  click(production, 'https://drgezhang.com/papers/olink-dcm.html', {type: 'auxclick', button: 1});
  assert.equal(window.dataLayer.length, 4);

  // Outbound targets belong to GA4's native click, so the custom delegate
  // never sends a second event for a DOI, publisher, or supplement.
  for (const href of [
    'https://doi.org/10.1021/acs.jproteome.4c00522',
    'https://doi.org/10.1021/acs.jproteome.4c00522.s005',
    'https://pubs.acs.org/doi/10.1021/acs.jproteome.4c00522',
    'https://drgezhang.com.examples.invalid/papers/olink-dcm.html',
    'https://www.drgezhang.com/papers/olink-dcm.html',
    'https://drgezhang.com:8443/papers/olink-dcm.html',
    'https://drgezhang.com/papers/olink-dcm.md',
    'https://drgezhang.com/citations/doi-10-1021-acs-jproteome-4c00522.ris',
    'https://drgezhang.com/publications.html',
    'mailto:research@example.net',
    'http://%',
  ]) click(production, href);
  click(production, 'https://drgezhang.com/papers/olink-dcm.html', {button: 2});
  click(production, 'https://drgezhang.com/papers/olink-dcm.html', {type: 'auxclick', button: 2});
  click(production, 'https://drgezhang.com/papers/olink-dcm.html', {defaultPrevented: true});
  assert.equal(window.dataLayer.length, 4);

  for (const origin of [
    'http://localhost:8765', 'https://preview.drgezhang.com',
    'http://drgezhang.com', 'https://drgezhang.com:8443', 'https://drzoggg.github.io',
  ]) {
    const preview = install(inline[0], origin + route + '?utm_source=chatgpt.com&utm_medium=referral');
    assert.equal(preview.loaders.length, 0, origin);
    assert.equal(preview.listeners.size, 0, origin);
    assert.equal(preview.window.dataLayer, undefined, origin);
  }
  const www = install(inline[0], 'https://www.drgezhang.com' + route);
  assert.equal(www.loaders.length, 1);
  assert.equal(www.window.dataLayer[1][2].page_referrer, '');
}
console.log('RESEARCH MEASUREMENT PASS: ' + targets.length + ' generated pages, one config, fixed ChatGPT labels, two activation types and no production load on previews');
