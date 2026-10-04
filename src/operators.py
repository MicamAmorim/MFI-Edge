
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Callable, Dict, Tuple

EPS = 1e-12

def clip01(z):
    return np.clip(np.asarray(z, dtype=float), 0.0, 1.0)

def TM(x,y): return np.minimum(x,y)
def TP(x,y): return np.asarray(x)*np.asarray(y)
def TL(x,y): return np.maximum(0.0, np.asarray(x)+np.asarray(y)-1.0)
def THP(x,y):
    x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    den=x+y-x*y
    return np.where(np.abs(den)<EPS, 0.0, (x*y)/den)
def TDP(x,y):
    x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    return np.where(np.isclose(y,1),x,np.where(np.isclose(x,1),y,0.0))

def AVG(x,y): return (np.asarray(x)+np.asarray(y))/2.0

def OB(x,y):
    x,y=clip01(x),clip01(y)
    return np.minimum(x*np.sqrt(y), y*np.sqrt(x))
def OmM(x,y):
    x,y=clip01(x),clip01(y)
    return np.minimum(x,y)*np.maximum(x*x,y*y)
def ODiv(x,y):
    x,y=clip01(x),clip01(y)
    return (x*y + np.minimum(x,y))/2.0
def GM(x,y):
    x,y=clip01(x),clip01(y)
    return np.sqrt(x*y)
def HM(x,y):
    x,y=clip01(x),clip01(y)
    den=x+y
    return np.where(den<EPS,0.0,2*x*y/den)
def S(x,y):
    x,y=clip01(x),clip01(y)
    return np.sin((np.pi/2.0)*np.power(x*y,0.25))
def ORS(x,y):
    x,y=clip01(x),clip01(y)
    return np.minimum((x+1.0)*np.sqrt(y)/2.0, y*np.sqrt(x))

def CF(x,y):
    x,y=clip01(x),clip01(y)
    return x*y + x*x*y*(1-x)*(1-y)
def CL(x,y):
    x,y=clip01(x),clip01(y)
    return np.maximum(np.minimum(x,y/2.0), x+y-1.0)

def FGL(x,y):
    x,y=clip01(x),clip01(y)
    return np.sqrt(x*(y+1.0)/2.0)
def FBPC(x,y):
    x,y=clip01(x),clip01(y)
    return x*y*y
def FNA(x,y):
    x,y=clip01(x),clip01(y)
    return np.where(x<=y, x, np.minimum(x/2.0,y))
def FNA2(x,y):
    x,y=clip01(x),clip01(y)
    return np.where(np.isclose(x,0.0),0.0,
                    np.where(x<=y,(x+y)/2.0,np.minimum(x/2.0,y)))
def FIM(x,y):
    x,y=clip01(x),clip01(y)
    return np.maximum(1-y,x)
def FIP(x,y):
    x,y=clip01(x),clip01(y)
    return 1-y+x*y

FUNCTIONS: Dict[str, Callable] = {
    "TP":TP, "TM":TM, "TL":TL, "AVG":AVG, "THP":THP, "TDP":TDP,
    "OB":OB, "OmM":OmM, "ODiv":ODiv, "GM":GM, "HM":HM, "S":S,
    "CF":CF, "CL":CL, "ORS":ORS, "FGL":FGL, "FBPC":FBPC,
    "FNA":FNA, "FNA2":FNA2, "FIM":FIM, "FIP":FIP
}

COPULA_LIKE = {"TP","TM","TL","THP","TDP","OB","OmM","ODiv","GM","HM","S","CF","CL","ORS"}

KNOWN_CF1F2_PAIRS = [
    ("TP","TL"), ("TM","FNA"), ("TP","FBPC"), ("FBPC","FBPC"),
    ("TM","TM"), ("FIP","FIP"), ("FGL","TM")
]

def symmetric_power_measure(n:int, q:float=0.1):
    """For sorted inputs, only |A_(i)| matters: m(A)= (|A|/n)^q."""
    sizes = np.arange(n,0,-1,dtype=float)
    return np.power(sizes/n, q)

def choquet_standard(x, q=0.1):
    x=np.asarray(x,dtype=float)
    xs=np.sort(x,axis=-1)
    xprev=np.concatenate([np.zeros_like(xs[...,:1]),xs[...,:-1]],axis=-1)
    m=symmetric_power_measure(xs.shape[-1],q)
    return np.sum((xs-xprev)*m,axis=-1)

def choquet_expanded(x, q=0.1):
    x=np.asarray(x,dtype=float)
    xs=np.sort(x,axis=-1)
    xprev=np.concatenate([np.zeros_like(xs[...,:1]),xs[...,:-1]],axis=-1)
    m=symmetric_power_measure(xs.shape[-1],q)
    return np.sum(xs*m-xprev*m,axis=-1)

def cf_integral(x, F:Callable, q=0.1):
    """Standard-form CF integral: min(1, sum_i F(delta x_i, m(A_i)))."""
    x=np.asarray(x,dtype=float)
    xs=np.sort(x,axis=-1)
    xprev=np.concatenate([np.zeros_like(xs[...,:1]),xs[...,:-1]],axis=-1)
    m=symmetric_power_measure(xs.shape[-1],q)
    z=np.sum(F(xs-xprev,m),axis=-1)
    return clip01(z)

def cc_integral(x, C:Callable, q=0.1):
    """Expanded CC integral."""
    x=np.asarray(x,dtype=float)
    xs=np.sort(x,axis=-1)
    xprev=np.concatenate([np.zeros_like(xs[...,:1]),xs[...,:-1]],axis=-1)
    m=symmetric_power_measure(xs.shape[-1],q)
    z=np.sum(C(xs,m)-C(xprev,m),axis=-1)
    return clip01(z)

def cf1f2_integral(x, F1:Callable, F2:Callable, q=0.1):
    """Expanded CF1F2 integral:
       min(1, x_(1) + sum_{i=2}^n [F1(x_i,m_i)-F2(x_{i-1},m_i)]).
    """
    x=np.asarray(x,dtype=float)
    xs=np.sort(x,axis=-1)
    n=xs.shape[-1]
    m=symmetric_power_measure(n,q)
    if n==1: return clip01(xs[...,0])
    delta=F1(xs[...,1:],m[1:])-F2(xs[...,:-1],m[1:])
    z=xs[...,0]+np.sum(delta,axis=-1)
    return clip01(z)

@dataclass
class PairCheck:
    dominates: bool
    f1_first_increasing: bool
    boundary_ok: bool
    min_margin: float

def check_cf1f2_pair(F1:Callable, F2:Callable, grid=101, tol=1e-9) -> PairCheck:
    """Numerical sanity check of key CF1F2 conditions on [0,1]^2.
    Not a proof; it only flags obvious violations.
    """
    a=np.linspace(0,1,grid)
    X,Y=np.meshgrid(a,a,indexing="ij")
    z1=F1(X,Y); z2=F2(X,Y)
    margin=float(np.min(z1-z2))
    dominates=margin>=-tol
    f1_inc=np.all(np.diff(z1,axis=0)>=-tol)
    boundary=(abs(float(F1(0,1)))<1e-7 and abs(float(F2(0,1)))<1e-7
              and abs(float(F1(1,1))-1)<1e-7)
    return PairCheck(dominates, bool(f1_inc), bool(boundary), margin)
