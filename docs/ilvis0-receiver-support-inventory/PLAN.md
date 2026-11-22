# Receiver-only window inventory

## Fixed question and input

On the 53 previously selected high-speed stretches, which local windows meet
a declared GNSS-only motion and completeness screen? Reuse the sealed
[receiver-gap inventory](../ilvis0-receiver-gap-inventory/README.md) and its 52
strictly decoded enhanced-position tables. Retain the remaining decoder
failure as an abstention. Do not read IMU increments, Group 1 fused navigation,
Earth-model residuals or held-out prediction scores.

## Window policy

For each uninterrupted receiver block, examine targets every **10 seconds**
from 15 seconds after its first position to 15 seconds before its last. At
each target, try symmetric half-windows of **5, 10 and 15 seconds** and choose
the longest that passes all of these fixed conditions:

| Receiver-only property | Limit |
|---|---:|
| Adjacent GPS-position gap | at most 1.5 seconds |
| Positions per window | at least 5 |
| Ground speed | 190–350 m/s |
| Course span within window | at most 1.5° |
| Speed span within window | at most 10 m/s |
| Vertical-rate span within window | at most 1 m/s |

The lower speed is slightly below the original 700 km/h stretch cutoff to
allow receiver rounding at individual epochs. The course limit corresponds to
the original 0.05°/s motion screen across the longest 30-second window. The
other limits are conservative **development support rules**, not measured
sensor-error bounds or a scientific acceptance threshold. This inventory will
not tune them after seeing which targets pass. A changed rule requires a new
version and fresh study.

Use the primary receiver's GPS timestamps and north/east/up velocity fields
for screening. Preserve every target, each candidate window and each rejection
reason. Do not interpolate or join gaps, and do not count blocks or overlapping
recorders as independent flights.

## Finite execution and interpretation

Freeze the study definition, source/environment hashes and all 52 receiver
tables before execution. One task may start once, using one worker and one
thread, zero native model calls and zero optimizer calls, with a five-minute
cooperative wall ceiling. Seal the earlier decoder abstention in the output.

This is preparation for a later matched acceleration/gyroscope comparison.
It does not calibrate receiver error, quantify support-selection uncertainty,
fit a physical model or change the existing 53-stretch result.
