/* Source-visible disclosure and asynchronous homepage-only scene enhancement. */
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

  if (!document.querySelector('#observatory-wheel')) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const connection = navigator.connection;
  let loaded = false;
  const enhance = () => {
    if (loaded || reduced.matches || (connection && connection.saveData)) return;
    loaded = true;
    import('./scientific-visuals/index.js')
      .then(module => module.mountScientificVisuals())
      .catch(() => { document.documentElement.dataset.visuals = 'fallback'; });
  };
  reduced.addEventListener('change', enhance);
  if (connection && connection.addEventListener) connection.addEventListener('change', enhance);
  if ('requestIdleCallback' in window) requestIdleCallback(enhance, {timeout: 1200});
  else setTimeout(enhance, 0);
})();
