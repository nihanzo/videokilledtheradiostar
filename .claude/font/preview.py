import sys, numpy as np
from PIL import Image
sys.path.insert(0, '.')
import glyphs as G

def build(chars=None):
    out = {}
    for ch, (f, w, l, r) in G.GL.items():
        if chars and ch not in chars: continue
        g = G.G(w); m = f(g); out[ch] = (G.soften(m), w, l, r)
    return out

def render(text, gl, scale, space=270):
    # Pixel-Bild einer Zeile (Grundlinie bei y = TOP*scale)
    xs = 60; parts = []
    for ch in text:
        if ch == ' ': xs += space; continue
        soft, w, l, r = gl[ch]; parts.append((xs + l, soft)); xs += l + w + r
    Wpx = int((xs + 2*G.PAD)*scale) + 4; Hc = G.TOP - G.BOT
    canvas = np.zeros((Hc, xs + 2*G.PAD), np.float32)
    for x0, soft in parts:
        sl = canvas[:, x0:x0+soft.shape[1]]; np.maximum(sl, soft[:, :sl.shape[1]], out=sl)
    im = Image.fromarray(((canvas > 127.5)*255).astype(np.uint8))
    return im.resize((max(1, int(im.width*scale)), int(im.height*scale)), Image.LANCZOS)

if __name__ == '__main__':
    lines = sys.argv[1:] or ['kind of aesthetic backlash', 'high-energy style saw a']
    gl = build(set(''.join(lines)))
    sc = 29.5/560
    ims = [render(t, gl, sc) for t in lines]
    W = max(i.width for i in ims); Hh = sum(i.height for i in ims)
    c = Image.new('L', (W, Hh), 0); y = 0
    for i in ims: c.paste(i, (0, y)); y += i.height
    c.save('prev_mine.png')
