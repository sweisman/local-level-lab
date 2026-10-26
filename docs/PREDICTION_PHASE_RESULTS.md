# Prediction calibration: outcome and review

**Calibration stopped early. Validation was not run.** Two required fits failed
the frozen numerical stopping checks, so this phase cannot supply a calibrated
prediction threshold. The original **53 globe preferences, zero flat preferences
and zero unresolved comparisons** are unchanged.

## What completed

| Item | Outcome |
|---|---|
| Independent-noise development pilot | All 48 fits passed numerical and physical-error checks. |
| Calibration/validation software | All 62 qualification checks passed. |
| Calibration execution | 1,686 starts returned outcomes out of 7,176 planned, in 25.34 hours. |
| Returned numerical outcomes | 1,683 qualified fits, two failed fits and one cooperatively stopped start. |
| Physical forecast screens | All 1,685 completed forecasts pass the fixed error screens; calibrated goodness of fit remains open. |
| Independent validation | Not launched; its reserved seeds remain unused. |
| Saved-results diagnosis | Eight preselected records, including seven saved fits; no new fits, noise draws or native calculations. |

These calibration examples are generated measurements with known truth. Each
physical model fits its own generated data. They are not additional flights or
votes for an Earth model.

## Why the run stopped

Both starts of one specified-field globe setting failed numerical qualification.
The stopping rule required every setting to have a usable fit. Once both starts
failed, completing the remaining examples could not produce the required finite
threshold. The workers stopped cooperatively under that predeclared rule.

The [saved-results review](prediction-phase-review/README.md) finds a specific
issue: both starts stopped after 41 evaluations, below their 200-evaluation limit.
Their predicted positions met the physical error screens, and their fresh-check
position changes were under 0.5 mm. Their stationarity checks also passed.
However, their relative cost change was about **83 times the allowed tolerance**.
They therefore remain failed fits. The preceding noise example passed, as did
the available alternate-processing fit for the failing example.

This identifies a stopping-rule limitation to investigate. It does not establish
that the limit should be relaxed, or that a larger evaluation allowance would fix it.

## What remains open

There is no validated uncertainty threshold from this phase, and no statistical
significance claim for the aircraft results follows from it. Even successful
validation on this generated population would not establish the actual archive's
measurement-error law or coverage across all allowed calibration values.

The next reviewed phase should:

1. Qualify the stopping rule against independently known optima and the saved
   failure, preserving the original failed labels.
2. Freeze any revised method and a new finite calibration/validation design
   before further runs; protect validation outcomes from method tuning.
3. Establish useful prediction uncertainty for the recorded aircraft data before
   opening reserved confirmation groups or claiming significance.

**This is the agreed review checkpoint. No further campaign starts automatically.**

[Calibration evidence](prediction-calibration/README.md) ·
[All 7,176 planned starts, including unexecuted rows](prediction-calibration/results.csv) ·
[Eight-record review CSV](prediction-phase-review/results.csv) ·
[Frozen execution plan](prediction-score-qualification/EXECUTION_PLAN.md) ·
[Broader roadmap](ANALYSIS_ROADMAP.md) · [Reproducibility](REPRODUCIBILITY.md).
