# Recovering the remaining airborne comparisons

**Complete: 30 globe preferences, zero flat preferences and 23 unresolved stretches.**
The run finished all 159 new fits. It preserved the original measurements, selected
intervals, three physical candidates, calibration bounds, receiver weights and clock.

The original study found twelve complete globe preferences. The preceding
[24-fit qualification](../ilvis0-position-stability-trial-20261013/RESULTS.md)
recovered three more. This wider run brings the total recovered from the original
unfinished population to eighteen, including those three, rather than counting
the subset twice. All thirty resolved stretches favor the specified background-field
globe over the zero-field globe under both processing assumptions. The comparison
does not identify the field's cause or distinguish solar from sidereal rate.

## Numerical results

| Calculation | Passed / completed |
|---|---:|
| New primary recovery fits | 84 / 115 |
| New repeated-start fits | 27 / 38 |
| Fresh controls | 6 / 6 |
| Total new fits | 117 / 159 |

The run used **22,355 native integration sweeps** within its fixed 95,718-sweep
ceiling, with no retries or execution errors. The entire run did not qualify every
comparison: twenty-one stretches have at least one unfinished primary fit, and two
more have complete primaries but failed scheduled repeat checks. Those 23 remain
unresolved, rather than becoming flat preferences or receiving automatic retries.

The thirty resolved stretches total **234.9 minutes**: 29 IMU21 stretches and one
IMU8 stretch, drawn from thirty recording hashes across nineteen dates. Overlapping
recorders and shared installations prevent treating them as thirty independent flights.
See [current findings](../ilvis0-position-stability-trial-20261013/FINDINGS.md),
[all 53 stretches](../ilvis0-position-stability-trial-20261013/STRETCHES.md), and
[costs and stopping reasons](../ilvis0-position-stability-trial-20261013/ANALYTICS.md).

The [frozen plan](PLAN.md) applies the same method to the remaining original
unfinished calculations. It reuses 18 qualified results and permits **159 new
starts**: 115 primary fits, 38 repeated starts and six fresh controls. All physical
models, observations and calibration bounds remain unchanged.
The [stretch inventory](../ilvis0-position-recovery-preparation-20261013/stretches.csv)
records source filenames, hashes, UTC intervals, duration, speed and recorded IMU type;
the [task ledger](../ilvis0-position-recovery-preparation-20261013/tasks.csv) identifies
new and reused calculations.

The worker uses two numerical threads, records each attempt before execution and
allows no retries. Its ceiling is 95,718 native sweeps, estimated at 51–76 hours
if difficult fits consume their full allowances. Actual time may be shorter.

Every recovered stretch passed six primary model fits, its scheduled repeat and
the fresh controls. Globe/flat is reported first;
the background-field comparison follows only for consistent globe preferences.
These are numerical model preferences, not calibrated statistical detections.

## Reproducibility and next investigation

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_position_recovery_worker.py --package-only
```

The completed study is frozen. Packaging verifies and copies existing evidence
without fitting; its unused allowance is closed. The next investigation compares
overlapping flight legs whose recorders have different numerical completion outcomes,
starting with the three marked pairs in the
[matched-recorder inventory](../ilvis0-position-stability-trial-20261013/shared-leg-pairs.csv).
Use saved fits and common UTC intervals before preparing a separate finite numerical study.
