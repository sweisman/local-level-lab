# Calibration audit of the geographic controls

**All 24 fits reconstruct the known tracks, but they do not accurately recover every
calibration parameter.** Z gyro offset is the main weak direction. This saved-result
audit adds no fits or navigation predictions and leaves the original controls frozen.
See the [prediction and convergence results](README.md).

| True model | Construction | True Z offset (°/hour) | Fitted Z offset range (°/hour) | Fits at offset bound | Smallest fit condition number |
|---|---|---:|---:|---:|---:|
| sphere_rotating | nominal | 0.250 | 0.895538–0.896787 | 0/4 | 1.19e+07 |
| sphere_rotating | variable | 0.990 | 1.000000–1.000000 | 4/4 | 9.75e+06 |
| sphere_still | nominal | 0.250 | 0.787992–0.788063 | 0/4 | 1.25e+07 |
| sphere_still | variable | 0.990 | 1.000000–1.000000 | 4/4 | 1.01e+07 |
| flat_still | nominal | 0.250 | 0.701167–0.704241 | 0/4 | 1.25e+07 |
| flat_still | variable | 0.990 | 1.000000–1.000000 | 4/4 | 1e+07 |

The interior controls inject +0.25°/hour Z offset. Their fitted offsets differ by up
to **0.646787°/hour**, despite track errors below
6 micrometres. The near-boundary controls inject +0.99°/hour; **12/24 fits** reach
the permitted +1°/hour limit. Values are known software injections and allowances,
not manufacturer performance or measurements of NASA calibration.

The six-parameter tangents have condition numbers around ten million. At the saved
reference points, five of six fixtures have numerical rank five under the declared
relative 10⁻⁷ cutoff; one has rank six. All singular values remain nonzero. This is a
cutoff-dependent conditioning diagnostic, not proof of an exact algebraic degeneracy.

All 12 verified-solver fits preserve their weakest right singular vector. Each is
dominated by Z gyro offset, whose absolute normalized component is at least
0.999997. A much smaller change in gyro gain accompanies it. These vectors
use parameter-bound units; they are not physical correlations or uncertainty intervals.
The original solver's saved records do not include these vectors, so none are invented.

## Implication

Numerical convergence and accurate predictions are insufficient to establish unique
calibration. In these short, straight equatorial tracks, offset is weakly constrained;
small finite-interval integration errors can move its best-fitting value substantially.
Both solvers return closely agreeing predictions and offsets. This is not evidence
that the NASA instrument drifts by this amount, nor does it identify the cause of its
Z-axis boundaries. The controls use known continuous increments and a midpoint
navigation approximation, rather than reproducing all instrument coning/sculling details.

The next useful control is a predefined integration-resolution and gyro-offset/gain
study: hold the analytic trajectory, receiver epochs and physical calibration fixed,
reduce the increment interval, and compare offset recovery and objective valleys.
Also test longer, more informative geometry and independently fitted initialization.
Preserve this 24-fit result; use a new source/configuration identity and finite allowance
for further numerical controls. Observed gain–bias profiles remain a separate budget.

Reproduce this metadata-only audit:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-geographic-controls-20261011/audit_calibration.py
```
