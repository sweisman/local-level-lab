# Constraining the step removes the predicted large timing jump

**All 18 linear proposals stay inside their timing intervals.** Both sides and
all three spacings propose the same internal boundary for the failed cases.
The successful controls retain their existing physical timing limit.

| Saved example | Matrices retained | Proposed timing offset |
|---|---:|---:|
| Successful control, start 0 | 3 | −10.000 ms |
| Successful control, start 1 | 3 | −10.000 ms |
| Failed case, start 0 | 6 | about −6.666667 ms |
| Failed case, start 1 | 6 | about −6.666667 ms |

These offsets are parameters of generated-data controls, not measured device
calibrations. The 18 matrices describe four related saved points, not independent
experiments.

## What changed in the proposed step

The earlier full correction could cross a change of slope while compensating
with other calibration parameters. This component solves the full 27-column
linear problem separately inside each feasible timing interval. All physical
nuisance bounds and unidentified directions remain present.

All 18 solves succeeded in 21–25 iterations, below the fixed 100-iteration cap.
For the failed cases, the largest predicted relative cost improvement is about
**2.1 × 10⁻¹¹**, well below the unchanged **10⁻⁸** cost-stability limit. Both sides
and all spacings were retained; none was selected because it looked favorable.

## What this establishes

The component passes 26 software checks, including independent face enumeration,
known smooth and kink minima, physical bounds and a rank-deficient problem with
all 27 columns. The saved-matrix review charged exactly 18 solves and used no
native calculations, noise generation or nonlinear fitting. Its objectives were
independently recomputed from the saved matrices.

**These remain linear predictions.** The proposed parameter vectors have not
yet been evaluated in the physical calculation. They do not qualify the failed
fits, change the original 53-stretch findings or provide a calibration threshold.

The next gate is a finite evaluation of every saved proposal using the unchanged
physical model. A complete numerical method needs further qualification before
another optimization or calibration campaign.

[Verified report](README.md) · [All 18 proposals](results.csv) ·
[Frozen plan](PLAN.md) · [Previous physical diagnostic](../saved-timing-boundary/INTERPRETATION.md) ·
[Next analyses](../NEXT_STEPS.md).
