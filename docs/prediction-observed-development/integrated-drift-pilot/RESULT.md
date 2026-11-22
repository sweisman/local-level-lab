# Generated changing-drift pilot result

All **8/8** frozen software tasks completed without a technical error.
The fixed candidate contained every withheld coordinate inside its
nominal 95% marginal range in **3/8** generated histories. This is
a development stress result, not a calibrated 95% coverage rate.

A separate, conservative simultaneous 95% Gaussian union bound for
the 180 later coordinates has a 3.635-standard-deviation threshold.
**6/8** histories remain inside it; two exceed it. Even if the
law were correct and the eight generated seeds independent, a
two-or-more-exceedance count has probability bounded by 5.7%.
This check was added after the frozen pilot, and does not establish
a formal rejection or an aircraft coverage claim.

| Seed | Physical vibration | Largest standardized later error | Weakest axis: fraction inside nominal range | Whole period inside? |
|---|---|---:|---:|---|
| 2026111600 | yes | 2.71 | 8.3% | no |
| 2026111601 | no | 3.11 | 26.7% | no |
| 2026111602 | yes | 5.88 | 3.3% | no |
| 2026111603 | no | 4.49 | 35.0% | no |
| 2026111604 | yes | 2.76 | 21.7% | no |
| 2026111605 | no | 1.80 | 100.0% | yes |
| 2026111606 | yes | 1.64 | 100.0% | yes |
| 2026111607 | no | 1.83 | 100.0% | yes |

The generator supplied the true starting state and the candidate used
its **declared** white-force, changing-force and receiver-error scales.
The generated gyro-bias walk is not fully represented by this law;
physical vibration and channel coupling are also present. The
observed misses leave the fixed candidate unqualified for this
generated mixture. Nominal marginal intervals did not promise
95% simultaneous containment, and eight draws do not calibrate
a coverage rate. They do not identify which omitted component caused
each miss. No parameter was changed after looking at these eight draws.

A revised candidate needs a separate frozen seed cohort and must
retain the original failed result. The seven reserved ESA flight
groups were not opened. No Earth-model decision is made.

[Frozen plan](PLAN.md) · [machine report](RESULT.json) ·
[error-law roadmap](../OBSERVED_ERROR_PLAN.md).
