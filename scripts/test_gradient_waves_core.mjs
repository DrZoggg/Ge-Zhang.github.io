/**
 * GradientWaves core unit checks: run with node scripts/test_gradient_waves_core.mjs.
 * Uses an explicit mock DOM/WebGL interface, NOT a browser, GPU, visual comparison,
 * GLSL compiler, screenshot, or performance benchmark. No network or private paths.
 */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { after, test } from 'node:test';

const source = readFileSync(new URL('../assets/gradient-waves/core.js', import.meta.url), 'utf8');
const { createGradientWavesRenderer } = await import(
  'data:text/javascript;base64,' + Buffer.from(source).toString('base64')
);

// Independent upstream baseline: the UTF-8 text INSIDE each original backtick
// literal, before JS interpolation, from the official fixed source below.
// https://raw.githubusercontent.com/DavidHDev/react-bits/e12c22192ac7b4b452c5e2feb9b586d74765d696/src/content/Backgrounds/GradientWaves/GradientWaves.jsx
// Do not derive these expected values from the local adapted core or auto-update.
const UPSTREAM_SHADER_SHA256 = Object.freeze({
  VERTEX: '254cf753223046ecd2701ab8d840273bb06e104774ef4940f99dbbfa852945f4',
  FRAGMENT: '73527d03cf36ec2215b578fcd6ff81545a0229966181c8df3350d14e2bbf37a6'
});

const globalNames = ['document', 'requestAnimationFrame', 'ResizeObserver', 'IntersectionObserver'];
const savedGlobals = new Map(globalNames.map(name => [name, Object.getOwnPropertyDescriptor(globalThis, name)]));
after(() => {
  for (const [name, descriptor] of savedGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else delete globalThis[name];
  }
});

function makeFixture(failure = '') {
  const live = { shaders: new Set(), programs: new Set(), buffers: new Set(), vaos: new Set() };
  const counts = { webglContexts: 0, draws: 0, contextLosses: 0, programsCreated: 0 };
  const uniforms = new Map();
  const createdCanvases = [];
  const deleted = new Set();
  let nextId = 0;
  const allocate = (kind, extra = {}) => {
    const handle = { id: ++nextId, kind, ...extra };
    live[kind].add(handle);
    return handle;
  };
  const release = (kind, handle) => {
    assert.ok(handle, `cannot delete null ${kind}`);
    assert.equal(deleted.has(handle), false, `must not delete ${kind} twice`);
    assert.equal(live[kind].delete(handle), true, `must delete owned ${kind}`);
    deleted.add(handle);
  };
  const gl = {
    VERTEX_SHADER: 1, FRAGMENT_SHADER: 2, COMPILE_STATUS: 3, LINK_STATUS: 4,
    ARRAY_BUFFER: 5, STATIC_DRAW: 6, FLOAT: 7, COLOR_BUFFER_BIT: 8, TRIANGLES: 9, NO_ERROR: 0,
    createShader(type) {
      return failure === 'shader-create' ? null : allocate('shaders', { type });
    },
    shaderSource(shader, text) { shader.source = text; },
    compileShader() {},
    getShaderParameter(shader) {
      return !(failure === 'vertex-compile' && shader.type === this.VERTEX_SHADER)
        && !(failure === 'fragment-compile' && shader.type === this.FRAGMENT_SHADER);
    },
    getShaderInfoLog() { return 'unit-controlled compile failure'; },
    deleteShader(handle) { release('shaders', handle); },
    createProgram() {
      if (failure === 'program-create') return null;
      counts.programsCreated += 1;
      return allocate('programs');
    },
    attachShader() {}, bindAttribLocation() {}, linkProgram() {},
    getProgramParameter() { return failure !== 'program-link'; },
    getProgramInfoLog() { return 'unit-controlled link failure'; },
    deleteProgram(handle) { release('programs', handle); },
    getUniformLocation(program, name) { return name; },
    createVertexArray() { return failure === 'vao-create' ? null : allocate('vaos'); },
    bindVertexArray() {},
    deleteVertexArray(handle) { release('vaos', handle); },
    createBuffer() { return failure === 'buffer-create' ? null : allocate('buffers'); },
    bindBuffer() {}, bufferData() {}, enableVertexAttribArray() {},
    vertexAttribPointer() {}, useProgram() {},
    deleteBuffer(handle) { release('buffers', handle); },
    getError() { return failure === 'gl-setup' ? 1282 : this.NO_ERROR; },
    getExtension(name) {
      assert.equal(name, 'WEBGL_lose_context');
      return { loseContext() { counts.contextLosses += 1; } };
    },
    viewport() {},
    uniform1f(name, value) { uniforms.set(name, value); },
    uniform2f(name, ...values) { uniforms.set(name, values); },
    uniform3f(name, ...values) { uniforms.set(name, values); },
    uniform3fv(name, value) { uniforms.set(name, [...value]); },
    clearColor() {}, clear() {},
    drawArrays() { counts.draws += 1; }
  };
  const container = {
    children: [],
    appendChild(canvas) {
      this.children.push(canvas);
      canvas.parentNode = this;
    }
  };
  globalThis.document = {
    createElement(name) {
      assert.equal(name, 'canvas');
      const canvas = {
        width: 300, height: 150, parentNode: null, removalCalls: 0,
        getContext(type, options) {
          // Only a color-parser stand-in; not a full CSS/canvas implementation.
          if (type === '2d') return { fillStyle: '#000000' };
          assert.equal(type, 'webgl2');
          assert.equal(options.premultipliedAlpha, true);
          counts.webglContexts += 1;
          return failure === 'no-webgl2' ? null : gl;
        },
        remove() {
          this.removalCalls += 1;
          if (this.parentNode) {
            this.parentNode.children = this.parentNode.children.filter(child => child !== this);
            this.parentNode = null;
          }
        }
      };
      createdCanvases.push(canvas);
      return canvas;
    },
    addEventListener() { assert.fail('the core must not own DOM listeners'); }
  };
  const forbiddenLifecycle = () => assert.fail('the core must not own scheduling/observers');
  globalThis.requestAnimationFrame = forbiddenLifecycle;
  globalThis.ResizeObserver = class { constructor() { forbiddenLifecycle(); } };
  globalThis.IntersectionObserver = class { constructor() { forbiddenLifecycle(); } };
  return {
    container, live, counts, uniforms, createdCanvases,
    assertReleased() {
      for (const [kind, handles] of Object.entries(live)) assert.equal(handles.size, 0, `${kind} leaked`);
      assert.equal(container.children.length, 0, 'canvas must be detached');
      const rendererCanvases = createdCanvases.filter(canvas => canvas.removalCalls > 0);
      assert.equal(rendererCanvases.length, 1, 'one renderer canvas removed');
      assert.equal(rendererCanvases[0].removalCalls, 1, 'canvas removal is idempotent');
    }
  };
}

