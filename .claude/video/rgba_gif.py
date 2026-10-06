import numpy as np, glob, json
from PIL import Image, ImageFilter
from kclass import score
meta=json.load(open('kgif/meta.json')); x0,y0,x1,y1=meta['box']
fs=sorted(glob.glob('kall/a*.png'))[:55]
def blurf(arr,r):  # Werte 0..1 (H,W) bzw. 0..255 (H,W,3) weichzeichnen (über 8-bit-Bilder, reicht hier)
    if arr.ndim==2: return np.asarray(Image.fromarray(np.clip(arr*255,0,255).astype(np.uint8),'L').filter(ImageFilter.GaussianBlur(r))).astype(np.float32)/255
    return np.asarray(Image.fromarray(np.clip(arr,0,255).astype(np.uint8),'RGB').filter(ImageFilter.GaussianBlur(r))).astype(np.float32)
check=[]
for i,f in enumerate(fs):
    a=np.asarray(Image.open(f).convert('RGB'))[y0:y1,x0:x1].astype(np.float32)
    M=np.load(f'kgif/m{i:03d}.npy')[y0:y1,x0:x1].astype(np.float32)
    sc,h,s,v=score(a.astype(np.uint8))
    G=(M>0)&(sc>=0.5)                                   # sicher grüne Pixel
    avg=blurf(a*G[...,None],3.0)/np.maximum(blurf(G.astype(np.float32),3.0),1e-3)[...,None]
    alpha=blurf(M,0.8)
    band=(M>0)&(blurf(M,2.0)<0.98)                      # Randstreifen ~2-3 px
    wb=blurf(G.astype(np.float32),3.0)
    fix=(((M>0)&(sc<0.5))|band)&(wb>0.08)               # gefüllte Poren + Rand -> Grün der Umgebung
    rgb=a.copy(); rgb[fix]=avg[fix]
    # 2. Durchgang: verbliebene nicht grüne deckende Pixel mit dem Grün eines größeren Umkreises einfärben
    sc_r,_,_,_=score(np.clip(rgb,0,255).astype(np.uint8)); G2=(alpha>=0.5)&(sc_r>=0.5)
    left=(alpha>=0.5)&(sc_r<0.5)
    if left.any():
        avg2=blurf(rgb*G2[...,None],9.0)/np.maximum(blurf(G2.astype(np.float32),9.0),1e-3)[...,None]
        rgb[left]=avg2[left]
    # 3. letzte Reste: Grundgrün des Bildes in ihrer Helligkeit
    sc_r,_,_,v_r=score(np.clip(rgb,0,255).astype(np.uint8)); left=(alpha>=0.5)&(sc_r<0.5)
    if left.any():
        base=np.median(rgb[(alpha>=0.5)&(sc_r>=0.5)],axis=0); base=base/base.max()
        rgb[left]=base[None,:]*np.maximum(v_r[left],0.16)[:,None]*255
    out=np.dstack([np.clip(rgb,0,255),np.clip(alpha*255,0,255)]).astype(np.uint8)
    Image.fromarray(out,'RGBA').save(f'kgif/r{i:03d}.png')
    # Kontrolle: deckende Pixel (alpha>=0.5), die NICHT grün sind
    op=alpha>=0.5; sc2,h2,s2,v2=score(out[...,:3])
    bad=op&(sc2<0.5)
    check.append((i,int(op.sum()),int(bad.sum())))
print('frame opaque nongreen_after')
for c in check: 
    if c[0]%6==0 or c[2]>200: print(*c)
print('max nongreen opaque px in any frame:', max(c[2] for c in check), ' (von', max(c[1] for c in check),')')
json.dump(check,open('kgif/check.json','w'))
