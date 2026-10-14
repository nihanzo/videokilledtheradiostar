# Grünkohl-GIF, 4. Fassung (gegen Flackern und weiße Einkerbungen an den Außenkanten):
# Der Video-Hintergrund ist exakt Schwarz (0) -> alles ab Helligkeit 5 ist Kohl, auch tiefe Schatten (wie im
# Vorlagenbild: dort dunkelgrün). Die Form wird GEOMETRISCH bestimmt statt aus der Helligkeit:
#  1) pro Bild: Kohl = nicht mit dem Rand verbundenes Schwarz; eingeschlossene schwarze Löcher < HOLE_MIN bleiben Kohl
#  2) Mehrheit über 5 Bilder (t-2..t+2) -> kein Pixel springt für 1–2 Bilder an/aus
#  3) Einkerbungen < ~8 px geschlossen, Kontur geglättet; Alpha = weiche Kante (~1.5 px), zeitlich [1 2 1] geglättet
#  4) Randstreifen (3 px) bekommt die Farbe des nahen Inneren -> kein heller Halo, kein dunkler Saum
#  4b) nur in den vom User markierten Bereichen (kale_regions.json, Ausgabe-Koordinaten x,y,w,h; +20 px, weicher Rand):
#     dunkle Stellen (Helligkeit < ~26, über 5 Bilder gemittelt) werden ausgeschnitten -> weiß
#  4c) nur in den Bereichen aus kale_fill.json (+20 px): kleine weiße/halbdurchsichtige Lücken im Kohl (Alpha < 0.9,
#     < FILL_MAX px² im Ausgabe-Maßstab, nicht mit großen Durchblicken verbunden) werden mit Grün gefüllt = Umgebungsfarbe + Blattstruktur eines
#     Nachbarbereichs; Entscheidung über 5 Bilder gemittelt (kein Flackern)
#  4d) Bereiche aus kale_keep.json: dort bleibt der Kohl DURCHGEHEND grün – jede Lücke im Kohl (nicht der große
#     Außenraum) wird gefüllt, unabhängig von der Größe; Lücken, die den Bereich berühren, ganz (bis 60 px darüber hinaus)
#  5) deckend auf Weiß + eingebackener Schatten (wie CSS drop-shadow 0 18px 30px rgba(0,0,0,.18)), 64 px Rand
# Aufruf: python3 key4.py <LAST> <Breite_Kohl> [HOLE_MIN=3000]  -> kgif/seq/f%03d.png (hin und zurück)
# Danach: gifski --width 960 --fps 24 --quality 90 -o ../../assets/img/kale.gif kgif/seq/f*.png
import numpy as np, glob, json, os, sys, subprocess
from PIL import Image, ImageFilter, ImageDraw
LAST = int(sys.argv[1]); WOUT = int(sys.argv[2]); HOLE_MIN = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
fs = sorted(glob.glob('kall/a*.png'))[:LAST+1]; N = len(fs)
lut = lambda t: (lambda v: 255 if v > t else 0)
L8 = lambda m: Image.fromarray((m*255).astype(np.uint8)) if m.dtype == bool else Image.fromarray(m)

def gblur(x, s):                                     # Gauß-Weichzeichnung (float) per FFT, mit Rand gegen Umlauf
    p = int(3*s) + 2; xp = np.pad(x, p)
    fy = np.fft.fftfreq(xp.shape[0])[:, None]; fx = np.fft.rfftfreq(xp.shape[1])[None, :]
    k = np.exp(-2*(np.pi*s)**2*(fx**2 + fy**2))
    return np.fft.irfft2(np.fft.rfft2(xp)*k, s=xp.shape)[p:-p, p:-p]

def big_only(m, amin):                               # nur Flächen >= amin behalten (Swift-Komponentenfilter ccfilter)
    H, W = m.shape; (m.astype(np.uint8)*255).tofile('cc_in.raw')
    subprocess.run(['./ccfilter', 'cc_in.raw', str(W), str(H), str(amin), 'cc_out.raw'], check=True, capture_output=True)
    return np.fromfile('cc_out.raw', np.uint8).reshape(H, W) > 127

