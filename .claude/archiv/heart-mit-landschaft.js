// Herz-Szene (three.js) nach der Foto-Galerie – im Kissen-Loch eine Punkt-Landschaft (Ref aboutluca.com: Gelände aus
// Partikeln, Kamera fliegt hindurch). Darin liegt das Palermo-Foto (assets/raw/P1000690) als feines Punkt-Relief: jeder
// Punkt auf dem Sehstrahl der Foto-Kamera PC (Straße = Boden, Fassaden senkrecht, Stadt/Berge immer weiter weg) –
// von PC aus sieht es genau aus wie das Foto. Drumherum: Ebene vorn (kleiner Hügel links), links endet die Stadt
// (Häuser dünnen aus), das Gelände steigt über Hügel zu einer Bergkette, die nach links weiterläuft (rechts kürzer).
// Davor schwebt der Glaswürfel (wie chasing-the-moment.byholm.co: three-Transmission + Klarlack + Studio-Umgebung)
// mit dem schwarzen Punkt-Herz. Nachgeladen von startpage.html (loadHeart); der Director setzt window.__heart = { t: 0..1 }.
// Ablauf in t: 0–0.15 Szene + Würfel erscheinen · 0.15–1 Kamerafahrt von der Ebene zum Würfel (frontal vor dem Herz);
// das Herz setzt sich während der Fahrt zusammen.

import * as THREE from 'three';

const holder = document.getElementById('heart3d');
const renderer = new THREE.WebGLRenderer({ alpha:true, antialias:true });
renderer.setPixelRatio(Math.min(devicePixelRatio||1, 2));
renderer.setClearColor(0xECE6EA, 1);                 // = Loch-Hintergrund (Himmel); deckend -> Glas bricht kein Weiß
holder.appendChild(renderer.domElement);

const scene  = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, 1, 0.05, 400);

let rs = 7; const rnd = ()=>((rs = (rs*16807) % 2147483647) / 2147483647);   // fester Zufall
const smooth = (t)=>t*t*(3-2*t), cl = (v,a,b)=>Math.max(a,Math.min(b,v)), DEG = Math.PI/180;
const sstep = (a,b,x)=>smooth(cl((x-a)/(b-a), 0, 1));
const loadPx = async (src)=>{ const im = new Image(); im.src = src; await im.decode();
  const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
  const x = c.getContext('2d', { willReadFrequently:true }); x.drawImage(im, 0, 0);
  return { W:im.width, H:im.height, px:x.getImageData(0, 0, im.width, im.height).data }; };
// 1D-Rauschen (für Bergkämme und Hügel)
const hash = (n)=>{ const s = Math.sin(n*127.1)*43758.5453; return s - Math.floor(s); };
const noise1 = (x)=>{ const i = Math.floor(x), f = x - i; return hash(i) + (hash(i+1) - hash(i))*smooth(f); };
const fbm = (x)=>0.5*noise1(x) + 0.25*noise1(x*2.1+7) + 0.125*noise1(x*4.3+13) + 0.0625*noise1(x*8.7+29);
const ridge = (x)=>{ let v = 0, a = 0.55, f = 1; for(let o = 0; o < 4; o++){ v += a*(1 - Math.abs(2*noise1(x*f + o*17) - 1)); a *= 0.5; f *= 2.05; } return v; };

