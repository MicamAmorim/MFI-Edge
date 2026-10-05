# MFI-Edge — architecture map for the future paper

This file is the **editable source of truth** for the model diagrams.  Keep it synchronized whenever a model family is added, renamed, or promoted.  The diagrams are Mermaid so they can be rendered directly by GitHub and later redrawn for the manuscript.

## 1. Global research architecture

```mermaid
flowchart LR
    I[Input image] --> C0[Robust conditioning]
    C0 --> CX[Context analyzer]
    C0 --> FE[Oriented multiscale descriptors]
    C0 --> SL[Spatial localizer branch]

    CX --> CTX[Context maps\nblur • noise • texture • HF/LF • coherence • heterogeneity]
    FE --> SG[Optional Shapley / regime gating]
    SG --> FA[Within-scale fuzzy aggregation]
    CTX --> SG
    CTX --> FA

    FA --> MS[Scale maps\n25 • 13 • 7 • 5 • 3]
    MS --> HM[Hierarchical multiscale fusion\ncoarse 25/13 + fine 7/5/3]
    HM --> MFI[MFI attention / evidence]
    MS --> U[Scale disagreement + entropy]
    U --> UNC[Uncertainty map]

    CTX --> SL
    SL --> DB[Dynamic derivative bank\nScharr • Sobel • DoG1 • DoG2]
    DB --> LOC[Precise spatial localization + NMS]

    MFI --> CTRL[Contextual / bilateral controller]
    UNC --> CTRL
    LOC --> CTRL
    CTRL --> SCORE[Continuous edge score]
    SCORE --> TH[Selection-frozen threshold / hysteresis]
    MFI --> LINK[MFI-guided topology repair]
    TH --> LINK
    LINK --> E[Final edge map]

    E --> EV[ODS/OIS/AP/F1 + connectivity + runtime]
```

The central hypothesis is that **MFI is primarily contextual evidence**, while the spatial branch is responsible for precise localization.  The controller decides how much the contextual evidence should influence the localizer rather than simply summing both maps.

---

## 2. Model A — MFI-Classic / historical control

```mermaid
flowchart LR
    I[Image] --> MED[Median 3x3]
    MED --> F[Oriented descriptors\nscales 25,13,7,5,3]
    F --> C[CF1F2 CL,CL\nfixed power capacity]
    C --> S[Functional-information surprisal]
    S --> CONF[MFI percentile confidence]
    CONF --> ROI[Top-confidence ROI]
    MED --> SCH[Scharr]
    ROI --> SCH
    SCH --> NMS[Oriented NMS]
    NMS --> T[Frozen threshold]
    CONF --> GL[MFI-guided geodesic linking]
    T --> GL
    GL --> E[Edge map]
```

Purpose in the article: historical baseline and ablation anchor.

---

## 3. Model B — MFI-Fuzzy++

```mermaid
flowchart LR
    I[Image] --> CTX[Context analyzer]
    I --> D[Multiscale descriptor tensors]
    CTX --> R[Regime memberships]
    D --> SH[Global or regime-specific Shapley gating]
    R --> SH

    SH --> OP{Aggregation family}
    OP --> STD[CF / CC / CF1F2]
    OP --> RDF[d-CF / d-CC / d-XC]
    OP --> SW[SWAFED local power measure]
    OP --> CI[Choquet-inspired]
    OP --> CP[Partition-conditioned aggregation]

    STD --> CAP{Capacity family}
    RDF --> CAP
    SW --> CAP
    CAP --> PWR[Power / additive / Sugeno]
    CAP --> DP[Distorted probability]
    CAP --> KINT[Regularized pair / k-interaction surrogate]
    CAP --> SCALE[Scale-specific learned capacities]

    PWR --> SM[Per-scale evidence]
    DP --> SM
    KINT --> SM
    SCALE --> SM
    CI --> SM
    CP --> SM

    SM --> H[Hierarchical coarse/fine Choquet]
    H --> MFI[MFI attention]
    SM --> U[Uncertainty]
```

