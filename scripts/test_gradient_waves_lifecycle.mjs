/**
 * Node mock unit tests for the homepage lifecycle, not GPU/browser acceptance.
 * Run: node scripts/test_gradient_waves_lifecycle.mjs
 * The real entry source is imported from an in-memory data URL with only its
 * core import replaced. No browser, CDP, screenshots, network or packages.
 */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('../assets/gradient-waves/index.js', import.meta.url), 'utf8');
const coreImport = "import { createGradientWavesRenderer } from './core.js';";
assert.equal(source.split(coreImport).length, 2, 'replace precisely the core import');
const mockSource = source.replace(coreImport,
  'const {createGradientWavesRenderer} = globalThis.__gradientWavesLifecycleMockCore;');
let moduleSequence = 0;
const NativeEvent = globalThis.Event;
const NativeEventTarget = globalThis.EventTarget;

class Target extends NativeEventTarget {
  constructor(fixture) {
    super(); this.listeners = new Map(); this.fixture = fixture;
    fixture.targets.push(this);
  }
  addEventListener(type, listener, options) {
    super.addEventListener(type, listener, options);
    if (options?.signal?.aborted) return;
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type).add(listener);
    options?.signal?.addEventListener('abort', () => this.listeners.get(type)?.delete(listener), {once:true});
  }
  removeEventListener(type, listener, options) {
    super.removeEventListener(type, listener, options);
    this.listeners.get(type)?.delete(listener);
  }
  get listenerCount() { return [...this.listeners.values()].reduce((sum, set) => sum + set.size, 0); }
}

class Element extends Target {
  constructor(fixture) {
    super(fixture); this.attrs = {}; this.dataset = {}; this.style = {};
    this.children = []; this.hidden = false; this.removed = false;
    this.classList = {add() {}};
  }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  appendChild(child) { this.children.push(child); child.parent = this; }
  remove() {
    this.removed = true;
    if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this);
  }
  closest() { return null; }
}

