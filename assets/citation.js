const doiPrefix = 'https://doi.org/';

function citationDoiHref(section) {
  return section.querySelector(`a[href^="${doiPrefix}"]`)?.getAttribute('href') || '';
}

function trackCitationEvent(name, details, doiHref) {
  if (typeof window.gtag !== 'function') return;
  const metadata = { paper_path: window.location.pathname };
  if (doiHref) metadata.paper_doi = doiHref.slice(doiPrefix.length);
  try {
    window.gtag('event', name, { ...metadata, ...details });
  } catch (_) {
    // Analytics must never interfere with citation actions.
  }
}

document.addEventListener('click', (event) => {
  const link = event.target.closest?.('a[href]');
  if (!link) return;
  const citationSection = link.closest('#cite-this-paper');
  const section = citationSection || (link.closest('main .hero .links') && document.getElementById('cite-this-paper'));
  if (!section) return;
  const href = link.getAttribute('href') || '';
  const doiHref = citationDoiHref(section);
  if (href && href === doiHref) {
    trackCitationEvent('citation_doi_click', {}, doiHref);
    return;
  }
  if (!citationSection) return;
  const path = href.split(/[?#]/, 1)[0].toLowerCase();
  const format = path.endsWith('.bib') ? 'bibtex'
    : path.endsWith('.ris') ? 'ris'
    : path.endsWith('.csl.json') ? 'csl_json' : null;
  if (format) {
    trackCitationEvent('citation_export', { citation_format: format }, doiHref);
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
      if (section) trackCitationEvent('citation_copy', {}, citationDoiHref(section));
      button.textContent = 'Copied';
      window.setTimeout(() => { button.textContent = 'Copy citation'; }, 2000);
    } catch (_) {
      button.textContent = 'Copy unavailable';
      window.setTimeout(() => { button.textContent = 'Copy citation'; }, 2000);
    }
  });
});
