import numpy as np
from src.operators import *
from src.fuzzy_measures import (
    capacity_table_additive, capacity_table_sugeno, capacity_table_2additive,
    tail_capacities, validate_capacity_table, shapley_values, interaction_matrix,
)
from src.measure_learning import learn_additive, learn_2additive

rng=np.random.default_rng(1)
x=rng.random((200,8))

# Legacy identities.
a=choquet_standard(x,.1)
b=choquet_expanded(x,.1)
assert np.max(np.abs(a-b))<1e-10
c=cf_integral(x,TP,.1)
d=cf1f2_integral(x,TP,TP,.1)
assert np.max(np.abs(a-c))<1e-10
assert np.max(np.abs(a-d))<1e-10
assert len(FUNCTIONS)==21
chk=check_cf1f2_pair(TP,TL)
assert chk.dominates and chk.f1_first_increasing and chk.boundary_ok

# Additive capacity must equal weighted average under classical Choquet.
w=np.arange(1,9,dtype=float); w/=w.sum()
spec={"kind":"additive","weights":w}
ca=choquet_standard(x,measure_spec=spec)
wa=x@w
assert np.max(np.abs(ca-wa))<1e-9
assert validate_capacity_table(capacity_table_additive(w))

# Sugeno-lambda capacity validity for sub/additive singleton-density regimes.
for target in (0.7,1.0,1.3):
    g=w*target
    tab=capacity_table_sugeno(g)
    assert validate_capacity_table(tab,1e-6)

# Positive 2-additive example.
s=np.ones(8)*0.08
p=np.zeros((8,8))
for i in range(7): p[i,i+1]=p[i+1,i]=0.01
tab2=capacity_table_2additive(s,p)
assert validate_capacity_table(tab2,1e-6)
sv=shapley_values(tab2)
assert abs(sv.sum()-1.0)<1e-7
I=interaction_matrix(tab2)
assert np.max(np.abs(I-I.T))<1e-12

# Local/adaptive measure variants produce valid nested weights.
for ms in (
    {"kind":"adaptive_power","mode":"mean"},
    {"kind":"adaptive_power","mode":"geomean"},
    {"kind":"local_additive","mode":"softmax"},
):
    m=tail_capacities(x,ms)
    assert m.shape==x.shape
    assert np.all(np.isfinite(m))
    assert np.min(m)>=-1e-9 and np.max(m)<=1+1e-9
    # A_(i+1) subset A_(i): capacities cannot increase with i.
    assert np.all(np.diff(m,axis=-1)<=1e-8)

# Small constrained-learning smoke tests.
y=(x[:,0]+0.7*x[:,1]>0.9).astype(float)
la=learn_additive(x,y)
assert validate_capacity_table(np.asarray(la['capacity_table']))
l2=learn_2additive(x,y,maxiter=150)
assert validate_capacity_table(np.asarray(l2['capacity_table']),1e-5)

print("OK: legacy identities + adaptive/learned fuzzy-measure tests.")
