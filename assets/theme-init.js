/* First-paint theme policy. The single default is dark; explicit choices persist. */
(() => {
  'use strict';
  const key = 'ge-zhang-theme';
  const defaultTheme = 'dark';
  let theme = defaultTheme;
  try {
    const saved = localStorage.getItem(key);
    if (saved === 'light' || saved === 'dark') theme = saved;
  } catch (_) { /* Storage restrictions do not prevent reading or switching. */ }
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  const colors = {dark: '#071419', light: '#f3f6f8'};
  const browserColor = document.createElement('meta');
  browserColor.name = 'theme-color';
  browserColor.content = colors[theme];
  document.head.appendChild(browserColor);
  window.SiteTheme = {key, defaultTheme, theme, colors};
})();
