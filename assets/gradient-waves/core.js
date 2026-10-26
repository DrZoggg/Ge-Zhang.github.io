/**
 * GradientWaves native rendering core, directly adapted from React Bits.
 * Upstream: DavidHDev/react-bits @ e12c22192ac7b4b452c5e2feb9b586d74765d696
 * License: MIT + Commons Clause; see LICENSE.md and NOTICE.md in this directory.
 * Shader literals and the surface, lighting, ray and swell mathematics are retained.
 * This module owns no RAF, event listeners or observers. All time is in seconds.
 */
const CANVAS = 'gradient-waves-canvas';

const MAX_SWELLS = 4;
const SWELL_SECONDS = 3.2;
const SWELL_GAIN = 2.8;
const SWELL_WIDTH = 8;
const INTRO_SECONDS = 2.6;
const CAMERA_HEIGHT = 30;
const QUALITY = { low: 56, medium: 84, high: 120 };

const VERTEX = `#version 300 es
in vec2 aPosition;
void main() {
  gl_Position = vec4(aPosition, 0.0, 1.0);
}`;

const FRAGMENT = `#version 300 es
precision highp float;
uniform vec2 uResolution;
uniform float uTime;
uniform float uClock;
uniform float uAmplitude;
uniform float uWaveScale;
uniform float uWaveRatio;
uniform float uSwell;
uniform float uTurbulence;
uniform float uHeight;
uniform float uTilt;
uniform float uZoom;
uniform vec2 uLook;
uniform float uFogDepth;
uniform float uBrightness;
uniform float uOpacity;
uniform float uGrain;
uniform vec3 uHorizon;
uniform vec3 uWave;
uniform vec3 uCrest;
uniform vec3 uBackground;
uniform float uOpaque;
uniform float uLight;
uniform vec3 uSun;
uniform float uRelief;
uniform float uSheen;
uniform float uSteps;
uniform float uStride;
uniform vec3 uIntro;
uniform vec3 uSwells[${MAX_SWELLS}];
uniform float uSwellWidth;
out vec4 outColor;

const float FAR = 4000.0;

float hash(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

vec3 surface(vec2 xy) {
  vec2 freq = vec2(uWaveScale / 7.0, (uWaveScale * uWaveRatio) / 3.0);
  vec4 tc = vec4(uTime / 0.130, uTime / 0.810, uTime / 0.200, uTime / 0.710);
  float a = xy.x + tc.x;
  float swellPhase = (xy.y + a) / 20.0 + tc.y;
  float bend = uSwell * cos(swellPhase) / 20.0;
  float mx = a + uSwell * sin(swellPhase);
  float crossPhase = xy.x / 23.0 + tc.w;
  float my = xy.y - tc.z + uTurbulence * cos(crossPhase);
  float twist = -uTurbulence * sin(crossPhase) / 23.0;
  float cx = cos(mx * freq.x);
  float cy = cos(my * freq.y);
  float rise = 1.0;
  if (uIntro.z > 0.0) rise = mix(1.0, smoothstep(uIntro.y * 0.45, uIntro.y * 1.6, xy.x), uIntro.z);
  float amp = uAmplitude * rise;
  float h = (sin(mx * freq.x) + sin(my * freq.y)) * amp + uHeight;
  float dx = amp * (freq.x * cx * (1.0 + bend) + freq.y * cy * twist);
  float dy = amp * (freq.x * cx * bend + freq.y * cy);
  for (int k = 0; k < ${MAX_SWELLS}; k++) {
    vec3 sw = uSwells[k];
    if (sw.z <= 0.0) continue;
    float u = (xy.x - sw.x) / uSwellWidth;
    float v = (xy.y - sw.y) / (uSwellWidth * 3.5);
    float bump = sw.z * exp(-u * u - v * v);
    h += bump;
    dx += bump * (-2.0 * u / uSwellWidth);
    dy += bump * (-2.0 * v / (uSwellWidth * 3.5));
  }
  return vec3(h, dx, dy);
}

float march(vec3 origin, vec3 dir) {
  float dist = 0.0;
  for (int i = 0; i < 128; i++) {
    if (float(i) >= uSteps) break;
    float gap = origin.z + dist * dir.z - surface(origin.xy + dist * dir.xy).x;
    if (abs(gap) < 0.002 * dist + 0.01) break;
    dist += uStride * gap;
    if (!(abs(dist) < FAR)) return FAR;
  }
  return dist;
}

void main() {
  float c;
  float s;
  float vfov = (3.14159 / 2.3) / max(uZoom, 0.05);
  vec3 cam = vec3(0.0, 0.0, ${CAMERA_HEIGHT.toFixed(1)});
  vec2 uv = gl_FragCoord.xy / uResolution - 0.5;
  uv.x *= uResolution.x / uResolution.y;
  uv.y *= -1.0;

  vec3 dir = vec3(0.0, 0.0, -1.0);
  float ulen = length(uv);
  float xrot = vfov * ulen;
  c = cos(xrot);
  s = sin(xrot);
  dir = mat3(1.0, 0.0, 0.0, 0.0, c, -s, 0.0, s, c) * dir;
  vec2 nuv = ulen > 1e-5 ? uv / ulen : vec2(1.0, 0.0);
  dir = mat3(nuv.x, -nuv.y, 0.0, nuv.y, nuv.x, 0.0, 0.0, 0.0, 1.0) * dir;
  c = cos(uTilt + uLook.y);
  s = sin(uTilt + uLook.y);
  dir = mat3(c, 0.0, s, 0.0, 1.0, 0.0, -s, 0.0, c) * dir;
  c = cos(uLook.x);
  s = sin(uLook.x);
  dir = mat3(c, s, 0.0, -s, c, 0.0, 0.0, 0.0, 1.0) * dir;

  float dist = march(cam, dir);
  vec3 pos = cam + dist * dir;
  vec3 field = surface(pos.xy);
  vec3 view = -dir;

  float crest = clamp((field.x - uHeight) / max(2.0 * uAmplitude, 0.001) * 0.5 + 0.5, 0.0, 1.0);
  vec3 body = mix(uWave, uCrest, smoothstep(0.45, 1.0, crest) * 0.5);
  vec3 normal = normalize(vec3(-field.yz * (1.0 + 1.5 * uRelief), 1.0));
  float diffuse = clamp(dot(normal, uSun) * 0.5 + 0.5, 0.0, 1.0);
  float lightness = mix(1.0, diffuse * diffuse * (3.0 - 2.0 * diffuse), uRelief);
  float sheen = pow(clamp(dot(normal, normalize(uSun + view)), 0.0, 1.0), 14.0) * uSheen * (0.4 + 0.6 * uRelief);
  float rim = pow(1.0 - clamp(dot(normal, view), 0.0, 1.0), 3.0);

  vec3 col;
  float alpha;
  float haze = 1.0 - exp(-dist / (uFogDepth * 5.0));
  float fade = 1.0 - smoothstep(0.35, 1.0, haze);
  if (uLight < 0.5) {
    vec3 lit = mix(uHorizon * 0.18, body, lightness) + uCrest * sheen;
    lit = mix(lit, uHorizon, rim * 0.15 * uRelief);
    col = mix(lit, uHorizon, smoothstep(0.0, 1.0, haze)) * 0.85 * uBrightness;
    alpha = fade;
  } else {
    vec3 hue = mix(uHorizon, body, 0.35 + 0.65 * lightness);
    float density = mix(0.16, 0.9, 1.0 - lightness);
    density *= 1.0 - clamp(sheen, 0.0, 1.0) * 0.85;
    density *= 1.0 - 0.5 * smoothstep(0.0, 1.0, haze);
    col = hue;
    alpha = fade * clamp(density * uBrightness, 0.0, 1.0);
  }

  float reveal = uIntro.x;
  col = clamp(col, 0.0, 1.0);
  float grain = (hash(gl_FragCoord.xy + fract(uClock) * 64.0) - 0.5) * uGrain;
  alpha = clamp(alpha * (1.0 + grain), 0.0, 1.0) * reveal * uOpacity;
  if (uOpaque > 0.5) {
    outColor = vec4(mix(uBackground, col, alpha), 1.0);
  } else {
    outColor = vec4(col * alpha, alpha);
  }
}`;

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

