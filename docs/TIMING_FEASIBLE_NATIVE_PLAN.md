# Native regression of feasible linear initialization

The revised optimizer passes 36 known-answer fits, eight direct probes and nine
starting-point comparisons. This separate regression now tests its complete
generated IMU-to-prediction pipeline with the native integrator.

## Fixed cases

Use both original prescribed starts for these exposed development cases:

| Seed | Input | Upstream-removal parameter | Earlier role |
|---|---|---|---|
| 281474977010692 | Point | Fitted | Earlier successful control |
| 281474977010693 | Point | Fitted | Earlier numerical failure/regression |
| 281474977210667 | Increment | Absent | Latest calibration failure |

All three cases use the specified-field globe generating candidate. Each fits
its own generating truth; these are not Earth-model votes. Preserve the old
fit labels. Require exact replay of all six original input, training-observation
and error-operator bindings. Keep 27 nuisance columns for the first two cases
and all 26 for the last. No future prediction error is used to select a start.

## Fresh finite allowance

Freeze six starts, at most 200 fitting evaluations and 620 linear operations
per fit, zero retries, four workers with one numerical thread each, and a
5,400-second cooperative ceiling. The unchanged shared formulas give maximum
charges of **359,724 native calls** and **2,259,076,518 packet visits**. These
are prepayment limits, not promises to consume the allowance. Estimated runtime
is about 15–20 minutes; the earlier four-fit regression took 10.7 minutes.

The shared worker and auditor receive an explicit six-reference count; their
historical default remains four. Bind the new analytical gate's exact hashes,
all seven numerical source files and the environment. Record source changes
against the latest closed calibration: the qualified linear solver and the
necessary reference-inventory worker/auditor changes only. Physical/noise source
changes must fail preparation. Qualify the interface and source bindings before
launch. Preserve every failure and interrupted charge; never reset a budget.

Require six complete numerical/physical passes, three agreeing start pairs,
exact original-input replays and independently checked timing-cell evidence.
Publish every outcome, verify hashes and archived replay, then compact working
copies through the shared store. No original aircraft or protected ESA data.

A complete native-model matrix remains a subsequent gate before a separately
budgeted calibration. Neither this trial nor analytical success reopens an old
campaign or supplies an uncertainty threshold.

[Analytical qualification](timing-feasible-optimizer-qualification/INTERPRETATION.md) ·
[Current roadmap](ANALYSIS_ROADMAP.md).
