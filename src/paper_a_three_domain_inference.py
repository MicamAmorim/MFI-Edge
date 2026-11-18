"""Draft three-domain inference core. Pure functions, no I/O or freeze authority.
Derived from the existing paired analysis; only domain eligibility is extended.
Actual outcome access remains prohibited until independent prospective review.
Source SHA256: cea98dc0ae431aa58b4f791b6e8f7822ff819ce702ebb2c91f18615924f8ee92 (normalized UTF-8).
"""
from __future__ import annotations
import numpy as np
from scipy.stats import rankdata

def partition_primary_secondary(records:list[dict],cohort:list[dict]):
    expected={(r['dataset'],r['image_id']):r for r in cohort}
    actual={(r['dataset'],r['image_id']) for r in records}
    if len(expected)!=len(cohort) or len(actual)!=len(records) or actual!=set(expected):
        raise ValueError('Exact full locked row identities required')
    primary=[];secondary=[]
    for r in records:
        role=expected[(r['dataset'],r['image_id'])]['analysis_role']
        if role=='primary' and r['dataset'] in {'MultiCue','NYUDv2','VSB100'}:primary.append(r)
        elif role=='secondary_exploratory' and r['dataset']=='BIPED':secondary.append(r)
        else:raise ValueError('Unapproved primary/secondary population')
    return primary,secondary

def rho(x: np.ndarray, y: np.ndarray) -> float:
    """Tied-midrank Spearman; reject undefined constant vectors."""
    xr = rankdata(np.asarray(x, dtype=float), method="average")
    yr = rankdata(np.asarray(y, dtype=float), method="average")
    xr = xr - xr.mean()
    yr = yr - yr.mean()
    nx, ny = np.linalg.norm(xr), np.linalg.norm(yr)
    if nx == 0 or ny == 0:
        raise ValueError("Undefined Spearman: constant/tied feature or outcome")
    return float(xr @ yr / (nx * ny))


def aggregate_domain_rho(rows: list[dict], x_key: str, y_key: str) -> tuple[float,dict]:
    groups = {}
    for row in rows:
        groups.setdefault(row["dataset"], []).append(row)
    values, weights, detail = [], [], {}
    for domain in sorted(groups):
        records = groups[domain]
        if len(records) < 3:
            raise ValueError("Too few independent captures per domain")
        r = rho(np.asarray([v[x_key] for v in records]),
                np.asarray([v[y_key] for v in records]))
        detail[domain] = {"n":len(records),"rho":r}
        values.append(r)
        weights.append(len(records)-1)
    if set(groups) != {"MultiCue", "NYUDv2", "VSB100"}:
        raise ValueError("Expected the three prospectively specified domains")
    return float(np.average(values, weights=weights)), detail


def permutation_test(rows: list[dict], hypothesis: str, count: int,
                     seed: int) -> dict:
    if hypothesis not in ("H1","H2"):
        raise ValueError("Unknown primary hypothesis")
    if count < 1:
        raise ValueError("Permutation count must be positive")
    x_key = "X1" if hypothesis == "H1" else "X2"
    y_key = "Y1" if hypothesis == "H1" else "Y2"
    sign = -1 if hypothesis == "H1" else 1
    observed, details = aggregate_domain_rho(rows, x_key, y_key)
    groups = {}
    for row in rows:
        groups.setdefault(row["dataset"], []).append(row)
    prepared = []
    denom = 0
    for domain in sorted(groups):
        group = groups[domain]
        xr = rankdata([v[x_key] for v in group], method="average")
        yr = rankdata([v[y_key] for v in group], method="average")
        xr = xr - xr.mean()
        yr = yr - yr.mean()
        nx,ny = np.linalg.norm(xr),np.linalg.norm(yr)
        if nx == 0 or ny == 0:
            raise ValueError("Constant variable in block")
        weight = len(group)-1
        denom += weight
        prepared.append((xr/nx,yr/ny,weight))
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(count):
        draw = sum(weight * float(x @ y[rng.permutation(len(y))])
                   for x,y,weight in prepared)/denom
        if sign * draw >= sign * observed - 1e-15:
            extreme += 1
    return {
        "hypothesis": hypothesis, "statistic_within_domain": observed,
        "domain_rho": details,
        "direction": "negative" if sign < 0 else "positive",
        "permutations": count,
        "extreme_permutations": extreme,
        "p_one_sided": (1+extreme)/(1+count),
        "mean_paired_F1_difference": float(np.mean([v[y_key] for v in rows])),
        "fraction_positive_difference": float(np.mean([v[y_key] > 0 for v in rows])),
    }


def stratified_bootstrap(rows: list[dict], hypothesis: str,
                         replicates: int, seed: int) -> dict:
    if hypothesis not in ("H1","H2"):
        raise ValueError("Unknown primary hypothesis")
    x_key = "X1" if hypothesis == "H1" else "X2"
    y_key = "Y1" if hypothesis == "H1" else "Y2"
    groups={}
    for row in rows:
        groups.setdefault(row["dataset"], []).append(row)
    rng = np.random.default_rng(seed)
    valid=[]
    bad=0
    for _ in range(replicates):
        sample=[]
        for domain in sorted(groups):
            g=groups[domain]
            sample.extend(g[j] for j in rng.integers(len(g),size=len(g)))
        try:
            estimate,_=aggregate_domain_rho(sample,x_key,y_key)
            valid.append(estimate)
        except ValueError:
            bad+=1
    if len(valid) < int(replicates * 0.95):
        raise ValueError("Too many undefined stratified bootstrap replicates")
    low,high=np.quantile(valid,[0.025,0.975])
    return {"ci95_lower":float(low),"ci95_upper":float(high),
            "valid_bootstrap_replicates":len(valid),
            "rejected_bootstrap_replicates":bad}


def holm2(a: float,b: float) -> tuple[float,float]:
    """Holm step-down for exactly two tests, adjusted p in original order."""
    if not (0<=a<=1 and 0<=b<=1):
        raise ValueError("Invalid p values")
    if a<=b:
        q1=min(1,2*a)
        return q1,max(q1,b)
    q2=min(1,2*b)
    return max(a,q2),q2


