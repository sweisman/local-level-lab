# Longer ESA development intervals

**2 eligible runs, totaling 393.4 minutes.**
They come from one development recording of the ESA/DTU airborne survey.
Selection uses receiver timing, speed, distance, quality and valid covariance,
before examining gyro values or fitting any physical candidate.

| Run | Duration | Distance | Mean ground speed | Mean latitude | Mean course | Height range |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 298.6 min | 1498.7 km | 301.1 km/h | 65.17° N | 90.8° | 356–3526 m |
| 2 | 94.8 min | 422.1 km | 267.3 km/h | 65.04° N | 49.1° | 402–1914 m |

Mean course summarizes a changing path; these are not straight, level legs.
The runs contain turns and climbs. Version 2 removes the quiet-motion veto
because the intended method explicitly propagates aircraft motion from IMU
samples. It does not certify unseen motion between receiver samples.
The zero-eligible version-1 inventory remains unchanged.

Every admitted run lasts at least 20 minutes, travels at least 60 km and
stays at or above 180 km/h at the receiver epochs. Reported quality, timing,
complete IMU support and positive-definite full covariance are required.
Receiver accuracy and the instrument sampling interpretation remain assumptions.

The one-pass inventory checks all 64,080 receiver epochs; 16,873 fail one or more epoch rules.
Saved-only verification reconciles every epoch and interval, all CSV outputs
and the original-source hash, plus the charged work journal. It reads no
original recording and performs no model fit.

No ESA shape or background-field result follows from this inventory.
The next study needs its own preselected interval, training/prediction split,
working errors, physical accuracy checks and finite fit allowance.
Seven separate confirmation groups remain protected.

[Full interval CSV](artifacts/receiver-inventory-187-v2/eligible.csv) · [Excluded-epoch reasons](artifacts/receiver-inventory-187-v2/epoch-reasons.csv.gz) · [Frozen plan](PLAN.md) · [Selection rules](../external-imu-data/ESA_SELECTION_V2.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
