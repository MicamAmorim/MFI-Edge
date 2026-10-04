
# MFI-Edge

MFI-Edge (Multiscale Functional Information Edge Detection) is a research prototype for multiscale edge detection using:
1. eight local descriptors per scale;
2. fuzzy fusion by a standard-form `CF` integral or expanded `CF1F2` integral;
3. a symmetric power fuzzy measure `m(A)=(|A|/n)^q`;
4. empirical functional surprisal `I=-log2 P_H0(score >= observed)`;
5. coarse-to-fine refinement across configurable scales;
6. heatmaps, refinement masks, best-scale map and prototype BSDS/synthetic metrics.


## Repository layout

- `src/` — descriptors, fuzzy integrals, multiscale pipeline, evaluation and visualization.
- `datasets/sintetics/test/` — fixed synthetic test images and exact ground-truth masks.
- `synthetic_demo.py` — reproducible synthetic generator and smoke benchmark.
- `run_synthetic_to_3x3.py` — multiscale experiment down to 3x3 windows.
- `prototype.py` — BSDS500 runner and operator sweeps.
- `outputs_synthetic/` and `outputs_synthetic_3x3/` — generated experiment artefacts (ignored by Git; reproducible from the scripts).

> The directory name `sintetics` is retained intentionally to match the project layout chosen for this repository.

## Mathematical forms

### CF
`CF_m^F(x) = min(1, sum_i F(x_(i)-x_(i-1), m(A_(i))))`

### CF1F2
`CF_m^(F1,F2)(x) = min(1, x_(1) + sum_{i=2}^n [F1(x_(i),m(A_(i))) - F2(x_(i-1),m(A_(i)))])`

`F1=F2=C` recovers the CC-style expanded construction.  
With `F=product`, both standard and expanded versions recover the classical discrete Choquet integral.

## The 21 functions implemented

`TP, TM, TL, AVG, THP, TDP, OB, OmM, ODiv, GM, HM, S, CF, CL, ORS, FGL, FBPC, FNA, FNA2, FIM, FIP`.

Not every function is theoretically admissible in every Choquet-like family. `check_cf1f2_pair` numerically checks dominance, first-coordinate monotonicity and key boundaries. This is a screening check, not a proof.

## Install

```bash
pip install -r requirements.txt
```

## Verify mathematics

```bash
python test_math.py
```

## Local synthetic smoke test

```bash
python synthetic_demo.py
```

## BSDS500: 10 validation images + ground truth

```bash
python prototype.py --download --n-images 10 --operator-mode default
```

This downloads 10 public BSDS500 validation images and their `.mat` annotations from the BIDS/BSDS500 mirror.

### Run all 21 functions in CF

```bash
python prototype.py --download --n-images 10 --operator-mode cf21
```

### Run 21 diagonal expanded variants `CF1F2(F,F)`

```bash
python prototype.py --download --n-images 10 --operator-mode diagonal21
```

### Run literature-motivated CF1F2 pairs

```bash
python prototype.py --download --n-images 10 --operator-mode knownpairs
```

### Scan all 21 x 21 pairs that pass the numerical admissibility screen

```bash
python prototype.py --download --n-images 10 --operator-mode allpairs
```

## Outputs

For each operator/image:
- `bits_s33.png`, `bits_s17.png`, `bits_s9.png` — functional-surprisal heatmaps;
- `refine_s*.png` — regions retained by the coarse-to-fine funnel;
- `final_bits.png` — max-surprisal across scales;
- `best_scale.png` — scale producing the maximum surprisal at each pixel;
- `panel.png` — compact visual summary.

CSV files:
- `outputs/metrics.csv`
- `outputs/summary.csv`

## Important methodological caveat

The included metric is a **prototype tolerant pixel F1** using a small spatial tolerance, not the official Berkeley ODS/OIS/AP evaluation code. Use this version for method development and visual/ablation analysis; for a paper, add the official BSDS benchmark evaluation.

The default surprisal uses **self-calibration** of a background distribution to keep the prototype immediately runnable. A paper-grade experiment should estimate `H0` only from the training split (non-boundary pixels) and freeze that calibration before validation/test.
