// Herz-Szene (three.js) nach der Foto-Galerie: Fahrt an vier Objekten vorbei bis frontal vor den Glaswürfel mit dem
// schwarzen Punkt-Herz. Nachgeladen von startpage.html (loadHeart); der Director setzt window.__heart = { t, lead }.
// Ablauf in t (0..1):
//   0 … lead   überlappt mit dem Ende der Foto-Galerie (das letzte Bild liegt als DOM darüber und verschwindet):
//              die SEITE blendet ihren Hintergrund per CSS (#bgWhite) ins Weiße; diese Szene wird erst danach
//              eingeblendet und hat nur eine weiße Rückwand (kein Nachbau des Fotos mehr -> kein Sprung)
//   danach     die Objekte erscheinen, dann Kamerafahrt als S-Kurve von rechts nach links mitten hindurch: Frau (Linien,
//              links) → Pferdekopf (Metallteile, rechts) → Affe (Pixel, links) → Glasfigur (Hampelmann, rechts); sie
//              fahren einfach aus dem Bild. Der Würfel erscheint unterwegs, das Herz setzt sich zusammen, am Ende frontal.
// Glas: eigener Shader statt three-Transmission – der Strahl wird im Quader verfolgt (Brechung, Totalreflexion an den
// Innenseiten, leichte Dispersion); austretende Strahlen sehen die Szene (Bildschirm-Textur) bzw. außerhalb davon die
// Umgebung (Würfel-Map aus den Rahmenbildern der Seite: Blumen links, Häuser oben (früher Berge), Bronze unten, Gebäude rechts,
// Glas-Foto hinter der Kamera + zwei Leuchtflächen) -> klar und spiegelnd, oben grün (Berge) statt grau/weiß.
// Das Herz wird NICHT gebrochen (sonst doppelt zu sehen), sondern zwischen Brechungs- und Spiegelungs-Pass gezeichnet.
// Frühere Punkt-Landschaft (Palermo-Relief + Gelände): .claude/archiv/heart-mit-landschaft.js

import * as THREE from 'three';

const holder = document.getElementById('heart3d');
const renderer = new THREE.WebGLRenderer({ alpha:true, antialias:true });
renderer.setPixelRatio(Math.min(devicePixelRatio||1, 2));
renderer.setClearColor(0xECE6EA, 1);
renderer.autoClear = false;
holder.appendChild(renderer.domElement);

const sceneBg = new THREE.Scene();                   // Rückwand + Objekte der Fahrt (wird vom Glas mitgebrochen)
const sceneGl = new THREE.Scene();                   // Glaswürfel + Herz
const camera  = new THREE.PerspectiveCamera(42, 1, 0.05, 400);
sceneBg.add(camera);

let rs = 7; const rnd = ()=>((rs = (rs*16807) % 2147483647) / 2147483647);   // fester Zufall
const smooth = (t)=>t*t*(3-2*t), cl = (v,a,b)=>Math.max(a,Math.min(b,v)), DEG = Math.PI/180;
const loadImg = async (src)=>{ const im = new Image(); im.src = src; await im.decode(); return im; };
const loadPx = async (src)=>{ const im = await loadImg(src);
  const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
  const x = c.getContext('2d', { willReadFrequently:true }); x.drawImage(im, 0, 0);
  return { W:im.width, H:im.height, px:x.getImageData(0, 0, im.width, im.height).data }; };