function fixture({hostExists=true, visible=true, reduced=false, saveData=false, compact=false,
  width=1600, height=700, deviceDpr=2, createFailure=false, withObservers=true}={}) {
  const f = {targets:[], renderers:[], events:[], raf:new Map(), nextRaf:1, cpu:0,
    stamp:0, renderCost:1, visible, createFailure, renderFailure:false,
    width, height, reduced, saveData, compact, restored:false};
  f.window = new Target(f); f.document = new Target(f);
  f.root = new Element(f); f.root.dataset.theme = 'dark';
  f.document.documentElement = f.root; f.document.hidden = false;
  f.hero = new Element(f); f.host = new Element(f); f.button = new Element(f);
  f.host.clientWidth = width; f.host.clientHeight = height;
  f.host.closest = () => f.hero;
  f.host.getBoundingClientRect = () => ({width:f.host.clientWidth,height:f.host.clientHeight,
    left:0,right:f.host.clientWidth,top:f.visible?100:-height-100,bottom:f.visible?height+100:-100});
  f.document.querySelector = selector => selector.includes('gradient-waves')
    ? (hostExists?f.host:null) : selector === '[data-wave-pause]'?f.button:null;
  f.reducedQuery = new Target(f); f.reducedQuery.matches = reduced;
  f.compactQuery = new Target(f); f.compactQuery.matches = compact;
  f.fineQuery = new Target(f); f.fineQuery.matches = true;
  f.connection = new Target(f); f.connection.saveData = saveData;
  f.document.addEventListener('hero-render-budget-change', event => f.events.push(event.detail.active));
  const beforeListeners = new Map(f.targets.map(target => [target,target.listenerCount]));
  class IntersectionMock {
    constructor(callback) { this.callback=callback; this.disconnected=false; f.intersection=this; }
    observe() {}
    disconnect() { this.disconnected=true; }
    emit(overrides={}) {
      const bounds=f.host.getBoundingClientRect();
      this.callback([{target:f.host,isIntersecting:f.visible,boundingClientRect:bounds,
        intersectionRect:{width:f.visible?bounds.width:0,height:f.visible?bounds.height:0},...overrides}]);
    }
  }
  class ResizeMock {
    constructor(callback) { this.callback=callback; this.disconnected=false; f.resize=this; }
    observe() {}
    disconnect() { this.disconnected=true; }
    emit() { this.callback([]); }
  }
  const createGradientWavesRenderer = (host, options) => {
    if (f.createFailure) throw new Error('mock creation failure');
    const canvas = new Element(f); host.appendChild(canvas);
    const renderer = {canvas,options:{...options},renders:[],sizes:[],disposed:false,time:0,
      resize(w,h,dpr) { this.sizes.push({w,h,dpr}); },
      render(dt, options) {
        assert.equal(f.events.at(-1), true, 'every submitted frame owns the hero budget');
        if (f.renderFailure) throw new Error('mock render failure');
        this.renders.push({dt,...options}); f.cpu += f.renderCost;
      },
      setOptions(next) { Object.assign(this.options,next); },
      setPointer() {}, addSwell() { return true; }, setTime(value) { this.time=value; },
      getState() { return {disposed:this.disposed,frames:this.renders.length,time:this.time}; },
      dispose() {
        this.disposed=true; canvas.remove();
        // Model the old core's asynchronous loseContext event after disposal.
        queueMicrotask(() => canvas.dispatchEvent(new NativeEvent('webglcontextlost',{cancelable:true})));
      },
    };
    f.renderers.push(renderer); return renderer;
  };
  const globals = {
    window:f.window, document:f.document, navigator:{connection:f.connection},
    innerHeight:1000, innerWidth:2000, devicePixelRatio:deviceDpr,
    matchMedia:query => query.includes('reduced-motion')?f.reducedQuery
      : query.includes('coarse')?f.compactQuery:f.fineQuery,
    performance:{now:()=>f.cpu},
    requestAnimationFrame:callback => {const id=f.nextRaf++;f.raf.set(id,callback);return id;},
    cancelAnimationFrame:id=>f.raf.delete(id),
    IntersectionObserver:withObservers?IntersectionMock:undefined,
    ResizeObserver:withObservers?ResizeMock:undefined,
    CustomEvent:class extends NativeEvent {constructor(type,options){super(type);this.detail=options?.detail;}},
    __gradientWavesLifecycleMockCore:{createGradientWavesRenderer},
  };
  const descriptors = new Map(Object.keys(globals).map(key=>[key,Object.getOwnPropertyDescriptor(globalThis,key)]));
  for (const [key,value] of Object.entries(globals)) Object.defineProperty(globalThis,key,{value,writable:true,configurable:true});
  f.emit = (target,type,values={}) => {
    const event = new NativeEvent(type,{cancelable:true});
    for (const [key,value] of Object.entries(values)) Object.defineProperty(event,key,{value});
    target.dispatchEvent(event); return event;
  };
  f.step = (milliseconds=17) => {
    f.stamp += milliseconds;
    const callbacks=[...f.raf.values()]; f.raf.clear();
    for (const callback of callbacks) callback(f.stamp);
    assert.ok(f.raf.size<=1,'only one hero RAF may be pending');
  };
  f.setVisible = next => {
    f.visible=next;
    if(f.intersection) f.intersection.emit(); else f.emit(f.window,'scroll');
  };
  f.setReduced = next => {f.reducedQuery.matches=next;f.emit(f.reducedQuery,'change');};
  f.setSaveData = next => {f.connection.saveData=next;f.emit(f.connection,'change');};
  f.theme = theme => f.emit(f.document,'site-theme-change',{detail:{theme}});
  f.assertClean = () => {
    assert.equal(f.raf.size,0);
    assert.equal(f.window.__gradientWaves,undefined);
    for(const target of f.targets) assert.equal(target.listenerCount,beforeListeners.get(target)||0,'dispose removes its listeners');
    if(f.intersection) assert.equal(f.intersection.disconnected,true);
    if(f.resize) assert.equal(f.resize.disconnected,true);
    assert.ok(f.renderers.every(renderer=>renderer.disposed));
  };
  f.restore = () => {
    if(f.restored) return;
    f.api?.dispose();
    for(const [key,descriptor] of descriptors) {
      if(descriptor) Object.defineProperty(globalThis,key,descriptor); else delete globalThis[key];
    }
    f.restored=true;
  };
  return f;
}

async function load(f) {
  const url='data:text/javascript;base64,'+Buffer.from(mockSource).toString('base64')+'#case-'+(++moduleSequence);
  const module=await import(url);
  f.api=module.mountGradientWaves(); return module;
}

async function run(name, options, callback) {
  await test(name,async()=>{
    const f=fixture(options);
    try {const module=await load(f);await callback(f,module);}
    finally {f.restore();await Promise.resolve();}
  });
}

await run('no host produces no API, renderer, listeners or RAF',{hostExists:false},(f,module)=>{
  assert.equal(f.api,null);assert.equal(module.mountGradientWaves(),null);
  assert.equal(f.renderers.length,0);assert.equal(f.raf.size,0);assert.equal(f.window.__gradientWaves,undefined);
  assert.equal(f.targets.reduce((count,target)=>count+target.listenerCount,0),1,'only the fixture budget observer exists');
});

await run('duplicate mount is idempotent and publishes running metrics before its first frame',{},(f,module)=>{
  assert.equal(module.mountGradientWaves(),f.api);assert.equal(f.renderers.length,1);
  assert.equal(f.api.metrics().running,true);assert.equal(f.raf.size,1);
  assert.equal(f.renderers[0].canvas.attrs['aria-hidden'],'true');
  assert.equal(f.button.attrs['aria-label'],'Pause wave animation');
  f.step();assert.equal(f.api.metrics().frames,1);
});

