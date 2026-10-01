// Boxsack oben rechts neben dem Gebäude (startpage.html #bag): hängt still und pendelt NUR, wenn die Maus drüberfährt.
// Physik = Doppelpendel: Kette (Aufhängung -> Ring) + Sack als starrer Körper am Ring (Lagrange-Gleichungen,
// halbimplizites Euler in 4-ms-Schritten). Die Maus schiebt wie eine Hand: Stoß ~ Relativgeschwindigkeit Maus <-> Treffpunkt,
// gewichtet mit der effektiven Masse dort (nah an der Aufhängung bewegt sich wenig). Schläft, sobald er ruht (kein Dauer-rAF).
(function(){
  const bag = document.getElementById('bag'), chainEl = document.getElementById('bagChain'), bodyEl = document.getElementById('bagBody');
  if(!bag || !chainEl || !bodyEl) return;

  // Maße in Bildpixeln (Quelle 1024×1536): Aufhängung 520/80, Gelenk = Ring 523/652, Schwerpunkt Sack (aus Alpha) −18/459 ab Ring
  const CHAIN_W = 51, J0 = [3, 572], COM = [-18, 459], BODY_LEN = 625, BODY_R = 131;
  // Silhouette des Sacks je 16 Bildpixel ab Ring: [xMin, xMax] relativ zum Ring (Gurte als Dreieck, dann der Zylinder)
  const ROWS = [[-19,19],[-26,19],[-35,25],[-45,33],[-53,41],[-60,48],[-70,57],[-79,64],[-88,72],[-95,87],[-105,109],
    [-109,121],[-114,126],[-118,128],[-122,129],[-125,129],[-128,128],[-130,126],[-132,125],[-134,124],[-136,122],[-137,121],
    [-139,120],[-141,119],[-143,117],[-145,116],[-146,115],[-148,114],[-149,113],[-151,112],[-152,111],[-154,109],[-155,108],
    [-157,107],[-159,106],[-161,105],[-162,104],[-163,103],[-165,101],[-166,100],[-168,99],[-169,98],[-171,97],[-173,96],
    [-174,95],[-174,94],[-172,92],[-166,88],[-156,81],[-138,67],[-107,39]];

  const T_SWING  = 1.9;     // Periode der Grundschwingung (s) – kleinerer Sack schwingt schneller
  const DAMP     = 0.9;     // Abklingen gesamt (1/s): ~15° -> unter 1° in ~6 s
  const DAMP_REL = 6;       // Wackeln Sack gegen Kette klingt schneller ab
  const KAPPA    = 5;       // Kopplung Maus -> Sack (1/s) – bewusst sanft
  const HAND     = 1;       // „Masse“ der Hand relativ zum Sack
  const MAX_DEG  = 30;      // Energie-Deckel: nie weiter als ~30° ausschlagen
  const m1 = 0.06, M = 1;   // Kette (am Ring gebündelt) / Sack

  let u = 1, j0x = 0, j0y = 0, L1 = 1, d = 1, A = 1, B = 0, C = 1, g = 0, ox = 0, oy = 0;
  let t1 = 0, t2 = 0, w1 = 0, w2 = 0, running = false, last = 0, calm = 0;

  function measure(){
    u = chainEl.offsetWidth / CHAIN_W || u;                        // Pixel pro Bildpixel (CSS --u)
    const r = bag.getBoundingClientRect(); ox = r.left; oy = r.top;  // Aufhängung (Container ist 0×0 und nicht transformiert)
    j0x = J0[0]*u; j0y = J0[1]*u; L1 = Math.hypot(j0x, j0y);
    d = Math.hypot(COM[0], COM[1])*u;
    const Ic = M*((BODY_LEN*u)**2/12 + (BODY_R*u)**2/4);             // Zylinder um die Querachse
    A = (m1+M)*L1*L1; B = M*L1*d; C = M*d*d + Ic;
    // g so, dass die langsame Eigenschwingung T_SWING dauert: det(K − λM) = 0 mit K = diag((m1+M)·L1, M·d), g = 1
    const k1 = (m1+M)*L1, k2 = M*d, qa = A*C - B*B, qb = -(k1*C + k2*A), qc = k1*k2;
    const lam = (-qb - Math.sqrt(qb*qb - 4*qa*qc))/(2*qa);
    g = (2*Math.PI/T_SWING)**2 / lam;
  }

  function step(h){
    const D = t1 - t2, c = Math.cos(D), s = Math.sin(D);
    const f1 = -B*s*w2*w2 - (m1+M)*g*L1*Math.sin(t1) + DAMP_REL*C*(w2 - w1);
    const f2 =  B*s*w1*w1 - M*g*d*Math.sin(t2)        - DAMP_REL*C*(w2 - w1);
    const det = A*C - B*B*c*c;
    const a1 = (C*f1 - B*c*f2)/det, a2 = (A*f2 - B*c*f1)/det;
    const k = Math.exp(-DAMP*h);
    w1 = (w1 + a1*h)*k; w2 = (w2 + a2*h)*k;
    t1 += w1*h; t2 += w2*h;
  }

  // Winkel positiv = nach rechts ausschlagen; Rot(θ)·v = (vx·cosθ + vy·sinθ, −vx·sinθ + vy·cosθ) = CSS rotate(−θ)
  function render(){
    chainEl.style.transform = t1 ? `rotate(${(-t1).toFixed(5)}rad)` : '';
    const c = Math.cos(t1), s = Math.sin(t1);
    const jx = j0x*c + j0y*s - j0x, jy = -j0x*s + j0y*c - j0y;      // Verschiebung des Rings
    bodyEl.style.transform = (t1 || t2) ? `translate(${jx.toFixed(2)}px,${jy.toFixed(2)}px) rotate(${(-t2).toFixed(5)}rad)` : '';
  }

  function frame(now){
    const dt = Math.min(0.05, Math.max(0, (now - last)/1000)); last = now;
    let n = Math.max(1, Math.ceil(dt/0.004)); const h = dt/n;
    while(n--) step(h);
    render();
    const e = Math.abs(t1) + Math.abs(t2) + 0.3*(Math.abs(w1) + Math.abs(w2));
    calm = e < 0.0015 ? calm + dt : 0;
    if(calm > 0.4){ t1 = t2 = w1 = w2 = 0; render(); running = false; return; }   // ruht -> schlafen
    requestAnimationFrame(frame);
  }
  function wake(){ if(running) return; running = true; calm = 0; last = performance.now(); requestAnimationFrame(frame); }

  // Treffer-Test in Sack-Koordinaten (Pixel relativ zum Ring, ungedreht) bzw. auf der Kette
  function hitTest(x, y){
    const qx = x - ox, qy = y - oy;
    const c1 = Math.cos(t1), s1 = Math.sin(t1);
    const rx = j0x*c1 + j0y*s1, ry = -j0x*s1 + j0y*c1;             // Ring relativ zur Aufhängung
    const c2 = Math.cos(t2), s2 = Math.sin(t2), ax = qx - rx, ay = qy - ry;
    const lx = ax*c2 - ay*s2, ly = ax*s2 + ay*c2;                    // Rot(−t2)
    const row = ROWS[Math.floor(ly/(16*u))];
    if(ly >= 0 && row && lx >= (row[0] - 6)*u && lx <= (row[1] + 6)*u) return { body:true, px:lx, py:ly };
    const f = Math.max(0, Math.min(1, (qx*rx + qy*ry)/(L1*L1)));
    if(Math.hypot(qx - rx*f, qy - ry*f) < 10) return { body:false, f };
    return null;
  }

  function push(hit, cvx, dt){
    if(Math.abs(cvx) < 40) return;                                   // ruhige Maus schiebt nicht
    const c1 = Math.cos(t1), s1 = Math.sin(t1);
    let J1 = -j0x*s1 + j0y*c1, J2 = 0;                               // ∂x/∂t1, ∂x/∂t2 am Treffpunkt
    if(hit.body) J2 = -hit.px*Math.sin(t2) + hit.py*Math.cos(t2); else J1 *= hit.f;
    const rel = cvx - (J1*w1 + J2*w2);
    if(rel*cvx <= 0) return;                                         // Sack ist schon schneller weg als die Maus
    const cD = Math.cos(t1 - t2), det = A*C - B*B*cD*cD;
    const q1 = (C*J1 - B*cD*J2)/det, q2 = (A*J2 - B*cD*J1)/det;      // M⁻¹·Jᵀ
    const wInv = J1*q1 + J2*q2; if(!(wInv > 0)) return;              // 1 / effektive Masse am Treffpunkt
    const dv = rel*(1 - Math.exp(-KAPPA*dt))*HAND/(HAND + 1/wInv);
    w1 += q1*dv/wInv; w2 += q2*dv/wInv;
    // Energie-Deckel
    const KE = 0.5*(A*w1*w1 + 2*B*cD*w1*w2 + C*w2*w2);
    const PE = (m1+M)*g*L1*(1 - Math.cos(t1)) + M*g*d*(1 - Math.cos(t2));
    const EMAX = ((m1+M)*g*L1 + M*g*d)*(1 - Math.cos(MAX_DEG*Math.PI/180));
    if(PE + KE > EMAX && KE > 0){ const k = Math.sqrt(Math.max(0, EMAX - PE)/KE); w1 *= k; w2 *= k; }
    wake();
  }

  let px = null, py = 0, pt = 0;
  addEventListener('pointermove', (e)=>{
    const now = e.timeStamp || performance.now();
    if(px === null || now - pt > 100){ px = e.clientX; py = e.clientY; pt = now; return; }   // Neustart nach Pause/Fensterwechsel
    const dt = Math.max(0.001, (now - pt)/1000), dx = e.clientX - px, dy = e.clientY - py;
    let hit = null;                                                  // entlang der Mausbahn prüfen (schnelle Wischer)
    for(let i = 1, n = Math.max(1, Math.ceil(Math.hypot(dx, dy)/12)); i <= n && !hit; i++) hit = hitTest(px + dx*i/n, py + dy*i/n);
    px = e.clientX; py = e.clientY; pt = now;
    if(hit) push(hit, dx/dt, dt);
  }, { passive:true });
  document.addEventListener('pointerleave', ()=>{ px = null; });

  measure();
  addEventListener('resize', ()=>{ measure(); render(); });
  window.__bag = { state:()=>({ t1, t2, w1, w2, running }), kick:(v=300)=>{ w1 += v/(L1 + d); wake(); } };   // zum Testen
})();