test('shader literal text matches independent fixed upstream SHA256', () => {
  for (const [name, expected] of Object.entries(UPSTREAM_SHADER_SHA256)) {
    const match = new RegExp('const ' + name + ' = `([\\s\\S]*?)`;').exec(source);
    assert.ok(match, `${name} literal declaration missing`);
    assert.equal(createHash('sha256').update(match[1], 'utf8').digest('hex'), expected, name);
  }
  assert.match(source, /const MAX_SWELLS = 4;/);
  assert.match(source, /const CAMERA_HEIGHT = 30;/);
  assert.match(source, /const QUALITY = \{ low: 56, medium: 84, high: 120 \};/);
});

test('resize, pointer smoothing, phase-only setTime and detached state snapshots', () => {
  const f = makeFixture();
  const renderer = createGradientWavesRenderer(f.container, { intro: false });
  try {
    renderer.resize(320, 180, 1.5);
    renderer.setPointer(0.9, 0.2, true);
    renderer.render(0.1);
    const state = renderer.getState();
    assert.deepEqual([state.width, state.height], [480, 270]);
    assert.deepEqual([renderer.canvas.width, renderer.canvas.height], [480, 270]);
    assert.ok(Math.abs(state.time - 0.04) < 1e-12);
    assert.ok(state.look[0] > 0 && state.look[1] < 0);
    assert.ok(state.steer[0] > 0 && state.steer[1] > 0);
    state.look[0] = 999;
    assert.notEqual(renderer.getState().look[0], 999);
    const clock = renderer.getState().clock;
    renderer.setTime(2.5);
    assert.equal(renderer.getState().time, 2.5);
    assert.equal(renderer.getState().clock, clock);
  } finally {
    renderer.dispose();
  }
  f.assertReleased();
});

