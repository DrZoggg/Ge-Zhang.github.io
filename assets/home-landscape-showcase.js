/* Static decorative photograph only. The existing wave renderer owns all motion. */
(() => {
  'use strict';
  const hero = document.querySelector('body.home .hero');
  const surface = hero?.querySelector('.home-landscape');
  const art = surface?.querySelector('.home-landscape-art');
  if (!hero || !art) return;

  // Keep native picture format, media and density selection off the page.
  const chooser = document.createElement('picture');
  for (const attributes of JSON.parse(surface.dataset.sources)) {
    const source = document.createElement('source');
    for (const [name, value] of Object.entries(attributes)) source.setAttribute(name, value);
    chooser.append(source);
  }
  const image = document.createElement('img');
  image.decoding = 'async';
  image.fetchPriority = 'high';
  chooser.append(image);

  let enabled = true, loaded = false, failed = false, announced = false;
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
    art.style.backgroundImage = loaded ? `url(${JSON.stringify(image.currentSrc)})` : '';
    sync();
    if (loaded && !announced) {
      announced = true;
      window.dispatchEvent(new Event('home-landscape-ready'));
    }
  }
  function failure() {
    failed = true;
    loaded = false;
    art.style.removeProperty('background-image');
    sync();
  }
  image.addEventListener('load', success);
  image.addEventListener('error', failure);
  image.sizes = surface.dataset.sizes;
  image.srcset = surface.dataset.srcset;
  image.src = surface.dataset.src;
})();
