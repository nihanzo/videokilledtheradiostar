from PIL import Image, ImageFilter
import numpy as np, sys
SRC='assets/raw/cosmos_2022624373.webp'
im=Image.open(SRC).convert('RGB')
P=np.asarray(im).astype(float)
PB=np.asarray(im.filter(ImageFilter.GaussianBlur(8))).astype(float)
PL=np.asarray(im.filter(ImageFilter.GaussianBlur(2.5))).astype(float)
BG=np.array([134,214,218.])
# sRGB <-> Lab (D65)
def s2l(c):
    c=c/255; return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def l2s(c):
    c=np.clip(c,0,1); return 255*np.where(c<=0.0031308,12.92*c,1.055*c**(1/2.4)-0.055)
M=np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]]); Mi=np.linalg.inv(M); W=np.array([0.95047,1,1.08883])
def f(t): return np.where(t>0.008856,np.cbrt(t),7.787*t+16/116)
def fi(t): return np.where(t>0.206893,t**3,(t-16/116)/7.787)
def rgb2lab(c):
    x=s2l(np.asarray(c,float))@M.T/W; fx,fy,fz=f(x[...,0]),f(x[...,1]),f(x[...,2])
    return np.stack([116*fy-16,500*(fx-fy),200*(fy-fz)],-1)
def lab2rgb(l):
    fy=(l[...,0]+16)/116; fx=fy+l[...,1]/500; fz=fy-l[...,2]/200
    x=np.stack([fi(fx),fi(fy),fi(fz)],-1)*W; return l2s(x@Mi.T)
def mute(c,k=0.8,dl=0):
    L=rgb2lab(np.array(c,float)); L[1:]*=k; L[0]+=dl; return lab2rgb(L)
# flower palette (muted)
ORANGE=mute([232,132,62],0.86); RED=mute([206,36,50],0.84,3); YELLOW=mute([248,186,84],0.86)
WHITE=mute([238,240,246],0.9); PINK=mute([240,138,178],0.8)
mode=sys.argv[1] if len(sys.argv)>1 else 'A'
# source ink anchors along phi (opponent-plane angle of p-BG)
src={330:[182,149,237],345:[213,126,226],0:[233,109,184],15:[238,103,122],30:[245,98,25],45:[237,108,33]}
if mode=='A': tgt={330:WHITE,345:WHITE,0:YELLOW,15:RED,30:ORANGE,45:ORANGE}
else:        tgt={330:WHITE,345:YELLOW,0:RED,15:RED,30:ORANGE,45:ORANGE}
ang=np.array([-22,-7,7,22,37,52.]); key=[330,345,0,15,30,45]
S_=np.array([src[k] for k in key],float); T_=np.array([tgt[k] for k in key],float)
def opp(v): return np.stack([(v[...,0]-v[...,1])/np.sqrt(2),(v[...,0]+v[...,1]-2*v[...,2])/np.sqrt(6)],-1)
v=P-BG; vb=PB-BG
def ang_of(w):
    o=opp(w); a=np.degrees(np.arctan2(o[...,1],o[...,0])); return np.where(a>180,a-360,a)
phiS=ang_of(vb); phiL=ang_of(PL-BG)
d=(phiL-phiS+180)%360-180; w=np.clip((np.abs(d)-12)/15,0,1)
phi=phiS+w*d
phic=np.clip(phi,ang[0],ang[-1])
def interp(tab):
    return np.stack([np.interp(phic,ang,tab[:,i]) for i in range(3)],-1)
C=interp(S_); Ct=interp(T_)
e=C-BG; ech=opp(e); vch=opp(v)
t=np.clip(1.15*(vch*ech).sum(-1)/np.maximum((ech**2).sum(-1),1e-6),0,1.4)
# directions far outside the ink arc = background variation, not ink
off=np.clip((np.abs(phi-phic)-10)/25,0,1); t*=1-off
r=v-t[...,None]*e
rl=r.mean(-1,keepdims=True); rc=r-rl
out=PINK+t[...,None]*(Ct-PINK)+rl+0.25*rc
Image.fromarray(np.clip(out,0,255).round().astype(np.uint8)).save(sys.argv[2],quality=92)
print(mode,'ORANGE',ORANGE.round(),'RED',RED.round(),'YELLOW',YELLOW.round(),'WHITE',WHITE.round(),'PINK',PINK.round())