const easeInOut = t => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

let probe = null;

const parseColor = (value, fallback) => {
  if (value === 'transparent') return null;
  if (typeof document === 'undefined') return fallback;
  if (!probe) probe = document.createElement('canvas').getContext('2d');
  if (!probe) return fallback;
  probe.fillStyle = '#000000';
  probe.fillStyle = value;
  const text = probe.fillStyle;
  if (text.startsWith('#')) {
    const hex = parseInt(text.slice(1), 16);
    return [((hex >> 16) & 255) / 255, ((hex >> 8) & 255) / 255, (hex & 255) / 255];
  }
  const match = /rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?/.exec(text);
  if (!match) return fallback;
  if (match[4] !== undefined && Number(match[4]) === 0) return null;
  return [Number(match[1]) / 255, Number(match[2]) / 255, Number(match[3]) / 255];
};

const rayAt = (point, aspect, s, look) => {
  const uvx = (point[0] - 0.5) * aspect;
  const uvy = point[1] - 0.5;
  const vfov = Math.PI / 2.3 / Math.max(s.zoom, 0.05);
  const length = Math.hypot(uvx, uvy);
  const turn = vfov * length;
  let dir = [0, -Math.sin(turn), -Math.cos(turn)];
  const nx = length > 1e-5 ? uvx / length : 1;
  const ny = length > 1e-5 ? uvy / length : 0;
  dir = [nx * dir[0] + ny * dir[1], -ny * dir[0] + nx * dir[1], dir[2]];
  const pitch = s.tilt + look[1];
  const cp = Math.cos(pitch);
  const sp = Math.sin(pitch);
  dir = [cp * dir[0] - sp * dir[2], dir[1], sp * dir[0] + cp * dir[2]];
  const cy = Math.cos(look[0]);
  const sy = Math.sin(look[0]);
  dir = [cy * dir[0] - sy * dir[1], sy * dir[0] + cy * dir[1], dir[2]];
  return dir;
};

