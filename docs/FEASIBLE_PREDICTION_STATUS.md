# Prediction calibration stopped after an execution interruption

**The campaign saved 1,813 numerically passing simulated fits before its execution
session ended.** Four charged starts were interrupted. These are missing results,
not numerical rejections of completed fits.

| Outcome | Fit attempts |
|---|---:|
| Saved and numerically passing | 1,813 |
| Interrupted, without a completed result | 4 |
| Not started; allowance closed unused | 5,359 |
| Originally planned | 7,176 |

The run lasted 38.7 hours. All 253 frozen sources, inputs, charge journals and
the numerical environment still match. The [independent audit](prediction-calibration-feasible/INTERPRETATION.md)
confirms that every completed forecast passes both numerical and position-error
checks. All 7,176 planned attempts are retained in the [result table](prediction-calibration-feasible/results.csv).
All 42,064 publication artifact hashes verify, and the archived report replays
identically. Recoverable working copies are compacted; no measurements were
refitted or replaced.

## Why validation cannot follow this run

Calibration requires every planned simulated family to supply every required
setting. The interruption left both prescribed starts unavailable for one
setting. Retrying those starts or dropping the family would change the frozen
procedure. The incomplete campaign therefore supplies no uncertainty threshold,
and the separate 181-family validation has not started.

These are generated measurements with known answers, not additional aircraft
observations or Earth-model votes. The original 53 aircraft preferences remain
unchanged. Actual flight-level uncertainty and statistical significance remain
unestablished.

## What remains

The audit, publication and archived replay are complete, including 40 partial
files from the interrupted starts. The [read-only recovery checker](execution-recovery/README.md)
passes its 61-check software suite. A [host-service control](execution-host-service/README.md)
also passes normal submitter-exit survival, with eight heartbeats and zero model
work. The [execution-recovery plan](CALIBRATION_RECOVERY_PLAN.md) now calls for
a [fresh finite release](HOST_PREDICTION_STATUS.md), now prepared after 154
software checks and independent freeze verification. Any replacement study needs a new
finite freeze; the closed campaign and its unused allowance stay closed.

The corrected optimizer's [48-case qualification](timing-matrix-combined/README.md)
remains valid: all cases, 24 starting-point pairs and four original-input replays
pass. The calibration interruption does not change those completed controls.

[Original finite plan](FEASIBLE_CALIBRATION_RELEASE_PLAN.md) ·
[Preparation snapshot](feasible-calibration-preparation/README.md) ·
[Next analyses](NEXT_STEPS.md) · [Original aircraft findings](CURRENT_STATUS.md).
