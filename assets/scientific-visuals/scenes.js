/* Instrument structure adapted from celestial-wheel (MIT); see NOTICE.md.
 * All surfaces, networks and animation here are conceptual artwork, not data. */
import * as THREE from '../vendor/three-r186/three.module.js';
const TAU=Math.PI*2;
export const PALETTES={
  dark:{ink:0x07111c,line:0x8aaec9,bright:0xe2f5ff,teal:0x70c9e1,gold:0xd2ad73,metal:0x8095a7,silver:0xc2d0df,glass:0x86c9e5},
  light:{ink:0xf3f6f8,line:0x355b72,bright:0x14394d,teal:0x327d91,gold:0x977044,metal:0x526f85,silver:0x7894a8,glass:0x4b829b},
};
function colorMaterial(material,key,opacity=1){material.userData.paletteKey=key;material.userData.baseOpacity=opacity;return material;}
function lineMaterial(key,opacity){return colorMaterial(new THREE.LineBasicMaterial({transparent:true,opacity,depthWrite:false}),key,opacity);}
function metalMaterial(key='metal',roughness=.32){return colorMaterial(new THREE.MeshStandardMaterial({metalness:.78,roughness}),key);}
function circle(r,material,segments=256,start=0,end=TAU,y=0){
  const p=new Float32Array((segments+1)*3);
  for(let i=0;i<=segments;i++){const a=start+i/segments*(end-start);p[i*3]=Math.cos(a)*r;p[i*3+1]=y;p[i*3+2]=Math.sin(a)*r;}
  return new THREE.Line(new THREE.BufferGeometry().setAttribute('position',new THREE.BufferAttribute(p,3)),material);
}
function disposeScene(scene){const gs=new Set(),ms=new Set();scene.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material)(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>ms.add(m));});gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());}
function applyPalette(scene,theme){const p=PALETTES[theme]||PALETTES.dark;scene.fog?.color.setHex(p.ink);scene.traverse(o=>{const m=o.material;if(!m)return;if(m.userData.paletteKey){m.color?.setHex(p[m.userData.paletteKey]);if(m.emissive){m.emissive.setHex(p[m.userData.paletteKey]);m.emissiveIntensity=m.userData.emission??(theme==='light'?.018:.045);}if(m.transparent)m.opacity=m.userData.baseOpacity*(theme==='light'?.86:1);}if(m.userData.glass){m.uniforms.uColor.value.setHex(p.glass);m.uniforms.uLight.value=theme==='light'?1:0;}});}
function pointerMotion(world,baseX=0){const target={x:0,y:0},current={x:0,y:0};return{set(x,y){target.x=THREE.MathUtils.clamp(Number(x)||0,-1,1);target.y=THREE.MathUtils.clamp(Number(y)||0,-1,1);},step(dt){const a=1-Math.exp(-Math.max(0,Math.min(dt||0,.08))*5.5);current.x+=(target.x-current.x)*a;current.y+=(target.y-current.y)*a;world.rotation.set(baseX+current.y*.035,current.x*.055,-current.x*.012);}};}
function bevelRing(radius,width,depth,material){
  const r0=radius-width/2,r1=radius+width/2,h=depth/2,b=Math.min(width*.2,depth*.3);
  const profile=[[r0+b,-h],[r1-b,-h],[r1,-h+b],[r1,h-b],[r1-b,h],[r0+b,h],[r0,h-b],[r0,-h+b],[r0+b,-h]].map(p=>new THREE.Vector2(...p));
  return new THREE.Mesh(new THREE.LatheGeometry(profile,256),material);
}
function glassShell(radius){
  const material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.FrontSide,
    uniforms:{uColor:{value:new THREE.Color()},uLight:{value:0}},
    vertexShader:'varying vec3 vNormal; varying vec3 vView; void main(){vec4 p=modelViewMatrix*vec4(position,1.);vNormal=normalize(normalMatrix*normal);vView=-p.xyz;gl_Position=projectionMatrix*p;}',
    fragmentShader:`uniform vec3 uColor;uniform float uLight;varying vec3 vNormal;varying vec3 vView;
      void main(){vec3 n=normalize(vNormal),v=normalize(vView);float facing=max(dot(n,v),0.);float edge=pow(1.-facing,2.7);float glint=pow(max(dot(reflect(-normalize(vec3(-.5,.8,1.)),n),v),0.),48.);vec3 c=mix(uColor,vec3(1.),glint*.8);float a=.026+edge*.38+glint*.38;gl_FragColor=vec4(c,a*(1.-uLight*.2));
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`});material.userData.glass=true;
  return new THREE.Mesh(new THREE.SphereGeometry(radius,64,40),material);
}
function lights(scene){scene.add(new THREE.HemisphereLight(0xcceeff,0x10243b,2.0));const key=new THREE.DirectionalLight(0xf0f5ff,4.3);key.position.set(-4,7,7);scene.add(key);const rim=new THREE.DirectionalLight(0x74c4eb,3.3);rim.position.set(6,1,-4);scene.add(rim);const fill=new THREE.DirectionalLight(0xe4bd83,1.05);fill.position.set(-5,-3,2);scene.add(fill);}