await run('initially offscreen host defers renderer; leaving view cancels all frames',{visible:false},f=>{
  assert.equal(f.renderers.length,0);assert.equal(f.api.metrics().running,false);
  f.setVisible(true);f.step();const renderer=f.renderers[0],frames=renderer.renders.length;
  f.setVisible(false);assert.equal(f.api.metrics().running,false);assert.equal(f.raf.size,0);
  f.theme('light');f.api.setTimeForTesting(9);f.resize.emit();f.step();
  assert.equal(renderer.renders.length,frames,'offscreen theme/testing/resize cannot submit a frame');
  f.setVisible(true);f.step();assert.ok(renderer.renders.length>frames);
});

await run('zero-area adjacent edges release hero budget and cancel RAF despite isIntersecting',{},f=>{
  f.step();const renderer=f.renderers[0],frames=renderer.renders.length;
  const originalBounds=f.host.getBoundingClientRect;
  f.host.getBoundingClientRect=()=>({width:f.width,height:f.height,left:0,right:f.width,top:-f.height,bottom:0});
  f.intersection.emit({isIntersecting:true,intersectionRect:{width:f.width,height:0}});
  assert.equal(f.api.metrics().visible,false);assert.equal(f.api.metrics().running,false);
  assert.equal(f.raf.size,0);assert.equal(f.events.at(-1),false);
  f.api.setTimeForTesting(8);f.step();assert.equal(renderer.renders.length,frames);
  f.host.getBoundingClientRect=originalBounds;
  f.intersection.emit({isIntersecting:true,intersectionRect:{width:f.width,height:100}});
  f.step();assert.equal(f.api.metrics().visible,true);assert.equal(f.api.metrics().running,true);
  f.intersection.emit({isIntersecting:true,intersectionRect:{width:0,height:100}});
  assert.equal(f.api.metrics().visible,false);assert.equal(f.api.metrics().running,false);assert.equal(f.raf.size,0);
});

await run('visibility and BFCache transitions stop and resume without extra renderer',{},f=>{
  f.step();const renderer=f.renderers[0],frames=renderer.renders.length;
  f.document.hidden=true;f.emit(f.document,'visibilitychange');f.theme('light');f.api.setTimeForTesting(3);
  assert.equal(renderer.renders.length,frames);assert.equal(f.raf.size,0);assert.equal(f.api.metrics().running,false);
  f.document.hidden=false;f.emit(f.document,'visibilitychange');f.step();
  f.emit(f.window,'pagehide',{persisted:true});const hiddenFrames=renderer.renders.length;
  f.theme('dark');assert.equal(renderer.renders.length,hiddenFrames);assert.equal(f.raf.size,0);
  f.emit(f.window,'pageshow',{persisted:true});f.step();
  assert.equal(f.renderers.length,1);assert.equal(f.api.metrics().running,true);
});

for(const preference of ['reduced','saveData']) {
  await run(`${preference} starts static, can animate later, and stops immediately on return`,{[preference]:true},f=>{
    assert.equal(f.renderers.length,0);assert.equal(f.button.hidden,true);assert.equal(f.raf.size,0);
    const change=preference==='reduced'?f.setReduced:f.setSaveData;
    change(false);f.step();assert.equal(f.api.metrics().running,true);const frames=f.api.metrics().frames;
    change(true);f.theme('light');f.step();
    assert.equal(f.api.metrics().frames,frames);assert.equal(f.api.metrics().running,false);assert.equal(f.raf.size,0);
  });
}

await run('paused theme/resize draws take and release a single-frame budget',{},f=>{
  f.step();f.emit(f.button,'click');assert.equal(f.api.metrics().paused,true);assert.equal(f.raf.size,0);
  assert.equal(f.button.attrs['aria-label'],'Resume wave animation');
  const renderer=f.renderers[0],frames=renderer.renders.length;
  f.events.length=0;f.theme('light');
  assert.deepEqual(f.events,[true,false]);assert.equal(renderer.renders.length,frames+1);
  assert.equal(renderer.renders.at(-1).freeze,true);assert.equal(f.api.metrics().theme,'light');
  assert.equal(f.api.metrics().running,false);assert.equal(f.raf.size,0);
  f.events.length=0;f.resize.emit();assert.deepEqual(f.events,[true,false]);
  assert.equal(f.api.metrics().paused,true);f.api.setPaused(false);f.step();assert.equal(f.api.metrics().running,true);
});

