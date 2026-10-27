# Stage 21F preregistration — context/localizer/NMS decomposition

Stage 21F is diagnostic only. It reconstructs the registered full-UDED fit of
compact MFI and frozen Stage 20C, then requires byte-for-byte agreement with
their existing BSDS500-validation PNGs. It changes no descriptor, fit,
capacity, calibration, gate, localizer, NMS rule, map, or threshold and reads
no protected split.

For both methods, report the contextual score, shared median-conditioned
Scharr magnitude before NMS, context-gated Scharr score before NMS, and final
score formed by gating the unchanged Scharr+NMS localizer. The last score must
serialize exactly to the frozen PNG for every image.

Report pooled and per-image AUC/AP against the fixed annotation-union label
dilated by `0.0075` of the image diagonal. Report descriptive bidirectional
union distances and support after stable top-k thresholding to match each
method's frozen final-ODS edge density. These are attribution diagnostics, not
official Berkeley metrics; intermediate dense maps are not benchmark outputs.

The deterministic positions 1/50/100 preview contains input, annotation union,
both contexts, pre-NMS Scharr, both pre-NMS combinations, and both final maps.
Completion advances only to Stage 21G human-consensus ranking analysis. No
detector may be fitted or promoted from Stage 21F, and Berkeley reference
reproduction remains unverified.
