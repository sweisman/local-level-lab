# What explains the remaining numerical failures?

All **11 unfinished primary fits across all six unresolved stretches** place every receiver epoch within **one microsecond of an IMU packet boundary**. This is reconstructed from saved receiver times, nominal packet counts and fitted offsets, without reading original recordings.

The timing parameter is the largest scaled projected-gradient component in **11/11** cases. All other gradient components are below the existing threshold in **11/11**. Seven primaries already pass the full gradient test; all seven fail a fresh correction that **increases** the objective. The other four fail the timing-gradient check before that correction is attempted.

Holding time offset fixed removes at least **99.98%** of the apparent improvement in each saved linearized correction. These are local linear systems; that reduction does not prove the remaining full-model optimum.

The independent cusp controls show why this matters: a true minimum can fail the original gate because a smooth correction crosses a derivative discontinuity and worsens the fit. The observed screen therefore identifies a common timing-boundary issue worth resolving before further optimizer changes or larger iteration budgets. It does not establish that every archival endpoint is optimal, and none of the six failures is relabeled.

The next diagnostic should check one-sided timing behavior together with nuisance reoptimization. Any revised stopping rule must reject genuinely unfinished smooth fits, respect the same physical bounds, and reproduce objective and predicted-track agreement. A tightly bounded timing profile can then test the archival minimum. This audit authorizes no new observed fits.

[Full audit and known-answer controls](README.md) · [All 22 endpoints](endpoints.csv).
