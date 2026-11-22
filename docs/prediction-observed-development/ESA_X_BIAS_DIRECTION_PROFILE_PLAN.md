# Locate the X-axis calibration sensitivity of the force directions

Use the original earlier 400 reports, the two fixed force kernels,
the existing matched-field prediction angle grids and the recorded
gyro. Hold all sensor corrections except X accelerometer bias at
zero. Reuse one gyro integration. Each weighted force vector changes
linearly with this one bias because the gyro rotations are fixed.

Evaluate 401 equally spaced biases from −0.10 to +0.10 m/s².
At each bias compare globe and disc after allowing each its own
retained fraction. Use the earlier continuous bound between retained
fractions. Also bound the change between bias samples. A vector
of the form (a-xc) has direction derivative of magnitude
(lVert a	imes cVert/lVert a-xcVert^2). Use the smallest
vector norm on the full bias interval to bound each pair angle
and each RMS error. Certify a preference only where the error
gap survives both bounds. Verify the previously saved bias endpoints
and the nominal angles.

If a positive edge to the contiguous common globe region lies
inside the bias box, take that exact bias to the two ground stops.
Calculate the best force consistency there with the other
accelerometer terms free and separate site force levels. Report
the ground spread at that boundary, while leaving its acceptable
size and transfer to flight calibration open.

Freeze one numerical thread, one integration of at most 155,868
packets, 401 bias values and at most one ground linear program.
No new Earth-model fit or reserved flight group. The result
covers this axis alone and keeps receiver and gyro assumptions fixed.

[Matched-field angles](ESA_MATCHED_GYRO_DIRECTION_RESULT.md) ·
[Ground bias check](ESA_GROUND_X_BIAS_RESULT.md)
