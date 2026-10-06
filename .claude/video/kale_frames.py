# Grünkohl-Schleife vorbereiten: Bilder aus kall/ (per `swift kall.swift <video>` exportiert) zuschneiden, verkleinern,
# letzte D Bilder in die ersten überblenden (nahtlose Schleife) -> kout/. Danach: swift enc.swift kout ../../assets/video/kale-loop.mp4
import numpy as np, glob
from PIL import Image
fs = sorted(glob.glob('kall/a*.png')); N = len(fs); D = 16
X0, Y0, X1, Y1 = 70, 50, 1920, 1060; W, H = 1280, 698
def fr(i): return np.asarray(Image.open(fs[i]).convert('RGB').crop((X0, Y0, X1, Y1)).resize((W, H), Image.LANCZOS)).astype(np.float32)
for i in range(N - D):
    a = fr(i)
    if i < D: w = i/D; a = fr(N - D + i)*(1 - w) + a*w
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save('kout/k%03d.png' % i)