const texOf = (im)=>{ const t = new THREE.Texture(im); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.needsUpdate = true; return t; };
const VS_UV = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position, 1.0); }`;

// ---------- Rückwand: schlicht weiß, kamerafest (= #bgWhite der Seite, über die diese Szene eingeblendet wird) ----------
const backdropMat = new THREE.ShaderMaterial({ vertexShader:VS_UV, depthWrite:false,
  fragmentShader:`void main(){ gl_FragColor = vec4(1.0); }` });
const backdrop = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), backdropMat);
backdrop.renderOrder = -1; backdrop.frustumCulled = false; camera.add(backdrop);
function fitBackdrop(){
  const D = 300, h = 2*D*Math.tan(camera.fov*DEG/2);
  backdrop.position.set(0, 0, -D); backdrop.scale.set(h*camera.aspect, h, 1);   // füllt genau das Bild
}

// ---------- Anordnung (Welt-Einheiten): der Würfel C steht fest. Die Kamera fährt eine Kurve von rechts hinten (erst
// geradeaus, dann nach links) bis schräg rechts vor den Würfel und schaut dabei IMMER zu ihm -> er bleibt an derselben
// Bildstelle (links der Mitte) und wird nur größer. Weil der Blick auf ihn nach und nach frontaler wird, ist seine linke
// Wand erst breit und dann schmal. Objekte abwechselnd links/rechts der Bahn (man fährt mittendurch), nach hinten kleiner.
const C = new THREE.Vector3(-1.0, 3.35, 7.5);
const P_S = C.clone().add(new THREE.Vector3(6.0, 0.7, 15.0)), P_K = C.clone().add(new THREE.Vector3(6.3, 0.5, 7.0)),
      CAM_END = C.clone().add(new THREE.Vector3(2.1, 0.3, 3.0));                // anfangs höher -> hintere Objekte stehen im Bild höher
const bez = (u, o)=>o.set(0, 0, 0).addScaledVector(P_S, (1-u)*(1-u)).addScaledVector(P_K, 2*(1-u)*u).addScaledVector(CAM_END, u*u);
const ARC = { N:400, L:0 }, U = [0];                                             // Bogenlänge -> gleichmäßiges Tempo
{ const a = bez(0, new THREE.Vector3()), b = new THREE.Vector3();
  for(let i = 1; i <= ARC.N; i++){ bez(i/ARC.N, b); ARC.L += a.distanceTo(b); U.push(ARC.L); a.copy(b); } }
const uAt = (s)=>{ s = cl(s, 0, ARC.L); let lo = 0, hi = ARC.N;
  while(hi - lo > 1){ const m = (lo + hi) >> 1; if(U[m] < s) lo = m; else hi = m; }
  return (lo + (s - U[lo])/Math.max(1e-6, U[hi] - U[lo]))/ARC.N; };
const arcPt    = (s, o = new THREE.Vector3())=>bez(uAt(s), o);
const arcRight = (s, o = new THREE.Vector3())=>{ const u = uAt(s);
  const d = bez(Math.min(1, u + 0.002), new THREE.Vector3()).sub(bez(Math.max(0, u - 0.002), new THREE.Vector3()));
  return o.set(-d.z, 0, d.x).normalize(); };
const LOOK_OFF = 16*DEG;                                                         // Blick rechts am Würfel vorbei -> Würfel links der Mitte
const onArc = (s, r, y, h)=>({ s, h, p:arcPt(s).addScaledVector(arcRight(s), r).setY(y) });   // r < 0 = links
// Reihenfolge wie im Brief: Frau links, dann Pferd rechts, Affe links, Figur rechts – die Bahn läuft mitten hindurch.
// Abstände/Höhen per Projektion so gewählt, dass zu Beginn nichts verdeckt ist (Affe springt etwas höher, über der Frau);
// die Figur steht kurz vor dem Würfel.
const FRAU  = onArc(4.0, -0.85, 3.25, 1.3);
const PFERD = onArc(6.6,  1.35, 3.4,  1.1);
const AFFE  = onArc(9.0, -0.8,  3.85, 0.45);                                     // Mitte im Stand (tiefster Punkt)
const FIGUR = onArc(12.5, 1.0,  3.6,  0.5);                                      // zuletzt = am kleinsten; nah am Würfel -> nach ihr kurzer Weg

// ---------- Glaswürfel: eigener Shader (Strahlverfolgung im Quader) ----------
const BOX = new THREE.Vector3(0.74, 0.9, 0.74);                                  // etwas enger als zuvor (0.9³)
const bgRT = new THREE.WebGLRenderTarget(2, 2, { type:THREE.HalfFloatType });  // Szene hinter dem Glas (halbe Auflösung)
const glassUni = {
  uBg:{ value:bgRT.texture }, uEnv:{ value:null }, uHalf:{ value:BOX.clone().multiplyScalar(0.5) },
  uIor:{ value:1.6 }, uDisp:{ value:0.025 }, uRefl:{ value:1.25 }, uAppear:{ value:0 },   // durchsichtiger
  uAbs:{ value:new THREE.Vector3(0, 0, 0) }, uRes:{ value:new THREE.Vector2(1, 1) },   // keine Tönung: Vorder-/Rückseite ganz durchsichtig
  uModel:{ value:new THREE.Matrix4() }, uModelInv:{ value:new THREE.Matrix4() }, uViewProj:{ value:new THREE.Matrix4() },
  // Oberseite spiegelt die Häuser (frame-houses.webp), die auf dem Bildschirm genau über ihr hängen:
  // uTopX = (linke Kante, Breite des Häuser-Bilds in Puffer-Pixeln, Bild-v am oberen Bildschirmrand, 1 = Textur da)
  uTop:{ value:null }, uTopX:{ value:new THREE.Vector4(0, 1, 0.36, 0) },
};
const GLASS_VS = `varying vec3 vL; varying vec3 vNL;
  void main(){ vL = position; vNL = normal; gl_Position = projectionMatrix*modelViewMatrix*vec4(position, 1.0); }`;
const GLASS_COMMON = `
  uniform sampler2D uBg; uniform samplerCube uEnv; uniform vec3 uHalf, uAbs; uniform vec2 uRes;
  uniform float uIor, uDisp, uRefl, uAppear; uniform mat4 uModel, uModelInv, uViewProj;
  varying vec3 vL; varying vec3 vNL;
  // Umgebung: Würfel-Map aus den Rahmenbildern + zwei Studio-Leuchtflächen (hinter der Kamera) für Glanzlichter
  vec3 envMap(vec3 d, float lod){
    vec3 c = textureLod(uEnv, vec3(-d.x, d.y, d.z), lod).rgb;   // three-Konvention (flipEnvMap)
    float az = atan(d.x, d.z);                                   // 0 = Richtung Kamera
    float s1 = smoothstep(0.14, 0.10, abs(az + 0.62)) * smoothstep(-0.25, -0.1, d.y) * smoothstep(0.8, 0.62, d.y);
    float s2 = smoothstep(0.975, 0.988, dot(d, normalize(vec3(0.62, 0.66, 0.42))));
    return c + vec3(1.0, 0.97, 0.92)*(s1*4.0 + s2*9.0);
  }
  // was ein austretender Strahl sieht: die Szene (Bildschirm-Textur), am Bildrand/außerhalb weich die Umgebung
  // (durchs Glas weicher und heller als in der Spiegelung -> Seiten bleiben durchsichtig statt Foto-Flächen)
  vec3 world(vec3 p, vec3 d){
    vec3 e = mix(envMap(d, 2.5), vec3(1.0), 0.2);
    vec4 c = uViewProj*vec4(p + d*3.0, 1.0);                      // ~Abstand zum Bild dahinter
    if(c.w < 0.05) return e;
    vec2 uv = c.xy/c.w*0.5 + 0.5;
    float k = smoothstep(0.0, 0.07, min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y)));
    return mix(e, texture2D(uBg, clamp(uv, 0.001, 0.999)).rgb, k);
  }
  float fresnelD(float ci, float eta){                           // exakt, unpolarisiert; eta = n2/n1
    ci = clamp(ci, 0.0, 1.0);
    float g2 = eta*eta - 1.0 + ci*ci;
    if(g2 < 0.0) return 1.0;                                     // Totalreflexion
    float g = sqrt(g2), a = (g - ci)/(g + ci), b = (ci*(g + ci) - 1.0)/(ci*(g - ci) + 1.0);
    return 0.5*a*a*(1.0 + b*b);
  }`;
const glassT = new THREE.ShaderMaterial({              // Pass 1: Durchsicht (ersetzt die Pixel hinter dem Glas)
  uniforms:glassUni, vertexShader:GLASS_VS, transparent:true, blending:THREE.NoBlending, depthWrite:false,
  fragmentShader: GLASS_COMMON + `
  vec3 trace(vec3 p, vec3 rd, float ior){
    vec3 acc = vec3(0.0); float w = 1.0, dist = 0.0;
    for(int b = 0; b < 5; b++){
      vec3 s = vec3(rd.x < 0.0 ? -1.0 : 1.0, rd.y < 0.0 ? -1.0 : 1.0, rd.z < 0.0 ? -1.0 : 1.0);
      vec3 tM = (s*uHalf - p)/(s*max(abs(rd), vec3(1e-5)));
      float t = min(min(tM.x, tM.y), tM.z);
      vec3 q = p + rd*t; dist += t;
      vec3 n = t == tM.x ? vec3(s.x, 0.0, 0.0) : (t == tM.y ? vec3(0.0, s.y, 0.0) : vec3(0.0, 0.0, s.z));
      if(abs(n.z) > 0.5){                                        // Vorder-/Rückseite: nur durchsichtig, keine Innenspiegelung
        vec3 ro = refract(rd, -n, ior); if(dot(ro, ro) < 1e-4) ro = rd;
        acc += w*exp(-uAbs*dist)*world((uModel*vec4(q, 1.0)).xyz, normalize(mat3(uModel)*ro)); w = 0.0; break;
      }
      float F = fresnelD(dot(rd, n), 1.0/ior);
      if(F < 1.0) acc += w*(1.0 - F)*exp(-uAbs*dist)*world((uModel*vec4(q, 1.0)).xyz, normalize(mat3(uModel)*refract(rd, -n, ior)));
      w *= F;
      if(w < 0.02) break;
      rd = reflect(rd, n); p = q;                                // Innenreflexion
    }
    return acc + w*exp(-uAbs*dist)*mix(envMap(normalize(mat3(uModel)*rd), 2.5), vec3(1.0), 0.2);
  }
  void main(){
    vec3 cam = (uModelInv*vec4(cameraPosition, 1.0)).xyz;
    vec3 rd = normalize(vL - cam), n = normalize(vNL);
    float i0 = uIor - uDisp, i2 = uIor + uDisp;                  // Dispersion: je Farbkanal eigene Brechzahl
    vec3 col = vec3(trace(vL, refract(rd, n, 1.0/i0), i0).r, trace(vL, refract(rd, n, 1.0/uIor), uIor).g,
                    trace(vL, refract(rd, n, 1.0/i2), i2).b);
    gl_FragColor = vec4(mix(texture2D(uBg, gl_FragCoord.xy/uRes).rgb, col, uAppear), 1.0);
    #include <colorspace_fragment>
  }` });
const glassR = new THREE.ShaderMaterial({              // Pass 2: Spiegelung (über dem Herz -> es liegt hinter Glas)
  uniforms:glassUni, vertexShader:GLASS_VS, transparent:true, depthWrite:false,
  blending:THREE.CustomBlending, blendSrc:THREE.OneFactor, blendDst:THREE.OneMinusSrcAlphaFactor,
  fragmentShader: GLASS_COMMON + `
  uniform sampler2D uTop; uniform vec4 uTopX;
  void main(){
    vec3 cam = (uModelInv*vec4(cameraPosition, 1.0)).xyz;
    vec3 rd = normalize(vL - cam), n = normalize(vNL);
    float F = abs(n.z) > 0.5 ? 0.0 : clamp(fresnelD(-dot(rd, n), uIor)*uRefl, 0.0, 1.0)*uAppear;   // Vorder-/Rückseite spiegeln nicht
    vec3 e = envMap(normalize(mat3(uModel)*reflect(rd, n)), 1.0);
    if(n.y > 0.5 && uTopX.w > 0.5){
      // Oberseite: x = Bildschirm-x -> genau die Häuser darüber; Tiefe wie ein Spiegel: hintere Kante = tiefste
      // Turmspitzen (Bildunterkante), vordere Kante = Häuser am oberen Bildschirmrand (flipY: v = 1 - Bildzeile)
      float vImg = mix(uTopX.z, 1.0, 0.5 - 0.5*vL.z/uHalf.z);
      vec4 h = texture2D(uTop, vec2((gl_FragCoord.x - uTopX.x)/uTopX.y, 1.0 - vImg));
      e = mix(e, h.rgb, h.a);
    }
    vec4 o = linearToOutputTexel(vec4(e, 1.0));
    gl_FragColor = vec4(o.rgb*F, F);
  }` });

const objG = new THREE.Group(); objG.position.copy(C); sceneGl.add(objG);
objG.lookAt(CAM_END);                                                // Herz-Vorderseite zeigt zum Fahrtende
const floatG = new THREE.Group(); objG.add(floatG);                  // leichtes Schweben (Herz + Würfel)
const heartG = new THREE.Group(); floatG.add(heartG);                // pulsiert
const cubeG  = new THREE.Group(); floatG.add(cubeG);
const boxGeo = new THREE.BoxGeometry(BOX.x, BOX.y, BOX.z);
const cubeT = new THREE.Mesh(boxGeo, glassT); cubeT.renderOrder = 1; cubeG.add(cubeT);
const cubeR = new THREE.Mesh(boxGeo, glassR); cubeR.renderOrder = 3; cubeG.add(cubeR);

// ---------- Herz: schwarze Zeichnung vorn (gewölbt) + runde, gleichmäßige Rückseite ----------
const SIDE_H = 0.8, STEP = 2;
const uni = { uTime:{value:0}, uForm:{value:0}, uPx:{value:800}, uDot:{value:0.004} };
async function buildHeart(){
  const { W, H, px } = await loadPx('assets/img/heart-ink.png'), S = SIDE_H/H;
  const pos = [], start = [], rn = [], ink = [];
  const add = (X,Y,Z,k,size)=>{ pos.push(X,Y,Z);
    const a = rnd()*Math.PI*2, r = 0.12 + rnd()*0.22;               // Start: locker verstreut IM Würfel
    start.push(X*0.4 + Math.cos(a)*r, Y*0.4 + Math.sin(a)*r, Z*0.4 + (rnd()-0.5)*0.4);
    rn.push(rnd()*6.283, 0.35 + rnd()*0.7, rnd(), size); ink.push(k); };
  const prof = (dn)=>Math.sqrt(dn*(2-dn));                           // runder Querschnitt, 0 am Rand
  for(let y = 0; y < H; y += STEP) for(let x = 0; x < W; x += STEP){
    const jx = Math.min(W-1, Math.max(0, Math.round(x + (rnd()-0.5)*STEP*0.9)));
    const jy = Math.min(H-1, Math.max(0, Math.round(y + (rnd()-0.5)*STEP*0.9)));
    const i = (jy*W + jx)*4, k = px[i]/255; if(k < 0.08 || rnd() > Math.pow(k, 0.85)) continue;
    add((jx - W/2)*S, -(jy - H/2)*S, 0.12*SIDE_H*prof(px[i+1]/255) + (rnd()-0.5)*0.006, 1, 0.62 + 0.5*Math.sqrt(k));   // Vorderseite
  }
  for(let y = 0; y < H; y += STEP*2) for(let x = 0; x < W; x += STEP*2){   // Rückseite: gleichmäßig, rund
    const jx = Math.min(W-1, Math.max(0, Math.round(x + (rnd()-0.5)*STEP*1.8)));
    const jy = Math.min(H-1, Math.max(0, Math.round(y + (rnd()-0.5)*STEP*1.8)));
    const i = (jy*W + jx)*4; if(px[i+2] < 128 || rnd() > 0.75) continue;
    add((jx - W/2)*S, -(jy - H/2)*S, -0.22*SIDE_H*prof(px[i+1]/255), 0.72, 0.8);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('aStart',   new THREE.Float32BufferAttribute(start, 3));
  geo.setAttribute('aRnd',     new THREE.Float32BufferAttribute(rn, 4));
  geo.setAttribute('aInk',     new THREE.Float32BufferAttribute(ink, 1));
  uni.uDot.value = STEP*S*0.82;
  // EINMAL gezeichnet, nach dem Durchsicht-Pass und vor der Spiegelung (nicht gebrochen -> nicht doppelt)
  const pts = new THREE.Points(geo, new THREE.ShaderMaterial({ uniforms:uni, transparent:true, depthWrite:false,
    vertexShader:`
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
    fragmentShader:`
      varying float vInk;
      void main(){
        vec2 c = gl_PointCoord - 0.5; if(dot(c,c) > 0.25) discard;    // runde Mini-Kreise, schwarz
        gl_FragColor = vec4(pow(mix(vec3(0.30,0.29,0.31), vec3(0.03,0.03,0.035), vInk), vec3(2.2)), 1.0);
        #include <colorspace_fragment>
      }` }));
  pts.renderOrder = 2; pts.frustumCulled = false; heartG.add(pts);
}

