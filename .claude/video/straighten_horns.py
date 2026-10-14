# Begradigt die Unterkante der waagerechten Hornstücke der Metall-Figur (822×1300-Seitenbilder), in allen Fassungen mit
# DERSELBEN Geraden (aus dem Original gefittet) -> Fassungen bleiben deckungsgleich. Pro Spalte wird der Streifen knapp über der
# Kante gestaucht/gestreckt, bis die Kante auf der Geraden liegt (Kontur/Schatten an der Kante bleiben erhalten); zu den Ecken
# hin: an der Hornspitze bis in die Ecke gerade (Ecke wird scharf), zum Kopf hin über 10 px weich auslaufend.
# Aufruf: python3 straighten_horns.py <original.webp> <fassung1.webp> ...   (überschreibt alle Dateien)
import sys, numpy as np
from PIL import Image
RANGES = [(40, 172, 60, 150, 'L'), (648, 775, 660, 770, 'R')]   # Spalten (von, bis), Fit-Bereich, Seite der Hornspitze
BAND = 14                                               # so viele px über der Kante werden mitverschoben

def edge(a, x):                                          # Unterkante auf Bruchteile eines Pixels (Alpha-Durchgang 128)
    col = a[:, x, 3]; ys = np.where(col[40:260] > 128)[0]
    if len(ys) == 0: return None
    y = ys[0] + 40
    while y < 260 and col[y] > 128: y += 1
    if not (y < 260 and (col[y:y+4] <= 128).all()): return None
    return (y-1) + (col[y-1]-128)/max(1e-6, col[y-1]-col[y])

ims = [np.asarray(Image.open(f).convert('RGBA')).astype(np.float64) for f in sys.argv[1:]]
lines = []
for x0, x1, f0, f1, tip in RANGES:                           # Gerade aus dem Original (Kante = erste durchsichtige Zeile)
    pts = [(x, edge(ims[0], x)) for x in range(f0, f1+1)]; pts = [(x, y) for x, y in pts if y is not None]
    X = np.array([p[0] for p in pts], float); Y = np.array([p[1] for p in pts], float)
    m, c = np.polyfit(X, Y, 1); lines.append((x0, x1, m, c, tip))
    print('Horn %d–%d: y = %.4f·x + %.2f' % (x0, x1, m, c))
for f, a in zip(sys.argv[1:], ims):
    pm = a.copy(); pm[..., :3] *= pm[..., 3:4]/255          # vormultipliziert (keine Säume)
    out = pm.copy(); moved = 0
    for x0, x1, m, c, tip in lines:
        for x in range(x0, x1+1):
            e = edge(a, x)
            if e is None: continue
            # zur Hornspitze hin bis in die Ecke gerade (Ecke wird scharf), nur zum Kopf hin über 10 px weich auslaufen
            w = min(1.0, (x1-x)/10) if tip == 'L' else min(1.0, (x-x0)/10)
            t = e + w*((m*x + c) - e)
            if abs(t-e) < 0.05: continue
            # Streifen [ya, E] (inkl. weichem Kantensaum bis 2.5 px unter der Kante) auf [ya, T] abbilden, darunter 1:1 weiter
            # in die Lücke -> Kante sitzt exakt auf der Geraden, Saum bleibt erhalten (keine Zacken)
            ya = int(e) - BAND; E = e + 2.5; T = t + 2.5; yb = int(max(E, T)) + 5
            for y in range(ya, yb+1):
                s = ya + (y - ya)*(E - ya)/(T - ya) if y <= T else E + (y - T)
                i = int(np.floor(s)); fr = s - i
                out[y, x] = pm[i, x]*(1-fr) + pm[i+1, x]*fr
            moved += 1
    o = out.copy(); al = o[..., 3:4]
    o[..., :3] = np.where(al > 0.5, o[..., :3]*255/np.maximum(al, 1e-6), 0)
    Image.fromarray(np.clip(o+0.5, 0, 255).astype(np.uint8)).save(f, 'WEBP', quality=90, method=6, alpha_quality=100)
    print(f, moved, 'Spalten angepasst')
