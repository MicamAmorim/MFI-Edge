# Synthetic benchmark v2

This benchmark is generated deterministically by `synthetic_v2.py`.

- Validation: 40 images
- Held-out test: 60 images
- Size: 96x96
- Primitives: line, stripe, circle, ellipse, rectangle, triangle, sinusoidal boundary, multiple objects, T-junction
- Conditions: clean, Gaussian noise, salt-and-pepper, speckle, Gaussian blur, motion blur, illumination gradient, texture, artificial gaps, compound degradation

Ground truth is generated from the clean binary primitive before degradation. Gap cases deliberately weaken a segment in the observed image while preserving a continuous GT boundary.

The generator writes:
`datasets/sintetics/benchmark_v2/validation/{images,ground_truth,manifest.csv}` and
`datasets/sintetics/benchmark_v2/test/{images,ground_truth,manifest.csv}`.

Seeds are fixed by split in the generator, so the benchmark can be regenerated exactly.