// ---------- Objekte der Fahrt ----------
const RIDE = [];
function addRide(o, obj, update){                                    // blickt fest zur Bahn kurz VOR dem Objekt
  const g = new THREE.Group(); g.position.copy(o.p); g.add(obj); sceneBg.add(g);
  const q = arcPt(o.s - 2.6); g.lookAt(q.x, o.p.y, q.z);
  RIDE.push({ o, g, update });
}
// 1) Frau: viele freiliegende waagrechte Linien in ihrer eigenen Farbe, die leise und willkürlich seitlich wandern
async function buildFrau(){
  const im = await loadImg('assets/img/ride/frau.webp');
  const H = FRAU.h, W = H*im.width/im.height, N = 150, FILL = 0.7;   // dichte Linien -> gut erkennbar
  const pos = [], uv = [], yc = [], rn = [], idx = [];
  for(let i = 0; i < N; i++){
    const v0 = (i + (1-FILL)/2)/N, v1 = v0 + FILL/N, y0 = H/2 - v0*H, y1 = H/2 - v1*H;
    const r = [rnd(), rnd(), rnd(), rnd()], b = pos.length/3;
    [[-W/2,y0,0,1-v0],[W/2,y0,1,1-v0],[-W/2,y1,0,1-v1],[W/2,y1,1,1-v1]].forEach(([x,y,u,v])=>{
      pos.push(x, y, 0); uv.push(u, v); yc.push((y0+y1)/2); rn.push(...r); });
    idx.push(b, b+2, b+1, b+1, b+2, b+3);
  }
  const geo = new THREE.BufferGeometry(); geo.setIndex(idx);
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv',       new THREE.Float32BufferAttribute(uv, 2));
  geo.setAttribute('aYc',      new THREE.Float32BufferAttribute(yc, 1));
  geo.setAttribute('aRnd',     new THREE.Float32BufferAttribute(rn, 4));
  const u = { map:{ value:texOf(im) }, uTime:{ value:0 }, uShow:{ value:0 }, uGone:{ value:0 }, uAmp:{ value:0.013 } };
  const m = new THREE.Mesh(geo, new THREE.ShaderMaterial({ uniforms:u, side:THREE.DoubleSide,
    vertexShader:`
      attribute float aYc; attribute vec4 aRnd;
      uniform float uTime, uShow, uGone, uAmp;
      varying vec2 vUv; varying float vVis;
      void main(){
        vUv = uv;
        float sk = clamp((uShow - aRnd.z*0.45)/0.55, 0.0, 1.0), gk = clamp((uGone - aRnd.y*0.45)/0.55, 0.0, 1.0);
        vVis = sk*(1.0 - gk);
        vec3 p = position;
        p.y = aYc + (p.y - aYc)*vVis;                                  // Linie wird beim Kommen dicker, beim Gehen dünn
        p.x += uAmp*(0.65*sin(uTime*(0.3 + 0.45*aRnd.z) + aRnd.x*6.2832) + 0.35*sin(uTime*(0.75 + 0.6*aRnd.w) + aRnd.y*6.2832));
        p.x += (aRnd.x < 0.5 ? -1.0 : 1.0)*(gk*gk*0.9 + (1.0 - sk)*(1.0 - sk)*0.6);
        gl_Position = projectionMatrix*modelViewMatrix*vec4(p, 1.0);  // alle Linien in einer Ebene -> unten so gleichmäßig wie oben
      }`,
    fragmentShader:`
      uniform sampler2D map; varying vec2 vUv; varying float vVis;
      void main(){ vec4 c = texture2D(map, vUv); if(c.a < 0.5 || vVis < 0.01) discard;
        gl_FragColor = vec4(c.rgb, 1.0);
        #include <colorspace_fragment>
      }` }));
  m.frustumCulled = false;
  addRide(FRAU, m, (sec, show, gone)=>{ u.uTime.value = sec; u.uShow.value = show; u.uGone.value = gone; });
}
// 2) Pferdekopf: entlang der Rillen/Plattengrenzen in Teile zerlegt (ID-Karte, Watershed), kleine Fugen; eine Welle
//    läuft langsam und endlos von unten nach oben durch (Teile heben sich, kippen, glänzen)
async function buildPferd(json){
  const [im, idIm] = await Promise.all([ loadImg('assets/img/ride/pferd.webp'), loadImg('assets/img/ride/pferd-id.png') ]);
  const { w, h, pieces } = json.pferd, S = PFERD.h/h;
  const idTex = new THREE.Texture(idIm); idTex.minFilter = idTex.magFilter = THREE.NearestFilter; idTex.generateMipmaps = false; idTex.needsUpdate = true;
  const pos = [], uv = [], pid = [], ctr = [], rn = [], idx = [];
  for(const P of pieces){
    const x0 = P.x0 - 2, x1 = P.x1 + 2, y0 = P.y0 - 2, y1 = P.y1 + 2, cx = (P.cx - w/2)*S, cy = -(P.cy - h/2)*S;
    const r = [rnd(), rnd(), rnd()], b = pos.length/3;
    [[x0,y0],[x1,y0],[x0,y1],[x1,y1]].forEach(([x,y])=>{
      pos.push((x - w/2)*S, -(y - h/2)*S, 0); uv.push(x/w, 1 - y/h); pid.push(P.id); ctr.push(cx, cy); rn.push(...r); });
    idx.push(b, b+2, b+1, b+1, b+2, b+3);
  }
  const geo = new THREE.BufferGeometry(); geo.setIndex(idx);
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv',       new THREE.Float32BufferAttribute(uv, 2));
  geo.setAttribute('aId',      new THREE.Float32BufferAttribute(pid, 1));
  geo.setAttribute('aC',       new THREE.Float32BufferAttribute(ctr, 2));
  geo.setAttribute('aRnd',     new THREE.Float32BufferAttribute(rn, 3));
  const u = { map:{ value:texOf(im) }, uIdMap:{ value:idTex }, uTime:{ value:0 }, uShow:{ value:0 }, uGone:{ value:0 }, uH:{ value:PFERD.h } };
  const m = new THREE.Mesh(geo, new THREE.ShaderMaterial({ uniforms:u, side:THREE.DoubleSide,
    vertexShader:`
      attribute float aId; attribute vec2 aC; attribute vec3 aRnd;
      uniform float uTime, uShow, uGone, uH;
      varying vec2 vUv; varying float vId, vLit;
      void main(){
        vUv = uv; vId = aId;
        float sk = clamp((uShow - aRnd.z*0.5)/0.5, 0.0, 1.0), gk = clamp((uGone - aRnd.y*0.5)/0.5, 0.0, 1.0);
        float y01 = aC.y/uH + 0.5;                                    // 0 unten .. 1 oben
        float wp = fract(uTime/5.5)*1.5 - 0.25;                       // Wellenfront, langsam nach oben, Loop
        float d = (y01 - wp)/0.11, w = exp(-d*d);
        vec2 rel = (position.xy - aC)*(1.0 + 0.05*w);
        float th = -0.55*d*w;                                         // Teile kippen, wenn die Welle durchläuft
        vec3 p = vec3(aC.x + rel.x, aC.y + rel.y*cos(th), rel.y*sin(th));
        vec2 dir = aC/max(length(aC), 1e-3);
        p.xy += aC*0.035 + dir*(0.012 + 0.03*w);                      // kleiner Abstand zwischen den Teilen
        p.z += 0.09*w + (aRnd.x - 0.5)*0.02;
        p.xy += dir*(gk*gk*1.1 + (1.0 - sk)*(1.0 - sk)*0.5);          // Kommen/Gehen: Teile fliegen ein bzw. auseinander
        p.z += gk*gk*(aRnd.x - 0.3)*1.2 + (1.0 - sk)*(1.0 - sk)*0.6;
        vLit = (1.0 + 0.35*w + 0.25*sin(th))*step(0.02, sk*(1.0 - gk));
        gl_Position = projectionMatrix*modelViewMatrix*vec4(p, 1.0);
      }`,
    fragmentShader:`
      uniform sampler2D map, uIdMap; varying vec2 vUv; varying float vId, vLit;
      void main(){
        if(vLit < 0.01 || abs(floor(texture2D(uIdMap, vUv).r*255.0 + 0.5) - vId) > 0.5) discard;
        vec4 c = texture2D(map, vUv); if(c.a < 0.4) discard;
        gl_FragColor = vec4(c.rgb*vLit, 1.0);
        #include <colorspace_fragment>
      }` }));
  m.frustumCulled = false;
  addRide(PFERD, m, (sec, show, gone)=>{ u.uTime.value = sec; u.uShow.value = show; u.uGone.value = gone; });
}
// 3) Affe: aus seinen Verpixelungen zusammengesetzt (Pixel mit kleinen Fugen), springt federnd auf und ab
async function buildAffe(){
  const { W, H, px } = await loadPx('assets/img/ride/affe.webp');
  const NX = 72, cs = W/NX, NY = Math.round(H/cs), OH = AFFE.h, OW = OH*W/H;
  const cells = [], cols = [], rn = [];
  for(let j = 0; j < NY; j++) for(let i = 0; i < NX; i++){
    let r = 0, g = 0, b = 0, n = 0, tot = 0;
    for(let y = Math.floor(j*cs); y < Math.min(H, Math.floor((j+1)*cs)); y++)
      for(let x = Math.floor(i*cs); x < Math.min(W, Math.floor((i+1)*cs)); x++){
        const k = (y*W + x)*4; tot++; if(px[k+3] > 128){ r += px[k]; g += px[k+1]; b += px[k+2]; n++; } }
    if(!tot || n/tot < 0.5) continue;
    const lin = (v)=>Math.pow(v/n/255, 2.2);
    cells.push((i + 0.5)/NX, (j + 0.5)/NY); cols.push(lin(r), lin(g), lin(b)); rn.push(rnd(), rnd());
  }
  const plane = new THREE.PlaneGeometry(1, 1), geo = new THREE.InstancedBufferGeometry();
  geo.index = plane.index; geo.setAttribute('position', plane.getAttribute('position'));
  geo.setAttribute('aCell', new THREE.InstancedBufferAttribute(new Float32Array(cells), 2));
  geo.setAttribute('aCol',  new THREE.InstancedBufferAttribute(new Float32Array(cols), 3));
  geo.setAttribute('aRnd',  new THREE.InstancedBufferAttribute(new Float32Array(rn), 2));
  geo.instanceCount = cells.length/2;
  const u = { uTime:{ value:0 }, uShow:{ value:0 }, uGone:{ value:0 }, uW:{ value:OW }, uH:{ value:OH }, uCell:{ value:OW/NX }, uJump:{ value:0.4*OH } };
  const m = new THREE.Mesh(geo, new THREE.ShaderMaterial({ uniforms:u, side:THREE.DoubleSide,
    vertexShader:`
      attribute vec2 aCell; attribute vec3 aCol; attribute vec2 aRnd;
      uniform float uTime, uShow, uGone, uW, uH, uCell, uJump;
      varying vec3 vCol;
      void main(){
        vCol = aCol;
        float sk = clamp((uShow - aRnd.x*0.5)/0.5, 0.0, 1.0), gk = clamp((uGone - aRnd.y*0.5)/0.5, 0.0, 1.0);
        float up = 1.0 - aCell.y;                                     // 0 unten .. 1 oben
        float ph = fract(uTime/1.5 - up*0.04);                        // langsam; obere Reihen folgen etwas später -> federt
        float hop = mix(4.0*ph*(1.0 - ph), 0.5 - 0.5*cos(6.2832*ph), 0.55);   // Bogen mit weichem Aufsetzen
        float land = exp(-pow(min(ph, 1.0 - ph)/0.12, 2.0));
        vec2 b = vec2((aCell.x - 0.5)*uW, up*uH)*vec2(1.0 + 0.05*land, 1.0 - 0.08*land);   // Aufprall: sanft gestaucht
        b.y += hop*uJump - uH*0.5;
        vec3 p = vec3(b + position.xy*uCell*0.8*sk*(1.0 - gk), 0.0);    // Pixel mit Fugen, wachsen/schrumpfen
        p.y -= gk*gk*(0.6 + aRnd.x)*1.2; p.x += gk*(aRnd.y - 0.5)*0.6; // beim Gehen: Pixel fallen
        p.z += (1.0 - sk)*(1.0 - sk)*(aRnd.y - 0.5)*0.8;
        gl_Position = projectionMatrix*modelViewMatrix*vec4(p, 1.0);
      }`,
    fragmentShader:`
      varying vec3 vCol;
      void main(){ gl_FragColor = vec4(vCol, 1.0);
        #include <colorspace_fragment>
      }` }));
  m.frustumCulled = false;
  addRide(AFFE, m, (sec, show, gone)=>{ u.uTime.value = sec; u.uShow.value = show; u.uGone.value = gone; });
}
// 4) Glasfigur: Körper + zwei Beine (Beine reichen unter den Körper), Hampelmann auf der Stelle
async function buildFigur(json){
  const F = json.figur, S = FIGUR.h/F.h, toW = (x, y)=>[(x - F.w/2)*S, -(y - F.h/2)*S];
  const hop = new THREE.Group(), parts = {};
  for(const name of ['legL', 'legR', 'body']){
    const P = F.parts[name], im = await loadImg(`assets/img/ride/figur-${name}.webp`);
    const mat = new THREE.MeshBasicMaterial({ map:texOf(im), transparent:true, depthWrite:false, side:THREE.DoubleSide });
    const m = new THREE.Mesh(new THREE.PlaneGeometry((P.x1 - P.x0)*S, (P.y1 - P.y0)*S), mat);
    const [mx, my] = toW((P.x0 + P.x1)/2, (P.y0 + P.y1)/2), [ox, oy] = P.pivot ? toW(...P.pivot) : [0, 0];
    const joint = new THREE.Group(); joint.position.set(ox, oy, 0); m.position.set(mx - ox, my - oy, 0);
    m.renderOrder = name === 'body' ? 1 : 0;                         // Körper vor den Beinen
    joint.add(m); hop.add(joint); parts[name] = { joint, mat };
  }
  addRide(FIGUR, hop, (sec, show, gone)=>{
    const a = sec*2*Math.PI/1.25, spread = 0.5 - 0.5*Math.cos(a);   // Beine auf und zu
    parts.legL.joint.rotation.z = -0.42*spread; parts.legR.joint.rotation.z = 0.42*spread;
    hop.position.y = 0.07*Math.abs(Math.sin(a));                     // kleiner Hüpfer bei jedem Wechsel
    const op = show*(1 - gone);
    for(const k in parts) parts[k].mat.opacity = op;
    hop.visible = op > 0.005; hop.scale.setScalar(0.9 + 0.1*op);
  });
}

