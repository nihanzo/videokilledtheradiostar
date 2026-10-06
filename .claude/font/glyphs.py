# Eigene Schrift im Stil des Musterbilds (sehr fette Grotesk, weiche Ecken, enge Laufweite).
# Jede Glyphe wird aus Grundformen (Rechtecke, Superellipsen, dicke Striche) als Maske gebaut
# (1 Einheit = 1 Pixel, Geviert 1000), dann weichgezeichnet und an der 50-%-Linie als Kontur abgegriffen.
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import math

H, A, D, S, T, O = 560, 790, -205, 232, 180, 12      # x-Höhe, Oberlänge, Unterlänge, Grundstrich, Querstrich, Überhang
NUM = 770                                            # Ziffernhöhe
TOP, BOT = 900, -300                                  # Leinwand (Font-y)
PAD = 120                                             # Rand links/rechts auf der Leinwand
SOFT = 20                                             # Weichzeichnung (Sigma) -> runde Ecken

class G:
    def __init__(self, w):
        self.w = w; self.W = w + 2*PAD; self.Hc = TOP - BOT
    def _img(self): return Image.new('L', (self.W, self.Hc), 0)
    def _xy(self, x, y): return (x + PAD, TOP - y)
    def _mask(self, im): return np.asarray(im) > 127
    # --- Grundformen (Font-Koordinaten, y nach oben) ---
    def R(self, x0, y0, x1, y1):
        im = self._img(); d = ImageDraw.Draw(im)
        a, b = self._xy(x0, y1), self._xy(x1, y0); d.rectangle([a[0], a[1], b[0]-1, b[1]-1], fill=255); return self._mask(im)
    def RR(self, x0, y0, x1, y1, r):
        im = self._img(); d = ImageDraw.Draw(im)
        a, b = self._xy(x0, y1), self._xy(x1, y0); d.rounded_rectangle([a[0], a[1], b[0]-1, b[1]-1], radius=r, fill=255); return self._mask(im)
    def P(self, pts):
        im = self._img(); ImageDraw.Draw(im).polygon([self._xy(x, y) for x, y in pts], fill=255); return self._mask(im)
    def SE(self, cx, cy, rx, ry, n=2.4):
        pts = []
        for i in range(720):
            t = 2*math.pi*i/720; c, s = math.cos(t), math.sin(t)
            pts.append((cx + rx*math.copysign(abs(c)**(2/n), c), cy + ry*math.copysign(abs(s)**(2/n), s)))
        return self.P(pts)
    def ST(self, p0, p1, w):                              # dicker Strich mit geraden Enden
        (x0, y0), (x1, y1) = p0, p1; L = math.hypot(x1-x0, y1-y0); nx, ny = -(y1-y0)/L*w/2, (x1-x0)/L*w/2
        return self.P([(x0+nx, y0+ny), (x1+nx, y1+ny), (x1-nx, y1-ny), (x0-nx, y0-ny)])
    def BZ(self, p0, p1, p2, p3, w, n=48):             # dicker Strich entlang einer kubischen Bézierkurve
        im = self._img(); d = ImageDraw.Draw(im); pts = []
        for i in range(n+1):
            t = i/n; a = (1-t)**3; b = 3*(1-t)**2*t; c = 3*(1-t)*t*t; e = t**3
            pts.append((a*p0[0]+b*p1[0]+c*p2[0]+e*p3[0], a*p0[1]+b*p1[1]+c*p2[1]+e*p3[1]))
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1-x0, y1-y0) or 1; nx, ny = -(y1-y0)/L*w/2, (x1-x0)/L*w/2
            d.polygon([self._xy(x0+nx, y0+ny), self._xy(x1+nx, y1+ny), self._xy(x1-nx, y1-ny), self._xy(x0-nx, y0-ny)], fill=255)
        for x, y in pts[1:-1]:
            cx, cy = self._xy(x, y); d.ellipse([cx-w/2, cy-w/2, cx+w/2, cy+w/2], fill=255)
        return self._mask(im)
    def DISC(self, x, y, r):
        im = self._img(); cx, cy = self._xy(x, y); ImageDraw.Draw(im).ellipse([cx-r, cy-r, cx+r, cy+r], fill=255); return self._mask(im)
    def band(self, y0, y1): return self.R(-PAD, y0, self.w+PAD, y1)
    def xb(self, x0, x1): return self.R(x0, BOT, x1, TOP)
    def above(self, y): return self.R(-PAD, y, self.w+PAD, TOP)
    def below(self, y): return self.R(-PAD, BOT, self.w+PAD, y)

