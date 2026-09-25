document.querySelectorAll('[data-copy-citation]').forEach((button) => {
  if (!navigator.clipboard || !navigator.clipboard.writeText) return;
  button.hidden = false;
  button.addEventListener('click', async () => {
    const source = document.getElementById(button.dataset.copyCitation);
    if (!source) return;
    try {
      await navigator.clipboard.writeText(source.textContent.trim());
      button.textContent = 'Copied';
      window.setTimeout(() => { button.textContent = 'Copy citation'; }, 2000);
    } catch (_) {
      button.textContent = 'Copy unavailable';
      window.setTimeout(() => { button.textContent = 'Copy citation'; }, 2000);
    }
  });
});