// ---------- Umgebung fürs Glas: Würfel-Map aus den Rahmenbildern (was den Würfel auf der Seite umgibt) ----------
async function buildEnv(){
  const ims = await Promise.all(['building', 'frame-flowers', 'frame-houses', 'frame-bronze']
    .map((n)=>loadImg(`assets/img/${n}.webp`)));
  const N = 512, face = (im, crop)=>{ const c = document.createElement('canvas'); c.width = c.height = N;
    const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, N, N);             // Transparentes = Weiß
    if(im){ const [sx, sy, sw, sh] = crop || [0, 0, im.naturalWidth, im.naturalHeight], k = Math.max(N/sw, N/sh);
      x.drawImage(im, sx, sy, sw, sh, (N - sw*k)/2, (N - sh*k)/2, sw*k, sh*k); }          // cover
    return c; };
  // Wand hinter dem Würfel = der Rahmen wie auf dem Bildschirm: weiße Mitte, Berge oben (breit, damit die flach
  // gesehene Oberseite sie spiegelt), Bronze unten, Blumen links, Gebäude oben rechts
  const front = face(null), fx = front.getContext('2d'), put = (im, x, y, w, h)=>fx.drawImage(im, x*N, y*N, w*N, h*N);
  put(ims[3], -0.3, 0.6, 1.6, 0.5); put(ims[2], -0.35, 0, 1.7, 1.0); put(ims[1], -0.42, 0, 0.62, 1.1); put(ims[0], 0.5, -0.02, 0.62, 0.41);
  // Reihenfolge px, nx, py, ny, pz, nz – mit three's flipEnvMap (x gespiegelt) liegt px links (−x), nx rechts (+x):
  // links Blumen, rechts Gebäude, oben Berge, unten Bronze, hinter der Kamera Blumen (Vorderseite spiegelt sie), hinter dem Würfel die Rahmen-Wand
  const env = new THREE.CubeTexture([ face(ims[1]), face(ims[0], [840, 0, 696, 850]), face(ims[2], [520, 0, 1000, 220]),
    face(ims[3], [1400, 60, 1000, 343]), face(ims[1]), front ]);                            // Häuser/Bronze: nur deckender Teil
  env.colorSpace = THREE.SRGBColorSpace; env.minFilter = THREE.LinearMipmapLinearFilter; env.needsUpdate = true;
  const top = texOf(ims[2]); top.anisotropy = renderer.capabilities.getMaxAnisotropy();   // stark gestaucht -> anisotrop filtern
  glassUni.uTop.value = top;
  return env;
}

