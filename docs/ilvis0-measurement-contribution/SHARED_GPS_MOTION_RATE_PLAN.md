# Check gyro-free motion bounds under the same GPS correction

Use the [archived IMU8 GPS correction](SHARED_FORCE_WITNESS_RESULT.md)
that cleared the force-only magnitude check and left the saved complete
IMU rankings unchanged. Apply that exact correction to the onboard GPS
path in the [saved motion-rate comparison](RECORDED_MOTION_RATE_RESULT.md).
Keep the 608 windows, their timestamps, selected accelerometer packets,
both clocks, both time periods and all four physical candidates. Match the
correction to the original GPS stamps and use its original conversion
into coordinate changes. Preserve the uncorrected and carrier-phase
brackets and the original IMU21 zero-correction control.

Use the same fourth-degree paths, half-count direction allowance and zero
calibration setting as the original rate comparison. Recalculate necessary
sampled angular rates and verify a nominal orientation history for each of
the 16 corrected cases. Apply the original one-probe, 4,096-twist policy
to the midpoint of each corrected bracket. Preserve inconclusive probes.
Report the change in each bound and whether the four model brackets still
overlap within each clock and time period. Keep every model and failure
in the report.

Freeze source, environment, original packet selection and GPS correction
before evaluation. Use at most 608 path approximations, 4,864 force-point
evaluations and 16 grid probes, each limited to four million cells. Use one
numerical thread and a 120-second cooperative limit. Use zero navigation
fits, receiver position solutions, original-file reads, gyroscope
observations or reserved-flight reads. This sensitivity check addresses
sampled motion on one recording. An independently justified aircraft rate
limit and a joint receiver-error law remain separate requirements.
