# The corrected arithmetic passes during fitting

**All 48 development fits pass the original numerical and physical checks.**
All 24 matched start pairs also agree, and all four previously saved input/error
bindings reproduce exactly. Both starts that failed in the earlier calibration
run now pass after eight evaluations each, under the unchanged limits.

The correction preserves tiny coordinate changes while summing the flight
trajectory and uses the feasible timing derivative at the lower clock bound.
The physical models, calibration bounds, generated measurements, error operator
and stopping thresholds are unchanged. The original failed fits keep their labels.

## What was tested

Two already exposed simulated noise families, including the earlier failure,
cover three generating physical candidates, two processing assumptions, two
input-error formats and two prescribed starts. Each candidate fits measurements
generated under that same candidate. This tests the calculation; these are not
48 new aircraft comparisons or votes for any Earth model.

| Check | Verified outcome |
|---|---:|
| Complete fits passing numerical and physical checks | 48/48 |
| Paired starts agreeing in cost and reconstructed training positions | 24/24 |
| Original saved input/error bindings reproduced exactly | 4/4 |
| Evaluations per fit | 7–12, within the unchanged 200 limit |
| Largest relative cost difference between starts | 2.45 × 10⁻¹⁴, below 10⁻⁸ |
| Largest per-axis RMS training-position difference | 0.0000000112 m, below 0.001 m |
| Largest later horizontal RMS error | 3.59 m |
| Largest later height RMS error | 2.06 m |

The last two rows compare forecasts with their known simulated physical truth.
They are not measured aircraft accuracy or calibrated confidence bounds.
Every fit still has five to seven calibration parameters at their permitted
limits. Numerical success does not establish unique calibration or an adequate
error model for actual instruments.

## Execution and evidence

The run finishes in **30.3 minutes**, using four one-thread workers after 93
source-bound software checks. It uses 382 optimizer evaluations. Actual work is
2,858,974 native operations and 919,272,978 conservative packet-query visits;
the larger frozen caps remain charged. No original or protected aircraft data
were read.

A separate eight-check reporting qualification corrects the saved-artifact
bundle and combines the shared numerical/physical status explicitly. This is
post-run reporting only. The original execution source freeze, fits, observations
and charges are preserved. Saved-data verification checks the physical errors,
compiled caches, construction/build journals, original bindings and paired starts
without generating measurements, fitting or propagating trajectories again.

## What follows

This clears the targeted arithmetic and optimizer qualification on the declared
development matrix. It does not restart the closed calibration campaign or supply
its missing uncertainty threshold. Fresh calibration and independent validation
need a separate finite release with this exact qualified method, new seed families
and their own accounting. The original 53-stretch findings are unchanged, and the
reserved ESA confirmation flights remain untouched.

[All fits](results.csv) · [Paired starts](start-pairs.csv) · [Frozen plan](PLAN.md) ·
[Previous saved-point diagnostic](../saved-point-coordinate-precision/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
