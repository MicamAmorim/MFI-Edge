
import numpy as np
from src.operators import *
rng=np.random.default_rng(1)
x=rng.random((200,8))
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
print("OK: Choquet identities, 21 functions, CF1F2(TP,TL) sanity.")
