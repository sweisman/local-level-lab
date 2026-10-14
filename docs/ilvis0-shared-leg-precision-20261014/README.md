# Wider arithmetic at the same airborne endpoints

**6/6 fixed endpoints completed**, using 84
integration evaluations and **zero optimizer starts**. Findings remain
**30 globe preferences, zero flat and 23 unresolved**. No fitted result is promoted.

The diagnostic changes internal arithmetic from 53 to **64 mantissa bits**,
keeping the same physical equations, observations, bounds, nominal packet clock
and timestamp branch choices. Inputs and exported coordinates/derivatives remain
float64. The generated source and compiler/binary hashes are retained.
The [finite plan](PLAN.md) explains all fourteen evaluations per endpoint.

Eleven known-answer software controls passed before archived evaluations: exact
straight-disc motion and its analytic velocity derivative, every active derivative
under all three models and both processing cases, and finite-call controls.
Software controls are not empirical calibration or Earth-model campaigns.

## Identical saved parameters

Costs are the same declared whitened sum of squared receiver-coordinate errors.
Coordinate shift is the largest axis RMS difference between arithmetic choices.
The paired recorder keeps its own original complete stretch; it does not replace
the failed recording or share fitted calibration without evidence.

| Stretch ID prefix | Saved endpoint passed | Ordinary cost | Wider cost | Central coordinate shift (µm) | Ordinary / wider stationarity |
|---|---|---:|---:|---:|---:|
| 3df34ea3 | False | 27.217983 | 27.217984 | 1.051 | 7.13e-06 / 7.13e-06 |
| 233183f6 | True | 13.797301 | 13.797301 | 0.3367 | 1.24e-07 / 7.9e-08 |
| e6629f14 | False | 22663.441 | 22663.441 | 0.1555 | 9.92e-06 / 9.92e-06 |
| abe881b5 | True | 18951.192 | 18951.192 | 0.2208 | 4.08e-08 / 4.01e-08 |
| a953c8dd | False | 2.373852 | 2.373852 | 0.2279 | 8.24e-07 / 8.1e-07 |
| 31d7e501 | True | 0.97862129 | 0.97862133 | 0.2244 | 2.02e-09 / 2.14e-07 |

Small cost changes at identical parameters can matter to a numerical stopping
limit of 1e-8. They are not changes in the underlying observations or model identity.

## Same frozen correction under both arithmetic choices

The following uses the exact same parameter direction, at full size, for both
implementations. All five fractions appear in the downloadable CSV. Linear error
is the difference between the actual physical prediction change and that predicted
by the center's derivative, reported as the largest axis RMS. It includes nonlinear
curvature as well as numerical effects; it is not a direct instrument error.

| Stretch ID prefix | Ordinary / wider cost-change ratio | Ordinary / wider linear error (µm) | Full probe checks pass, ordinary / wider |
|---|---:|---:|---|
| 3df34ea3 | 1.057 / 0.009469 | 0.1144 / 0.1226 | False / True |
| 233183f6 | 0.397 / 0.01999 | 0.05611 / 0.0005767 | True / True |
| e6629f14 | 0.02961 / 0.01097 | 0.07352 / 0.0005855 | False / False |
| abe881b5 | 0.0163 / 0.0003015 | 0.04591 / 0.0005991 | True / True |
| a953c8dd | 4.014 / 0.06153 | 0.1082 / 0.001909 | False / True |
| 31d7e501 | 5.474 / 0.1049 | 0.05488 / 0.0005861 | False / True |

The same full direction passes **2/6** ordinary-arithmetic probes
and **5/6** wider-arithmetic probes. These are fixed diagnostics,
not counts of recovered fits. A wider kernel's center and correction must be
qualified together before a subsequent numerical trial.

## Correction calculated from the wider derivative

This table uses one bounded affine correction calculated at the wider center,
then evaluated with wider arithmetic. It is separate from the frozen-direction
comparison above. Ratios at most one pass the unchanged numerical limits.

| Stretch ID prefix | Cost change / limit | Fresh stationarity / limit | Largest axis RMS change (mm) | These probe checks pass |
|---|---:|---:|---:|---|
| 3df34ea3 | 0.008616 | 0.0004084 | 0.0263 | True |
| 233183f6 | 0.02452 | 3.301e-05 | 0.001177 | True |
| e6629f14 | 0.01114 | 5.538e-07 | 3.766 | False |
| abe881b5 | 4.887e-05 | 1.433e-07 | 0.0121 | True |
| a953c8dd | 0.03541 | 0.0002015 | 0.001802 | True |
| 31d7e501 | 0.04293 | 6.36e-05 | 0.0009989 | True |

**5/6** pass these probes. An affine correction is not an
observed-data optimization, and a diagnostic pass does not establish a global
minimum or replace a primary/repeat comparison. The original failure labels remain.

## Interpretation and next qualification

The comparison isolates numerical representation while holding the declared model
fixed. Improvement in local prediction agreement supports further precision testing;
lack of improvement leaves nonlinear curvature or weak calibration combinations
as unresolved explanations. A general change needs known-answer solver checks and
a separately frozen paired-recording trial, retaining all models, both processing
assumptions, repeated starts and the original tolerances. No extra bias freedom,
automatic retries or corpus-wide rerun follows from this diagnostic.

## Reproduce the report

```sh
~/venv/bin/python docs/ilvis0-shared-leg-precision-20261014/build_report.py
```

[Individual precision probes](probes.csv) retain all fractions and both directions.
Rendering performs no integration or optimization. Completed native work is frozen.