def soften(mask, sigma=SOFT):
    im = Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
    return np.asarray(im).astype(np.float32)

# ---------- Bausteine ----------
def bowl(g, x0, x1, y0=-O, y1=H+O, n=2.4):           # Superellipse in einem Kasten
    return g.SE((x0+x1)/2, (y0+y1)/2, (x1-x0)/2, (y1-y0)/2, n)
def counter(g, x0, x1, y0=-O, y1=H+O, n=2.4, sx=S, sy=T):
    return bowl(g, x0+sx, x1-sx, y0+sy, y1-sy, n)
def arch(g, x0, x1, top, yc, n=2.4):                 # obere Hälfte einer Superellipse, darunter senkrecht weiter
    return (g.SE((x0+x1)/2, yc, (x1-x0)/2, top-yc, n) & g.above(yc)) | g.R(x0, -500, x1, yc+1)
def ascender_stem(g, x0, y0=0, y1=A):
    return g.RR(x0, y0, x0+S, y1, 70) | g.R(x0, y0, x0+S, y1-120)

def vshape(g, x0, x1, top=H, bot=0, bw=190, nw=130, tip=H*0.40):
    cx = (x0+x1)/2
    outer = g.P([(x0, top), (x1, top), (cx+bw/2, bot), (cx-bw/2, bot)])
    notch = g.P([(cx-nw/2*(top+60-tip)/(top-tip), top+60), (cx+nw/2*(top+60-tip)/(top-tip), top+60), (cx, tip)])
    return outer & ~notch

