(() => {
  const { location, gtag } = window;
  if (typeof gtag !== 'function') return;

  function trackPaperHandoff(event) {
    if (event.defaultPrevented || event.button !== (event.type === 'click' ? 0 : 1)) return;
    const link = event.target.closest?.('a[href]');
    if (!link) return;

    try {
      const target = new URL(link.href);
      // GA4 Enhanced Measurement owns outbound clicks. This event owns only
      // same-origin paper HTML, including its in-page evidence anchors.
      if (target.origin !== location.origin || !/^\/papers\/[a-z0-9-]+\.html$/.test(target.pathname)) return;
      // The stream already reports paper_path as an event-scoped dimension.
      // GA4 records the source from the guide's configured page location.
      gtag('event', 'research_handoff', {paper_path: target.pathname});
    } catch (_) {
      // Analytics must not interrupt navigation.
    }
  }

  document.addEventListener('click', trackPaperHandoff);
  document.addEventListener('auxclick', trackPaperHandoff);
})();