export function createWheel(){
  const scene=new THREE.Scene();scene.fog=new THREE.Fog(PALETTES.dark.ink,17,31);lights(scene);
  const camera=new THREE.PerspectiveCamera(36,1,.1,100);camera.position.set(1.4,5.9,17.5);camera.lookAt(0,0,0);
  const world=new THREE.Group();scene.add(world);const pointer=pointerMotion(world);
  const silver=metalMaterial(),pale=metalMaterial('silver',.25),gold=metalMaterial('gold',.38);
  const nodeMaterial=colorMaterial(new THREE.MeshStandardMaterial({metalness:.3,roughness:.2,emissiveIntensity:.7}),'bright');nodeMaterial.userData.emission=.7;
  const nodeGeometry=new THREE.SphereGeometry(.062,12,8);
  const definitions=[
    [1.55,.68,-.28,.18,1,.055,.045,'secondary'],
    [2.2,-.65,.55,.86,-1,.07,.05,'secondary'],
    [2.9,.92,-.66,1.6,1,.15,.095,'primary'],
    [3.5,-.9,-.36,2.5,-1,.065,.05,'secondary'],
    [4.08,.38,.8,3.2,1,.105,.075,'primary'],
    [4.64,-.35,-.9,4.4,-1,.045,.04,'secondary'],
    [5.1,1.08,.25,5.2,1,.18,.105,'primary'],
  ];
  const rings=[];
  definitions.forEach(([r,tx,tz,phase,direction,width,depth,tier],i)=>{
    const group=new THREE.Group();world.add(group);const primary=tier==='primary';
    group.add(bevelRing(r,width,depth,i===4?gold:primary?pale:silver));
    // Two inset grooves and a bevel highlight give the broad ring a machined face.
    group.add(circle(r-width*.26,lineMaterial('line',primary?.72:.35),256,0,TAU,depth*.51));
    if(primary)group.add(circle(r+width*.27,lineMaterial(i===4?'gold':'bright',.66),256,0,TAU,depth*.51));
    const marks=[],n=primary?240:120;
    for(let k=0;k<n;k++){const a=k/n*TAU,major=k%12===0;const r0=r+width*.56,r1=r0+(major?.13:k%4===0?.065:.025);marks.push(Math.cos(a)*r0,depth*.55,Math.sin(a)*r0,Math.cos(a)*r1,depth*.55,Math.sin(a)*r1);}
    group.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(marks,3)),lineMaterial(i===4?'gold':'bright',primary?.83:.48)));
    if(primary){
      const arc=new THREE.Mesh(new THREE.TorusGeometry(r-width*.43,.012,6,60,.45),colorMaterial(new THREE.MeshBasicMaterial({transparent:true,opacity:.8}),i===4?'gold':'teal',.8));arc.rotation.x=Math.PI/2;arc.rotation.z=phase;arc.position.y=depth*.6;group.add(arc);
    }
    const base=new THREE.Quaternion().setFromEuler(new THREE.Euler(tx,phase,tz,'YXZ'));
    let node=null;
    if(primary){node=new THREE.Mesh(nodeGeometry,nodeMaterial);group.add(node);}
    rings.push({group,base,phase,direction,r,depth,node});
  });
  // Remote rings remain fine and dim; they are not styled like the metal carriers.
  [[5.48,.8,.3],[5.62,-.6,-.45],[4.9,.2,1.15]].forEach(([r,tx,tz],i)=>{const orbit=circle(r,lineMaterial('line',i===2?.11:.2));orbit.rotation.set(tx,0,tz);world.add(orbit);});
  const core=new THREE.Group();world.add(core);core.add(glassShell(1.04));
  const cageGeometry=new THREE.IcosahedronGeometry(.73,0);
  core.add(new THREE.LineSegments(new THREE.EdgesGeometry(cageGeometry),lineMaterial('bright',.7)));
  const cageNodes=new THREE.Points(cageGeometry,new THREE.PointsMaterial({color:PALETTES.dark.teal,size:.045,transparent:true,opacity:.8}));colorMaterial(cageNodes.material,'teal',.8);core.add(cageNodes);
  const nucleus=new THREE.Mesh(new THREE.IcosahedronGeometry(.35,1),metalMaterial('teal',.22));core.add(nucleus);
  const inner=new THREE.Group();core.add(inner);
  [[.87,.2,.6],[.89,1.1,-.4]].forEach(([r,x,z])=>{const band=circle(r,lineMaterial('teal',.32),160);band.rotation.set(x,0,z);inner.add(band);});
  const axis=new THREE.Vector3(0,1,0),wobble=new THREE.Quaternion(),spin=new THREE.Quaternion(),euler=new THREE.Euler();
  function update(time,dt=0){const c=TAU*time/32;pointer.step(dt);rings.forEach(r=>{euler.set(.12*Math.sin(c+r.phase),0,.09*Math.cos(c+r.phase));wobble.setFromEuler(euler);spin.setFromAxisAngle(axis,c*r.direction+r.phase);r.group.quaternion.copy(r.base).multiply(wobble).multiply(spin);r.group.position.y=.05*Math.sin(c+r.phase);if(r.node){const a=c*r.direction*1.6+r.phase;r.node.position.set(Math.cos(a)*r.r,r.depth*.75,Math.sin(a)*r.r);}});nucleus.rotation.set(.22,time*.055,.3);inner.rotation.y=time*.07;}
  update(0);
  return{scene,camera,update,kind:'wheel',cycleSeconds:32,setPointer:(x,y)=>pointer.set(x,y),
    setTheme(theme){applyPalette(scene,theme);},
    resize(w,h){camera.aspect=w/h;camera.position.set(1.4,5.9,w/h<.9?19.1:17.5);camera.lookAt(0,0,0);camera.updateProjectionMatrix();},
    setQuality(){},dispose(){disposeScene(scene);}};
}

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
  return {points:[...unique.values()].flat(),lines,triangles:vertices};
}


