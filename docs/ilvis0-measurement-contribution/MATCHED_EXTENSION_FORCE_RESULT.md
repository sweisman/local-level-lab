# The accelerometer-only check does not reproduce the full forecast ranking

On the added IMU21 flight, every candidate met the necessary force
inequalities after the gain was set from earlier data. On the added IMU8
flight, only the specified-field disc met every later inequality. The
inequality asks whether a prediction requires too little force. It places
no penalty on a prediction that requires too much.

| Recorder | Candidate | Training gain | Later misses / checks | Largest later gap |
|---|---|---:|---:|---:|
| IMU8 | Specified-field globe | 0.288% | 26 / 990 | 0.01080 m/s² |
| IMU8 | Zero-field globe | 0.353% | 27 / 990 | 0.01087 m/s² |
| IMU8 | Specified-field disc | 0.000% | 0 / 990 | 0 |
| IMU8 | Zero-field disc | 0.236% | 26 / 990 | 0.01115 m/s² |
| IMU21 | All four candidates | 0.267–0.362% | 0 / 900 each | 0 |

The counts include both clocks and all three receiver tracks. Adjacent
windows overlap. They cannot be counted as independent trials. The
gyro-inclusive forecasts give lower 3D error for globe on both same-field
comparisons on both flights. That comparison uses angular measurements
and the full prediction path. The accelerometer calculation uses a scalar
inequality and cannot settle the shape question by itself. Its IMU8 gaps
all clear under one [shared GPS perturbation](MATCHED_EXTENSION_FORCE_WITNESS_RESULT.md).
The full-IMU forecast order survives that adjustment. A calibrated
GPS and continuous-motion allowance remains open.

Both tasks passed their software checks in 74 seconds. They evaluated
24,072 force envelopes on 1,003 supported windows and excluded 120
windows at the recording edges or the training cut. The study used no new
model fits or forecast propagations. For fuller calibration work, a
[separate packet calculation](GYRO_FREE_PACKET_CALIBRATION.md) passes
known-answer checks for applying gains and offsets before averaging.

[Frozen design](MATCHED_EXTENSION_FORCE_PLAN.md) ·
[Verified summary](matched-extension-force-result.json) ·
[Reproduction bundle](matched-extension-force-evidence/bundle.zip)
