# Grünkohl-GIF: Bilder 0–54 (bevor Blätter aus dem Bild ragen). Pro Bild nur Grünes behalten:
# Farbton 60–170° (weicher Übergang), genug Sättigung und Helligkeit -> heller Gelb-/Braun-Saum an den Konturen,
# Braunes, Blasses und schwarze Lücken fallen weg; winzige dunkle Poren werden gefüllt, Krümel entfernt,
# Randfarben aus dem Inneren übernommen (kein gelber Rest-Saum). Ausgabe RGBA (voller Ausschnitt) + Statistik.
import numpy as np, glob, json, subprocess
from PIL import Image, ImageFilter
from kclass import score
fs=sorted(glob.glob('kall/a*.png'))[:55]
def L(m): return Image.fromarray((m*255).astype(np.uint8))
def blur(m,r): return np.asarray(L(m).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)/255
def dilate(m,r): return blur(m,r/2)>0.12
def erode(m,r): return blur(m,r/2)>0.88
def cc(M,amin):
    H,W=M.shape; (M.astype(np.uint8)*255).tofile('cc_in.raw')
    subprocess.run(['./ccfilter','cc_in.raw',str(W),str(H),str(amin),'cc_out.raw'],check=True,capture_output=True)
    return np.fromfile('cc_out.raw',np.uint8).reshape(H,W)>127
stats=[]
masks=[]
for i,f in enumerate(fs):
    a=np.asarray(Image.open(f).convert('RGB'))
    sc,h,s,v=score(a)
    M=sc>=0.5
    M=erode(dilate(M,3.0),3.0)|M          # Poren < ~6 px schließen
    M=dilate(erode(M,2.2),2.2)&M          # Krümel/Fäden < ~4 px weg
    M=cc(M,400)                           # freistehende Krümel < 400 px weg (Swift-Komponentenfilter)
    M=~cc(~M,150)                         # Nadellöcher < 150 px füllen (werden später grün eingefärbt)
    masks.append(M)
    obj=a.max(2)>18
    stats.append({'frame':i,'kept':int(M.sum()),'removed_nongreen':int((obj&~M).sum()),
                  'nongreen_left':int((M&(sc<0.5)&(v>0.13)).sum())})
    np.save(f'kgif/m{i:03d}.npy',M)
U=np.any(masks,axis=0); ys,xs=np.where(U)
box=[int(max(0,xs.min()-6)),int(max(0,ys.min()-6)),int(min(1920,xs.max()+7)),int(min(1080,ys.max()+7))]
json.dump({'box':box,'stats':stats},open('kgif/meta.json','w'))
print('crop box',box, 'size',box[2]-box[0],box[3]-box[1])
print('frame  kept  removed  nongreen_left(=gefüllte Poren)')
for s_ in stats[::6]+[stats[-1]]: print(s_['frame'],s_['kept'],s_['removed_nongreen'],s_['nongreen_left'])
