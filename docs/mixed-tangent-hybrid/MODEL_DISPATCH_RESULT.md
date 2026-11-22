# Model-declared tangent precision: saved-result audit

A fixed rule selects the first selective tangent for both globe candidates and the established wide tangent for the flat candidate. The choice uses only the model ID, before fitting. On the complete sealed 24-case ESA development audit, all 16 globe pairs passed the original selective-versus-wide gate. The eight flat cases use the original wide outcomes unchanged.

| Selected method | Cases | Numerical passes |
| --- | ---: | ---: |
| Selective, globe | 16 | 16 |
| Wide, flat | 8 | 7 |

All 24 saved numerical dispositions match the wide reference, including one retained flat-model failure. This is a development audit of **existing results**.

Two generated 20-second smoke cases also run the dispatcher through the fitter and forecast. They match the wide reference on inputs and forecast positions within 0.00001 m. Both stop at the test’s eight-evaluation cap without meeting convergence, so neither is a qualifying fit. The dispatcher has not been timed or qualified for observed substitution; the established wide method remains in use. No Earth-model decision follows.

[Fixed method](MODEL_DISPATCH_PLAN.md) · [Per-case audit](MODEL_DISPATCH_RESULT.json) · [Original 24-case audit](../esa-observed-hybrid/combined/README.md).