test('freeze redraws without advancing clocks, look, steering or swells', () => {
  const f = makeFixture();
  const renderer = createGradientWavesRenderer(f.container, { intro: false });
  try {
    renderer.resize(320, 180, 1);
    renderer.setPointer(0.8, 0.3, true);
    renderer.render(0.1);
    assert.equal(renderer.addSwell(0.5, 0.5), true);
    const before = renderer.getState();
    renderer.render(100, { freeze: true });
    const frozen = renderer.getState();
    for (const key of ['time', 'clock', 'look', 'steer', 'swells']) assert.deepEqual(frozen[key], before[key], key);
    assert.equal(frozen.frames, before.frames + 1);
    assert.equal(f.counts.draws, 2);
    assert.ok(Number.isFinite(frozen.drawMs) && frozen.drawMs >= 0, 'CPU-submit metric only');
  } finally {
    renderer.dispose();
  }
  f.assertReleased();
});

test('theme and quality update uniforms without replacing the context/program', () => {
  const f = makeFixture();
  const renderer = createGradientWavesRenderer(f.container, { intro: false });
  try {
    const canvas = renderer.canvas;
    renderer.render(0);
    assert.equal(f.uniforms.get('uLight'), 0);
    assert.equal(f.uniforms.get('uSteps'), 84);
    renderer.setOptions({ lightMode: true, horizonColor: '#2563eb', quality: 'low' });
    renderer.render(0, { freeze: true });
    assert.equal(f.uniforms.get('uLight'), 1);
    assert.deepEqual(f.uniforms.get('uHorizon'), [37 / 255, 99 / 255, 235 / 255]);
    assert.equal(f.uniforms.get('uSteps'), 56);
    renderer.setOptions({ quality: 'high' });
    renderer.render(0, { freeze: true });
    assert.equal(f.uniforms.get('uSteps'), 120);
    assert.equal(renderer.canvas, canvas);
    assert.equal(f.counts.webglContexts, 1);
    assert.equal(f.counts.programsCreated, 1);
  } finally {
    renderer.dispose();
  }
  f.assertReleased();
});

test('click swells retain newest four, reach uniforms and expire', () => {
  const f = makeFixture();
  const renderer = createGradientWavesRenderer(f.container, { intro: false });
  try {
    renderer.resize(320, 180, 1);
    const inserted = [];
    for (let index = 0; index < 6; index += 1) {
      assert.equal(renderer.addSwell(0.35 + index * 0.05, 0.5), true);
      inserted.push(renderer.getState().swells.at(-1));
    }
    assert.deepEqual(renderer.getState().swells, inserted.slice(-4));
    renderer.render(0.1);
    const uniform = f.uniforms.get('uSwells');
    assert.equal(uniform.length, 12);
    assert.ok(uniform.filter((value, index) => index % 3 === 2).every(value => value > 0));
    for (let frame = 0; frame < 33; frame += 1) renderer.render(0.1);
    assert.equal(renderer.getState().swells.length, 0);
  } finally {
    renderer.dispose();
  }
  f.assertReleased();
});

test('reduced rendering skips intro, base movement, pointer steering and new swells', () => {
  const f = makeFixture();
  const renderer = createGradientWavesRenderer(f.container, { intro: true });
  try {
    renderer.setPointer(0.9, 0.1, true);
    renderer.render(0.1, { reduced: true });
    const state = renderer.getState();
    assert.equal(state.introProgress, 1);
    assert.equal(state.time, 0);
    assert.equal(state.clock, 0.1);
    assert.deepEqual(state.look, [0, 0]);
    assert.deepEqual(state.steer, [0, 0]);
    assert.equal(f.uniforms.get('uIntro')[0], 1);
    assert.equal(f.uniforms.get('uIntro')[2], 0);
    assert.equal(renderer.addSwell(0.5, 0.5), false);
  } finally {
    renderer.dispose();
  }
  f.assertReleased();
});

test('dispose is idempotent and releases all owned GL/canvas resources', () => {
  const f = makeFixture();
  const renderer = createGradientWavesRenderer(f.container, { intro: false });
  renderer.render(0);
  renderer.dispose();
  renderer.dispose();
  assert.equal(renderer.getState().disposed, true);
  assert.equal(f.counts.contextLosses, 1);
  assert.throws(() => renderer.render(0), /disposed/);
  f.assertReleased();
});

for (const failure of [
  'no-webgl2', 'shader-create', 'vertex-compile', 'fragment-compile',
  'program-create', 'program-link', 'vao-create', 'buffer-create', 'gl-setup'
]) {
  test(`initialization failure ${failure} cleans partial resources before throwing`, () => {
    const f = makeFixture(failure);
    assert.throws(() => createGradientWavesRenderer(f.container, { intro: false }), /GradientWaves/);
    assert.equal(f.counts.contextLosses, failure === 'no-webgl2' ? 0 : 1);
    f.assertReleased();
  });
}
