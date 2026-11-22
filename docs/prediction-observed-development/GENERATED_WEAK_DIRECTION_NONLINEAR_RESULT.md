# Nonlinear check: the small weak-axis move is not the large path miss

The [revised frozen study](GENERATED_WEAK_DIRECTION_NONLINEAR_V2_PLAN.md)
closed **2/2 technical tasks** after a passing short native preflight. It
reconstructed the exact saved generated IMU inputs, reproduced each original
forecast and ran four native forward calculations per error law. There was no
new fit or aircraft-data read.

The perturbation direction came from each saved training Jacobian. Its sign
was chosen using only the calibration box, then its size was fixed at 0.05,
0.10 and 0.20 normalized parameter units before scoring. The 0.20 result is:

| Generated IMU error law | Training path change | Later path change | Later nonlinear-minus-tangent difference | Original later path miss |
|---|---:|---:|---:|---:|
| Increment | 0.40 m | 0.70 m | 0.013 m | 108.60 m |
| Point | 0.40 m | 0.69 m | 0.013 m | 91.31 m |

All values are horizontal RMS. The two generated laws use the same route.
The selected weak direction is real in the local training SVD, but these
small, box-feasible moves do **not** reproduce the much larger path errors.
The native path and its local tangent agree closely over this tested range.
This does not rule out larger calibration moves, other directions, a different
fit basin, or an inadequate error law. Both original fits still fail their
physical accuracy screen, and the aircraft error law remains unqualified.

The first [frozen preflight](GENERATED_WEAK_DIRECTION_NONLINEAR_PLAN.md)
ended terminal before any native work because its adapter supplied a study
bookkeeping field to the route generator. Its failure and zero native charges
remain preserved; the revised version used a fresh source freeze and study ID.

[Verified machine report](generated-weak-nonlinear-result.json) ·
[Saved weak-direction audit](GENERATED_WEAK_DIRECTION_RESULT.md)