const groundAt = (point, aspect, s, look) => {
  const dir = rayAt(point, aspect, s, look);
  if (dir[2] > -0.02) return null;
  const travel = (CAMERA_HEIGHT - s.height) / -dir[2];
  return [dir[0] * travel, dir[1] * travel];
};

const normalizeOptions = ({
  horizonColor = '#5227FF',
  waveColor = '#FF9FFC',
  crestColor = '#FFFFFF',
  backgroundColor = 'transparent',
  lightMode = false,
  speed = 0.4,
  amplitude = 2.5,
  waveScale = 0.6,
  waveRatio = 0.9,
  swell = 35,
  turbulence = 20,
  tilt = 64,
  zoom = 1,
  height = 5.5,
  fogDepth = 15,
  relief = 1,
  lightAngle = 120,
  sheen = 0,
  brightness = 1,
  opacity = 1,
  grain = 0.2,
  quality = 'medium',
  intro = true,
  mouseInteraction = true,
  parallaxStrength = 0.5,
  mouseStrength = 0.6,
  swellOnClick = true,
  paused = false,
  dpr = 2,
  className = '',
  style
} = {}) => {
  const horizon = parseColor(horizonColor, [0.32, 0.15, 1]) ?? [0.32, 0.15, 1];
  const wave = parseColor(waveColor, [1, 0.62, 0.99]) ?? [1, 0.62, 0.99];
  const crest = parseColor(crestColor, [1, 1, 1]) ?? [1, 1, 1];
  const paper = parseColor(backgroundColor, null);
  return {
    horizon,
    wave,
    crest,
    paper,
    lightMode,
    speed,
    amplitude: Math.max(0, amplitude),
    waveScale: Math.max(0.01, waveScale),
    waveRatio: Math.max(0.01, waveRatio),
    swell,
    turbulence,
    tilt: (clamp(tilt, 10, 85) * Math.PI) / 180,
    zoom: Math.max(0.05, zoom),
    height,
    fogDepth: Math.max(0.5, fogDepth),
    relief: clamp(relief, 0, 1),
    lightAngle: (lightAngle * Math.PI) / 180,
    sheen: Math.max(0, sheen),
    brightness: Math.max(0, brightness),
    opacity: clamp(opacity, 0, 1),
    grain: typeof grain === 'number' ? Math.max(0, grain) : grain ? 0.05 : 0,
    steps: QUALITY[quality] ?? QUALITY.medium,
    intro,
    mouseInteraction,
    parallaxStrength: Math.max(0, parallaxStrength),
    mouseStrength: clamp(mouseStrength, 0, 1),
    swellOnClick,
    paused,
    dpr: Math.max(0.5, dpr)
  };
};

const compile = (gl, type, source) => {
  const shader = gl.createShader(type);
  if (!shader) throw new Error('GradientWaves could not create a shader');
  try {
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      throw new Error('GradientWaves shader compilation failed: ' + (gl.getShaderInfoLog(shader) || 'unknown error'));
    }
    return shader;
  } catch (error) {
    gl.deleteShader(shader);
    throw error;
  }
};