// ---------- Aufbau ----------
let ready = false;
(async function init(){
  const [json, env] = await Promise.all([ fetch('assets/img/ride/ride.json').then((r)=>r.json()), buildEnv() ]);
  glassUni.uEnv.value = env;
  await Promise.all([ buildHeart(), buildFrau(), buildPferd(json), buildAffe(), buildFigur(json) ]);
  [...RIDE].sort((a, b)=>a.o.s - b.o.s).forEach((r, i)=>{ r.rank = i; });       // Reihenfolge des Erscheinens: vorn -> hinten
  layout(); renderer.compile(sceneBg, camera); renderer.compile(sceneGl, camera);   // Shader vorab -> kein Ruckler beim Einblenden
  ready = true;
})();

function layout(){
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w/h; camera.updateProjectionMatrix();
  const b = new THREE.Vector2(); renderer.getDrawingBufferSize(b);
  uni.uPx.value = b.y / (2*Math.tan(camera.fov*DEG/2));              // Welt-Punktgröße -> Pixel
  glassUni.uRes.value.copy(b); bgRT.setSize(Math.ceil(b.x/2), Math.ceil(b.y/2));
  fitBackdrop(); topLayout();
}
// Lage des Häuser-Bilds (.frame--top der Seite) für die Spiegelung der Würfel-Oberseite
const frameTop = document.querySelector('.frame--top');
function topLayout(){
  if(!frameTop) return;
  const r = frameTop.getBoundingClientRect(), k = glassUni.uRes.value.x/innerWidth, hh = r.width*360/2048;   // Bild 2048×360
  glassUni.uTopX.value.set(r.left*k, Math.max(1, r.width*k), cl(-r.top/hh, 0, 1), glassUni.uTop.value ? 1 : 0);
}
addEventListener('resize', layout);

