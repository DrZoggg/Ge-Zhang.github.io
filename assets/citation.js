function trackCitationEvent(name, details, section) {
  if (typeof window.gtag !== 'function') return;
  const doiLink = section.querySelector('a[href^="https://doi.org/"]');
  const href = doiLink ? doiLink.getAttribute('href') : '';
  const metadata = { paper_path: window.location.pathname };
  if (href) metadata.paper_doi = href.slice('https://doi.org/'.length);
  try {
    window.gtag('event', name, { ...metadata, ...details });
  } catch (_) {
    // Analytics must never interfere with citation actions.
  }
}

document.addEventListener('click', (event) => {
  const link = event.target.closest && event.target.closest('#cite-this-paper a[href]');
  if (!link) return;
  const section = link.closest('#cite-this-paper');
  const href = link.getAttribute('href') || '';
  const path = href.split(/[?#]/, 1)[0].toLowerCase();
  const format = path.endsWith('.bib') ? 'bibtex'
    : path.endsWith('.ris') ? 'ris'
    : path.endsWith('.csl.json') ? 'csl_json' : null;
  if (format) {
    trackCitationEvent('citation_export', { citation_format: format }, section);
  } else if (href.startsWith('https://doi.org/')) {
    trackCitationEvent('citation_doi_click', {}, section);
  }
});

document.querySelectorAll('[data-copy-citation]').forEach((button) => {
  if (!navigator.clipboard || !navigator.clipboard.writeText) return;
  button.hidden = false;
  button.addEventListener('click', async () => {
    const source = document.getElementById(button.dataset.copyCitation);
    if (!source) return;
    try {
      await navigator.clipboard.writeText(source.textContent.trim());
      const section = button.closest('#cite-this-paper');
      if (section) trackCitationEvent('citation_copy', {}, section);
      button.textContent = 'Copied';
      window.setTimeout(() => { button.textContent = 'Copy citation'; }, 2000);
    } catch (_) {
      button.textContent = 'Copy unavailable';
      window.setTimeout(() => { button.textContent = 'Copy citation'; }, 2000);
    }
  });
});
