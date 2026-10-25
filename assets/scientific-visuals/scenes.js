/* Wheel geometry/pose structure adapted from celestial-wheel (MIT), pinned in NOTICE.md.
 * Field geometry and shaders are original conceptual artwork, not research data. */
import * as THREE from '../vendor/three-r186/three.module.js';

const TAU = Math.PI * 2;
export const PALETTES = {
  dark: { ink: 0x071419, line: 0x89b9cb, bright: 0xd6f3f0, teal: 0x75d7c7, gold: 0xd9b984, metal: 0x7a929c },
  light: { ink: 0xf3f6f8, line: 0x376879, bright: 0x234552, teal: 0x26746d, gold: 0x947044, metal: 0x48616d },
};

// Upstream circle construction is retained: an XZ-plane circle, assembled into
// independently posed groups. No glyph atlas, cosmological data, taiji or picking.
function circle(radius, material, segments = 256, start = 0, end = TAU) {
  const positions = new Float32Array((segments + 1) * 3);
  for (let k = 0; k <= segments; k++) {
    const a = start + k / segments * (end - start);
    positions[k * 3] = Math.cos(a) * radius;
    positions[k * 3 + 2] = Math.sin(a) * radius;
  }
  return new THREE.Line(new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(positions, 3)), material);
}
function materialColor(material, key, opacity = 1) {
  material.userData.paletteKey = key;
  material.userData.darkOpacity = opacity;
  return material;
}
function lineMaterial(key, opacity) {
  return materialColor(new THREE.LineBasicMaterial({ transparent: true, opacity, depthWrite: false }), key, opacity);
}
function disposeScene(scene) {
  const geometries = new Set(), materials = new Set();
  scene.traverse(object => {
    if (object.geometry) geometries.add(object.geometry);
    if (object.material) (Array.isArray(object.material) ? object.material : [object.material]).forEach(m => materials.add(m));
  });
  geometries.forEach(g => g.dispose());
  materials.forEach(m => m.dispose());
}
function applyPalette(scene, theme) {
  const palette = PALETTES[theme] || PALETTES.dark;
  if(scene.fog) scene.fog.color.setHex(palette.ink);
  scene.traverse(object => {
    const material = object.material;
    if (!material || !material.userData.paletteKey) return;
    const key = material.userData.paletteKey;
    material.color?.setHex(palette[key]);
    if (material.emissive) { material.emissive.setHex(palette[key]); material.emissiveIntensity = theme === 'light' ? .06 : .18; }
    if (material.transparent) material.opacity = material.userData.darkOpacity * (theme === 'light' ? .86 : 1);
  });
}

