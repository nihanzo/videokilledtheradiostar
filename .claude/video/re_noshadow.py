# Entfernt den Boden-Schatten unter dem aufgeblasenen „re“ (raw re_farbe_61708F.png; unter dem e liegt sogar ein fast deckender
# grauer Fleck): Buchstabe = deckend UND blau ((B−R)/B >= 0.25; Schatten/Fleck sind grau-rosa). Pro Spalte unterhalb des
# untersten Buchstaben-Pixels: 1 px Kantenglättung wie an den Seitenkanten, darunter durchsichtig;
# Farbe der Kantenpixel = Farbe der Buchstaben-Unterkante (kein rosa/grauer Schatten-Saum). Spalten ohne Buchstabe: ganz durchsichtig.
# Dann wie zuvor beschnitten (171,184)–(1337,926) und auf 420 px Höhe -> assets/img/re-blau.webp
# Aufruf: python3 re_noshadow.py <eingabe.png> <ausgabe.webp>
import sys, numpy as np
from PIL import Image
src = np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(np.float64)
out = src.copy(); A = src[..., 3]; H, W = A.shape; W_EDGE = 1.6   # Kantenbreite (px) wie an den Seiten
E_X0 = 745     # ab dieser Spalte: das e
# e: unter seiner hellen Nahtlinie liegt im flachen Teil noch ein dunkler Kontaktstreifen (Sockel, bis 8 Zeilen). Nahtlinie je
# Spalte suchen (letztes helles Maximum über einem dunklen Streifen), zu einer glatten Kurve mitteln; unten bleiben 2 Zeilen
# darunter stehen (wie an den Rundungen des e)
def body_rows(x):
    r, b = src[:, x, 0], src[:, x, 2]
    return np.where((A[:, x] >= 200) & ((b - r) >= 0.25*np.maximum(b, 1)))[0]
seam = np.full(W, np.nan)
for x in range(E_X0, W):
    rows = body_rows(x)
    if len(rows) == 0: continue
    yb = rows.max(); lum = src[:, x, :3] @ [0.299, 0.587, 0.114]; s = lum[yb-10:yb+1]
    for k in range(len(s)-2, 0, -1):
        if s[k] > s[k-1] and s[k] >= s[k+1] and s[k] - s[k+1:].min() > 12: seam[x] = yb - 10 + k; break
xs = np.where(~np.isnan(seam))[0]
full = np.interp(np.arange(W), xs, seam[xs])
med = np.array([np.median(full[max(0, i-5):i+6]) for i in range(W)])
curve = np.array([med[max(0, i-4):i+5].mean() for i in range(W)])

for x in range(W):
    body = body_rows(x)
    if len(body) == 0: out[:, x, 3] = 0; continue
    yb = float(body.max())
    if x >= E_X0: yb = min(yb, curve[x] + 2.0)                              # e: Sockel weg
    y0 = int(np.floor(yb)); c = yb + 1                                      # Kante = Unterseite des letzten Buchstaben-Pixels
    ys = np.arange(y0+1, H)
    tgt = 255*np.clip(0.5 - (ys - c)/W_EDGE, 0, 1)
    out[y0+1:, x, 3] = np.minimum(A[y0+1:, x], tgt)
    out[y0+1:, x, :3] = src[y0, x, :3]
o = np.clip(out + 0.5, 0, 255).astype(np.uint8); o[o[..., 3] == 0, :3] = 0
im = Image.fromarray(o).crop((171, 184, 1337, 926))
h = 420; w = round(im.width*h/im.height)
im.resize((w, h), Image.LANCZOS).save(sys.argv[2], 'WEBP', quality=90, method=6, alpha_quality=100)
print(sys.argv[2], (w, h))
