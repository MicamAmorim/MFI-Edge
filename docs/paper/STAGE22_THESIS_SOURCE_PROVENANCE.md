# Stage 22 thesis-source provenance

The user supplied the private Google Drive folder:

`1LpKQgn5x3qG7BAXqZaMjdbigoHjARsuB`

The following thesis-era files were identified there before Stage 22 activation:

| Role | Drive file / folder | ID |
|---|---|---|
| historical boundary extraction | `getBoundaries.m` | `1zG-ig0zBaOiM_DhylUNA6slNi_8Hy2YF` |
| historical per-GT wrapper | `ComparisonResiduals.m` | `1Nwnsg1fdU6cOahj53bPk7wTVdsZdqyMd` |
| full thesis helper archive | `functions.zip` | `12Xn3GrNXMbx8YVpGcVJFBYifPDJz15P3` |
| historical helper folder | `external/` | `14j8Gm2WIt5bPaCMOHobXr1rmCTuMHVdD` |
| KITT boundary comparison package | `boundaryImageComparison/` | `1nWczAg3mTFwKQCjYYCSNQR6wv3hMZ3UM` |
| complete Estrada–Jepson v1.00 backup | `estradaJepsonMatching.bckp.m` | `1WxGnsYZcSvIIxPYfeu2lK6ouY-WZXVv0` |
| ejBCM-F confusion matrix | `ejmBasedConfusionMatrix.m` | `1V9AxCoglLdQf7W-hOhAIGvyNSrc01D3s` |

Historical `getBoundaries` dependencies in the Drive `external/` folder include `featureorient.m`, `nonmaxsup.m`, `doubleRosinUnimodalThr.m`, `rosinUnimodalThr.m`, `cleanLineSegments.m`, `derivative5.m`, `gaussfilt.m`, and `hysthresh.m`.

## Historical semantics confirmed from the thesis archive

`getBoundaries(im, inf)` normalizes the continuous map, estimates local orientation, applies non-maximum suppression, derives Rosin hysteresis thresholds, applies the historical `histmedcar` procedure, cleans line segments, and returns a uint8 boundary map.

`ComparisonResiduals('ejBCM-F', bnImage, gtImages, 0.025)` iterates over human ground-truth annotations independently and returns one `[precision, recall, F]` row per GT using `ejmBasedConfusionMatrix`.

The thesis text states that the automatically detected boundary map is matched against all human annotations using EjBCM and that the largest legacy F value (“best match”) per image is retained for the historical summary. Stage 22B therefore preserves every per-GT row and separately reports the historical best-match summary plus transparent mean/median distribution summaries.

These legacy metrics are descriptive and cannot replace or rescue the standard Berkeley `0.0075` promotion gate.
