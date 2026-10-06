# Grünkohl-GIF, 3. Fassung: ALLES, was nicht schwarzer Hintergrund ist, bleibt drin (keine Farbfilterung mehr).
# Kante weich aus der Helligkeit: Hintergrund ist schwarz -> beobachtete Farbe = α·Kohl, α = v / v_Kohl (v = max(RGB),
# v_Kohl = Helligkeit des sicheren Inneren in der Nähe). Danach direkt auf Weiß verrechnet (+ Schatten wie vorher
# CSS drop-shadow 0 18px 30px rgba(0,0,0,.18)) -> deckendes GIF ohne harte 1-Bit-Kante (kein Flackern, kein Saum).
# Eingeschlossene schwarze Löcher < HOLE_MIN px (Original-Pixel) werden NICHT ausgeschnitten -> Originalbild bleibt.
# Aufruf: python3 key3.py <LAST> <Breite_Kohl> [HOLE_MIN=3000]   -> kgif/seq/f%03d.png (hin und zurück) + kgif/meta3.json
import numpy as np, glob, json, os, sys, subprocess
from PIL import Image, ImageFilter, ImageDraw, ImageChops
LAST = int(sys.argv[1]); WOUT = int(sys.argv[2]); HOLE_MIN = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
fs = sorted(glob.glob('kall/a*.png'))[:LAST+1]
lut = lambda t: (lambda v: 255 if v > t else 0)

def gblur(x, s):                                     # Gauß-Weichzeichnung (float) per FFT, mit Rand gegen Umlauf
    p = int(3*s) + 2; xp = np.pad(x, p)
    fy = np.fft.fftfreq(xp.shape[0])[:, None]; fx = np.fft.rfftfreq(xp.shape[1])[None, :]
    k = np.exp(-2*(np.pi*s)**2*(fx**2 + fy**2))
    return np.fft.irfft2(np.fft.rfft2(xp)*k, s=xp.shape)[p:-p, p:-p]

def big_only(m, amin):                               # nur Flächen >= amin behalten (Swift-Komponentenfilter ccfilter)
    H, W = m.shape; (m.astype(np.uint8)*255).tofile('cc_in.raw')
    subprocess.run(['./ccfilter', 'cc_in.raw', str(W), str(H), str(amin), 'cc_out.raw'], check=True, capture_output=True)
    return np.fromfile('cc_out.raw', np.uint8).reshape(H, W) > 127

def key(a):
    v = a.max(2); H, W = v.shape
    lum = Image.fromarray(np.clip(v, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    ink = lum.point(lut(14)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    fl = Image.new('L', (W+2, H+2), 0); fl.paste(ink, (1, 1)); ImageDraw.floodfill(fl, (0, 0), 128)
    inside = fl.crop((1, 1, W+1, H+1)).point(lambda q: 0 if q == 128 else 255)
    dark = ImageChops.invert(lum.point(lut(14)))                        # schwarze Lücken ab ~5 px Breite …
    holes = np.asarray(dark.filter(ImageFilter.GaussianBlur(2)).point(lut(245)).filter(ImageFilter.GaussianBlur(2)).point(lut(10))) > 0
    holes = big_only(holes & (np.asarray(inside) > 0), HOLE_MIN)       # … aber nur große Durchblicke = Hintergrund
    inside = Image.fromarray(((np.asarray(inside) > 0) & ~holes).astype(np.uint8)*255)
    solid = np.asarray(inside.filter(ImageFilter.MinFilter(9))).astype(np.float32)/255   # sicheres Inneres (4 px eingezogen)
    near = np.asarray(inside.filter(ImageFilter.MaxFilter(13))) > 0                       # bis 6 px außerhalb
    ws = gblur(solid, 5.0); vref = gblur(v*solid, 5.0)/np.maximum(ws, 1e-3)
    vref = np.where(ws > 0.02, np.maximum(vref, 30.0), 255.0)
    af = np.clip((v - 8.0)/(vref - 8.0), 0, 1)*near
    # heller grauer Saum (Firefly-Halo) an der Kontur: im Kantenband zählt nur, was farbig ist (grau -> durchsichtig)
    sat = (v - a.min(2))/np.maximum(v, 1.0); t = np.clip((sat - 0.10)/0.18, 0, 1)
    return np.maximum(af*t*t*(3 - 2*t), solid)

def frame(i):
    a = np.asarray(Image.open(fs[i]).convert('RGB'))
    return a, key(a.astype(np.float32)).astype(np.float16)          # Speicher sparen

# 1) Alpha aller Bilder -> gemeinsamer Ausschnitt + Prüfung, dass nichts am Bildrand klebt
data = [frame(i) for i in range(len(fs))]
U = np.max([al for _, al in data], axis=0) > 0.02
ys, xs = np.where(U)
edge = [(i, int((al[:, -2:] > 0.05).sum()), int((al[:, :2] > 0.05).sum()), int((al[-2:] > 0.05).sum())) for i, (_, al) in enumerate(data)]
print('Rand-Pixel (Bild, rechts, links, unten) > 0:', [e for e in edge if any(e[1:])][:8])
x0, y0, x1, y1 = xs.min()-4, ys.min()-4, xs.max()+5, ys.max()+5
sc = WOUT/(x1-x0)                                    # Ausgabe-Maßstab (Kohl-Kasten = WOUT px breit)
PADO = 64; PAD = int(round(PADO/sc))                 # Rand für den Schatten (Ausgabe 64 px)
SIG, OFF, OP = 15/sc, 18/sc, 0.18                    # CSS 30px Blur = σ 15, Versatz 18, Deckkraft .18
X0, Y0, X1, Y1 = x0-PAD, y0-PAD, x1+PAD, y1+PAD
Wout = WOUT + 2*PADO; Hout = round((Y1-Y0)*sc)
json.dump({'box': [int(x0), int(y0), int(x1), int(y1)], 'pad_out': PADO, 'size': [Wout, Hout], 'kale': [WOUT, Hout-2*PADO]}, open('kgif/meta3.json', 'w'))
print('Kasten', x0, y0, x1, y1, '-> Ausgabe', Wout, 'x', Hout, ' (Kohl', WOUT, 'x', Hout-2*PADO, ')')

def place(arr):                                      # Ausschnitt mit Rand (außerhalb des Videos = 0)
    out = np.zeros((Y1-Y0, X1-X0) + arr.shape[2:], np.float32)
    sy0, sx0 = max(Y0, 0), max(X0, 0); sy1, sx1 = min(Y1, arr.shape[0]), min(X1, arr.shape[1])
    out[sy0-Y0:sy1-Y0, sx0-X0:sx1-X0] = arr[sy0:sy1, sx0:sx1]; return out

os.makedirs('kgif/seq', exist_ok=True); [os.remove(f) for f in glob.glob('kgif/seq/*.png')]
imgs = []
for a, al in data:
    c = place(a.astype(np.float32)); A = place(al.astype(np.float32))
    sh = gblur(np.roll(A, int(round(OFF)), axis=0), SIG)               # Schatten (nach unten versetzt)
    bg = 255.0*(1 - OP*np.clip(sh, 0, 1))
    out = np.clip(c*(A > 0)[..., None] + (1 - A)[..., None]*bg[..., None], 0, 255)   # Kohl über Weiß + Schatten
    imgs.append(Image.fromarray(out.astype(np.uint8)).resize((Wout, Hout), Image.LANCZOS))
order = list(range(len(imgs))) + list(range(len(imgs)-2, 0, -1))
for k, j in enumerate(order): imgs[j].save(f'kgif/seq/f{k:03d}.png')
print(len(order), 'Bilder')
