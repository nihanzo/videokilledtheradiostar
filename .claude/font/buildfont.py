# Baut aus den Glyphen-Masken (glyphs.py) eine TrueType-Datei: Kontur per Marching Squares auf der
# weichgezeichneten Maske (50-%-Linie), vereinfacht (Douglas-Peucker), Tabellen von Hand geschrieben.
import sys, struct, math
import numpy as np
sys.path.insert(0, '.')
import glyphs as G

LEVEL = 127.5

def contours(v):
    inside = v > LEVEL
    tl, tr, bl, br = inside[:-1, :-1], inside[:-1, 1:], inside[1:, :-1], inside[1:, 1:]
    case = tl*8 + tr*4 + br*2 + bl*1
    rs, cs = np.nonzero((case > 0) & (case < 15))
    def pt(key):
        k, r, c = key
        if k == 'h':                                   # waagrechte Kante (r,c)-(r,c+1)
            a, b = v[r, c], v[r, c+1]; t = (LEVEL-a)/(b-a); return (c+t, r)
        a, b = v[r, c], v[r+1, c]; t = (LEVEL-a)/(b-a); return (c, r+t)
    segs = []
    for r, c in zip(rs, cs):
        k = case[r, c]; T_, B_, L_, R_ = ('h', r, c), ('h', r+1, c), ('v', r, c), ('v', r, c+1)
        center = (v[r, c]+v[r, c+1]+v[r+1, c]+v[r+1, c+1])/4 > LEVEL
        tab = {1: [(L_, B_)], 2: [(B_, R_)], 3: [(L_, R_)], 4: [(T_, R_)], 6: [(T_, B_)], 7: [(L_, T_)],
               8: [(L_, T_)], 9: [(T_, B_)], 11: [(T_, R_)], 12: [(L_, R_)], 13: [(B_, R_)], 14: [(L_, B_)],
               5: [(L_, T_), (B_, R_)] if center else [(T_, R_), (L_, B_)],
               10: [(T_, R_), (L_, B_)] if center else [(L_, T_), (B_, R_)]}
        segs += tab[int(k)]
    by = {}
    for i, (a, b) in enumerate(segs):
        by.setdefault(a, []).append(i); by.setdefault(b, []).append(i)
    used = [False]*len(segs); loops = []
    for i in range(len(segs)):
        if used[i]: continue
        used[i] = True; a, b = segs[i]; loop = [a]; cur = b
        while cur != a:
            loop.append(cur)
            nxt = [j for j in by[cur] if not used[j]]
            if not nxt: break
            j = nxt[0]; used[j] = True; s0, s1 = segs[j]; cur = s1 if s0 == cur else s0
        loops.append([pt(k) for k in loop])
    return loops

def rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = np.array(pts[0]), np.array(pts[-1]); d = b - a; L = math.hypot(*d)
    P = np.array(pts)
    dist = np.abs(d[0]*(P[:, 1]-a[1]) - d[1]*(P[:, 0]-a[0]))/L if L > 0 else np.hypot(*(P - a).T)
    i = int(np.argmax(dist))
    if dist[i] > eps: return rdp(pts[:i+1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]

def simplify_closed(loop, eps=0.75):
    P = np.array(loop); c = P.mean(0); i0 = int(np.argmax(np.hypot(*(P - c).T)))
    loop = loop[i0:] + loop[:i0]; P = np.array(loop); i1 = int(np.argmax(np.hypot(*(P - P[0]).T)))
    out = rdp(loop[:i1+1], eps)[:-1] + rdp(loop[i1:] + [loop[0]], eps)[:-1]
    res = []
    for x, y in out:
        q = (int(round(x)), int(round(y)))
        if not res or res[-1] != q: res.append(q)
    if len(res) > 1 and res[0] == res[-1]: res.pop()
    return res

def area(c): return sum(x0*y1 - x1*y0 for (x0, y0), (x1, y1) in zip(c, c[1:] + c[:1]))/2
def inside_poly(p, c):
    x, y = p; n = False
    for (x0, y0), (x1, y1) in zip(c, c[1:] + c[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0)*(x1 - x0)/(y1 - y0): n = not n
    return n

def glyph_outline(ch):
    f, w, lsb, rsb = G.GL[ch]; g = G.G(w); soft = G.soften(f(g))
    cs = []
    for loop in contours(soft):
        if len(loop) < 8: continue
        # Pixelmitte -> Font-Einheiten (x: Tinte beginnt bei lsb; y nach oben)
        pts = [(x + 0.5 - G.PAD + lsb, G.TOP - (y + 0.5)) for x, y in loop]
        c = simplify_closed(pts)
        if len(c) >= 3 and abs(area(c)) > 40: cs.append(c)
    fixed = []
    for i, c in enumerate(cs):                       # außen im Uhrzeigersinn, Löcher dagegen (TrueType)
        depth = sum(inside_poly((c[0][0]+0.01, c[0][1]+0.01), o) for j, o in enumerate(cs) if j != i)
        want_cw = depth % 2 == 0
        if (area(c) < 0) != want_cw: c = c[::-1]
        fixed.append(c)
    return fixed, lsb + w + rsb

# ---------------- TrueType schreiben ----------------
def checksum(b):
    b = b + b'\0'*((4 - len(b) % 4) % 4); return sum(struct.unpack('>%dI' % (len(b)//4), b)) & 0xFFFFFFFF

def build(path, family='Nihanzo Grotesk'):
    chars = sorted(G.GL.keys())
    order = ['.notdef', ' '] + chars
    outlines = {'.notdef': ([[(60, 0), (60, 700), (440, 700), (440, 0)][::-1], [(120, 60), (380, 60), (380, 640), (120, 640)][::-1][::-1]], 500),
                ' ': ([], 270)}
    # .notdef: Kasten mit Loch (außen im Uhrzeigersinn)
    outlines['.notdef'] = ([[(60, 0), (60, 700), (440, 700), (440, 0)], [(120, 60), (380, 60), (380, 640), (120, 640)]], 500)
    for ch in chars: outlines[ch] = glyph_outline(ch)
    glyf = b''; loca = []; hmtx = b''; maxPts = maxCt = 0
    gx0 = gy0 = 10**9; gx1 = gy1 = -10**9; advMax = 0; minL = minR = 10**9; xMaxExt = -10**9; widths = []
    for name in order:
        cs, adv = outlines[name]; loca.append(len(glyf)); advMax = max(advMax, adv); widths.append(adv)
        if not cs:
            hmtx += struct.pack('>Hh', adv, 0); continue
        xs = [x for c in cs for x, y in c]; ys = [y for c in cs for x, y in c]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        gx0, gy0, gx1, gy1 = min(gx0, x0), min(gy0, y0), max(gx1, x1), max(gy1, y1)
        minL = min(minL, x0); minR = min(minR, adv - x1); xMaxExt = max(xMaxExt, x1)
        ends = []; n = 0
        for c in cs: n += len(c); ends.append(n - 1)
        maxPts = max(maxPts, n); maxCt = max(maxCt, len(cs))
        g = struct.pack('>hhhhh', len(cs), x0, y0, x1, y1) + struct.pack('>%dH' % len(ends), *ends) + struct.pack('>H', 0)
        g += bytes([1])*n
        px = py = 0; dx = []; dy = []
        for c in cs:
            for x, y in c: dx.append(x - px); dy.append(y - py); px, py = x, y
        g += struct.pack('>%dh' % n, *dx) + struct.pack('>%dh' % n, *dy)
        g += b'\0'*((4 - len(g) % 4) % 4); glyf += g
        hmtx += struct.pack('>Hh', adv, x0)
    loca.append(len(glyf))
    ng = len(order); ASC, DSC = 900, -250
    head = struct.pack('>IIIIHHqqhhhhHHhhh', 0x00010000, 0x00010000, 0, 0x5F0F3CF5, 0x000B, 1000, 0, 0,
                       gx0, gy0, gx1, gy1, 0, 8, 2, 1, 0)
    hhea = struct.pack('>IhhhHhhhhhhhhhhhH', 0x00010000, ASC, DSC, 0, advMax, minL, minR, xMaxExt, 1, 0, 0, 0, 0, 0, 0, 0, ng)
    maxp = struct.pack('>IHHHHHHHHHHHHHH', 0x00010000, ng, maxPts, maxCt, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0)
    # cmap (Format 4): Kleinbuchstaben auch für Großbuchstaben (außer eigenen Versal-Glyphen), geschütztes Leerzeichen = Leerzeichen
    gid = {name: i for i, name in enumerate(order)}
    m = {ord(' '): gid[' '], 0xA0: gid[' ']}
    for ch in chars:
        m[ord(ch)] = gid[ch]
        if ch.isalpha() and ch.upper() != ch and ch.upper() not in chars: m[ord(ch.upper())] = gid[ch]
    codes = sorted(m)
    segs = [(c, c, (m[c] - c) & 0xFFFF) for c in codes] + [(0xFFFF, 0xFFFF, 1)]
    sc = len(segs); sr = 2*(2**int(math.log2(sc))); es = int(math.log2(sr//2)); rs = 2*sc - sr
    sub = struct.pack('>HHHHHHH', 4, 0, 0, 2*sc, sr, es, rs)
    sub += struct.pack('>%dH' % sc, *[e for s, e, d in segs]) + b'\0\0'
    sub += struct.pack('>%dH' % sc, *[s for s, e, d in segs]) + struct.pack('>%dH' % sc, *[d for s, e, d in segs])
    sub += struct.pack('>%dH' % sc, *([0]*sc))
    sub = sub[:2] + struct.pack('>H', len(sub)) + sub[4:]
    cmap = struct.pack('>HH', 0, 2) + struct.pack('>HHI', 0, 3, 20) + struct.pack('>HHI', 3, 1, 20) + sub
    avg = int(sum(w for w in widths if w)/len([w for w in widths if w]))
    os2 = struct.pack('>HhHHHhhhhhhhhhhh', 4, avg, 800, 5, 0, 650, 600, 0, 75, 650, 600, 0, 350, 50, 280, 0)
    os2 += bytes([2, 11, 8, 2, 2, 4, 2, 2, 2, 4])    # Panose: Sans, sehr fett
    os2 += struct.pack('>IIII', 0x00000003, 0, 0, 0) + b'NHZO'
    os2 += struct.pack('>HHHhhhHHII', 0x00C0, min(codes), max(c for c in codes if c < 0xFFFF), ASC, DSC, 0,
                       max(ASC, gy1), max(-DSC, -gy0), 0x00000001, 0)
    os2 += struct.pack('>hhHHH', G.H, G.A, 32, 32, 2)
    names = {1: family, 2: 'Regular', 3: family + ' 1.000', 4: family, 5: 'Version 1.000',
             6: family.replace(' ', '') + '-Regular'}
    recs = b''; strs = b''
    for nid, sv in names.items():
        b = sv.encode('utf-16-be'); recs += struct.pack('>HHHHHH', 3, 1, 0x409, nid, len(b), len(strs)); strs += b
    name = struct.pack('>HHH', 0, len(names), 6 + 12*len(names)) + recs + strs
    post = struct.pack('>IIhhIIIII', 0x00030000, 0, -120, 60, 0, 0, 0, 0, 0)
    loca_b = struct.pack('>%dI' % len(loca), *loca)
    tables = {b'OS/2': os2, b'cmap': cmap, b'glyf': glyf, b'head': head, b'hhea': hhea, b'hmtx': hmtx,
              b'loca': loca_b, b'maxp': maxp, b'name': name, b'post': post}
    tags = sorted(tables); nt = len(tags); sr = 16*(2**int(math.log2(nt))); es = int(math.log2(sr//16)); rs = nt*16 - sr
    out = struct.pack('>IHHHH', 0x00010000, nt, sr, es, rs); off = 12 + 16*nt; dirs = b''; body = b''
    for t in tags:
        d = tables[t]; dirs += struct.pack('>4sIII', t, checksum(d), off + len(body), len(d))
        body += d + b'\0'*((4 - len(d) % 4) % 4)
    font = bytearray(out + dirs + body)
    adj = (0xB1B0AFBA - checksum(bytes(font))) & 0xFFFFFFFF
    hoff = off + body.index(head) if False else None
    # Position der head-Tabelle aus dem Verzeichnis
    for i, t in enumerate(tags):
        if t == b'head':
            _, _, o, _ = struct.unpack('>4sIII', dirs[16*i:16*i+16]); font[o+8:o+12] = struct.pack('>I', adj)
    open(path, 'wb').write(bytes(font))
    print('glyphs', ng, 'maxPts', maxPts, 'bytes', len(font), 'bbox', gx0, gy0, gx1, gy1)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'NihanzoGrotesk.ttf')