def plant(a):                                        # 1) Kohl-Maske eines Bildes
    lum = Image.fromarray(a.max(2)).filter(ImageFilter.GaussianBlur(0.8)); H, W = a.shape[:2]
    ink = lum.point(lut(5)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    fl = Image.new('L', (W+2, H+2), 0); fl.paste(ink, (1, 1)); ImageDraw.floodfill(fl, (0, 0), 128)
    inside = np.asarray(fl.crop((1, 1, W+1, H+1))) != 128
    dark = np.asarray(lum) <= 5
    wide = np.asarray(L8(dark).filter(ImageFilter.GaussianBlur(2)).point(lut(245)).filter(ImageFilter.GaussianBlur(2)).point(lut(10))) > 0
    return inside & ~big_only(wide & inside, HOLE_MIN)

A = [np.asarray(Image.open(f).convert('RGB')) for f in fs]
P = [plant(a) for a in A]
rf = lambda t: abs(t) if t < 0 else (2*(N-1) - t if t > N-1 else t)   # Spiegeln an den Enden (Hin-und-zurück-Schleife)
alphas = []
for t in range(N):
    maj = sum(P[rf(t+k)].astype(np.uint8) for k in (-2, -1, 0, 1, 2)) >= 3          # 2) Mehrheit
    m = L8(maj).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))   # 3) Einkerbungen schließen
    m = np.asarray(m).astype(np.float32)/255
    m = gblur(m, 1.5) > 0.5                                                          #    Kontur glätten
    b = gblur(m.astype(np.float32), 1.0); u = np.clip((b - 0.35)/0.5, 0, 1)
    alphas.append((u*u*(3 - 2*u)).astype(np.float16))
alphas = [((alphas[rf(t-1)].astype(np.float32) + 2*alphas[t] + alphas[rf(t+1)])/4).astype(np.float16) for t in range(N)]

# Ausschnitt (gemeinsam über alle Bilder) + Prüfung, dass nichts am Bildrand klebt
U = np.max(alphas, axis=0) > 0.02; ys, xs = np.where(U)
edge = [(i, int((al[:, -2:] > 0.05).sum()), int((al[:, :2] > 0.05).sum()), int((al[-2:] > 0.05).sum())) for i, al in enumerate(alphas)]
print('Rand-Pixel (Bild, rechts, links, unten) > 0:', [e for e in edge if any(e[1:])][:8])
x0, y0, x1, y1 = xs.min()-4, ys.min()-4, xs.max()+5, ys.max()+5
sc = WOUT/(x1-x0); PADO = 64; PAD = int(round(PADO/sc))
SIG, OFF, OP = 15/sc, 18/sc, 0.18
X0, Y0, X1, Y1 = x0-PAD, y0-PAD, x1+PAD, y1+PAD
Wout = WOUT + 2*PADO; Hout = round((Y1-Y0)*sc)
json.dump({'box': [int(x0), int(y0), int(x1), int(y1)], 'pad_out': PADO, 'size': [Wout, Hout]}, open('kgif/meta4.json', 'w'))
print('Kasten', x0, y0, x1, y1, '-> Ausgabe', Wout, 'x', Hout, ' (Kohl', WOUT, 'x', Hout-2*PADO, ')')

def place(arr):
    out = np.zeros((Y1-Y0, X1-X0) + arr.shape[2:], np.float32)
    sy0, sx0 = max(Y0, 0), max(X0, 0); sy1, sx1 = min(Y1, arr.shape[0]), min(X1, arr.shape[1])
    out[sy0-Y0:sy1-Y0, sx0-X0:sx1-X0] = arr[sy0:sy1, sx0:sx1]; return out

REG = json.load(open('kale_regions.json')).values() if os.path.exists('kale_regions.json') else []
kx, ky = (X1-X0)/Wout, (Y1-Y0)/Hout
reg = np.zeros((Y1-Y0, X1-X0), np.float32)
for x, y, w, h in REG:
    m = 20; reg[int((y-m)*ky):int((y+h+m)*ky), int((x-m)*kx):int((x+w+m)*kx)] = 1
reg = gblur(reg, 10.0) if len(REG) else reg
lumf = lambda t: gblur(place(A[t].max(2).astype(np.float32)), 1.2)

