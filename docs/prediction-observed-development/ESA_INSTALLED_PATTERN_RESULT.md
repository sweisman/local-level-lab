# How much could a fixed antenna response change the comparison?

On ESA development flight 187, a fixed antenna response would need to
change by **at least 5.94 mm per degree between some sampled directions**
to explain the full saved carrier score gap by itself under the tested
motion allowance. A slope of **2.90 mm per degree** would be needed to use
up the earlier example allowance for the ground-covered part of the
score. This gives a scale for evaluating a measured antenna calibration
when one is available. [Frozen plan](ESA_INSTALLED_PATTERN_PLAN.md)

| Motion used | Minimum slope for the full gap | Minimum slope for the example ground-covered allowance |
| --- | ---: | ---: |
| Logged relative gyro rotation | 5.96 mm/° | 2.91 mm/° |
| Logged rotation plus one nominal background-field rate | 5.94 mm/° | 2.90 mm/° |

The calculation used 240 half-second intervals and 2,496 range terms.
The median satellite direction changed by 0.0035° per interval in
Earth-fixed coordinates. The median aircraft rotation from the logged
gyro increments was 0.139°. The bound allows the two angular changes to
add in the least favorable direction and accounts for the satellite mean
removed by the original score. It applies for any fixed initial antenna
pose. The slope is a necessary size under these assumptions. A pattern
with that slope might still fail to produce the needed signs and timing.
[Original error budget](ESA_NKAR_ERROR_BUDGET_RESULT.md) ·
[Ideal phase wind-up](ESA_PHASE_WINDUP_RESULT.md)

The aircraft files still leave the installed antenna unidentified. This
result neither measures the actual antenna response nor bounds changing
reflections, tracking errors or other errors shared by the three
receivers. Qualified confirmation still needs independently supported
aircraft error limits. [Antenna inventory](ESA_AIRCRAFT_ANTENNA_INVENTORY.md)

One task completed all 242 charged operations. Twelve tests passed.
There were zero new model fits, source downloads or reserved-flight reads.
SHA-256 `31c76af074d5877037241ace422e3ee32cef75247ab6dc7a5755dc88f20a8a26`.
[Numerical result](esa-installed-pattern-result.json) ·
[Frozen execution evidence](esa-installed-pattern-evidence/README.md)
