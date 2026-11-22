# Faster source-error transfer with exact arithmetic

The predictor reconciles its reference position and all 27 derivative
columns with independently enclosed source values. Each input coefficient
is a binary fraction. The revised calculation adds their corrections
exactly by aligning their powers of two. It then adds the existing
nonlinear remainder as a rational number and rounds outward once.

In a local CPU timing, 512 transfers took **1.57 seconds**, compared with
**3.75 seconds** for the archived rational calculation. The verification
checks matched the original rounded results, including nonbinary
remainder and calibration-domain cases. All 30 focused and regression
tests passed. The timing measures only this part of packet propagation.

The [recorded-input check](ESA_SHAPE_PREFIX_PREFLIGHT_V2_PLAN.md) kept
the same 470 packets, two queries and 50-second propagation limit per model.
Both completed under that limit.

| Model | Bound time | Largest difference from a sealed position | Largest unshared remainder at the second query |
| --- | ---: | ---: | ---: |
| Zero-field globe | 35.9 s | 1.42 nm | 7.24 mm |
| Zero-field disc | 34.9 s | 1.42 nm | 7.94 mm |

The disc’s two bound reports matched the earlier run byte for byte. The
earlier globe timeout remains recorded. The new run charged two bounds
and used no new native forecasts, fits, later receiver positions or
reserved groups.

The 155,868-packet history would still take hours at the preflight's
observed rate. The table reports unshared remainders. The full bound
must also account for the linked calibration terms over all reports
and the constraints from the earlier fit.

The [shared coefficient study](ESA_SHARED_PROFILE_RESULT.md) now identifies
which terms remain important after linking them across the record.

[Verified matched evidence](esa-shape-prefix-preflight-v2-evidence/README.md) ·
[Original preflight](ESA_SHAPE_PREFIX_PREFLIGHT_RESULT.md).
