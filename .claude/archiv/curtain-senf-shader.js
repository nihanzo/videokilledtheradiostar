// Archiv 2026-10-06: Senf-Shader des Vorhangs (Körnung, Vignette, aquarellige Flecken). Wurde aus startpage.html
// entfernt, weil der Vorhang seit 2026-10-05 ganz weiß ist (gl_FragColor = Weiß) – Weiß kommt jetzt per CSS.
// Zum Wiederbeleben: Block wieder in curtainIntro() einsetzen, gl_FragColor = vec4(cream, 1.0).
    // ---- WebGL: Senf wie das Hintergrundbild der Startseite (Film-Look: Körnung, Vignette, Lichtfleck) – statisch ----
    const gl = cv.getContext('webgl', { antialias:false, premultipliedAlpha:false, alpha:true });
    if(gl){
      const sh = (type, src)=>{ const o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); return o; };
      const prog = gl.createProgram();
      gl.attachShader(prog, sh(gl.VERTEX_SHADER, `attribute vec2 aPos; varying vec2 vUv;
        void main(){ vUv = aPos*0.5+0.5; gl_Position = vec4(aPos,0.0,1.0); }`));
      gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, `precision highp float; varying vec2 vUv; uniform vec2 uRes;
        float hash(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
        float noise(vec2 p){ vec2 i=floor(p), f=fract(p);
          float a=hash(i), b=hash(i+vec2(1.,0.)), c=hash(i+vec2(0.,1.)), d=hash(i+vec2(1.,1.));
          vec2 u=f*f*(3.-2.*f); return mix(mix(a,b,u.x),mix(c,d,u.x),u.y); }
        void main(){
          vec2 uv = vUv;
          float grain = noise(uv*uRes/2.4);
          float vig = 1.0 - smoothstep(0.36, 1.12, length((uv-vec2(0.5,0.42))*vec2(1.1,1.0)));
          vec3 cream = vec3(0.776,0.706,0.573);                    // #C6B492 = Senf-Ton des Glas-Fotos auf der Startseite
          cream *= mix(0.90, 1.0, vig);
          // sanfte, verwaschene Flecken, die ins Weiße gehen – mal größer, mal kleiner (Rand per Rauschen unruhig wie Aquarell)
          vec2 asp = vec2(uRes.x/uRes.y, 1.0);
          float spots = 0.0;
          for(int i = 0; i < 18; i++){
            float fi = float(i);
            vec2 c = vec2(hash(vec2(fi, 1.37)), hash(vec2(fi, 7.11)));
            float r = mix(0.05, 0.36, pow(hash(vec2(fi, 3.73)), 1.8));        // meist klein, einige groß
            float a = mix(0.25, 0.70, hash(vec2(fi, 9.29)));
            vec2 q = (uv - c)*asp;
            float an = hash(vec2(fi, 5.51))*6.2832, cs = cos(an), sn = sin(an);
            q = vec2(cs*q.x - sn*q.y, sn*q.x + cs*q.y);                       // zufällig gedreht …
            q.x *= mix(0.55, 1.5, hash(vec2(fi, 2.21)));                       // … und gestreckt
            q += (vec2(noise(uv*3.5 + fi*2.3), noise(uv*3.5 + fi*5.9 + 11.0)) - 0.5)*r*1.1;   // verzerrt (verwaschen)
            float d = length(q) + (noise(uv*11.0 - fi*1.7) - 0.5)*r*0.45;
            float k = smoothstep(r, 0.0, d);                                   // weich, ohne hellen Kern
            spots = 1.0 - (1.0 - spots)*(1.0 - k*a);
          }
          cream = mix(cream, vec3(1.0), spots*0.8);
          cream = mix(cream, cream*0.93, grain*0.35);
          cream += smoothstep(0.75,0.0, length(uv-vec2(0.34,0.72)))*0.045;
          gl_FragColor = vec4(1.0);                                // Vorhang ganz weiß (2026-10-05); Senf-Flecken oben bleiben für später
        }`));
      gl.linkProgram(prog); gl.useProgram(prog);
      const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
      const aPos = gl.getAttribLocation(prog, 'aPos'); gl.enableVertexAttribArray(aPos); gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
      const uRes = gl.getUniformLocation(prog,'uRes');
      const paint = ()=>{ const dpr = Math.min(devicePixelRatio||1, 2);
        cv.width = Math.round(innerWidth*dpr); cv.height = Math.round(innerHeight*dpr); gl.viewport(0,0,cv.width,cv.height);
        gl.uniform2f(uRes, cv.width, cv.height); gl.clearColor(0,0,0,0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        cv.style.background = 'transparent'; };                         // CSS-Senf nur bis zum 1. Bild
      addEventListener('resize', paint); paint();
    }

