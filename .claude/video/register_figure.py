# Verformt eine Stil-Fassung der Metall-Figur (z. B. Buntstift/Anime, 2250×3000, freigestellt) so, dass ihr Umriss exakt auf dem
# Original liegt (Demons-Registrierung auf den geglätteten Alpha-Masken, grob -> fein, geglättetes Verschiebungsfeld).
# Aufruf: python3 register_figure.py <Original.png> <Fassung.png> <Ausgabe.png>   (alles im selben 2250×3000-Rahmen)
import sys, numpy as np
from PIL import Image

def gblur(x, s):                                     # Gauß-Weichzeichnung per FFT (mit Rand gegen Umlauf)
    if s <= 0: return x
    p = int(3*s) + 2; xp = np.pad(x, p, mode='edge')
    fy = np.fft.fftfreq(xp.shape[0])[:, None]; fx = np.fft.rfftfreq(xp.shape[1])[None, :]
    k = np.exp(-2*(np.pi*s)**2*(fx**2 + fy**2))
    return np.fft.irfft2(np.fft.rfft2(xp)*k, s=xp.shape)[p:-p, p:-p]

def sample(img, X, Y):                               # bilinear, Koordinaten in Pixeln, außerhalb = Randwert
    H, W = img.shape[:2]
    X = np.clip(X, 0, W-1.001); Y = np.clip(Y, 0, H-1.001)
    x0 = np.floor(X).astype(int); y0 = np.floor(Y).astype(int); fx = X-x0; fy = Y-y0
    if img.ndim == 3: fx = fx[..., None]; fy = fy[..., None]
    a = img[y0, x0]; b = img[y0, x0+1]; c = img[y0+1, x0]; d = img[y0+1, x0+1]
    return (a*(1-fx) + b*fx)*(1-fy) + (c*(1-fx) + d*fx)*fy

def grad(a):
    gy, gx = np.gradient(a); return gx, gy

def demons(F, M, iters, s_fluid, s_diff, ux=None, uy=None):
    H, W = F.shape; yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    if ux is None: ux = np.zeros((H, W)); uy = np.zeros((H, W))
    Fx, Fy = grad(F)
    for it in range(iters):
        Mw = sample(M, xx+ux, yy+uy); Mx, My = grad(Mw)
        gx = (Fx+Mx)/2; gy = (Fy+My)/2; d = Mw-F
        den = gx*gx + gy*gy + 0.25*d*d + 1e-9
        dux = -d*gx/den; duy = -d*gy/den
        dux[den < 1e-6] = 0; duy[den < 1e-6] = 0
        dux = gblur(dux, s_fluid); duy = gblur(duy, s_fluid)
        m = np.maximum(1, np.sqrt(dux**2+duy**2).max()/1.5); dux /= m; duy /= m    # Schritt höchstens 1.5 px
        ux = gblur(ux+dux, s_diff); uy = gblur(uy+duy, s_diff)
    return ux, uy

def up(u, shape, f):                                 # Feld auf größere Auflösung (Werte mitskalieren)
    return np.asarray(Image.fromarray(u.astype(np.float32)).resize((shape[1], shape[0]), Image.BILINEAR)).astype(np.float64)*f

def fill_small_holes(mask, max_area, f=4):
    # kleine innere Löcher (nicht mit dem Rand verbunden, Fläche < max_area px im Vollbild) füllen; gerechnet in 1/f Auflösung.
    # Grund: z. B. Hüft-Dreiecke sind im Foto durchsichtig, im Anime-Bild schwarz gemalt -> sonst zieht die Verformung Wirbel
    H, W = mask.shape; h, w = H//f, W//f
    m = np.asarray(Image.fromarray((mask*255).astype(np.uint8)).resize((w, h), Image.BILINEAR)) > 127
    free = ~m; out = np.zeros_like(free); out[0, :] = free[0, :]; out[-1, :] = free[-1, :]; out[:, 0] = free[:, 0]; out[:, -1] = free[:, -1]
    while True:                                          # Außenraum vom Rand her fluten
        n = out.copy(); n[1:] |= out[:-1]; n[:-1] |= out[1:]; n[:, 1:] |= out[:, :-1]; n[:, :-1] |= out[:, 1:]; n &= free
        if (n == out).all(): break
        out = n
    holes = free & ~out
    lab = np.where(holes, np.arange(h*w).reshape(h, w), h*w)   # Löcher kennzeichnen (kleinste Nummer breitet sich aus)
    while True:
        n = lab.copy()
        n[1:] = np.minimum(n[1:], lab[:-1]); n[:-1] = np.minimum(n[:-1], lab[1:])
        n[:, 1:] = np.minimum(n[:, 1:], lab[:, :-1]); n[:, :-1] = np.minimum(n[:, :-1], lab[:, 1:])
        n = np.where(holes, n, h*w)
        if (n == lab).all(): break
        lab = n
    area = np.bincount(lab.ravel(), minlength=h*w+1)[lab]*f*f
    small = holes & (area < max_area)
    small = np.asarray(Image.fromarray((small*255).astype(np.uint8)).resize((W, H), Image.NEAREST)) > 127
    return mask | small

orig = np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(np.float64)
mov  = np.asarray(Image.open(sys.argv[2]).convert('RGBA')).astype(np.float64)
H, W = orig.shape[:2]
HOLE = 6000                                          # Löcher unter 6000 px² (Vollbild) zählen nicht (große Lücken Arm/Körper bleiben)
A0 = fill_small_holes(orig[..., 3] > 100, HOLE).astype(np.float64); A1 = fill_small_holes(mov[..., 3] > 100, HOLE).astype(np.float64)
ux = uy = None; prev = None
for f, its, sm in ((8, 250, 3.0), (4, 160, 2.0), (2, 90, 1.5)):
    h, w = H//f, W//f
    F = np.asarray(Image.fromarray((A0*255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float64)/255
    M = np.asarray(Image.fromarray((A1*255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float64)/255
    F = gblur(F, sm); M = gblur(M, sm)
    if ux is not None: ux = up(ux, (h, w), prev/f); uy = up(uy, (h, w), prev/f)
    ux, uy = demons(F, M, its, 1.0, 2.2 if f > 2 else 1.6, ux, uy); prev = f
    print('Stufe 1/%d fertig, max. Verschiebung %.1f px (Vollbild)' % (f, np.sqrt(ux**2+uy**2).max()*f), flush=True)
UX = up(ux, (H, W), prev); UY = up(uy, (H, W), prev)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
# Farbe vormultipliziert verformen (keine dunklen Säume an der Alpha-Kante)
pm = mov.copy(); pm[..., :3] *= pm[..., 3:4]/255
out = sample(pm, xx+UX, yy+UY); a = out[..., 3:4]
out[..., :3] = np.where(a > 0.5, out[..., :3]*255/np.maximum(a, 1e-6), 0)
Image.fromarray(np.clip(out+0.5, 0, 255).astype(np.uint8)).save(sys.argv[3])
Aw = sample(A1, xx+UX, yy+UY) > 0.5; B = A0 > 0.5
print('IoU vorher %.4f  nachher %.4f' % (((A1>0.5)&B).sum()/((A1>0.5)|B).sum(), (Aw&B).sum()/(Aw|B).sum()))
