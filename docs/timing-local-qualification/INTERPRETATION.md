# Local timing checks pass the mathematical controls

All 36 known-answer fits and eight direct controls pass. All nine groups
agree across their four declared starting points. The run takes 27.5 seconds,
uses 1,046 analytical evaluations and 927 bounded linear operations, and makes
no native integration calls or reads of aircraft observations.

The four-fit simulator trial had failed final cost stability when its checks
used distant cell midpoints. A separate curved-minimum control reproduces a
false failure. Simply using the nearest point also fails sharp-corner software
tests, so that candidate was rejected before this study. This version samples
both sides using cell midpoints restricted to the existing ±10-microsecond
window. Every dispatch cell and nuisance direction remains included.

Cost, stationarity and position-change thresholds are unchanged. These tests
qualify mathematical behavior; they do not establish that the flight-data
simulator will pass or supply statistical confidence. The next gate is a new,
separately frozen four-fit simulator regression from the original starts.
The broader matrix and calibration remain blocked until that regression passes.

The original 53-stretch comparison is unchanged. Earlier failures and closed
allowances remain preserved.

[Every result](results.csv) · [Starting-point comparisons](pairs.csv) ·
[Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
