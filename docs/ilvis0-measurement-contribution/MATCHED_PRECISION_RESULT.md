# Precision check on the 33 unfinished fits

All 33 fixed-point pairs reproduced their saved binary64 costs.
With wider arithmetic, **31/33** had a cost change within the original limit. The cost still rose in 8/33 pairs.

| Generated case | Fitted model | Gyro cap | Removal profiled | Wide cost change |
|---|---|---:|---|---:|
| flat_still | sphere_rotating | ±20°/h | yes | -1.31e-07 |
| sphere_rotating | flat_still | ±20°/h | yes | +0.000528 |

All endpoints and probe steps were held fixed. These are cost checks, with no new optimization and no later receiver observations. All original stopping labels remain unchanged. Wider arithmetic addresses most of the cost failures at the saved points. The two exceptions and the wider solver still require separate checks.

[Frozen plan](MATCHED_PRECISION_PLAN.md) · [Per-fit results](matched-precision-report.json)
