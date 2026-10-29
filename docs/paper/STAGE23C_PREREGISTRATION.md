# Stage 23C preregistration - cached UDED evidence atlas and individual baselines

## Role and firewall

Stage 23C is the first benchmark-reading Stage-23 experiment. It uses only the
overlap-clean UDED selection set. The known BSDS-lineage item `03-35028` is
excluded from the pair list before image or GT bytes are read. UDED held-out,
BSDS500 validation/test, BIPED, and every protected/external split are absent.

This stage extracts the frozen Stage-23A evidence pool once, certifies the
persisted cache records, and reports individual-map baselines. It does not
select a descriptor, fit an aggregator, change compact MFI, or promote a
detector. Stage 23D must analyze all thirteen maps regardless of their
individual ranking.

## Dataset and raster contract

- source: UDED `test_pair.lst`, selection positions `1,3,...,29` only;
- lineage exclusion: any selection filename with canonical BSDS id `35028`,
  applied before file reads;
- expected retained count: 14;
- raster: aspect-preserving downscale only to maximum side 256, bilinear RGB
  image and nearest-neighbour binary GT;
- fixed descriptor input conditioning is part of each cache identity;
- source-file SHA-256 and resized shape are recorded.

## Frozen evidence maps

Exactly the Stage-23A D01--D13 pool is permitted:

1. `scharr_pre_nms_magnitude`;
2. `lab_dizenzo_tensor_gradient` before NMS;
3. `gabor4_s5`;
4. `hessian_s7`;
5. `gabor4_s13`;
6. `hessian_s13`;
7. `gabor4_scale_persistence`;
8. `structure_tensor_coherence` at noise/integration scales `0.5/4.0`;
9. fixed-default `phase_congruency_max_moment`;
10. `halfdisc_distribution_contrast`, using uniform-LBP half-discs with radius
    `max(3, round(0.02*diagonal))`, 8 points at radius 1, 10 bins, 8
    orientations, and chi-square contrast;
11. fixed Stage-18j `pmi_dependency_deficit`;
12. fixed Stage-17x `semiglobal_changepoint`, maximum working side 256;
13. fixed Stage-18b `fh_region_boundary`, sigma `0.8`, `k=300`,
    8-connectivity, and no minimum-size cleanup.

The five incumbent maps use median-3 conditioned grayscale and the
`oriented_ms` schedule. The vector gradient uses channelwise median-3 CIELAB.
Changing any definition, preprocessing id, parameter, implementation hash,
source hash, dataset/split, or image creates a new cache key.

## Cache and failure contract

The canonical root is `cache/local_dev/stage23/`. Every map is requested
through `src/stage23_cache.py`. A valid exact-key hit must load without calling
its extractor. A miss may compute and atomically persist once. Corruption,
partial artifacts, manifest mismatch, or provenance mismatch fails closed; the
runner may not repair or overwrite it. After extraction, all 182 identities
must reload and validate from the manifest.

Inference extractors receive image arrays only and declare `gt_used=false`.
GT is used solely by the downstream baseline evaluator.

## Individual baseline protocol

Each raw evidence map is evaluated independently. Five repeats of three
image-grouped folds use seed `20261029`. For each fold and descriptor, a
41-point pooled score-quantile grid is constructed from outer-training images;
the threshold maximizing tolerant aggregate training F1 is frozen and applied
to outer-validation images. Tolerance is 0.0075 of image diagonal under the
repository UDED proxy. No membership, calibration, or aggregator is fitted.

Report aggregate outer-validation precision/recall/F1, mean/std fold F1 and
thresholds, support density, raw score distribution, per-fold/per-image rows,
runtime, and cache provenance. These are internal tolerant-proxy baselines,
not Berkeley ODS/OIS/AP and not a descriptor-selection rule.

## Qualitative and official attachments

`best_method_preview.png` uses retained sorted UDED positions 1, 7, and 14,
fixed before results. Every row is `input | GT | D01 | D02 | ... | D13`.
The preview is documentary only. Stage 23C has no BSDS candidate detector map,
so its default-on official manifest is incumbent-only and explicitly
non-selective. Prospective BSDS descriptor extraction remains Stage 23F work.

## Decision

Pass only if all 14 images and 182 artifacts complete, every exact reload and
manifest check passes, maps are finite and shape-correct, all 15 folds complete
for every descriptor, and the preview and tables exist. A pass registers Stage
23D over these exact cached maps. A failure permits only a harness or explicit
cache-repair experiment; it may not change the pool or proceed to aggregation.
