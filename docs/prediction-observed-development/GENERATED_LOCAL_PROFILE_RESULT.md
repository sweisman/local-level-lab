# Local joint-profile check on a generated flight

The [corrected one-case study](GENERATED_LOCAL_PROFILE_V2_PLAN.md) completed
its single frozen task. All three candidates replayed their sealed forecasts
exactly, and each was profiled over the same later generated receiver path
with all 26 calibration columns retained. The correction in each coordinate
was limited to ±0.1 of its normalized calibration range, intersected with
the original physical bounds. There were **no new model-fit starts**, no
observed or protected flight reads, and no scientific decision.

| Candidate | Linear profiled future cost | Nuisance rank | Local bounds reached | Native minus tangent RMS, N/E/U |
|---|---:|---:|---:|---:|
| Globe, specified field (generated truth) | 3.05 | 26/26 | 14 | 0.79 / 1.30 / 0.13 m |
| Globe, zero field | 61.97 | 26/26 | 15 | 0.61 / 0.89 / 0.73 m |
| Flat disc, zero field | 7.19 | 26/26 | 16 | 0.15 / 0.41 / 0.33 m |

The local linear cost is lowest for the generated truth, but even this smaller
correction leaves decimetre-to-metre nonlinear path differences. Those are
larger than the precision needed for a convincing aircraft model comparison.
The cost table is therefore **a numerical development diagnostic**, not a
model preference or test statistic. Future receiver positions selected the
correction; it is not a held-out prediction. One generated case does not
establish power, coverage or an error law for actual flights.

The first radius-0.1 preparation was never launched after an accounting
mistake was found in its source. The corrected version subtracts exactly 119
sealed later positions from new-generation charges. It passed 19 source
tests, 5 recovery tests, the complete native replay and its final receipt
check. Its completion and per-candidate artifacts are in
`data/generated-local-profile-v2-20261118`. The earlier full-range replay
failures remain as recorded in the [saved audit](GENERATED_JOINT_PROFILE_SAVED_RESULT.md).

Next: keep the local profile separate from the primary earlier-only
prediction method. Any candidate decision from future-data profiling would
need an independently chosen trust region, full nonlinear verification,
real-aircraft error-law qualification and its own null calibration.