export function createWheel() {
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(PALETTES.dark.ink, 12, 28);
  // Original upstream perspective FOV, calm camera framing and XZ ring convention.
  const camera = new THREE.PerspectiveCamera(36, 1, .1, 100);
  camera.position.set(1.4, 5.9, 17.1); camera.lookAt(0, 0, 0);
  const world = new THREE.Group(); scene.add(world);
  scene.add(new THREE.HemisphereLight(0xc4edee, 0x173347, 2.2));
  const key = new THREE.DirectionalLight(0xf0f5e8, 3.4); key.position.set(-5, 7, 5); scene.add(key);
  const rim = new THREE.DirectionalLight(0x7cc9e5, 2.4); rim.position.set(6, 1, -4); scene.add(rim);
  const rings = [];
  const definitions = [
    [1.18, .5, -.24, .18, 1], [1.84, -.65, .55, .86, -1],
    [2.48, .92, -.66, 1.6, 1], [3.05, -.9, -.36, 2.5, -1],
    [3.65, .38, .8, 3.2, 1], [4.18, -.35, -.9, 4.4, -1],
    [4.72, 1.08, .25, 5.2, 1], [5.12, -.12, .16, 5.9, -1],
  ];
  const pointGeometry = new THREE.SphereGeometry(.035, 7, 5);
  const metallic = materialColor(new THREE.MeshStandardMaterial({ metalness: .72, roughness: .32 }), 'metal');
  const bright = materialColor(new THREE.MeshBasicMaterial(), 'bright');
  definitions.forEach(([r, tx, tz, phase, direction], i) => {
    const group = new THREE.Group(); world.add(group);
    const track = new THREE.Mesh(new THREE.TorusGeometry(r, i === 7 ? .017 : .012, 5, 240), metallic);
    track.rotation.x = Math.PI / 2; group.add(track);
    group.add(circle(r + .045, lineMaterial(i % 3 === 0 ? 'gold' : 'line', i === 7 ? .65 : .44)));
    if (i % 2 === 0) group.add(circle(r - .045, lineMaterial('line', .3)));
    const marks = [];
    const n = i === 7 ? 240 : 120;
    for (let k = 0; k < n; k++) {
      const a = k / n * TAU;
      const length = k % 10 === 0 ? .12 : k % 5 === 0 ? .065 : .025;
      const r0 = r + .065, r1 = r0 + length;
      marks.push(Math.cos(a) * r0, 0, Math.sin(a) * r0, Math.cos(a) * r1, 0, Math.sin(a) * r1);
    }
    group.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(marks, 3)), lineMaterial(i % 3 === 0 ? 'gold' : 'bright', .64)));
    // Sparse arcs and tiny bead markers give a stable directional cue without labels.
    group.add(circle(r - .075, lineMaterial(i % 3 === 0 ? 'gold' : 'teal', .85), 40, phase, phase + .42));
    const bead = new THREE.Mesh(pointGeometry, bright); bead.position.set(Math.cos(phase) * r, 0, Math.sin(phase) * r); group.add(bead);
    const base = new THREE.Quaternion().setFromEuler(new THREE.Euler(tx, phase, tz, 'YXZ'));
    rings.push({ group, base, tx, tz, phase, direction });
  });
  // Quiet independent outer trajectories; original upstream orbit idea, now bounded.
  [[5.42, .8, .3], [5.54, -.6, -.45]].forEach(([r, tx, tz]) => {
    const orbit = circle(r, lineMaterial('line', .18)); orbit.rotation.set(tx, 0, tz); world.add(orbit);
  });
  const core = new THREE.Group(); world.add(core);
  const coreGeometry = new THREE.TorusKnotGeometry(.38, .08, 120, 5, 2, 3);
  core.add(new THREE.LineSegments(new THREE.WireframeGeometry(coreGeometry), lineMaterial('teal', .24))); coreGeometry.dispose();
  const wobble = new THREE.Quaternion(), spin = new THREE.Quaternion(), euler = new THREE.Euler();
  const axis = new THREE.Vector3(0, 1, 0);
  function update(time) {
    const cycle = TAU * time / 32;
    rings.forEach(ring => {
      euler.set(.13 * Math.sin(cycle + ring.phase), 0, .10 * Math.cos(cycle + ring.phase));
      wobble.setFromEuler(euler); spin.setFromAxisAngle(axis, cycle * ring.direction + ring.phase);
      ring.group.quaternion.copy(ring.base).multiply(wobble).multiply(spin);
      ring.group.position.y = .06 * Math.sin(cycle + ring.phase);
    });
    core.rotation.set(.3 + .1 * Math.sin(cycle), cycle, .2);
  }
  update(0);
  return { scene, camera, update, setTheme(theme) { applyPalette(scene, theme); },
    resize(w, h) { camera.aspect = w / h; camera.position.z = w / h < .9 ? 18.7 : 17.1; camera.updateProjectionMatrix(); },
    setQuality() {}, dispose() { pointGeometry.dispose(); disposeScene(scene); }, kind: 'wheel', cycleSeconds: 32 };
}

