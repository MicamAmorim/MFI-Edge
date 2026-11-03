from __future__ import annotations
"""Mathematical type audit: do not label arbitrary fusions as copulas/capacities.

Grid checks are counterexample detectors, NEVER proofs of copula properties.
No legacy operator output or historical results are modified by this audit.
"""
import numpy as np
from src.operators import FUNCTIONS, COPULA_LIKE
from src.fuzzy_measures import validate_capacity_table
from src.stage24_strict_generalized_cf1f2 import VALID_PAIRS, check_pseudo_pair


COPULA_THEORETICAL_CANDIDATES = (
    "TP","TM","TL","THP","OB","ODiv","CF","CL",
)


def numerical_copula_contract(fn, n=101, tol=1e-8):
    t=np.linspace(0,1,int(n))
    x,y=np.meshgrid(t,t,indexing="ij")
    z=np.asarray(fn(x,y),float)
    margin=max(
        float(np.max(np.abs(z[0,:]))),
        float(np.max(np.abs(z[:,0]))),
        float(np.max(np.abs(z[-1,:]-t))),
        float(np.max(np.abs(z[:,-1]-t))),
    )
    volumes=z[1:,1:]-z[:-1,1:]-z[1:,:-1]+z[:-1,:-1]
    return {
        "margins_pass":bool(margin<=tol),
        "two_increasing_grid_pass":bool(float(np.min(volumes))>=-tol),
        "max_margin_error":margin,
        "min_rectangular_volume":float(np.min(volumes)),
        "grid_size":int(n),
        "warning":"Finite grid is screening, not a mathematical proof",
    }


def audit_operator_labels():
    output={}
    for name in sorted(COPULA_LIKE):
        result=numerical_copula_contract(FUNCTIONS[name],n=101)
        output[name]={"legacy_registry":True,
                      "strict_candidate":name in COPULA_THEORETICAL_CANDIDATES,
                      **result}
    for name,pair in VALID_PAIRS.items():
        f1,f2=tuple(FUNCTIONS[p] for p in pair)
        output[name]={"generalized_pair":list(pair),
                      "numerical_pseudo_pair":check_pseudo_pair(f1,f2)}
    return output


def synthetic_contract():
    findings=audit_operator_labels()
    for name in COPULA_THEORETICAL_CANDIDATES:
        item=findings[name]
        if not item["margins_pass"] or not item["two_increasing_grid_pass"]:
            raise RuntimeError("Copula candidate failed numerical contract: "+name)
    for name in ("TDP","OmM","GM","HM","S","ORS"):
        if (findings[name]["margins_pass"] and
                findings[name]["two_increasing_grid_pass"]):
            raise RuntimeError("Historical non-copula mislabeled as copula: "+name)
    for name in VALID_PAIRS:
        if not all(findings[name]["numerical_pseudo_pair"].values()):
            raise RuntimeError("Invalid generalized CF1F2 numeric pair: "+name)
    # Numeric monotonicity check is separate from fuzzy-measure dependence.
    if not validate_capacity_table(np.array([0.,.4,.6,1.])):
        raise RuntimeError("Valid capacity rejected")
    return findings
