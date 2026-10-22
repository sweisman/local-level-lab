# Derivative bounds for calibrated packets

An **inertial measurement unit (IMU)** contains gyroscopes and accelerometers.
The prediction-bound calculation needs to know how an IMU increment changes
as calibration varies. A new exact-arithmetic component encloses that change
through third order, for the stated bias/gain region and calibration path.

The component also handles the partial-packet arithmetic used when a query
falls inside a packet. It rejects clock ranges that cross a packet boundary;
it cannot silently treat them as one smooth interval.

Nine focused checks pass, including comparison with an independent power-series
calculation at 27 parameter/path points. Denominator failures, invalid paths
and unsupported clock ranges are rejected.

This supplies calibrated-increment derivatives, not complete trajectory
derivatives or verified clock-partition coverage. No original measurements
were read, altered or fitted. It changes no instrument scale or calibration bound.

[Mathematics](MATHEMATICS.md) · [Source](../../analysis/lll/ilvis0_calibration_path.py) ·
[Tests](../../analysis/tests/test_ilvis0_calibration_path.py) · [Next native work](NEXT_PLAN.md)