await run('context restoration replaces renderer and ignores old canvas events',{},async f=>{
  f.step();const old=f.renderers[0];
  const lost=f.emit(old.canvas,'webglcontextlost');
  assert.equal(lost.defaultPrevented,true);assert.equal(f.api.metrics().lost,true);assert.equal(f.raf.size,0);
  f.emit(old.canvas,'webglcontextrestored');await Promise.resolve();
  assert.equal(f.renderers.length,2);assert.equal(old.disposed,true);assert.equal(old.canvas.listenerCount,0);
  assert.equal(f.api.metrics().lost,false);assert.equal(f.api.metrics().running,true);
  f.emit(old.canvas,'webglcontextlost');f.emit(old.canvas,'webglcontextrestored');
  assert.equal(f.renderers.length,2);assert.equal(f.api.metrics().lost,false);f.step();
  assert.equal(f.renderers[1].renders.length,1);
});

await run('creation failure exposes API error without scheduling frames',{createFailure:true},f=>{
  assert.equal(f.window.__gradientWaves,f.api);assert.equal(f.api.metrics().failed,true);
  assert.match(f.api.metrics().error,/creation failure/);assert.equal(f.raf.size,0);assert.equal(f.api.metrics().running,false);
});

await run('render failure disposes its canvas and cannot keep scheduling',{},async f=>{
  f.renderFailure=true;f.step();await Promise.resolve();
  assert.equal(f.api.metrics().failed,true);assert.match(f.api.metrics().error,/render failure/);
  assert.equal(f.api.metrics().rendererCount,0);assert.equal(f.api.metrics().running,false);assert.equal(f.raf.size,0);
  assert.equal(f.host.dataset.waveState,'fallback');assert.equal(f.renderers[0].canvas.listenerCount,0);
});

await run('compact DPR is bounded and sustained slow frames degrade then use poster',{compact:true},async f=>{
  assert.ok(f.api.metrics().dpr<=1.25);assert.equal(f.api.metrics().quality,'low');
  const initialDpr=f.api.metrics().dpr;
  for(let i=0;i<130;i++)f.step(70);
  assert.equal(f.api.metrics().quality,'low');assert.ok(f.api.metrics().dpr<initialDpr);
  assert.ok(f.api.metrics().dpr<=.9);assert.ok(f.width*f.height*f.api.metrics().dpr**2<=1050000);
  for(let i=0;i<260;i++)f.step(150);
  await Promise.resolve();
  assert.equal(f.api.metrics().degraded,true);assert.equal(f.api.metrics().rendererCount,0);
  assert.equal(f.api.metrics().running,false);assert.equal(f.raf.size,0);
  assert.equal(f.host.dataset.waveState,'low-performance');
});

await run('1000ms scheduler gaps do not cause degradation and foreground cadence recovers',{},f=>{
  f.renderCost=.05;
  f.step();const initialDpr=f.api.metrics().dpr;
  for(let i=0;i<300;i++)f.step(1000);
  let metrics=f.api.metrics();
  assert.equal(metrics.quality,'medium');assert.equal(metrics.degraded,false);
  assert.equal(metrics.dpr,initialDpr);assert.equal(metrics.rendererCount,1);
  assert.equal(metrics.measuredFrameSamples,0);assert.equal(metrics.frameIntervalAverageMs,0);
  assert.equal(metrics.running,true);assert.equal(f.raf.size,1);
  for(let i=0;i<180;i++)f.step(1000/60);
  metrics=f.api.metrics();
  assert.ok(metrics.measuredFrameSamples>=120,'fresh foreground samples accumulate');
  assert.ok(metrics.frameIntervalAverageMs>16 && metrics.frameIntervalAverageMs<18);
  assert.ok(metrics.cpuSubmitAverageMs<1);
  assert.equal(metrics.quality,'medium');assert.equal(metrics.degraded,false);
  assert.equal(metrics.running,true);assert.equal(f.raf.size,1);
});

await run('dispose releases listeners, observers, canvas, API and pending RAF',{},async f=>{
  f.step();f.api.dispose();await Promise.resolve();f.assertClean();
  const count=f.renderers.length;f.theme('light');f.emit(f.window,'pageshow');f.resize.emit();f.intersection.emit();
  assert.equal(f.renderers.length,count);assert.equal(f.raf.size,0);f.api.dispose();
});

await run('scroll/resize fallback works without observers and non-BFCache pagehide disposes',{withObservers:false,visible:false},async f=>{
  f.setVisible(true);f.step();assert.equal(f.api.metrics().running,true);
  f.setVisible(false);assert.equal(f.raf.size,0);f.emit(f.window,'resize');assert.equal(f.raf.size,0);
  f.emit(f.window,'pagehide',{persisted:false});await Promise.resolve();f.assertClean();
});

console.log('Mock lifecycle coverage only: real shader compilation, GPU cost, visual quality and browser behavior require separate authorized acceptance.');
