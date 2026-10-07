# Saved-recording covariance refits

This bounded research comparison uses six saved analysis cases from the
observed Chicago–Los Angeles trajectory: three simulated recordings, one per model
truth, each fitted with two wind candidates. These are not independent flights.
It creates no new flights. Each case
is fitted under four fixed assumptions about how long GPS and IMU measurement
errors persist: 0/0, 15/15, 300/300 and 15/300 seconds, respectively.

Each case/assumption receives one unconstrained fit and three fits with the Earth-model
coefficients fixed. All four share the exact same full measurement covariance and
the existing physical wind model's 2 m/s allowance. Covariance includes shared
measurement paths; it is not updated to favor the result of any model fit.

The authorization is 96 primary fits, with at most one predefined nesting repair
per recording/assumption: 120 optimizer starts maximum, including interruptions.
Each optimizer has a 200-evaluation limit. Completed failures and nonconverged fits
are preserved. An interrupted repair is never repeated. An append-only, synced
journal counts starts; individually hashed checkpoints preserve completed work.
Source, inputs and numerical environment are frozen. A process lock prevents two
workers from running the same scope.

Resume only this scope, with the original frozen sources and environment:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=analysis:analysis/tests /home/sweisman/venv/bin/python analysis/tests/refit_covariance_measurement.py --detach
```

`status.json` records progress; `worker.log` records durable output. `plan.json`
freezes the scope and dependencies; `attempts.jsonl` preserves optimizer starts and
completions. Each case contains its working covariance, fit metadata, arrays and
final summary. `review.json` is written after all 24 comparisons finish.
`analysis/tests/assess_covariance_refits.py` independently checks recorded objective
arithmetic, residuals, covariance/support identity, convergence, nesting and bounds.
It reports local pairwise information without applying an eligibility threshold.
A durable hashed fit checkpoint remains completed even if an interruption happened
before its journal completion event; the independent audit reports that gap separately.

These are development diagnostics. The assumed error scales and correlations have
not been characterized on hardware. Raw objective differences do not establish
statistical significance, power, calibrated decisions or a three-model winner.
No bootstrap, empirical calibration, validation or production promotion is included.

## Result

The scope is complete: **96 fits, all converged; 24 model comparisons, all nested
correctly; no repairs, interruptions or failed fits.** No parameter reached a bound
or came within 1% of its allowed range. The optimizer work took 28.9 minutes in total;
the primary comparison finished in about 30.5 minutes from launch on one numerical
thread. No worker remains active. The unused repair allowance does not authorize more fits.

Residual variation after the free fits ranged from 4.47 to 9.88 degrees per hour.
The model used to generate each recording had the lowest fixed-model objective
under every assumption and both wind candidates. This is a consistency check on
three shared development recordings, not 24 independent successes or a calibrated
decision. Longer-lived errors substantially reduce the strength of the differences.

A local calculation asks how much of each model difference remains after allowing
all fitted nuisance directions to imitate it. It uses the fitted state and provisional
covariance, without nuisance penalties or an acceptance threshold:

| Comparison | Fraction of contrast information retained | Local information range |
|---|---:|---:|
| Rotating versus stationary globe | 23.5–52.4% | 2.84–270.84 |
| Rotating globe versus disc | 4.0–14.3% | 0.40–33.97 |
| Stationary globe versus disc | 31.7–64.3% | 1.20–117.14 |

Rotating-globe versus disc remains the weak comparison. There is more information
about the other pairs, including a useful shape comparison, but its statistical
strength depends on error persistence that has not yet been measured on hardware.
These local values are not the frozen design gate and do not establish a usable
three-model protocol.

The independent audit reproduced every full-equation residual exactly. Direct
correlated-matrix objective arithmetic agreed to less than 6.3×10⁻¹⁶ relative error;
an independent full-equation Jacobian direction agreed to 2.4×10⁻¹⁰. Support,
covariance, input/source/environment hashes, bounds and journal identities were
checked. Seventeen focused solver, covariance, recovery and projection checks pass.
A completed-scope resume verified all checkpoints and skipped all 24 comparisons
without starting any optimizer. Including the audit, the run took about 31.3 minutes.

The next scientific need is to characterize actual instrument and GPS error
persistence and verify the acceleration correction against measured motion. That
evidence can define a defensible covariance domain for the research candidate.
A three-way conclusion still needs adequate geometry for the weakest contrast,
followed by fresh calibration and independent validation. Separate pairwise and
shape evidence remain useful development paths. No additional campaign is authorized
by this completed scope.
