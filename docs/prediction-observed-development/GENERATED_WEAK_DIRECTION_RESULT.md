# A shared weak calibration direction in the generated fits

A [saved-fit audit](GENERATED_WEAK_DIRECTION_PLAN.md) examined the two closed
generated fits without refitting or opening aircraft data. Each fit has 26
calibration parameters and a complete numerical solution, but its fitted
physical path fails the original accuracy screen.

| Generated error law | Local Jacobian rank | Weakest / strongest singular value | Reciprocal weakest singular value |
|---|---:|---:|---:|
| Increment | 26/26 | 0.0000210 | 2.99 normalized parameter units |
| Point | 26/26 | 0.0000211 | 3.00 normalized parameter units |

The weakest direction mixes **gyro X and Y gain, gravity adjustment, and
vertical accelerometer bias**. Its axis is nearly identical in the two fits:
the sign-independent direction similarity is **0.99999**. The reciprocal
singular value describes local sensitivity under the assumed whitening; it
is not a measured instrument uncertainty or a valid nonlinear confidence
interval. Several fitted parameters reach their allowed bounds.

Full algebraic rank therefore does not imply that training positions pin down
every calibration combination tightly enough for an accurate later path.
The same route was used under both error laws, so their similar weak axis is
not independent replication. This audit does **not** prove that this one
direction caused either path miss. The next generated control should vary
that combined calibration direction through the full nonlinear forward model
and measure its effect on the training and later path, with all original
accuracy failures preserved. No Earth-model decision follows.

[Verified machine report](generated-weak-direction-result.json) ·
[Original bound-aware pilot](BOUND_AWARE_GENERATED_PILOT_V2_RESULT.md)