Research question: **what to aggregate, how to aggregate, and which capacity should be used in each local regime and scale?**

---

## 4. Model C — CH-MFI / bilateral contextual-localization model

```mermaid
flowchart TB
    I[Image]
    I --> CTX[Context analyzer]
    I --> FZ[Fuzzy context branch]
    I --> SP[Spatial localization branch]

    CTX --> FZ
    FZ --> MFI[MFI attention]
    FZ --> U[Uncertainty]

    CTX --> ROUTER[Localizer router]
    SP --> BANK[Scharr • Sobel • DoG sigma1 • DoG sigma2]
    ROUTER --> BANK
    BANK --> L[Dynamic localizer]
    L --> NMS[NMS]

    MFI --> B[bilateral controller]
    U --> B
    NMS --> B
    B --> S[score = L' controlled by context]
    S --> POST[threshold / hysteresis / topology]
    POST --> E[Final edge]
```

This is the current **CH-MFI-v2** research direction.  It operationalizes the observation from natural-image experiments that MFI may rank relevant regions well without being the best pixel localizer itself.

---

## 5. Model D — MFI-Hybrid / fuzzy ensemble of heterogeneous detectors

```mermaid
flowchart LR
    I[Image] --> M[MFI / CH-MFI]
    I --> T[TEED]
    I --> P[PiDiNet or other lightweight learned detector]
    I --> C[Classical dynamic localizer]

    M --> Q[Quality / uncertainty descriptors]
    T --> F[Fuzzy detector fusion]
    P --> F
    C --> F
    M --> F
    Q --> ROUTE[Context-dependent capacity / router]
    ROUTE --> F
    F --> NMS[NMS / crisp localization]
    NMS --> E[Final edge]
```

Purpose: test whether fuzzy nonadditive fusion is more valuable **between heterogeneous detectors** than only between handcrafted descriptor channels.

---

## 6. Model E — uncertainty + granularity-aware CH-MFI

```mermaid
flowchart LR
    A[Multiple human annotations] --> PG[GT agreement map p_GT]
    PG --> UG[Annotation uncertainty]
    PG --> RL[Ranking / certainty supervision]

    I[Image] --> CH[CH-MFI]
    G[Granularity parameter g] --> CH
    CH --> E1[Structural/coarse edge]
    CH --> E2[Intermediate edge]
    CH --> E3[Fine/texture edge]
    CH --> UM[Model uncertainty]

    UG --> RL
    E1 --> RL
    E2 --> RL
    E3 --> RL
    RL --> TRAIN[Future learning stage]
    UM --> T[Uncertainty-aware threshold/linking]
```

This family requires datasets with multiple annotations (e.g. BSDS500 / Multicue) and should not be judged only on UDED.

---

## 7. Experimental decision flow

```mermaid
flowchart LR
    DEV[Selection / train data] --> LEARN[Learn capacities, Shapley, routers]
    LEARN --> CV[Inner CV model ranking]
    CV --> TOP[Freeze top candidates + thresholds]
    TOP --> HELD[Held-out evaluation]
    HELD --> BOOT[Paired bootstrap + effect sizes]
    BOOT --> EXT[Cross-dataset external test]
    EXT --> PROMOTE{Promote?}
    PROMOTE -->|yes| MAIN[main]
    PROMOTE -->|yes| WEB[mfi-edge-webui registry]
    PROMOTE -->|no| DEV
```

### Rules to preserve

- Never re-rank the full model family using held-out/test results.
- Capacity, Shapley, H0, context routers and thresholds must be learned/fitted without held-out leakage.
- UDED is useful for external generalization but is too small to be the sole dataset for final claims.
- Official publication metrics should ultimately use the official dataset evaluation protocol (especially BSDS500 boundary matching).
