/* Homepage lifecycle for the pinned React Bits WebGL2 core. See NOTICE.md. */
import { createGradientWavesRenderer } from './core.js';

let mounted = null;
export const WAVE_THEMES = Object.freeze({
  dark: Object.freeze({horizonColor:'#5227FF', waveColor:'#FF9FFC', crestColor:'#FFFFFF', backgroundColor:'#090e21', lightMode:false, speed:.4, amplitude:2.5, waveScale:.6, waveRatio:.9, swell:35, turbulence:20, tilt:64, zoom:1, height:5.5, fogDepth:15, relief:1, lightAngle:120, sheen:.12, brightness:1, opacity:1, grain:.015, intro:true, mouseInteraction:true, parallaxStrength:.5, mouseStrength:.6, swellOnClick:true}),
  light: Object.freeze({horizonColor:'#2563a6', waveColor:'#43a7c3', crestColor:'#d9eeff', backgroundColor:'#edf3f8', lightMode:true, speed:.4, amplitude:2.5, waveScale:.6, waveRatio:.9, swell:35, turbulence:20, tilt:64, zoom:1, height:5.5, fogDepth:18, relief:1, lightAngle:140, sheen:.3, brightness:1.3, opacity:1, grain:.01, intro:true, mouseInteraction:true, parallaxStrength:.5, mouseStrength:.6, swellOnClick:true}),
});

