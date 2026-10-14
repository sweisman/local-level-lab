# Prediction precision at the shared-recorder endpoints

**All six endpoints completed**, using 60 native integration evaluations
and **zero optimizer starts**. The published finding remains **30 globe preferences,
zero flat and 23 unresolved**. These checks do not promote an old fit or change its
acceptance rules.

The [finite plan](PLAN.md) tests the three failed model/processing endpoints and
their three successful-recorder counterparts. Each retains its original complete
stretch, observations, clock, covariance and calibration bounds. The
[saved recorder-pair audit](../ilvis0-shared-leg-diagnosis-20261014/README.md)
compares measurements on common UTC seconds and explains the exact stopping failures.

## Central prediction checks

Both integration implementations are evaluated at identical saved parameters.
The value implementation predicts the track; the tangent implementation predicts
the track and its derivatives. Neither uses fused Group-1 navigation as an observation.
Two identical evaluations of each implementation test deterministic repeatability.

| Stretch ID prefix | Original endpoint passed | Reproduced tangent cost | Central value/tangent relative cost difference | Largest coordinate difference (µm) | Largest repeated-coordinate difference (µm) |
|---|---|---:|---:|---:|---:|
| 3df34ea3 | False | 27.218 | 2.11e-14 | 5.457e-06 | 0 |
| 233183f6 | True | 13.7973 | 0 | 0 | 0 |
| e6629f14 | False | 22663.4 | 0 | 0 | 0 |
| abe881b5 | True | 18951.2 | 0 | 0 | 0 |
| a953c8dd | False | 2.37385 | 1.12e-15 | 3.638e-06 | 0 |
| 31d7e501 | True | 0.978621 | 1.9e-12 | 0.0001473 | 0 |

The largest repeat difference is **0 µm**. The largest difference
between value and tangent coordinates, including all noncentral probes, is
**0.0002474 µm**. These comparisons test the two implementations at
the specified points; they do not independently verify every derivative or
establish a precision floor for nearby parameters.

## Full, half and quarter local corrections

The correction is the same bounded affine least-squares direction used by the
stability test. Each fraction receives a fresh prediction and derivative evaluation.
Ratios at most one pass the original cost and gradient limits; position RMS must
remain at most 1 mm per axis, and no epoch may move more than 1 cm.

| Stretch ID prefix | Correction fraction | Fresh cost change / limit | Fresh gradient / limit | Largest axis RMS change (mm) | These probe checks pass |
|---|---:|---:|---:|---:|---|
| 3df34ea3 | 1.00 | 1.057 | 0.0002476 | 0.02625 | False |
| 3df34ea3 | 0.50 | 0.813 | 0.03559 | 0.0131 | True |
| 3df34ea3 | 0.25 | 0.3291 | 0.05352 | 0.006494 | True |
| 233183f6 | 1.00 | 0.397 | 0.000102 | 0.00133 | True |
| 233183f6 | 0.50 | 0.272 | 0.0006119 | 0.000664 | True |
| 233183f6 | 0.25 | 0.3108 | 0.0009398 | 0.000327 | True |
| e6629f14 | 1.00 | 0.02961 | 6.578e-06 | 3.766 | False |
| e6629f14 | 0.50 | 0.06987 | 0.04961 | 1.883 | False |
| e6629f14 | 0.25 | 0.04505 | 0.07442 | 0.9415 | True |
| abe881b5 | 1.00 | 0.0163 | 3.437e-06 | 0.01217 | True |
| abe881b5 | 0.50 | 0.008037 | 0.0002041 | 0.006082 | True |
| abe881b5 | 0.25 | 0.0001339 | 0.0003062 | 0.003038 | True |
| a953c8dd | 1.00 | 4.014 | 0.0004536 | 0.001773 | False |
| a953c8dd | 0.50 | 1.257 | 0.00395 | 0.0008865 | False |
| a953c8dd | 0.25 | 1.686 | 0.006054 | 0.0004441 | False |
| 31d7e501 | 1.00 | 5.474 | 0.0003909 | 0.0009594 | False |
| 31d7e501 | 0.50 | 0.6494 | 0.0003422 | 0.0004807 | True |
| 31d7e501 | 0.25 | 0.3992 | 0.0002733 | 0.0002445 | True |

Half or quarter steps passing here are **diagnostic observations, not accepted fits**.
Shrinking a correction arbitrarily can hide remaining work; a revised stopping
procedure needs independent known-answer qualification and a separately frozen
observed comparison. The CSV retains affine predicted costs alongside actual
costs, rather than assuming a locally linear prediction is exact.

## What these checks establish

- Every central objective reproduced its saved endpoint within the frozen
  reproduction limit. Both implementations produced identical repeated coordinates.
- At the October 2009 IMU8 failure, the half correction passes all measured probe
  checks, while the full correction misses the relative-cost limit narrowly.
- At the September 2015 DMS disc failure, the quarter correction moves vertical
  predictions by about 0.94 mm RMS and passes these checks; the full correction
  moves them by about 3.77 mm RMS.
- At the October 2015 DMS background-field failure, full, half and quarter
  corrections all miss the relative-cost check. The progression is not monotonic.
- The October 2015 loaner endpoint was complete under the original solver. It
  fails this newer full-correction check, although its half and quarter probes
  pass. Original completion and a fresh check under a later policy are distinct.

The two implementations disagree far too little at these evaluated points to
explain the failed cost probes. Exact repeated evaluations also rule out random
variation at the same parameters in this diagnostic. They **do not rule out
deterministic roundoff as parameters change**, inaccurate derivatives or nonlinear
curvature. The saved local systems are poorly conditioned, with weak directions
dominated by gravity correction and correlated calibration parameters.

The useful next test is derivative and accumulation precision in those directions,
before qualifying a revised numerical strategy. More attempts or accepting whichever
step fraction passes would not establish that the original fit is fully resolved.

The next numerical investigation should distinguish integration roundoff,
derivative accuracy and nonlinear curvature in the weak gravity/calibration
directions. The September disc endpoint also needs its vertical stability failure
addressed. This study supplies no new nuisance freedom or statistical significance.

## Reproduce the report

```sh
~/venv/bin/python docs/ilvis0-shared-leg-probes-20261014/build_report.py
```

[Individual probes](probes.csv) preserve objective values, physical movements and
checks. Report rendering performs no integration or optimization. Completed native
work is frozen and cannot resume; interrupted identities receive no retries.
