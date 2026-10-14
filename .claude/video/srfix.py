# KI-Hochskalierung (sr4) macht die äußersten Pixel dunkler (bis 221 statt 254) -> grauer Rahmen im weißen Vorhang.
# Der Rand ist reiner Hintergrund: äußere B px durch die normal (Lanczos) vergrößerte Quelle ersetzen, weich übergeblendet.
# Aufruf: python3 srfix.py <Quelle-Ordner> <KI-Ordner>   (überschreibt die Bilder im KI-Ordner)
import sys, glob, os, numpy as np
from PIL import Image
src, sr = sys.argv[1], sys.argv[2]; B = 16
for f in sorted(glob.glob(sr + '/f*.png')):
    a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32); H, W = a.shape[:2]
    b = np.asarray(Image.open(src + '/' + os.path.basename(f)).convert('RGB').resize((W, H), Image.LANCZOS)).astype(np.float32)
    y = np.minimum(np.arange(H), np.arange(H)[::-1])[:, None]; x = np.minimum(np.arange(W), np.arange(W)[::-1])[None, :]
    w = np.clip(1 - (np.minimum(y, x) - B/2)/(B/2), 0, 1)[..., None]   # 1 außen (0..8 px), auf 0 bei 16 px
    Image.fromarray(np.clip(a*(1 - w) + b*w + .5, 0, 255).astype(np.uint8)).save(f)
print('ok')
