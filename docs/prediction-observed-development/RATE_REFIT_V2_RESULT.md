# Refitting the ESA rate alternatives does not fix prediction accuracy

All **six training-only fits converged** under the unchanged bounds and
stopping rule. Both original linear-point fits reproduced their saved fitted
parameters and forecasts exactly. The three rate interpretations were fitted
separately under each of the two original IMU error laws, using only the first
800 receiver positions. The 400 later positions were opened only after all six
forecasts sealed.

| Rate interpretation | Fits converged | Training horizontal error, RMS | Later horizontal error, RMS | Later height error, RMS | Preset accuracy screen |
|---|---:|---:|---:|---:|---|
| Original linear points | 2/2 | 39.96 m | 249.41 m | 4.35 m | Fail |
| Left sample hold | 2/2 | 39.56 m | 247.89 m | 4.41 m | Fail |
| Right sample hold | 2/2 | 37.69 m | 240.37 m | 4.55 m | Fail |

Values shown to two decimals agree for the *increment* and *point* error laws;
the [machine-readable result](rate-refit-v2-result.json) preserves all six
separate values, vertical errors, maxima, evaluation counts and stopping
records. The fits took eight or nine evaluations each. None ended at an active
calibration bound; the largest absolute normalized parameter was 0.489 on a
scale bounded by ±1. That removes boundary saturation as the immediate reason
for these six numerical outcomes, without establishing that the calibration
or observation model is correct. Every training and
later horizontal RMS exceeds the predeclared **10 m** screen. The screen is a
descriptive physical-accuracy rule, not a calibrated confidence interval.

The right-hold calculation has the smallest error in this one development
recording. **That does not identify the instrument's actual sampling rule:**
choosing from later receiver errors would use the withheld answers to select
the method. The three methods differ by less than 10 m in later horizontal RMS
after refitting, while all miss by more than 240 m. The large mismatch is
therefore not resolved by rate assignment alone. The present scientific
decision is **abstain**.

This was one previously selected ESA development interval, not six flights or
independent confirmation. It used three workers at one numerical thread each,
sealed 6/6 passing technical tasks in 5,935.76 seconds, and charged the frozen
ceilings of 4.2 million native calls and 270 billion packet/query visits.
Those are reserved upper bounds, not a count of operations actually needed.
No original source file or one of the seven reserved ESA confirmation groups
was opened during fitting.

The next development gate is to locate the error common to all three rate
conversions—initialization, calibration, force model, or receiver-error
assumptions—using saved residuals and separately qualified controls. Do not
open the seven reserved groups or promote an Earth-model comparison from these
failed accuracy screens.

[Frozen observed plan](RATE_REFIT_V2_PLAN.md) ·
[Generated software check](RATE_REFIT_V2_SMOKE_RESULT.md) ·
[Earlier fixed-point check](RATE_PROPAGATION_V2_RESULT.md) ·
[Comparison with the earlier accurate fit](RATE_REFIT_HISTORICAL_COMPARISON.md).

Completed observed-study manifest:
`fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba`.
Summary:
`47f01b56eda5710d0698f26a4727b12945abfcaa8f8fe3be50ff5a8df0fc03a7`.