def idot(g, x0):                                     # i-Punkt: oben halbrund, unten gerade Kante
    return (g.RR(x0, 620, x0+S, 805, S//2) & g.above(700)) | g.R(x0, 620, x0+S, 701)

GL = {}
def glyph(ch, w, lsb_pad=20, rsb_pad=20):
    def deco(f):
        GL[ch] = (f, w, lsb_pad, rsb_pad); return f
    return deco

# ---------- Kleinbuchstaben ----------
@glyph('o', 600, 14, 14)
def _o(g): w = g.w; return bowl(g, 0, w) & ~counter(g, 0, w)

@glyph('n', 570)
def _n(g):
    w = g.w; yc = 250
    outer = g.R(0, 0, S, H) | (arch(g, 0, w, H+O, yc) & g.above(0))
    inner = arch(g, S, w-S, H+O-T, yc) & g.above(-10)
    return outer & ~inner

@glyph('h', 570)
def _h(g): return _n(g) | ascender_stem(g, 0)

@glyph('m', 874)
def _m(g):
    w = g.w; yc = 250; mid0 = (w-S)/2
    outer = g.R(0, 0, S, H) | ((arch(g, 0, mid0+S, H+O, yc) | arch(g, mid0, w, H+O, yc)) & g.above(0))
    inner = (arch(g, S, mid0, H+O-T, yc) | arch(g, mid0+S, w-S, H+O-T, yc)) & g.above(-10)
    return outer & ~inner

@glyph('u', 570)
def _u(g):
    n = _n(g); return np.flip(np.flip(n, 0), 1) if False else rot180(g, n)

def rot180(g, m):                                    # 180°-Drehung um die Glyphenmitte (x) und x-Höhen-Mitte (y)
    out = np.zeros_like(m)
    cx = PAD + g.w/2; cy = TOP - H/2
    ys, xs = np.nonzero(m)
    nx = np.round(2*cx - xs - 1).astype(int); ny = np.round(2*cy - ys - 1).astype(int)
    ok = (nx >= 0) & (nx < m.shape[1]) & (ny >= 0) & (ny < m.shape[0])
    out[ny[ok], nx[ok]] = True; return out

def mirx(g, m):
    out = np.zeros_like(m); cx = PAD + g.w/2
    ys, xs = np.nonzero(m); nx = np.round(2*cx - xs - 1).astype(int)
    ok = (nx >= 0) & (nx < m.shape[1]); out[ys[ok], nx[ok]] = True; return out

@glyph('b', 590, 20, 14)
def _b(g):
    w = g.w
    return (ascender_stem(g, 0) | (bowl(g, 0, w) & g.xb(S/2, w)) | g.R(0, 0, S, H)) & ~counter(g, 0, w)

@glyph('d', 590, 14, 20)
def _d(g): return mirx(g, _b(g))

@glyph('p', 590, 20, 14)
def _p(g):
    w = g.w
    return (g.R(0, D, S, H) | (bowl(g, 0, w) & g.xb(S/2, w))) & ~counter(g, 0, w)

@glyph('q', 590, 14, 20)
def _q(g): return mirx(g, _p(g))

@glyph('c', 520, 14, 16)
def _c(g):
    w = g.w
    gap = g.R(w*0.5, H*0.5-62, w+PAD, H*0.5+62)
    return bowl(g, 0, w) & ~counter(g, 0, w) & ~gap

@glyph('e', 560, 14, 16)
def _e(g):
    w = g.w
    eye = g.SE(w*0.52, H*0.66, w*0.2, 52, 2.2)
    ap = g.ST((w*0.46, H*0.335), (w+90, H*0.285), 66) | g.DISC(w*0.46, H*0.335, 34)
    return bowl(g, 0, w) & ~eye & ~ap

@glyph('a', 555, 16, 20)
def _a(g):
    w = g.w
    stem = g.R(w-S, 0, w, H-160)
    top = (g.SE(w/2, H-230, w/2-10, 230+O, 2.4) & g.above(H-230) & g.xb(40, w))
    topin = g.SE(w/2, H-230, w/2-10-S+20, 230+O-T, 2.4) & g.above(H-230-40)
    bowlo = g.SE(w/2-14, 175, w/2-14, 175+O, 2.4)
    slit = g.ST((w*0.24, 182), (w*0.50, 150), 62) | g.DISC(w*0.24, 182, 31) | g.DISC(w*0.50, 150, 31)   # schräg, links unten
    notch = g.ST((-80, 372), (w*0.40, 334), 46) | g.DISC(w*0.40, 334, 23)
    m = (stem | top | bowlo) & ~topin & ~slit & ~notch
    return m | (g.R(w-S, 0, w, H-160))

@glyph('s', 500, 16, 16)
def _s(g):
    w = g.w
    out = bowl(g, 0, w, n=2.3)
    up = g.ST((w*0.40, H*0.668), (w+90, H*0.598), 60) | g.DISC(w*0.40, H*0.668, 34)
    lo = g.ST((-90, H*0.402), (w*0.60, H*0.332), 60) | g.DISC(w*0.60, H*0.332, 34)
    return out & ~up & ~lo

@glyph('t', 460, 12, 16)
def _t(g):
    w = g.w; x0 = 34; cx = x0+S+70
    stem = g.P([(x0, 220), (x0, 610), (x0+S, 675), (x0+S, 220)])
    bar = g.RR(0, H-T, w-14, H, 40) | g.R(0, H-T, x0+S, H)
    ring = g.SE(cx, 230, S+70, 230+O, 2.4) & ~g.SE(cx, 230, 70, 230+O-T, 2.4) & g.below(230) & g.xb(x0, cx)
    return stem | bar | ring | g.R(cx-1, -O, w-6, T-O)

@glyph('f', 500, 12, 10)
def _f(g):
    w = g.w; x0 = 50; cx = x0+S+70
    stem = g.R(x0, 0, x0+S, A-220)
    ring = g.SE(cx, A-230, S+70, 230+O, 2.4) & ~g.SE(cx, A-230, 70, 230+O-T, 2.4) & g.above(A-230) & g.xb(x0, cx)
    term = g.R(cx-1, A-T+O, w-4, A+O)
    bar = g.RR(0, H-T, w-40, H, 40) | g.R(x0, H-T, x0+S, H)
    return stem | ring | term | bar

@glyph('r', 400, 20, 4)
def _r(g):
    w = g.w; yc = 300
    sh = (g.SE(w-20, yc, w-20, H+O-yc, 2.4) & g.above(yc) & g.xb(0, w))
    shi = g.SE(w-20, yc, w-20-S, H+O-yc-T, 2.4) & g.above(yc-40)
    cut = g.R(w-90, -PAD, w+PAD, H-200)
    return g.R(0, 0, S, H) | (sh & ~shi & ~cut)

@glyph('l', 232)
def _l(g): return ascender_stem(g, 0)

@glyph('i', 232)
def _i(g): return g.R(0, 0, S, H) | idot(g, 0)

@glyph('j', 300, -30, 20)
def _j(g):
    w = g.w; x0 = w-S; cx = x0-60
    stem = g.R(x0, D+230, w, H)
    ring = g.SE(cx, D+230, S+60, 230+O, 2.4) & ~g.SE(cx, D+230, 60, 230+O-T, 2.4) & g.below(D+230) & g.xb(cx, w)
    return stem | ring | g.R(0, D-O, cx+1, D+T-O) | idot(g, x0)

@glyph('k', 580)
def _k(g):
    w = g.w
    arm = g.ST((S-40, 200), (w-60, H+40), 230) & g.band(0, H) & g.xb(S-60, w)
    leg = g.ST((S+30, 330), (w-70, -40), 240) & g.band(0, H) & g.xb(S-60, w)
    return ascender_stem(g, 0) | arm | leg

@glyph('v', 570, 10, 10)
def _v(g): return vshape(g, 0, g.w) & g.band(0, H)

@glyph('w', 840, 10, 10)
def _w(g):
    w = g.w; w1 = w*0.6
    return (vshape(g, 0, w1, bw=170, nw=120) | vshape(g, w-w1, w, bw=170, nw=120)) & g.band(0, H)

@glyph('x', 580, 10, 10)
def _x(g):
    w = g.w
    m = g.R(0, 0, w, H)
    for p in ([(w/2-75, H+40), (w/2+75, H+40), (w/2, H*0.64)], [(w/2-75, -40), (w/2+75, -40), (w/2, H*0.36)],
              [(-40, H/2+150), (-40, H/2-150), (w*0.34, H/2)], [(w+40, H/2+150), (w+40, H/2-150), (w*0.66, H/2)]):
        m = m & ~g.P(p)
    return m

@glyph('y', 580, 10, 10)
def _y(g):
    w = g.w; k = 0.339                                # k = Neigung des rechten Arms (dx/dy)
    top = vshape(g, 0, w) & g.band(0, H)
    desc = g.P([(w/2-95, 1), (w/2+95, 1), (w/2+95-k*60, -60), (w/2-95-k*60, -60)])
    bx = w/2 - k*60                                   # Mitte des Arms unten -> runder Bogen nach links (wie ein u)
    tail = g.BZ((bx, -40), (bx-25, D+70), (bx-120, D+T/2), (w*0.12, D+T/2+20), 195)
    return (top | desc | tail) & g.xb(0, w) & g.above(D-O)

@glyph('z', 500, 16, 16)
def _z(g):
    w = g.w
    return g.R(10, H-T, w-10, H) | g.R(0, 0, w, T) | (g.ST((w-110, H-T+20), (110, T-20), 250) & g.band(T-40, H-T+40))

@glyph('g', 590, 14, 20)
def _g(g):
    w = g.w; x0 = w-S; cy = D+215
    q = (g.R(x0, cy, w, H) | (bowl(g, 0, w, y0=30) & g.xb(0, w-S/2))) & ~counter(g, 0, w, y0=30)
    ring = g.SE(w/2+10, cy, w/2-10, 215+O, 2.4) & ~g.SE(w/2+10, cy, w/2-10-S, 215+O-T, 2.4) & g.below(cy)
    ring = ring & ~(g.xb(-PAD, w/2) & g.above(D+T+10))
    return q | ring

# ---------- Großbuchstaben (nur S C R O L für „SCROLL“; alle anderen fallen auf die Kleinbuchstaben zurück) ----------
CAP = NUM                                            # Versalhöhe = Ziffernhöhe

@glyph('O', 700, 14, 14)
def _O(g): w = g.w; return bowl(g, 0, w, -O, CAP+O, 2.3) & ~bowl(g, S, w-S, T-O, CAP+O-T, 2.3)

@glyph('C', 640, 14, 16)
def _C(g):
    w = g.w
    gap = g.R(w*0.5, CAP*0.5-80, w+PAD, CAP*0.5+80)
    return bowl(g, 0, w, -O, CAP+O, 2.3) & ~bowl(g, S, w-S, T-O, CAP+O-T, 2.3) & ~gap

@glyph('S', 600, 16, 16)
def _S(g):
    w = g.w
    out = bowl(g, 0, w, -O, CAP+O, 2.3)
    up = g.ST((w*0.40, CAP*0.672), (w+110, CAP*0.592), 72) | g.DISC(w*0.40, CAP*0.672, 40)
    lo = g.ST((-110, CAP*0.408), (w*0.60, CAP*0.328), 72) | g.DISC(w*0.60, CAP*0.328, 40)
    return out & ~up & ~lo

@glyph('R', 640, 20, 10)
def _R(g):
    w = g.w; yb = 300                                # Unterkante der Schüssel
    bw = w - 30
    bowlR = (g.SE(bw/2, (yb+CAP+O)/2, bw/2, (CAP+O-yb)/2, 2.4) & g.xb(S/2, bw)) & ~g.SE(bw/2, (yb+CAP+O)/2, bw/2-S, (CAP+O-yb)/2-T, 2.4)
    leg = g.ST((w*0.42, yb+60), (w-90, -40), 240) & g.band(0, yb+60) & g.xb(S-60, w)
    return g.R(0, 0, S, CAP) | g.R(0, CAP-T, bw/2, CAP) | g.R(0, yb, bw/2, yb+T) | bowlR | leg

@glyph('L', 520, 20, 10)
def _L(g): w = g.w; return g.R(0, 0, S, CAP) | g.RR(0, 0, w, T+10, 40) | g.R(0, 0, S, T+10)

@glyph('0', 600, 20, 20)
def _0(g): w = g.w; return bowl(g, 0, w, -O, NUM+O, 2.3) & ~bowl(g, S, w-S, T-O, NUM+O-T, 2.3)

@glyph('1', 440, 20, 20)
def _1(g):
    w = g.w; x0 = w-S-20
    return g.R(x0, 0, x0+S, NUM) | (g.ST((x0+40, NUM-90), (10, NUM-300), 210) & g.xb(0, x0+S) & g.below(NUM))

@glyph('2', 560, 16, 16)
def _2(g):
    w = g.w; k = 215
    arc = g.BZ((k/2+10, NUM-250), (k/2-10, NUM+60), (w-k/2, NUM+60), (w-k/2, NUM-250), k)
    dia = g.BZ((w-k/2, NUM-250), (w-k/2, NUM-430), (k/2+40, 330), (k/2+10, T-20), 235)
    m = (arc & ~(g.xb(-PAD, w/2) & g.below(NUM-250))) | dia
    return (m & g.above(T-30)) | g.R(0, 0, w, T)

@glyph('3', 560, 16, 16)
def _3(g):
    w = g.w; k = 215; my = NUM*0.53
    up = g.BZ((k/2+10, NUM-200), (k/2+10, NUM+50), (w-k/2-20, NUM+50), (w-k/2-20, NUM-190), k) | \
         g.BZ((w-k/2-20, NUM-190), (w-k/2-20, my+20), (w*0.6, my), (w*0.34, my), k)
    lo = g.BZ((w*0.34, my), (w*0.75, my), (w-k/2, my-60), (w-k/2, 240), k) | \
         g.BZ((w-k/2, 240), (w-k/2, -60), (k/2+10, -60), (k/2+10, 200), k)
    return (up & ~(g.xb(-PAD, w*0.45) & g.band(my-10, NUM-200))) | (lo & ~(g.xb(-PAD, w*0.45) & g.band(200, my+10)))

@glyph('4', 590, 10, 16)
def _4(g):
    w = g.w; x0 = w-S-40
    return g.R(x0, 0, x0+S, NUM) | g.R(0, 150, w, 150+T) | (g.ST((x0+60, NUM+30), (0, 150+T/2), 230) & g.xb(0, x0+S) & g.band(150, NUM))

@glyph('5', 560, 16, 16)
def _5(g):
    w = g.w; k = 215
    top = g.R(40, NUM-T, w-20, NUM)
    stem = g.R(40, 400, 40+S, NUM)
    bowlp = g.BZ((40+S/2, 470), (w*0.55, 560), (w-k/2, 470), (w-k/2, 250), k) | \
            g.BZ((w-k/2, 250), (w-k/2, -60), (k/2+10, -60), (k/2+10, 190), k)
    return top | stem | (bowlp & ~(g.xb(-PAD, w*0.4) & g.band(190, 420)))

@glyph('6', 580, 16, 16)
def _6(g):
    w = g.w
    lo = bowl(g, 0, w, -O, 500) & ~bowl(g, S, w-S, T-O, 500-T)
    up = g.BZ((S/2, 250), (S/2, 640), (w*0.35, NUM-T/2), (w-50, NUM-T/2), 220) & g.below(NUM+O)
    return lo | (up & g.xb(0, w-30))

@glyph('7', 540, 10, 16)
def _7(g):
    w = g.w
    return g.R(0, NUM-T, w, NUM) | (g.ST((w-S/2, NUM-T/2), (w*0.28, -40), 250) & g.band(0, NUM))

@glyph('8', 580, 16, 16)
def _8(g):
    w = g.w
    up = g.SE(w/2, NUM-200, w/2-25, 200+O, 2.4) & ~g.SE(w/2, NUM-200, w/2-25-S+20, 200+O-T+10, 2.4)
    lo = g.SE(w/2, 220, w/2, 220+O, 2.4) & ~g.SE(w/2, 220, w/2-S, 220+O-T, 2.4)
    return up | lo

@glyph('9', 580, 16, 16)
def _9(g): return rot180_num(g, _6(g))

def rot180_num(g, m):
    out = np.zeros_like(m); cx = PAD + g.w/2; cy = TOP - NUM/2
    ys, xs = np.nonzero(m); nx = np.round(2*cx - xs - 1).astype(int); ny = np.round(2*cy - ys - 1).astype(int)
    ok = (nx >= 0) & (nx < m.shape[1]) & (ny >= 0) & (ny < m.shape[0]); out[ny[ok], nx[ok]] = True; return out

# ---------- Satzzeichen ----------
@glyph('.', 232, 24, 24)
def _dot(g): return g.RR(0, 0, S, 220, 80)

@glyph(',', 240, 24, 24)
def _comma(g): return g.RR(0, 0, S, 220, 80) | (g.ST((S-40, 150), (40, -170), 150) & g.band(-170, 150))

@glyph(':', 232, 24, 24)
def _colon(g): return g.RR(0, 0, S, 220, 80) | g.RR(0, H-220, S, H, 80)

@glyph('·', 232, 24, 24)
def _mid(g): return g.RR(0, H/2-110, S, H/2+110, 80)

@glyph('-', 300, 20, 20)
def _hy(g): return g.RR(0, 200, 300, 200+T, 40)

@glyph('+', 520, 24, 24)
def _plus(g): return g.RR(0, H/2-95+20, 520, H/2+95+20, 30) | g.RR(260-100, H/2-260+20, 260+100, H/2+260+20, 30)

@glyph('/', 420, 10, 10)
def _sl(g): return g.ST((420-70, A+20), (70, D+20), 200) & g.band(D, A)

@glyph('(', 300, 30, 10)
def _pl(g):
    return (g.SE(300, (A+D)/2, 300, (A-D)/2, 2.2) & ~g.SE(300+40, (A+D)/2, 300+40-S+20, (A-D)/2-60, 2.2)) & g.xb(0, 300)

@glyph(')', 300, 10, 30)
def _pr(g): return mirx(g, _pl(g))

@glyph('%', 760, 16, 16)
def _pct(g):
    w = g.w
    o1 = g.SE(150, NUM-170, 150, 170, 2.3) & ~g.SE(150, NUM-170, 55, 75, 2.3)
    o2 = g.SE(w-150, 170, 150, 170, 2.3) & ~g.SE(w-150, 170, 55, 75, 2.3)
    sl = g.ST((w-160, NUM+20), (160, -20), 190) & g.band(0, NUM)
    return o1 | o2 | sl

@glyph("'", 232, 24, 24)
def _ap(g): return g.RR(0, A-300, S, A, 70)

@glyph('"', 520, 24, 24)
def _qu(g): return g.RR(0, A-300, S, A, 70) | g.RR(520-S, A-300, 520, A, 70)

@glyph('!', 232, 24, 24)
def _ex(g): return g.RR(0, 300, S, A, 70) | g.RR(0, 0, S, 220, 80)

@glyph('?', 520, 16, 16)
def _q2(g):
    w = g.w; yc = A-260
    top = g.SE(w/2, yc, w/2, 260+O, 2.4) & g.above(yc) & ~g.SE(w/2, yc, w/2-S, 260+O-T, 2.4)
    right = g.R(w-S, yc-80, w, yc+1)
    neck = g.R(w/2-S/2, 300, w/2+S/2, yc-60) | (g.ST((w-S/2, yc-60), (w/2, 360), 230) & g.band(300, yc))
    return top | right | neck | g.RR(w/2-S/2, 0, w/2+S/2, 220, 80)

@glyph('\u25b6', 470, 30, 40)
def _play(g): return g.P([(0, 20), (0, 540), (470, 280)])     # ▶ für „enter with sound“
