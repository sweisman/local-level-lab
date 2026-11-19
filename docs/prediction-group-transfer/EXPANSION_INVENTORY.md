# Unused NASA prediction-development groups

The existing 53 selected stretches form 27 conservative recording groups.
Three groups were used in the original prediction pilot and four in the first
transfer check. A metadata-only rule now selects one representative from each
of the **20 remaining groups**. It chooses the longest eligible stretch in
each group, with segment ID breaking a duration tie. No model result, gyro
value or residual enters the choice.

All 20 representatives are **IMU21** recordings; 18 are southern and two are
northern. Their durations range from **4.07 to 9.33 minutes** (median
**8.73 minutes**), with a median recorded ground speed of **825 km/h**. This
inventory expands group coverage within the selected NASA archive, but it does
not add IMU8 hardware diversity or supply long flight windows. The groups are
conservative split units, not proven independent flights.

The [20-row inventory](remaining-groups.csv) lists exact identities, source
hashes, route summaries and group IDs. The
[selection plan](EXPANSION_INVENTORY_PLAN.md) fixes the rule, and the
[receipt](remaining-groups-receipt.json) hashes the four source tables, selector
and output. Three focused tests pass; recomputation matches the saved receipt
and CSV hash. This preparation made **zero fits**, read no original IMU file
and did not open any reserved ESA group.

A later prediction study needs its own frozen error law, full model and
processing grid, earlier/later split, physical adequacy rule, group-level
scoring and finite recoverable allowance. The earlier four-group transfer
result remains [separate](RESULT.md). This inventory does not establish
prediction coverage or a scientific detection.
