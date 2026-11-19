# Small calibration changes grow farther along the ESA forecast

The fixed-fit replay reproduced all 520 receiver-coordinate predictions and
all 400 earlier residual vectors exactly. It retained the derivatives for
all 27 fitted quantities using the original flight 187 inputs, frozen source
and compiler build. One of one replay tasks passed, with one native sweep,
zero new fits and no withheld receiver positions or reserved flights opened.

The three combinations least constrained by the earlier fit show larger
effects on the later path. The table scales each unit direction by 0.01 in
the normalized calibration coordinates and reports its **linearized** position
effect in metres.

| Direction, weakest first | Largest three contributions | Earlier RMS | Later RMS | Later / earlier |
|---|---|---:|---:|---:|
| 1 | Z, Y and X gyro offsets | 0.0095 m | 0.0356 m | 3.73× |
| 2 | Y gyro offset, Y gyro gain, Z accelerometer offset | 0.0046 m | 0.0402 m | 8.71× |
| 3 | Y and Z gyro offsets, timing offset | 0.0100 m | 0.0535 m | 5.33× |

To reproduce the table, compute the right singular vectors of the sealed
fit's whitened training Jacobian in descending singular-value order. Multiply
the replayed coordinate Jacobian by 0.01 times each of the last three vectors.
Convert latitude and longitude changes to north and east metres at the
nominal forecast coordinates and take the RMS three-axis displacement over
each period. The 0.01 scale is a reporting unit. Whether a finite step is
within the calibration bounds and whether it predicts the same change must
be checked separately.

This is a local sensitivity of one saved fit. The next check needs to bound
nonlinear prediction errors over feasible calibration changes and to compare
them against a defensible aircraft error model.

[Fixed replay plan](ESA_NATIVE_TANGENT_REPLAY_PLAN.md)

The closed study ID is `esa-native-tangent-replay-v1-20261118`.
Its manifest SHA-256 is
`3a294c22063ed997c22a031f7664b67edeb4aa4652b2af7b0c6e0dcb0303441a`.
The sealed `full-tangent.json` array has 1,560 rows and 27 columns and
SHA-256 `543a78e7f334a90612a86a28c83dce8492bda3ebc0d48cf5c3f00382b97ba1f3`.
