# How stable are the chosen GPS windows?

The existing GPS-only rule chose a local window at 2,194 of 2,365 target
times. This check keeps those same receiver records, target times and rule. It
asks whether the choice is **guaranteed to stay the same** if every reported
speed, course and climb-rate value lies within a stated error range. No IMU
data or Earth-model fits entered the check.

| Assumed per-reading error | Chosen window guaranteed unchanged | Rejection guaranteed unchanged | Choice not guaranteed |
|---|---:|---:|---:|
| Zero | 2,194 | 171 | 0 |
| Speed and climb rate ±0.05 m/s; course ±0.05° | 1,580 | 111 | 674 |
| Speed and climb rate ±0.10 m/s; course ±0.05° | 1,111 | 73 | 1,181 |

“Not guaranteed” does **not** mean a window actually changes. It means the
declared range contains values for which this bound cannot certify the original
choice. The calculation permits each reading to move independently within its
range, which is conservative for shared or slowly varying errors. Its course
bound also abstains near a 180° unwrapping ambiguity.

The tested ranges are illustrative; they are **not measured accuracy limits**
for these GPS receivers. This check holds timestamps and the recorded position
path fixed. It does not propagate position error into the force calculation or
account for shared GPS errors. The earlier [paired-receiver
comparison](../ilvis0-receiver-window-pairs/README.md) measures repeatability
between receivers, not absolute error. A calibrated receiver error law and a
matched IMU-channel comparison remain open.

The [per-target table](window-stability.csv) includes every original target,
scenario, three candidate-window classifications and whether the original
decision is certified. The [receipt](window-stability-receipt.json) binds the
table to the sealed receiver-only study, this calculation's source and the
[fixed question](WINDOW_STABILITY_PLAN.md). The zero-error replay recovered
all 2,194 chosen windows and 171 original rejections exactly. All six focused
software checks passed. No scientific model decision follows from this check.
