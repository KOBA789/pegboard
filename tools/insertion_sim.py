"""2D insertion-feasibility check for the pegboard hook (used to choose rod_d / R / sweep / lip_gap).

Copied from the earlier HUB75 rail project (not public). Here x points INTO the board (board = 0 <= x <= t) and the origin
is the hook rod centre, unlike the board coordinates of src/pegboard. Added since the copy:
pitch (holes repeat every pitch along y instead of a single hole) and peg_y / peg_len (a straight
peg of the same radius r, peg_y below the rod centre, that must also go in and come out).

Models the hook profile + rigid rail as it tilts into a phi6 hole of a 5.5 mm board, and
searches the (angle, x, y) pose grid for a collision-free path from "seated" (peg resting on the
bottom of the hole) to "in front of the board".

Final geometry (rod phi5, straight a=2.388, bend R8, sweep 60, board 5.5, hole phi6, rail top 5 mm above peg):
    uv run --with numpy --with scipy python insertion_sim.py \
      '{"kind":"arc","r":2.5,"a":2.388,"R":8,"sweep":60,"t":5.5,"hr":3.0,"y_top":5,"dxy":0.1,"th_min":-70,"tx_min":-16,"ty_max":5}'

TrackPoint keyboard cradle (plate top 6 above the rod centre, peg 2 pitches below; the phi6.1
press-fit peg is modelled as r = 2.5, i.e. this checks the motion, the slot takes the interference):
    uv run python tools/insertion_sim.py \
      '{"kind":"arc","r":2.5,"a":2.388,"R":8,"sweep":60,"t":5.5,"hr":3.0,"y_top":6,"y_bot":-58,"pitch":25,"peg_y":-49.5,"peg_len":5.5,"dxy":0.1,"th_min":-70,"tx_min":-16,"ty_max":5}'
"""
import numpy as np, sys, itertools
from scipy import ndimage

def hook_samples(kind, r, a, R, sweep_deg, ds=0.2):
    pts=[]
    for x in np.arange(0, a+1e-9, ds): pts.append((x,0.0))
    if kind=='arc':
        C=(a,R); n=int(np.radians(sweep_deg)*R/ds)+1
        for ang in np.linspace(-np.pi/2, -np.pi/2+np.radians(sweep_deg), n):
            pts.append((C[0]+R*np.cos(ang), C[1]+R*np.sin(ang)))
    else: # 'L': straight lip up, height R (reuse R as lip height), lip centre at x=a+r
        for x in np.arange(a, a+r+1e-9, ds): pts.append((x,0.0))
        for y in np.arange(0, R+1e-9, ds): pts.append((a+r,y))
    return np.array(pts)

def plate_samples(P, y_bot, y_top, ds=0.25):
    pts=[(0.0,y) for y in np.arange(-40, y_top+1e-9, ds)]           # back face near hook
    pts+=[(x,y_top) for x in np.arange(-P,0+1e-9,ds)]               # top edge
    pts+=[(-P,y) for y in np.arange(-40, y_top+1e-9, 1.0)]          # front face near hook
    pts+=[(0.0,y) for y in np.arange(y_bot,-40,2.0)]+[(-P,y_bot),(0.0,y_bot)]  # lower part coarse
    return np.array(pts)

def free_grid(hook, plate, r, t, hr, thetas, txs, tys, pitch=None):
    """returns bool array free[θ,tx,ty]"""
    T=np.array(list(itertools.product(txs,tys)))  # M,2
    free=np.ones((len(thetas),len(txs),len(tys)),bool)
    for i,th in enumerate(thetas):
        c,s=np.cos(th),np.sin(th); Rm=np.array([[c,-s],[s,c]])
        for pts,rad in ((hook,r),(plate,0.0)):
            p=pts@Rm.T                                   # N,2
            q=p[None,:,:]+T[:,None,:]                    # M,N,2
            x=q[...,0]; y=q[...,1]
            if pitch: y=y-pitch*np.round(y/pitch)       # relative to the nearest hole
            dx=np.maximum(np.maximum(-x,0), np.maximum(x-t,0))
            dyu=np.maximum(hr-y,0); dyl=np.maximum(y+hr,0)
            rr=max(rad-0.02,0.0); hit=((dx*dx+dyu*dyu)<rr*rr)|((dx*dx+dyl*dyl)<rr*rr)
            if rad==0: hit=(x>0.02)&(x<t-0.02)&(np.abs(y)>hr+0.02)
            free[i]&=~hit.any(axis=1).reshape(len(txs),len(tys))
    return free

def feasible(kind,r,a,R,sweep,t,hr,y_top,P=5.0,y_bot=-184.0,dth=1.0,dxy=0.15,th_min=-92,tx_min=-24,ty_max=10,pitch=None,peg_y=None,peg_len=0.0,verbose=False):
    hook=hook_samples(kind,r,a,R,sweep); plate=plate_samples(P,y_bot,y_top)
    if peg_y is not None:
        hook=np.vstack([hook,[(x,peg_y) for x in np.arange(0,peg_len+1e-9,0.2)]])
    thetas=np.radians(np.arange(th_min,3+1e-9,dth)); txs=np.arange(tx_min,2+1e-9,dxy); tys=np.arange(-ty_max,ty_max+1e-9,dxy)
    free=free_grid(hook,plate,r,t,hr,thetas,txs,tys,pitch)
    lab,n=ndimage.label(free, structure=np.ones((3,3,3)))
    i0=np.argmin(np.abs(thetas)); j0=np.argmin(np.abs(txs))
    ks=[k for k in range(len(tys)) if free[i0,j0,k] and abs(tys[k])<=hr-r+0.05]
    if not ks: return False,'seated pose collides'
    k0=ks[0]; start=lab[i0,j0,k0]
    if verbose: print('seated ty =',round(tys[k0],3))
    # goal: hook fully in front of the board (max x of all samples < -0.3)
    goal=np.zeros_like(free)
    T=np.array(list(itertools.product(txs,tys)))
    for i,th in enumerate(thetas):
        c,s=np.cos(th),np.sin(th); Rm=np.array([[c,-s],[s,c]]); p=hook@Rm.T
        mx=(p[None,:,0]+T[:,None,0]).max(axis=1)+r
        goal[i]=(mx<-0.3).reshape(len(txs),len(tys))
    ok=np.any(lab[goal&free]==start)
    return bool(ok), f'labels={n}'

if __name__=='__main__':
    import json
    cfg=json.loads(sys.argv[1])
    ok,msg=feasible(**cfg); print(json.dumps(cfg), '->', 'OK' if ok else 'NG', msg)
