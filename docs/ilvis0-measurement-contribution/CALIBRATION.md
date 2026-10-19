# Calibration can hide an acceleration-only difference

The gyro-removal diagnostic compares acceleration magnitudes without supplying
an assumed aircraft orientation. A new known-answer control shows why that
comparison also needs a calibration-identifiability check.

On the constructed constant-height eastbound leg, **one constant accelerometer
gain change of 0.066–0.307% erases every wrong-model magnitude difference**.
The same gain applies to all three axes and all 21 epochs, including two changing
instrument orientations. No per-epoch adjustment, bias or gravity change is needed.
All nine truth/candidate combinations pass this mathematical control.

This is a limitation of the scalar diagnostic, not a finding about the airborne
measurements. It does not change the completed 53-stretch full-position results.

## Why it happens

For constant required force magnitude, let the generated measurement have
magnitude \(m\) and a candidate require magnitude \(q\). With the calibration
convention \(f_{\rm corrected}=f_{\rm measured}/(1+g)\), setting

\[
g=m/q-1
\]

makes their magnitudes agree. Rotating the body axes does not change this result.
On a changing trajectory, one constant gain need not match every epoch; the
part of the difference that varies over time must be assessed separately.

| Generated truth | Comparison candidate | Constant gain change | Largest uncorrected gap (m/s²) |
|---|---|---:|---:|
| Specified-field globe | Zero-field globe | −0.2406% | 0.0235885 |
| Specified-field globe | Stationary disc | −0.3065% | 0.0300683 |
| Zero-field globe | Specified-field globe | +0.2412% | 0.0235885 |
| Zero-field globe | Stationary disc | −0.0661% | 0.00647984 |
| Stationary disc | Specified-field globe | +0.3074% | 0.0300683 |
| Stationary disc | Zero-field globe | +0.0661% | 0.00647984 |

Every corrected gap is below 4 × 10⁻¹⁵ m/s². The existing exploratory model permits
axis gain changes up to ±15%; that is an assumed search bound, not a measured
device error. These controls neither estimate actual gains nor justify changing
the bound. Same-model controls recover zero gain within numerical rounding.

The [nine known-answer tests](../../analysis/tests/test_ilvis0_magnitude_calibration.py)
use the independent Cartesian reference motion and the receiver-force adapter.
The [complete numerical table](magnitude-calibration-controls.csv) retains all
nine combinations. No archive file, fused navigation, observed fit or native
integration is used. These are ordinary software controls, separate from the
completed frozen error-budget matrix.

## Consequence for the next comparison

The subsequent [72-case local calibration matrix](../ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md)
is complete. Straight-leg differences disappear in its projection; changing
motion retains local differences, but all wrong-model changing-motion linear
corrections exceed the permitted bounds. A bounded nonlinear check is needed
before those differences can be interpreted.

An acceleration-only model ranking with calibration fixed cannot establish
which part of the original separation requires gyroscopes. Before recorded-data
use, test whether differences remain after the allowed calibration freedoms:

1. Start with changing-speed, changing-heading and changing-latitude controls.
   Compare complete time histories with one shared calibration per constructed
   recording, rather than matching each epoch separately.
2. Include all three acceleration gains, all three offsets and gravity. A surviving
   difference after only isotropic gain removal is insufficient. Check nonlinear
   ambiguity as well as local rank; retain unidentifiable nuisance directions.
3. Specify the quantization, noise, time association and averaging model equally
   for every candidate. Select support using receiver motion and completeness,
   before examining observed model residuals.
4. If the remaining information is inadequate, report that limitation and retain
   the full-vector analysis. Do not tighten bounds or choose favorable windows
   to create a separation.

[Channel controls](CHANNEL_CONTROLS.md) · [Measurement contributions](README.md).
