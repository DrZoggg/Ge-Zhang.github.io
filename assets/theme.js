/* Shared reading controls. No graphics dependency and no network requests. */
(() => {
  'use strict';
  if (window.__siteThemeMounted) return;
  window.__siteThemeMounted = true;
  const root = document.documentElement;
  const policy = window.SiteTheme;
  if (!policy) return;
  const controls = Array.from(document.querySelectorAll('[data-theme-toggle]'));
  let transitionFrame = 0;
  function apply(theme, persist = false) {
    if (theme !== 'dark' && theme !== 'light') return;
    const changed = root.dataset.theme !== theme;
    if (changed) {
      cancelAnimationFrame(transitionFrame);
      root.classList.add('theme-switching');
    }
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
    policy.theme = theme;
    const browserColor = document.querySelector('meta[name="theme-color"]');
    if (browserColor) browserColor.content = policy.colors[theme];
    if (persist) {
      try { localStorage.setItem(policy.key, theme); } catch (_) { /* Session-only choice. */ }
    }
    const next = theme === 'dark' ? 'light' : 'dark';
    controls.forEach(button => {
      button.hidden = false;
      button.setAttribute('aria-label', 'Switch to ' + next + ' theme');
      button.title = 'Switch to ' + next + ' theme';
      const label = button.querySelector('[data-theme-label]');
      if (label) label.textContent = next === 'light' ? 'Light' : 'Dark';
      button.dataset.activeTheme = theme;
    });
    if (changed) {
      document.dispatchEvent(new CustomEvent('site-theme-change', {detail: {theme}}));
      // Change paired foreground/background colors together, then restore hover feedback.
      transitionFrame = requestAnimationFrame(() => {
        transitionFrame = requestAnimationFrame(() => root.classList.remove('theme-switching'));
      });
    }
  }
  controls.forEach(button => button.addEventListener('click', () => {
    apply(root.dataset.theme === 'dark' ? 'light' : 'dark', true);
  }));
  window.addEventListener('storage', event => {
    if (event.key === policy.key) apply(event.newValue || policy.defaultTheme);
  });
  window.addEventListener('pageshow', event => {
    if (!event.persisted) return;
    try { apply(localStorage.getItem(policy.key) || policy.defaultTheme); } catch (_) { /* Keep session. */ }
  });
  apply(policy.theme);
})();
