# Stage-1 best-method masks

Best operator under the fixed Stage-1 synthetic screen: **CF1F2(CL, CL)**.

Settings:
- scales: 33, 25, 17, 11, 7, 5, 3
- q = 0.1
- refine quantile = 0.82
- heterogeneity quantile = 0.82
- dilation radius = 3
- NMS enabled
- global ODS threshold = 14.102959885910124
- evaluation tolerance = 2 px

Important: the vertical case receives an empty final mask at the global ODS threshold. This is a real failure mode of the current configuration and should be preserved for diagnosis rather than hidden.
