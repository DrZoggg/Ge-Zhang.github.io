/* Static decorative photograph only. The existing wave renderer owns all motion. */
(() => {
  'use strict';
  const hero = document.querySelector('body.home .hero');
  const image = hero?.querySelector('.home-landscape img');
  if (!hero || !image) return;
  let enabled = true, loaded = false, failed = false;
  function sync() {
    if (enabled && loaded && !failed) hero.dataset.landscape = 'ready';
    else delete hero.dataset.landscape;
  }
  const api = {
    setEnabled(value) { enabled = Boolean(value); sync(); },
    metrics() { return { enabled, loaded, failed, active: hero.dataset.landscape === 'ready', source: image.currentSrc }; },
  };
  window.__homeLandscape = api;
  function success() {
    loaded = image.naturalWidth > 0;
    failed = !loaded;
    sync();
    window.dispatchEvent(new Event('home-landscape-ready'));
  }
  function failure() { failed = true; loaded = false; sync(); }
  image.addEventListener('load', success, { once: true });
  image.addEventListener('error', failure, { once: true });
  if (image.complete) { if (image.naturalWidth) success(); else failure(); }
})();
