# Begradigt die GANZE Unterkante der waagerechten Hornstücke (Hornspitzen-Ecke bis Kopf) der Metall-Figur (822×1300-Seitenbilder).
# Anlass: straighten_horns.py hatte nur den freien Teil (Hintergrund darunter) gerade gezogen; wo das Horn über der Schulter liegt,
# lief die Linie mit Stufe (links ~3 px) bzw. Knick (rechts bis ~6 px) weiter -> sichtbare Welle.
# Kante je Spalte: Buntstift/Anime = Mitte der dunklen Konturlinie, Foto-Original = stärkster Hell-Sprung nach unten (Ausreißer per
# Median entfernt). Ziel je Seite: Gerade durch die Kante an der Hornspitzen-Ecke (Pin, bleibt wie sie ist), Neigung = Mittel der
# Buntstift-/Anime-Fits (für alle Fassungen gleich -> bleiben deckungsgleich). Pro Spalte wird ein Band um die Kante gestaucht/
# gestreckt, bis die Kante auf der Geraden liegt (zum Kopf hin über 6 px auslaufend).
# Aufruf: python3 straighten_horns2.py <original.webp> <buntstift.webp> <anime.webp> [ausgabe-ordner]   (ohne Ordner: überschreibt)
import sys, os, numpy as np
from PIL import Image

#        Seite, Start-Suchgerade (m, c), Spanne x0..x1 (Spitze..Kopf), Pin, Suchfenster um die Startgerade, Übergangs-Kerbe
SIDES = [('L', (0.0255, 193.53), 44, 268, 46, (-4, 7), (160, 180)),
         ('R', (-0.0674, 248.06), 552, 766, 764, (-10, 4), (636, 662))]
UP, DOWN, FADE = 22, 16, 6          # Band über / unter der Kante (px), Auslauf zum Kopf (Spalten)

def load(f):
    a = np.asarray(Image.open(f).convert('RGBA')).astype(np.float64)
    w = a[..., :3]*a[..., 3:]/255 + 255*(1 - a[..., 3:]/255)                 # auf Weiß
    return a, w @ [0.299, 0.587, 0.114]

def sub_min(p, i):                                                          # Parabel durch 3 Punkte -> Bruchteil-Pixel
    if 0 < i < len(p)-1:
        d = p[i-1] - 2*p[i] + p[i+1]
        if d > 1e-6: return i + 0.5*(p[i-1] - p[i+1])/d
    return float(i)

def measure(lum, x, y0, lo, hi, mode):
    ys = np.arange(int(np.floor(y0+lo)), int(np.ceil(y0+hi)) + 1); p = lum[ys, x]
    if mode == 'dark': return ys[0] + sub_min(p, int(np.argmin(p)))
    g = np.convolve(p, [1, 1, 1], 'same')/3; dg = np.diff(g); dg[0] = dg[-1] = 0
    return ys[0] + sub_min(-dg, int(np.argmax(dg))) + 0.5

def medf(v, w): return np.array([np.median(v[max(0, i-w//2):i+w//2+1]) for i in range(len(v))])
def boxf(v, w): return np.array([v[max(0, i-w//2):i+w//2+1].mean() for i in range(len(v))])
def clean(v, w):                                                            # Fehltreffer (Nieten, Schatten) -> Median
    med = medf(v, w)
    return np.where(np.abs(v - med) < 0.8, v, med)

files = sys.argv[1:4]; outdir = sys.argv[4] if len(sys.argv) > 4 else None
modes = ['grad', 'dark', 'dark']
data = [load(f) for f in files]

edges = {}; slopes = {}
for side, (m, c), x0, x1, xp, (lo, hi), (n0, n1) in SIDES:
    xs = np.arange(x0, x1+1); keep = (xs < n0) | (xs > n1); sl = []
    for k, ((a, lum), mode) in enumerate(zip(data, modes)):
        v = clean(np.array([measure(lum, x, m*x + c, lo, hi, mode) for x in xs]), 11)
        # freier Teil (Spitze .. Kerbe) ist schon gerade (straighten_horns.py) -> dort die Ausgleichsgerade statt Einzelwerte
        free = (xs <= n0 - 4) if side == 'L' else (xs >= n1 + 4)
        A = np.vstack([xs[free], np.ones(free.sum())]).T; co, *_ = np.linalg.lstsq(A, v[free], rcond=None)
        v = np.where(free, co[0]*xs + co[1], v)
        edges[side, k] = v
        yp = v[xs == xp][0]; dx = xs[keep] - xp; dy = v[keep] - yp
        sl.append((dx*dy).sum()/(dx*dx).sum())
    slopes[side] = (sl[1] + sl[2])/2
    print('Seite %s: Neigung je Fassung %s -> gemeinsam %.4f' % (side, ' '.join('%.4f' % s for s in sl), slopes[side]))

for k, (f, (a, lum)) in enumerate(zip(files, data)):
    pm = a.copy(); pm[..., :3] *= pm[..., 3:4]/255                         # vormultipliziert (keine Säume)
    out = pm.copy(); H = a.shape[0]; maxd = 0
    for side, (m, c), x0, x1, xp, (lo, hi), (n0, n1) in SIDES:
        xs = np.arange(x0, x1+1); v = edges[side, k]; yp = v[xs == xp][0]
        head = (x1 - xs) if side == 'L' else (xs - x0)                        # Abstand zum Kopf-Ende der Spanne
        d = (yp + slopes[side]*(xs - xp)) - v
        d = boxf(medf(d, 5), 5)*np.minimum(1.0, (head + 1)/FADE)             # Verschiebung glatt (keine Einzelspalten-Sprünge)
        for x, e, dd in zip(xs, v, d):
            t = e + dd
            if abs(t - e) < 0.08: continue
            maxd = max(maxd, abs(t - e))
            ya = int(np.floor(min(e, t))) - UP; yb = int(np.ceil(max(e, t))) + DOWN
            for y in range(ya, yb+1):
                s = ya + (y - ya)*(e - ya)/(t - ya) if y <= t else e + (y - t)*(yb - e)/(yb - t)
                i = int(np.floor(s)); fr = s - i
                out[y, x] = pm[i, x]*(1 - fr) + pm[min(i+1, H-1), x]*fr
    o = out.copy(); al = o[..., 3:4]
    o[..., :3] = np.where(al > 0.5, o[..., :3]*255/np.maximum(al, 1e-6), 0)
    dst = os.path.join(outdir, os.path.basename(f)) if outdir else f
    Image.fromarray(np.clip(o + 0.5, 0, 255).astype(np.uint8)).save(dst, 'WEBP', quality=90, method=6, alpha_quality=100)
    print(dst, 'max. Verschiebung %.2f px' % maxd)
