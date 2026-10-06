# GIF aus den freigestellten Bildern: Hin und zurück (0→54→1, nahtlos), Kanten auf Weiß verrechnet (Vorhang ist weiß),
# GIF-Transparenz (1 bit) ab 50 % Deckkraft, eigene Palette pro Bild mit Fehlerstreuung, Entsorgung = Hintergrund
import numpy as np, glob, sys
from PIL import Image
W=int(sys.argv[1]); step=int(sys.argv[2]); out=sys.argv[3]; pingpong=len(sys.argv)<5 or sys.argv[4]!='forward'
fs=sorted(glob.glob('kgif/r*.png'))[::step]
order=fs+fs[-2:0:-1] if pingpong else fs
frames=[]
cache={}
for f in order:
    if f not in cache:
        im=Image.open(f); H=round(im.height*W/im.width); im=im.resize((W,H),Image.LANCZOS)
        a=np.asarray(im).astype(np.float32); al=a[...,3:4]/255
        rgb=a[...,:3]*al+255*(1-al)                         # Kante auf Weiß
        p=Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        idx=np.asarray(p).copy(); idx[al[...,0]<0.5]=255    # Index 255 = durchsichtig
        q=Image.fromarray(idx,'P'); pal=p.getpalette()[:765]+[255,255,255]; q.putpalette(pal)
        cache[f]=q
    frames.append(cache[f])
d=40*step
frames[0].save(out, save_all=True, append_images=frames[1:], duration=d, loop=0, disposal=2, transparency=255, optimize=False)
import os; print(out, W, 'x', frames[0].height, len(frames),'frames', d,'ms', round(os.path.getsize(out)/1e6,2),'MB')
