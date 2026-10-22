# More training positions: a generated-data diagnostic

6/6 software diagnostics pass; 6/6 completed.

| Model | Processing | Five epochs: N / E / height | 292 epochs: N / E / height | Linear target met? |
|---|---|---:|---:|---|
| Specified-field globe | Zero removal | 420.263 / 747.100 / 39.927 m | 292.214 / 283.105 / 21.768 m | No |
| Specified-field globe | Profiled removal | 445.141 / 1068.424 / 54.499 m | 295.808 / 416.223 / 25.690 m | No |
| Zero-field globe | Zero removal | 420.160 / 748.501 / 49.232 m | 291.454 / 285.634 / 24.983 m | No |
| Zero-field globe | Profiled removal | 460.684 / 1071.583 / 68.364 m | 291.491 / 421.390 / 30.674 m | No |
| Flat disc | Zero removal | 447.043 / 150.881 / 70.007 m | 311.288 / 123.450 / 54.908 m | No |
| Flat disc | Profiled removal | 515.579 / 245.023 / 111.322 m | 337.358 / 154.925 / 70.726 m | No |

These are exactly checked outer bounds for the saved linearized prediction, **not nonlinear prediction ranges or aircraft confidence intervals**. All 27 physical columns and their original broad domain remain. Shared errors and nonlinear terms are omitted in this diagnostic.

The dense set includes every sparse training epoch. Native batch/endpoints agree exactly, and packet-boundary counters are preserved and checked. The target remains 20 / 20 / 50 m. A numerical pass and a useful linear width are different outcomes. Neither establishes useful full-history nonlinear bounds, an observation-error law or scientific significance.

[Fixed scope](PLAN.md) · [Earlier sparse-training diagnostic](../ilvis0-linear-leverage/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