// Four continuous, parameterized fiber sheets converge around a folded toroidal
// core. All vertices are generated deterministically; there is no random star field.
function foldedCore() {
  // A smoothly bounded Schwarz-P-inspired level set: three intersecting passages
  // form one connected, multiply perforated surface rather than overlapping rings.
  // Marching tetrahedra is evaluated once during initialization, never per frame.
  const size=32, bound=1.72, step=bound*2/size, vertices=[], lines=[];
  const corners=[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]];
  const tetrahedra=[[0,5,1,6],[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6]];
  const edges=[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]];
  const value=(x,y,z)=>Math.cos(x*2.6)+Math.cos(y*2.6)+Math.cos(z*2.6)+.13*Math.sin(x*2+y*1.8-z*2.1);
  function emit(a,b,c){
    const center=[(a[0]+b[0]+c[0])/3,(a[1]+b[1]+c[1])/3,(a[2]+b[2]+c[2])/3];
    if(Math.hypot(...center)>1.72)return;
    const clip=p=>{const r=Math.hypot(...p);return r>1.70?p.map(v=>v*1.70/r):p;};
    a=clip(a);b=clip(b);c=clip(c);
    vertices.push(...a,...b,...c);lines.push(...a,...b,...b,...c,...c,...a);
  }
  for(let ix=0;ix<size;ix++)for(let iy=0;iy<size;iy++)for(let iz=0;iz<size;iz++){
    const points=corners.map(([x,y,z])=>[-bound+(ix+x)*step,-bound+(iy+y)*step,-bound+(iz+z)*step]);
    const values=points.map(p=>value(...p));
    if(values.every(v=>v<0)||values.every(v=>v>0))continue;
    for(const tetra of tetrahedra){
      const cuts=[];
      for(const [j,k]of edges){
        const ia=tetra[j],ib=tetra[k],a=values[ia],b=values[ib];
        if((a<0)===(b<0))continue;
        const t=a/(a-b);cuts.push(points[ia].map((v,n)=>v+(points[ib][n]-v)*t));
      }
      if(cuts.length===3)emit(...cuts);
      else if(cuts.length===4){
        const center=new THREE.Vector3();cuts.forEach(p=>center.add(new THREE.Vector3(...p)));center.multiplyScalar(.25);
        const basis=new THREE.Vector3(...cuts[0]).sub(center).normalize();
        const normal=new THREE.Vector3().crossVectors(basis,new THREE.Vector3(...cuts[1]).sub(center)).normalize();
        const other=new THREE.Vector3().crossVectors(normal,basis);
        cuts.sort((a,b)=>{const va=new THREE.Vector3(...a).sub(center),vb=new THREE.Vector3(...b).sub(center);return Math.atan2(va.dot(other),va.dot(basis))-Math.atan2(vb.dot(other),vb.dot(basis));});
        emit(cuts[0],cuts[1],cuts[2]);emit(cuts[0],cuts[2],cuts[3]);
      }
    }
  }
  // Dedupe point samples so shared triangle corners don't become overbright dots.
  const unique=new Map();
  for(let i=0;i<vertices.length;i+=3){const p=vertices.slice(i,i+3),key=p.map(v=>Math.round(v*10000)).join(',');if(!unique.has(key))unique.set(key,p);}
  return {points:[...unique.values()].flat(),lines};
}
function wingPoint(u, v, index) {
  const angles = [.18, 2.94, 3.68, 5.94];
  const angle = angles[index], length = 1.3 + 5.0 * u;
  const spread = (.14 + u * 1.0) * v;
  const curve = .44 * Math.sin(u * Math.PI * 1.6 + index * .8);
  const x = Math.cos(angle) * length - Math.sin(angle) * (spread + curve);
  const y = Math.sin(angle) * length + Math.cos(angle) * (spread + curve);
  const z = .18 + .75 * Math.sin(u * TAU + index * 1.2) * Math.sin(u * Math.PI) + .28 * Math.sin(v * 3.2 + u * 4 + index);
  return [x, y * .84, z];
}
const deformation = `
  uniform float uCompact;
  vec3 flow(vec3 p, float t) {
    // On narrow viewports only the outer fiber sheets fold inward. The central
    // geometry retains its proportions; no whole-scene CSS stretch is used.
    p.x *= 1. - .44 * uCompact * smoothstep(1.2, 5., length(p.xy));
    p.y *= 1. + .1 * uCompact;
    float envelope = .28 + .72 * smoothstep(1., 5., length(p.xy));
    p.z += envelope * (.075 * sin(p.x * 1.6 + p.y * .9 - t * .63) + .045 * cos(p.y * 2.5 + t * .39));
    p.y += .035 * sin(p.x * 1.8 - t * .51);
    return p;
  }
`;
function fieldMaterial(points, opacity, size = 2) {
  return new THREE.ShaderMaterial({ transparent: true, depthWrite: false,
    uniforms: { uTime: { value: 0 }, uColor: { value: new THREE.Color() }, uOpacity: { value: opacity }, uDpr: { value: 1 }, uSize: { value: size }, uLight: { value: 0 }, uCompact: { value: 0 } },
    vertexShader: `uniform float uTime; uniform float uSize; uniform float uDpr; varying float vDepth; ${deformation}
      void main(){ vec3 p=flow(position,uTime); vec4 mv=modelViewMatrix*vec4(p,1.); vDepth=clamp((mv.z+19.)/10.,.15,1.); gl_Position=projectionMatrix*mv; ${points ? 'gl_PointSize=clamp(uSize*uDpr*(12./-mv.z),.8,4.5);' : ''} }`,
    fragmentShader: `uniform vec3 uColor; uniform float uOpacity; uniform float uLight; varying float vDepth;
      void main(){ float a=uOpacity*(.35+.65*vDepth); ${points ? 'float r=length(gl_PointCoord-.5); if(r>.5) discard; a*=1.-smoothstep(.05,.5,r);' : ''} gl_FragColor=vec4(uColor,a); \n #include <tonemapping_fragment> \n #include <colorspace_fragment> }`,
  });
}
export function createField() {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 2.7, .1, 100);
  camera.position.set(.4, -3.9, 11.8); camera.lookAt(0, 0, 0);
  const world = new THREE.Group(); world.rotation.x = -.18; scene.add(world);
  const materials = [], pointSets = [];
  function surface(fn, nu, nv, key, isCore = false) {
    const positions = [], lines = [];
    for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) positions.push(...fn(i / nu, j / nv));
    const p = (i, j) => (i * (nv + 1) + j) * 3;
    for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
      const a = p(i,j), b = p(i+1,j), c = p(i,j+1);
      // Dense longitudinal fibers, lighter transverse sampling, avoiding solid grids.
      if (j % (isCore ? 2 : 2) === 0) lines.push(...positions.slice(a,a+3), ...positions.slice(b,b+3));
      if (i % (isCore ? 3 : 6) === 0) lines.push(...positions.slice(a,a+3), ...positions.slice(c,c+3));
    }
    const geometry = new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(positions,3));
    const indices=[];for(let parity=0;parity<2;parity++)for(let i=parity;i<positions.length/3;i+=2)indices.push(i);geometry.setIndex(indices);
    const mat = fieldMaterial(true, isCore ? .9 : .75, isCore ? 2.4 : 2.0); mat.userData.fieldKey = key;mat.userData.outer=true; materials.push(mat);
    const dots = new THREE.Points(geometry,mat); world.add(dots); pointSets.push({ geometry, total: positions.length/3 });
    const lineMat = fieldMaterial(false,isCore ? .24 : .17); lineMat.userData.fieldKey=key;lineMat.userData.outer=true; materials.push(lineMat);
    world.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(lines,3)),lineMat));
  }
  const core=foldedCore();
  const coreGeometry=new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(core.points,3));
  const corePointMaterial=fieldMaterial(true,.56,1.8);corePointMaterial.userData.fieldKey='bright';materials.push(corePointMaterial);
  const coreLineMaterial=fieldMaterial(false,.07);coreLineMaterial.userData.fieldKey='teal';materials.push(coreLineMaterial);
  const coreGroup=new THREE.Group();coreGroup.rotation.set(.3,-.55,.3);coreGroup.scale.setScalar(.92);
  coreGroup.add(new THREE.Points(coreGeometry,corePointMaterial));
  coreGroup.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(core.lines,3)),coreLineMaterial));world.add(coreGroup);
  for(let i=0;i<4;i++) surface((u,v)=>wingPoint(u,v*2-1,i),100,40,i%2?'teal':'line');
  for(const index of [0,2]){
    const trajectory=[];for(let i=0;i<=160;i++)trajectory.push(...wingPoint(i/160,.22,index));
    const mat=fieldMaterial(false,.42);mat.userData.fieldKey='gold';mat.userData.outer=true;materials.push(mat);
    world.add(new THREE.Line(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(trajectory,3)),mat));
  }
  const flowGeometry = new THREE.BufferGeometry();
  const flowPositions = new Float32Array(24*3); flowGeometry.setAttribute('position',new THREE.BufferAttribute(flowPositions,3));
  const flowMaterial=fieldMaterial(true,.95,4.4);flowMaterial.userData.fieldKey='gold';flowMaterial.userData.outer=true;materials.push(flowMaterial);
  world.add(new THREE.Points(flowGeometry,flowMaterial));
  function update(time) {
    materials.forEach(m=>{m.uniforms.uTime.value=time;});
    // Only 24 trajectory samples are updated; the 26k-vertex sheets deform on GPU.
    for(let i=0;i<24;i++) {
      const u=(time/22+i/6)%1, p=wingPoint(u,Math.sin(i*2.4)*.74,i%4);
      flowPositions[i*3]=p[0];flowPositions[i*3+1]=p[1];flowPositions[i*3+2]=p[2]+.025;
    }
    flowGeometry.attributes.position.needsUpdate=true;
  }
  update(0);
  return {scene,camera,update,kind:'field',cycleSeconds:32,
    setTheme(theme){const p=PALETTES[theme]||PALETTES.dark;materials.forEach(m=>{m.uniforms.uColor.value.setHex(p[m.userData.fieldKey]);m.uniforms.uLight.value=theme==='light'?1:0;});},
    resize(w,h){
      camera.aspect=w/h;const compact=camera.aspect<1.5;
      camera.position.set(.4,compact?-2.2:-3.9,compact?13.5:11.8);
      camera.lookAt(0,compact?-.7:0,0);camera.updateProjectionMatrix();
      materials.forEach(m=>{m.uniforms.uCompact.value=compact&&m.userData.outer?1:0;});
    },
    setQuality(level,dpr){materials.forEach(m=>m.uniforms.uDpr.value=dpr);pointSets.forEach(({geometry,total})=>geometry.setDrawRange(0,level==='low'?Math.ceil(total*.5):total));},
    dispose(){disposeScene(scene);},
  };
}

export function createRenderer(canvas) {
  const renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,powerPreference:'low-power',preserveDrawingBuffer:false});
  renderer.setClearColor(0x000000,0);renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
  renderer.debug.onShaderError=()=>{throw new Error('Scientific visual shader could not compile.');};
  return renderer;
}