// ---------- Studio-Umgebung (wie RoomEnvironment): Raum + Leuchtflächen -> Spiegelungen auf dem Glas ----------
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = (function room(){
  const s = new THREE.Scene();
  s.add(new THREE.Mesh(new THREE.BoxGeometry(10,10,10), new THREE.MeshBasicMaterial({ color:0x4d4a52, side:THREE.BackSide })));
  const lamp = (w,h,d,x,y,z,i)=>{ const m = new THREE.Mesh(new THREE.BoxGeometry(w,h,d),
    new THREE.MeshBasicMaterial({ color:new THREE.Color(i,i,i) })); m.position.set(x,y,z); s.add(m); };
  lamp(4,0.2,4, 0,4.8,0, 2.2); lamp(0.2,2.6,3.2, -4.8,1,0.6, 4.5); lamp(0.2,2.2,2.6, 4.8,1.6,-1.2, 3.2); lamp(3.2,1.8,0.2, 0,1.6,-4.8, 2.6);
  lamp(2.4,1.5,0.2, -1.8,2.3,4.8, 6); lamp(0.9,3.2,0.2, 2.7,0.4,4.8, 4);   // hinter der Kamera -> Glanz auf den vorderen Flächen
  return pmrem.fromScene(s, 0.04).texture;
})();
scene.add(new THREE.AmbientLight(0xffffff, 0.9));
const l1 = new THREE.DirectionalLight(0xffffff, 1.5); l1.position.set(2,3,4);  scene.add(l1);
const l2 = new THREE.DirectionalLight(0xffffff, 1.1); l2.position.set(-3,2,-2); scene.add(l2);

// ---------- Foto-Kamera (Standpunkt des Fotos) ----------
const H0 = 4;                                         // Höhe über der Straße
const PC = new THREE.Vector3(0, H0, 12);
const PITCH = -11.7*DEG, VFOV_P = 38*DEG;             // Horizont liegt im Foto bei ~16 % von oben
const F  = new THREE.Vector3(0, Math.sin(PITCH), -Math.cos(PITCH));
const UP = new THREE.Vector3(0, Math.cos(PITCH),  Math.sin(PITCH));
const FS = new THREE.Vector3(0, Math.sin(-8.7*DEG), -Math.cos(-8.7*DEG));
const HALF_AZ = Math.atan(Math.tan(VFOV_P/2)*1500/1126);   // halber Bildwinkel des Fotos (≈ 24.7°)

// Würfel: schwebt vor der Stadt, etwas links der Mitte; Kamera endet frontal davor
const C = PC.clone().addScaledVector(FS, 4.6).add(new THREE.Vector3(-0.5, 0, 0));
const SIDE = 0.9, HEART_H = 0.8;
const CAM_END   = C.clone().addScaledVector(PC.clone().sub(C).normalize(), 2.4);
const CAM_START = new THREE.Vector3(0.5, 3.3, 20.5);  // weiter hinten über der Ebene, nahe der Blickachse des Fotos

// ---------- Landschaft (Relief + Ebene + Gelände/Berge) – ein Punkt-Material ----------
const land = { uPx:{value:800}, uReveal:{value:0} };
const landMat = new THREE.ShaderMaterial({
  uniforms: land,
  vertexShader: `
    attribute float aSize, aShade, aDelay;
    uniform float uPx, uReveal;
    varying float vShade, vFog;
    void main(){
      float k = clamp((uReveal - aDelay*0.6)/0.4, 0.0, 1.0); k = k*k*(3.0-2.0*k);
      vec4 mv = modelViewMatrix*vec4(position, 1.0);
      float sz = aSize*uPx/-mv.z*k;
      gl_PointSize = clamp(sz, 1.0, 6.0);
      gl_Position = sz < 0.35 ? vec4(2.0, 2.0, 2.0, 1.0) : projectionMatrix*mv;
      vShade = aShade; vFog = smoothstep(25.0, 170.0, -mv.z)*0.55;       // Dunst zu den Bergen
    }`,
  fragmentShader: `
    varying float vShade, vFog;
    void main(){
      vec2 c = gl_PointCoord - 0.5; if(dot(c,c) > 0.25) discard;
      vec3 col = mix(vec3(0.85,0.75,0.62), vec3(0.47,0.34,0.22), vShade);   // hellbraun (dunkle Stellen etwas kräftiger)
      col = mix(col, vec3(0.925,0.902,0.918), vFog);
      gl_FragColor = vec4(pow(col, vec3(2.2)), 1.0);                      // linear -> im Glas (Render-Target) richtig hell
      #include <colorspace_fragment>
    }`,
});

