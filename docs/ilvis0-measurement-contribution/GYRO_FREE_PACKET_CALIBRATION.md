# Applying one calibration before averaging accelerometer packets

An accelerometer reports a force vector averaged over each packet. To use
that reading without a gyroscope, apply the same three gains and three
offsets to every packet of a recording. Take the length of each calibrated
vector, then average the lengths by packet duration. Turning can cancel
vectors that are averaged first, even when their lengths stay constant.

The [packet calculation](../../analysis/lll/ilvis0_packet_force_calibration.py)
computes the time-weighted means and derivatives for overlapping packet
windows in a single pass per calibration. The derivatives are with respect
to physical gains and offsets. Generated controls use exact known forces
and changes in direction, irregular packet durations, independent direct
sums and finite differences.

This is the measured force side of a gyro-free fit. It exposes no assumed
attitude or gyro rotation. To qualify a recorded-data comparison, the
predicted force must use the same time support. Its covariance must account
for GPS differentiation and overlapping windows. The difference between
packet averages and continuous force also needs an explicit error allowance.

The [training and later force controls](GYRO_FREE_CALIBRATION_CONTROLS_RESULT.md)
now pass all eight generated cases under both clocks, including a later
force change with the earlier calibration held fixed. A separate rotating
force check verifies the packet-averaging bound for a supplied motion limit.

A [check of adjacent aircraft packets](PACKET_FORCE_CHANGE_RESULT.md)
shows which small motion limits are inconsistent with the recorded signal
under stated error allowances. Establishing an upper limit requires
additional evidence about motion and sensor error.
