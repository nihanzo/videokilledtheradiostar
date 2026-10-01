// Glas-3D (three.js) – wird von startpage.html erst nachgeladen, wenn die Galerie beginnt (entlastet den Seitenstart)

  import * as THREE from 'three';
  import { GLTFLoader } from './vendor/three/GLTFLoader.js';

  const holder = document.getElementById('glass3d');
  const renderer = new THREE.WebGLRenderer({ alpha:true, antialias:true });
  renderer.setPixelRatio(Math.min(devicePixelRatio||1, 2));
  renderer.setClearColor(0x000000, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;   // weniger Belichtung -> Bernstein wäscht nicht zu Weiß aus
  holder.appendChild(renderer.domElement);

  const scene  = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 500);

  // Prozedurale Studio-Umgebung (helle Softboxen) – gibt dem Glas Reflexe/Kanten
  const pmrem = new THREE.PMREMGenerator(renderer);
  (function setEnv(){
    const c = document.createElement('canvas'); c.width = 256; c.height = 128;
    const g = c.getContext('2d');
    const grd = g.createLinearGradient(0,0,0,128);
    grd.addColorStop(0.00,'#ffffff'); grd.addColorStop(0.50,'#f3eef2'); grd.addColorStop(1.00,'#cfc8d2');
    g.fillStyle = grd; g.fillRect(0,0,256,128);
    const tex = new THREE.CanvasTexture(c);
    tex.mapping = THREE.EquirectangularReflectionMapping;
    scene.environment = pmrem.fromEquirectangular(tex).texture;
    tex.dispose();
  })();
  scene.add(new THREE.AmbientLight(0xffffff, 0.45));
  const key = new THREE.DirectionalLight(0xfff1de, 1.7); key.position.set(2,3,2.5); scene.add(key);
  const rim = new THREE.DirectionalLight(0xC65563, 1.0); rim.position.set(-2.5,-1,-2); scene.add(rim);

  const pivot = new THREE.Group(); scene.add(pivot);
  let ready = false, objH = 1, sphereR = 0.5;
  new GLTFLoader().load('assets/models/glass-transp.glb', (gltf)=>{
    const obj = gltf.scene;
    const box = new THREE.Box3().setFromObject(obj);
    const size = box.getSize(new THREE.Vector3());
    obj.position.sub(box.getCenter(new THREE.Vector3()));
    objH = size.y; sphereR = 0.5*size.length();
    // Farben wie das Referenzfoto: Kelch/Stiel/Ränder honig-bernstein, geschliffene Felder klar,
    // Fuß hell-grau klar. Durchscheinend (Transmission wäre auf transparentem Canvas schwarz).
    const LOOK = {
      amber: { color:'#c8922a', opacity:0.36 },   // Transparentes bernsteinfarbenes Glas + Glasränder (durchsichtiger)
      field: { color:'#fbf7ec', opacity:0.42 },   // Helle geschliffene Felder (Verzierung am Rand)
      foot:  { color:'#d8d5cf', opacity:0.18 }    // Heller Glasfuß
    };
    obj.traverse(o=>{
      if(!o.isMesh) return;
      const n = (o.material && o.material.name) || '';
      const L = /Felder/.test(n) ? LOOK.field : /Fuss/.test(n) ? LOOK.foot : LOOK.amber;
      o.material = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(L.color), metalness: 0, roughness: 0.05, ior: 1.48,
        transparent: true, opacity: L.opacity,
        envMapIntensity: 1.1, clearcoat: 1, clearcoatRoughness: 0.05,
        side: THREE.DoubleSide, depthWrite: false
      });
      // Verzierungen (Felder) immer ZULETZT zeichnen -> verschwinden beim Drehen nicht hinter dem Kelch/Schaum
      o.renderOrder = (L===LOOK.field) ? 20 : 0;
    });
    pivot.add(obj);
    buildPour(obj);
    ready = true; layout();
    // Shader vorab (asynchron) kompilieren -> kein Ruckler beim ersten sichtbaren Frame
    try{ renderer.compileAsync(scene, camera).catch(()=>{}); }catch(_){}
  }, undefined, (e)=>console.warn('glass glb load error', e));

  // ---------- Champagner: füllt sich beim Karussell-Scroll (ohne Strahl), Schaum wächst mit ----------
  // Kelch-Innenraum (aus den GLB-Vertices gemessen, Modell-Koordinaten): Kegel, Spitze y≈0.118,
  // Radius wächst mit 0.418·(y−Spitze), Rand bei y=0.255 (r=0.06). Innenwand ≈ 93%.
  const BOWL_Y0=0.118, BOWL_TOP=0.255, BOWL_K=0.418*0.93, FILL_MAX=0.212;
  const bowlR = (y)=>Math.max(0,(y-BOWL_Y0)*BOWL_K);
  let liquid, foam, bubbles, bubbleData=[], objRef;
  function foamTexture(){
    // Schaum: oben dicht & weiß, nach unten zu Perlen ausdünnend (Alpha-Verlauf -> geht in den Champagner über)
    const c=document.createElement('canvas'); c.width=256; c.height=128; const g=c.getContext('2d');
    const grd=g.createLinearGradient(0,0,0,128);
    grd.addColorStop(0,'rgba(255,251,240,.96)'); grd.addColorStop(.45,'rgba(252,244,222,.75)'); grd.addColorStop(1,'rgba(245,228,170,0)');
    g.fillStyle=grd; g.fillRect(0,0,256,128);
    for(let i=0;i<900;i++){
      const y=Math.pow(Math.random(),1.8)*128, x=Math.random()*256, r=0.8+Math.random()*(4.2-y/40);
      const a=0.9*(1-y/128);
      g.beginPath(); g.arc(x,y,Math.max(r,.6),0,Math.PI*2);
      g.fillStyle=`rgba(255,253,246,${(a*0.55).toFixed(2)})`; g.fill();
      g.strokeStyle=`rgba(214,190,130,${(a*0.7).toFixed(2)})`; g.lineWidth=.7; g.stroke();
    }
    const t=new THREE.CanvasTexture(c); t.wrapS=THREE.RepeatWrapping; t.repeat.set(3,1); return t;
  }
  function buildPour(obj){
    objRef=obj;
    // Flüssigkeit: Einheits-Kegel (Spitze unten, Ursprung an der Spitze) -> per scale exakt auf Füllhöhe
    const cone=new THREE.CylinderGeometry(1,0,1,48,1,false); cone.translate(0,0.5,0);
    liquid=new THREE.Mesh(cone,new THREE.MeshPhysicalMaterial({
      color:new THREE.Color('#f0cf6a'), transparent:true, opacity:0.62, roughness:0.08,
      envMapIntensity:0.9, clearcoat:1, depthWrite:false, side:THREE.DoubleSide }));
    liquid.position.y=BOWL_Y0; liquid.renderOrder=-2; liquid.visible=false; obj.add(liquid);
    // Schaum: dünne Scheibe mit Bläschen-Textur auf der Oberfläche
    const fg=new THREE.CylinderGeometry(1,0.96,1,48,1,false); fg.translate(0,0.5,0);
    foam=new THREE.Mesh(fg,new THREE.MeshStandardMaterial({ map:foamTexture(), color:0xffffff,
      roughness:0.85, emissive:new THREE.Color('#fff4dc'), emissiveIntensity:0.22, transparent:true, opacity:1, depthWrite:false, side:THREE.DoubleSide }));
    foam.renderOrder=10; foam.visible=false; obj.add(foam);   // nach dem Glas zeichnen -> Schaum leuchtet weiß durch
    // aufsteigende Perlen in der Flüssigkeit
    const N=70, pos=new Float32Array(N*3);
    for(let i=0;i<N;i++) bubbleData.push({a:Math.random()*Math.PI*2, r:Math.random(), v:0.25+Math.random()*0.6, p:Math.random()});
    const bg=new THREE.BufferGeometry(); bg.setAttribute('position',new THREE.BufferAttribute(pos,3));
    bubbles=new THREE.Points(bg,new THREE.PointsMaterial({ color:0xfffbe8, size:0.0022, transparent:true, opacity:0.85, depthWrite:false }));
    bubbles.visible=false; obj.add(bubbles);
  }
  function updatePour(car, now){
    if(!liquid) return;
    const sm=(u)=>u*u*(3-2*u), c=(v)=>Math.min(1,Math.max(0,v));
    const fill=sm(c((car-0.06)/0.62));                 // Füllen während des Karussells (6%..68%)
    const yF=BOWL_Y0+(FILL_MAX-BOWL_Y0)*fill, h=yF-BOWL_Y0, rF=bowlR(yF);
    liquid.visible=h>0.001; liquid.scale.set(rF||1e-4,h||1e-4,rF||1e-4);
    // Schaum wächst mit dem Füllen und bleibt am Ende groß (flacht nicht ab)
    const foamH=fill>0.02 ? 0.006+0.034*fill : 0;
    foam.visible=foamH>0.0005; const yT=Math.min(yF+foamH,BOWL_TOP+0.004);
    if(foam.visible){                                   // Kegelstumpf exakt an der Innenwand (unten rF, oben r(yT))
      foam.geometry.dispose();
      foam.geometry=new THREE.CylinderGeometry(bowlR(yT)*0.99, rF*0.99, yT-yF, 48, 1, false);
      foam.position.y=(yF+yT)/2; foam.scale.set(1,1,1);
    }
    foam.material.map.offset.x=now*0.00003;
    // Perlen
    bubbles.visible=h>0.01;
    if(bubbles.visible){
      const arr=bubbles.geometry.attributes.position.array;
      bubbleData.forEach((b,i)=>{
        const y=BOWL_Y0+0.004+((b.p+now*0.00005*b.v)%1)*(h-0.004);
        const rr=bowlR(y)*0.85*b.r;
        arr[i*3]=Math.cos(b.a)*rr; arr[i*3+1]=y; arr[i*3+2]=Math.sin(b.a)*rr;
      });
      bubbles.geometry.attributes.position.needsUpdate=true;
    }
  }

  // Kamera-Abstand D so, dass das Glas bei z=0 0.4× so hoch ist wie die Figur (centerpic)
  let D = 5;
  function layout(){
    const w = innerWidth, h = innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w/h; camera.updateProjectionMatrix();
    const figH = (document.getElementById('centerpic').offsetHeight || h*0.64);
    const tanH = Math.tan(THREE.MathUtils.degToRad(camera.fov/2));
    D = objH*h / (2*tanH*0.4*figH);                      // Glas = 0.4 × Figurhöhe (etwas kleiner)
    camera.position.set(0,0,D); camera.lookAt(0,0,0);
    camera.far = D*45; camera.updateProjectionMatrix();
  }
  addEventListener('resize', layout); layout();

  let tS = 0, carS = 0, drawn = false;
  (function frame(){
    const tRaw = (window.__glass && window.__glass.t) || 0;
    tS += (tRaw - tS)*0.15;
    if(ready && holder.style.opacity==='1' && !window.__glassPhoto){
      const e = 1-Math.pow(1-tS,3);                     // easeOut: schnell nah, weich ankommen
      const sc = Math.pow(0.03, 1-e);                    // scheinbare Größe 3% -> 100% (aus der Ferne)
      pivot.position.z = D - D/sc;                        // perspektivisch: weit hinten -> z=0
      carS += (((window.__glass && window.__glass.car) || 0) - carS)*0.15;
      const sway = Math.sin(carS*Math.PI*4)*0.13;          // schwankt beim Karussell-Drehen rechts <-> links
      pivot.rotation.set(tS*Math.PI*2, 0, sway);          // Anflug: eine Umdrehung kopfüber
      pivot.updateMatrixWorld(true);
      updatePour(carS, performance.now());
      renderer.render(scene, camera); drawn = true;
    } else if(drawn){ renderer.clear(); drawn = false; }   // ausgeblendet: leeren, sonst blitzt beim Wiedereinblenden kurz das alte Bild auf
    requestAnimationFrame(frame);
  })();
