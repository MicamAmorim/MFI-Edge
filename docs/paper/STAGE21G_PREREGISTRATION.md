# Stage 21G preregistration — human-consensus ranking analysis

Stage 21G is the final diagnostic stage before the single-candidate Stage 21H
decision. It fits no detector, changes no frozen map, and reads only BSDS500
validation. The exact frozen incumbent and Stage-20A--D PNGs are analyzed.

At each pixel belonging to the exact union of human boundary annotations,
consensus strength is the fraction of annotations having a boundary within a
fixed Euclidean radius of `1.5` pixels. This small fixed allowance addresses
annotator raster misalignment; it is not the Berkeley matching tolerance and
does not create an official score. Consensus strata are fixed as low
`(0,1/3]`, medium `(1/3,2/3]`, and high `(2/3,1]`.

For every frozen method, report pooled and per-image Spearman correlation,
Kendall tau-b, and pairwise accuracy that a higher-consensus boundary pixel
receives a higher score than a lower-consensus pixel, with score ties worth
one half. Report score and frozen-ODS detection-rate summaries by consensus
stratum. Emit a deterministic table of weak-versus-strong consensus inversions
for failure inspection; this table is diagnostic and cannot select or tune a
model.

The fixed positions 1/50/100 preview contains input, consensus strength,
incumbent final score, and Stage-20C final score. The required official
attachment rescoring is unchanged and remains reference-unverified. Completion
does not promote a candidate. It advances only to a Stage-21H synthesis that
may preregister at most one causally justified mechanism under the already
fixed primary promotion rules.
