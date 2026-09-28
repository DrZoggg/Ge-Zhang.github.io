/* Evidence operations are interaction signals, never proof of academic citation. */
(function () {
  'use strict';
  function track(name, doi, extra) {
    if (typeof window.gtag !== 'function') return;
    try { window.gtag('event', name, {paper_doi: doi, paper_path: window.location.pathname, ...extra}); }
    catch (_) { /* Analytics cannot interfere with evidence actions. */ }
  }
  document.querySelectorAll('[data-copy-evidence]').forEach(button => {
    const source = document.getElementById(button.dataset.copyEvidence);
    let payload;
    try { payload = JSON.parse(source.textContent); } catch (_) { return; }
    const controls = button.closest('.evidence-actions');
    const status = controls.querySelector('.evidence-copy-status');
    const fallback = controls.querySelector('textarea');
    button.hidden = false;
    button.addEventListener('click', async () => {
      button.disabled = true;
      status.textContent = '';
      fallback.hidden = true;
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw Error('Clipboard unavailable');
        await navigator.clipboard.writeText(payload.text);
        status.textContent = 'Copied';
        track('evidence_copy', payload.doi, {});
      } catch (_) {
        status.textContent = 'Automatic copy unavailable. Select and copy the complete text below.';
        fallback.value = payload.text;
        fallback.hidden = false;
        fallback.focus(); fallback.select();
      } finally { button.disabled = false; }
    });
  });
  document.querySelectorAll('a[data-evidence-export]').forEach(link => {
    link.addEventListener('click', () => {
      track('evidence_export', link.dataset.evidenceExport, {citation_format: 'evidence_csv'});
    });
  });
})();