let mx = 0, my = 0, emx = 0, emy = 0, mpx = -1, mpy = -1;
const hov = new THREE.Vector2(), hovT = new THREE.Vector2();                      // Kippen beim Drüberfahren (aktuell/Ziel)
addEventListener('mousemove', e=>{ mx = e.clientX/innerWidth*2 - 1; my = e.clientY/innerHeight*2 - 1; mpx = e.clientX; mpy = e.clientY; });
// sanfter Herzschlag: zwei weiche Wellen, Periode 1.6 s
const beat = (s)=>{ const x = (s % 1.6)/1.6; return Math.exp(-Math.pow((x-0.12)/0.09,2)) + 0.5*Math.exp(-Math.pow((x-0.38)/0.1,2)); };
const rideEase = (x)=>0.7*smooth(x) + 0.3*x;                         // ein Rutsch: weich an/aus

window.__heartDbg = { glassUni, cubeG, objG, heartG, uni, camera, backdropMat, RIDE, arcPt, arcRight, C, ARC, THREE };   // Konsole

let tS = 0; const t0 = performance.now();
const camPos = new THREE.Vector3(), lookAt = new THREE.Vector3(),
      right = new THREE.Vector3(), up = new THREE.Vector3(0,1,0);
// Sichtbarkeit steuert heart.js selbst (der Director setzt nur window.__heart.on): eingeblendet wird erst NACH einem
// frisch gerenderten Bild, und tS springt dabei auf den aktuellen Stand -> kein altes (weißes) Bild blitzt kurz auf
const contact = document.getElementById('contact'), camRight = new THREE.Vector3(), tmpC = new THREE.Vector3();
let shown = false;
function hideScene(){
  if(shown){ holder.style.visibility = 'hidden'; shown = false; }
  if(contact && contact.style.opacity !== '0'){ contact.style.opacity = '0'; contact.style.pointerEvents = 'none'; }
}
(function frame(now){
  requestAnimationFrame(frame);
  const hs = window.__heart || {};
  if(!hs.on || !ready){ hideScene(); return; }
  const tRaw = hs.t || 0, lead = hs.lead || 0.125;
  tS = shown ? tS + (tRaw - tS)*0.12 : tRaw;
  const sec = (now - t0)/1000;
  const R0 = lead + 0.06, f = rideEase(cl((tS - R0)/(1 - R0), 0, 1)), s = f*ARC.L;   // Fahrt in einem Rutsch
  // Kamera: fährt die Kurve entlang und schaut immer knapp rechts am Würfel vorbei (Würfel bleibt an seiner Bildstelle)
  arcPt(s, camPos); lookAt.subVectors(C, camPos);
  { const x = lookAt.x, z = lookAt.z, c = Math.cos(-LOOK_OFF), n = Math.sin(-LOOK_OFF); lookAt.x = x*c + z*n; lookAt.z = -x*n + z*c; }
  lookAt.add(camPos);
  lookAt.y -= Math.tan((6 - 4*f)*DEG)*Math.hypot(lookAt.x - camPos.x, lookAt.z - camPos.z);   // Blick leicht gesenkt -> alles steht höher im Bild
  emx += (mx - emx)*0.05; emy += (my - emy)*0.05;
  right.subVectors(lookAt, camPos).cross(up).normalize();
  camera.position.copy(camPos).addScaledVector(right, emx*0.12).addScaledVector(up, -emy*0.07);
  camera.lookAt(lookAt);
  // Objekte: erscheinen erst, wenn der Hintergrund ganz weiß ist (nah zuerst); beim Vorbeifahren verlassen sie
  // einfach das Bild (kein Auflösen), hinter der Kamera werden sie ausgeblendet
  RIDE.forEach((r, k)=>{
    const show = smooth(cl((tS - lead - r.rank*0.025)/0.05, 0, 1));    // von vorn nach hinten
    r.g.visible = show > 0.001 && s < r.o.s + 1.5;                    // rein von der Scroll-Lage abhängig -> vor/zurück gleich
    if(r.g.visible) r.update(sec, show, 0);
  });
  // Würfel erscheint unterwegs, das Herz setzt sich zusammen; beide schweben leicht, der Würfel dreht sich ins Bild
  const ap = smooth(cl((tS - lead - RIDE.length*0.025)/0.05, 0, 1));  // Würfel erscheint als letztes (ganz hinten)
  glassUni.uAppear.value = ap; cubeG.visible = ap > 0.002;
  uni.uTime.value = sec; uni.uForm.value = smooth(cl((f - 0.3)/0.6, 0, 1));
  heartG.scale.setScalar(1 + 0.014*beat(sec));
  floatG.position.y = Math.sin(sec*0.9)*0.03;                           // schwebt leicht
  // Maus über dem Würfel: er kippt deutlich zur Maus hin (Herz mit), sonst ruhig
  hov.x += (hovT.x - hov.x)*0.08; hov.y += (hovT.y - hov.y)*0.08;
  floatG.rotation.set(hov.y*14*DEG, hov.x*22*DEG, 0);
  cubeG.rotation.set(10*DEG + Math.sin(sec*0.31)*1*DEG, 15*DEG + Math.sin(sec*0.23)*1.5*DEG, 0);   // fest; linke Wand wird durch die Fahrt schmaler
  // Rendern: Szene -> Bildschirm; bei sichtbarem Glas zusätzlich in bgRT (halbe Auflösung) für die Durchsicht,
  // dann Glas-Durchsicht, Herz, Glas-Spiegelung
  camera.updateMatrixWorld(); objG.updateMatrixWorld(true);
  renderer.setRenderTarget(null); renderer.clear(); renderer.render(sceneBg, camera);
  if(cubeG.visible || uni.uForm.value > 0){
    if(cubeG.visible){
      renderer.setRenderTarget(bgRT); renderer.clear(); renderer.render(sceneBg, camera); renderer.setRenderTarget(null);
      topLayout();                                                    // Häuser-Lage frisch (Bühne kann sich verschoben haben)
      glassUni.uModel.value.copy(cubeT.matrixWorld); glassUni.uModelInv.value.copy(cubeT.matrixWorld).invert();
      glassUni.uViewProj.value.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    }
    renderer.render(sceneGl, camera);
  }
  if(!shown){ holder.style.visibility = 'visible'; shown = true; }
  // Hover-Ziel: Mausabstand zur Würfelmitte im Bild (Radius = halbe Würfelbreite); nur direkt darüber wird gekippt
  { camRight.setFromMatrixColumn(camera.matrixWorld, 0);
    const c = tmpC.copy(C).project(camera), cx = (c.x + 1)/2*innerWidth, cy = (1 - c.y)/2*innerHeight;
    const e = tmpC.copy(C).addScaledVector(camRight, 0.45).project(camera), rad = Math.max(20, Math.abs((e.x + 1)/2*innerWidth - cx));
    const dx = (mpx - cx)/rad, dy = (mpy - cy)/rad, w = mpx < 0 ? 0 : smooth(cl((1.35 - Math.hypot(dx, dy))/0.5, 0, 1))*cl(glassUni.uAppear.value, 0, 1);
    hovT.set(cl(dx, -1, 1)*w, cl(dy, -1, 1)*w); }
  // Kontakt-Links rechts neben dem Würfel, sobald man angekommen ist
  if(contact){
    const k = smooth(cl((f - 0.86)/0.1, 0, 1))*(1 - (hs.fade || 0));
    contact.style.opacity = k.toFixed(3); contact.style.pointerEvents = k > 0.5 ? 'auto' : 'none';
    if(k > 0){
      camRight.setFromMatrixColumn(camera.matrixWorld, 0);
      tmpC.copy(C).addScaledVector(camRight, 0.62).project(camera);
      contact.style.transform = `translate(${((tmpC.x + 1)/2*innerWidth).toFixed(1)}px,${((1 - tmpC.y)/2*innerHeight - contact.offsetHeight/2).toFixed(1)}px)`;
    }
  }
})(performance.now());
