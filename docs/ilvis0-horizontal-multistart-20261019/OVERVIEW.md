# Matched horizontal-only multi-start comparison

This separate sensitivity study asks whether the earlier IMU21 repeat disagreement
can be resolved by searching a fixed list of initial timing offsets. The original
53-stretch full-position findings remain unchanged.

The four-minute IMU21 stretch is fitted under all three models and both processing
cases. Each receives the same three timing starts and two independent seed
families. Two fresh IMU8 controls check continuity with the earlier results.
Eight exact reconstruction checks precede fitting.

The fixed allowance is **38 starts /7,646 native evaluations**, on four threads,
with a 20-hour ceiling and no retries. Prior timings suggest roughly six hours.
The numerical stopping and independent-repeat requirements are unchanged.
Every attempt is preserved, including failed stops and local optima. A lower-cost
unfinished fit cannot be discarded in favor of a higher-cost successful one.

The worker publishes its saved results automatically; a separate metadata-only
watcher generates the attempt table and calibration CSV afterward. Those completed
reports will be published separately. Large unscored height errors remain an
explicit limitation: horizontal scoring does not establish adequate full-flight
reconstruction, gyro-only evidence or calibrated statistical significance.

[Frozen method and limits](PLAN.md) ·
[Known-answer software qualification](../ilvis0-multistart-controls-v3-20261019/README.md) ·
[Earlier horizontal-only findings](../ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md).
