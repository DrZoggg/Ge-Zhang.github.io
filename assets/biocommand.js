/* Luminous Lab progressive decoration. Scientific content is never hidden or loaded here. */
(() => {
  'use strict';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const pointer = matchMedia('(min-width: 768px) and (hover: hover) and (pointer: fine)');
  const scene = document.querySelector('.bio-scene');
  const control = document.querySelector('.motion-toggle');
  const animations = [], ambient = [];
  let paused = false, visible = true, bounds;
  const animate = (element, frames, options, loop = false) => {
    if (!element || !element.animate) return;
    const animation = element.animate(frames, {easing: 'cubic-bezier(.2,.65,.3,1)', ...options});
    animations.push(animation);
    if (loop) ambient.push(animation);
  };
  function sync() {
    ambient.forEach(a => (paused || !visible || document.hidden || reduce.matches) ? a.pause() : a.play());
  }
  function resetPointer() {
    if (!scene) return;
    scene.style.removeProperty('--parallax-x');
    scene.style.removeProperty('--parallax-y');
  }
  function start() {
    animations.splice(0).forEach(a => a.cancel());
    ambient.length = 0;
    resetPointer();
    if (control) control.hidden = reduce.matches || !scene || !scene.animate;
    if (reduce.matches || !scene || !scene.animate) return;
    const art = scene.querySelector('img');
    animate(art, [{opacity: .75}, {opacity: 1}], {duration: 1100});
    animate(document.querySelector('.home h1'), [{opacity: .85, transform: 'translateY(8px)'}, {opacity: 1, transform: 'none'}], {duration: 850, delay: 80});
    animate(document.querySelector('.bio-entry'), [{opacity: .9, transform: 'translateY(4px)'}, {opacity: 1, transform: 'none'}], {duration: 700, delay: 320});
    if (pointer.matches) {
      animate(scene.querySelector('.optical-sheen'), [{opacity: .2, transform: 'translateX(-3%)'}, {opacity: .7, transform: 'translateX(3%)'}], {duration: 28000, iterations: Infinity, direction: 'alternate'}, true);
    }
    animate(art, [{transform: 'translateY(0)'}, {transform: 'translateY(7px)'}], {duration: 24000, iterations: Infinity, direction: 'alternate'}, true);
    if (paused) animations.filter(a => !ambient.includes(a)).forEach(a => a.finish());
    sync();
  }
  if (scene) {
    const frame = scene.closest('.bio-visual');
    frame.addEventListener('pointerenter', () => { bounds = frame.getBoundingClientRect(); });
    frame.addEventListener('pointermove', event => {
      if (!pointer.matches || reduce.matches || paused || !bounds) return;
      const clamp = value => Math.max(-8, Math.min(8, value));
      scene.style.setProperty('--parallax-x', clamp(((event.clientX - bounds.left) / bounds.width - .5) * 16) + 'px');
      scene.style.setProperty('--parallax-y', clamp(((event.clientY - bounds.top) / bounds.height - .5) * 16) + 'px');
    }, {passive: true});
    frame.addEventListener('pointerleave', resetPointer);
    if ('IntersectionObserver' in window) new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      sync();
    }).observe(frame);
  }
  if (control) control.addEventListener('click', () => {
    paused = !paused;
    control.setAttribute('aria-pressed', String(paused));
    control.textContent = paused ? 'Resume motion' : 'Pause motion';
    if (paused) { animations.filter(a => !ambient.includes(a)).forEach(a => a.finish()); resetPointer(); }
    sync();
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      if (!reduce.matches) animate(entry.target, [{opacity: .86}, {opacity: 1}], {duration: 450});
      observer.unobserve(entry.target);
    }), {threshold: .12});
    document.querySelectorAll('.home #featured .paper,.publications .year-group').forEach(e => observer.observe(e));
  }
  reduce.addEventListener('change', start);
  pointer.addEventListener('change', start);
  document.addEventListener('visibilitychange', sync);
  window.addEventListener('pagehide', () => { animations.forEach(a => a.cancel()); resetPointer(); });
  window.addEventListener('pageshow', event => { if (event.persisted) start(); });
  start();
})();
