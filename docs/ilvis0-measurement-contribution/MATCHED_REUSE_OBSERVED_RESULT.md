# The revised solver reproduced both recorded controls

Both previously converged fits passed the same stopping checks with exact
agreement in training cost and every later forecast position. No later GPS
positions entered the fits or the comparison. The two controls used 20
training evaluations and two forecast calls in 6.9 minutes.

| Recorder and model | Original training calls | Revised training calls | Rejections eligible for reuse |
|---|---:|---:|---:|
| IMU8, specified-field globe | 9 | 9 | 0 |
| IMU21, zero-field globe | 11 | 11 | 0 |

The option preserved the result and used the same work on these aircraft
controls. The 15% saving was measured on generated cases with repeated
proposals. The earlier unresolved IMU8 zero-field disc fit remains in the
record. This numerical qualification supplies no new aircraft accuracy or
scientific result.

[Frozen plan](MATCHED_REUSE_OBSERVED_PLAN.md) ·
[Verified comparisons](matched-reuse-observed-result.json) ·
[Reproduction bundle](matched-reuse-observed-evidence/bundle.zip)
