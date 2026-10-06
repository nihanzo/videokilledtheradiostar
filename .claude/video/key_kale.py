# Grünkohl wie der Reifen freistellen: Schwarz, das mit dem Rand verbunden ist, + große schwarze Lücken raus,
# kleine dunkle Ritzen bleiben; Kontur geglättet, ~1 px eingezogen, Randfarben aus dem Inneren.
# Ausgabe: gepackte Bilder (oben Farbe, 8 px Abstand, unten Maske) für ein normales MP4
import numpy as np, glob, sys
from PIL import Image, ImageFilter, ImageDraw, ImageChops
lut=lambda t:(lambda v:255 if v>t else 0)
fs=sorted(glob.glob('kout/k*.png')); out='kpack'
GAP=8
def smooth(m,r): return m.filter(ImageFilter.GaussianBlur(r)).point(lut(127))
for n,f in enumerate(fs):
    im=Image.open(f).convert('RGB'); a=np.asarray(im); W,H=im.size
    lum=Image.fromarray(a.max(axis=2)).filter(ImageFilter.GaussianBlur(0.8))
    ink=lum.point(lut(14)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))   # Krümel im Kohl schließen
    # Außen = schwarze Fläche, die mit dem Rand verbunden ist (Rahmen aus Schwarz, damit jede Randlücke erreicht wird)
    fl=Image.new('L',(W+2,H+2),0); fl.paste(ink,(1,1)); ImageDraw.floodfill(fl,(0,0),128)
    inside=fl.crop((1,1,W+1,H+1)).point(lambda v:0 if v==128 else 255)
    # große schwarze Lücken innen (breiter als ~11 px) ebenfalls raus, schmale Ritzen bleiben
    dark=ImageChops.invert(ink)
    er=dark.filter(ImageFilter.GaussianBlur(4)).point(lut(250))          # runder Einzug (nur breite Flächen bleiben)
    holes=er.filter(ImageFilter.GaussianBlur(4)).point(lut(8))          # rund wieder ausdehnen
    solid=smooth(ImageChops.multiply(inside, ImageChops.invert(holes)), 1.6)
    al=solid.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v:max(0,min(255,(v-110)*255//145)))   # weich + ~1 px eingezogen
    # Randfarben = Mittel naher deckender Innenpixel (kein dunkler Saum)
    inner=solid.filter(ImageFilter.MinFilter(5)); m=np.asarray(inner).astype(np.float32)/255
    pre=np.asarray(Image.fromarray((a*m[...,None]).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
    wb=np.asarray(inner.filter(ImageFilter.GaussianBlur(4))).astype(np.float32)/255
    A=np.asarray(al); edge=(A<250)&(wb>0.02); rgb=a.astype(np.float32)
    rgb[edge]=pre[edge]/np.maximum(wb[edge],1e-3)[:,None]
    rgb=rgb*(A[...,None]>0)                                            # außen schwarz (spart Bitrate)
    pack=Image.new('RGB',(W,2*H+GAP),(0,0,0))
    pack.paste(Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)),(0,0))
    pack.paste(Image.fromarray(A).convert('RGB'),(0,H+GAP))
    pack.save(f'{out}/p{n:03d}.png')
print('packed',len(fs),W,2*H+GAP)
