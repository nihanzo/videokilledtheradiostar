# Bilder für gifski: Grünkohl 0..LAST (danach ragen Blätter rechts aus dem Bild), hin und zurück (nahtlos),
# Kanten auf Weiß verrechnet (Vorhang ist weiß), Alpha hart ab 50 % (GIF kennt nur an/aus)
import numpy as np, sys, os, glob
from PIL import Image
W=int(sys.argv[1]); LAST=int(sys.argv[2]); out='kgif/seq'
os.makedirs(out,exist_ok=True); [os.remove(f) for f in glob.glob(out+'/*.png')]
fs=[f'kgif/r{i:03d}.png' for i in range(LAST+1)]
order=fs+fs[-2:0:-1]
for k,f in enumerate(order):
    im=Image.open(f); H=round(im.height*W/im.width)
    a=np.asarray(im.resize((W,H),Image.LANCZOS)).astype(np.float32); al=a[...,3:4]/255
    rgb=a[...,:3]*al+255*(1-al)
    A=np.where(al[...,0]>=0.5,255,0)
    Image.fromarray(np.dstack([np.clip(rgb,0,255),A]).astype(np.uint8),'RGBA').save(f'{out}/f{k:03d}.png')
print(W,'x',H,len(order),'Bilder')