def rect_mask(path, m=20):
    if not os.path.exists(path): return None
    r = np.zeros((Y1-Y0, X1-X0), bool)
    for x, y, w, h in json.load(open(path)).values():
        r[max(0, int((y-m)*ky)):int((y+h+m)*ky), max(0, int((x-m)*kx)):int((x+w+m)*kx)] = True
    return r
fillreg = rect_mask('kale_fill.json'); FILL_MAX = 1200
keep_in, keep_out = rect_mask('kale_keep.json', 20), rect_mask('kale_keep.json', 60)
def reconstruct(seed, mask):                         # alle Pixel von mask, die mit seed zusammenhängen
    cur = seed & mask
    for _ in range(60):
        nxt = (np.asarray(L8(cur).filter(ImageFilter.MaxFilter(9))) > 0) & mask
        if np.array_equal(nxt, cur): break
        cur = nxt
    return cur

ALS = []                                                                       # Alpha je Bild nach 4b
for t in range(N):
    al = place(alphas[t].astype(np.float32))
    if len(REG):                                                               # 4b) dunkle Stellen in den Bereichen -> weiß
        lv = sum(w*lumf(rf(t+k)) for k, w in zip(range(-2, 3), (1, 2, 3, 2, 1)))/9
        u = np.clip((lv - 18)/16, 0, 1); keep = u*u*(3 - 2*u)
        al = al*(1 - reg*(1 - keep))
    ALS.append(al.astype(np.float16))
FW = None
if fillreg is not None or keep_in is not None:                                 # 4c/4d) Lücken (je Bild) …
    amax = int(FILL_MAX*kx*ky)
    FM = []
    for t in range(N):
        holes = ALS[t] < 0.9; fm = np.zeros_like(holes)
        if fillreg is not None: fm |= holes & ~big_only(holes, amax) & fillreg
        if keep_in is not None:
            inner_holes = holes & ~big_only(holes, 200000)                     # alles außer dem großen Außenraum
            fm |= reconstruct(inner_holes & keep_in, inner_holes & keep_out)
        FM.append(fm.astype(np.float16))
    FW = [np.clip(2*sum(w*FM[rf(t+k)].astype(np.float32) for k, w in zip(range(-2, 3), (1, 2, 3, 2, 1)))/9, 0, 1)
          for t in range(N)]                                                   # … über 5 Bilder gemittelt

