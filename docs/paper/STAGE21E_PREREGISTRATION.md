# Stage 21E preregistration â€” spatial-tolerance response curve

## Role and immutable inputs

Stage 21E is a frozen-map diagnostic, not a detector experiment. It evaluates
the exact BSDS500-validation PNGs already frozen for compact MFI and Stage
20A--20D. It does not fit, regenerate, calibrate, select, or promote a model,
and it reads no protected split. The compact distorted-Choquet controller
remains the incumbent.

## Protocol

For each frozen method, run the same pinned Berkeley boundary benchmark with
all annotations, `nthresh=99`, thinning enabled, and one-to-one
`correspondPixels` matching at exactly these image-diagonal distance fractions:

- `0.00375`
- `0.0075` (the only primary endpoint)
- `0.015`
- `0.025`

The existing complete Stage-21B results at `0.0075` and `0.025` must be reused
without rematching. Only the two missing tolerance tracks may invoke the
matcher. Matching is resumable from nonempty per-image count tables and
collection occurs only after all 100 images for a method are present.

## Required outputs and interpretation

Emit one table of ODS/OIS/AP (plus ODS precision, recall, and threshold) over
method and distance, a delta table relative to each method's `0.0075` row,
complete PR-count-derived curves for the two newly matched tracks, a compact
JSON/Markdown summary, and `best_method_preview.png` copied byte-for-byte from
the fixed Stage-21B positions 1/50/100 panel.

The outputs are sensitivity curves only. They may diagnose how rapidly scores
change with spatial tolerance, but only `0.0075` is the standard primary
protocol; no looser result may promote or rescue a model. Results are not an
Estrada--Jepson evaluation. The pinned Windows matcher remains clock-seeded
and reference reproduction remains unverified, so cross-run absolute drift
must be retained as a caveat rather than treated as detector change.

Completion advances only to Stage 21F context/localizer/NMS decomposition.