export function mountGradientWaves() {
  if (mounted) return mounted;
  const host = document.querySelector('[data-gradient-waves], #gradient-waves');
  if (!host) return null;
  const hero = host.closest('.hero') || host;
  const button = document.querySelector('[data-wave-pause]');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const compact = matchMedia('(max-width: 700px), (pointer: coarse)');
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
  const connection = navigator.connection;
  const removers = [];
  let renderer = null, rendererEvents = null, disposed = false, failed = false, lost = false, degraded = false;
  let paused = false, running = false, pageActive = true, raf = 0, lastTick = 0, lastDraw = 0;
  let theme = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
  let quality = compact.matches ? 'low' : 'medium', dpr = 1, qualityReduced = false;
  let frames = 0, samples = 0, frameAverage = 0, frameStamp = 0, renderAverage = 0, lowAt = 0;
  let pointerUpdates = 0, swellRequests = 0, error = null;
  const inView = () => {const r=host.getBoundingClientRect();return r.width>0 && r.height>0 && r.bottom>0 && r.top<innerHeight && r.right>0 && r.left<innerWidth;};
  let visible = inView();
  const staticPreference = () => reduced.matches || Boolean(connection?.saveData);
  const canRun = () => !disposed && !failed && !lost && !degraded && !paused && visible && pageActive && !document.hidden && !staticPreference() && Boolean(renderer);
  function listen(target, type, fn, options) {
    target?.addEventListener?.(type, fn, options);
    removers.push(() => target?.removeEventListener?.(type, fn, options));
  }
  function budget(active) {
    if (running === active) return;
    running = active;
    document.dispatchEvent(new CustomEvent('hero-render-budget-change', {detail:{active}}));
  }
  function syncButton() {
    if (!button) return;
    button.hidden = !renderer || failed || degraded || staticPreference();
    button.disabled = lost;
    button.setAttribute('aria-pressed', String(paused));
    const label = `${paused ? 'Resume' : 'Pause'} wave animation`;
    button.setAttribute('aria-label', label); button.title = label;
  }
  function state(value) {host.dataset.waveState=value;syncButton();}
  function stop() {cancelAnimationFrame(raf);raf=0;lastTick=0;frameStamp=0;budget(false);}
  function poster(reason) {stop();state(reason);}
  function fit() {
    if (!renderer || lost || disposed) return;
    const width=host.clientWidth, height=host.clientHeight;
    if (!width || !height) return;
    // Bound both DPR and total fragment workload. The original ray marcher stays intact.
    const cap=qualityReduced ? .9 : compact.matches ? 1.25 : 1.5;
    const pixelBudget=qualityReduced ? 1050000 : compact.matches ? 950000 : 2200000;
    dpr=Math.max(.65,Math.min(devicePixelRatio||1,cap,Math.sqrt(pixelBudget/(width*height))));
    renderer.resize(width,height,dpr);
  }
  function releaseRenderer() {
    rendererEvents?.abort();rendererEvents=null;
    const previous=renderer;renderer=null;previous?.dispose();
  }
  function fail(reason) {failed=true;error=String(reason?.message||reason);releaseRenderer();poster('fallback');}
  function draw(dt, freeze=false) {
    if (!renderer || lost || failed || degraded || staticPreference() || !visible || !pageActive || document.hidden) return;
    const singleFrameBudget=!running;
    if(singleFrameBudget)budget(true);
    const start=performance.now();
    try {
      renderer.render(dt,{reduced:false,freeze});
      const cost=performance.now()-start;
      renderAverage=renderAverage ? renderAverage*.95+cost*.05 : cost;
      frames++;state(paused?'paused':'ready');
    } catch (failure) {fail(failure);}
    finally {if(singleFrameBudget)budget(false);}
  }
  function tick(stamp) {
    raf=0;
    if (!canRun()) {stop();return;}
    budget(true);
    const dt=lastTick ? Math.min((stamp-lastTick)/1000,.08) : 0;
    lastTick=stamp;
    const interval=compact.matches||qualityReduced ? 1000/30 : 1000/60;
    if (stamp-lastDraw >= interval-1) {
      if (frameStamp) {
        const spacing=stamp-frameStamp;
        // Background-window throttling and suspended compositor gaps are not GPU timings.
        // Start a fresh cadence window after a scheduling discontinuity.
        if (spacing>250) {samples=0;frameAverage=0;}
        else {frameAverage=samples?frameAverage*.96+spacing*.04:spacing;samples++;}
      }
      frameStamp=stamp;
      // Accumulate skipped RAF time, preserving the upstream speed at 30/60 fps.
      const elapsed=lastDraw ? Math.min((stamp-lastDraw)/1000,.1) : dt;
      lastDraw=stamp;draw(elapsed);
      if (!qualityReduced && samples>120 && (frameAverage>(compact.matches?65:37)||renderAverage>28)) {
        qualityReduced=true;quality='low';lowAt=frames;samples=0;frameAverage=0;
        renderer?.setOptions({quality});fit();
      } else if (qualityReduced && frames-lowAt>150 && samples>100 && (frameAverage>110||renderAverage>75)) {
        degraded=true;releaseRenderer();poster('low-performance');return;
      }
    }
    if (canRun()) raf=requestAnimationFrame(tick);else stop();
  }
  function schedule() {
    if (!canRun()) {stop();return;}
    budget(true);
    if (!raf) {lastTick=0;lastDraw=0;raf=requestAnimationFrame(tick);}
  }
  function initialize() {
    if (renderer || disposed || failed || degraded || staticPreference() || !visible || !host.clientWidth || !host.clientHeight) return;
    try {
      renderer=createGradientWavesRenderer(host,{...WAVE_THEMES[theme],quality});
      const canvas=renderer.canvas;
      const ownRenderer=renderer;
      rendererEvents=new AbortController();
      canvas.classList.add('gradient-waves-canvas');canvas.setAttribute('aria-hidden','true');
      canvas.addEventListener('webglcontextlost',event=>{if(renderer!==ownRenderer||disposed)return;event.preventDefault();lost=true;poster('context-lost');},{signal:rendererEvents.signal});
      canvas.addEventListener('webglcontextrestored',()=>{
        if (disposed||renderer!==ownRenderer) return;
        releaseRenderer();lost=false;initialize();schedule();
      },{signal:rendererEvents.signal});
      fit();syncButton();schedule();
    } catch (failure) {fail(failure);}
  }
  function local(event) {
    const r=host.getBoundingClientRect();
    return {x:(event.clientX-r.left)/Math.max(r.width,1),y:(event.clientY-r.top)/Math.max(r.height,1)};
  }
  listen(hero,'pointermove',event=>{
    if (!canRun() || !finePointer.matches || event.pointerType==='touch') return;
    const p=local(event);renderer.setPointer(p.x,p.y,true);pointerUpdates++;
  },{passive:true});
  listen(hero,'pointerleave',()=>renderer?.setPointer(.5,.5,false),{passive:true});
  // Passive click: scrolling and all native controls remain in charge of input.
  listen(hero,'click',event=>{
    if (!canRun() || !event.detail || event.button!==0 || event.target.closest('a,button,input,textarea,select,label,summary,[role="button"]')) return;
    const p=local(event);if(p.x<0||p.x>1||p.y<0||p.y>1)return;
    if(renderer.addSwell(p.x,p.y))swellRequests++;
  },{passive:true});
  listen(button,'click',()=>{paused=!paused;if(paused){stop();state('paused');}else schedule();syncButton();});
  listen(document,'site-theme-change',event=>{
    theme=event.detail?.theme==='light'?'light':'dark';
    renderer?.setOptions({...WAVE_THEMES[theme],quality});
    if (renderer && !lost && !failed && !staticPreference()) draw(0,true);
    schedule();
  });
  listen(document,'visibilitychange',()=>{if(document.hidden)stop();else{visible=inView();initialize();schedule();}});
  listen(window,'pagehide',event=>{pageActive=false;stop();if(!event.persisted)api.dispose();});
  listen(window,'pageshow',()=>{pageActive=true;visible=inView();initialize();schedule();});
  const preferences=()=>{
    if(staticPreference())poster('static-preference');
    else{visible=inView();initialize();if(renderer&&visible)draw(0,true);schedule();}
    syncButton();
  };
  listen(reduced,'change',preferences);listen(connection,'change',preferences);
  listen(compact,'change',()=>{fit();schedule();});
  const observer=typeof IntersectionObserver==='function'?new IntersectionObserver(records=>{
    // Edge adjacency counts as isIntersecting even with zero visible pixels.
    // Require positive intersection area so an exact section-anchor scroll stops GPU work.
    visible=records.some(record=>record.isIntersecting && (record.intersectionRect
      ? record.intersectionRect.width>0 && record.intersectionRect.height>0 : inView()));
    if(visible)initialize();schedule();
  },{threshold:0}):null;
  observer?.observe(host);
  if(!observer)listen(window,'scroll',()=>{visible=inView();if(visible)initialize();schedule();},{passive:true});
  const sizes=typeof ResizeObserver==='function'?new ResizeObserver(()=>{fit();if(paused&&visible)draw(0,true);schedule();}):null;
  sizes?.observe(host);
  if(!sizes)listen(window,'resize',()=>{fit();schedule();});
  const api={
    metrics(){return {theme,running,visible,paused,disposed,failed,lost,degraded,frames,quality,dpr,rendererCount:renderer?1:0,schedulerPending:Boolean(raf),frameIntervalAverageMs:frameAverage,measuredFrameSamples:samples,cpuSubmitAverageMs:renderAverage,pointerUpdates,swellRequests,error,core:renderer?.getState()||null};},
    setPaused(next){paused=Boolean(next);if(paused){stop();state('paused');}else schedule();syncButton();},
    setTimeForTesting(seconds){renderer?.setTime?.(seconds);if(renderer&&!lost)draw(0,true);},
    dispose(){if(disposed)return;disposed=true;stop();observer?.disconnect();sizes?.disconnect();removers.forEach(remove=>remove());releaseRenderer();state('disposed');mounted=null;if(window.__gradientWaves===api)delete window.__gradientWaves;},
  };
  mounted=api;window.__gradientWaves=api;
  state(staticPreference()?'static-preference':'poster');initialize();
  return api;
}
