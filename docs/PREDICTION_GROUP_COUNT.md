# How many independent flights would test prediction coverage?

The seven reserved ESA flight groups are intended as separate-flight checks
of a method fixed in advance. They are **not enough on their own** to establish
that a future prediction range covers 95% of flights.

Each group now has one [20-minute slice with verified IMU timing](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md).
The seven groups still await a qualified forecast and decision rule.

The repository's [exact order-statistic planner](../analysis/lll/prediction_calibration.py)
requires **59 independent calibration groups** before the largest observed
group error can serve as a 95%-coverage upper tolerance limit with 95%
confidence. With seven groups, it returns no finite limit. Similarly, even
if all seven reserved groups passed a fixed range, the exact one-sided 95%
upper bound on its flight-group failure rate would be **34.8%**. These numbers
assume exchangeable, independent groups; shared aircraft, instruments or
processing could reduce the effective count further.

This does not make the seven groups useless. They can challenge a frozen
method and show whether it transfers to other equipment and flights. A
stronger coverage statement requires many more independent groups, or a
separately justified physical or statistical error model tested against the
observations. Several 120-second positions within one flight count as one
group for this purpose.

The calculation is reproducible with `order_statistic_plan(7,
coverage=.95, confidence=.95)`, `order_statistic_plan(59, coverage=.95,
confidence=.95)` and `tail_upper(7, 0, family_size=1, confidence=.95)`.

## Possible source of more groups

The saved [NASA file ledger](ilvis0-highspeed-segments-20261008/files.csv)
contains 232 retained recordings with **130 distinct five-digit date-like
filename tokens**, counted from the `filename` field with the pattern
`_5[0-8][0-9]{3}_`. This is only a receiver/source
metadata count. It does not mean 130 independent flights have suitable level
stretches: some recordings overlap, some share hardware, and the original
700 km/h selection yielded just 27 conservative groups among 53 stretches.

A separate, prospectively fixed receiver-and-motion inventory tested whether
a distance-and-duration rule admits additional flight groups. Its versioned
**inventory-only** policy required:
at least 10 continuous minutes, at least 50 km of sampled receiver path,
and every supported ground-speed sample at least 180 km/h, with the original
alignment, level-motion, gap, buffer and raw-completeness rules. The 50 km
distance is slightly longer than the original minimum of 4 minutes at
700 km/h (46.7 km). A lower speed floor permits longer survey legs to be
counted without treating taxi movement as flight. This policy has passed
synthetic selection and strict streaming checks. The [completed 232-file
inventory](ilvis0-distance-inventory/RESULT.md) found **five** candidate
stretches, totaling **55.0 minutes**, on **four** conservative recorded-date
groups. All five sources and all four dates already appear in the original
53-stretch study, so this rule added **zero** new groups. It made no model
fits and did not change the original selection. The scan does not solve the
independent-flight count needed for a distribution-free coverage claim.
The [saved rejection audit](ilvis0-distance-inventory/REJECTION_AUDIT.md)
shows that fused-navigation alignment and course-rate screens flagged many
samples. The flags overlap and do not identify a unique reason for each
missing candidate. A separately fixed [receiver/raw inventory](ilvis0-receiver-raw-inventory/RESULT.md)
then scanned the same 232 files without those fused-motion exclusions. It
found **29 technical candidates** totaling **314.6 minutes** on **26
recorded dates**. Sixteen of those dates do not appear among the original
53 selected stretches (comparison of `date_group` in its candidate table
with the first ten characters of `start_utc` in the original selection table).
They are possible new source groups, not verified level flights or independent
replications. Receiver geometry, aircraft motion and model information must
be checked under a separate fixed rule before any fit or coverage claim.

A subsequent [receiver-motion profile](ilvis0-receiver-motion-profile/RESULT.md)
closed all 29 candidate tasks without fitting an Earth model. Twelve tracks
on ten dates fall below both earlier **reference** values for 95th-percentile
climb and course-change rate; six of those dates are absent from the original
selected-stretch cohort. These are descriptive comparisons, not a level-flight
gate. Receiver course does not establish aircraft heading or roll, and the
full nuisance-information test has not been run for these candidates.

The [alignment-only ablation](ilvis0-alignment-ablation/COMPARISON.md) then
removed the fused alignment-status veto while retaining every other strict
screen. It recovered **exactly the original five longer intervals**, with no
new date. Alignment status by itself does not explain the lack of extra
strict candidates. The broader receiver/raw candidates remain unqualified.

The [conditional model-geometry check](ilvis0-receiver-geometry-profile/INTERPRETATION.md)
profiles all 29 paths against local bias, drift, gain and mounting directions.
Under its widest unbounded tangent, the median retained rate contrast is
around one part in a billion for every model pair. This is a rate-only
diagnostic under an independently known aircraft-motion assumption; it does
not overturn the original bounded full-IMU fits. It does prevent treating
these new route shapes alone as guaranteed model-discrimination evidence.