/**
 * x/y pointer and swell coordinates are normalized container coordinates (0..1).
 * resize takes CSS-pixel width/height and an explicit actual DPR chosen by caller.
 * setTime changes wave phase (uTime), not the independent intro/swell/grain clock.
 */
export function createGradientWavesRenderer(container, options = {}) {
  if (!container || typeof container.appendChild !== 'function') {
    throw new TypeError('GradientWaves requires a container element');
  }
  let rawOptions = { ...options };
  const settingsRef = { current: normalizeOptions(rawOptions) };
  const canvas = document.createElement('canvas');
  canvas.className = CANVAS;
  let gl = null;
  let vertex = null;
  let fragment = null;
  let program = null;
  let vao = null;
  let buffer = null;
  let disposed = false;
  const state = {
    width: 1, height: 1, cssWidth: 0, cssHeight: 0, dpr: 1,
    time: 0, clock: 0, introAt: -1,
    pointer: [0.5, 0.5], inside: false,
    look: [0, 0], steer: [0, 0], swells: [],
    frames: 0, drawMs: 0, reduced: false,
    moving: false, turning: false, transient: false
  };
  const now = () => typeof performance !== 'undefined' ? performance.now() : Date.now();
  const safely = action => { try { action(); } catch { /* Complete all cleanup paths. */ } };
  const dispose = () => {
    if (disposed) return;
    disposed = true;
    if (gl) {
      if (vertex) safely(() => gl.deleteShader(vertex));
      if (fragment) safely(() => gl.deleteShader(fragment));
      if (program) safely(() => gl.deleteProgram(program));
      if (buffer) safely(() => gl.deleteBuffer(buffer));
      if (vao) safely(() => gl.deleteVertexArray(vao));
      safely(() => gl.getExtension('WEBGL_lose_context')?.loseContext());
    }
    vertex = fragment = program = buffer = vao = null;
    safely(() => canvas.remove());
  };
  const assertAlive = () => {
    if (disposed) throw new Error('GradientWaves renderer is disposed');
  };
  let u;
  try {
    container.appendChild(canvas);
    gl = canvas.getContext('webgl2', {
      alpha: true, antialias: false, depth: false, stencil: false,
      premultipliedAlpha: true, powerPreference: 'high-performance'
    });
    if (!gl || typeof gl.createVertexArray !== 'function') {
      throw new Error('GradientWaves requires WebGL2');
    }
    vertex = compile(gl, gl.VERTEX_SHADER, VERTEX);
    fragment = compile(gl, gl.FRAGMENT_SHADER, FRAGMENT);
    program = gl.createProgram();
    if (!program) throw new Error('GradientWaves could not create a program');
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.bindAttribLocation(program, 0, 'aPosition');
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error('GradientWaves program linking failed: ' + (gl.getProgramInfoLog(program) || 'unknown error'));
    }
    gl.deleteShader(vertex);
    gl.deleteShader(fragment);
    vertex = fragment = null;
    const names = [
      'uResolution',
      'uTime',
      'uClock',
      'uAmplitude',
      'uWaveScale',
      'uWaveRatio',
      'uSwell',
      'uTurbulence',
      'uHeight',
      'uTilt',
      'uZoom',
      'uLook',
      'uFogDepth',
      'uBrightness',
      'uOpacity',
      'uGrain',
      'uHorizon',
      'uWave',
      'uCrest',
      'uBackground',
      'uOpaque',
      'uLight',
      'uSun',
      'uRelief',
      'uSheen',
      'uSteps',
      'uStride',
      'uIntro',
      'uSwells',
      'uSwellWidth'
    ];
    u = {};
    names.forEach(name => {
      u[name] = gl.getUniformLocation(program, name);
    });
    vao = gl.createVertexArray();
    if (!vao) throw new Error('GradientWaves could not create a vertex array');
    gl.bindVertexArray(vao);
    buffer = gl.createBuffer();
    if (!buffer) throw new Error('GradientWaves could not create a vertex buffer');
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.useProgram(program);
    if (gl.getError() !== gl.NO_ERROR) throw new Error('GradientWaves WebGL2 setup failed');
  } catch (error) {
    dispose();
    throw error;
  }
  const swellData = new Float32Array(MAX_SWELLS * 3);
  const introProgress = (s, reduced) => {
    if (!s.intro || reduced || state.introAt < 0) return 1;
    return clamp((state.clock - state.introAt) / INTRO_SECONDS, 0, 1);
  };

  const draw = reduced => {
    const s = settingsRef.current;
    gl.viewport(0, 0, state.width, state.height);
    gl.uniform2f(u.uResolution, state.width, state.height);
    gl.uniform1f(u.uTime, state.time);
    gl.uniform1f(u.uClock, state.clock);
    gl.uniform1f(u.uAmplitude, s.amplitude);
    gl.uniform1f(u.uWaveScale, s.waveScale);
    gl.uniform1f(u.uWaveRatio, s.waveRatio);
    gl.uniform1f(u.uSwell, s.swell);
    gl.uniform1f(u.uTurbulence, s.turbulence);
    gl.uniform1f(u.uHeight, s.height);
    gl.uniform1f(u.uTilt, s.tilt);
    gl.uniform1f(u.uZoom, s.zoom);
    gl.uniform2f(u.uLook, state.look[0], state.look[1]);
    gl.uniform1f(u.uFogDepth, s.fogDepth);
    gl.uniform1f(u.uBrightness, s.brightness);
    gl.uniform1f(u.uOpacity, s.opacity);
    gl.uniform1f(u.uGrain, s.grain);
    gl.uniform3fv(u.uHorizon, s.horizon);
    gl.uniform3fv(u.uWave, s.wave);
    gl.uniform3fv(u.uCrest, s.crest);
    const paperColor = s.paper ?? [0, 0, 0];
    gl.uniform3f(u.uBackground, paperColor[0], paperColor[1], paperColor[2]);
    gl.uniform1f(u.uOpaque, s.paper ? 1 : 0);
    gl.uniform1f(u.uLight, s.lightMode ? 1 : 0);
    const elevation = 0.52;
    const angle = s.lightAngle + state.steer[0] * s.mouseStrength * 2;
    const altitude = elevation - state.steer[1] * s.mouseStrength * 0.7;
    gl.uniform3f(
      u.uSun,
      Math.cos(altitude) * Math.cos(angle),
      Math.cos(altitude) * Math.sin(angle),
      Math.sin(altitude)
    );
    gl.uniform1f(u.uRelief, s.relief);
    gl.uniform1f(u.uSheen, s.sheen);
    gl.uniform1f(u.uSteps, s.steps);
    const slope =
      s.amplitude *
      ((s.waveScale / 7) * (1 + Math.abs(s.swell) / 20) +
        ((s.waveScale * s.waveRatio) / 3) * (1 + Math.abs(s.turbulence) / 23));
    const progress = introProgress(s, reduced);
    const shown = Math.min(1, progress / 0.22);
    const crest = 160 * Math.pow(3 / 160, easeInOut(Math.max(0, (progress - 0.1) / 0.9)));
    const settle = clamp((progress - 0.75) / 0.25, 0, 1);
    gl.uniform3f(u.uIntro, shown * shown * (3 - 2 * shown), crest, 1 - settle * settle * (3 - 2 * settle));
    swellData.fill(0);
    let swellPeak = 0;
    state.swells.forEach((swell, index) => {
      const age = state.clock - swell.at;
      const life = age / SWELL_SECONDS;
      const envelope = (1 - Math.exp(-age / 0.25)) * Math.pow(1 - life, 1.6);
      const lift = s.amplitude * SWELL_GAIN * envelope;
      swellData.set([swell.x - age * 12, swell.y, lift], index * 3);
      swellPeak = Math.max(swellPeak, lift);
    });
    gl.uniform3fv(u.uSwells, swellData);
    gl.uniform1f(u.uSwellWidth, SWELL_WIDTH);
    gl.uniform1f(u.uStride, 0.9 / Math.max(1, (slope + (swellPeak * 0.86) / SWELL_WIDTH) / 1.5));
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  };

  const getState = () => ({
    time: state.time, clock: state.clock,
    look: [...state.look], steer: [...state.steer],
    swells: state.swells.map(swell => ({ ...swell })),
    frames: state.frames, drawMs: state.drawMs,
    width: state.width, height: state.height,
    cssWidth: state.cssWidth, cssHeight: state.cssHeight, dpr: state.dpr,
    pointer: [...state.pointer], inside: state.inside,
    moving: state.moving, turning: state.turning, transient: state.transient,
    reduced: state.reduced, disposed,
    introProgress: introProgress(settingsRef.current, state.reduced)
  });
  const setOptions = next => {
    assertAlive();
    if (!next || typeof next !== 'object' || Array.isArray(next)) throw new TypeError('Expected options object');
    const merged = { ...rawOptions, ...next };
    const normalized = normalizeOptions(merged);
    rawOptions = merged;
    settingsRef.current = normalized;
  };
  const resize = (width, height, dpr = 1) => {
    assertAlive();
    if (![width, height, dpr].every(Number.isFinite) || width < 0 || height < 0 || dpr <= 0) {
      throw new TypeError('Expected nonnegative CSS dimensions and positive DPR');
    }
    state.cssWidth = width;
    state.cssHeight = height;
    state.dpr = dpr;
    const pixelWidth = Math.max(1, Math.round(width * dpr));
    const pixelHeight = Math.max(1, Math.round(height * dpr));
    if (pixelWidth !== state.width || pixelHeight !== state.height) {
      state.width = pixelWidth;
      state.height = pixelHeight;
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
  };
  const setPointer = (x, y, inside = true) => {
    assertAlive();
    const within = Number.isFinite(x) && Number.isFinite(y) && x >= 0 && x <= 1 && y >= 0 && y <= 1;
    state.inside = Boolean(inside) && within;
    if (state.inside) state.pointer = [x, y];
  };
  const addSwell = (x, y) => {
    assertAlive();
    const s = settingsRef.current;
    if (!s.swellOnClick || state.reduced || !Number.isFinite(x) || !Number.isFinite(y) || x < 0 || x > 1 || y < 0 || y > 1) return false;
    const ground = groundAt([x, y], state.width / Math.max(state.height, 1), s, state.look);
    if (!ground) return false;
    state.swells.push({ x: ground[0], y: ground[1], at: state.clock });
    if (state.swells.length > MAX_SWELLS) state.swells.shift();
    return true;
  };
  const render = (dt = 0, { reduced = false, freeze = false } = {}) => {
    assertAlive();
    if (!Number.isFinite(dt)) throw new TypeError('Expected finite delta seconds');
    dt = freeze ? 0 : clamp(dt, 0, 0.1);
    reduced = Boolean(reduced);
    const s = settingsRef.current;
    state.reduced = reduced;
    state.clock += dt;
    if (state.introAt < 0) state.introAt = state.clock;
    if (!s.paused && !reduced) state.time += dt * s.speed;

    const steering = s.mouseInteraction && state.inside && !reduced;
    const target = steering ? state.pointer : [0.5, 0.5];
    const ease = 1 - Math.exp(-dt / 0.45);
    const goalX = (target[0] - 0.5) * s.parallaxStrength * 0.35;
    const goalY = (target[1] - 0.5) * s.parallaxStrength * 0.18;
    state.look[0] += (goalX - state.look[0]) * ease;
    state.look[1] += (goalY - state.look[1]) * ease;
    const moving = Math.abs(goalX - state.look[0]) + Math.abs(goalY - state.look[1]) > 0.0002;

    const steerEase = 1 - Math.exp(-dt / 0.6);
    const steerX = steering ? state.pointer[0] - 0.5 : 0;
    const steerY = steering ? 0.5 - state.pointer[1] : 0;
    state.steer[0] += (steerX - state.steer[0]) * steerEase;
    state.steer[1] += (steerY - state.steer[1]) * steerEase;
    const turning = Math.abs(steerX - state.steer[0]) + Math.abs(steerY - state.steer[1]) > 0.0005;
    state.swells = state.swells.filter(swell => state.clock - swell.at < SWELL_SECONDS);
    state.moving = moving;
    state.turning = turning;
    state.transient = moving || turning || state.swells.length > 0 || introProgress(s, reduced) < 1;
    const started = now();
    draw(reduced);
    state.drawMs = now() - started;
    state.frames += 1;
    return getState();
  };
  const setTime = seconds => {
    assertAlive();
    if (!Number.isFinite(seconds) || seconds < 0) throw new TypeError('Expected nonnegative phase seconds');
    state.time = seconds;
  };
  // Canvas starts with the same 1x1 state until the caller supplies its dimensions.
  canvas.width = state.width;
  canvas.height = state.height;
  return { canvas, setOptions, resize, render, setPointer, addSwell, getState, setTime, dispose };
}
