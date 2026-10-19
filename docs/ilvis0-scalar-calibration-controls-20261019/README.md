# Scalar calibration projection controls

**72/72 software controls passed** in 3.85 seconds. No original recordings, observed fits or native integrations were used.

The matrix compares stationary, eastbound, changing-direction and climbing reference motion under three truth models, all three candidates and two body-orientation histories. All seven calibration columns remain in the rank calculation.

[All 72 outcomes](controls.csv) include ranks, local projection, feasibility and actual nonlinear residual at feasible linear corrections. These are mathematical controls, not measured device errors or calibrated evidence.

| Motion | Cases | Rank range | Largest uncorrected RMS | Largest projected RMS | Feasible linear steps |
|---|---:|---|---:|---:|---:|
| stationary | 18 | 4–6 | 8.234253e-16 | 8.108177e-16 | 18 |
| eastbound | 18 | 6–6 | 0.03006832 | 1.119002e-15 | 18 |
| changing direction | 18 | 7–7 | 0.04140383 | 0.00433956 | 6 |
| climbing | 18 | 7–7 | 0.0206112 | 0.0007693376 | 6 |

RMS values are in m/s². Maxima can belong to different cases; compare individual rows for matched changes.

A local projection is unbounded and first order. Its removed difference need not be attainable with feasible nonlinear calibration; its remaining difference does not rule out other nonlinear solutions. No model verdict follows.

The main 53-stretch results and unresolved horizontal-only sensitivity outcome are unchanged.

[Frozen plan and limits](PLAN.md) · [Calibration ambiguity](../ilvis0-measurement-contribution/CALIBRATION.md) · [Measurement contributions](../ilvis0-measurement-contribution/README.md).