# Ausgabe größer als der Kasten (echte Details aus der 1920er Quelle, Kasten ≈ 1876 px breit -> bis ~1.6×):
# KALE_FOUT=1.6 KALE_OUT=kgif/seq16 python3 key4.py 53 1150   (Bereiche/Ränder bleiben in 1278er-Koordinaten)
FOUT = float(os.environ.get('KALE_FOUT', '1')); OUTD = os.environ.get('KALE_OUT', 'kgif/seq')
# 4e) KALE_DARKR=1: nur auf der rechten Kohl-Hälfte (weicher Übergang 42–58 % der Breite): dunkler Saum am Umriss
#     (~7 Quell-px, dunkler als das nahe Blattinnere) bekommt weich die Farbe von innen; fast Schwarzes bis ~11 px vom
#     Umriss (Helligkeit < DR_HI, voll ab DR_LO) wird durchsichtig; Stärke DR_K
DARKR = os.environ.get('KALE_DARKR') == '1'; DR_LO, DR_HI, DR_S, DR_K = 8.0, 24.0, 3.5, 0.85
_u = np.clip((np.arange(X1 - X0, dtype=np.float32)/(X1 - X0) - 0.42)/0.16, 0, 1); RW = (_u*_u*(3 - 2*_u))[None, :]
WF, HF = (Wout, Hout) if FOUT == 1 else (int(Wout*FOUT)//2*2, int(Hout*FOUT)//2*2)
os.makedirs(OUTD, exist_ok=True); [os.remove(f) for f in glob.glob(OUTD + '/*.png')]
imgs = []
for t in range(N):
    c = place(A[t].astype(np.float32)); al = ALS[t].astype(np.float32)
    if FW is not None and FW[t].any():                                         # 4c) mit Grün füllen
        f = np.clip(gblur(FW[t], 1.0)*1.4, 0, 1)
        lv = c.max(2); ok = ((al > 0.9) & (lv > 30)).astype(np.float32)
        fillc = None
        for sg in (5.0, 12.0, 30.0):                                           # Umgebungsfarbe, für große Lücken weiter weg
            wo = gblur(ok, sg); av = np.dstack([gblur(c[..., k]*ok, sg) for k in range(3)])/np.maximum(wo, 1e-4)[..., None]
            if fillc is None: fillc, have = av, np.clip(wo*20, 0, 1)
            else: fillc = fillc*have[..., None] + av*(1 - have[..., None]); have = np.maximum(have, np.clip(wo*20, 0, 1))
        oke = np.asarray(L8(ok > 0.5).filter(ImageFilter.MinFilter(9))).astype(np.float32)/255   # nur sicheres Inneres
        detail = np.zeros_like(c); got = np.zeros(c.shape[:2], np.float32)
        for sh_ in ((7, 11), (-13, 17), (21, -9), (-25, -23), (31, 27), (-41, 5)):  # Blattstruktur vom Nachbarn
            cs = np.roll(c, sh_, axis=(0, 1)); oks = np.roll(oke, sh_, axis=(0, 1))*(1 - got)
            detail += (cs - np.dstack([gblur(cs[..., k], 2.0) for k in range(3)]))*oks[..., None]; got += oks
        fillc = np.clip(fillc + 0.9*detail, 0, 255)
        fc = np.clip(gblur(FW[t], 2.0)*3.0, 0, 1)[..., None]                   # Farbe 2–3 px über den Lückenrand (kein dunkler Umriss)
        c = c*(1 - fc) + fillc*fc; al = np.maximum(al, f)
    if DARKR:                                                                  # 4e) rechte Hälfte: dunkle Ränder sanft entfernen
        lv = c.max(2)
        k6 = (gblur((al > 0.5).astype(np.float32), DR_S) > 0.98).astype(np.float32)   # Inneres ohne ~7 px Rand
        w6 = gblur(k6, 4.0); av6 = np.dstack([gblur(c[..., k]*k6, 4.0) for k in range(3)])/np.maximum(w6, 1e-3)[..., None]
        ring = ((al > 0.02) & (k6 < 0.5) & (w6 > 0.02)).astype(np.float32)
        rel = lv/np.maximum(av6.max(2), 1.0)                                   # Helligkeit relativ zum nahen Blattinneren
        mix = gblur(np.clip((0.97 - rel)/0.35, 0, 1)*ring*RW, 1.0)*ring         # dunkler als innen -> weich zur Farbe von innen
        c = c + (av6 - c)*(DR_K*mix)[..., None]
        lum = (lumf(rf(t-1)) + 2*lumf(t) + lumf(rf(t+1)))/4                      # fast Schwarzes (zeitlich [1 2 1], kein Flackern)
        kb = (gblur((al > 0.5).astype(np.float32), 6.0) > 0.97).astype(np.float32)   # bis ~11 px vom Umriss
        al = al*(1 - DR_K*np.clip((DR_HI - lum)/(DR_HI - DR_LO), 0, 1)*(1 - kb)*RW)
    inner = np.asarray(L8(al > 0.5).filter(ImageFilter.MinFilter(7))).astype(np.float32)/255   # 3 px eingezogen
    wi = gblur(inner, 3.0); avg = np.dstack([gblur(c[..., k]*inner, 3.0) for k in range(3)])/np.maximum(wi, 1e-3)[..., None]
    band = (inner < 0.5) & (wi > 0.02)                                         # 4) Randstreifen -> Farbe von innen
    c[band] = avg[band]
    sh = gblur(np.roll(al, int(round(OFF)), axis=0), SIG)
    bg = 255.0*(1 - OP*np.clip(sh, 0, 1))
    out = np.clip(c*al[..., None] + (1 - al)[..., None]*bg[..., None], 0, 255)
    imgs.append(Image.fromarray(out.astype(np.uint8)).resize((WF, HF), Image.LANCZOS))
order = list(range(N)) + list(range(N-2, 0, -1))
for k, j in enumerate(order): imgs[j].save(f'{OUTD}/f{k:03d}.png')
print(len(order), 'Bilder')
