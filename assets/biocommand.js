/* Visual 3.0: progressive disclosure and one optional conceptual orbit. */
(() => {
  'use strict';

  // All selected titles, summaries and links are already in the HTML.
  // Without this enhancement every selected work remains visible.
  const collection = document.getElementById('featured-papers');
  const toggle = document.getElementById('featured-toggle');
  if (collection && toggle) {
    const cards = Array.from(collection.querySelectorAll('.paper'));
    const firstCount = 6;
    if (cards.length > firstCount) {
      let expanded = true;
      function disclose(next, interacted = false) {
        if (!next && cards.slice(firstCount).some(card => card.contains(document.activeElement))) {
          toggle.focus({preventScroll: true});
        }
        cards.forEach((card, i) => { card.hidden = !next && i >= firstCount; });
        expanded = next;
        toggle.setAttribute('aria-expanded', String(next));
        toggle.textContent = next ? 'Show first 6' : 'Show all selected research (' + cards.length + ')';
        if (interacted && next) {
          const firstNewLink = cards[firstCount].querySelector('h3 a');
          if (firstNewLink) firstNewLink.focus({preventScroll: true});
          cards[firstCount].scrollIntoView({block: 'nearest', behavior: 'instant'});
        } else if (interacted) {
          toggle.focus({preventScroll: true});
          toggle.scrollIntoView({block: 'nearest', behavior: 'instant'});
        }
      }
      toggle.addEventListener('click', () => disclose(!expanded, true));
      toggle.setAttribute('aria-controls', collection.id);
      disclose(false);
      toggle.hidden = false;
    }
  }

  const scene = document.querySelector('.bio-scene');
  const orbit = scene && scene.querySelector('.bio-orbit');
  const control = document.querySelector('.motion-toggle');
  if (!scene || !orbit || !control || typeof matchMedia !== 'function') return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const desktop = matchMedia('(min-width: 960px) and (hover: hover) and (pointer: fine)');
  const connection = navigator.connection;
  const constrained = (navigator.deviceMemory > 0 && navigator.deviceMemory <= 2)
    || (navigator.hardwareConcurrency > 0 && navigator.hardwareConcurrency <= 2);
  let paused = false;
  let visible = !('IntersectionObserver' in window);
  let animation = null;

  function sync() {
    if (!animation) {
      scene.dataset.motion = 'static';
      return;
    }
    const stopped = paused || !visible || document.hidden || reduce.matches;
    stopped ? animation.pause() : animation.play();
    scene.dataset.motion = stopped ? 'paused' : 'running';
  }
  function start() {
    if (animation) animation.cancel();
    animation = null;
    const enabled = !reduce.matches && desktop.matches && !constrained
      && !(connection && connection.saveData) && typeof orbit.animate === 'function';
    control.hidden = !enabled;
    control.setAttribute('aria-pressed', String(paused));
    control.textContent = paused ? 'Resume motion' : 'Pause motion';
    if (enabled) {
      animation = orbit.animate(
        [{transform: 'rotate(0deg)'}, {transform: 'rotate(360deg)'}],
        {duration: 28000, iterations: Infinity, easing: 'linear'}
      );
    }
    sync();
  }
  control.addEventListener('click', () => {
    paused = !paused;
    control.setAttribute('aria-pressed', String(paused));
    control.textContent = paused ? 'Resume motion' : 'Pause motion';
    sync();
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      sync();
    }, {threshold: 0.05});
    observer.observe(scene.closest('.bio-visual') || scene);
  }
  [reduce, desktop].forEach(query => {
    if (query.addEventListener) query.addEventListener('change', start);
    else if (query.addListener) query.addListener(start);
  });
  if (connection && connection.addEventListener) connection.addEventListener('change', start);
  document.addEventListener('visibilitychange', sync);
  window.addEventListener('pagehide', () => {
    if (animation) animation.cancel();
    animation = null;
    scene.dataset.motion = 'static';
  });
  window.addEventListener('pageshow', event => { if (event.persisted) start(); });
  start();
})();
