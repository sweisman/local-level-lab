# Matched horizontal-only multi-start comparison

This completed sensitivity study tested whether a fixed timing search resolves
the earlier IMU21 repeat disagreement. **It did not:** 37 of 38 individual fits
passed, but only two of six selected primary/repeat comparisons agreed within
the required limits. Both fresh controls passed. The original 53-stretch
full-position findings remain unchanged.

The four-minute IMU21 stretch is fitted under all three models and both processing
cases. Each receives the same three timing starts and two independent seed
families. Two fresh IMU8 controls check continuity with the earlier results.
Eight exact reconstruction checks precede fitting.

The study used **38 starts /2,376 native evaluations in 6.59 hours**, within its
frozen 7,646-evaluation, four-thread, 20-hour allowance, with no retries.
The numerical stopping and independent-repeat requirements are unchanged.
Every attempt is preserved, including failed stops and local optima. A lower-cost
unfinished fit cannot be discarded in favor of a higher-cost successful one.

The [results](README.md), [attempt table](DETAILS.md) and
[calibration CSV](attempts.csv) preserve every attempt. The
[interpretation](INTERPRETATION.md) explains the four repeat failures and why a
wider timing search is not the next priority. Large unscored height errors remain an
explicit limitation: horizontal scoring does not establish adequate full-flight
reconstruction, gyro-only evidence or calibrated statistical significance.

[Frozen method and limits](PLAN.md) ·
[Known-answer software qualification](../ilvis0-multistart-controls-v3-20261019/README.md) ·
[Earlier horizontal-only findings](../ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md).
