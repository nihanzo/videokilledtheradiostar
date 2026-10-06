import numpy as np
def hsv(a):
    a=a.astype(np.float32)/255; r,g,b=a[...,0],a[...,1],a[...,2]
    mx=a.max(2); mn=a.min(2); d=mx-mn+1e-6
    h=np.where(mx==r, ((g-b)/d)%6, np.where(mx==g, (b-r)/d+2, (r-g)/d+4))*60
    s=(mx-mn)/(mx+1e-6); return h,s,mx
def ss(x,a,b): t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
def score(a, H0=(52,66), H1=(168,182), S=(0.10,0.20), V=(0.06,0.13)):
    h,s,v=hsv(a)
    return ss(h,*H0)*(1-ss(h,*H1))*ss(s,*S)*ss(v,*V), h, s, v
