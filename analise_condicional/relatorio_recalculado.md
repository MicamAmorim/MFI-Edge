# MFI-EDGE — landscape condicional de complementaridade e agregação

## Escopo e integridade
Reanálise exploratória de **resultados arquivados** da Stage24G–L. Não houve extração, refitting, seleção de limiares ou reexecução de benchmarks. Não são resultados de teste independente.
UDED: 14 imagens distintas, 7 conjuntos de descritores, 195 candidatos incluindo controles individuais.

## Casos fixados para exame
| Grupo | Operador | Δ F1 médio vs média | Ganhos/perdas por imagem |
|---|---|---:|---:|
| `fh_region_boundary|halfdisc_distribution_contrast` | `equal_mean` | +0.0000 | 0/0 |
| `gabor4_scale_persistence|halfdisc_distribution_contrast` | `maximum` | -0.0094 | 7/7 |
| `gabor4_scale_persistence|halfdisc_distribution_contrast` | `nonnegative_logistic` | +0.0290 | 11/3 |
| `gabor4_scale_persistence|pmi_dependency_deficit|structure_tensor_coherence` | `median` | +0.0158 | 12/2 |
| `halfdisc_distribution_contrast|hessian_s7` | `choquet_signed_2add` | +0.0329 | 11/3 |

## Rankings entre imagens
| Grupo | Modal retrospectivo | Fração modal | Spearman médio entre rankings de imagens | Fração de correlações negativas |
|---|---|---:|---:|---:|
| `fh_region_boundary|halfdisc_distribution_contrast` | `lukasiewicz` | 50.0% | 0.652 | 0.0% |
| `fh_region_boundary|halfdisc_distribution_contrast|structure_tensor_coherence` | `choquet_generalized_150` | 35.7% | 0.842 | 0.0% |
| `gabor4_scale_persistence|halfdisc_distribution_contrast` | `lukasiewicz` | 35.7% | 0.244 | 36.3% |
| `gabor4_scale_persistence|pmi_dependency_deficit|structure_tensor_coherence` | `median` | 57.1% | 0.618 | 0.0% |
| `gabor4_scale_persistence|structure_tensor_coherence` | `gcf_cl_cl` | 42.9% | 0.399 | 17.6% |
| `halfdisc_distribution_contrast|hessian_s7` | `gcf_tp_tl` | 28.6% | 0.434 | 20.9% |
| `halfdisc_distribution_contrast|pmi_dependency_deficit` | `minimum` | 28.6% | 0.665 | 0.0% |

## Mapas espaciais de descritores
{"status": "complete", "verified_descriptor_maps": 182, "group_image_records": 98, "note": "Sem GT ou reextração; correlações exploratórias (muitos testes)"}

## BSDS500 validation
{"status": "complete", "original_threshold_rows": 79200, "methods": 8, "images": 100, "contrasts": [{"method": "stage24gl_best_single", "reference": "incumbent_compact_positive_choquet", "n_images": 100, "mean_per_image_delta": 0.0217602368959207, "median_per_image_delta": 0.02739207187211462, "n_positive": 70, "n_negative": 30, "n_ge_0p01": 65, "n_le_minus_0p01": 28, "limitation": "Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation"}, {"method": "stage24gl_identity", "reference": "incumbent_compact_positive_choquet", "n_images": 100, "mean_per_image_delta": 0.03782419479636535, "median_per_image_delta": 0.036424274702760884, "n_positive": 90, "n_negative": 10, "n_ge_0p01": 76, "n_le_minus_0p01": 7, "limitation": "Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation"}, {"method": "stage24gl_identity_quantile", "reference": "incumbent_compact_positive_choquet", "n_images": 100, "mean_per_image_delta": 0.03418480364176342, "median_per_image_delta": 0.03475519373631536, "n_positive": 80, "n_negative": 20, "n_ge_0p01": 70, "n_le_minus_0p01": 11, "limitation": "Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation"}, {"method": "stage24gl_pair04_logistic", "reference": "incumbent_compact_positive_choquet", "n_images": 100, "mean_per_image_delta": -0.062484679141359474, "median_per_image_delta": -0.037897001864927005, "n_positive": 33, "n_negative": 67, "n_ge_0p01": 28, "n_le_minus_0p01": 64, "limitation": "Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation"}, {"method": "stage24gl_pair04_weighted", "reference": "incumbent_compact_positive_choquet", "n_images": 100, "mean_per_image_delta": -0.06244698164582968, "median_per_image_delta": -0.038333731981363306, "n_positive": 33, "n_negative": 67, "n_ge_0p01": 28, "n_le_minus_0p01": 64, "limitation": "Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation"}, {"method": "stage24gl_winner", "reference": "incumbent_compact_positive_choquet", "n_images": 100, "mean_per_image_delta": -0.022952904725146064, "median_per_image_delta": -0.022175437024983702, "n_positive": 38, "n_negative": 62, "n_ge_0p01": 29, "n_le_minus_0p01": 55, "limitation": "Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation"}, {"method": "stage24gl_winner_quantile", "reference": "incumbent_compact_positive_choquet", "n_images": 100, "mean_per_image_delta": -0.023793505826819022, "median_per_image_delta": -0.025203626780020055, "n_positive": 33, "n_negative": 67, "n_ge_0p01": 27, "n_le_minus_0p01": 57, "limitation": "Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation"}, {"method": "stage24gl_winner", "reference": "stage24gl_identity", "n_images": 100, "mean_per_image_delta": -0.060777099521511425, "median_per_image_delta": -0.059141614218958305, "n_positive": 9, "n_negative": 91, "n_ge_0p01": 6, "n_le_minus_0p01": 89, "limitation": "Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation"}], "warning": "Esses deltas F1 por imagem NÃO substituem os deltas ODS/OIS/AP oficiais; thresholds são da validation."}

## Mapas agregados BSDS existentes
{"status": "complete", "expected": 700, "verified": 700, "missing": 0, "winner_identity_pairs": 100, "note": "Somente scores agregados finais; não substituem 13 mapas de descritores BSDS"}

## Limitações inferenciais
1. Identificar quais imagens favorecem uma fórmula e correlacionar esse rótulo com características é **análise retrospectiva**, sujeita a seleção e multiplicidade.
2. Para cada imagem UDED, cinco repetições não são cinco observações independentes. A quantidade de imagens distintas permanece 14.
3. Uma fusão que supera a média de seus componentes não necessariamente supera o melhor descritor individual; o melhor indivíduo por imagem também é um oráculo retrospectivo.
4. Resumos marginais não identificam, por si, complementaridade espacial. Use `uded_spatial_group_features.csv` quando os mapas float com SHA estiverem disponíveis.
5. No BSDS, as variantes congeladas não constituem o landscape completo de descritores/agregadores. Comparações no limiar ODS obtido na própria validation são descritivas.
6. Não inferir uma política de seleção de agregadores ou causalidade a partir das correlações observadas. Exige treino/teste externo para alegação preditiva.

## Fontes originais
https://github.com/MicamAmorim/MFI-Edge/tree/mfi-edge-stage24-residual-suppression/results/paper_a_evidence/stage24_image_groups
https://github.com/MicamAmorim/MFI-Edge/tree/mfi-edge-stage24-residual-suppression/results/paper_a_evidence/stage24gl