function sheetPoint(u,v,index){
  const side=index<3?-1:1,layer=index%3;
  const length=1.25+5.1*u,spread=(.12+u*.95)*v;
  const y=(layer-1)*(.3+.76*u)+.48*Math.sin(u*Math.PI*1.65+layer*.9+side*.5)+spread;
  const z=(layer-1)*1.14+.7*Math.sin(u*TAU+v*1.3+layer*.8)*Math.sin(u*Math.PI)+.24*Math.cos(v*3+u*4);
  return[side*length,y,z];
}
const deformation=`uniform float uCompact;
vec3 flow(vec3 p,float t){float outer=smoothstep(1.3,5.4,abs(p.x));p.x*=1.-.45*uCompact*outer;p.y*=1.+.3*uCompact*outer;p.z+=.11*sin(p.x*1.3+p.y*.8-t*.55)+.05*cos(p.y*2.3+t*.31);p.y+=.055*sin(p.x*1.6-t*.43);return p;}`;
function fieldMaterial(points,opacity,size=2){return new THREE.ShaderMaterial({transparent:true,depthWrite:false,
  uniforms:{uTime:{value:0},uColor:{value:new THREE.Color()},uOpacity:{value:opacity},uDpr:{value:1},uSize:{value:size},uCompact:{value:0},uLight:{value:0},uPulse:{value:0},uEdgeFade:{value:0}},
  vertexShader:`uniform float uTime,uSize,uDpr;varying float vDepth;varying float vPulse;varying float vEdge;${deformation}
    void main(){vec3 p=flow(position,uTime);vec4 mv=modelViewMatrix*vec4(p,1.);vDepth=clamp((mv.z+19.)/9.,.1,1.);vPulse=pow(max(0.,sin(position.x*.85-uTime*.55)),12.);vEdge=smoothstep(1.25,1.7,abs(position.x))*(1.-smoothstep(5.75,6.35,abs(position.x)));gl_Position=projectionMatrix*mv;${points?'gl_PointSize=clamp(uSize*uDpr*(12./-mv.z),.8,9.);':''}}`,
  fragmentShader:`uniform vec3 uColor;uniform float uOpacity,uLight,uPulse,uEdgeFade;varying float vDepth,vPulse,vEdge;
    void main(){float a=uOpacity*(.2+.8*vDepth)*(1.+uPulse*vPulse*.6)*mix(1.,vEdge,uEdgeFade);${points?'float r=length(gl_PointCoord-.5);if(r>.5)discard;a*=1.-smoothstep(.03,.5,r);':''}gl_FragColor=vec4(uColor,a);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
    }`});}
