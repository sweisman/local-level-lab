# Fresh prediction calibration: why it stopped

**The run stopped at a numerical check. It established no uncertainty threshold,
and independent validation has not started.** The original 53-stretch aircraft
comparison is unchanged.

The corrected arithmetic had passed 48 development fits. This larger test used
fresh simulated measurements to check whether prediction errors could support
a reliable uncertainty threshold. Every physical model fitted its own generated
truth: these examples are not votes for globe or flat geometry.

## What completed

| Item | Verified outcome |
|---|---|
| Software qualification before launch | 126 source-bound checks passed. |
| Returned starts | 909 of 7,176 planned, in 9.58 hours. |
| Numerical outcomes | 904 passed; two failed; three stopped cooperatively. |
| Position-error screens | All 906 completed forecasts passed. |
| Complete noise families with available scores | 37 of 299 planned. Related settings and repeated starts are not independent trials. |
| Calibration threshold | Unavailable. The incomplete cohort cannot supply the planned bound. |
| Independent validation | Not launched. Its separate seed cohort remains unused. |

All workers exited and released their locks. The remaining allowance is closed;
the run will not be extended or restarted.

## The specific failure

Both prescribed starts failed for the same noise family: seed 281474977010693,
rate-sample input errors, specified-field globe, with upstream field removal
allowed. They stopped after 43 and 41 evaluations, below the 200-evaluation limit.
Both reported no positive predicted decrease.

Their position predictions were accurate under the fixed screens: later
horizontal RMS was about **2.58 m**, and height RMS was about **0.31 m**.
The numerical acceptance check asks a different question: does one fresh bounded
correction leave the cost, predicted positions and stationarity stable?

The stationarity and position-change checks passed. The relative cost changed
by about **6.27 × 10⁻⁸**, exceeding the unchanged **10⁻⁸** limit by about sixfold.
Maximum position change was under **0.20 mm**. These remain failed fits;
small position changes do not override the frozen cost requirement.

Once both starts failed, a required family score was unavailable. The frozen
rule therefore stopped the other workers cooperatively. Three interrupted
starts remain recorded, alongside every unexecuted planned row.

## What follows

The saved fits identify a cost-stability failure; they do not establish its
underlying cause or justify relaxing the limit. Any revised numerical method
needs separate qualification and a reviewed finite plan before another campaign.
No fits or native calculations were run to produce this report.

A publication-path repair passes 106 software checks, including a regression
that copies the actual frozen plan through the shared packager. Only the reporter
and its test changed after execution; the 242 execution-source snapshots,
numerical environment, scientific settings and saved outcomes remain preserved.

This test concerns two-minute generated trajectories and declared error laws.
It does not establish actual aircraft error coverage, calibrated significance
for the 53 stretches, or readiness to open protected ESA confirmation groups.

[Machine-checked report](README.md) · [All planned starts](results.csv) ·
[Frozen plan](PLAN.md) · [Earlier calibration outcome](../PREDICTION_PHASE_RESULTS.md) ·
[Next analyses](../NEXT_STEPS.md) · [Reproducibility](../REPRODUCIBILITY.md).
