# Paired vibration control

## Question

Did the four vibration-case range failures in the completed 256-history
generated check reflect the generator's physical vibration, or a chance
difference between its independent noise seeds?

## Fixed diagnostic

Use 16 fresh seeds, `2026112100`–`2026112115`. For each seed, generate
both vibration settings with **identical gyro, accelerometer and receiver
error draws**. Retain the fixed 15-state error law, 120-second histories,
100 Hz IMU, 61 earlier receiver reports and 60 withheld reports from the
completed check. Verify equality of all six generated error components
before forecasting. Save both earlier-only forecasts before scoring either
withheld history.

Report the paired difference in each history's maximum absolute standardized
error, the two failure counts, discordant pairs and the final range widths.
Preserve every technical failure. This is a descriptive control selected
after observing the 256-history result. It cannot replace that failed gate,
estimate aircraft coverage, or decide an Earth model. No aircraft original
or protected ESA group is read.

Use one worker and one numerical thread, one original start per pair,
at most 24,000 generated IMU packets and 242 receiver reports per pair,
and a 15-minute original wall allowance. Qualify task-level recovery before
launch; any continuation has a separately charged finite allowance. Freeze
the source, environment, policy and limits before the first task starts.
