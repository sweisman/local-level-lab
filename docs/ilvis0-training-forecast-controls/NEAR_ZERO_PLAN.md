# A stopping rule for already near-zero residuals

The 24-fit control found accurate forecasts but only three passing stopping
checks. The saved tangent audit explains why changing to a minimum-norm
correction alone is insufficient. A separate near-zero rule is now a software
proposal; it has not qualified the complete prediction pipeline.

The shared check is `lll.ilvis0_near_zero.verify`. It checks two fresh
calculations at exactly the same feasible calibration point. Both computed
sums of squared normalized residuals must be at most 10⁻⁸, with projected
stationarity at most 10⁻⁴. Position-repeat differences must satisfy the existing
1 mm axis RMS and 1 cm maximum limits. All nuisance columns remain present.

The numerical rationale is specific: a sum of squares is nonnegative. A value
already within a fixed absolute tolerance of zero cannot meaningfully improve
its computed objective by more than that tolerance, even if calibration terms
are not separately identifiable. The test avoids moving arbitrarily along
those weak directions solely to decide whether to stop.

This does not certify integration roundoff, parameter uncertainty, observational
adequacy or scientific significance. It does not apply a near-zero assumption
to nonzero optima. Their ordinary stopping checks remain necessary. Historical
failures are unchanged.

The composed training solver passes 74 focused checks, including malformed
inputs, repeat safeguards, exact call accounting and 40 nonzero or boundary
known-optimum cases. The two fresh calls stay inside the original evaluation
ceiling. A separately frozen [24-case comparison](../ilvis0-near-zero-forecast-controls/PLAN.md)
passes all 24 complete-pipeline cases on the same generated tracks, using 2,976
native calls. Aircraft fitting still requires its own frozen inputs, source,
environment and finite limits; unit tests alone would not qualify it.

[Complete control results](README.md) · [Saved diagnosis](../ilvis0-forecast-tangent-audit/README.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md)