let landReady = false, landPts = null;
(async function buildLand(){
  const P = [], SZ = [], SH = [], DL = [];
  const add = (x,y,z,size,shade)=>{ P.push(x,y,z); SZ.push(size); SH.push(shade); DL.push(rnd()); };

  // 1) Palermo-Relief auf den Sehstrahlen des Fotos. An beiden Rändern geht die Stadt mit gespiegelten Häusern weiter
  //    (füllt die Lücke neben den vorderen Fassaden), wird dabei niedriger und lockerer und läuft ins Gelände aus
  const { W, H, px } = await loadPx('assets/img/palermo-relief.png');
  const tanV = Math.tan(VFOV_P/2), tanH = tanV*W/H, EXT = 0.34, VG = 0.888;
  const d = new THREE.Vector3();
  const dirAt = (u,v)=>{ const yc = (1-2*v)*tanV; return d.set((2*u-1)*tanH, F.y + UP.y*yc, F.z + UP.z*yc); };
  dirAt(0.5, VG); const DF = H0*(-d.z)/(-d.y);        // waagrechter Abstand der Fassaden-Ebene (= Straßenkante)
  const ang = 2*tanV/H, cols = Math.round(W*(1+2*EXT));
  for(let iy = 0; iy < H; iy++) for(let ix = 0; ix < cols; ix++){
    const u = (ix + rnd())/W - EXT, v = (iy + rnd())/H;
    const out = (u < 0 ? -u : u > 1 ? u - 1 : 0)/EXT; // 0 am Bildrand … 1 am Ende der Verlängerung
    if(out > 0){
      if(rnd() < Math.pow(out, 1.3)) continue;                            // lockerer
      if(v < 0.2 + 0.45*smooth(out) - (out < 0.08 ? 0.2 : 0)) continue;    // niedriger (Berge nur direkt am Rand)
    }
    let sx = Math.floor(u*W); if(sx < 0) sx = -sx-1; if(sx >= W) sx = 2*W-1-sx;
    const i = (Math.min(H-1, iy)*W + cl(sx,0,W-1))*4; if(px[i+3] < 128) continue;   // Himmel
    const dk = 1 - px[i]/255;
    if(rnd() > 0.1 + 0.52*Math.pow(dk, 0.95)) continue;              // weniger Punkte (Leistung), etwas größer
    dirAt(u, v);
    const t = v >= VG ? H0/(-d.y) : DF*Math.exp(5.17*Math.max(0, 0.55 - v)*sstep(0.6, 0.48, v))/(-d.z);
    add(PC.x + d.x*t, PC.y + d.y*t, PC.z + d.z*t, t*ang*1.4*(0.75 + 0.8*dk), dk);
  }

  // 2) Ebene vorn (fein, im Blickfeld der Fahrt), kleiner Hügel links; die Straße des Fotos liegt schon im Relief
  const hill = (x,z)=>0.9*Math.exp(-(((x+8)/2.8)**2 + ((z-8)/3.4)**2));
  for(let z = 3.5; z < 26; z += 0.1){
    const hw = 3 + (24 - z)*0.75;
    for(let x = -hw; x < hw; x += 0.1){
      const X = x + (rnd()-0.5)*0.09, Z = z + (rnd()-0.5)*0.09;
      const az = Math.atan2(X - PC.x, PC.z - Z), r = Math.hypot(X - PC.x, PC.z - Z);
      if(Math.abs(az) < HALF_AZ && r > 6.6 && Z < PC.z) continue;         // dort liegt die Foto-Straße
      if(r > 9 && Z < PC.z) continue;                                      // weiter hinten: Gelände (3)
      const h = hill(X,Z);
      add(X, h + (rnd()-0.5)*0.01, Z, 0.028, 0.12 + rnd()*0.12 + h*0.3);
    }
  }

  // 3) Gelände um die Stadt (polar um PC, Abstand ∝ Entfernung): Ebene -> Hügel -> Bergkette; links lang und hoch
  for(let r = 9; r < 125; r += r*0.013){
    for(let a = -118*DEG; a < 78*DEG; a += 0.013){
      const A = a + (rnd()-0.5)*0.012, R = r*(1 + (rnd()-0.5)*0.012);
      const e = Math.abs(A) - HALF_AZ;                                     // Winkel hinter dem Bildrand
      if(e < -0.02) continue;                                              // im Bild: Relief
      const left = A < 0, eD = e/DEG;
      const X = PC.x + Math.sin(A)*R, Z = PC.z - Math.cos(A)*R;
      if(Z > 3.5 && R < 9) continue;
      // Kammlinie: links hoch und zerklüftet (wie die Berge im Foto), rechts kürzer
      const crest = left ? 7 + 9*ridge(A*6.2 + 3.1) + 3*sstep(0, 35, eD) : 5 + 6*ridge(A*6.8 + 11.3);
      const mtn = crest*sstep(40, 78, R)*(0.35 + 0.65*sstep(2, 14, eD)); // am Stadtrand erst flach, dann Berge
      const hills = 1.4*fbm(A*9 + R*0.09)*sstep(10, 32, R)*sstep(-2, 10, eD);
      const y = mtn + hills*(1 - sstep(40, 78, R)*0.5);
      const slope = Math.abs(ridge(A*6.2 + 3.15) - ridge(A*6.2 + 3.05));   // grobe Neigung -> Schattierung
      const shade = cl(0.16 + 0.03*y + 1.6*slope + (rnd()-0.5)*0.12, 0.08, 0.72);
      add(X, y, Z, R*0.013*1.1, shade);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  geo.setAttribute('aSize',  new THREE.Float32BufferAttribute(SZ, 1));
  geo.setAttribute('aShade', new THREE.Float32BufferAttribute(SH, 1));
  geo.setAttribute('aDelay', new THREE.Float32BufferAttribute(DL, 1));
  landPts = new THREE.Points(geo, landMat); landPts.frustumCulled = false; scene.add(landPts);
  landReady = true;
})();

// ---------- Herz: schwarze Zeichnung vorn (gewölbt) + runde, gleichmäßige Rückseite ----------
const objG   = new THREE.Group(); objG.position.copy(C); scene.add(objG);
objG.lookAt(CAM_END);                                                // Vorderseite zeigt zum Fahrtende (kein Drehen)
const floatG = new THREE.Group(); objG.add(floatG);                  // leichtes Schweben (Herz + Würfel)
const heartG = new THREE.Group(); floatG.add(heartG);                // pulsiert
const STEP = 2;
const uni = { uTime:{value:0}, uForm:{value:0}, uPx:{value:800}, uDot:{value:0.004} };
let heartReady = false;
(async function buildHeart(){
  const { W, H, px } = await loadPx('assets/img/heart-ink.png'), S = HEART_H/H;
  const pos = [], start = [], rn = [], ink = [];
  const add = (X,Y,Z,k,size)=>{ pos.push(X,Y,Z);
    const a = rnd()*Math.PI*2, r = 0.25 + rnd()*0.35;               // Start: locker verstreut IM Würfel
    start.push(X*0.4 + Math.cos(a)*r, Y*0.4 + Math.sin(a)*r, Z*0.4 + (rnd()-0.5)*0.5);
    rn.push(rnd()*6.283, 0.35 + rnd()*0.7, rnd(), size); ink.push(k); };
  const prof = (dn)=>Math.sqrt(dn*(2-dn));                           // runder Querschnitt, 0 am Rand
  for(let y = 0; y < H; y += STEP) for(let x = 0; x < W; x += STEP){
    const jx = Math.min(W-1, Math.max(0, Math.round(x + (rnd()-0.5)*STEP*0.9)));
    const jy = Math.min(H-1, Math.max(0, Math.round(y + (rnd()-0.5)*STEP*0.9)));
    const i = (jy*W + jx)*4, k = px[i]/255; if(k < 0.08 || rnd() > Math.pow(k, 0.85)) continue;
    const X = (jx - W/2)*S, Y = -(jy - H/2)*S;
    add(X, Y, 0.12*HEART_H*prof(px[i+1]/255) + (rnd()-0.5)*0.006, 1, 0.62 + 0.5*Math.sqrt(k));   // Vorderseite = Zeichnung
  }
  for(let y = 0; y < H; y += STEP*2) for(let x = 0; x < W; x += STEP*2){   // Rückseite: gleichmäßig, rund, am Rand angesetzt
    const jx = Math.min(W-1, Math.max(0, Math.round(x + (rnd()-0.5)*STEP*1.8)));
    const jy = Math.min(H-1, Math.max(0, Math.round(y + (rnd()-0.5)*STEP*1.8)));
    const i = (jy*W + jx)*4; if(px[i+2] < 128 || rnd() > 0.75) continue;
    add((jx - W/2)*S, -(jy - H/2)*S, -0.22*HEART_H*prof(px[i+1]/255), 0.72, 0.8);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('aStart',   new THREE.Float32BufferAttribute(start, 3));
  geo.setAttribute('aRnd',     new THREE.Float32BufferAttribute(rn, 4));
  geo.setAttribute('aInk',     new THREE.Float32BufferAttribute(ink, 1));
  uni.uDot.value = STEP*S*0.82;
  const shader = {
    uniforms: uni,
    vertexShader: `
      attribute vec3 aStart; attribute vec4 aRnd; attribute float aInk;
      uniform float uTime, uForm, uPx, uDot;
      varying float vInk;
      void main(){
        float k = clamp((uForm - aRnd.z*0.5)/0.5, 0.0, 1.0); k = k*k*(3.0-2.0*k);
        vec3 p = mix(aStart, position, k);
        float t = uTime*aRnd.y;                                       // im Ziel nur noch ganz leichtes Schweben
        p += vec3(sin(t+aRnd.x), cos(t*0.83+aRnd.x*1.7), sin(t*0.61+aRnd.x*2.3)) * mix(0.03, 0.0009, k);
        vec4 mv = modelViewMatrix*vec4(p, 1.0);
        float sz = uDot*aRnd.w*k*uPx / -mv.z;                          // Punkte wachsen beim Zusammensetzen aus dem Nichts
        gl_PointSize = clamp(sz, 1.0, 10.0);
        gl_Position = sz < 0.3 ? vec4(2.0, 2.0, 2.0, 1.0) : projectionMatrix*mv;
        vInk = aInk;
      }`,
    fragmentShader: `
      varying float vInk;
      void main(){
        vec2 c = gl_PointCoord - 0.5; if(dot(c,c) > 0.25) discard;    // runde Mini-Kreise, schwarz
        gl_FragColor = vec4(pow(mix(vec3(0.30,0.29,0.31), vec3(0.03,0.03,0.035), vInk), vec3(2.2)), 1.0);
        #include <colorspace_fragment>
      }`,
  };
  // 1) deckend -> wird vom Glas gebrochen   2) dieselben Punkte NACH dem Glas -> Herz bleibt scharf und schwarz
  heartG.add(new THREE.Points(geo, new THREE.ShaderMaterial(shader)));
  const top = new THREE.Points(geo, new THREE.ShaderMaterial({ ...shader, transparent:true, depthWrite:false }));
  top.renderOrder = 2; heartG.add(top);
  heartG.children.forEach(o=>{ o.frustumCulled = false; });
  heartReady = true; layout();
})();

// ---------- Glaswürfel (Ref byholm „struggle-cube"): Transmission + Klarlack, eng ums Herz, leicht gekippt ----------
const glassMat = new THREE.MeshPhysicalMaterial({
  color:0xffffff, metalness:0, roughness:0.04, transmission:1, thickness:0.35, ior:1.42,
  envMapIntensity:1.0, clearcoat:1, clearcoatRoughness:0, transparent:true, opacity:0, depthWrite:false,
});
const cube = new THREE.Mesh(new THREE.BoxGeometry(SIDE, SIDE, SIDE), glassMat);
cube.rotation.set(12*DEG, 28*DEG, 0); cube.renderOrder = 1; floatG.add(cube);   // Oberseite + zwei Seiten sichtbar
// Kanten: dunkle Linie + helle Glanzlinie knapp innen (auf hellem Grund liest sich der Würfel sonst kaum)
const edgeGeo = new THREE.EdgesGeometry(cube.geometry);
const edgeMat = new THREE.LineBasicMaterial({ color:0x5a5048, transparent:true, opacity:0, depthWrite:false });
const hiMat   = new THREE.LineBasicMaterial({ color:0xffffff, transparent:true, opacity:0, depthWrite:false });
const edges = new THREE.LineSegments(edgeGeo, edgeMat); edges.renderOrder = 3; cube.add(edges);
const hiEdges = new THREE.LineSegments(edgeGeo, hiMat); hiEdges.scale.setScalar(0.985); hiEdges.renderOrder = 4; cube.add(hiEdges);
window.__heartDbg = { glassMat, cube, objG, heartG, land, uni, camera, THREE };   // zum Feintunen in der Konsole

// ---------- Kamerafahrt: von der Ebene durch den Raum, am Foto-Standpunkt vorbei, bis frontal vor das Herz ----------
const path = new THREE.CatmullRomCurve3([
  CAM_START.clone(), new THREE.Vector3(1.1, 3.4, 16), new THREE.Vector3(0.6, 3.45, 12.2), CAM_END.clone() ]);
const look0 = PC.clone().addScaledVector(FS, 30);

function layout(){
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w/h; camera.updateProjectionMatrix();
  const b = new THREE.Vector2(); renderer.getDrawingBufferSize(b);
  const px = b.y / (2*Math.tan(camera.fov*DEG/2));                   // Welt-Punktgröße -> Pixel
  land.uPx.value = px; uni.uPx.value = px;
}
addEventListener('resize', layout); layout();

let mx = 0, my = 0, emx = 0, emy = 0;
addEventListener('mousemove', e=>{ mx = e.clientX/innerWidth*2 - 1; my = e.clientY/innerHeight*2 - 1; });
// sanfter Herzschlag: zwei weiche Wellen, Periode 1.6 s
const beat = (s)=>{ const x = (s % 1.6)/1.6; return Math.exp(-Math.pow((x-0.12)/0.09,2)) + 0.5*Math.exp(-Math.pow((x-0.38)/0.1,2)); };

let tS = 0; const t0 = performance.now();
const camPos = new THREE.Vector3(), lookAt = new THREE.Vector3(), right = new THREE.Vector3(), up = new THREE.Vector3(0,1,0);
(function frame(now){
  requestAnimationFrame(frame);
  if(!landReady || !heartReady || holder.style.visibility !== 'visible') return;
  const tRaw = (window.__heart && window.__heart.t) || 0;
  tS += (tRaw - tS)*0.12;
  const sec = (now - t0)/1000;
  const reveal = smooth(cl(tS/0.15, 0, 1));                          // Szene + Würfel gemeinsam
  glassMat.opacity = reveal; edgeMat.opacity = 0.5*reveal; hiMat.opacity = 0.7*reveal; cube.visible = reveal > 0.002;
  const f = smooth(cl((tS-0.15)/0.85, 0, 1));                        // Kamerafahrt
  const landK = reveal*(1 - smooth(cl((f-0.72)/0.26, 0, 1)));        // am Ende lösen sich die Landschaftspunkte auf -> nur Herz + Würfel
  land.uReveal.value = landK; landPts.visible = landK > 0.001;
  uni.uTime.value = sec;
  uni.uForm.value = smooth(cl((f-0.05)/0.6, 0, 1));                  // Herz entsteht mit der Fahrt
  heartG.scale.setScalar(1 + 0.014*beat(sec));                      // leicht und sanft pulsieren
  floatG.position.y = Math.sin(sec*0.9)*0.03;                        // schwebt in der Luft
  path.getPointAt(f, camPos); lookAt.copy(look0).lerp(C, smooth(f));
  emx += (mx - emx)*0.05; emy += (my - emy)*0.05;
  right.subVectors(lookAt, camPos).cross(up).normalize();
  camera.position.copy(camPos).addScaledVector(right, emx*0.12).addScaledVector(up, -emy*0.07);
  camera.lookAt(lookAt);
  renderer.render(scene, camera);
})(performance.now());