export function createField(){
  const scene=new THREE.Scene();lights(scene);
  const camera=new THREE.PerspectiveCamera(34,2.7,.1,100);
  const world=new THREE.Group();scene.add(world);const pointer=pointerMotion(world,-.1);
  const materials=[],pointSets=[];
  function addMaterial(points,opacity,size,key,outer=true){const m=fieldMaterial(points,opacity,size);m.userData.fieldKey=key;m.userData.outer=outer;materials.push(m);return m;}
  function addPoints(positions,material){const g=new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(positions,3));const indices=[];for(let n=0;n<2;n++)for(let i=n;i<positions.length/3;i+=2)indices.push(i);g.setIndex(indices);world.add(new THREE.Points(g,material));pointSets.push({geometry:g,total:positions.length/3});return g;}
  function surface(index){
    const nu=100,nv=32,positions=[],lines=[];
    for(let i=0;i<=nu;i++)for(let j=0;j<=nv;j++)positions.push(...sheetPoint(i/nu,j/nv*2-1,index));
    const p=(i,j)=>(i*(nv+1)+j)*3;
    for(let i=0;i<nu;i++)for(let j=0;j<nv;j++){const a=p(i,j),b=p(i+1,j),c=p(i,j+1);if(j%2===0)lines.push(...positions.slice(a,a+3),...positions.slice(b,b+3));if(i%8===0)lines.push(...positions.slice(a,a+3),...positions.slice(c,c+3));}
    const layer=index%3,key=layer===2?'bright':layer===1?'teal':'line';
    const pm=addMaterial(true,[.34,.65,.82][layer],[1.5,1.9,2.4][layer],key);pm.uniforms.uPulse.value=.3;addPoints(positions,pm);
    const lm=addMaterial(false,[.1,.2,.32][layer],1,key);lm.uniforms.uPulse.value=.6;
    world.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(lines,3)),lm));
  }
  for(let i=0;i<6;i++)surface(i);
  const core=foldedCore(),coreGroup=new THREE.Group();coreGroup.rotation.set(.22,-.55,.3);coreGroup.scale.setScalar(.97);world.add(coreGroup);
  const coreG=new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(core.points,3));
  coreGroup.add(new THREE.Points(coreG,addMaterial(true,.72,2.1,'bright',false)));
  coreGroup.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(core.lines,3)),addMaterial(false,.1,1,'teal',false)));
  // A subtle lit skin gives the network depth without closing its open passages.
  const skinGeometry=new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(core.triangles,3));skinGeometry.computeVertexNormals();
  const skin=colorMaterial(new THREE.MeshStandardMaterial({transparent:true,opacity:.12,depthWrite:false,side:THREE.DoubleSide,metalness:.3,roughness:.42}),'teal',.12);coreGroup.add(new THREE.Mesh(skinGeometry,skin));
  const inner=new THREE.Mesh(new THREE.IcosahedronGeometry(.23,1),metalMaterial('gold',.28));coreGroup.add(inner);
  const innerCage=new THREE.IcosahedronGeometry(.58,0);coreGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(innerCage),lineMaterial('gold',.42)));innerCage.dispose();
  // Six sparse, three-dimensional node clusters sit at distinct depths. Their
  // anchor positions come from the wave geometry, never a random star volume.
  const satellites=[],hubs=[],links=[];
  for(const side of [0,3])for(let cluster=0;cluster<3;cluster++){
    const u=[.24,.5,.77][cluster],index=side+(cluster===1?1:2);
    const anchor=sheetPoint(u,[-.32,.28,-.18][cluster],index);anchor[2]+=.5;
    hubs.push(...anchor);
    const nodes=[];
    for(let j=0;j<6;j++){
      const a=j/6*TAU+cluster*.38;
      const node=[anchor[0]+Math.cos(a)*(.28+cluster*.035),anchor[1]+Math.sin(a)*.31,anchor[2]+Math.sin(a*2+cluster)*.32];
      nodes.push(node);satellites.push(...node);links.push(...anchor,...node);
    }
    for(let j=0;j<6;j++)if(j%3!==0)links.push(...nodes[j],...nodes[(j+1)%6]);
    if(cluster<2){const next=sheetPoint([.5,.77][cluster],.1,side+(cluster===0?1:2));next[2]+=.5;links.push(...anchor,...next);}
  }
  addPoints(satellites,addMaterial(true,1,6.1,'bright'));
  addPoints(hubs,addMaterial(true,1,8.2,'gold'));
  world.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(links,3)),addMaterial(false,.56,1,'line')));
  for(const index of [1,5]){const p=[];for(let i=0;i<=160;i++)p.push(...sheetPoint(i/160,.18,index));const m=addMaterial(false,.62,1,'gold');world.add(new THREE.Line(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(p,3)),m));}
  const flowGeometry=new THREE.BufferGeometry(),flowPositions=new Float32Array(24*3);flowGeometry.setAttribute('position',new THREE.BufferAttribute(flowPositions,3));
  const pulseMaterial=addMaterial(true,1,6.8,'gold');pulseMaterial.uniforms.uEdgeFade.value=1;world.add(new THREE.Points(flowGeometry,pulseMaterial));
  function update(time,dt=0){pointer.step(dt);materials.forEach(m=>m.uniforms.uTime.value=time);for(let i=0;i<24;i++){const index=i%6,u=(time/24+Math.floor(i/6)*.25)%1,p=sheetPoint(u,.18,index);flowPositions[i*3]=p[0];flowPositions[i*3+1]=p[1];flowPositions[i*3+2]=p[2]+.035;}flowGeometry.attributes.position.needsUpdate=true;inner.rotation.y=time*.08;}
  update(0);
  return{scene,camera,update,kind:'field',cycleSeconds:32,setPointer:(x,y)=>pointer.set(x,y),
    setTheme(theme){const p=PALETTES[theme]||PALETTES.dark;applyPalette(scene,theme);materials.forEach(m=>{m.uniforms.uColor.value.setHex(p[m.userData.fieldKey]);m.uniforms.uLight.value=theme==='light'?1:0;});},
    resize(w,h){camera.aspect=w/h;const compact=camera.aspect<1.5;camera.position.set(.3,compact?-2.6:-4.4,compact?12.5:12.7);camera.lookAt(0,compact?-.1:0,0);camera.updateProjectionMatrix();materials.forEach(m=>m.uniforms.uCompact.value=compact&&m.userData.outer?1:0);},
    setQuality(level,dpr){materials.forEach(m=>m.uniforms.uDpr.value=dpr);pointSets.forEach(({geometry,total})=>geometry.setDrawRange(0,level==='low'?Math.ceil(total*.5):total));},
    dispose(){disposeScene(scene);}};
}
export function createRenderer(canvas){const renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,powerPreference:'low-power',preserveDrawingBuffer:false});renderer.setClearColor(0x000000,0);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;renderer.debug.onShaderError=()=>{throw new Error('Scientific visual shader could not compile.');};return renderer;}
