# Compare the saved alternatives under shared receiver-error assumptions

This is the next saved-data diagnostic. It uses the completed one-second native
predictions and performs no new integration, optimization or original-file read.
It asks how temporal error assumptions change the distinguishability of those
fixed trajectories. It is not an estimate of the actual receiver covariance.

## Fixed cases and error laws

Retain the original calibration and selected north-extreme pair for each of the
six model/processing cases. Preserve their source/manifest/artifact hashes and
the verified original epoch values. Use the 289 earlier predictions at 2 through
290 seconds; compare with their original five-epoch subset. Exclude the later
438-second prediction from every noise-scaled calculation.

All six cases share the frozen physical-coordinate scales
`[6371000, 2692500.945549996, 1]`. Verify equality before preparation; do not
give candidates different error weights. These are the existing fixed local
coordinate conversions, not a new measurement of geometry.

Reuse the two previously declared receiver sensitivities:

| Component | North / east / height standard deviation |
|---|---|
| Independent floor | 0.3 / 0.3 / 0.7 m |
| Correlated component | 1 / 1 / 3 m |
| Shared offset | 1 / 1 / 3 m |
| Linear drift | 1 / 1 / 3 m at 438 seconds |

Use either a 10- or 300-second exponential correlation time. Drift remains
anchored at zero seconds with span 438 seconds for both training subsets.
These settings come from the earlier retrospective prediction proposal;
they are sensitivity assumptions, not newly inferred device specifications.

## Calculation and limits

For each case and law, compute the three pairwise distances between the saved
training trajectories after whitening by the common receiver covariance.
Report raw per-axis RMS differences alongside those noise-scaled distances.
Use the existing structured whitening implementation; check the new interface
against independent simple cases and a small dense reference.

The covariance belongs to one hypothetical observation stream. Do not multiply
it by two as though two independent measurements were being subtracted: the
trajectories are competing deterministic means. No actual added observations,
noise draws, p-values, significance thresholds or model decisions are produced.

Freeze six copied saved-prediction inputs and a common recipe. Allow **12 task
starts**, one per case/law, one worker and one numerical thread, with a
120-second cooperative total allowance. Native calls, packet visits, bound
evaluations and optimizer starts are zero. No retries or budget expansion.
Preserve missing, failed and unsupported results rather than dropping cases.

This is a receiver-component diagnostic. Accumulated IMU noise, covariance
estimation, complete nonlinear calibration uncertainty and whole-period coverage
remain separate requirements. A changed distance does not qualify the aircraft
error law or authorize observed prediction fits. Preserve the 53-stretch
baseline and all earlier failed numerical studies.

[Next connection](NEXT_PLAN.md) · [Completed cadence diagnostic](README.md) ·
[Shared error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md).
