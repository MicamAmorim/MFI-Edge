# Synthetic test set

Deterministic synthetic edge-detection cases used by the MFI-Edge prototype.

- `images/`: noisy grayscale inputs.
- `ground_truth/`: exact binary edge masks used for evaluation.
- `manifest.csv`: case/seed/file mapping.

Cases: `vertical`, `diagonal`, `circle`, `box`, and `two_scale`.

The current generator is `synthetic_demo.make_case`; seeds are fixed in `manifest.csv` so the set can be regenerated exactly.
