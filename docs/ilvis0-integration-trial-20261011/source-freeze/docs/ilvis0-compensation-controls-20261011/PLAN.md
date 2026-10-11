# Original-rate coning/sculling controls

Keep every 200 Hz synthetic increment and receiver observation from the interior
geographic controls. Use the same six nuisance bounds, original solver and zero
start for each model. Do not change the old value/tangent kernels or completed work.

The separately compiled candidate assumes ordinary body angular-rate and specific-
force integrals. Recover local linear variation from the calibrated average rates
at three adjacent packet centers, including unequal intervals and one-sided ends.
The raw input arrays remain unchanged. This is an explicit forward-model hypothesis,
not repair or interpolation of measured science data.

For interval h, elapsed part t, mean rate w and force F, and slopes α and β, the
partial means are w + α(t−h)/2 and F + β(t−h)/2. A coning correction adds
t³(w×α)/12 to the partial angular increment. The rotating-force correction adds
t³[w×(w×F)/24 + (w×β−α×F)/12] to the midpoint-frame velocity increment.
Here w and F in the correction are the partial means. These are truncated series,
not a universal manufacturer algorithm. Earth/transport, gravity and geographic
updates retain the existing midpoint equations. Disabled mode delegates exactly
to the old tangent kernel. Baseline, linear-only, coning-only, sculling-only and
combined modes isolate the proposed changes and partial-packet timing assumptions.

Independently validate the series against continuous attitude/force differential
equations for constant, single-axis and changing-axis motion. Check calibration
and latency derivatives, partial intervals, variable spacing, zero motion and
explicit rejection of applying corrections to already-compensated input.

The report allows 15 known-calibration native predictions: five modes for each of
three true models. Then charge exactly nine new fits: coning, sculling and combined,
each under rotating globe, still globe and stationary disc. Each fit has at most
200 native sweeps including fresh diagnostics and two final predictions. Thus the
report ceiling is 1,815 sweeps, with no retries and two numerical threads. Reuse
the three saved original/interior/zero-start fits; never refit them. Unit tests have
separate small software calls. Zero observed-data starts and no NASA input files.

Preserve every result, including failures, estimated calibration, limits, objective,
prediction errors, weak directions and convergence. Prediction/convergence checks
use the original 2 mm tolerance and objective-reference allowance. Calibration
recovery is reported separately against known truth; do not infer it from low cost.
Hash source, inputs, native build, environment and plan before the first fit; charge
starts durably. Interrupted starts remain charged without retry. Package saved data
without running fits. No solver or correction is promoted to archival analysis here.

Processing context: [Brouk and DeMars, 2021](https://ntrs.nasa.gov/citations/14626669150663)
discuss coning/sculling and their uncertainty propagation. The series above is
derived and tested independently in this repository; that paper does not establish
NASA Group-4 increment conventions or justify applying these corrections to them.
