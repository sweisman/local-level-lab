# The trial calculation preserved both recorded fits

Both IMU8 cases reproduced their complete solver records exactly. The
specified-field globe control also reproduced every saved forecast
coordinate. The zero-field disc retained its failed stopping check at the
original 30-evaluation allowance.

| Candidate | Original full tangent calls | Full tangent calls with value trials | Value-only calls | Stopping check |
|---|---:|---:|---:|---|
| Specified-field globe, including forecast | 10 | 10 | 6 | Passed |
| Zero-field disc | 30 | 12 | 27 | Failed as before |

The two tasks finished in 10.4 minutes and charged all 55 native calls.
The speed benefit depends on how frequently the solver rejects proposals.
The globe control accepted every proposal and saved no tangent calls. The
disc case avoided 18. This verifies substitution on one recorded IMU8
history under the [frozen settings](MATCHED_TRIAL_OBSERVED_PLAN.md).
A broader recorded comparison and aircraft uncertainty qualification
remain open. The original four-model preflight remains incomplete.

The [sealed evidence](../ilvis0-matched-trial-observed-runtime/README.md)
contains the original and new records, the one forecast and the complete
accounting. The comparison used no later receiver positions.
