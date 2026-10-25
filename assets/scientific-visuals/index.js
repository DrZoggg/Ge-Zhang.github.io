/* Homepage-only, progressive WebGL enhancement. No runtime network dependencies. */
let mounted = null;

export async function mountScientificVisuals() {
  if (mounted) return mounted;
  const hosts = ['observatory-wheel', 'research-field'].map(id => document.getElementById(id)).filter(Boolean);
  if (!hosts.length) return null;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const compact = matchMedia('(max-width: 700px), (pointer: coarse)');
  const connection = navigator.connection;
  let disposed = false, raf = 0, lastTick = 0, pageActive = true, imported = null;
  let theme = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
  const removers = [], entries = [];
  function listen(target, type, fn, options) {
    target?.addEventListener?.(type, fn, options);
    removers.push(() => target?.removeEventListener?.(type, fn, options));
  }
  const staticPreference = () => reduced.matches || Boolean(connection?.saveData);
  const inView = host => { const r = host.getBoundingClientRect(); return r.width>0 && r.height>0 && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth; };
  const canRun = e => !disposed && pageActive && !document.hidden && e.visible && !e.paused && !e.lost && !e.failed && !e.degraded && !staticPreference() && Boolean(e.renderer);
  function syncButton(e) {
    if (!e.button) return;
    e.button.hidden = !e.renderer || e.failed || e.degraded || staticPreference();
    e.button.disabled = e.lost;
    e.button.setAttribute('aria-pressed', String(e.paused));
    e.button.textContent = e.paused ? 'Resume animation' : 'Pause animation';
    e.button.setAttribute('aria-label', `${e.paused ? 'Resume' : 'Pause'} ${e.id === 'observatory-wheel' ? 'orbital instrument' : 'research field'} animation`);
  }
  function showPoster(e, state) {
    e.host.dataset.sceneState = state;
    if (e.poster) e.poster.style.visibility = '';
    if (e.canvas) e.canvas.style.visibility = 'hidden';
    syncButton(e);
  }
  function draw(e, animationStamp = 0) {
    if (!e.renderer || e.lost || e.failed || e.degraded || staticPreference()) return;
    const start = performance.now();
    try {
      e.scene.update(e.time); e.renderer.render(e.scene.scene, e.scene.camera);
      e.frames++; e.dirty = false; e.renderMs = performance.now() - start;
      e.renderAverage = e.renderAverage ? e.renderAverage * .95 + e.renderMs * .05 : e.renderMs;
      // Measure actual submitted-frame spacing, not the raw monitor RAF rate.
      // Inactive/resume boundaries clear frameStamp, so they never count as slow frames.
      if(animationStamp && e.frameStamp){
        e.frameIntervalMs=animationStamp-e.frameStamp;
        e.frameIntervalAverage=e.intervalSamples?e.frameIntervalAverage*.95+e.frameIntervalMs*.05:e.frameIntervalMs;
        e.intervalSamples++;
      }
      if(animationStamp)e.frameStamp=animationStamp;
      if (e.canvas.style.visibility !== 'visible') {
        e.canvas.style.visibility = 'visible';
        if (e.poster) e.poster.style.visibility = 'hidden';
      }
      e.host.dataset.sceneState = e.paused ? 'paused' : 'ready';
      // Either sustained actual frame spacing or CPU submission cost can lower
      // quality. A 240 Hz RAF does not become a fictitious 240 fps renderer metric.
      const slowFrames=e.intervalSamples>100 && e.frameIntervalAverage>(compact.matches?46:25);
      if (e.frames > 100 && (slowFrames || e.renderAverage > (compact.matches ? 20 : 15)) && e.quality !== 'low') {
        e.quality = 'low'; e.lowSince=e.frames; e.intervalSamples=0; e.frameIntervalAverage=0; resizeEntry(e);
      }
      if(e.quality==='low' && e.frames-e.lowSince>180 && (e.renderAverage>35 || (e.intervalSamples>100 && e.frameIntervalAverage>85))){e.degraded=true;showPoster(e,'low-performance');}
    } catch (error) { e.failed = true; e.error = error.message; showPoster(e, 'fallback'); }
    syncButton(e);
  }
  function tick(stamp) {
    raf = 0;
    if (disposed) return;
    const dt = lastTick ? Math.min((stamp - lastTick) / 1000, .06) : 0;
    lastTick = stamp;
    let again = false;
    for (const e of entries) {
      const active = canRun(e);
      if(!active || !e.wasActive)e.frameStamp=0;
      e.wasActive=active;
      if (active) {
        e.time += dt;
        const interval = compact.matches || e.quality === 'low' ? 1000 / 30 : 1000 / 60;
        if (stamp - e.lastDraw >= interval - 1) { draw(e, stamp); e.lastDraw = stamp; }
        again = true;
      } else if (e.dirty && e.visible && pageActive && !document.hidden) draw(e);
    }
    if (again) raf = requestAnimationFrame(tick); else lastTick = 0;
  }
  function schedule() {
    if (disposed || raf) return;
    if (entries.some(e => canRun(e) || (e.dirty && e.visible && e.renderer && !e.failed && !e.degraded && !e.lost && !staticPreference() && pageActive && !document.hidden))) raf = requestAnimationFrame(tick);
  }
  function resizeEntry(e) {
    if (!e.renderer) return;
    const w = e.host.clientWidth, h = e.host.clientHeight;
    if (!w || !h) return;
    e.dpr = Math.min(devicePixelRatio || 1, e.quality === 'low' ? 1 : compact.matches ? 1.25 : 1.6);
    e.renderer.setPixelRatio(e.dpr); e.renderer.setSize(w, h, false);
    e.scene.resize(w, h); e.scene.setQuality(e.quality, e.dpr); e.dirty = true;
  }
  async function initialize(e) {
    if (e.renderer || e.loading || e.failed || disposed || staticPreference() || !e.host.clientWidth || !e.host.clientHeight) return;
    e.loading = true;
    try {
      imported ||= import('./scenes.js');
      const {createWheel, createField, createRenderer} = await imported;
      if (disposed || staticPreference() || !e.host.clientWidth || !e.host.clientHeight) return;
      const canvas = document.createElement('canvas');
      canvas.className = 'scientific-canvas'; canvas.setAttribute('aria-hidden', 'true');
      canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;visibility:hidden;';
      e.canvas = canvas;
      e.renderer = createRenderer(canvas);
      e.scene = e.id === 'observatory-wheel' ? createWheel() : createField();
      e.scene.setTheme(theme); e.host.append(canvas);
      listen(canvas, 'webglcontextlost', event => { event.preventDefault(); e.lost = true; showPoster(e, 'context-lost'); });
      listen(canvas, 'webglcontextrestored', () => { e.lost = false; e.dirty = true; resizeEntry(e); schedule(); });
      resizeEntry(e); syncButton(e); schedule();
    } catch (error) {
      e.failed = true; e.error = error.message;
      e.scene?.dispose(); e.renderer?.forceContextLoss(); e.renderer?.dispose(); e.canvas?.remove(); e.renderer = null;
      showPoster(e, 'fallback');
    } finally { e.loading = false; }
  }
  hosts.forEach(host => {
    const e = { host, id: host.id, poster: host.querySelector('[data-scene-poster]'),
      button: document.querySelector(`[data-scene-pause="${host.id}"]`), visible: inView(host),
      renderer: null, scene: null, canvas: null, loading: false, failed: false, lost: false,
      paused: false, dirty: true, time: 0, frames: 0, lastDraw: 0, renderMs: 0, renderAverage: 0,
      frameStamp:0, wasActive:false, frameIntervalMs:0, frameIntervalAverage:0, intervalSamples:0, lowSince:0, quality: 'high', dpr: 1 };
    entries.push(e); showPoster(e, staticPreference() ? 'static-preference' : 'poster');
    if (e.button) listen(e.button, 'click', () => { e.paused = !e.paused; e.dirty = true; syncButton(e); schedule(); });
  });
  const observer = typeof IntersectionObserver === 'function' ? new IntersectionObserver(records => {
    records.forEach(record => { const e = entries.find(x => x.host === record.target); e.visible = record.isIntersecting && record.boundingClientRect.width>0 && record.boundingClientRect.height>0; if (e.visible) initialize(e); }); schedule();
  }, { threshold: 0 }) : null;
  entries.forEach(e => { observer?.observe(e.host); if (e.visible || !observer) initialize(e); });
  const resizeObserver = typeof ResizeObserver === 'function' ? new ResizeObserver(records => {
    records.forEach(record => { const e = entries.find(x => x.host === record.target); if (e) resizeEntry(e); }); schedule();
  }) : null;
  entries.forEach(e => resizeObserver?.observe(e.host));
  if (!resizeObserver) listen(window, 'resize', () => { entries.forEach(resizeEntry); schedule(); });
  if (!observer) listen(window, 'scroll', () => { entries.forEach(e => { e.visible = inView(e.host); if (e.visible) initialize(e); }); schedule(); }, { passive: true });
  listen(document, 'site-theme-change', event => {
    theme = event.detail?.theme === 'light' ? 'light' : 'dark';
    entries.forEach(e => { e.scene?.setTheme(theme); e.dirty = true; }); schedule();
  });
  listen(document, 'visibilitychange', () => { lastTick = 0; entries.forEach(e=>{e.frameStamp=0;e.wasActive=false;}); if (document.hidden && raf) { cancelAnimationFrame(raf); raf = 0; } else schedule(); });
  listen(window, 'pagehide', event => { pageActive = false; if (raf) cancelAnimationFrame(raf); raf = 0; lastTick = 0; entries.forEach(e=>{e.frameStamp=0;e.wasActive=false;}); if (!event.persisted) api.dispose(); });
  listen(window, 'pageshow', () => { pageActive = true; lastTick = 0; schedule(); });
  function preferencesChanged() {
    entries.forEach(e => { if (staticPreference()) showPoster(e, 'static-preference'); else { e.dirty = true; initialize(e); } syncButton(e); });
    if (staticPreference() && raf) { cancelAnimationFrame(raf); raf = 0; lastTick = 0; } schedule();
  }
  listen(reduced, 'change', preferencesChanged); listen(connection, 'change', preferencesChanged);
  listen(compact, 'change', () => { entries.forEach(resizeEntry); schedule(); });
  const api = {
    metrics() { return { disposed, theme, schedulerPending: Boolean(raf), rendererCount: entries.filter(e => e.renderer).length,
      scenes: entries.map(e => ({ id: e.id, state: e.host.dataset.sceneState, visible: e.visible, paused: e.paused, running: canRun(e), frames: e.frames, time: e.time, quality: e.quality, dpr: e.dpr, cpuSubmitMs:e.renderMs, cpuSubmitAverageMs:e.renderAverage, actualFrameIntervalMs:e.frameIntervalMs, actualFrameIntervalAverageMs:e.frameIntervalAverage, measuredFrameSamples:e.intervalSamples, error: e.error || null, geometries: e.renderer?.info.memory.geometries || 0, textures: e.renderer?.info.memory.textures || 0, drawCalls: e.renderer?.info.render.calls || 0 })) }; },
    setPaused(id, paused) { const e = entries.find(x => x.id === id); if (e) { e.paused = Boolean(paused); e.dirty = true; syncButton(e); schedule(); } },
    // Deterministic captures only. No URL/query parameters, no data or tracking.
    setTimeForTesting(seconds) { entries.forEach(e => { e.time = Math.max(0, Number(seconds) || 0); e.dirty = true; }); schedule(); },
    dispose() {
      if (disposed) return; disposed = true; cancelAnimationFrame(raf); raf = 0;
      observer?.disconnect(); resizeObserver?.disconnect(); removers.forEach(remove => remove());
      entries.forEach(e => { e.scene?.dispose(); e.renderer?.forceContextLoss(); e.renderer?.dispose(); e.canvas?.remove(); e.renderer = null; e.scene = null; showPoster(e, 'disposed'); });
      mounted = null; if (window.__scientificVisuals === api) delete window.__scientificVisuals;
    },
  };
  mounted = api; window.__scientificVisuals = api;
  return api;
}
